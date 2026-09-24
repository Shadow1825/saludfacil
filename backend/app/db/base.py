"""Base declarativa de SQLAlchemy para los modelos del sistema (FASE 2+)."""

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Clase base declarativa de todos los modelos."""


class TimestampedMixin:
    """Mixin con marcas de tiempo para auditoría básica."""

    created_at = mapped_column(nullable=False)
    updated_at = mapped_column(nullable=False)