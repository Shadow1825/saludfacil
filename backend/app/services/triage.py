"""Motor de clasificación inicial del triaje (FASE 5).

Especificación oficial del proyecto (académica, NO es un protocolo médico):

| Regla | Condición                                                                    | Resultado |
|-------|-------------------------------------------------------------------------------|-----------|
| R1    | Dificultad respiratoria intensa                                              | Alta      |
| R2    | Dolor torácico intenso                                                       | Alta      |
| R3    | Pérdida de conciencia                                                        | Alta      |
| R4    | No hay regla de Alta y existen 2 o más síntomas de severidad moderada        | Media     |
| R5    | No hay regla de Alta ni R4 y existe al menos 1 síntoma de severidad moderada | Media     |
| R6    | No se cumple ninguna regla anterior y los síntomas son de severidad leve     | Baja      |

Precedencia: Alta → Media → Baja.

Propiedades: la clasificación es 100% determinista: ante exactamente los mismos
datos de entrada produce exactamente el mismo resultado (RF-16 / CA-10.x).

Los únicos síntomas que disparan Alta (R1-R3) son los tres canónicos de la tabla.
No se definen aquí síntomas, signos vitales, umbrales ni criterios médicos adicionales.
"""

# Síntomas de severidad intensa definidos en las reglas R1/R2/R3 (normalizados).
SINTOMAS_ALTA_CANONICOS = frozenset(
    {"dificultad respiratoria", "dolor torácico", "pérdida de conciencia"}
)

SEVERIDADES = ("leve", "moderada", "intensa")

CLASIFICACION_ALTA = "alta"
CLASIFICACION_MEDIA = "media"
CLASIFICACION_BAJA = "baja"


def normalizar_sintoma(nombre: str) -> str:
    """Normaliza el nombre de un síntoma para comparación determinista."""
    return " ".join(nombre.strip().lower().split())


def es_sintoma_canonico_alta(nombre: str) -> bool:
    """¿El síntoma corresponde a las reglas R1/R2/R3 (severidad intensa)?"""
    return normalizar_sintoma(nombre) in SINTOMAS_ALTA_CANONICOS


def clasificar(sintomas: list[dict]) -> str:
    """Clasifica los síntomas según R1-R6 y su precedencia (Alta → Media → Baja).

    Requiere una lista no vacía ya validada por el esquema.
    """
    intensos = [s for s in sintomas if es_sintoma_canonico_alta(s["nombre"])]
    if intensos:
        # R1 / R2 / R3 — cualquier síntoma canónico de Alta dispara la regla.
        return CLASIFICACION_ALTA

    moderados = sum(1 for s in sintomas if s["severidad"] == "moderada")
    if moderados >= 2:
        return CLASIFICACION_MEDIA  # R4
    if moderados >= 1:
        return CLASIFICACION_MEDIA  # R5

    # R6 — solo síntomas de severidad leve (la lista no vacía garantiza ≥1 leve).
    return CLASIFICACION_BAJA


CLASIFICACION_LABEL = {
    CLASIFICACION_ALTA: "Alta",
    CLASIFICACION_MEDIA: "Media",
    CLASIFICACION_BAJA: "Baja",
}