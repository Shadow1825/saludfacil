"""Seguridad: hash de contraseñas, tokens JWT y dependencias de autenticación.

Cumplimiento:
- RNF-01: hash con sal (bcrypt), nunca texto plano; expiración a los 30 minutos.
- RNF-02: el control de acceso se aplica en el servidor (403 si no autorizado).
- RF-19 / RF-20: RBAC por rol y cierre de sesión que invalida la sesión activa.
- RNF-06: los errores no revelan información interna.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserRole

_bearer = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Aplica hash con sal mediante bcrypt (RNF-01)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verifica una contraseña contra su hash almacenado."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user: User) -> str:
    """Crea un token JWT con expiración de 30 minutos (RNF-01).

    El token incluye la versión de sesión del usuario; al cerrar sesión (RF-20)
    se incrementa esa versión y el token deja de ser válido.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "role": user.role.value,
        "ver": user.token_version,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesión ha expirado. Inicie sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión inválida. Inicie sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Resuelve el usuario autenticado a partir del token (protección de endpoints)."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Debe iniciar sesión para acceder a este recurso.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = _decode_token(credentials.credentials)

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión inválida. Inicie sesión nuevamente.",
        ) from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no disponible. Contacte al administrador.",
        )

    # Invalidación por cierre de sesión (RF-20)
    if payload.get("ver") != user.token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesión fue cerrada. Inicie sesión nuevamente.",
        )

    return user


def require_roles(*roles: UserRole):
    """Dependencia de autorización por rol (RF-19 / RNF-02).

    Devuelve HTTP 403 cuando el usuario no tiene el rol requerido,
    incluso si acumula la solicitud directamente a la API.
    """

    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para realizar esta operación.",
            )
        return current_user

    return _dependency