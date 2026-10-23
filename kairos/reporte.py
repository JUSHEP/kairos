"""Salidas legibles para el estudiante: el plan en tabla y las alertas."""
from __future__ import annotations

from .modelo import DIAS_CORTOS
from .restricciones import puede_agregar


def _fecha_corta(momento) -> str:
    return f"{DIAS_CORTOS[momento.weekday()]} {momento:%d/%m}"


def tabla_plan(problema, plan) -> list[dict]:
    """Filas del plan ordenadas en el tiempo (una por tarea programada)."""
    filas = []
    for i, s in sorted(plan.items(), key=lambda par: par[1]):
        t = problema.tareas[i]
        ini = problema.hora_de_bloque(s)
        fin = problema.hora_de_bloque(s + problema.dur[i])
        filas.append({
            "día": _fecha_corta(ini),
            "inicio": f"{ini:%H:%M}",
            "fin": f"{fin:%H:%M}",
            "tarea": t.nombre,
            "prioridad": t.prioridad,
            "fecha límite": f"{_fecha_corta(t.fecha_limite)} {t.fecha_limite:%H:%M}",
        })
    return filas


def explicar_no_programadas(problema, plan) -> list[dict]:
    """Alertas: por qué cada tarea quedó por fuera y qué puede hacer el estudiante."""
    alertas = []
    for i, t in enumerate(problema.tareas):
        if i in plan:
            continue
        cabe_sola = any(puede_agregar(problema, {}, i, s) for s in range(problema.total_bloques))
        if cabe_sola:
            motivo = ("Cabe sola, pero no junto con tareas de mayor valor. "
                      "Opciones: liberar tiempo, bajar la prioridad de otra o pedir más plazo.")
        else:
            motivo = ("No hay ningún hueco libre suficiente antes de su fecha límite, "
                      "ni siquiera sin otras tareas. Opciones: pedir más plazo o dividirla.")
        alertas.append({"tarea": t.nombre, "prioridad": t.prioridad,
                        "duración (min)": t.duracion_min, "motivo": motivo})
    return alertas
