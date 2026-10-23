"""Búsqueda exacta: búsqueda en profundidad (BPP) con memoria de estados.

Formulación como problema de búsqueda
-------------------------------------
- Estado: qué tareas ya se programaron, en qué bloque terminó la última y
  cuántos bloques de tareas lleva el día de esa última tarea.
- Estado inicial: ninguna tarea programada, al comienzo del horizonte.
- Acciones: "programar a continuación la tarea j". La tarea se ubica en el
  PRIMER bloque posible después de la última, respetando el descanso, la carga
  diaria, los bloques fijos y su fecha límite. Si no cabe, la acción no existe.
- Valor de un plan: suma de las prioridades de las tareas programadas.
  Desempate: entre planes de igual valor, el que termina las tareas más temprano.
- Cualquier estado ya es un plan válido; se busca el de mayor valor.

¿Por qué basta con "lo antes posible"?
Tomemos cualquier plan válido y recorramos sus tareas en orden de inicio. Si
cada una se pone en el primer hueco válido después de la anterior, ninguna
termina más tarde que en el plan original. Se ve tarea por tarea: la anterior
terminó antes o igual, y el hueco original sigue disponible. Por eso las fechas
límite se siguen cumpliendo, y basta con decidir el ORDEN de las tareas y
cuáles quedan por fuera. Las pruebas automáticas comparan este resultado con
una fuerza bruta que sí prueba todas las horas de inicio en casos pequeños.

¿Para qué la memoria?
Dos órdenes distintos pueden llegar al mismo estado: mismas tareas
programadas, mismo punto del calendario y misma carga del día. Desde ahí el
futuro es idéntico, así que se calcula una sola vez (programación dinámica).
Sin memoria, la BPP revisaría las mismas ramas muchas veces.
"""
from __future__ import annotations

import itertools

from .restricciones import validar_plan


class BusquedaDemasiadoGrande(Exception):
    """Se alcanzó el máximo de estados permitido (la instancia es muy grande)."""


def _tabla_siguiente(problema, i):
    """sig[k] = primer bloque >= k donde la tarea i cabe sola (libres + fecha límite)."""
    d, lim, total = problema.dur[i], problema.limite[i], problema.total_bloques
    sig = [None] * (total + 2)
    for k in range(total, -1, -1):
        if k + d <= lim and problema.cabe_en_libres(k, d):
            sig[k] = k
        else:
            sig[k] = sig[k + 1]
    return sig


def planificar_optimo(problema, max_estados: int = 3_000_000):
    """Devuelve (plan óptimo, estados explorados).

    Lanza BusquedaDemasiadoGrande si se superan `max_estados` estados.
    """
    n = len(problema.tareas)
    bpd = problema.bloques_por_dia
    total = problema.total_bloques
    sig = [_tabla_siguiente(problema, i) for i in range(n)]
    prioridad = [t.prioridad for t in problema.tareas]
    memo = {}

    def siguiente_inicio(i, fin_ultimo, carga, hay_ultima):
        """Primer inicio válido de la tarea i después de la última tarea programada."""
        d = problema.dur[i]
        if d > problema.max_carga:
            return None
        if not hay_ultima:
            s = sig[i][0]
            return None if s is None else (s, d)
        dia_ultimo = (fin_ultimo - 1) // bpd
        inicio_dia_siguiente = min((dia_ultimo + 1) * bpd, total)
        # El descanso solo se exige dentro del mismo día.
        desde = min(fin_ultimo + problema.descanso, inicio_dia_siguiente)
        s = sig[i][desde]
        if s is None:
            return None
        if s // bpd != dia_ultimo:
            return s, d                          # otro día: la carga empieza de cero
        if carga + d <= problema.max_carga:
            return s, carga + d                  # mismo día y no supera el tope
        s = sig[i][inicio_dia_siguiente]         # ese día ya está lleno: probar el siguiente
        return None if s is None else (s, d)

    def mejor(mascara, fin_ultimo, carga):
        clave = (mascara, fin_ultimo, carga)
        if clave in memo:
            return memo[clave][0]
        if len(memo) >= max_estados:
            raise BusquedaDemasiadoGrande(f"Se superaron {max_estados} estados")
        hay_ultima = mascara != 0
        mejor_valor, mejor_accion = (0, 0), None
        for i in range(n):
            if mascara >> i & 1:
                continue
            r = siguiente_inicio(i, fin_ultimo, carga, hay_ultima)
            if r is None:
                continue
            s, carga_nueva = r
            fin = s + problema.dur[i]
            futuro = mejor(mascara | (1 << i), fin, carga_nueva)
            valor = (prioridad[i] + futuro[0], futuro[1] - fin)
            if valor > mejor_valor:
                mejor_valor, mejor_accion = valor, (i, s, fin, carga_nueva)
        memo[clave] = (mejor_valor, mejor_accion)
        return mejor_valor

    mejor(0, 0, 0)

    # Reconstruir el plan siguiendo las mejores decisiones guardadas.
    plan, clave = {}, (0, 0, 0)
    while memo[clave][1] is not None:
        i, s, fin, carga_nueva = memo[clave][1]
        plan[i] = s
        clave = (clave[0] | (1 << i), fin, carga_nueva)
    return plan, len(memo)


def planificar_fuerza_bruta(problema) -> dict:
    """Prueba TODAS las combinaciones de (no programar | cada inicio posible).

    Solo sirve para verificar la búsqueda exacta en instancias muy pequeñas:
    el número de combinaciones crece de forma exponencial.
    """
    opciones = []
    for i in range(len(problema.tareas)):
        inicios = [s for s in range(problema.total_bloques)
                   if s + problema.dur[i] <= problema.limite[i]
                   and problema.cabe_en_libres(s, problema.dur[i])]
        opciones.append([None] + inicios)

    mejor_plan, mejor_valor = {}, 0
    for combinacion in itertools.product(*opciones):
        plan = {i: s for i, s in enumerate(combinacion) if s is not None}
        valor = sum(problema.tareas[i].prioridad for i in plan)
        if valor > mejor_valor and not validar_plan(problema, plan):
            mejor_plan, mejor_valor = plan, valor
    return mejor_plan
