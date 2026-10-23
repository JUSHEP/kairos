"""Pruebas automáticas de Kairos. Ejecutar con:  python -m pytest -q

Qué se comprueba:
1. El validador detecta cada tipo de violación (R1 a R4).
2. Los casos didácticos dan el resultado esperado.
3. Todas las estrategias producen planes válidos (0 violaciones).
4. La búsqueda exacta nunca es peor que una estrategia voraz.
5. La búsqueda exacta encuentra el mismo valor que una fuerza bruta que
   prueba TODAS las horas de inicio (en instancias pequeñas).
6. Los archivos de ejemplo se leen bien.
"""
from datetime import datetime, time
from pathlib import Path

import pytest

from kairos.busqueda import planificar_fuerza_bruta, planificar_optimo
from kairos.datos import cargar_problema
from kairos.escenarios import (LUNES, caso_fecha_limite_falla, caso_prioridad_falla,
                               generar_escenario, generar_instancia_diminuta)
from kairos.metricas import valor_plan
from kairos.modelo import Configuracion, Problema, Tarea
from kairos.planificador import ESTRATEGIAS, resolver
from kairos.restricciones import validar_plan

RAIZ = Path(__file__).resolve().parents[1]


def problema_pequeno():
    """Un día, libre de 18:00 a 22:00 (bloques 36 a 43), tope de 3 h y descanso de 30 min."""
    config = Configuracion(fecha_inicio=LUNES, dias=1, hora_inicio_dia=time(18, 0),
                           hora_fin_dia=time(22, 0), max_horas_tareas_dia=3, descanso_min=30)
    tareas = [
        Tarea("A", "A", 60, datetime(2026, 10, 26, 22, 0), 3),
        Tarea("B", "B", 60, datetime(2026, 10, 26, 20, 0), 2),
        Tarea("C", "C", 90, datetime(2026, 10, 26, 22, 0), 1),
    ]
    return Problema(tareas, [], config)


# ---------- 1. El validador ----------
def test_plan_valido_no_tiene_violaciones():
    p = problema_pequeno()
    assert validar_plan(p, {1: 36, 0: 39}) == []          # B 18:00-19:00, A 19:30-20:30


@pytest.mark.parametrize("plan, codigo", [
    ({0: 30}, "R1"),               # A a las 15:00: fuera del horario del día
    ({0: 36, 1: 37}, "R2"),        # A y B se solapan
    ({0: 36, 1: 38}, "R2"),        # sin los 30 min de descanso
    ({1: 39}, "R3"),               # B termina 20:30, después de su límite (20:00)
    ({1: 36, 0: 39, 2: 41}, "R4"), # 1 h + 1 h + 1,5 h = 3,5 h > tope de 3 h
])
def test_validador_detecta_cada_restriccion(plan, codigo):
    violaciones = validar_plan(problema_pequeno(), plan)
    assert any(v.startswith(codigo) for v in violaciones), violaciones


# ---------- 2. Casos didácticos ----------
def test_caso_prioridad_falla():
    p = caso_prioridad_falla()
    assert valor_plan(p, resolver(p, "voraz_prioridad").plan) == 5
    assert valor_plan(p, resolver(p, "busqueda_exacta").plan) == 8


def test_caso_fecha_limite_falla():
    p = caso_fecha_limite_falla()
    assert valor_plan(p, resolver(p, "voraz_fecha_limite").plan) == 1
    assert valor_plan(p, resolver(p, "busqueda_exacta").plan) == 5


# ---------- 3 y 4. Escenarios sintéticos ----------
ESCENARIOS = [(n, s) for n in (4, 6, 8, 10) for s in range(8)]


@pytest.mark.parametrize("n, semilla", ESCENARIOS)
def test_planes_validos_y_exacta_no_peor(n, semilla):
    p = generar_escenario(n, semilla)
    valores = {}
    for e in ESTRATEGIAS:
        plan = resolver(p, e).plan
        assert validar_plan(p, plan) == [], (e, validar_plan(p, plan))
        valores[e] = valor_plan(p, plan)
    assert all(valores["busqueda_exacta"] >= v for v in valores.values())


# ---------- 5. Exacta contra fuerza bruta ----------
@pytest.mark.parametrize("semilla", range(40))
def test_exacta_igual_a_fuerza_bruta(semilla):
    p = generar_instancia_diminuta(semilla)
    plan_exacto, _ = planificar_optimo(p)
    plan_bruto = planificar_fuerza_bruta(p)
    assert validar_plan(p, plan_exacto) == []
    assert valor_plan(p, plan_exacto) == valor_plan(p, plan_bruto)


# ---------- 6. Datos de ejemplo ----------
def test_lectura_de_ejemplo():
    p = cargar_problema(RAIZ / "datos" / "ejemplo")
    assert len(p.tareas) == 12
    assert len(p.bloques_fijos) == 24
    assert validar_plan(p, resolver(p, "busqueda_exacta").plan) == []
