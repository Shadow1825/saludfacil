"""Gestión de la sesión de base de datos.

La conexión no se abre en import; el inicio de la aplicación no depende de la
disponibilidad de PostgreSQL (el estado de la BD se reporta en `/api/health`).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

_connect_args = {"connect_timeout": 2} if settings.database_url.startswith("postgresql") else {}

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependencia de FastAPI que entrega una sesión de base de datos."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()