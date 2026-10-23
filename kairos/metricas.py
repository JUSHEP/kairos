"""Métricas del plan (métricas del SISTEMA, no de un modelo de aprendizaje).

- violaciones:            restricciones duras incumplidas (debe ser 0).
- valor:                  suma de prioridades de las tareas programadas.
- prioridad_cubierta_pct: valor / suma de prioridades de TODAS las tareas.
- tareas_programadas:     cuántas tareas quedaron en el plan.
- horas_programadas:      horas de tareas ubicadas en el plan.
- brecha_pct:             qué tan lejos queda del valor óptimo (0 = óptimo).
- tiempo_ms:              tiempo de cómputo de la estrategia.
"""
from __future__ import annotations

from .restricciones import validar_plan


def valor_plan(problema, plan) -> int:
    return sum(problema.tareas[i].prioridad for i in plan)


def evaluar(problema, resultado, valor_optimo: int | None = None) -> dict:
    plan = resultado.plan
    valor = valor_plan(problema, plan)
    valor_total = sum(t.prioridad for t in problema.tareas)
    horas = problema.minutos_por_bloque / 60
    fila = {
        "estrategia": resultado.estrategia,
        "violaciones": len(validar_plan(problema, plan)),
        "valor": valor,
        "prioridad_cubierta_pct": round(100 * valor / valor_total, 1) if valor_total else 100.0,
        "tareas_programadas": len(plan),
        "tareas_total": len(problema.tareas),
        "horas_programadas": sum(problema.dur[i] for i in plan) * horas,
        "horas_pedidas": sum(problema.dur) * horas,
        "tiempo_ms": round(resultado.segundos * 1000, 3),
    }
    if valor_optimo is not None:
        fila["brecha_pct"] = round(100 * (valor_optimo - valor) / valor_optimo, 1) if valor_optimo else 0.0
    if resultado.estados is not None:
        fila["estados"] = resultado.estados
    return fila
