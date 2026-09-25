"""Punto de entrada de la aplicación FastAPI de SaludFácil."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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


# ----- RNF-06: los errores y logs no exponen datos personales ni información interna -----

def _field_from_loc(loc: tuple) -> str:
    """Une la ruta del campo sin exponer valores (solo la localización)."""
    return ".".join(str(part) for part in loc if part not in ("body", "query", "path"))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """422 con la localización y el mensaje, SIN `input` (valores enviados).

    El formato por defecto de FastAPI incluye los valores recibidos en `input`;
    aquí se eliminan para no exponer contraseñas, DNI, correos ni teléfonos (RNF-06).
    """
    errores = [
        {"field": _field_from_loc(err.get("loc", ())), "message": str(err.get("msg", "Valor inválido."))}
        for err in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errores})


@app.exception_handler(Exception)
async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """500 genérico para excepciones no controladas.

    Solo se registra el tipo de la excepción; nunca su mensaje ni argumentos,
    para evitar que datos personales terminen en los logs (RNF-06 / RNF-11).
    """
    get_logger(__name__).error(
        "Excepción no controlada: %s", type(exc).__name__
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor. Intente nuevamente."},
    )


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Cabeceras de seguridad en todas las respuestas (RNF-07: seguridad)."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
    return response


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