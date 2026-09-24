"""Seed de datos ficticios para desarrollo y pruebas (RES-04).

Datos 100% ficticios (Ley N.° 29733): no corresponden a personas reales.
Uso: python -m app.seed (desde backend/, o dentro del contenedor).
"""

from datetime import time

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Especialidad, Horario, Profesional
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


SEED_SPECIALTIES = [
    "Medicina General",
    "Pediatría",
    "Cardiología",
    "Dermatología",
    "Ginecología y Obstetricia",
    "Traumatología",
]

# Profesionales de prueba relacionados a cuentas de usuario ficticias.
SEED_PROFESSIONALS = [
    {
        "email": "profesional@saludfacil.com",
        "password": "Profesional!1",
        "first_name": "María",
        "last_name": "López Cárdenas",
        "dni": "10000003",
        "phone": "999111003",
        "specialty": "Medicina General",
    },
    {
        "email": "jose.garcia@saludfacil.com",
        "password": "Profesional!1",
        "first_name": "José",
        "last_name": "García Mendoza",
        "dni": "10000004",
        "phone": "999111004",
        "specialty": "Cardiología",
    },
    {
        "email": "rosa.vera@saludfacil.com",
        "password": "Profesional!1",
        "first_name": "Rosa",
        "last_name": "Vera Díaz",
        "dni": "10000005",
        "phone": "999111005",
        "specialty": "Pediatría",
    },
]

# 1=Lunes … 7=Domingo. Horarios de ejemplo por profesional.
SEED_SCHEDULES = {
    "profesional@saludfacil.com": [
        (1, time(8, 0), time(12, 0)),
        (3, time(8, 0), time(12, 0)),
        (5, time(14, 0), time(18, 0)),
    ],
    "jose.garcia@saludfacil.com": [
        (2, time(9, 0), time(13, 0)),
        (4, time(9, 0), time(13, 0)),
    ],
    "rosa.vera@saludfacil.com": [
        (1, time(9, 0), time(12, 0)),
        (3, time(15, 0), time(18, 0)),
    ],
}


def seed_medical(db: Session) -> None:
    """Especialidades, profesionales y horarios ficticios (idempotente)."""
    especialidades: dict[str, Especialidad] = {}
    for nombre in SEED_SPECIALTIES:
        e = db.query(Especialidad).filter(Especialidad.nombre == nombre).first()
        if e is None:
            e = Especialidad(nombre=nombre)
            db.add(e)
            db.flush()
        especialidades[nombre] = e

    for item in SEED_PROFESSIONALS:
        user = db.query(User).filter(User.email == item["email"]).first()
        if user is None:
            user = User(
                email=item["email"],
                password_hash=hash_password(item["password"]),
                role=UserRole.PROFESIONAL,
                first_name=item["first_name"],
                last_name=item["last_name"],
                dni=item["dni"],
                phone=item["phone"],
                is_active=True,
                token_version=0,
            )
            db.add(user)
            db.flush()
        profesional = db.query(Profesional).filter(Profesional.user_id == user.id).first()
        if profesional is None:
            profesional = Profesional(
                user_id=user.id,
                specialty_id=especialidades[item["specialty"]].id,
            )
            db.add(profesional)
            db.flush()
        for (day, inicio, fin) in SEED_SCHEDULES.get(item["email"], []):
            existe = (
                db.query(Horario)
                .filter(
                    Horario.professional_id == profesional.id,
                    Horario.day == day,
                    Horario.start_time == inicio,
                )
                .first()
            )
            if existe is None:
                db.add(Horario(professional_id=profesional.id, day=day, start_time=inicio, end_time=fin))
    db.commit()


def run() -> None:
    db: Session = SessionLocal()
    try:
        seed_users(db)
        seed_medical(db)
        print("Seed completado: usuarios, especialidades, profesionales y horarios ficticios.")
    finally:
        db.close()


if __name__ == "__main__":
    run()