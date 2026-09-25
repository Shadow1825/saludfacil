"""Esquemas del perfil del paciente (FASE 6 / RF-03 / HU-15 / CA-15.x).

Interpretación documentada (aprobada para FASE 6):
- El paciente actualiza únicamente sus propios datos: nombre, apellido,
  teléfono y, opcionalmente, su contraseña.
- DNI y correo electrónico son inmutables por el propio usuario (identidad y
  identificador de inicio de sesión); cualquier intento de enviarlos se rechaza
  con 422 (extra="forbid" → CA-15.3).
- Solicitudes sin campos editables se rechazan con 422.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProfileUpdateRequest(BaseModel):
    """Actualización del perfil del paciente (RF-03 / HU-15 / CA-15.x).

    - CA-15.1: permite actualizar los datos propios y devuelve los nuevos valores.
    - CA-15.2: validación de formato de teléfono (≥ 7 dígitos) y contraseña
      (mínimo 8 caracteres), igual que en el registro (RNF-05).
    - CA-15.3: los campos protegidos (DNI, correo) no se pueden modificar aquí.
    """

    model_config = ConfigDict(extra="forbid")  # rechaza dni/email → 422 (CA-15.3)

    first_name: str | None = Field(default=None, min_length=1, max_length=120)
    last_name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = Field(default=None, min_length=7, max_length=20)
    current_password: str | None = Field(default=None, min_length=1, max_length=128)
    new_password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("phone")
    @classmethod
    def phone_valido(cls, value: str | None) -> str | None:
        if value is None:
            return None
        valor = value.strip()
        if not valor.isdigit() or len(valor) < 7:
            raise ValueError("El teléfono debe contener al menos 7 dígitos")
        return valor

    @model_validator(mode="after")
    def _reglas_de_actualizacion(self) -> "ProfileUpdateRequest":
        if self.new_password is not None and self.current_password is None:
            raise ValueError(
                "Debe indicar su contraseña actual para cambiar la contraseña."
            )
        if self.new_password is None and self.current_password is not None:
            raise ValueError("Debe indicar la nueva contraseña.")
        if (
            self.first_name is None
            and self.last_name is None
            and self.phone is None
            and self.new_password is None
        ):
            raise ValueError("No hay datos para actualizar.")
        return self