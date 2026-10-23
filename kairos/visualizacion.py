"""Gráficas de Kairos: el plan como calendario y los resultados del experimento.

Convenciones visuales:
- Tareas: un solo tono azul, más oscuro = mayor prioridad (escala ordinal 1 a 5).
- Bloques fijos: gris neutro. Fuera del horario del día: fondo blanco.
- El nombre completo de cada tarea va en la tabla del plan; en el calendario
  solo se escribe lo que cabe dentro del bloque.
"""
from __future__ import annotations

import sys
import textwrap
from datetime import timedelta

import matplotlib

if "ipykernel" not in sys.modules:   # en scripts no hace falta ventana; en Colab/Jupyter se muestran en el cuaderno
    matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

from .modelo import DIAS_CORTOS  # noqa: E402

SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
TINTA_TENUE = "#898781"
REJILLA = "#e1e0d9"
FIJO = "#ecebe6"
# Prioridad 1..5 -> tono azul de claro a oscuro, y color del texto encima.
AZULES = {1: "#86b6ef", 2: "#5598e7", 3: "#2a78d6", 4: "#1c5cab", 5: "#104281"}
TEXTO_EN_AZUL = {1: TINTA, 2: TINTA, 3: "#ffffff", 4: "#ffffff", 5: "#ffffff"}
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]   # paleta categórica (3 series)


def _estilo(ax):
    ax.set_facecolor(SUPERFICIE)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color("#c3c2b7")
    ax.tick_params(colors=TINTA_SECUNDARIA, labelsize=9)


def _horas(t):
    return t.hour + t.minute / 60


def _coma(texto: str) -> str:
    """Usa coma decimal, como se escribe en Colombia."""
    return texto.replace(".", ",")


