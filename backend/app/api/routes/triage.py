"""Rutas del triaje inicial (FASE 5) y su revisión administrativa (FASE 6).

- RF-12 / HU-07 / CA-07.x: POST /api/triage (registro de síntomas + clasificación).
- RF-13 / HU-08 / CA-08.1–08.4: el paciente consulta su clasificación inicial.
- RF-14 / HU-08 / CA-08.2–08.4: el profesional consulta solo el de sus citas.
- RF-15 / HU-09 / CA-09.x: clasificación entregada de inmediato en la respuesta.
- RF-16 / HU-10 / CA-10.x: determinismo (mismos datos → mismo resultado).
- RF-17 / HU-13 / CA-13.x: PATCH /api/triage/{id}/revision (solo administrador).
"""

from datetime import date, datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import get_db
from app.models import Cita, CitaEstado, Especialidad, Profesional, Triaje, User, UserRole
from app.schemas.triage import RevisionTriaje, TriageCreate, serialize_triage
from app.services.security import get_current_user, require_roles
from app.services.triage import clasificar

SessionDep = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

router = APIRouter(prefix="/api", tags=["triaje"])
logger = get_logger(__name__)


def _hoy() -> date:
    return datetime.now(timezone.utc).date()


def _es_rol(user: User, *roles: UserRole) -> bool:
    return user.role in roles


def _profesional_de_usuario(db: Session, user: User) -> Profesional | None:
    """Profesional vinculado a la cuenta de usuario (RF-14)."""
    if user.role != UserRole.PROFESIONAL:
        return None
    return db.scalar(select(Profesional).where(Profesional.user_id == user.id))


# ---------------------------------------------------------------------------
# REGISTRO DE SÍNTOMAS Y CLASIFICACIÓN (RF-12 / HU-07 / CA-07.x)
# ---------------------------------------------------------------------------
@router.post("/triage", status_code=201)
def create_triage(
    payload: TriageCreate,
    db: SessionDep,
    user: User = Depends(require_roles(UserRole.PACIENTE)),
):
    cita = db.get(Cita, payload.cita_id)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada.")
    if cita.paciente_id != user.id:
        raise HTTPException(status_code=403, detail="Solo puede registrar el triaje de sus propias citas.")
    if cita.estado != CitaEstado.RESERVADA.value:
        raise HTTPException(status_code=422, detail="El triaje solo se registra para citas reservadas.")
    if cita.fecha < _hoy():
        raise HTTPException(status_code=422, detail="La cita ya pasó; no puede registrar el triaje.")

    ya_existe = db.scalar(select(Triaje).where(Triaje.cita_id == cita.id))
    if ya_existe:
        raise HTTPException(status_code=409, detail="La cita ya tiene un triaje registrado.")

    sintomas = [
        {"nombre": s.nombre, "severidad": s.severidad}
        for s in payload.sintomas
    ]
    clasificacion = clasificar(sintomas)  # R1-R6, determinista (RF-16)
    triaje = Triaje(
        paciente_id=user.id,
        cita_id=cita.id,
        clasificacion=clasificacion,
        sintomas=sintomas,
    )
    db.add(triaje)
    db.commit()
    db.refresh(triaje)

    paciente = db.get(User, cita.paciente_id)
    profesional = db.get(Profesional, cita.professional_id)
    user_prof = db.get(User, profesional.user_id) if profesional else None
    especialidad = db.get(Especialidad, cita.specialty_id)
    cuerpo = serialize_triage(triaje, paciente, cita, user_prof, especialidad)
    cuerpo["message"] = "Clasificación inicial registrada correctamente (RF-12)."
    return cuerpo


