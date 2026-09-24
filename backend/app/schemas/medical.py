"""Esquemas del catálogo médico (FASE 3): especialidades, profesionales y horarios."""

from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.medical import DIAS_SEMANA


def _parse_time(value: str) -> time:
    try:
        hora, minuto = value.strip().split(":")
        return time(int(hora), int(minuto))
    except (ValueError, AttributeError) as exc:
        raise ValueError("La hora debe tener formato HH:MM (24 horas).") from exc


def _time_str(value: time) -> str:
    return value.strftime("%H:%M")


# ---------------------------------------------------------------------------
# Especialidades (RF-05)
# ---------------------------------------------------------------------------
class EspecialidadCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)


class EspecialidadUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    is_active: bool | None = None


class EspecialidadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    is_active: bool


# ---------------------------------------------------------------------------
# Profesionales (RF-04)
# ---------------------------------------------------------------------------
class ProfessionalCreate(BaseModel):
    """Registro de un profesional: crea cuenta de usuario y perfil profesional."""

    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    dni: str = Field(min_length=8, max_length=8)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=20)
    password: str = Field(min_length=8, max_length=128)
    specialty_id: int

    @model_validator(mode="after")
    def _dni_8_digitos(self) -> "ProfessionalCreate":
        if not self.dni.strip().isdigit() or len(self.dni.strip()) != 8:
            raise ValueError("El DNI debe contener exactamente 8 dígitos")
        return self

    @model_validator(mode="after")
    def _phone_digitos(self) -> "ProfessionalCreate":
        if not self.phone.strip().isdigit() or len(self.phone.strip()) < 7:
            raise ValueError("El teléfono debe contener al menos 7 dígitos")
        return self


class ProfessionalUpdate(BaseModel):
    """/Edición de un profesional: especialidad o datos básicos (RF-04)."""

    first_name: str | None = Field(default=None, min_length=1, max_length=120)
    last_name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = Field(default=None, min_length=7, max_length=20)
    specialty_id: int | None = None
    is_active: bool | None = None


class ProfessionalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    specialty_id: int
    specialty_name: str
    first_name: str
    last_name: str
    email: str
    is_active: bool


# ---------------------------------------------------------------------------
# Horarios (RF-06 / RF-08)
# ---------------------------------------------------------------------------
class ScheduleCreate(BaseModel):
    professional_id: int
    day: int = Field(ge=1, le=7)
    start_time: str
    end_time: str

    @model_validator(mode="after")
    def _validar_horas(self) -> "ScheduleCreate":
        inicio = _parse_time(self.start_time)
        fin = _parse_time(self.end_time)
        if inicio >= fin:
            raise ValueError("La hora de inicio debe ser anterior a la hora de fin")
        return self


class ScheduleUpdate(BaseModel):
    day: int | None = Field(default=None, ge=1, le=7)
    start_time: str | None = None
    end_time: str | None = None
    is_active: bool | None = None


class ScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    professional_id: int
    day: int
    day_name: str
    start_time: str
    end_time: str
    is_active: bool


class AvailableSchedule(ScheduleOut):
    """Horario disponible del profesional seleccionado (RF-08)."""


def serialize_schedule(schedule) -> dict:
    """Serializa un horario con hora en formato HH:MM (evita tz en comparaciones)."""
    return {
        "id": schedule.id,
        "professional_id": schedule.professional_id,
        "day": schedule.day,
        "day_name": DIAS_SEMANA.get(schedule.day, str(schedule.day)),
        "start_time": _time_str(schedule.start_time),
        "end_time": _time_str(schedule.end_time),
        "is_active": schedule.is_active,
    }


def serialize_especialidad(especialidad) -> dict:
    return {"id": especialidad.id, "nombre": especialidad.nombre, "is_active": especialidad.is_active}


def serialize_profesional(profesional, user) -> dict:
    return {
        "id": profesional.id,
        "user_id": profesional.user_id,
        "specialty_id": profesional.specialty_id,
        "specialty_name": profesional.specialty.nombre,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "is_active": profesional.is_active,
    }