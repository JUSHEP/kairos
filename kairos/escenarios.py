"""Escenarios de prueba.

IMPORTANTE: todo lo que hay aquí es SINTÉTICO, es decir, construido por el
equipo. Sirve para probar y comparar estrategias de planificación, NO para
sacar conclusiones sobre estudiantes reales.

- caso_prioridad_falla / caso_fecha_limite_falla: casos didácticos mínimos,
  hechos a mano para mostrar el punto débil de cada regla voraz.
- generar_escenario: semanas aleatorias pero plausibles (clases, almuerzo,
  transporte y, algunos días, trabajo), reproducibles con una semilla.
"""
from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta

from .modelo import BloqueFijo, Configuracion, Problema, Tarea

LUNES = date(2026, 10, 26)
TIPOS = ["estudio", "taller", "lectura", "proyecto", "informe", "otro"]


def _config_noches(dias: int) -> Configuracion:
    """Solo hay tiempo libre de 18:00 a 22:00 (como un estudiante que trabaja de día)."""
    return Configuracion(fecha_inicio=LUNES, dias=dias, hora_inicio_dia=time(18, 0),
                         hora_fin_dia=time(22, 0), minutos_por_bloque=30,
                         max_horas_tareas_dia=4, descanso_min=30)


def caso_prioridad_falla() -> Problema:
    """La regla 'primero lo más importante' ocupa el lunes y pierde la tarea urgente."""
    tareas = [
        Tarea("A", "Proyecto final", 180, datetime(2026, 10, 27, 22, 0), 5, "proyecto"),
        Tarea("B", "Taller para el martes", 180, datetime(2026, 10, 26, 22, 0), 3, "taller"),
    ]
    return Problema(tareas, [], _config_noches(dias=2))


def caso_fecha_limite_falla() -> Problema:
    """La regla 'primero lo más urgente' gasta la noche en algo poco importante."""
    tareas = [
        Tarea("D", "Ejercicios opcionales", 180, datetime(2026, 10, 26, 21, 0), 1, "taller"),
        Tarea("E", "Estudiar para el parcial", 180, datetime(2026, 10, 26, 22, 0), 5, "estudio"),
    ]
    return Problema(tareas, [], _config_noches(dias=1))


def generar_instancia_diminuta(semilla: int) -> Problema:
    """1 o 2 noches con huecos aleatorios y 3 o 4 tareas.

    Es tan pequeña que la fuerza bruta puede revisar TODAS las combinaciones;
    sirve para comprobar que la búsqueda exacta encuentra el óptimo.
    """
    rng = random.Random(semilla)
    dias = rng.choice([1, 2])
    config = Configuracion(fecha_inicio=LUNES, dias=dias, hora_inicio_dia=time(18, 0),
                           hora_fin_dia=time(22, 0), max_horas_tareas_dia=rng.choice([2, 3, 4]),
                           descanso_min=rng.choice([0, 30]))
    fijos = []
    for d in range(dias):
        if rng.random() < 0.6:                    # un compromiso corto que parte la noche
            h = rng.choice([19, 20])
            fijos.append(BloqueFijo("Fijo", d, time(h, 0), time(h, 30)))
    tareas = []
    for k in range(rng.choice([3, 4])):
        dia = rng.randrange(dias)
        tareas.append(Tarea(f"T{k}", f"T{k}", rng.choice([30, 60, 90, 120]),
                            datetime(2026, 10, 26 + dia, rng.choice([20, 21, 22]), 0),
                            rng.randint(1, 5)))
    return Problema(tareas, fijos, config)


def generar_escenario(n_tareas: int, semilla: int, dias: int = 5) -> Problema:
    """Semana sintética reproducible: misma semilla -> mismo escenario."""
    rng = random.Random(semilla)
    config = Configuracion(fecha_inicio=LUNES, dias=dias, hora_inicio_dia=time(7, 0),
                           hora_fin_dia=time(22, 0), minutos_por_bloque=30,
                           max_horas_tareas_dia=5, descanso_min=30)
    bloques = []
    for d in range(dias):
        dia_semana = (LUNES + timedelta(days=d)).weekday()
        clases = sorted(rng.sample([7, 9, 11, 14, 16, 18], rng.choice([2, 3])))
        for h in clases:
            bloques.append(BloqueFijo("Clase", dia_semana, time(h), time(h + 2)))
        bloques.append(BloqueFijo("Almuerzo", dia_semana, time(13), time(14)))
        primera, ultima = clases[0], clases[-1] + 2
        if primera >= 8:
            bloques.append(BloqueFijo("Transporte", dia_semana, time(primera - 1), time(primera)))
        if ultima <= 21:
            bloques.append(BloqueFijo("Transporte", dia_semana, time(ultima), time(ultima + 1)))
        if rng.random() < 0.3:
            bloques.append(BloqueFijo("Trabajo", dia_semana, time(14), time(18)))

    tareas = []
    for k in range(n_tareas):
        dia_limite = rng.randint(0, dias - 1)
        hora_limite = rng.choice([time(7, 0), time(12, 0), time(23, 59)])
        if dia_limite == 0 and hora_limite == time(7, 0):
            hora_limite = time(23, 59)        # evita tareas imposibles desde el inicio
        tareas.append(Tarea(
            id=f"T{k + 1}",
            nombre=f"Tarea {k + 1}",
            duracion_min=rng.choice([30, 60, 90, 120, 150, 180]),
            fecha_limite=datetime.combine(LUNES + timedelta(days=dia_limite), hora_limite),
            prioridad=rng.randint(1, 5),
            tipo=rng.choice(TIPOS),
        ))
    return Problema(tareas, bloques, config)
