"""Esquemas del módulo de citas (FASE 4): RF-09, RF-10, RF-11, RF-21."""

from datetime import date, time

from pydantic import BaseModel, Field, model_validator

from app.models.medical import DIAS_SEMANA


def _parse_time(value: str) -> time:
    try:
        hora, minuto = value.strip().split(":")
        return time(int(hora), int(minuto))
    except (ValueError, AttributeError) as exc:
        raise ValueError("La hora debe tener formato HH:MM (24 horas).") from exc


def _time_str(value: time) -> str:
    return value.strftime("%H:%M")


class CitaCreate(BaseModel):
    """Reserva de cita: profesional, fecha y hora de inicio (RF-09)."""

    professional_id: int
    fecha: date
    hora_inicio: str

    @model_validator(mode="after")
    def _hora_valida(self) -> "CitaCreate":
        _parse_time(self.hora_inicio)
        return self


class AvailableSlot(BaseModel):
    """Tramo de 30 minutos disponible de un profesional en una fecha (RF-08/RF-09)."""

    fecha: date
    hora_inicio: str
    hora_fin: str


class AdminCitaEstado(BaseModel):
    """Cambio de estado administrativo de una cita (RF-21 / CA-11.4)."""

    estado: str = Field(pattern="^(cancelada|atendida|no_asistio)$")


def serialize_cita(cita) -> dict:
    return {
        "id": cita.id,
        "paciente_id": cita.paciente_id,
        "professional_id": cita.professional_id,
        "specialty_id": cita.specialty_id,
        "fecha": cita.fecha.isoformat(),
        "hora_inicio": _time_str(cita.hora_inicio),
        "hora_fin": _time_str(cita.hora_fin),
        "estado": cita.estado,
        "is_active": cita.is_active,
    }


def serialize_cita_detalle(cita, paciente, profesional, especialidad) -> dict:
    info = serialize_cita(cita)
    info["paciente"] = (
        f"{paciente.first_name} {paciente.last_name}" if paciente else ""
    )
    info["profesional"] = (
        f"{profesional.first_name} {profesional.last_name}"
        if profesional
        else ""
    )
    info["profesional_email"] = profesional.email if profesional else ""
    info["specialty_name"] = especialidad.nombre if especialidad else ""
    info["dia"] = DIAS_SEMANA.get(cita.fecha.weekday() + 1, "")
    return info