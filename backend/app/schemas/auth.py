"""Esquemas de autenticación y cuentas (FASE 2)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole

# Validaciones comunes (RNF-05)
EMAIL = r""
DNI_PATTERN = r"^\d{8}$"


def _validar_dni(value: str) -> str:
    value = value.strip()
    return value


class PacientRegisterRequest(BaseModel):
    """Formulario de registro de paciente (RF-01)."""

    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    dni: str = Field(min_length=8, max_length=8)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=20)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("dni")
    @classmethod
    def dni_8_digitos(cls, value: str) -> str:
        if not value.strip().isdigit() or len(value.strip()) != 8:
            raise ValueError("El DNI debe contener exactamente 8 dígitos")
        return value.strip()

    @field_validator("phone")
    @classmethod
    def phone_valido(cls, value: str) -> str:
        valor = value.strip()
        if not valor.isdigit() or len(valor) < 7:
            raise ValueError("El teléfono debe contener al menos 7 dígitos")
        return valor


class AdminUserCreateRequest(BaseModel):
    """Creación de cuenta por el administrador (RF-18)."""

    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    dni: str = Field(min_length=8, max_length=8)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=20)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.PACIENTE


class AdminUserUpdateRequest(BaseModel):
    """Edición de cuenta por el administrador (RF-18): desactivar, reasignar rol, datos."""

    first_name: str | None = Field(default=None, min_length=1, max_length=120)
    last_name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = Field(default=None, min_length=7, max_length=20)
    role: UserRole | None = None
    is_active: bool | None = None


class LoginRequest(BaseModel):
    """Credenciales de inicio de sesión (RF-02)."""

    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    """Token de acceso (RNF-01: sesión con expiración de 30 minutos)."""

    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    """Representación pública de un usuario (sin datos sensibles)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: UserRole
    first_name: str
    last_name: str
    dni: str
    phone: str
    is_active: bool
    created_at: datetime