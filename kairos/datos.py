"""Lectura de los datos del estudiante desde archivos CSV y JSON.

Formatos (ver la carpeta datos/ejemplo):

tareas.csv
    id,nombre,tipo,duracion_min,fecha_limite,prioridad
    T1,Taller de cálculo,taller,120,2026-10-28 07:00,4

bloques_fijos.csv
    nombre,dia_semana,hora_inicio,hora_fin
    Cálculo,lunes,07:00,09:00

configuracion.json
    {"fecha_inicio": "2026-10-26", "dias": 7, "hora_inicio_dia": "07:00",
     "hora_fin_dia": "22:00", "minutos_por_bloque": 30,
     "max_horas_tareas_dia": 5, "descanso_min": 30}
"""
from __future__ import annotations

import csv
import json
import unicodedata
from datetime import date, datetime, time
from pathlib import Path

from .modelo import DIAS_SEMANA, BloqueFijo, Configuracion, Problema, Tarea


def _sin_tildes(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.strip().lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def _hora(texto: str) -> time:
    return datetime.strptime(texto.strip(), "%H:%M").time()


def leer_tareas(ruta) -> list[Tarea]:
    tareas = []
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f):
            tareas.append(Tarea(
                id=fila["id"].strip(),
                nombre=fila["nombre"].strip(),
                duracion_min=int(fila["duracion_min"]),
                fecha_limite=datetime.strptime(fila["fecha_limite"].strip(), "%Y-%m-%d %H:%M"),
                prioridad=int(fila["prioridad"]),
                tipo=fila.get("tipo", "otro").strip() or "otro",
            ))
    return tareas


def leer_bloques_fijos(ruta) -> list[BloqueFijo]:
    bloques = []
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f):
            dia = _sin_tildes(fila["dia_semana"])
            if dia not in DIAS_SEMANA:
                raise ValueError(f"Día de la semana no reconocido: {fila['dia_semana']}")
            bloques.append(BloqueFijo(
                nombre=fila["nombre"].strip(),
                dia_semana=DIAS_SEMANA.index(dia),
                hora_inicio=_hora(fila["hora_inicio"]),
                hora_fin=_hora(fila["hora_fin"]),
            ))
    return bloques


def leer_configuracion(ruta) -> Configuracion:
    with open(ruta, encoding="utf-8") as f:
        c = json.load(f)
    return Configuracion(
        fecha_inicio=date.fromisoformat(c["fecha_inicio"]),
        dias=int(c.get("dias", 7)),
        hora_inicio_dia=_hora(c.get("hora_inicio_dia", "07:00")),
        hora_fin_dia=_hora(c.get("hora_fin_dia", "22:00")),
        minutos_por_bloque=int(c.get("minutos_por_bloque", 30)),
        max_horas_tareas_dia=float(c.get("max_horas_tareas_dia", 5)),
        descanso_min=int(c.get("descanso_min", 30)),
    )


def cargar_problema(carpeta) -> Problema:
    """Lee tareas.csv, bloques_fijos.csv y configuracion.json de una carpeta."""
    carpeta = Path(carpeta)
    return Problema(
        tareas=leer_tareas(carpeta / "tareas.csv"),
        bloques_fijos=leer_bloques_fijos(carpeta / "bloques_fijos.csv"),
        config=leer_configuracion(carpeta / "configuracion.json"),
    )
