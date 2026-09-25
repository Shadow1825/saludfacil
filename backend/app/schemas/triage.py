"""Esquemas del módulo de triaje (FASE 5) y revisión administrativa (FASE 6).

- RF-12 a RF-16 (FASE 5): registro, consulta, síncrona y determinismo.
- RF-17 / HU-13 / CA-13.x (FASE 6): revisión administrativa (revisado/descartado).
"""

from datetime import datetime

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Literal

from app.models.medical import DIAS_SEMANA
from app.services.triage import CLASIFICACION_LABEL, es_sintoma_canonico_alta

# Mensaje mostrado junto a cada resultado de triaje (RF-12 / CA-07.x).
MENSAJE_NO_DIAGNOSTICO = (
    "Clasificación inicial orientativa. Esta clasificación no constituye "
    "un diagnóstico médico ni sustituye la valoración de un profesional."
)

CLASIFICACION_LABEL1 = CLASIFICACION_LABEL

Severidad = Literal["leve", "moderada", "intensa"]

# Estados de la revisión administrativa del triaje (RF-17 / HU-13 / CA-13.x).
ESTADOS_REVISION = ("pendiente", "revisado", "descartado")
ESTADO_REVISION_LABEL = {
    "pendiente": "Pendiente de revisión",
    "revisado": "Revisado",
    "descartado": "Descartado",
}

RevisionEstado = Literal["revisado", "descartado"]


class SintomaInput(BaseModel):
    """Síntoma reportado por el paciente: nombre y severidad (CA-07.2/07.3).

    Validaciones de severidad conforme a las reglas oficiales R1-R6:
    - La severidad "intensa" solo corresponde a los síntomas de las reglas
      R1/R2/R3 definidos en el documento oficial (dificultad respiratoria,
      dolor torácico, pérdida de conciencia).
    - Los demás síntomas solo pueden reportarse como "moderada" o "leve".
    """

    nombre: str = Field(min_length=2, max_length=150)
    severidad: Severidad

    @model_validator(mode="after")
    def _severidad_acorde_a_reglas(self) -> "SintomaInput":
        if self.severidad == "intensa" and not es_sintoma_canonico_alta(self.nombre):
            raise ValueError(
                "La severidad 'intensa' solo corresponde a los síntomas de las reglas R1-R3 del triaje."
            )
        if es_sintoma_canonico_alta(self.nombre) and self.severidad != "intensa":
            raise ValueError(
                "Los síntomas de las reglas R1-R3 del triaje solo se registran con severidad 'intensa'."
            )
        return self


class TriageCreate(BaseModel):
    """Registro de síntomas para clasificación inicial (RF-12 / CA-07.1).

    Al menos un síntoma es obligatorio (CA-07.3); la lista no puede estar vacía.
    """

    cita_id: int
    sintomas: list[SintomaInput] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def _norm_nombres(self) -> "TriageCreate":
        for sintoma in self.sintomas:
            sintoma.nombre = " ".join(sintoma.nombre.strip().lower().split())
        return self


class RevisionTriaje(BaseModel):
    """Resolución de la revisión administrativa de un triaje (RF-17 / CA-13.x).

    El administrador confirma el registro (revisado) o lo descarta cuando los
    datos reportados son inconsistentes (descartado).
    """

    estado: RevisionEstado


def _time_str(value) -> str:
    return value.strftime("%H:%M") if hasattr(value, "strftime") else str(value)


def serialize_triage(triaje, paciente, cita, profesional, especialidad) -> dict:
    """Representación del triaje para la API (clasificación inicial, no diagnóstico)."""
    return {
        "id": triaje.id,
        "cita_id": triaje.cita_id,
        "paciente_id": triaje.paciente_id,
        "fecha": cita.fecha.isoformat() if cita else "",
        "hora_inicio": _time_str(cita.hora_inicio) if cita else "",
        "paciente": f"{paciente.first_name} {paciente.last_name}" if paciente else "",
        "profesional": f"{profesional.first_name} {profesional.last_name}" if profesional else "",
        "specialty_name": especialidad.nombre if especialidad else "",
        "dia": DIAS_SEMANA.get(cita.fecha.weekday() + 1, "") if cita else "",
        "clasificacion": triaje.clasificacion,  # alta | media | baja
        "resultado": CLASIFICACION_LABEL.get(triaje.clasificacion, triaje.clasificacion),
        "sintomas": triaje.sintomas,
        "es_diagnostico": False,
        "mensaje": MENSAJE_NO_DIAGNOSTICO,
        "estado_revision": triaje.estado_revision,  # pendiente|revisado|descartado (RF-17)
        "estado_revision_label": ESTADO_REVISION_LABEL.get(
            triaje.estado_revision, triaje.estado_revision
        ),
        "revisado_en": (
            triaje.creado_por_admin_en.isoformat()
            if isinstance(triaje.creado_por_admin_en, datetime)
            else None
        ),
        "created_at": triaje.created_at.isoformat() if isinstance(triaje.created_at, datetime) else str(triaje.created_at),
    }


# reexports usados por __init__ de schemas
__all__ = [
    "MENSAJE_NO_DIAGNOSTICO",
    "SintomaInput",
    "TriageCreate",
    "RevisionTriaje",
    "Severidad",
    "RevisionEstado",
    "ESTADOS_REVISION",
    "ESTADO_REVISION_LABEL",
    "serialize_triage",
]