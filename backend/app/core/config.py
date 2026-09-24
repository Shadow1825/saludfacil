"""Configuración centralizada de SaludFácil.

Los valores se cargan desde variables de entorno (`.env` en el entorno local).
Ver `.env.example` en la raíz del proyecto.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Nombre e identificación
    app_name: str = "SaludFácil API"
    app_version: str = "0.1.0"
    environment: str = "development"

    # Base de datos
    database_url: str = (
        "postgresql+psycopg://saludfacil:saludfacil_dev_password@localhost:5432/saludfacil"
    )

    # Autenticación (utilizados desde FASE 2, documentados ya para cumplir RNF-01)
    secret_key: str = "cambiar-este-secreto-en-produccion"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        """Orígenes permitidos como lista."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Instancia única (cacheada) de configuración."""
    return Settings()


settings = get_settings()