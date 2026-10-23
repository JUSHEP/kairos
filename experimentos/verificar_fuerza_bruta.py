"""Verificación: ¿la búsqueda exacta encuentra el mismo valor que la fuerza bruta?

Uso (desde la carpeta raíz del proyecto):
    python experimentos/verificar_fuerza_bruta.py          # 640 instancias (semillas 0 a 639)
    python experimentos/verificar_fuerza_bruta.py 100      # otra cantidad

La fuerza bruta prueba TODAS las horas de inicio posibles de cada tarea, así que
solo funciona en instancias diminutas. Si en todas da el mismo valor que la
búsqueda exacta, queda comprobado en la práctica que poner cada tarea "lo antes
posible" (sin cambiar el orden) no hace perder el óptimo.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from kairos.busqueda import planificar_fuerza_bruta, planificar_optimo  # noqa: E402
from kairos.escenarios import generar_instancia_diminuta  # noqa: E402
from kairos.metricas import valor_plan  # noqa: E402
from kairos.restricciones import validar_plan  # noqa: E402


def main(cantidad: int = 640):
    iguales, diferentes = 0, []
    for semilla in range(cantidad):
        p = generar_instancia_diminuta(semilla)
        exacto, _ = planificar_optimo(p)
        assert validar_plan(p, exacto) == [], f"Plan inválido en la semilla {semilla}"
        if valor_plan(p, exacto) == valor_plan(p, planificar_fuerza_bruta(p)):
            iguales += 1
        else:
            diferentes.append(semilla)
    print(f"Instancias revisadas: {cantidad} | mismo valor que la fuerza bruta: {iguales}")
    if diferentes:
        print("Semillas con diferencia:", diferentes)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 640)
