"""Pruebas de FASE 6: perfil del paciente (RF-03 / HU-15 / CA-15.x).

Interpretación documentada: el paciente actualiza nombre, apellido, teléfono y,
opcionalmente, contraseña. DNI y correo son inmutables por el propio usuario
(CA-15.3). La sesión activa se mantiene tras cambiar la contraseña.
"""

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User
from app.models.user import UserRole
from app.services.security import hash_password, verify_password

PASSWORD = "ClaveSegura!1"
NUEVA_CLAVE = "NuevaClaveSegura!2"


def _crear_usuario(db: Session, email: str, role: UserRole = UserRole.PACIENTE, dni: str = "20000001") -> User:
    user = User(
        email=email,
        password_hash=hash_password(PASSWORD),
        role=role,
        first_name="Paciente",
        last_name="Prueba",
        dni=dni,
        phone="999000001",
        is_active=True,
        token_version=0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _token(client: TestClient, email: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _patch(client: TestClient, token: str, body: dict):
    return client.patch("/api/profile", json=body, headers=_auth(token))


# ---------------------------------------------------------------------------
# CA-15.1 — actualización de datos propios
# ---------------------------------------------------------------------------
def test_actualiza_nombre_apellido_y_telefono(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "pac@test.com", UserRole.PACIENTE, "20000010")
    tok = _token(client, "pac@test.com")

    resp = _patch(
        client,
        tok,
        {"first_name": "  Ana  ", "last_name": "Gómez", "phone": "987654321"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["first_name"] == "Ana"  # se recortan espacios
    assert body["last_name"] == "Gómez"
    assert body["phone"] == "987654321"

    guardado = db.scalar(select(User).where(User.email == "pac@test.com"))
    assert guardado.first_name == "Ana"
    assert guardado.last_name == "Gómez"
    assert guardado.phone == "987654321"


def test_actualiza_solo_un_campo_o_dos(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "pac@test.com", UserRole.PACIENTE, "20000011")
    tok = _token(client, "pac@test.com")

    resp = _patch(client, tok, {"phone": "911223344"})
    assert resp.status_code == 200
    assert resp.json()["phone"] == "911223344"
    assert resp.json()["first_name"] == "Paciente"  # el resto no cambia

    resp = _patch(client, tok, {"first_name": "María", "last_name": "López"})
    assert resp.status_code == 200
    assert resp.json()["first_name"] == "María"
    assert resp.json()["last_name"] == "López"


def test_patch_incluye_campos_inalterables(client: TestClient, db: Session) -> None:
    """DNI y correo se devuelven intactos tras actualizar otros campos."""
    _crear_usuario(db, "pac@test.com", UserRole.PACIENTE, "20000012")
    tok = _token(client, "pac@test.com")

    resp = _patch(client, tok, {"phone": "955667788"})
    assert resp.status_code == 200
    assert resp.json()["dni"] == "20000012"
    assert resp.json()["email"] == "pac@test.com"


# ---------------------------------------------------------------------------
# CA-15.2 — validación de formato
# ---------------------------------------------------------------------------
def test_telefono_invalido_422(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "pac@test.com", UserRole.PACIENTE, "20000013")
    tok = _token(client, "pac@test.com")

    assert _patch(client, tok, {"phone": "123"}).status_code == 422  # muy corto
    assert _patch(client, tok, {"phone": "holamundo"}).status_code == 422  # no numérico
    assert _patch(client, tok, {"first_name": ""}).status_code == 422


def test_peticion_vacia_422(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "pac@test.com", UserRole.PACIENTE, "20000014")
    tok = _token(client, "pac@test.com")

    assert _patch(client, tok, {}).status_code == 422  # nada que actualizar


# ---------------------------------------------------------------------------
# CA-15.3 — campos protegidos (DNI/email) no editables por el propio usuario
# ---------------------------------------------------------------------------
def test_intento_cambiar_dni_422(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "pac@test.com", UserRole.PACIENTE, "20000015")
    tok = _token(client, "pac@test.com")

    resp = _patch(client, tok, {"dni": "12345678"})
    assert resp.status_code == 422  # extra="forbid"


def test_intento_cambiar_email_422(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "pac@test.com", UserRole.PACIENTE, "20000016")
    tok = _token(client, "pac@test.com")

    resp = _patch(client, tok, {"email": "otro@test.com"})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Cambio de contraseña (CA-15.2 / decisión documentada: la sesión se mantiene)
# ---------------------------------------------------------------------------
def test_cambio_de_contraseña_con_clave_actual(client: TestClient, db: Session) -> None:
    usuario = _crear_usuario(db, "pac@test.com", UserRole.PACIENTE, "20000017")
    tok = _token(client, "pac@test.com")

    resp = _patch(client, tok, {"current_password": PASSWORD, "new_password": NUEVA_CLAVE})
    assert resp.status_code == 200, resp.text
    assert resp.json()["first_name"] == "Paciente"

    db.expire_all()  # relee desde la BD (evita la caché de identidad de la sesión)
    guardado = db.scalar(select(User).where(User.email == "pac@test.com"))
    assert verify_password(NUEVA_CLAVE, guardado.password_hash)

    # Se puede iniciar sesión con la nueva contraseña.
    nuevo = client.post("/api/auth/login", json={"email": "pac@test.com", "password": NUEVA_CLAVE})
    assert nuevo.status_code == 200
    # La antigua ya no funciona.
    viejo = client.post("/api/auth/login", json={"email": "pac@test.com", "password": PASSWORD})
    assert viejo.status_code == 401


def test_cambio_contraseña_con_clave_actual_incorrecta_422(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "pac@test.com", UserRole.PACIENTE, "20000018")
    tok = _token(client, "pac@test.com")

    resp = _patch(client, tok, {"current_password": "ClaveEquivocada!9", "new_password": NUEVA_CLAVE})
    assert resp.status_code == 422


def test_cambio_contraseña_sin_clave_actual_422(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "pac@test.com", UserRole.PACIENTE, "20000019")
    tok = _token(client, "pac@test.com")

    assert _patch(client, tok, {"new_password": NUEVA_CLAVE}).status_code == 422
    assert _patch(client, tok, {"current_password": PASSWORD}).status_code == 422


def test_la_sesion_se_mantiene_tras_cambiar_la_contraseña(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "pac@test.com", UserRole.PACIENTE, "20000020")
    tok = _token(client, "pac@test.com")

    _patch(client, tok, {"current_password": PASSWORD, "new_password": NUEVA_CLAVE})
    me = client.get("/api/auth/me", headers=_auth(tok))
    assert me.status_code == 200  # decisión documentada: sesión vigente


# ---------------------------------------------------------------------------
# RBAC y autenticación
# ---------------------------------------------------------------------------
def test_rol_no_paciente_403(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000021")
    _crear_usuario(db, "doc@test.com", UserRole.PROFESIONAL, "20000022")
    admin_tok = _token(client, "admin@test.com")
    doc_tok = _token(client, "doc@test.com")

    assert _patch(client, admin_tok, {"phone": "999888777"}).status_code == 403  # RF-03 es del paciente
    assert _patch(client, doc_tok, {"phone": "999888777"}).status_code == 403


def test_sin_autenticacion_401(client: TestClient) -> None:
    resp = client.patch("/api/profile", json={"phone": "999888777"})
    assert resp.status_code == 401