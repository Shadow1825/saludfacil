"""Pruebas de FASE 5: triaje inicial (RF-12 a RF-16).

Cubre las reglas oficiales R1-R6, su precedencia (Alta → Media → Baja), el
determinismo (RF-16 / CA-10.x), los casos inválidos (CA-07.x) y el control de
acceso por rol (RF-13/RF-14 / CA-08.x).
"""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Cita, CitaEstado, Especialidad, Profesional, Triaje
from app.models.user import User, UserRole
from app.services.security import hash_password
from app.services.triage import (
    CLASIFICACION_ALTA,
    CLASIFICACION_BAJA,
    CLASIFICACION_MEDIA,
    clasificar,
)

PASSWORD = "ClaveSegura!1"
HN = {"nombre": "algo", "severidad": "leve"}


# ---------------------------------------------------------------------------
# Reglas R1-R6 del motor de clasificación (unitarias, sin BD)
# ---------------------------------------------------------------------------
def test_r1_dificultad_respiratoria_intensa_alta() -> None:
    assert clasificar([{"nombre": "dificultad respiratoria", "severidad": "intensa"}]) == CLASIFICACION_ALTA


def test_r2_dolor_toracico_intenso_alta() -> None:
    assert clasificar([{"nombre": "DOLOR TORÁCICO", "severidad": "intensa"}]) == CLASIFICACION_ALTA


def test_r3_perdida_de_conciencia_alta() -> None:
    assert clasificar([{"nombre": "  pérdida de conciencia ", "severidad": "intensa"}]) == CLASIFICACION_ALTA


def test_r4_dos_sintomas_moderados_media() -> None:
    sintomas = [{"nombre": "fiebre", "severidad": "moderada"}, {"nombre": "cefalea", "severidad": "moderada"}]
    assert clasificar(sintomas) == CLASIFICACION_MEDIA


def test_r5_un_sintoma_moderado_media() -> None:
    sintomas = [{"nombre": "dolor abdominal", "severidad": "moderada"}, {"nombre": "tos", "severidad": "leve"}]
    assert clasificar(sintomas) == CLASIFICACION_MEDIA


def test_r6_solo_sintomas_leves_baja() -> None:
    sintomas = [{"nombre": "tos", "severidad": "leve"}, {"nombre": "congestión nasal", "severidad": "leve"}]
    assert clasificar(sintomas) == CLASIFICACION_BAJA


def test_precedencia_alta_descarta_media_y_leves() -> None:
    # R1/R2/R3 deben ganar aunque haya moderados y leves (Alta → Media → Baja).
    sintomas = [
        {"nombre": "dificultad respiratoria", "severidad": "intensa"},
        {"nombre": "fiebre", "severidad": "moderada"},
        {"nombre": "fiebre", "severidad": "leve"},
    ]
    assert clasificar(sintomas) == CLASIFICACION_ALTA


def test_precedencia_media_refuerza_y_sobre_leves() -> None:
    assert (
        clasificar(
            [
                {"nombre": "fiebre", "severidad": "moderada"},
                {"nombre": "fiebre", "severidad": "moderada"},
                {"nombre": "tos", "severidad": "leve"},
            ]
        )
        == CLASIFICACION_MEDIA  # R4
    )
    assert (
        clasificar([{"nombre": "cefalea", "severidad": "moderada"}, {"nombre": "tos", "severidad": "leve"}])
        == CLASIFICACION_MEDIA  # R5
    )


def test_determinismo_mismos_datos_mismo_resultado() -> None:
    sintomas = [{"nombre": "Fiebre", "severidad": "moderada"}, {"nombre": "tos", "severidad": "leve"}]
    primero = clasificar(sintomas)
    segundo = clasificar(
        [{"nombre": "   FIEBRE  ", "severidad": "moderada"}, {"nombre": "  tos ", "severidad": "leve"}]
    )
    assert primero == segundo == CLASIFICACION_MEDIA  # RF-16 / CA-10.x


# ---------------------------------------------------------------------------
# Datos de apoyo
# ---------------------------------------------------------------------------
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


