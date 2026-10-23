"""Exploración del dataset público SiP como posible fuente para el módulo de aprendizaje.
Quedó como dataset de contraste: el seleccionado es el Renzo Pomodoro dataset
(ver experimentos/explorar_dataset_pomodoro.py).

Pregunta: ¿sirve este dataset para aprender a corregir la duración que una
persona estima para sus tareas?

Dataset: SiP (Software in Partnership), tareas de un equipo de desarrollo de
software con horas estimadas y reales. Repositorio:
https://github.com/Derek-Jones/SiP_dataset. Licencia CC BY-NC-ND 4.0: se
permite el uso no comercial con atribución, pero NO redistribuir versiones
modificadas. Por eso este script descarga los datos desde la fuente y no los
guarda en el repositorio.

Uso:
    python experimentos/explorar_dataset_sip.py
    (necesita internet; también funciona en Colab)

Pasos (el mismo proceso de aprendizaje de máquina visto en clase):
1. Filtrar: tareas terminadas, de una sola persona, estimadas en 8 h o menos
   (una escala parecida a la de las tareas de un estudiante).
2. Partición temporal: se entrena con el 75 % más antiguo y se prueba con el
   25 % más reciente. Así el modelo nunca aprende del futuro.
3. Comparar contra la línea base "usar la estimación tal cual" con MAE (error
   absoluto medio, en horas) y MSE.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

URL = "https://raw.githubusercontent.com/Derek-Jones/SiP_dataset/master/"


def cargar():
    tareas = pd.read_csv(URL + "Sip-task-info.csv", encoding="latin-1")
    fechas = pd.read_csv(URL + "est-act-dates.csv", encoding="latin-1").drop_duplicates("TaskNumber")
    return tareas, fechas


def filtrar(tareas, fechas):
    por_tarea = tareas["TaskNumber"].value_counts()
    x = tareas[tareas["TaskNumber"].isin(por_tarea[por_tarea == 1].index)]          # una sola persona
    x = x[x["StatusCode"].isin(["FINISHED", "COMPLETED", "RELEASED"])]               # terminadas
    x = x[(x["HoursEstimate"] > 0) & (x["HoursActual"] > 0) & (x["HoursEstimate"] <= 8)]
    x = x.merge(fechas[["TaskNumber", "EstimateOn"]], on="TaskNumber")
    x["fecha"] = pd.to_datetime(x["EstimateOn"], format="%d-%b-%y")
    return x.sort_values("fecha").reset_index(drop=True)


def caracteristicas(df, columnas=None):
    X = pd.get_dummies(df[["HoursEstimate", "Category", "DeveloperID"]].astype({"DeveloperID": str}),
                       columns=["Category", "DeveloperID"], dtype=float)
    return X if columnas is None else X.reindex(columns=columnas, fill_value=0.0)


def main():
    tareas, fechas = cargar()
    x = filtrar(tareas, fechas)
    ratio = x["HoursActual"] / x["HoursEstimate"]
    print(f"Registros originales: {len(tareas)} | tareas tras el filtro: {len(x)}")
    print(f"Personas: {x['DeveloperID'].nunique()} | periodo: {x['fecha'].min():%Y-%m} a {x['fecha'].max():%Y-%m}")
    print(f"Real == estimada exactamente: {100 * (ratio == 1).mean():.1f} %")
    print(f"Real > estimada (subestimación): {100 * (ratio > 1).mean():.1f} %")
    print(f"Mediana de real/estimada: {ratio.median():.2f}")

    corte = int(len(x) * 0.75)
    entrenamiento, prueba = x.iloc[:corte], x.iloc[corte:]
    y = prueba["HoursActual"].to_numpy()

    def reportar(nombre, prediccion):
        error = y - prediccion
        return {"modelo": nombre, "MAE_horas": round(np.abs(error).mean(), 3),
                "MSE": round(np.mean(error ** 2), 2)}

    filas = [reportar("Línea base: usar la estimación tal cual", prueba["HoursEstimate"].to_numpy())]
    simple = LinearRegression().fit(entrenamiento[["HoursEstimate"]], entrenamiento["HoursActual"])
    filas.append(reportar("Regresión lineal simple (estimación)",
                          simple.predict(prueba[["HoursEstimate"]])))
    columnas = caracteristicas(entrenamiento).columns
    multiple = LinearRegression().fit(caracteristicas(entrenamiento), entrenamiento["HoursActual"])
    filas.append(reportar("Regresión lineal múltiple (+ categoría + persona)",
                          multiple.predict(caracteristicas(prueba, columnas))))
    print(f"\nEntrenamiento: {len(entrenamiento)} tareas | prueba: {len(prueba)} tareas")
    print(pd.DataFrame(filas).to_string(index=False))


if __name__ == "__main__":
    main()
