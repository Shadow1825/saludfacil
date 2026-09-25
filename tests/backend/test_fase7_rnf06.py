"""Pruebas de FASE 7 (RNF-06): los errores y logs no exponen datos personales
ni información interna.

Interpretación documentada:
- RNF-06: errores HTTP sin `input` (valores enviados) y sin trazas internas;
  excepciones no controladas devuelven 500 genérico y solo registran el tipo.
- RNF-07 (seguridad): cabeceras de seguridad en todas las respuestas.
"""

import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import unhandled_error_handler, validation_error_handler


# ---------------------------------------------------------------------------
# RNF-06: validación 422 sin eco de los valores enviados
# ---------------------------------------------------------------------------
def test_422_no_expone_valores_enviados(client: TestClient, db: Session) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "first_name": "Ana",
            "last_name": "Gómez",
            "dni": "12",  # inválido: el DNI debe tener 8 dígitos (RNF-05)
            "email": "correo.personal@test.com",
            "phone": "987654321",
            "password": "ClaveSecreta!1",
        },
    )
    assert response.status_code == 422

    body = response.json()
    assert isinstance(body["detail"], list)
    assert all("input" not in item for item in body["detail"])  # sin valores recibidos
    assert all("loc" not in item for item in body["detail"])  # solo field + message
    for item in body["detail"]:
        assert "field" in item
        assert "message" in item

    # El texto crudo no debe contener datos personales ni la contraseña enviada.
    raw = response.text
    assert "CorreoSecreto" not in raw and "correo.personal@test.com" not in raw
    assert "ClaveSecreta!1" not in raw


def test_422_error_desconocido_no_expone_valores(client: TestClient, db: Session) -> None:
    """Un campo inesperado (extra="forbid") tampoco devuelve el valor enviado."""
    from tests.backend.test_fase6_profile import PASSWORD, _crear_usuario, _token

    _crear_usuario(db, "pac@test.com")
    tok = _token(client, "pac@test.com")

    response = client.patch(
        "/api/profile",
        json={"phone": "987654321", "campo_secreto_interno": "valor-sensible"},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert response.status_code == 422
    assert "valor-sensible" not in response.text


# ---------------------------------------------------------------------------
# RNF-06: excepción no controlada -> 500 genérico sin información interna
# ---------------------------------------------------------------------------
def test_excepcion_no_controlada_500_generico() -> None:
    mini = FastAPI()
    mini.add_exception_handler(Exception, unhandled_error_handler)

    @mini.get("/explota")
    async def explota() -> None:
        raise RuntimeError("secreto interno BD: contraseña [Tok3n] de paciente 1")

    client_options = {"raise_server_exceptions": False}
    with TestClient(mini, **client_options) as test_client:
        response = test_client.get("/explota")
    assert response.status_code == 500
    assert response.json() == {"detail": "Error interno del servidor. Intente nuevamente."}
    # El cliente no ve el mensaje interno ni trazas.
    assert "secreto interno" not in response.text
    assert "RuntimeError" not in response.text
    assert "Traceback" not in response.text


def test_log_de_excepcion_solo_registra_el_tipo(caplog) -> None:
    mini = FastAPI()
    mini.add_exception_handler(Exception, unhandled_error_handler)

    @mini.get("/explota")
    async def explota() -> None:
        raise ValueError("quiebra plugin: dni 20000001 email x@y.com")

    with caplog.at_level(logging.ERROR):
        with TestClient(mini, raise_server_exceptions=False) as test_client:
            assert test_client.get("/explota").status_code == 500

    # Se registra el tipo de la excepción, nunca su mensaje ni argumentos (RNF-11).
    assert "ValueError" in caplog.text
    assert "quiebra plugin" not in caplog.text
    assert "20000001" not in caplog.text
    assert "x@y.com" not in caplog.text
    assert "Traceback" not in caplog.text


# ---------------------------------------------------------------------------
# RNF-07 (seguridad): cabeceras de seguridad en las respuestas
# ---------------------------------------------------------------------------
def test_cabeceras_de_seguridad(client: TestClient, db: Session) -> None:
    response = client.get("/api/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]

    # También en respuestas de error.
    error_response = client.post(
        "/api/auth/login", json={"email": "nobody@test.com", "password": "x"}
    )
    assert error_response.status_code == 401
    assert error_response.headers["X-Frame-Options"] == "DENY"