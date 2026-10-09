"""Rutas del perfil del paciente (FASE 6 / RF-03 / HU-15 / CA-15.x).

- RF-03 / HU-15 / CA-15.1–15.4: PATCH /api/profile — el paciente actualiza sus
  propios datos (nombre, apellido, teléfono y contraseña opcional).
- DNI y correo son inmutables por el propio usuario (CA-15.3).
- La sesión activa se mantiene válida tras el cambio de contraseña
  (decisión documentada: no se incrementa token_version).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import get_db
from app.models import User, UserRole
from app.schemas.auth import UserOut
from app.schemas.profile import ProfileUpdateRequest
from app.services.security import (
    hash_password,
    require_roles,
    verify_password,
)

SessionDep = Annotated[Session, Depends(get_db)]

router = APIRouter(prefix="/api", tags=["perfil"])
logger = get_logger(__name__)


@router.patch("/profile", status_code=status.HTTP_200_OK, response_model=UserOut)
def update_profile(
    payload: ProfileUpdateRequest,
    db: SessionDep,
    user: User = Depends(require_roles(UserRole.PACIENTE)),
):
    """Actualización de los datos propios del paciente (RF-03 / HU-15 / CA-15.x)."""
    if payload.first_name is not None:
        user.first_name = payload.first_name.strip()
    if payload.last_name is not None:
        user.last_name = payload.last_name.strip()
    if payload.phone is not None:
        user.phone = payload.phone.strip()
    if payload.new_password is not None:
        if not verify_password(payload.current_password or "", user.password_hash):
            raise HTTPException(
                status_code=422, detail="La contraseña actual es incorrecta."
            )
        user.password_hash = hash_password(payload.new_password)
        logger.info("El paciente %s cambió su contraseña.", user.id)

    db.commit()
    db.refresh(user)
    logger.info("Perfil actualizado para el paciente %s.", user.id)
    return user