def _especialidad_y_profesional(db: Session, email: str, dni: str) -> tuple[int, int, int, Especialidad]:
    """Crea especialidad + profesional (directo en BD) y devuelve (esp, prof, prof_user, especialidad)."""
    esp = Especialidad(nombre=f"Especialidad {dni}")
    db.add(esp)
    db.flush()
    prof_user = _crear_usuario(db, email, UserRole.PROFESIONAL, dni)
    profesional = Profesional(user_id=prof_user.id, specialty_id=esp.id)
    db.add(profesional)
    db.commit()
    db.refresh(esp)
    db.refresh(profesional)
    return esp.id, profesional.id, prof_user.id, esp


def _crear_cita(
    db: Session,
    paciente_id: int,
    professional_id: int,
    specialty_id: int,
    fecha: str,
    estado: str = CitaEstado.RESERVADA.value,
    is_active: bool = True,
) -> Cita:
    hora = datetime.strptime("10:00", "%H:%M").time()
    cita = Cita(
        paciente_id=paciente_id,
        professional_id=professional_id,
        specialty_id=specialty_id,
        fecha=datetime.strptime(fecha, "%Y-%m-%d").date(),
        hora_inicio=hora,
        hora_fin=datetime.strptime("10:30", "%H:%M").time(),
        estado=estado,
        is_active=is_active,
    )
    db.add(cita)
    db.commit()
    db.refresh(cita)
    return cita


def _post_triaje(client: TestClient, token: str, cita_id: int, sintomas: list[dict]):
    return client.post("/api/triage", json={"cita_id": cita_id, "sintomas": sintomas}, headers=_auth(token))


# ---------------------------------------------------------------------------
# RF-12 / HU-07 / CA-07.x — REGISTRO Y CLASIFICACIÓN
# ---------------------------------------------------------------------------
def test_registro_triaje_alta_201(client: TestClient, db: Session) -> None:
    admin = _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    paciente = _crear_usuario(db, "pac@test.com", UserRole.PACIENTE, "20000003")
    esp_id, prof_id, _, _ = _especialidad_y_profesional(db, "doc@test.com", "20000004")
    cita = _crear_cita(db, paciente.id, prof_id, esp_id, _fecha_futura())
    tok = _token(client, "pac@test.com")

    resp = _post_triaje(client, tok, cita.id, [{"nombre": "Pérdida de conciencia", "severidad": "intensa"}])

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["clasificacion"] == "alta"  # R3
    assert body["resultado"] == "Alta"
    assert body["paciente_id"] == paciente.id  # asociado al paciente
    assert body["cita_id"] == cita.id  # asociado al proceso/cita
    assert body["es_diagnostico"] is False  # clasificación inicial, no diagnóstico
    assert "no constituye un diagnóstico" in body["mensaje"]
    guardado = db.scalar(__import__("sqlalchemy").select(Triaje).where(Triaje.cita_id == cita.id))
    assert guardado is not None and guardado.clasificacion == "alta"


def test_registro_triaje_media_por_dos_moderados() -> None:
    sintomas = [{"nombre": "fiebre", "severidad": "moderada"}, {"nombre": "dolor abdominal", "severidad": "moderada"}]
    assert clasificar(sintomas) == CLASIFICACION_MEDIA  # R4


def test_registro_triaje_baja_solo_leves() -> None:
    sintomas = [{"nombre": "tos", "severidad": "leve"}, {"nombre": "congestión nasal", "severidad": "leve"}]
    assert clasificar(sintomas) == CLASIFICACION_BAJA  # R6


def test_registro_triaje_cita_de_otro_paciente_403(client: TestClient, db: Session) -> None:
    admin = _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    p1 = _crear_usuario(db, "p1@test.com", UserRole.PACIENTE, "20000003")
    p2 = _crear_usuario(db, "p2@test.com", UserRole.PACIENTE, "20000004")
    esp_id, prof_id, _, _ = _especialidad_y_profesional(db, "doc@test.com", "20000005")
    cita = _crear_cita(db, p1.id, prof_id, esp_id, _fecha_futura())
    tok2 = _token(client, "p2@test.com")

    resp = _post_triaje(client, tok2, cita.id, [{"nombre": "tos", "severidad": "leve"}])
    assert resp.status_code == 403  # no es su cita


def test_registro_triaje_rol_no_paciente_403(client: TestClient, db: Session) -> None:
    admin = _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    p = _crear_usuario(db, "pac@test.com", UserRole.PACIENTE, "20000003")
    esp_id, prof_id, _, _ = _especialidad_y_profesional(db, "doc@test.com", "20000004")
    cita = _crear_cita(db, p.id, prof_id, esp_id, _fecha_futura())
    admin_tok = _token(client, "admin@test.com")

    resp = _post_triaje(client, admin_tok, cita.id, [{"nombre": "tos", "severidad": "leve"}])
    assert resp.status_code == 403  # solo el rol paciente registra triaje


