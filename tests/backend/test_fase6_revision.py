"""Pruebas de FASE 6: revisión administrativa del triaje (RF-17 / HU-13 / CA-13.x).

- CA-13.1: el administrador marca un triaje como "revisado".
- CA-13.2: el administrador lo marca como "descartado".
- CA-13.3: paciente y profesional no pueden cambiar el estado (403).
- Un triaje recién creado nace como "pendiente".
"""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Cita, CitaEstado, Especialidad, Profesional, Triaje
from app.models.triage import TriajeEstadoRevision
from app.models.user import User, UserRole
from app.services.security import hash_password

PASSWORD = "ClaveSegura!1"


def _crear_usuario(db: Session, email: str, role: UserRole = UserRole.PACIENTE, dni: str = "20000001") -> User:
    user = User(
        email=email,
        password_hash=hash_password(PASSWORD),
        role=role,
        first_name="Prueba",
        last_name="Apellido",
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


def _fecha_futura() -> str:
    return (datetime.utcnow().date() + timedelta(days=30)).isoformat()


def _escenario_con_triaje(client: TestClient, db: Session, sintomas: list[dict] | None = None) -> tuple[int, str, str]:
    """Crea paciente+profesional+cita+triaje. Devuelve (triaje_id, paciente_token, admin_token)."""
    _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    paciente = _crear_usuario(db, "pac@test.com", UserRole.PACIENTE, "20000003")
    esp = Especialidad(nombre="Medicina General")
    db.add(esp)
    db.flush()
    prof_user = _crear_usuario(db, "doc@test.com", UserRole.PROFESIONAL, "20000004")
    profesional = Profesional(user_id=prof_user.id, specialty_id=esp.id)
    db.add(profesional)
    db.commit()
    db.refresh(esp)
    db.refresh(profesional)

    cita = Cita(
        paciente_id=paciente.id,
        professional_id=profesional.id,
        specialty_id=esp.id,
        fecha=datetime.strptime(_fecha_futura(), "%Y-%m-%d").date(),
        hora_inicio=datetime.strptime("10:00", "%H:%M").time(),
        hora_fin=datetime.strptime("10:30", "%H:%M").time(),
        estado=CitaEstado.RESERVADA.value,
        is_active=True,
    )
    db.add(cita)
    db.commit()
    db.refresh(cita)

    pac_tok = _token(client, "pac@test.com")
    resp = client.post(
        "/api/triage",
        json={"cita_id": cita.id, "sintomas": sintomas or [{"nombre": "tos", "severidad": "leve"}]},
        headers=_auth(pac_tok),
    )
    assert resp.status_code == 201, resp.text
    admin_tok = _token(client, "admin@test.com")
    return resp.json()["id"], pac_tok, admin_tok


def _revisar(client: TestClient, token: str, triaje_id: int, estado: str):
    return client.patch(f"/api/triage/{triaje_id}/revision", json={"estado": estado}, headers=_auth(token))


# ---------------------------------------------------------------------------
# Estado inicial
# ---------------------------------------------------------------------------
def test_triaje_nuevo_nace_pendiente(client: TestClient, db: Session) -> None:
    triaje_id, _, admin_tok = _escenario_con_triaje(client, db)

    lista = client.get("/api/triage", headers=_auth(admin_tok))
    assert lista.status_code == 200
    fila = [t for t in lista.json() if t["id"] == triaje_id][0]
    assert fila["estado_revision"] == TriajeEstadoRevision.PENDIENTE.value
    assert fila["estado_revision_label"] == "Pendiente de revisión"


# ---------------------------------------------------------------------------
# CA-13.1 — marca como revisado
# ---------------------------------------------------------------------------
def test_admin_marca_revisado_200(client: TestClient, db: Session) -> None:
    triaje_id, _, admin_tok = _escenario_con_triaje(client, db)

    resp = _revisar(client, admin_tok, triaje_id, "revisado")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["estado_revision"] == "revisado"
    assert body["estado_revision_label"] == "Revisado"
    assert body["clasificacion"] in {"alta", "media", "baja"}  # datos intactos

    guardado = db.scalar(select(Triaje).where(Triaje.id == triaje_id))
    assert guardado.estado_revision == "revisado"


# ---------------------------------------------------------------------------
# CA-13.2 — marca como descartado
# ---------------------------------------------------------------------------
def test_admin_marca_descartado_200(client: TestClient, db: Session) -> None:
    triaje_id, _, admin_tok = _escenario_con_triaje(client, db)

    resp = _revisar(client, admin_tok, triaje_id, "descartado")
    assert resp.status_code == 200, resp.text
    assert resp.json()["estado_revision"] == "descartado"

    guardado = db.scalar(select(Triaje).where(Triaje.id == triaje_id))
    assert guardado.estado_revision == "descartado"


def test_admin_cambia_estado_despues_de_revisar(client: TestClient, db: Session) -> None:
    triaje_id, _, admin_tok = _escenario_con_triaje(client, db)
    _revisar(client, admin_tok, triaje_id, "descartado")
    resp = _revisar(client, admin_tok, triaje_id, "revisado")  # reversión
    assert resp.status_code == 200
    assert resp.json()["estado_revision"] == "revisado"


# ---------------------------------------------------------------------------
# CA-13.3 — solo el administrador puede cambiar el estado
# ---------------------------------------------------------------------------
def test_paciente_no_puede_revisar_403(client: TestClient, db: Session) -> None:
    triaje_id, pac_tok, _ = _escenario_con_triaje(client, db)
    resp = _revisar(client, pac_tok, triaje_id, "revisado")
    assert resp.status_code == 403


def test_profesional_no_puede_revisar_403(client: TestClient, db: Session) -> None:
    triaje_id, _, _ = _escenario_con_triaje(client, db)
    doc_tok = _token(client, "doc@test.com")
    resp = _revisar(client, doc_tok, triaje_id, "descartado")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Casos inválidos
# ---------------------------------------------------------------------------
def test_triaje_inexistente_404(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000005")
    admin_tok = _token(client, "admin@test.com")
    resp = _revisar(client, admin_tok, 999999, "revisado")
    assert resp.status_code == 404


def test_estado_invalido_422(client: TestClient, db: Session) -> None:
    triaje_id, _, admin_tok = _escenario_con_triaje(client, db)
    resp = _revisar(client, admin_tok, triaje_id, "aprobado")
    assert resp.status_code == 422
    resp = _revisar(client, admin_tok, triaje_id, "")
    assert resp.status_code == 422


def test_sin_autenticacion_401(client: TestClient) -> None:
    resp = client.patch("/api/triage/1/revision", json={"estado": "revisado"})
    assert resp.status_code == 401