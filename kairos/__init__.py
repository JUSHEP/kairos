"""Kairos: agente que planifica las tareas de un estudiante en su tiempo libre.

Módulos:
    modelo         qué es un problema (tareas, bloques fijos, calendario)
    datos          lectura de CSV/JSON
    restricciones  reglas duras y verificador independiente
    voraz          estrategias voraces (línea base)
    busqueda       búsqueda exacta (BPP con memoria) y fuerza bruta de control
    planificador   ejecutar cualquier estrategia y medir su tiempo
    metricas       métricas del plan
    reporte        plan en tabla y alertas de tareas que no caben
    escenarios     casos didácticos y escenarios sintéticos
    visualizacion  calendario del plan
"""
__version__ = "0.1.0"