def test_registro_triaje_sintomas_vacios_422(client: TestClient, db: Session) -> None:
    admin = _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    p = _crear_usuario(db, "pac@test.com", UserRole.PACIENTE, "20000003")
    esp_id, prof_id, _, _ = _especialidad_y_profesional(db, "doc@test.com", "20000004")
    cita = _crear_cita(db, p.id, prof_id, esp_id, _fecha_futura())
    tok = _token(client, "pac@test.com")

    resp = _post_triaje(client, tok, cita.id, [])
    assert resp.status_code == 422  # CA-07.3: al menos un síntoma

    resp = client.post("/api/triage", json={"cita_id": cita.id}, headers=_auth(tok))
    assert resp.status_code == 422  # campo sintomas obligatorio


def test_registro_triaje_sintoma_invalido_422(client: TestClient, db: Session) -> None:
    admin = _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    p = _crear_usuario(db, "pac@test.com", UserRole.PACIENTE, "20000003")
    esp_id, prof_id, _, _ = _especialidad_y_profesional(db, "doc@test.com", "20000004")
    cita = _crear_cita(db, p.id, prof_id, esp_id, _fecha_futura())
    tok = _token(client, "pac@test.com")

    assert _post_triaje(client, tok, cita.id, [{"nombre": "", "severidad": "leve"}]).status_code == 422
    assert _post_triaje(client, tok, cita.id, [{"nombre": "tos", "severidad": "extrema"}]).status_code == 422
    assert _post_triaje(client, tok, cita.id, [{"nombre": "tos"}]).status_code == 422


def test_registro_triaje_intensa_no_canonica_422(client: TestClient, db: Session) -> None:
    admin = _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    p = _crear_usuario(db, "pac@test.com", UserRole.PACIENTE, "20000003")
    esp_id, prof_id, _, _ = _especialidad_y_profesional(db, "doc@test.com", "20000004")
    cita = _crear_cita(db, p.id, prof_id, esp_id, _fecha_futura())
    tok = _token(client, "pac@test.com")

    # "intensa" solo corresponde a los síntomas de R1-R3 (especificación oficial).
    resp = _post_triaje(client, tok, cita.id, [{"nombre": "dolor de cabeza", "severidad": "intensa"}])
    assert resp.status_code == 422
    # Los canónicos solo aceptan severidad "intensa".
    resp = _post_triaje(client, tok, cita.id, [{"nombre": "dificultad respiratoria", "severidad": "leve"}])
    assert resp.status_code == 422


def test_registro_triaje_cita_cancelada_o_pasada_422(client: TestClient, db: Session) -> None:
    admin = _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    p = _crear_usuario(db, "pac@test.com", UserRole.PACIENTE, "20000003")
    esp_id, prof_id, _, _ = _especialidad_y_profesional(db, "doc@test.com", "20000004")
    tok = _token(client, "pac@test.com")
    futura = _fecha_futura()

    cancelada = _crear_cita(db, p.id, prof_id, esp_id, futura, estado=CitaEstado.CANCELADA.value, is_active=False)
    assert _post_triaje(client, tok, cancelada.id, [{"nombre": "tos", "severidad": "leve"}]).status_code == 422

    pasada = _crear_cita(db, p.id, prof_id, esp_id, (datetime.utcnow().date() - timedelta(days=5)).isoformat())
    assert _post_triaje(client, tok, pasada.id, [{"nombre": "tos", "severidad": "leve"}]).status_code == 422


def test_registro_triaje_cita_inexistente_404(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "pac@test.com", UserRole.PACIENTE, "20000003")
    tok = _token(client, "pac@test.com")
    resp = _post_triaje(client, tok, 999999, [{"nombre": "tos", "severidad": "leve"}])
    assert resp.status_code == 404


def test_registro_triaje_duplicado_por_cita_409(client: TestClient, db: Session) -> None:
    admin = _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    p = _crear_usuario(db, "pac@test.com", UserRole.PACIENTE, "20000003")
    esp_id, prof_id, _, _ = _especialidad_y_profesional(db, "doc@test.com", "20000004")
    cita = _crear_cita(db, p.id, prof_id, esp_id, _fecha_futura())
    tok = _token(client, "pac@test.com")

    primero = _post_triaje(client, tok, cita.id, [{"nombre": "tos", "severidad": "leve"}])
    assert primero.status_code == 201
    segundo = _post_triaje(client, tok, cita.id, [{"nombre": "fiebre", "severidad": "moderada"}])
    assert segundo.status_code == 409  # uno por cita


