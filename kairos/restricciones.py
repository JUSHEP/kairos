"""Restricciones duras de Kairos y verificador independiente.

Un plan válido debe cumplir TODAS estas restricciones:

  R1 Disponibilidad: la tarea solo ocupa bloques libres (dentro del horario del
     día y fuera de los bloques fijos) y no se parte entre dos días.
  R2 No solapamiento: dos tareas nunca comparten bloques y, si son del mismo
     día, entre ellas queda al menos el descanso mínimo.
  R3 Fecha límite: la tarea termina antes o justo en su fecha límite.
  R4 Carga diaria: las tareas de un mismo día no superan el tope de horas.

`validar_plan` revisa un plan desde cero, sin confiar en el algoritmo que lo
generó. Así todas las estrategias se comprueban con la misma regla.
`puede_agregar` responde si una tarea se puede añadir a un plan parcial; lo usan
las estrategias voraces y el reporte de tareas que no cupieron.
"""
from __future__ import annotations

from collections import defaultdict


def validar_plan(problema, plan) -> list[str]:
    """Devuelve la lista de violaciones encontradas (lista vacía = plan válido)."""
    violaciones = []
    n = len(problema.tareas)

    for i, s in plan.items():
        if not 0 <= i < n:
            violaciones.append(f"Índice de tarea inválido: {i}")
            continue
        t, d = problema.tareas[i], problema.dur[i]
        if not problema.cabe_en_libres(s, d):
            violaciones.append(f"R1 {t.id}: ocupa bloques no disponibles o cruza de un día a otro")
        if s + d > problema.limite[i]:
            violaciones.append(f"R3 {t.id}: termina después de su fecha límite")

    validas = sorted((s, i) for i, s in plan.items() if 0 <= i < n)

    # R2: basta revisar tareas consecutivas en el orden de inicio.
    for (s1, i1), (s2, i2) in zip(validas, validas[1:]):
        fin1 = s1 + problema.dur[i1]
        mismo_dia = problema.dia_de(fin1 - 1) == problema.dia_de(s2)
        separacion_minima = problema.descanso if mismo_dia else 0
        if s2 < fin1:
            violaciones.append(f"R2 {problema.tareas[i1].id} y {problema.tareas[i2].id}: se solapan")
        elif s2 < fin1 + separacion_minima:
            violaciones.append(
                f"R2 {problema.tareas[i1].id} y {problema.tareas[i2].id}: no respetan el descanso mínimo")

    # R4: sumar la carga de cada día.
    carga = defaultdict(int)
    for s, i in validas:
        carga[problema.dia_de(s)] += problema.dur[i]
    for dia, bloques in carga.items():
        if bloques > problema.max_carga:
            violaciones.append(f"R4 día {dia + 1}: supera el tope de horas de tareas")

    return violaciones


def puede_agregar(problema, plan, i, s) -> bool:
    """True si la tarea i puede empezar en el bloque s sin romper el plan parcial."""
    d = problema.dur[i]
    fin = s + d
    if s < 0 or fin > problema.limite[i]:                 # R3
        return False
    if not problema.cabe_en_libres(s, d):                 # R1
        return False
    dia = problema.dia_de(s)
    carga = d
    for j, sj in plan.items():
        fj = sj + problema.dur[j]
        mismo_dia = problema.dia_de(sj) == dia
        g = problema.descanso if mismo_dia else 0
        if s < fj + g and sj < fin + g:                   # R2 (con descanso)
            return False
        if mismo_dia:
            carga += problema.dur[j]
    return carga <= problema.max_carga                    # R4


def primer_inicio_posible(problema, plan, i):
    """Primer bloque donde la tarea i cabe junto al plan parcial, o None si no cabe."""
    for s in range(0, problema.limite[i] - problema.dur[i] + 1):
        if puede_agregar(problema, plan, i, s):
            return s
    return None
