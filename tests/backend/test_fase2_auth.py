"""Pruebas de FASE 2: autenticaciÃ³n, registro, RBAC, logout y validaciones.

Trazabilidad: RF-01, RF-02, RF-18, RF-19, RF-20 y RNF-01, RNF-02, RNF-05
(historias HU-01, HU-02, HU-11, HU-12, HU-14 y criterios de aceptaciÃ³n CA-xx).
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

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


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------------
# RF-01 / HU-01 / CA-01 â€” Registro de paciente
# --------------------------------------------------------------------------
def test_registro_valido_crea_paciente(client: TestClient, db: Session) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "first_name": "Valentino",
            "last_name": "Carazas",
            "dni": "12345678",
            "email": "valentino@ejemplo.com",
            "phone": "987654321",
            "password": PASSWORD,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["role"] == "paciente"
    assert body["is_active"] is True
    assert body["dni"] == "12345678"
    assert "password" not in body  # CA-02.3 / RNF-06: no exponer datos sensibles


def test_registro_rechaza_campos_obligatorios_vacios(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "first_name": "",
            "last_name": "",
            "dni": "12345678",
            "email": "x@ejemplo.com",
            "phone": "987654321",
            "password": PASSWORD,
        },
    )
    assert response.status_code == 422


def test_registro_rechaza_dni_invalido(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "first_name": "A",
            "last_name": "B",
            "dni": "123",  # no cumple 8 dÃ­gitos (RNF-05)
            "email": "x@ejemplo.com",
            "phone": "987654321",
            "password": PASSWORD,
        },
    )
    assert response.status_code == 422


def test_registro_rechaza_correo_invalido(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "first_name": "A",
            "last_name": "B",
            "dni": "12345678",
            "email": "correo-sin-formato",
            "phone": "987654321",
            "password": PASSWORD,
        },
    )
    assert response.status_code == 422


def test_registro_correo_duplicado_devuelve_409(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "duplicado@ejemplo.com", dni="20000002")
    response = client.post(
        "/api/auth/register",
        json={
            "first_name": "A",
            "last_name": "B",
            "dni": "20000003",
            "email": "duplicado@ejemplo.com",
            "phone": "987654321",
            "password": PASSWORD,
        },
    )
    assert response.status_code == 409  # CA-01.3


# --------------------------------------------------------------------------
# RF-02 / HU-02 / CA-02 â€” Inicio de sesiÃ³n
# --------------------------------------------------------------------------
def test_login_con_credenciales_validas_otorga_token(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "login.ok@ejemplo.com")
    response = client.post(
        "/api/auth/login", json={"email": "login.ok@ejemplo.com", "password": PASSWORD}
    )
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_rechaza_credenciales_incorrectas(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "login.bad@ejemplo.com")
    response = client.post(
        "/api/auth/login", json={"email": "login.bad@ejemplo.com", "password": "Incorrecta1!"}
    )
    assert response.status_code == 401
    assert "Incorrecta" not in response.text  # sin datos sensibles


def test_login_tras_autenticacion_devuelve_rol(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "login.rol@ejemplo.com")
    token = _token(client, "login.rol@ejemplo.com")
    me = client.get("/api/auth/me", headers=_auth_header(token))
    assert me.status_code == 200
    assert me.json()["role"] == "paciente"


def test_login_usuario_desactivado_rechazado(client: TestClient, db: Session) -> None:
    user = _crear_usuario(db, "login.off@ejemplo.com")
    user.is_active = False
    db.commit()
    response = client.post(
        "/api/auth/login", json={"email": "login.off@ejemplo.com", "password": PASSWORD}
    )
    assert response.status_code == 403


# --------------------------------------------------------------------------
# RF-19 / RNF-02 / HU-12 / CA-12 â€” Control de acceso en el servidor
# --------------------------------------------------------------------------
def test_ruta_protegida_sin_token_devuelve_401(client: TestClient, db: Session) -> None:
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_paciente_no_accede_a_rutas_admin_devuelve_403(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "rbac.paciente@ejemplo.com")
    token = _token(client, "rbac.paciente@ejemplo.com")
    response = client.get("/api/users", headers=_auth_header(token))
    assert response.status_code == 403  # RNF-02 en el servidor


def test_profesional_no_accede_a_rutas_admin_devuelve_403(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "rbac.profesional@ejemplo.com", role=UserRole.PROFESIONAL)
    token = _token(client, "rbac.profesional@ejemplo.com")
    response = client.get("/api/users", headers=_auth_header(token))
    assert response.status_code == 403


# --------------------------------------------------------------------------
# RF-18 / HU-11 / CA-11.5 â€” GestiÃ³n de cuentas por el administrador
# --------------------------------------------------------------------------
def test_admin_lista_crea_edita_y_desactiva_usuarios(client: TestClient, db: Session) -> None:
    admin = _crear_usuario(
        db, "admin.rbac@ejemplo.com", role=UserRole.ADMINISTRADOR, dni="30000001"
    )
    token = _token(client, "admin.rbac@ejemplo.com")

    # Listar
    listing = client.get("/api/users", headers=_auth_header(token))
    assert listing.status_code == 200
    assert any(u["id"] == admin.id for u in listing.json())

    # Crear (CA-11.5)
    created = client.post(
        "/api/users",
        headers=_auth_header(token),
        json={
            "first_name": "Nuevo",
            "last_name": "Usuario",
            "dni": "30000002",
            "email": "nuevo.user@ejemplo.com",
            "phone": "999222333",
            "password": PASSWORD,
            "role": "profesional",
        },
    )
    assert created.status_code == 201
    new_id = created.json()["id"]

    # Desactivar (RF-18)
    deactivated = client.patch(
        f"/api/users/{new_id}", headers=_auth_header(token), json={"is_active": False}
    )
    assert deactivated.status_code == 200
    assert deactivated.json()["is_active"] is False


def test_crear_usuario_duplicado_admin_409(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "admin.dup@ejemplo.com", role=UserRole.ADMINISTRADOR, dni="30000003")
    _crear_usuario(db, "duplicado2@ejemplo.com", dni="30000004")
    token = _token(client, "admin.dup@ejemplo.com")
    response = client.post(
        "/api/users",
        headers=_auth_header(token),
        json={
            "first_name": "A",
            "last_name": "B",
            "dni": "30000004",
            "email": "otro@ejemplo.com",
            "phone": "999222333",
            "password": PASSWORD,
            "role": "paciente",
        },
    )
    assert response.status_code == 409


# --------------------------------------------------------------------------
# RF-20 / HU-14 / CA-14 â€” Cierre de sesiÃ³n
# --------------------------------------------------------------------------
def test_logout_invalida_la_sesion_activa(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "logout@ejemplo.com")
    token = _token(client, "logout@ejemplo.com")

    assert client.get("/api/auth/me", headers=_auth_header(token)).status_code == 200

    logout = client.post("/api/auth/logout", headers=_auth_header(token))
    assert logout.status_code == 200

    # El mismo token ya no es vÃ¡lido (sesiÃ³n cerrada).
    me_after = client.get("/api/auth/me", headers=_auth_header(token))
    assert me_after.status_code == 401


def test_logout_sin_autenticacion_devuelve_401(client: TestClient) -> None:
    response = client.post("/api/auth/logout")
    assert response.status_code == 401


# --------------------------------------------------------------------------
# RNF-01 â€” SesiÃ³n con expiraciÃ³n de 30 minutos
# --------------------------------------------------------------------------
def test_token_incluye_expiracion_de_30_minutos(client: TestClient, db: Session) -> None:
    _crear_usuario(db, "exp.token@ejemplo.com")
    token = _token(client, "exp.token@ejemplo.com")
    import jwt

    payload = jwt.decode(
        token,
        "cambiar-este-secreto-en-produccion",
        algorithms=["HS256"],
        options={"verify_exp": False},
    )
    import datetime as dt

    duracion = dt.datetime.fromtimestamp(payload["exp"], tz=dt.timezone.utc) - dt.datetime.fromtimestamp(
        payload["iat"], tz=dt.timezone.utc
    )
    assert duracion.total_seconds() == 30 * 60
