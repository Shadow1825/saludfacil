"""Rutas del módulo de citas (FASE 4).

- RF-09 / HU-04 / CA-04.x: POST /api/appointments (reserva, valida disponibilidad).
- RF-10 / HU-05 / CA-05.x: GET /api/appointments (citas del paciente).
- RF-11 / HU-06 / CA-06.x: POST /api/appointments/{id}/cancel (libera el horario).
- RF-21 / HU-11 / CA-11.4: GET/PATCH administrativo de citas.
- RNF-09: rechaza fechas pasadas y horarios ya ocupados (409) o no ofertados (422).
"""

from datetime import date, datetime, time, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import get_db
from app.models import (
    APPOINTMENT_DURATION_MINUTES,
    APPOINTMENT_MINUTES_STEP,
    Cita,
    CitaEstado,
    Especialidad,
    Horario,
    Profesional,
    User,
    UserRole,
)
from app.schemas import AdminCitaEstado, serialize_cita_detalle
from app.schemas.appointment import CitaCreate
from app.services.security import get_current_user, require_roles

SessionDep = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

router = APIRouter(prefix="/api", tags=["citas"])
logger = get_logger(__name__)


def _hoy() -> date:
    return datetime.now(timezone.utc).date()


def _sumar_minutos(hora: time, minutos: int) -> time:
    dt = datetime.combine(date(2000, 1, 1), hora) + timedelta(minutes=minutos)
    return dt.time()


def _slots_libres(db: Session, profesional: Profesional, fecha: date) -> list[dict]:
    """Tramos de 30 minutos libres del profesional en la fecha indicada (RF-08)."""
    dia_semana = fecha.weekday() + 1  # 1=Lunes … 7=Domingo
    horarios = db.execute(
        select(Horario).where(
            Horario.professional_id == profesional.id,
            Horario.is_active.is_(True),
            Horario.day == dia_semana,
        )
    ).scalars().all()

    ocupados = set(
        db.execute(
            select(Cita.hora_inicio).where(
                Cita.professional_id == profesional.id,
                Cita.fecha == fecha,
                Cita.is_active.is_(True),
            )
        ).scalars()
    )

    ahora = datetime.now(timezone.utc)
    hoy = ahora.date()
    ahora_hora = ahora.time().replace(second=0, microsecond=0)

    slots: list[dict] = []
    for horario in horarios:
        actual = horario.start_time
        while _sumar_minutos(actual, APPOINTMENT_DURATION_MINUTES) <= horario.end_time:
            if fecha == hoy and actual < ahora_hora:
                actual = _sumar_minutos(actual, APPOINTMENT_MINUTES_STEP)
                continue
            if actual not in ocupados:
                slots.append(
                    {
                        "fecha": fecha,
                        "hora_inicio": actual.strftime("%H:%M"),
                        "hora_fin": _sumar_minutos(actual, APPOINTMENT_DURATION_MINUTES).strftime("%H:%M"),
                    }
                )
            actual = _sumar_minutos(actual, APPOINTMENT_MINUTES_STEP)
    return slots


# ---------------------------------------------------------------------------
# RESERVA (RF-09 / HU-04)
# ---------------------------------------------------------------------------
@router.post("/appointments", status_code=201)
def create_appointment(
    payload: CitaCreate,
    db: SessionDep,
    user: User = Depends(require_roles(UserRole.PACIENTE)),
):
    if payload.fecha < _hoy():
        raise HTTPException(status_code=422, detail="No se pueden reservar citas en fechas pasadas.")

    profesional = db.get(Profesional, payload.professional_id)
    if not profesional or not profesional.is_active:
        raise HTTPException(status_code=404, detail="Profesional no encontrado o inactivo.")

    hora_inicio: time = datetime.strptime(payload.hora_inicio, "%H:%M").time()
    libre = _slots_libres(db, profesional, payload.fecha)
    tramo = next((s for s in libre if s["hora_inicio"] == payload.hora_inicio), None)
    if tramo is None:
        ocupado = db.scalar(
            select(Cita).where(
                Cita.professional_id == profesional.id,
                Cita.fecha == payload.fecha,
                Cita.hora_inicio == hora_inicio,
                Cita.is_active.is_(True),
            )
        )
        if ocupado:
            raise HTTPException(
                status_code=409,
                detail="Ese horario ya fue reservado por otro paciente.",
            )
        raise HTTPException(
            status_code=422,
            detail="El horario solicitado no está disponible para esa fecha.",
        )

    cita = Cita(
        paciente_id=user.id,
        professional_id=profesional.id,
        specialty_id=profesional.specialty_id,
        fecha=payload.fecha,
        hora_inicio=hora_inicio,
        hora_fin=datetime.strptime(tramo["hora_fin"], "%H:%M").time(),
        estado=CitaEstado.RESERVADA.value,
        is_active=True,
    )
    db.add(cita)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ese horario ya fue reservado por otro paciente.")
    db.refresh(cita)
    especialidad = db.get(Especialidad, cita.specialty_id)
    user_prof = db.get(User, profesional.user_id) if profesional else None
    return serialize_cita_detalle(cita, user, user_prof, especialidad)


