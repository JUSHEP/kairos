"""Punto de entrada único para ejecutar cualquier estrategia y medir su tiempo."""
from __future__ import annotations

import time

from .busqueda import planificar_optimo
from .modelo import Resultado
from .voraz import planificar_voraz

ESTRATEGIAS = ["voraz_prioridad", "voraz_fecha_limite", "voraz_razon", "busqueda_exacta"]

NOMBRES = {
    "voraz_prioridad": "Voraz: prioridad",
    "voraz_fecha_limite": "Voraz: fecha límite",
    "voraz_razon": "Voraz: prioridad/duración",
    "busqueda_exacta": "Búsqueda exacta (BPP + memoria)",
}


def resolver(problema, estrategia: str) -> Resultado:
    """Ejecuta la estrategia indicada sobre el problema y mide cuánto tarda."""
    inicio = time.perf_counter()
    estados = None
    if estrategia == "busqueda_exacta":
        plan, estados = planificar_optimo(problema)
    elif estrategia.startswith("voraz_"):
        plan = planificar_voraz(problema, estrategia.removeprefix("voraz_"))
    else:
        raise ValueError(f"Estrategia desconocida: {estrategia}. Opciones: {ESTRATEGIAS}")
    return Resultado(estrategia, plan, time.perf_counter() - inicio, estados)