# ---------------------------------------------------------------------------
# RF-13 / RF-14 / HU-08 / CA-08.x — CONSULTA Y ACCESO POR ROL
# ---------------------------------------------------------------------------
def _dos_escenarios(client: TestClient, db: Session):
    _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    p1 = _crear_usuario(db, "p1@test.com", UserRole.PACIENTE, "20000003")
    p2 = _crear_usuario(db, "p2@test.com", UserRole.PACIENTE, "20000004")
    esp_a, prof_a, _, _ = _especialidad_y_profesional(db, "doca@test.com", "20000005")
    esp_b, prof_b, _, _ = _especialidad_y_profesional(db, "docb@test.com", "20000006")
    cita_a = _crear_cita(db, p1.id, prof_a, esp_a, _fecha_futura())
    cita_b = _crear_cita(db, p2.id, prof_b, esp_b, _fecha_futura())
    tok1 = _token(client, "p1@test.com")
    tok2 = _token(client, "p2@test.com")
    assert _post_triaje(client, tok1, cita_a.id, [{"nombre": "tos", "severidad": "leve"}]).status_code == 201
    assert _post_triaje(client, tok2, cita_b.id, [{"nombre": "dificultad respiratoria", "severidad": "intensa"}]).status_code == 201
    return p1, cita_a, cita_b, tok1, tok2


def _triaje_de_cita(db: Session, cita_id: int) -> Triaje:
    return db.execute(__import__("sqlalchemy").select(Triaje).where(Triaje.cita_id == cita_id)).scalar_one()


def test_paciente_consulta_solo_sus_triajes(client: TestClient, db: Session) -> None:
    _, cita_a, _, tok1, _ = _dos_escenarios(client, db)
    triaje_a = _triaje_de_cita(db, cita_a.id)

    detalle = client.get(f"/api/triage/{triaje_a.id}", headers=_auth(tok1))
    assert detalle.status_code == 200
    assert detalle.json()["clasificacion"] == "baja"

    lista = client.get("/api/triage", headers=_auth(tok1))
    assert lista.status_code == 200
    body = lista.json()
    assert len(body) == 1  # CA-08.1: solo los suyos
    assert body[0]["clasificacion"] == "baja"


def test_paciente_consulta_detalle_ajeno_403(client: TestClient, db: Session) -> None:
    _, _, cita_b, tok1, _ = _dos_escenarios(client, db)
    triaje_b = _triaje_de_cita(db, cita_b.id)  # triaje de otro paciente
    resp = client.get(f"/api/triage/{triaje_b.id}", headers=_auth(tok1))
    assert resp.status_code == 403


def test_profesional_consulta_solo_triajes_de_sus_citas(client: TestClient, db: Session) -> None:
    _, _, cita_b, _, _ = _dos_escenarios(client, db)
    docA_tok = _token(client, "doca@test.com")

    lista = client.get("/api/triage", headers=_auth(docA_tok))
    assert lista.status_code == 200
    body = lista.json()
    assert len(body) == 1  # RF-14: solo las citas del profesional A
    assert body[0]["clasificacion"] == "baja"

    # No puede consultar el triaje de la cita de otro profesional.
    triaje_b = _triaje_de_cita(db, cita_b.id)
    resp = client.get(f"/api/triage/{triaje_b.id}", headers=_auth(docA_tok))
    assert resp.status_code == 403


def test_admin_consulta_todos_los_triajes(client: TestClient, db: Session) -> None:
    _dos_escenarios(client, db)
    admin_tok = _token(client, "admin@test.com")
    lista = client.get("/api/triage", headers=_auth(admin_tok))
    assert lista.status_code == 200
    assert len(lista.json()) == 2  # el admin ve el sistema completo


def test_profesional_sin_registro_asociado_403(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "solodoc@test.com", UserRole.PROFESIONAL, "20000007")  # sin fila en profesionales
    tok = _token(client, "solodoc@test.com")
    resp = client.get("/api/triage", headers=_auth(tok))
    assert resp.status_code == 403