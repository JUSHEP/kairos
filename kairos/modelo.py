"""Modelo de datos de Kairos.

Este archivo describe QUÉ es un problema de planificación. No contiene
ningún algoritmo. Define:

- las tareas pendientes del estudiante (Tarea),
- los compromisos que no se pueden mover, como clases, trabajo o transporte (BloqueFijo),
- los parámetros del horizonte y de bienestar (Configuracion),
- y el calendario partido en bloques de igual duración, 30 minutos por defecto (Problema).

Convención usada en todo el proyecto: un PLAN es un diccionario
{indice_de_tarea: bloque_de_inicio}. Si una tarea no aparece en el
diccionario, quedó sin programar.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

DIAS_SEMANA = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
DIAS_CORTOS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]


@dataclass(frozen=True)
class Tarea:
    """Actividad pendiente que Kairos debe ubicar en el tiempo libre."""

    id: str
    nombre: str
    duracion_min: int        # duración estimada por el propio estudiante
    fecha_limite: datetime   # la tarea debe TERMINAR a más tardar en este momento
    prioridad: int           # 1 = baja ... 5 = alta (la define el estudiante)
    tipo: str = "otro"       # estudio, taller, lectura, proyecto, informe u otro

    def __post_init__(self):
        if self.duracion_min <= 0:
            raise ValueError(f"{self.id}: la duración debe ser mayor que 0")
        if not 1 <= self.prioridad <= 5:
            raise ValueError(f"{self.id}: la prioridad debe estar entre 1 y 5")


@dataclass(frozen=True)
class BloqueFijo:
    """Compromiso inamovible que se repite cada semana (por ejemplo, una clase)."""

    nombre: str
    dia_semana: int          # 0 = lunes ... 6 = domingo
    hora_inicio: time
    hora_fin: time

    def __post_init__(self):
        if not 0 <= self.dia_semana <= 6:
            raise ValueError(f"{self.nombre}: día de la semana inválido")
        if self.hora_fin <= self.hora_inicio:
            raise ValueError(f"{self.nombre}: la hora de fin debe ser posterior a la de inicio")


@dataclass(frozen=True)
class Configuracion:
    """Parámetros del horizonte de planificación y de bienestar."""

    fecha_inicio: date
    dias: int = 7
    hora_inicio_dia: time = time(7, 0)    # antes de esta hora no se programan tareas
    hora_fin_dia: time = time(22, 0)      # después de esta hora no se programan tareas
    minutos_por_bloque: int = 30
    max_horas_tareas_dia: float = 5.0     # tope de horas de tareas por día (evita sobrecarga)
    descanso_min: int = 30                # descanso mínimo entre dos tareas del mismo día

    def __post_init__(self):
        if self.dias < 1:
            raise ValueError("El horizonte debe tener al menos un día")
        if self.hora_fin_dia <= self.hora_inicio_dia:
            raise ValueError("hora_fin_dia debe ser posterior a hora_inicio_dia")


def _minutos(h: time) -> int:
    return h.hour * 60 + h.minute


class Problema:
    """Problema discretizado en bloques de tiempo.

    El horizonte se parte en bloques de `minutos_por_bloque` minutos que cubren
    las 24 horas de cada día. El bloque k empieza en
    inicio_del_horizonte + k * minutos_por_bloque. Un bloque está "libre" si
    cae completo dentro del horario del día y no se cruza con ningún bloque fijo.

    Atributos que usan los algoritmos (medidos en número de bloques):
        dur[i]      duración de la tarea i
        limite[i]   la tarea i debe terminar en un bloque <= limite[i]
        libre[k]    True si el bloque k está disponible
        racha[k]    cuántos bloques libres seguidos hay desde k (incluido)
        max_carga   máximo de bloques de tareas por día
        descanso    bloques mínimos entre dos tareas del mismo día
    """

    def __init__(self, tareas, bloques_fijos, config: Configuracion):
        self.tareas = list(tareas)
        self.bloques_fijos = list(bloques_fijos)
        self.config = config

        m = config.minutos_por_bloque
        if (24 * 60) % m != 0:
            raise ValueError("minutos_por_bloque debe dividir exactamente un día (15, 30 o 60)")
        self.minutos_por_bloque = m
        self.bloques_por_dia = 24 * 60 // m
        self.total_bloques = self.bloques_por_dia * config.dias
        self.inicio = datetime.combine(config.fecha_inicio, time(0, 0))

        self.libre = self._calcular_libres()
        self.racha = self._calcular_rachas()
        # Las duraciones se redondean hacia arriba al bloque completo.
        self.dur = [math.ceil(t.duracion_min / m) for t in self.tareas]
        self.limite = [self.bloque_limite(t.fecha_limite) for t in self.tareas]
        self.max_carga = int(config.max_horas_tareas_dia * 60 // m)
        self.descanso = math.ceil(config.descanso_min / m)

    # ---------- conversión entre tiempo real y bloques ----------
    def hora_de_bloque(self, k: int) -> datetime:
        """Momento real en que empieza el bloque k."""
        return self.inicio + timedelta(minutes=k * self.minutos_por_bloque)

    def bloque_limite(self, momento: datetime) -> int:
        """Cantidad de bloques que terminan antes o justo en `momento`."""
        minutos = (momento - self.inicio).total_seconds() / 60
        k = math.floor(minutos / self.minutos_por_bloque)
        return max(0, min(self.total_bloques, k))

    def dia_de(self, k: int) -> int:
        """Índice del día (0 = primer día del horizonte) al que pertenece el bloque k."""
        return k // self.bloques_por_dia

    # ---------- disponibilidad ----------
    def _calcular_libres(self):
        m = self.minutos_por_bloque
        ini_dia = _minutos(self.config.hora_inicio_dia)
        fin_dia = _minutos(self.config.hora_fin_dia)
        libre = []
        for d in range(self.config.dias):
            dia_semana = (self.config.fecha_inicio + timedelta(days=d)).weekday()
            fijos_hoy = [(_minutos(b.hora_inicio), _minutos(b.hora_fin))
                         for b in self.bloques_fijos if b.dia_semana == dia_semana]
            for j in range(self.bloques_por_dia):
                a, b = j * m, (j + 1) * m          # minutos del día que ocupa el bloque
                dentro = ini_dia <= a and b <= fin_dia
                choca = any(a < f_fin and f_ini < b for f_ini, f_fin in fijos_hoy)
                libre.append(dentro and not choca)
        return libre

    def _calcular_rachas(self):
        racha = [0] * (self.total_bloques + 1)
        for k in range(self.total_bloques - 1, -1, -1):
            racha[k] = racha[k + 1] + 1 if self.libre[k] else 0
        return racha

    def cabe_en_libres(self, inicio: int, dur: int) -> bool:
        """True si los bloques [inicio, inicio + dur) están libres y en un mismo día."""
        if inicio < 0 or inicio + dur > self.total_bloques:
            return False
        return self.racha[inicio] >= dur and self.dia_de(inicio) == self.dia_de(inicio + dur - 1)

    def horas_libres(self) -> float:
        """Horas libres del horizonte (sin contar el tope diario ni los descansos)."""
        return sum(self.libre) * self.minutos_por_bloque / 60


@dataclass
class Resultado:
    """Lo que devuelve una estrategia de planificación."""

    estrategia: str
    plan: dict               # {indice_de_tarea: bloque_de_inicio}
    segundos: float
    estados: int | None = None   # estados explorados (solo en la búsqueda exacta)
