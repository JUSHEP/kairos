"""Módulo de aprendizaje (primera versión): ¿cuánto dura de verdad una tarea?

Kairos planifica con la duración que la persona estima. Si la estimación falla,
el plan falla. Este módulo aprende del historial cuánto suele durar de verdad
una tarea, según lo que se estimó y el tipo de tarea.

Dataset seleccionado: Renzo Pomodoro dataset (Jones y Borgatti, 2019).
- Una persona planeó sus tareas del día, entre 2009 y 2019, con la técnica
  Pomodoro: estimaba cada tarea en pomodoros (bloques de 25 minutos de trabajo)
  y luego anotaba cuántos gastó de verdad.
- Columnas que usamos: date (fecha), estimate (pomodoros estimados), actual
  (pomodoros reales), DONE (1 si la tarea quedó terminada ese día) y X.words
  (etiquetas como @planning; la primera se usa como tipo de tarea).
- Fuente: https://github.com/Derek-Jones/renzo-pomodoro. El repositorio no
  declara licencia. Lo usamos solo con fines académicos, citando la fuente, y
  no lo subimos a nuestro repositorio: se descarga al ejecutar y la copia local
  queda en datos/externos/, que está en .gitignore.

Proceso (el mismo visto en clase):
1. Preparar: quitar filas duplicadas y quedarse con tareas terminadas que
   tengan estimación y registro real mayores que cero.
2. Partición temporal: entrenar con lo anterior a una fecha de corte (cerca del
   75 % de las tareas) y probar con lo posterior. Así el modelo nunca aprende
   del futuro.
3. Comparar contra la línea base "usar la estimación tal cual".
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import KNeighborsRegressor

URL_POMODORO = "https://raw.githubusercontent.com/Derek-Jones/renzo-pomodoro/master/all-tasks.csv"
CACHE_POMODORO = Path(__file__).resolve().parents[1] / "datos" / "externos" / "renzo-pomodoro.csv"
MINUTOS_POR_POMODORO = 25
N_ETIQUETAS = 10                 # tipos de tarea: las 10 etiquetas más frecuentes; el resto es "otra"
VALORES_K = (5, 10, 25, 50, 100)


def cargar_pomodoro(ruta: Path | str = CACHE_POMODORO) -> pd.DataFrame:
    """Lee el dataset original. Si no hay copia local, lo descarga de la fuente."""
    ruta = Path(ruta)
    if not ruta.exists():
        ruta.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(URL_POMODORO, ruta)
    return pd.read_csv(ruta)


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    """Tareas terminadas con estimado y real > 0, ordenadas por fecha."""
    x = df.drop_duplicates()
    x = x[(x["DONE"] == 1) & (x["estimate"] > 0) & (x["actual"] > 0)].copy()
    x["fecha"] = pd.to_datetime(x["date"])
    x["etiqueta"] = x["X.words"].fillna("(sin etiqueta)").str.split(",").str[0].str.strip()
    x = x.rename(columns={"estimate": "estimado", "actual": "real"})
    x = x.sort_values("fecha", kind="stable").reset_index(drop=True)
    return x[["fecha", "etiqueta", "estimado", "real"]]


def resumen(x: pd.DataFrame) -> dict:
    """Qué tan buena es la estimación original (antes de cualquier modelo)."""
    razon = x["real"] / x["estimado"]
    return {
        "tareas": len(x),
        "dias_distintos": x["fecha"].dt.normalize().nunique(),
        "desde": x["fecha"].min().date().isoformat(),
        "hasta": x["fecha"].max().date().isoformat(),
        "etiquetas_distintas": x["etiqueta"].nunique(),
        "pct_exacta": round(100 * (razon == 1).mean(), 1),
        "pct_se_paso": round(100 * (razon > 1).mean(), 1),
        "pct_sobro_tiempo": round(100 * (razon < 1).mean(), 1),
        "real_total_sobre_estimado_total": round(x["real"].sum() / x["estimado"].sum(), 3),
    }


def tabla_por_estimacion(x: pd.DataFrame) -> pd.DataFrame:
    """Para cada estimación (en pomodoros), cuántas tareas hay y cuánto duraron de verdad."""
    t = x.groupby("estimado")["real"].agg(tareas="count", real_promedio="mean", real_mediana="median")
    t["real_promedio"] = t["real_promedio"].round(2)
    return t.reset_index()


def particion_temporal(x: pd.DataFrame, fraccion: float = 0.75):
    """Entrenamiento: antes de la fecha de corte. Prueba: desde la fecha de corte.

    Se corta por fecha (no por fila) para que un mismo día no quede repartido
    entre entrenamiento y prueba.
    """
    fecha_corte = x["fecha"].iloc[int(len(x) * fraccion)]
    return x[x["fecha"] < fecha_corte], x[x["fecha"] >= fecha_corte]


def _caracteristicas(d: pd.DataFrame, etiquetas: list[str]) -> pd.DataFrame:
    """Estimado + tipo de tarea en columnas 0/1 (codificación one-hot)."""
    tipo = d["etiqueta"].where(d["etiqueta"].isin(etiquetas), "otra")
    X = pd.get_dummies(tipo, dtype=float).reindex(columns=list(etiquetas) + ["otra"], fill_value=0.0)
    X.insert(0, "estimado", d["estimado"].to_numpy())
    return X


def elegir_k(entrenamiento: pd.DataFrame, etiquetas: list[str], valores=VALORES_K) -> int:
    """Elige k para k-NN con una validación DENTRO del entrenamiento (sin mirar la prueba).

    Se separa el 20 % más reciente del entrenamiento, se prueba cada k y se
    queda el de menor MAE.
    """
    a, v = particion_temporal(entrenamiento, 0.8)
    mejor_k, mejor_mae = None, None
    for k in valores:
        if k > len(a):
            break
        modelo = KNeighborsRegressor(n_neighbors=k).fit(_caracteristicas(a, etiquetas), a["real"])
        mae = np.abs(v["real"].to_numpy() - modelo.predict(_caracteristicas(v, etiquetas))).mean()
        if mejor_mae is None or mae < mejor_mae:
            mejor_k, mejor_mae = k, mae
    return mejor_k


def _metricas(nombre: str, real: np.ndarray, prediccion: np.ndarray) -> dict:
    """Métricas del modelo (MAE, MSE) y del planificador (cuánto cabe en lo reservado).

    Kairos reserva bloques completos, así que lo reservado es la predicción
    redondeada hacia arriba.
    """
    error = real - prediccion
    reservado = np.ceil(prediccion)
    return {
        "modelo": nombre,
        "MAE_pomodoros": round(float(np.abs(error).mean()), 3),
        "MAE_minutos": round(float(np.abs(error).mean() * MINUTOS_POR_POMODORO), 1),
        "MSE": round(float(np.mean(error ** 2)), 3),
        "pct_caben_en_lo_reservado": round(float(100 * (real <= reservado).mean()), 1),
        "reservado_sobre_real": round(float(reservado.sum() / real.sum()), 3),
    }


def comparar_modelos(entrenamiento: pd.DataFrame, prueba: pd.DataFrame) -> pd.DataFrame:
    """Línea base frente a regresión lineal y k-NN, evaluados en la prueba."""
    etiquetas = list(entrenamiento["etiqueta"].value_counts().index[:N_ETIQUETAS])
    real = prueba["real"].to_numpy(dtype=float)
    filas = [_metricas("Línea base: usar la estimación tal cual", real,
                       prueba["estimado"].to_numpy(dtype=float))]

    simple = LinearRegression().fit(entrenamiento[["estimado"]], entrenamiento["real"])
    filas.append(_metricas("Regresión lineal: real ~ estimado", real,
                           simple.predict(prueba[["estimado"]])))

    multiple = LinearRegression().fit(_caracteristicas(entrenamiento, etiquetas), entrenamiento["real"])
    filas.append(_metricas("Regresión lineal: real ~ estimado + tipo", real,
                           multiple.predict(_caracteristicas(prueba, etiquetas))))

    k = elegir_k(entrenamiento, etiquetas)
    vecinos = KNeighborsRegressor(n_neighbors=k).fit(_caracteristicas(entrenamiento, etiquetas),
                                                     entrenamiento["real"])
    filas.append(_metricas(f"k-NN (k = {k}, elegido con validación): estimado + tipo", real,
                           vecinos.predict(_caracteristicas(prueba, etiquetas))))
    return pd.DataFrame(filas)


def coeficientes_regresion_simple(entrenamiento: pd.DataFrame) -> tuple[float, float]:
    """Intercepto y pendiente de real = a + b * estimado (para explicar el modelo)."""
    m = LinearRegression().fit(entrenamiento[["estimado"]], entrenamiento["real"])
    return float(m.intercept_), float(m.coef_[0])