# ---------------------------------------------------------------------------
# CONSULTA (RF-10 / HU-05; RF-21 / HU-11)
# ---------------------------------------------------------------------------
@router.get("/appointments")
def list_appointments(
    db: SessionDep,
    _: CurrentUser,
    profesional_id: int | None = Query(default=None),
    especialidad_id: int | None = Query(default=None),
    estado: str | None = Query(default=None),
):
    """Citas del paciente (RF-10) o de todo el sistema si es administrador (RF-21)."""
    if _.role == UserRole.PACIENTE:
        query = select(Cita).where(Cita.paciente_id == _.id)
        profesional_id = None  # el paciente no filtra por profesional (pantalla propia)
    elif _.role == UserRole.PROFESIONAL:
        prof = db.execute(select(Profesional).where(Profesional.user_id == _.id)).scalar_one_or_none()
        if prof is None:
            raise HTTPException(status_code=403, detail="Perfil profesional no encontrado.")
        query = select(Cita).where(Cita.professional_id == prof.id)
        profesional_id = None  # el profesional solo ve sus citas asignadas (RF-14 / HU-08)
    elif _.role == UserRole.ADMINISTRADOR:
        query = select(Cita)

    if profesional_id is not None:
        query = query.where(Cita.professional_id == profesional_id)
    if especialidad_id is not None:
        query = query.where(Cita.specialty_id == especialidad_id)
    if estado is not None:
        query = query.where(Cita.estado == estado)

    citas = db.execute(query.order_by(Cita.fecha.desc(), Cita.hora_inicio.desc())).scalars().all()

    salida = []
    for cita in citas:
        paciente = db.get(User, cita.paciente_id)
        profesional = db.get(Profesional, cita.professional_id)
        user_prof = db.get(User, profesional.user_id) if profesional else None
        especialidad = db.get(Especialidad, cita.specialty_id)
        salida.append(serialize_cita_detalle(cita, paciente, user_prof, especialidad))
    return salida


# ---------------------------------------------------------------------------
# CANCELACIÓN (RF-11 / HU-06)
# ---------------------------------------------------------------------------
@router.post("/appointments/{cita_id}/cancel", status_code=200)
def cancel_appointment(
    cita_id: int,
    db: SessionDep,
    user: User = Depends(get_current_user),
):
    cita = db.get(Cita, cita_id)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada.")
    es_admin = user.role == UserRole.ADMINISTRADOR
    es_dueño = user.role == UserRole.PACIENTE and cita.paciente_id == user.id
    if not (es_admin or es_dueño):
        raise HTTPException(status_code=403, detail="No tiene permisos para cancelar esta cita.")
    if cita.estado != CitaEstado.RESERVADA.value:
        raise HTTPException(status_code=409, detail="La cita ya no está reservada.")
    ahora = datetime.now(timezone.utc)
    if cita.fecha < ahora.date():
        raise HTTPException(status_code=422, detail="No se puede cancelar una cita ya pasada.")
    if cita.fecha == ahora.date() and cita.hora_inicio <= ahora.time():
        raise HTTPException(status_code=422, detail="No se puede cancelar una cita ya iniciada.")

    cita.estado = CitaEstado.CANCELADA.value
    cita.is_active = False
    db.commit()
    db.refresh(cita)
    return {"message": "Cita cancelada correctamente.", "id": cita.id}


# ---------------------------------------------------------------------------
# ADMINISTRACIÓN (RF-21 / HU-11 / CA-11.4)
# ---------------------------------------------------------------------------
@router.patch("/appointments/{cita_id}", status_code=200)
def update_appointment_state(
    cita_id: int,
    payload: AdminCitaEstado,
    db: SessionDep,
    _: User = Depends(require_roles(UserRole.ADMINISTRADOR)),
):
    cita = db.get(Cita, cita_id)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada.")
    cita.estado = payload.estado
    cita.is_active = payload.estado != CitaEstado.RESERVADA.value
    db.commit()
    db.refresh(cita)
    return {"message": "Estado de la cita actualizado.", "id": cita.id, "estado": cita.estado}