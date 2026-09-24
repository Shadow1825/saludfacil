"""Pruebas base de FASE 1.

El objetivo de esta etapa es comprobar la infraestructura mínima:
configuración, aplicación y endpoint de estado.
Las pruebas de requisitos (RF/RNF) se incorporan en fases posteriores.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint_returns_service_name() -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "SaludFácil API"


def test_api_docs_available() -> None:
    response = client.get("/docs")
    assert response.status_code in (200, 307)


def test_openapi_schema_contains_health() -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/api/health" in response.json()["paths"]


def test_health_endpoint_reports_status_and_service() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "saludfacil-api"
    assert body["database"] in ("ok", "unreachable")


def test_configuration_defaults() -> None:
    from app.core.config import Settings

    settings = Settings()
    assert settings.access_token_expire_minutes == 30
    assert settings.app_name == "SaludFácil API"