# ---------------------------------------------------------------------------
# CONSULTA SEGÚN ROL (RF-13/RF-14 / HU-08 / CA-08.x)
# ---------------------------------------------------------------------------
@router.get("/triage")
def list_triage(db: SessionDep, user: CurrentUser):
    """Triajes según rol:
    - paciente: solo los suyos (RF-13 / CA-08.1-08.4).
    - profesional: solo los de sus citas autorizadas (RF-14 / CA-08.2-08.4).
    - administrador: lectura de todo el sistema para la revisión (RF-17 / HU-13).
    """
    if user.role == UserRole.PACIENTE:
        query = select(Triaje).where(Triaje.paciente_id == user.id)
    elif user.role == UserRole.PROFESIONAL:
        profesional = _profesional_de_usuario(db, user)
        if profesional is None:
            raise HTTPException(
                status_code=403,
                detail="Su cuenta no está vinculada a un profesional registrado.",
            )
        query = (
            select(Triaje)
            .join(Cita, Cita.id == Triaje.cita_id)
            .where(Cita.professional_id == profesional.id)
        )
    elif user.role == UserRole.ADMINISTRADOR:
        query = select(Triaje)
    else:
        raise HTTPException(status_code=403, detail="Acceso no autorizado.")

    triajes = db.execute(query.order_by(Triaje.created_at.desc(), Triaje.id.desc())).scalars().all()
    return [_armar(triaje, db) for triaje in triajes]


# ---------------------------------------------------------------------------
# DETALLE (CA-08.2 – control de acceso por dueño / profesional de la cita / admin)
# ---------------------------------------------------------------------------
@router.get("/triage/{triage_id}")
def get_triage(triage_id: int, db: SessionDep, user: CurrentUser):
    triaje = db.get(Triaje, triage_id)
    if not triaje:
        raise HTTPException(status_code=404, detail="Triaje no encontrado.")

    puede_ver = False
    if user.role == UserRole.PACIENTE:
        puede_ver = triaje.paciente_id == user.id  # CA-08.1: solo los suyos
    elif user.role == UserRole.PROFESIONAL:
        profesional = _profesional_de_usuario(db, user)
        cita = db.get(Cita, triaje.cita_id)
        puede_ver = bool(profesional and cita and cita.professional_id == profesional.id)
    elif user.role == UserRole.ADMINISTRADOR:
        puede_ver = True
    if not puede_ver:
        raise HTTPException(status_code=403, detail="No tiene permisos para consultar este triaje.")

    return _armar(triaje, db)


# ---------------------------------------------------------------------------
# REVISIÓN ADMINISTRATIVA (RF-17 / HU-13 / CA-13.x)
# ---------------------------------------------------------------------------
@router.patch("/triage/{triage_id}/revision", status_code=200)
def revisar_triaje(
    triage_id: int,
    payload: RevisionTriaje,
    db: SessionDep,
    user: User = Depends(require_roles(UserRole.ADMINISTRADOR)),
):
    """El administrador revisa un triaje: lo confirma (revisado) o lo descarta.

    - CA-13.1: marca como "revisado" (confirma el registro).
    - CA-13.2: marca como "descartado" (datos inconsistentes).
    - CA-13.3: paciente o profesional no pueden cambiar el estado (403).
    """
    triaje = db.get(Triaje, triage_id)
    if not triaje:
        raise HTTPException(status_code=404, detail="Triaje no encontrado.")

    triaje.estado_revision = payload.estado
    triaje.creado_por_admin_en = datetime.now(timezone.utc)  # momento de la revisión
    db.commit()
    db.refresh(triaje)
    logger.info("Triaje %s marcado como %s por el administrador.", triaje.id, payload.estado)
    return _armar(triaje, db)


def _armar(triaje: Triaje, db: Session) -> dict:
    cita = db.get(Cita, triaje.cita_id)
    paciente = db.get(User, triaje.paciente_id)
    profesional = db.get(Profesional, cita.professional_id) if cita else None
    user_prof = db.get(User, profesional.user_id) if profesional else None
    especialidad = db.get(Especialidad, cita.specialty_id) if cita else None
    return serialize_triage(triaje, paciente, cita, user_prof, especialidad)