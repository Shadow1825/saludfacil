"""Pruebas de FASE 4: citas médicas (reserva, consulta, cancelación, administración).

Trazabilidad:
- RF-09 / HU-04 / CA-04.1–04.4: reserva (bloquea el horario, confirma cita).
- RF-10 / HU-05 / CA-05.x: consulta de citas del paciente.
- RF-11 / HU-06 / CA-06.x: cancelación (libera el horario).
- RF-21 / HU-11 / CA-11.4: gestión de citas por el administrador.
- RNF-09: no citas en fechas pasadas ni horarios ocupados.
"""

from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Cita, CitaEstado
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


def _proxima_fecha_con_dia(day: int) -> date:
    """Fecha futura estricta cuyo día de semana es `day` (1=Lunes … 7=Domingo)."""
    hoy = datetime.utcnow().date()
    delta = (day - (hoy.weekday() + 1)) % 7
    if delta == 0:
        delta = 7
    return hoy + timedelta(days=delta)


def _crear_profesional_con_horario(
    client: TestClient, db: Session, token: str, dia: int, inicio: str = "08:00", fin: str = "12:00"
) -> tuple[int, int]:
    """Crea especialidad + profesional + horario activo para el día indicado."""
    esp = client.post("/api/specialties", json={"nombre": f"Especialidad {dia}"}, headers=_auth(token)).json()
    prof = client.post(
        "/api/professionals",
        json={
            "first_name": "Diego",
            "last_name": "Ramos",
            "dni": f"7000000{dia}",
            "email": f"doc{dia}@prof.com",
            "phone": "999000222",
            "password": PASSWORD,
            "specialty_id": esp["id"],
        },
        headers=_auth(token),
    ).json()
    horario = client.post(
        "/api/schedules",
        json={"professional_id": prof["id"], "day": dia, "start_time": inicio, "end_time": fin},
        headers=_auth(token),
    )
    assert horario.status_code == 201, horario.text
    return esp["id"], prof["id"]


def _setup_extras(
    client: TestClient, db: Session, admin_token: str, dia: int
) -> tuple[date, int, int]:
    fecha = _proxima_fecha_con_dia(dia)
    esp_id, prof_id = _crear_profesional_con_horario(client, db, admin_token, dia)
    return fecha, esp_id, prof_id


