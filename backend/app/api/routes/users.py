"""Rutas administrativas de usuarios (FASE 2).

Trazabilidad: RF-18 / HU-11 / CA-11.5 — el administrador crea, edita y
desactiva cuentas. Protegidas por rol administrador (RF-19 / RNF-02: 403).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import AdminUserCreateRequest, AdminUserUpdateRequest, UserOut
from app.services.security import get_current_user, hash_password, require_roles

router = APIRouter(prefix="/users", tags=["users"])
logger = get_logger(__name__)

require_admin = require_roles(UserRole.ADMINISTRADOR)


def _user_o_no_encontrado(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario solicitado no existe.",
        )
    return user


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> list[User]:
    """Consulta de usuarios (administrador)."""
    return db.query(User).order_by(User.id).all()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=UserOut)
def create_user(
    data: AdminUserCreateRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> User:
    """Creación de cuenta de usuario (RF-18 / CA-11.5)."""
    email_normalizado = data.email.lower()
    existing = (
        db.query(User)
        .filter(or_(User.email == email_normalizado, User.dni == data.dni))
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo electrónico o el DNI ya se encuentran registrados.",
        )

    user = User(
        email=email_normalizado,
        password_hash=hash_password(data.password),
        role=data.role,
        first_name=data.first_name.strip(),
        last_name=data.last_name.strip(),
        dni=data.dni,
        phone=data.phone,
        is_active=True,
        token_version=0,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo electrónico o el DNI ya se encuentran registrados.",
        ) from exc
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: AdminUserUpdateRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> User:
    """Edición de cuenta: datos, rol o desactivación (RF-18 / CA-11.5)."""
    user = _user_o_no_encontrado(db, user_id)

    updates = data.model_dump(exclude_unset=True)
    if "role" in updates and updates["role"] is not None:
        user.role = updates["role"]
    if "is_active" in updates and updates["is_active"] is not None:
        # Al desactivar se invalidan sus sesiones activas.
        if updates["is_active"] != user.is_active:
            user.token_version += 1
        user.is_active = updates["is_active"]
    if updates.get("first_name") is not None:
        user.first_name = updates["first_name"].strip()
    if updates.get("last_name") is not None:
        user.last_name = updates["last_name"].strip()
    if updates.get("phone") is not None:
        user.phone = updates["phone"]

    db.commit()
    db.refresh(user)
    return user