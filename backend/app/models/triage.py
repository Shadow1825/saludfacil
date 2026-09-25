"""Modelo de triaje inicial (FASE 5) y su revisión administrativa (FASE 6).

Trazabilidad:
- RF-12 / HU-07 / CA-07.x: registro de síntomas y clasificación inicial.
- RF-13 / HU-08 / CA-08.x: el paciente consulta su clasificación inicial.
- RF-14 / HU-08 / CA-08.x: el profesional consulta solo el triaje de sus citas.
- RF-15 / HU-09 / CA-09.x: la clasificación se entrega en tiempo real (síncrona).
- RF-16 / HU-10 / CA-10.x: determinismo: mismos datos → mismo resultado.
- RF-17 / HU-13 / CA-13.x: el administrador revisa los triajes (FASE 6) y los
  marca como pendiente (registro), revisado o descartado.

El resultado es una clasificación inicial orientativa (NUNCA un diagnóstico médico).
Un triaje queda asociado al paciente (paciente_id) y a la cita reservada que lo
motiva (cita_id, uno por cita).
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    JSON,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TriajeEstadoRevision(str, enum.Enum):
    """Estados de la revisión administrativa de un triaje (RF-17 / HU-13)."""

    PENDIENTE = "pendiente"
    REVISADO = "revisado"
    DESCARTADO = "descartado"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Triaje(Base):
    """Clasificación inicial registrada para una cita reservada (RF-12)."""

    __tablename__ = "triajes"
    __table_args__ = (
        UniqueConstraint("cita_id", name="uq_triaje_cita"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paciente_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    cita_id: Mapped[int] = mapped_column(
        ForeignKey("citas.id", ondelete="CASCADE"), index=True, nullable=False
    )
    clasificacion: Mapped[str] = mapped_column(String(10), nullable=False)  # alta|media|baja
    sintomas: Mapped[list] = mapped_column(JSON, nullable=False)
    # Revisión administrativa (RF-17 / HU-13 / CA-13.x). Por defecto pendiente.
    estado_revision: Mapped[str] = mapped_column(
        String(12), nullable=False, default=TriajeEstadoRevision.PENDIENTE.value
    )
    creado_por_admin_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )