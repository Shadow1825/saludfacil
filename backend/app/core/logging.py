"""Registro de loggers de SaludFácil.

Política (RNF-06 y RNF-11):
- NUNCA registrar contraseñas, tokens, DNI, correos, teléfonos,
  síntomas, resultados de triaje u otros datos personales/sensibles.
- Los mensajes deben ser comprensibles y no exponer trazas internas,
  rutas del servidor ni consultas SQL.
"""

import logging
import sys

from app.core.config import settings

_CONFIGURED = False


def configure_logging() -> None:
    """Configura el logging raíz de la aplicación (idempotente)."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    level = logging.DEBUG if settings.environment == "development" else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Devuelve un logger con el nombre del módulo solicitado."""
    configure_logging()
    return logging.getLogger(name)