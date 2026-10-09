"""Rutas del catálogo médico (FASE 3).

Administración (solo administrador): RF-04, RF-05, RF-06.
Directorio y disponibilidad (paciente/profesional autenticado): RF-07, RF-08.
"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.logging import get_logger
from app.db.session import get_db
from app.models import Especialidad, Horario, Profesional, User, UserRole
from app.schemas import (
    EspecialidadCreate,
    EspecialidadOut,
    EspecialidadUpdate,
    ProfessionalCreate,
    ProfessionalOut,
    ProfessionalUpdate,
    ScheduleCreate,
    ScheduleOut,
    ScheduleUpdate,
    _parse_time,
    serialize_especialidad,
    serialize_profesional,
    serialize_schedule,
)
from app.services.security import get_current_user, require_roles

SessionDep = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

router = APIRouter(prefix="/api", tags=["catálogo médico"])
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# ESPECIALIDADES (RF-05) — solo administrador
# ---------------------------------------------------------------------------
@router.post("/specialties", response_model=EspecialidadOut, status_code=201)
def create_specialty(payload: EspecialidadCreate, db: SessionDep, _: User = Depends(require_roles(UserRole.ADMINISTRADOR))):
    nombre = payload.nombre.strip()
    existe = db.scalar(select(Especialidad).where(Especialidad.nombre == nombre))
    if existe:
        raise HTTPException(status_code=409, detail="Ya existe una especialidad con ese nombre.")
    especialidad = Especialidad(nombre=nombre)
    db.add(especialidad)
    db.commit()
    db.refresh(especialidad)
    return especialidad


@router.get("/specialties", response_model=list[EspecialidadOut])
def list_specialties(db: SessionDep, _: CurrentUser):
    """Listado para gestión (admin ve activas e inactivas) y para el paciente."""
    resultado = db.execute(select(Especialidad).order_by(Especialidad.nombre)).scalars().all()
    return [serialize_especialidad(e) for e in resultado]


@router.patch("/specialties/{specialty_id}", response_model=EspecialidadOut)
def update_specialty(
    specialty_id: int,
    payload: EspecialidadUpdate,
    db: SessionDep,
    _: User = Depends(require_roles(UserRole.ADMINISTRADOR)),
):
    especialidad = db.get(Especialidad, specialty_id)
    if not especialidad:
        raise HTTPException(status_code=404, detail="Especialidad no encontrada.")
    if payload.nombre is not None and payload.nombre.strip().lower() != especialidad.nombre.lower():
        nombre = payload.nombre.strip()
        duplicado = db.scalar(select(Especialidad).where(Especialidad.nombre == nombre, Especialidad.id != specialty_id))
        if duplicado:
            raise HTTPException(status_code=409, detail="Ya existe una especialidad con ese nombre.")
        especialidad.nombre = nombre
    if payload.is_active is not None:
        especialidad.is_active = payload.is_active
    db.commit()
    db.refresh(especialidad)
    return especialidad


# ---------------------------------------------------------------------------
# PROFESIONALES (RF-04) — solo administrador
# ---------------------------------------------------------------------------
@router.get("/professionals", response_model=list[ProfessionalOut])
def list_professionals(db: SessionDep, _: User = Depends(require_roles(UserRole.ADMINISTRADOR))):
    resultado = (
        db.execute(
            select(Profesional)
            .options(joinedload(Profesional.specialty))
            .order_by(Profesional.id)
        )
        .scalars()
        .all()
    )
    salida = []
    for profesional in resultado:
        user = db.get(User, profesional.user_id)
        if user:
            salida.append(serialize_profesional(profesional, user))
    return salida


@router.post("/professionals", response_model=ProfessionalOut, status_code=201)
def create_professional(
    payload: ProfessionalCreate, db: SessionDep, _: User = Depends(require_roles(UserRole.ADMINISTRADOR))
):
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="El correo ya está registrado.")
    if db.scalar(select(User).where(User.dni == payload.dni)):
        raise HTTPException(status_code=409, detail="El DNI ya está registrado.")
    especialidad = db.get(Especialidad, payload.specialty_id)
    if not especialidad or not especialidad.is_active:
        raise HTTPException(status_code=404, detail="Especialidad no encontrada o inactiva.")
    from app.services.security import hash_password

    user = User(
        email=email,
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        dni=payload.dni.strip(),
        phone=payload.phone.strip(),
        role=UserRole.PROFESIONAL,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.flush()
    profesional = Profesional(user_id=user.id, specialty_id=especialidad.id)
    db.add(profesional)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Datos duplicados.")
    db.refresh(user)
    db.refresh(profesional)
    return serialize_profesional(profesional, user)


@router.patch("/professionals/{professional_id}", response_model=ProfessionalOut)
def update_professional(
    professional_id: int,
    payload: ProfessionalUpdate,
    db: SessionDep,
    _: User = Depends(require_roles(UserRole.ADMINISTRADOR)),
):
    profesional = db.get(Profesional, professional_id)
    if not profesional:
        raise HTTPException(status_code=404, detail="Profesional no encontrado.")
    user = db.get(User, profesional.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Cuenta del profesional no encontrada.")
    if payload.specialty_id is not None and payload.specialty_id != profesional.specialty_id:
        especialidad = db.get(Especialidad, payload.specialty_id)
        if not especialidad or not especialidad.is_active:
            raise HTTPException(status_code=404, detail="Especialidad no encontrada o inactiva.")
        profesional.specialty_id = especialidad.id
    if payload.is_active is not None:
        profesional.is_active = payload.is_active
        user.is_active = payload.is_active
    if payload.first_name is not None:
        user.first_name = payload.first_name.strip()
    if payload.last_name is not None:
        user.last_name = payload.last_name.strip()
    if payload.phone is not None:
        user.phone = payload.phone.strip()
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Datos inválidos.")
    db.refresh(user)
    db.refresh(profesional)
    return serialize_profesional(profesional, user)


# ---------------------------------------------------------------------------
# HORARIOS (RF-06) — solo administrador
# ---------------------------------------------------------------------------
@router.get("/schedules", response_model=list[ScheduleOut])
def list_schedules(
    db: SessionDep,
    professional_id: int | None = Query(default=None),
    _: User = Depends(require_roles(UserRole.ADMINISTRADOR)),
):
    query = select(Horario).order_by(Horario.professional_id, Horario.day, Horario.start_time)
    if professional_id is not None:
        query = query.where(Horario.professional_id == professional_id)
    resultado = db.execute(query).scalars().all()
    return [serialize_schedule(h) for h in resultado]


@router.post("/schedules", response_model=ScheduleOut, status_code=201)
def create_schedule(
    payload: ScheduleCreate, db: SessionDep, _: User = Depends(require_roles(UserRole.ADMINISTRADOR))
):
    profesional = db.get(Profesional, payload.professional_id)
    if not profesional or not profesional.is_active:
        raise HTTPException(status_code=404, detail="Profesional no encontrado o inactivo.")
    horario = Horario(
        professional_id=payload.professional_id,
        day=payload.day,
        start_time=_parse_time(payload.start_time),
        end_time=_parse_time(payload.end_time),
    )
    db.add(horario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe ese horario para el profesional.")
    db.refresh(horario)
    return serialize_schedule(horario)


@router.patch("/schedules/{schedule_id}", response_model=ScheduleOut)
def update_schedule(
    schedule_id: int,
    payload: ScheduleUpdate,
    db: SessionDep,
    _: User = Depends(require_roles(UserRole.ADMINISTRADOR)),
):
    horario = db.get(Horario, schedule_id)
    if not horario:
        raise HTTPException(status_code=404, detail="Horario no encontrado.")
    if payload.day is not None:
        horario.day = payload.day
    if payload.start_time is not None:
        horario.start_time = _parse_time(payload.start_time)
    if payload.end_time is not None:
        horario.end_time = _parse_time(payload.end_time)
    if horario.start_time >= horario.end_time:
        raise HTTPException(status_code=422, detail="La hora de inicio debe ser anterior a la hora de fin.")
    if payload.is_active is not None:
        horario.is_active = payload.is_active
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe ese horario para el profesional.")
    db.refresh(horario)
    return serialize_schedule(horario)


# ---------------------------------------------------------------------------
# DIRECTORIO Y DISPONIBILIDAD (RF-07 / RF-08) — paciente y profesional
# ---------------------------------------------------------------------------
@router.get("/directory/specialties", response_model=list[EspecialidadOut])
def directory_specialties(db: SessionDep, _: CurrentUser):
    """Especialidades activas (CA-03.1)."""
    return [
        serialize_especialidad(e)
        for e in db.execute(
            select(Especialidad).where(Especialidad.is_active.is_(True)).order_by(Especialidad.nombre)
        ).scalars()
    ]


@router.get("/directory/professionals", response_model=list[ProfessionalOut])
def directory_professionals(
    db: SessionDep,
    specialty_id: int | None = Query(default=None),
    _: User = Depends(get_current_user),
):
    """Profesionales activos de la especialidad seleccionada (CA-03.2)."""
    query = (
        select(Profesional)
        .options(joinedload(Profesional.specialty))
        .where(Profesional.is_active.is_(True))
        .order_by(Profesional.id)
    )
    if specialty_id is not None:
        query = query.where(Profesional.specialty_id == specialty_id)
    resultado = db.execute(query).scalars().all()
    salida = []
    for profesional in resultado:
        user = db.get(User, profesional.user_id)
        if user and user.is_active:
            salida.append(serialize_profesional(profesional, user))
    return salida


@router.get("/directory/schedules", response_model=list[ScheduleOut])
def directory_schedules(
    db: SessionDep,
    professional_id: int = Query(...),
    _: User = Depends(get_current_user),
):
    """Solo horarios disponibles del profesional seleccionado (RF-08, CA-03.3/03.4)."""
    profesional = db.get(Profesional, professional_id)
    if not profesional or not profesional.is_active:
        raise HTTPException(status_code=404, detail="Profesional no encontrado o inactivo.")
    resultado = db.execute(
        select(Horario)
        .where(Horario.professional_id == professional_id, Horario.is_active.is_(True))
        .order_by(Horario.day, Horario.start_time)
    ).scalars().all()
    # FASE 3: un horario activo está disponible (las citas se restan en FASE 4).
    return [serialize_schedule(h) for h in resultado]


@router.get("/directory/slots")
def directory_slots(
    db: SessionDep,
    professional_id: int = Query(...),
    fecha: str = Query(...),
    _: User = Depends(get_current_user),
):
    """Tramos de 30 minutos libres del profesional en la fecha indicada (RF-08/RF-09).

    Excluye tramos ya reservados y fechas pasadas (RNF-09).
    """
    try:
        fecha_date = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=422, detail="Formato de fecha inválido (use YYYY-MM-DD).")
    if fecha_date < datetime.now(timezone.utc).date():
        raise HTTPException(status_code=422, detail="No se pueden consultar fechas pasadas.")

    profesional = db.get(Profesional, professional_id)
    if not profesional or not profesional.is_active:
        raise HTTPException(status_code=404, detail="Profesional no encontrado o inactivo.")

    from app.api.routes.appointments import _slots_libres

    return _slots_libres(db, profesional, fecha_date)