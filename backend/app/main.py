"""Punto de entrada de la aplicación FastAPI de SaludFácil."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import appointments, auth, health, medical, profile, triage, users
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.db.base import Base
from app.db.session import engine
from app.models import appointment as _appointment_model  # noqa: F401  (registra los modelos)
from app.models import medical as _medical_model  # noqa: F401  (registra los modelos)
from app.models import triage as _triage_model  # noqa: F401  (registra los modelos)
from app.models import user as _user_model  # noqa: F401  (registra los modelos)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Al iniciar, crea las tablas si no existen (sin migraciones en esta fase)."""
    configure_logging()
    logger = get_logger(__name__)
    Base.metadata.create_all(bind=engine)
    logger.info("Base de datos lista.")
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "API REST de SaludFácil: Sistema de Gestión de Citas Médicas y Triaje. "
        "Documentación generada automáticamente (OpenAPI)."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router := health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(medical.router)  # FASE 3 (catálogo médico)
app.include_router(appointments.router)  # FASE 4 (citas)
app.include_router(profile.router)  # FASE 6 (RF-03): perfil del paciente
app.include_router(triage.router)  # FASE 5 y 6 (triaje y revisión)


@app.get("/", include_in_schema=False)
async def root() -> dict:
    """Redirige a la documentación interactiva."""
    return {"service": settings.app_name, "docs": "/docs", "health": "/api/health"}