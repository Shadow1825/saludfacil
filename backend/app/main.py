"""Punto de entrada de la aplicación FastAPI de SaludFácil."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "API REST de SaludFácil: Sistema de Gestión de Citas Médicas y Triaje. "
        "Documentación generada automáticamente (OpenAPI)."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")


@app.get("/", include_in_schema=False)
async def root() -> dict:
    """Redirige a la documentación interactiva."""
    return {"service": settings.app_name, "docs": "/docs", "health": "/api/health"}