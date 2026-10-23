"""Exploración del dataset seleccionado para el módulo de aprendizaje.

Pregunta: con el historial de una persona, ¿se puede estimar mejor cuánto dura
de verdad una tarea que simplemente creyendo su estimación?

Dataset: Renzo Pomodoro dataset (Jones y Borgatti, 2019).
https://github.com/Derek-Jones/renzo-pomodoro
Las funciones están en kairos/duraciones.py; ahí se explica cada paso.

Uso (desde la carpeta raíz del proyecto; la primera vez necesita internet):
    python experimentos/explorar_dataset_pomodoro.py

Genera en resultados/:
    pomodoro_resumen.csv, pomodoro_por_estimacion.csv, pomodoro_modelos.csv
    y la figura pomodoro_real_vs_estimado.png
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

import pandas as pd  # noqa: E402

from kairos.duraciones import (cargar_pomodoro, coeficientes_regresion_simple,  # noqa: E402
                               comparar_modelos, particion_temporal, preparar, resumen,
                               tabla_por_estimacion)
from kairos.visualizacion import dibujar_real_vs_estimado  # noqa: E402


def main():
    salida = RAIZ / "resultados"
    salida.mkdir(exist_ok=True)
    original = cargar_pomodoro()
    x = preparar(original)
    info = resumen(x)
    print(f"Filas originales: {len(original)} | tareas tras preparar: {info['tareas']}")
    for clave, valor in info.items():
        print(f"  {clave}: {valor}")

    tabla = tabla_por_estimacion(x)
    print("\nDuración real según lo estimado (en pomodoros):")
    print(tabla.to_string(index=False))

    entrenamiento, prueba = particion_temporal(x)
    a, b = coeficientes_regresion_simple(entrenamiento)
    print(f"\nEntrenamiento: {len(entrenamiento)} tareas ({entrenamiento['fecha'].min():%Y-%m-%d} a "
          f"{entrenamiento['fecha'].max():%Y-%m-%d}) | prueba: {len(prueba)} tareas "
          f"({prueba['fecha'].min():%Y-%m-%d} a {prueba['fecha'].max():%Y-%m-%d})")
    print(f"Regresión lineal simple: real = {a:.2f} + {b:.2f} x estimado")
    modelos = comparar_modelos(entrenamiento, prueba)
    print(modelos.to_string(index=False))

    info.update({"tareas_entrenamiento": len(entrenamiento), "tareas_prueba": len(prueba),
                 "fecha_corte": prueba["fecha"].min().date().isoformat(),
                 "intercepto_regresion": round(a, 3), "pendiente_regresion": round(b, 3)})
    pd.DataFrame([info]).to_csv(salida / "pomodoro_resumen.csv", index=False)
    tabla.to_csv(salida / "pomodoro_por_estimacion.csv", index=False)
    modelos.to_csv(salida / "pomodoro_modelos.csv", index=False)
    dibujar_real_vs_estimado(tabla, ruta=salida / "pomodoro_real_vs_estimado.png")
    print(f"\nResultados guardados en {salida}")


if __name__ == "__main__":
    main()
