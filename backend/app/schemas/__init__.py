"""Esquemas Pydantic del dominio."""

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

__all__ = [
    "AdminUserCreateRequest",
    "AdminUserUpdateRequest",
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
    "TokenResponse",
    "UserOut",
    "_parse_time",
    "serialize_especialidad",
    "serialize_profesional",
    "serialize_schedule",
]