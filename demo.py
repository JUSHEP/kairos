"""Demostración de Kairos con datos en CSV.

Uso (desde la carpeta raíz del proyecto):
    python demo.py                    # usa datos/ejemplo
    python demo.py datos/mi_semana    # usa otra carpeta con el mismo formato

Muestra la comparación de las cuatro estrategias, el plan de la búsqueda exacta,
las alertas de tareas que no caben y guarda el calendario en resultados/.
"""
import sys
from pathlib import Path

import pandas as pd

from kairos.datos import cargar_problema
from kairos.metricas import evaluar, valor_plan
from kairos.planificador import ESTRATEGIAS, NOMBRES, resolver
from kairos.reporte import explicar_no_programadas, tabla_plan
from kairos.visualizacion import dibujar_plan

pd.set_option("display.width", 160)
pd.set_option("display.max_colwidth", 60)


def main(carpeta: str = "datos/ejemplo"):
    problema = cargar_problema(carpeta)
    print(f"Datos: {carpeta} | {len(problema.tareas)} tareas | "
          f"{sum(problema.dur) * problema.minutos_por_bloque / 60:.1f} h pedidas | "
          f"{problema.horas_libres():.1f} h libres en el horizonte\n")

    resultados = {e: resolver(problema, e) for e in ESTRATEGIAS}
    optimo = valor_plan(problema, resultados["busqueda_exacta"].plan)
    tabla = pd.DataFrame([evaluar(problema, r, optimo) for r in resultados.values()])
    tabla["estrategia"] = tabla["estrategia"].map(NOMBRES)
    columnas = ["estrategia", "violaciones", "valor", "prioridad_cubierta_pct",
                "tareas_programadas", "brecha_pct", "tiempo_ms"]
    print("Comparación de estrategias")
    print(tabla[columnas].to_string(index=False), "\n")

    plan = resultados["busqueda_exacta"].plan
    print("Plan propuesto (búsqueda exacta)")
    print(pd.DataFrame(tabla_plan(problema, plan)).to_string(index=False), "\n")

    alertas = explicar_no_programadas(problema, plan)
    print("Alertas" if alertas else "Todas las tareas quedaron programadas.")
    for a in alertas:
        print(f"- {a['tarea']} (prioridad {a['prioridad']}): {a['motivo']}")

    salida = Path("resultados")
    salida.mkdir(exist_ok=True)
    ruta = salida / f"plan_{Path(carpeta).name}.png"
    dibujar_plan(problema, plan, "Plan propuesto por Kairos (búsqueda exacta)", ruta)
    print(f"\nCalendario guardado en {ruta}")


if __name__ == "__main__":
    main(*sys.argv[1:2])
