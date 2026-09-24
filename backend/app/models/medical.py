"""Modelos del catálogo médico (FASE 3).

Entidades equivalentes a especialidades, profesionales y horarios del documento.
Trazabilidad: RF-04, RF-05, RF-06 (gestión), RF-07, RF-08 (consulta).
"""

from datetime import datetime, time, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

DIAS_SEMANA = {
    1: "Lunes",
    2: "Martes",
    3: "Miércoles",
    4: "Jueves",
    5: "Viernes",
    6: "Sábado",
    7: "Domingo",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Especialidad(Base):
    """Especialidad médica (RF-05)."""

    __tablename__ = "especialidades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )


class Profesional(Base):
    """Profesional de salud vinculado a una cuenta de usuario (RF-04).

    admin puede registrar/editar/desactivar profesionales; CA-11.1.
    """

    __tablename__ = "profesionales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    specialty_id: Mapped[int] = mapped_column(
        ForeignKey("especialidades.id"), index=True, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    specialty: Mapped[Especialidad] = relationship(lazy="joined")


class Horario(Base):
    """Horario de atención de un profesional (RF-06).

    Define día, hora de inicio y hora de fin (CA-11.3).
    """

    __tablename__ = "horarios"
    __table_args__ = (
        UniqueConstraint(
            "professional_id", "day", "start_time", name="uq_horario_prof_dia_hora"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    professional_id: Mapped[int] = mapped_column(
        ForeignKey("profesionales.id", ondelete="CASCADE"), index=True, nullable=False
    )
    day: Mapped[int] = mapped_column(Integer, nullable=False)  # 1=Lunes … 7=Domingo
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    @property
    def day_name(self) -> str:
        return DIAS_SEMANA.get(self.day, str(self.day))