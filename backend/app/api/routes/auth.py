"""Rutas de autenticación (FASE 2).

RFC de trazabilidad:
- RF-01 / HU-01: POST /api/auth/register  (CA-01.1 a CA-01.4)
- RF-02 / HU-02: POST /api/auth/login     (CA-02.1 a CA-02.4)
- RF-20 / HU-14: POST /api/auth/logout    (CA-14.1 a CA-14.3)
- RF-19 / HU-12: RBAC aplicada en cada endpoint protegido (CA-12.x)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    PacientRegisterRequest,
    TokenResponse,
    UserOut,
)
from app.services.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)

# No se revela si el error proviene del correo o la contraseña (RNF-06 / CA-02.3).
_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Correo electrónico o contraseña incorrectos.",
    headers={"WWW-Authenticate": "Bearer"},
)


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserOut)
def register(data: PacientRegisterRequest, db: Session = Depends(get_db)) -> User:
    """Registro de nuevo paciente (RF-01)."""
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
        role="paciente",
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
    except IntegrityError as exc:  # Defensa extra ante condiciones de carrera
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo electrónico o el DNI ya se encuentran registrados.",
        ) from exc
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Inicio de sesión con correo y contraseña (RF-02)."""
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if user is None or not verify_password(data.password, user.password_hash):
        raise _INVALID_CREDENTIALS
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Su cuenta se encuentra desactivada. Contacte al administrador.",
        )
    return TokenResponse(access_token=create_access_token(user))


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Cierre de sesión: invalida la sesión activa (RF-20 / CA-14.1)."""
    current_user.token_version += 1
    db.commit()
    logger.info("Sesión cerrada para el usuario %s.", current_user.id)
    return {"message": "Sesión cerrada correctamente."}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> User:
    """Información del usuario autenticado (apoyo a la interfaz)."""
    return current_user