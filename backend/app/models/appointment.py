"""Modelo de citas médicas (FASE 4).

Trazabilidad:
- RF-09 / HU-04 / CA-04.x: reserva de cita (valida disponibilidad y bloquea el horario).
- RF-10 / HU-05 / CA-05.x: consulta de citas del paciente.
- RF-11 / HU-06 / CA-06.x: cancelación (libera el horario).
- RF-21 / HU-11 / CA-11.4: administración de citas por el administrador.
- RNF-09: no se reservan citas en fechas pasadas ni en horarios ocupados.
"""

import enum
from datetime import date, datetime, time, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Time,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

APPOINTMENT_DURATION_MINUTES = 30
APPOINTMENT_MINUTES_STEP = 30


class CitaEstado(str, enum.Enum):
    RESERVADA = "reservada"
    CANCELADA = "cancelada"
    ATENDIDA = "atendida"
    NO_ASISTIO = "no_asistio"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Cita(Base):
    """Cita médica reservada por un paciente a un profesional (RF-09)."""

    __tablename__ = "citas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paciente_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    professional_id: Mapped[int] = mapped_column(
        ForeignKey("profesionales.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    specialty_id: Mapped[int] = mapped_column(
        ForeignKey("especialidades.id"), nullable=False
    )
    fecha: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[time] = mapped_column(Time, nullable=False)
    estado: Mapped[str] = mapped_column(
        String(20), default=CitaEstado.RESERVADA.value, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )


# Índice único parcial: un horario (profesional + fecha + inicio) solo puede
# tener una cita activa (RNF-09 / CA-04.2). Al cancelar, la cita pasa a
# inactiva (is_active=false) y el horario queda libre para re-reserva.
Index(
    "uq_cita_prof_fecha_hora_activa",
    "professional_id",
    "fecha",
    "hora_inicio",
    unique=True,
    sqlite_where=text("is_active = 1"),
    postgresql_where=text("is_active = true"),
)