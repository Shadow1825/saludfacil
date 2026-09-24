"""Pruebas base de FASE 1.

Infraestructura mínima: configuración, aplicación y endpoint de estado.
Las pruebas de requisitos (RF/RNF) se incorporan en sus respectivas fases.
"""

from fastapi.testclient import TestClient


def test_root_endpoint_returns_service_name(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "SaludFácil API"


def test_api_docs_available(client: TestClient) -> None:
    response = client.get("/docs")
    assert response.status_code in (200, 307)


def test_openapi_schema_contains_health_and_auth(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/health" in paths
    assert "/api/auth/register" in paths


def test_health_endpoint_reports_status(client: TestClient) -> None:
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