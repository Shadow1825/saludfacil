"""Configuración de pruebas del backend.

Las pruebas base (FASE 1) no requieren PostgreSQL: el motor se reemplaza por
SQLite en memoria para que el endpoint de estado pueda comprobarse localmente.
Las pruebas de integración con PostgreSQL real se incorporarán al validar Docker.
"""

import pytest
from sqlalchemy import create_engine

from app.api.routes import health
from app.db.session import engine as real_engine


@pytest.fixture(scope="session", autouse=True)
def _replace_runtime_engine():
    """Reemplaza el motor de producción por SQLite en memoria durante las pruebas."""
    health.engine = create_engine("sqlite://", future=True)
    yield
    health.engine = real_engine