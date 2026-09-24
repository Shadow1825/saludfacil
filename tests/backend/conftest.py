"""Configuración de pruebas del backend.

Las pruebas no requieren PostgreSQL: el motor se reemplaza por SQLite en memoria
(compartido entre sesiones) para ejercitar modelos, rutas, hash y JWT de forma
reproducible. Las pruebas de integración con PostgreSQL real se ejecutan en Docker.
"""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite+pysqlite://"

import app.db.session as db_session_mod  # noqa: E402
import app.main as main_mod  # noqa: E402
from app.api.routes import health  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.models import Cita, Especialidad, Horario, Profesional, Triaje, User  # noqa: E402

TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)

# El endpoint de estado y la app usan el motor de prueba.
health.engine = TEST_ENGINE
db_session_mod.engine = TEST_ENGINE
main_mod.engine = TEST_ENGINE

TestingSessionLocal = sessionmaker(bind=TEST_ENGINE, autocommit=False, autoflush=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


main_mod.app.dependency_overrides[db_session_mod.get_db] = override_get_db

Base.metadata.create_all(bind=TEST_ENGINE)


@pytest.fixture()
def db() -> Generator:
    """Sesión de base de datos de prueba limpia por test (SQLite compartida)."""
    session = TestingSessionLocal()
    try:
        session.query(Triaje).delete()  # FK -> citas (borrar primero)
        session.query(Cita).delete()
        session.query(Horario).delete()
        session.query(Profesional).delete()
        session.query(Especialidad).delete()
        session.query(User).delete()  # aislamiento entre pruebas
        session.commit()
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client() -> Generator:
    """Cliente HTTP de prueba con la app configurada sobre SQLite."""
    with TestClient(main_mod.app) as test_client:
        yield test_client