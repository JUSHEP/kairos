"""Experimento: comparar las estrategias de planificación en escenarios sintéticos.

Uso (desde la carpeta raíz del proyecto):
    python experimentos/comparar_algoritmos.py

Qué hace:
1. Comparación: para 4, 6, 8, 10 y 12 tareas genera 20 semanas sintéticas
   (semillas 0 a 19) y ejecuta las cuatro estrategias en cada una.
2. Escalabilidad: mide cuánto tarda la búsqueda exacta al crecer el número de
   tareas (de 4 a 18, 5 semanas por tamaño) y si termina antes del límite de estados.

Salidas en resultados/:
    comparacion_escenarios.csv   una fila por (escenario, estrategia)
    resumen_por_tamano.csv       promedios por número de tareas y estrategia
    resumen_global.csv           promedios sobre los 100 escenarios
    escalabilidad.csv            tiempos de la búsqueda exacta
    brecha_voraces.png           gráfica de brecha frente al óptimo
    tiempo_busqueda_exacta.png   gráfica de tiempos

Los escenarios son SINTÉTICOS: sirven para comparar estrategias, no para
sacar conclusiones sobre estudiantes reales.
"""
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

import pandas as pd  # noqa: E402

from kairos.busqueda import BusquedaDemasiadoGrande, planificar_optimo  # noqa: E402
from kairos.escenarios import generar_escenario  # noqa: E402
from kairos.metricas import evaluar, valor_plan  # noqa: E402
from kairos.planificador import ESTRATEGIAS, resolver  # noqa: E402
from kairos.visualizacion import dibujar_brecha, dibujar_tiempos  # noqa: E402

TAMANOS = [4, 6, 8, 10, 12]
SEMILLAS = range(20)
TAMANOS_ESCALA = [4, 6, 8, 10, 12, 14, 16, 18]
SEMILLAS_ESCALA = range(5)
MAX_ESTADOS = 3_000_000
SALIDA = RAIZ / "resultados"


def comparar() -> pd.DataFrame:
    filas = []
    for n in TAMANOS:
        for semilla in SEMILLAS:
            p = generar_escenario(n, semilla)
            exacta = resolver(p, "busqueda_exacta")
            v_opt = valor_plan(p, exacta.plan)
            for e in ESTRATEGIAS:
                r = exacta if e == "busqueda_exacta" else resolver(p, e)
                fila = evaluar(p, r, v_opt)
                fila.update(n_tareas=n, semilla=semilla, horas_libres=p.horas_libres())
                filas.append(fila)
    return pd.DataFrame(filas)


def resumir(df: pd.DataFrame, por) -> pd.DataFrame:
    resumen = df.groupby(por).agg(
        escenarios=("semilla", "count"),
        violaciones=("violaciones", "sum"),
        prioridad_cubierta_media=("prioridad_cubierta_pct", "mean"),
        brecha_media=("brecha_pct", "mean"),
        brecha_max=("brecha_pct", "max"),
        pct_escenarios_optimos=("brecha_pct", lambda b: 100 * (b == 0).mean()),
        tiempo_ms_mediana=("tiempo_ms", "median"),
        tiempo_ms_max=("tiempo_ms", "max"),
    ).reset_index()
    return resumen.round(2)


def escalabilidad() -> pd.DataFrame:
    filas = []
    for n in TAMANOS_ESCALA:
        for semilla in SEMILLAS_ESCALA:
            p = generar_escenario(n, semilla)
            inicio = time.perf_counter()
            try:
                _, estados = planificar_optimo(p, max_estados=MAX_ESTADOS)
                terminado = True
            except BusquedaDemasiadoGrande:
                estados, terminado = MAX_ESTADOS, False
            filas.append(dict(n_tareas=n, semilla=semilla, estados=estados, terminado=terminado,
                              tiempo_ms=round((time.perf_counter() - inicio) * 1000, 2)))
        print(f"  escalabilidad: {n} tareas listo")
    return pd.DataFrame(filas)


def main():
    SALIDA.mkdir(exist_ok=True)
    print("1) Comparación de estrategias (100 escenarios)...")
    df = comparar()
    df.to_csv(SALIDA / "comparacion_escenarios.csv", index=False)
    por_tamano = resumir(df, ["n_tareas", "estrategia"])
    por_tamano.to_csv(SALIDA / "resumen_por_tamano.csv", index=False)
    global_ = resumir(df, ["estrategia"])
    global_.to_csv(SALIDA / "resumen_global.csv", index=False)
    dibujar_brecha(por_tamano, SALIDA / "brecha_voraces.png")
    print(global_.to_string(index=False))

    print("\n2) Escalabilidad de la búsqueda exacta...")
    esc = escalabilidad()
    esc.to_csv(SALIDA / "escalabilidad.csv", index=False)
    tiempos = esc.groupby("n_tareas").agg(
        tiempo_ms_mediana=("tiempo_ms", "median"), tiempo_ms_max=("tiempo_ms", "max"),
        estados_max=("estados", "max"), sin_terminar=("terminado", lambda t: int((~t).sum())),
    ).reset_index()
    dibujar_tiempos(tiempos, SALIDA / "tiempo_busqueda_exacta.png")
    print(tiempos.to_string(index=False))


if __name__ == "__main__":
    main()
