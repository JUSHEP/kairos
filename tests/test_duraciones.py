"""Pruebas del módulo de aprendizaje (kairos/duraciones.py).

No usan internet: trabajan con tablas pequeñas hechas a mano que tienen las
mismas columnas que el dataset Pomodoro.
"""
import pandas as pd

from kairos.duraciones import (comparar_modelos, particion_temporal, preparar, resumen,
                               tabla_por_estimacion)


def tabla_cruda():
    return pd.DataFrame({
        "X.words": ["@a", "@a", "@b,@c", "@b", "@a", "@a", "@b"],
        "word_cnt": ["1"] * 7,
        "description": [1, 2, 3, 4, 5, 5, 6],
        "DONE": [1, 0, 1, 1, 1, 1, 1],
        "date": ["2010-01-02", "2010-01-01", "2010-01-01", "2010-01-03", "2010-01-04", "2010-01-04", "2010-01-05"],
        "estimate": [1, 2, 2, 0, 3, 3, 1],
        "actual": [2, None, 2, 1, 2, 2, 0],
    })


def test_preparar_filtra_y_ordena():
    x = preparar(tabla_cruda())
    # Se van: la no terminada, la de estimado 0, la de real 0 y la fila duplicada.
    assert len(x) == 3
    assert list(x["fecha"].dt.day) == [1, 2, 4]               # ordenadas por fecha
    assert list(x["etiqueta"]) == ["@b", "@a", "@a"]            # primera etiqueta de cada tarea


def test_resumen_porcentajes_suman_100():
    info = resumen(preparar(tabla_cruda()))
    assert info["tareas"] == 3
    assert abs(info["pct_exacta"] + info["pct_se_paso"] + info["pct_sobro_tiempo"] - 100) < 0.2


def test_tabla_por_estimacion():
    t = tabla_por_estimacion(preparar(tabla_cruda()))
    fila = t[t["estimado"] == 3].iloc[0]
    assert fila["tareas"] == 1 and fila["real_promedio"] == 2


def serie_sintetica(n=200):
    """Tareas donde lo real es SIEMPRE 1 pomodoro más que lo estimado."""
    fechas = pd.date_range("2015-01-01", periods=n, freq="D")
    estimado = [1 + (i % 4) for i in range(n)]
    return pd.DataFrame({"fecha": fechas, "etiqueta": ["@a" if i % 2 else "@b" for i in range(n)],
                         "estimado": estimado, "real": [e + 1 for e in estimado]})


def test_particion_temporal_no_mezcla_fechas():
    x = serie_sintetica()
    entrenamiento, prueba = particion_temporal(x)
    assert len(entrenamiento) + len(prueba) == len(x)
    assert entrenamiento["fecha"].max() < prueba["fecha"].min()


def test_modelos_aprenden_un_sesgo_constante():
    entrenamiento, prueba = particion_temporal(serie_sintetica())
    tabla = comparar_modelos(entrenamiento, prueba).set_index("modelo")
    base = tabla.loc["Línea base: usar la estimación tal cual"]
    regresion = tabla.loc["Regresión lineal: real ~ estimado"]
    assert base["MAE_pomodoros"] == 1.0                     # siempre se queda corta en 1
    assert base["pct_caben_en_lo_reservado"] == 0.0         # nunca cabe en lo reservado
    assert regresion["MAE_pomodoros"] < 0.01                # la regresión aprende el +1
    assert regresion["pct_caben_en_lo_reservado"] == 100.0
    assert len(tabla) == 4                                  # base, 2 regresiones y k-NN
