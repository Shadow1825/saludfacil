"""Seed de datos ficticios para desarrollo y pruebas (RES-04).

Datos 100% ficticios (Ley N.° 29733): no corresponden a personas reales.
Uso: python -m app.seed (desde backend/, o dentro del contenedor).
"""

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.services.security import hash_password

SEED_USERS = [
    {
        "email": "admin@saludfacil.com",
        "password": "AdminSaludFacil!1",
        "role": UserRole.ADMINISTRADOR,
        "first_name": "Ana",
        "last_name": "Torres Medina",
        "dni": "10000001",
        "phone": "999111001",
    },
    {
        "email": "paciente@saludfacil.com",
        "password": "PacientePrueba!1",
        "role": UserRole.PACIENTE,
        "first_name": "Luis",
        "last_name": "Quispe Rojas",
        "dni": "10000002",
        "phone": "999111002",
    },
    {
        "email": "profesional@saludfacil.com",
        "password": "Profesional!1",
        "role": UserRole.PROFESIONAL,
        "first_name": "María",
        "last_name": "López Cárdenas",
        "dni": "10000003",
        "phone": "999111003",
    },
]


def seed_users(db: Session) -> None:
    """Inserta los usuarios de prueba si no existen (idempotente)."""
    for item in SEED_USERS:
        exists = db.query(User).filter(User.email == item["email"]).first()
        if exists is None:
            db.add(
                User(
                    email=item["email"],
                    password_hash=hash_password(item["password"]),
                    role=item["role"],
                    first_name=item["first_name"],
                    last_name=item["last_name"],
                    dni=item["dni"],
                    phone=item["phone"],
                    is_active=True,
                    token_version=0,
                )
            )
    db.commit()


def run() -> None:
    db: Session = SessionLocal()
    try:
        seed_users(db)
        print("Seed completado: usuarios ficticios creados/sincronizados.")
    finally:
        db.close()


if __name__ == "__main__":
    run()