"""Estrategias voraces (línea base).

Una estrategia voraz ordena las tareas con una regla sencilla y coloca cada una
en el PRIMER hueco donde quepa, sin volver atrás nunca. Es rápida y fácil de
explicar, pero no garantiza el mejor plan. Sirve como punto de comparación.

Se prueban tres reglas, cada una con una intuición distinta:
  - "prioridad":    primero lo más importante (desempate: fecha límite más cercana).
  - "fecha_limite": primero lo más urgente (EDF, earliest deadline first).
  - "razon":        primero lo que da más prioridad por hora (prioridad / duración).
                    Era la regla propuesta en la primera entrega.
"""
from __future__ import annotations

from .restricciones import primer_inicio_posible

CRITERIOS = {
    "prioridad": lambda p, i: (-p.tareas[i].prioridad, p.limite[i], p.dur[i]),
    "fecha_limite": lambda p, i: (p.limite[i], -p.tareas[i].prioridad, p.dur[i]),
    "razon": lambda p, i: (-p.tareas[i].prioridad / p.dur[i], p.limite[i]),
}


def planificar_voraz(problema, criterio: str = "prioridad") -> dict:
    """Devuelve un plan {indice_de_tarea: bloque_de_inicio} con la regla indicada."""
    if criterio not in CRITERIOS:
        raise ValueError(f"Criterio desconocido: {criterio}. Opciones: {list(CRITERIOS)}")
    orden = sorted(range(len(problema.tareas)), key=lambda i: CRITERIOS[criterio](problema, i))
    plan = {}
    for i in orden:
        s = primer_inicio_posible(problema, plan, i)
        if s is not None:
            plan[i] = s
    return plan
