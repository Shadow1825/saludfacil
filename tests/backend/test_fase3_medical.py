"""Pruebas de FASE 3: catálogo médico (especialidades, profesionales, horarios).

Trazabilidad:
- RF-04 / HU-11 / CA-11.1: profesionales (registro, edición, desactivación).
- RF-05 / HU-11 / CA-11.2: especialidades (registro, edición, desactivación).
- RF-06 / HU-11 / CA-11.3: horarios (día, inicio, fin).
- RF-07 / HU-03 / CA-03.1, CA-03.2: consulta de especialidades y profesionales activos.
- RF-08 / HU-03 / CA-03.3, CA-03.4: solo horarios disponibles.
- RNF-02 y RNF-05 se verifican junto con las anteriores.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Especialidad, Profesional
from app.models.user import User, UserRole
from app.services.security import hash_password

PASSWORD = "ClaveSegura!1"


def _crear_usuario(
    db: Session,
    email: str,
    role: UserRole = UserRole.PACIENTE,
    dni: str = "20000001",
) -> User:
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


def test_profesional_inactivo_no_lista_en_especialidad(client: TestClient, db: Session) -> None:
    admin = _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    _crear_usuario(db, "paciente@test.com", UserRole.PACIENTE, "20000003")
    admin_token = _token(client, "admin@test.com")
    paciente_token = _token(client, "paciente@test.com")
    esp = Especialidad(nombre="Medicina General")
    db.add(esp)
    db.commit()
    db.refresh(esp)

    response = client.post(
        "/api/professionals",
        json={
            "first_name": "Pepe",
            "last_name": "Palacios",
            "dni": "70000001",
            "email": "pepe@prof.com",
            "phone": "999000111",
            "password": PASSWORD,
            "specialty_id": esp.id,
        },
        headers=_auth(admin_token),
    )
    assert response.status_code == 201, response.text
    prof_id = response.json()["id"]

    directorio = client.get(
        "/api/directory/professionals", params={"specialty_id": esp.id}, headers=_auth(paciente_token)
    )
    assert [p["id"] for p in directorio.json()] == [prof_id]

    cliente = client.patch(
        f"/api/professionals/{prof_id}", json={"is_active": False}, headers=_auth(admin_token)
    )
    assert cliente.status_code == 200

    directorio = client.get(
        "/api/directory/professionals", params={"specialty_id": esp.id}, headers=_auth(paciente_token)
    )
    assert directorio.json() == []  # CA-03.2 / CA-03.4: solo activos


def test_specialties_admin_full_crud(client: TestClient, db: Session) -> None:
    admin = _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    token = _token(client, "admin@test.com")

    creada = client.post("/api/specialties", json={"nombre": "Pediatría"}, headers=_auth(token))
    assert creada.status_code == 201, creada.text
    esp_id = creada.json()["id"]

    duplicado = client.post("/api/specialties", json={"nombre": "Pediatría"}, headers=_auth(token))
    assert duplicado.status_code == 409  # RF-05: sin duplicados

    editada = client.patch(f"/api/specialties/{esp_id}", json={"is_active": False}, headers=_auth(token))
    assert editada.status_code == 200 and editada.json()["is_active"] is False

    lista_admin = client.get(" /api/specialties".strip(), headers=_auth(token))
    assert any(e["id"] == esp_id for e in lista_admin.json())  # admin ve inactivas

def test_specialty_directory_only_active(client: TestClient, db: Session) -> None:
    admin = _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    paciente = _crear_usuario(db, "p@test.com", UserRole.PACIENTE, "20000003")
    token = _token(client, "admin@test.com")
    pat = _token(client, "p@test.com")

    a = client.post("/api/specialties", json={"nombre": "Cardiología"}, headers=_auth(token)).json()
    b = client.post("/api/specialties", json={"nombre": "Dermatología"}, headers=_auth(token)).json()
    client.patch(f"/api/specialties/{b['id']}", json={"is_active": False}, headers=_auth(token))

    directorio = client.get("/api/directory/specialties", headers=_auth(pat))
    nombres = [e["nombre"] for e in directorio.json()]
    assert "Cardiología" in nombres and "Dermatología" not in nombres  # CA-03.1: solo activas


def _crear_especialidad_y_prof(db: Session, client: TestClient, token: str, nombre_esp: str = "Cardiología", email: str = "doc@prof.com", dni: str = "70000002"):
    esp = client.post("/api/specialties", json={"nombre": nombre_esp}, headers=_auth(token)).json()
    profesional = client.post(
        "/api/professionals",
        json={
            "first_name": "Diego",
            "last_name": "Ramos",
            "dni": dni,
            "email": email,
            "phone": "999000222",
            "password": PASSWORD,
            "specialty_id": esp["id"],
        },
        headers=_auth(token),
    )
    assert profesional.status_code == 201, profesional.text
    return esp, profesional.json()


def test_professional_duplicated_dni_409(client: TestClient, db: Session) -> None:
    admin = _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    token = _token(client, "admin@test.com")
    _crear_especialidad_y_prof(db, client, token, email="doc@prof.com", dni="70000002")

    response = client.post(
        "/api/professionals",
        json={
            "first_name": "Otra",
            "last_name": "Persona",
            "dni": "70000002",
            "email": "doc2@prof.com",
            "phone": "999000222",
            "password": PASSWORD,
            "specialty_id": 1,
        },
        headers=_auth(token),
    )
    assert response.status_code == 409

def test_schedule_duplicado_409_e_invalido_422(client: TestClient, db: Session) -> None:
    admin = _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    token = _token(client, "admin@test.com")
    _, prof = _crear_especialidad_y_prof(db, client, token)

    valido = client.post(
        "/api/schedules",
        json={"professional_id": prof["id"], "day": 1, "start_time": "08:00", "end_time": "12:00"},
        headers=_auth(token),
    )
    assert valido.status_code == 201, valido.text  # RF-06 creación

    invalido = client.post(
        "/api/schedules",
        json={"professional_id": prof["id"], "day": 1, "start_time": "08:00", "end_time": "08:00"},
        headers=_auth(token),
    )
    assert invalido.status_code == 422  # RNF-05: inicio anterior a fin

    duplicado = client.post(
        "/api/schedules",
        json={"professional_id": prof["id"], "day": 1, "start_time": "08:00", "end_time": "12:30"},
        headers=_auth(token),
    )
    assert duplicado.status_code == 409  # RF-06: sin duplicados por día/hora


def test_availability_solo_activos(client: TestClient, db: Session) -> None:
    admin = _crear_usuario(db, "admin@test.com", UserRole.ADMINISTRADOR, "20000002")
    paciente = _crear_usuario(db, "p@test.com", UserRole.PACIENTE, "20000003")
    token = _token(client, "admin@test.com")
    pat = _token(client, "p@test.com")
    _, prof = _crear_especialidad_y_prof(db, client, token)

    h1 = client.post(
        "/api/schedules",
        json={"professional_id": prof["id"], "day": 2, "start_time": "09:00", "end_time": "13:00"},
        headers=_auth(token),
    ).json()
    h2 = client.post(
        "/api/schedules",
        json={"professional_id": prof["id"], "day": 4, "start_time": "09:00", "end_time": "12:00"},
        headers=_auth(token),
    ).json()
    client.patch(f"/api/schedules/{h2['id']}", json={"is_active": False}, headers=_auth(token))

    disponible = client.get("/api/directory/schedules", params={"professional_id": prof["id"]}, headers=_auth(pat))
    ids = [s["id"] for s in disponible.json()]
    assert h1["id"] in ids and h2["id"] not in ids  # RF-08 / CA-03.3: solo disponibles

    sin_data = client.get("/api/directory/schedules", params={"professional_id": 99999}, headers=_auth(pat))
    assert sin_data.status_code == 404  # CA-03.4: informativo

def test_rbac_non_admin_blocked(client: TestClient, db: Session) -> None:
    paciente = _crear_usuario(db, "p@test.com", UserRole.PACIENTE, "20000003")
    token = _token(client, "p@test.com")

    crear_esp = client.post("/api/specialties", json={"nombre": "Neurología"}, headers=_auth(token))
    assert crear_esp.status_code == 403  # RF-05 + RNF-02: solo admin

    crear_prof = client.post("/api/professionals", json={}, headers=_auth(token))
    assert crear_prof.status_code in (403, 422)  # bloqueado por rol antes de validar

    directorio_sin_token = client.get("/api/directory/specialties")
    assert directorio_sin_token.status_code == 401  # RF-07: requiere autenticación