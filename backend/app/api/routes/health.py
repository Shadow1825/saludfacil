"""Enrutador de estado del servicio (FASE 1).

Permite verificar la conectividad frontend -> backend -> PostgreSQL
sin exponer información sensible (RNF-06, RNF-11).
"""

from fastapi import APIRouter
from sqlalchemy import text
from starlette.concurrency import run_in_threadpool

from app.core.logging import get_logger
from app.db.session import engine

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


def _check_database() -> str:
    """Devuelve el estado de la conexión a la base de datos."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        # No se propaga el detalle del error de conexión al cliente (RNF-06).
        return "unreachable"


@router.get("/health")
async def health() -> dict:
    """Estado del servicio y de la conexión a la base de datos."""
    database = await run_in_threadpool(_check_database)
    return {"status": "ok", "service": "saludfacil-api", "database": database}