def dibujar_plan(problema, plan, titulo="Plan propuesto por Kairos", ruta=None):
    """Calendario semanal: columnas = días, filas = horas."""
    cfg = problema.config
    h_ini, h_fin = _horas(cfg.hora_inicio_dia), _horas(cfg.hora_fin_dia)
    dias = cfg.dias
    fig, ax = plt.subplots(figsize=(1.75 * dias + 1.2, 0.5 * (h_fin - h_ini) + 1.6))
    fig.patch.set_facecolor(SUPERFICIE)
    _estilo(ax)
    margen_x, margen_y = 0.03, 0.03   # deja un hueco claro entre bloques vecinos

    # Bloques fijos (recortados al horario del día).
    for d in range(dias):
        fecha = cfg.fecha_inicio + timedelta(days=d)
        for b in problema.bloques_fijos:
            if b.dia_semana != fecha.weekday():
                continue
            y0, y1 = max(_horas(b.hora_inicio), h_ini), min(_horas(b.hora_fin), h_fin)
            if y1 <= y0:
                continue
            ax.add_patch(Rectangle((d + margen_x, y0 + margen_y), 1 - 2 * margen_x,
                                   y1 - y0 - 2 * margen_y, facecolor=FIJO, linewidth=0))
            if y1 - y0 >= 0.5:
                ax.text(d + 0.5, (y0 + y1) / 2, b.nombre, ha="center", va="center",
                        fontsize=7, color=TINTA_SECUNDARIA)

    # Tareas del plan.
    for i, s in plan.items():
        t = problema.tareas[i]
        ini = problema.hora_de_bloque(s)
        d = problema.dia_de(s)
        y0 = ini.hour + ini.minute / 60
        alto = problema.dur[i] * problema.minutos_por_bloque / 60
        ax.add_patch(Rectangle((d + margen_x, y0 + margen_y), 1 - 2 * margen_x,
                               alto - 2 * margen_y, facecolor=AZULES[t.prioridad], linewidth=0))
        lineas_que_caben = max(1, int((alto - 0.1) / 0.32))
        lineas = textwrap.wrap(f"{t.id} · {t.nombre}", width=26)
        if len(lineas) > lineas_que_caben:
            lineas = lineas[:lineas_que_caben]
            lineas[-1] = lineas[-1][:24].rstrip() + "…"
        ax.text(d + 0.07, y0 + 0.1, "\n".join(lineas), ha="left", va="top", fontsize=6.5,
                color=TEXTO_EN_AZUL[t.prioridad], linespacing=1.15)

    ax.set_xlim(0, dias)
    ax.set_ylim(h_fin, h_ini)                       # la mañana arriba
    etiquetas = []
    for d in range(dias):
        fecha = cfg.fecha_inicio + timedelta(days=d)
        etiquetas.append(f"{DIAS_CORTOS[fecha.weekday()]} {fecha:%d/%m}")
    ax.set_xticks([d + 0.5 for d in range(dias)], etiquetas)
    ax.xaxis.tick_top()
    horas = range(int(h_ini), int(h_fin) + 1)
    ax.set_yticks(list(horas), [f"{h:02d}:00" for h in horas])
    ax.grid(axis="y", color=REJILLA, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", length=0)
    for d in range(1, dias):
        ax.axvline(d, color=REJILLA, linewidth=0.6, zorder=0)

    leyenda = [Patch(facecolor=FIJO, label="Bloque fijo")]
    leyenda += [Patch(facecolor=AZULES[p], label=f"Prioridad {p}") for p in range(1, 6)]
    ax.legend(handles=leyenda, loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=6,
              frameon=False, fontsize=8, labelcolor=TINTA_SECUNDARIA)
    ax.set_title(titulo, loc="left", fontsize=12, color=TINTA, pad=28)
    fig.tight_layout()
    if ruta:
        fig.savefig(ruta, dpi=160, facecolor=SUPERFICIE)
    return fig


def dibujar_brecha(resumen, ruta=None):
    """Brecha promedio frente al óptimo (%) de cada regla voraz según el número de tareas.

    `resumen` es un DataFrame con columnas: n_tareas, estrategia, brecha_media.
    """
    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor(SUPERFICIE)
    _estilo(ax)
    nombres = {"voraz_prioridad": "Voraz: prioridad", "voraz_fecha_limite": "Voraz: fecha límite",
               "voraz_razon": "Voraz: prioridad/duración"}
    for color, (clave, etiqueta) in zip(SERIES, nombres.items()):
        datos = resumen[resumen["estrategia"] == clave].sort_values("n_tareas")
        ax.plot(datos["n_tareas"], datos["brecha_media"], color=color, linewidth=2,
                marker="o", markersize=7, markeredgecolor=SUPERFICIE, markeredgewidth=1.5,
                label=etiqueta, solid_capstyle="round")
        ultimo = datos.iloc[-1]
        ax.annotate(_coma(f"{ultimo['brecha_media']:.1f} %"),
                    (ultimo["n_tareas"], ultimo["brecha_media"]),
                    xytext=(8, 0), textcoords="offset points", va="center", fontsize=8,
                    color=TINTA_SECUNDARIA)
    ax.set_xticks(sorted(resumen["n_tareas"].unique()))
    ax.set_xlabel("Número de tareas por escenario", color=TINTA_SECUNDARIA, fontsize=9)
    ax.set_ylabel("Brecha promedio frente al óptimo (%)", color=TINTA_SECUNDARIA, fontsize=9)
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", color=REJILLA, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8, labelcolor=TINTA_SECUNDARIA, loc="upper left")
    ax.set_title("¿Cuánto valor pierden las reglas voraces?", loc="left", fontsize=11, color=TINTA)
    fig.tight_layout()
    if ruta:
        fig.savefig(ruta, dpi=160, facecolor=SUPERFICIE)
    return fig


def dibujar_real_vs_estimado(tabla, minimo=30, resaltar=(1, 4), ruta=None):
    """Duración real promedio según lo estimado (dataset Pomodoro).

    `tabla` es un DataFrame con columnas: estimado, tareas, real_promedio. Solo se
    dibujan las estimaciones con al menos `minimo` tareas. La línea punteada es
    "real = estimado": un punto por encima significa que esas tareas tardaron más
    de lo estimado.
    """
    datos = tabla[tabla["tareas"] >= minimo].sort_values("estimado")
    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor(SUPERFICIE)
    _estilo(ax)
    tope = float(max(datos["estimado"].max(), datos["real_promedio"].max())) + 0.5
    ax.plot([0, tope], [0, tope], color=TINTA_TENUE, linewidth=1.2, linestyle=(0, (4, 3)), zorder=1)
    ax.annotate("real = estimado", (tope - 0.6, tope - 0.6), xytext=(-4, 6), textcoords="offset points",
                ha="right", fontsize=8, color=TINTA_TENUE, rotation=0)
    ax.plot(datos["estimado"], datos["real_promedio"], linestyle="none", marker="o", markersize=8,
            color=SERIES[0], markeredgecolor=SUPERFICIE, markeredgewidth=1.5, zorder=3)
    for _, fila in datos[datos["estimado"].isin(resaltar)].iterrows():
        arriba = fila["real_promedio"] >= fila["estimado"]
        ax.annotate(_coma(f"{fila['real_promedio']:.2f}"), (fila["estimado"], fila["real_promedio"]),
                    xytext=(0, 10 if arriba else -14), textcoords="offset points", ha="center",
                    fontsize=8, color=TINTA_SECUNDARIA)
    ax.set_xlim(0, tope)
    ax.set_ylim(0, tope)
    ax.set_xticks(list(datos["estimado"]), [f"{v:g}" for v in datos["estimado"]])
    ax.set_xlabel("Pomodoros estimados (1 pomodoro = 25 min)", color=TINTA_SECUNDARIA, fontsize=9)
    ax.set_ylabel("Pomodoros reales (promedio)", color=TINTA_SECUNDARIA, fontsize=9)
    ax.grid(axis="y", color=REJILLA, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_title("Duración real promedio según lo estimado", loc="left", fontsize=11, color=TINTA)
    fig.text(0.01, 0.01, f"Solo estimaciones con {minimo} tareas o más. Fuente: Renzo Pomodoro dataset.",
             fontsize=7, color=TINTA_TENUE)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    if ruta:
        fig.savefig(ruta, dpi=160, facecolor=SUPERFICIE)
    return fig


def dibujar_tiempos(tiempos, ruta=None):
    """Tiempo de la búsqueda exacta (escala logarítmica) según el número de tareas.

    `tiempos` es un DataFrame con columnas: n_tareas, tiempo_ms_mediana.
    """
    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor(SUPERFICIE)
    _estilo(ax)
    datos = tiempos.sort_values("n_tareas")
    ax.plot(datos["n_tareas"], datos["tiempo_ms_mediana"], color=SERIES[0], linewidth=2,
            marker="o", markersize=7, markeredgecolor=SUPERFICIE, markeredgewidth=1.5)
    for _, fila in datos.iterrows():
        ms = fila["tiempo_ms_mediana"]
        texto = f"{ms / 1000:.1f} s" if ms >= 1000 else f"{ms:.0f} ms" if ms >= 1 else f"{ms:.2f} ms"
        ax.annotate(_coma(texto), (fila["n_tareas"], ms), xytext=(0, 9), textcoords="offset points",
                    ha="center", fontsize=8, color=TINTA_SECUNDARIA)
    ax.set_yscale("log")
    marcas = [0.1, 1, 10, 100, 1000, 10000]
    ax.set_yticks(marcas, ["0,1 ms", "1 ms", "10 ms", "100 ms", "1 s", "10 s"])
    ax.minorticks_off()
    ax.set_xticks(list(datos["n_tareas"]))
    ax.set_xlabel("Número de tareas por escenario", color=TINTA_SECUNDARIA, fontsize=9)
    ax.set_ylabel("Tiempo de cómputo (mediana, escala logarítmica)", color=TINTA_SECUNDARIA, fontsize=9)
    ax.grid(axis="y", color=REJILLA, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_title("Tiempo de la búsqueda exacta", loc="left", fontsize=11, color=TINTA)
    fig.tight_layout()
    if ruta:
        fig.savefig(ruta, dpi=160, facecolor=SUPERFICIE)
    return fig
