"""Esquemas Pydantic del dominio."""

from app.schemas.appointment import (
    AdminCitaEstado,
    AvailableSlot,
    CitaCreate,
    serialize_cita,
    serialize_cita_detalle,
)
from app.schemas.auth import (
    AdminUserCreateRequest,
    AdminUserUpdateRequest,
    LoginRequest,
    PacientRegisterRequest,
    TokenResponse,
    UserOut,
)
from app.schemas.medical import (
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
from app.schemas.triage import SintomaInput, TriageCreate, serialize_triage

__all__ = [
    "AdminCitaEstado",
    "AdminUserCreateRequest",
    "AdminUserUpdateRequest",
    "AvailableSlot",
    "CitaCreate",
    "EspecialidadCreate",
    "EspecialidadOut",
    "EspecialidadUpdate",
    "LoginRequest",
    "PacientRegisterRequest",
    "ProfessionalCreate",
    "ProfessionalOut",
    "ProfessionalUpdate",
    "ScheduleCreate",
    "ScheduleOut",
    "ScheduleUpdate",
    "SintomaInput",
    "TokenResponse",
    "TriageCreate",
    "UserOut",
    "_parse_time",
    "serialize_cita",
    "serialize_cita_detalle",
    "serialize_especialidad",
    "serialize_profesional",
    "serialize_schedule",
    "serialize_triage",
]