# --------------------------------------------------------------------------
# RF-09 / HU-04 — RESERVA
# --------------------------------------------------------------------------
def test_reserva_cita_exitosa(client: TestClient, db: Session) -> None:
    admin = _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    paciente = _crear_usuario(db, "paciente@test.com", UserRole.PACIENTE, "20000003")
    admin_tok = _token(client, "admin@test.com")
    paci_tok = _token(client, "paciente@test.com")

    dia = 1
    fecha, _, prof_id = _setup_extras(client, db, admin_tok, dia)

    response = client.post(
        "/api/appointments",
        json={"professional_id": prof_id, "fecha": fecha.isoformat(), "hora_inicio": "08:00"},
        headers=_auth(paci_tok),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["estado"] == "reservada"
    assert body["hora_inicio"] == "08:00" and body["hora_fin"] == "08:30"
    assert body["professional_id"] == prof_id
    assert body["paciente_id"] == paciente.id  # CA-04.1: confirma cita del paciente


def test_reserva_horario_ocupado_409(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    _crear_usuario(db, "p1@test.com", UserRole.PACIENTE, "20000003")
    _crear_usuario(db, "p2@test.com", UserRole.PACIENTE, "20000004")
    admin_tok = _token(client, "admin@test.com")
    p1 = _token(client, "p1@test.com")
    p2 = _token(client, "p2@test.com")

    fecha, _, prof_id = _setup_extras(client, db, admin_tok, 2)

    primero = client.post(
        "/api/appointments",
        json={"professional_id": prof_id, "fecha": fecha.isoformat(), "hora_inicio": "09:00"},
        headers=_auth(p1),
    )
    assert primero.status_code == 201, primero.text

    segundo = client.post(
        "/api/appointments",
        json={"professional_id": prof_id, "fecha": fecha.isoformat(), "hora_inicio": "09:00"},
        headers=_auth(p2),
    )
    assert segundo.status_code == 409  # CA-04.2 / RNF-09: horario bloqueado


def test_reserva_fecha_pasada_422(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    _crear_usuario(db, "p@test.com", UserRole.PACIENTE, "20000003")
    admin_tok = _token(client, "admin@test.com")
    p = _token(client, "p@test.com")

    _, _, prof_id = _setup_extras(client, db, admin_tok, 3)
    ayer = (datetime.utcnow().date() - timedelta(days=1)).isoformat()

    response = client.post(
        "/api/appointments",
        json={"professional_id": prof_id, "fecha": ayer, "hora_inicio": "08:00"},
        headers=_auth(p),
    )
    assert response.status_code == 422  # RNF-09: no fechas pasadas


def test_reserva_hora_no_ofertada_422(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    _crear_usuario(db, "p@test.com", UserRole.PACIENTE, "20000003")
    admin_tok = _token(client, "admin@test.com")
    p = _token(client, "p@test.com")

    fecha, _, prof_id = _setup_extras(client, db, admin_tok, 4)

    response = client.post(
        "/api/appointments",
        json={"professional_id": prof_id, "fecha": fecha.isoformat(), "hora_inicio": "13:00"},
        headers=_auth(p),
    )
    assert response.status_code == 422  # fuera del horario de atención (08:00-12:00)


def test_reserva_solo_paciente_403(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    _crear_usuario(db, "p@test.com", UserRole.PACIENTE, "20000003")
    admin_tok = _token(client, "admin@test.com")

    fecha, _, prof_id = _setup_extras(client, db, admin_tok, 5)

    response = client.post(
        "/api/appointments",
        json={"professional_id": prof_id, "fecha": fecha.isoformat(), "hora_inicio": "08:00"},
        headers=_auth(admin_tok),
    )
    assert response.status_code == 403  # RF-09: solo el rol paciente reserva


# --------------------------------------------------------------------------
# RF-10 / HU-05 — CONSULTA
# --------------------------------------------------------------------------
def test_mis_citas_solo_propias(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    _crear_usuario(db, "p1@test.com", UserRole.PACIENTE, "20000003")
    _crear_usuario(db, "p2@test.com", UserRole.PACIENTE, "20000004")
    admin_tok = _token(client, "admin@test.com")
    p1 = _token(client, "p1@test.com")
    p2 = _token(client, "p2@test.com")

    fecha, _, prof_id = _setup_extras(client, db, admin_tok, 1)

    client.post(
        "/api/appointments",
        json={"professional_id": prof_id, "fecha": fecha.isoformat(), "hora_inicio": "08:00"},
        headers=_auth(p1),
    )

    citas_p1 = client.get("/api/appointments", headers=_auth(p1))
    assert citas_p1.status_code == 200
    assert len(citas_p1.json()) == 1

    citas_p2 = client.get("/api/appointments", headers=_auth(p2))
    assert citas_p2.status_code == 200
    assert citas_p2.json() == []  # CA-05.1: cada paciente ve solo las suyas


def test_profesional_consulta_sus_citas(client: TestClient, db: Session) -> None:
    admin = _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    _crear_usuario(db, "p1@test.com", UserRole.PACIENTE, "20000003")
    admin_tok = _token(client, "admin@test.com")
    p1 = _token(client, "p1@test.com")

    dia = 3
    fecha, _, prof_id = _setup_extras(client, db, admin_tok, dia)
    prof_tok = _token(client, f"doc{dia}@prof.com")

    cita = client.post(
        "/api/appointments",
        json={"professional_id": prof_id, "fecha": fecha.isoformat(), "hora_inicio": "08:00"},
        headers=_auth(p1),
    )
    assert cita.status_code == 201, cita.text

    # RF-14 / HU-08: el profesional consulta solo las citas que tiene asignadas.
    mis_citas = client.get("/api/appointments", headers=_auth(prof_tok))
    assert mis_citas.status_code == 200, mis_citas.text
    citas = mis_citas.json()
    assert len(citas) == 1
    assert citas[0]["professional_id"] == prof_id
    assert citas[0]["paciente"]  # el paciente aparece en el detalle de la cita


# --------------------------------------------------------------------------
# RF-11 / HU-06 — CANCELACIÓN (libera horario)
# --------------------------------------------------------------------------
def test_cancelacion_libera_horario(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    _crear_usuario(db, "p1@test.com", UserRole.PACIENTE, "20000003")
    _crear_usuario(db, "p2@test.com", UserRole.PACIENTE, "20000004")
    admin_tok = _token(client, "admin@test.com")
    p1 = _token(client, "p1@test.com")
    p2 = _token(client, "p2@test.com")

    fecha, _, prof_id = _setup_extras(client, db, admin_tok, 2)

    cita = client.post(
        "/api/appointments",
        json={"professional_id": prof_id, "fecha": fecha.isoformat(), "hora_inicio": "10:00"},
        headers=_auth(p1),
    ).json()

    otro_paciente = client.post(f"/api/appointments/{cita['id']}/cancel", headers=_auth(p2))
    assert otro_paciente.status_code == 403  # CA-06.2: solo el dueño (o admin)

    cancelada = client.post(f"/api/appointments/{cita['id']}/cancel", headers=_auth(p1))
    assert cancelada.status_code == 200, cancelada.text

    doble = client.post(f"/api/appointments/{cita['id']}/cancel", headers=_auth(p1))
    assert doble.status_code == 409  # ya no está reservada

    re_reserva = client.post(
        "/api/appointments",
        json={"professional_id": prof_id, "fecha": fecha.isoformat(), "hora_inicio": "10:00"},
        headers=_auth(p2),
    )
    assert re_reserva.status_code == 201  # CA-06.3: el horario se liberó


# --------------------------------------------------------------------------
# RF-21 / HU-11 / CA-11.4 — ADMINISTRACIÓN
# --------------------------------------------------------------------------
def test_admin_ve_y_gestiona_todas_las_citas(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    _crear_usuario(db, "p1@test.com", UserRole.PACIENTE, "20000003")
    _crear_usuario(db, "p2@test.com", UserRole.PACIENTE, "20000004")
    admin_tok = _token(client, "admin@test.com")
    p1 = _token(client, "p1@test.com")
    p2 = _token(client, "p2@test.com")

    f1, _, prof_a = _setup_extras(client, db, admin_tok, 3)
    f2, _, prof_b = _setup_extras(client, db, admin_tok, 5)

    client.post(
        "/api/appointments",
        json={"professional_id": prof_a, "fecha": f1.isoformat(), "hora_inicio": "08:00"},
        headers=_auth(p1),
    )
    cita_b = client.post(
        "/api/appointments",
        json={"professional_id": prof_b, "fecha": f2.isoformat(), "hora_inicio": "09:00"},
        headers=_auth(p2),
    ).json()

    todas = client.get("/api/appointments", headers=_auth(admin_tok))
    assert todas.status_code == 200
    assert len(todas.json()) == 2  # CA-11.4: el admin ve todo el sistema

    patch_estado = client.patch(
        f"/api/appointments/{cita_b['id']}", json={"estado": "no_asistio"}, headers=_auth(admin_tok)
    )
    assert patch_estado.status_code == 200

    admin_cancela = client.post(f"/api/appointments/{cita_b['id']}/cancel", headers=_auth(admin_tok))
    assert admin_cancela.status_code == 409  # ya no está reservada (cambio previo)

    persistida = db.get(Cita, cita_b["id"])
    assert persistida is not None
    assert persistida.estado == CitaEstado.NO_ASISTIO.value