# Kairos

**Planificador inteligente del tiempo diario basado en algoritmos de optimización.**

Kairos es un agente que recibe las tareas pendientes de un estudiante universitario y su horario fijo. Para cada tarea tiene la duración estimada, la fecha límite y la prioridad. El horario fijo incluye clases, trabajo y transporte. Con eso, Kairos propone en qué bloque hacer cada tarea sin romper ninguna restricción y cubriendo la mayor prioridad posible. Si algo no cabe, avisa por qué.

Proyecto de la asignatura Inteligencia Artificial, 2026-2. Equipo: Yeimar Bernal, Jair Ortiz y Mateo Orozco.

> **Estado (23 de octubre de 2026): avance del tercer corte.** El núcleo de planificación funciona y está probado. El dataset del módulo de aprendizaje ya está seleccionado y explorado (Renzo Pomodoro dataset). Falta conectar ese módulo al planificador y recolectar datos propios. Ver [Próximos pasos](#próximos-pasos).

## El problema en una frase

Dadas unas tareas con duración, fecha límite y prioridad, y unos bloques de tiempo libres, hay que decidir **qué tareas programar y cuándo**. Debe cumplirse que:

| Restricción | Qué exige |
|---|---|
| R1 Disponibilidad | Solo se usan bloques libres (dentro del horario del día y fuera de los bloques fijos), y una tarea no se parte entre días. |
| R2 No solapamiento | Dos tareas no se cruzan. Entre tareas del mismo día queda un descanso mínimo. |
| R3 Fecha límite | Cada tarea termina antes de su fecha límite. |
| R4 Carga diaria | Las tareas de un día no superan el tope de horas definido por el estudiante. |

**Objetivo:** maximizar la suma de prioridades de las tareas programadas. Si hay empate, se prefiere el plan que termina antes.

## Estrategias implementadas

| Estrategia | Cómo decide | Papel |
|---|---|---|
| Voraz: prioridad | Primero lo más importante, en el primer hueco donde quepa | Línea base |
| Voraz: fecha límite | Primero lo más urgente | Línea base |
| Voraz: prioridad/duración | Primero lo que da más prioridad por hora (regla de la primera entrega) | Línea base |
| Búsqueda exacta | Búsqueda en profundidad (BPP) sobre el orden de las tareas, con memoria de estados repetidos | Estrategia principal |

La búsqueda exacta no prueba todas las horas de inicio. Decide el **orden** de las tareas y ubica cada una lo antes posible. Esto no hace perder el óptimo: las pruebas automáticas lo comparan con una fuerza bruta que sí prueba todas las horas. La explicación completa está en `kairos/busqueda.py`.

## Resultados preliminares (escenarios sintéticos)

Se usaron 100 semanas sintéticas, 20 por cada tamaño (4, 6, 8, 10 y 12 tareas). **Son datos construidos por el equipo, no de estudiantes reales.**

| Estrategia | Violaciones | Prioridad cubierta (media) | Brecha frente al óptimo (media / máx.) | Escenarios en el óptimo |
|---|---|---|---|---|
| Búsqueda exacta | 0 | 93,7 % | 0 % / 0 % | 100 % |
| Voraz: fecha límite | 0 | 90,9 % | 3,3 % / 25,0 % | 67 % |
| Voraz: prioridad | 0 | 86,4 % | 7,9 % / 25,0 % | 27 % |
| Voraz: prioridad/duración | 0 | 83,9 % | 10,7 % / 37,5 % | 23 % |

Con hasta 12 tareas, la búsqueda exacta tardó menos de medio segundo en todos los escenarios. Con 18 tareas la mediana es de unos 4 s, y el tiempo crece de forma exponencial. Las cifras de tiempo cambian un poco según el computador. Los detalles están en `resultados/`.

## Módulo de aprendizaje: dataset seleccionado

El planificador usa la duración que estima el estudiante, y la gente suele quedarse corta. El módulo de aprendizaje estimará **cuánto dura de verdad una tarea** a partir del historial. Es un problema de regresión.

**Dataset: Renzo Pomodoro dataset** (Jones y Borgatti, 2019), https://github.com/Derek-Jones/renzo-pomodoro. Una persona planeó sus tareas del día entre 2009 y 2019. Estimaba cada una en pomodoros (bloques de 25 min) y después anotaba cuántos gastó. Es la misma decisión que toma Kairos: cuántos bloques reservar.

| Dato | Valor |
|---|---|
| Filas del archivo original | 17.764 |
| Tareas terminadas con estimado y real mayores que cero | 7.274, en 1.905 días distintos (2009-04-09 a 2019-02-07) |
| Salieron exactas / se pasó / sobró tiempo | 53,3 % / 27,2 % / 19,6 % |
| Duración real promedio de las tareas estimadas en 1 y en 4 pomodoros | 1,41 y 3,77 |

Primera comparación (entrenamiento antes del 6 de noviembre de 2014, prueba después; partición temporal):

| Modelo | MAE | MSE | Tareas que caben en lo reservado | Reservado / real |
|---|---|---|---|---|
| Línea base: usar la estimación tal cual | 0,90 pomodoros (22,4 min) | 2,45 | 71,4 % | 0,90 |
| Regresión lineal: real ~ estimado | 1,00 (25,1 min) | 2,32 | 84,0 % | 1,21 |
| Regresión lineal: real ~ estimado + tipo | 0,97 (24,3 min) | 2,33 | 83,9 % | 1,20 |
| k-NN (k = 5, elegido con validación) | 0,94 (23,6 min) | 2,40 | 79,2 % | 1,12 |

En MAE ningún modelo le gana todavía a la línea base. La regresión reduce los errores grandes (MSE) y hace que más tareas quepan en lo reservado, a cambio de reservar más tiempo. **Límites:** es una sola persona y no es estudiante, y el repositorio no declara licencia (ver [Datos y privacidad](#datos-y-privacidad)). Por eso el siguiente paso es aplicar el mismo proceso a datos propios. El código está en `kairos/duraciones.py` y `experimentos/explorar_dataset_pomodoro.py`.

Otros datasets evaluados: SiP (tareas de software de una empresa, en horas; quedó como contraste) y el CSV de estudiantes del curso (no tiene duraciones de tareas).

## Cómo ejecutarlo

### En Google Colab (recomendado para la demo)
1. Abran `notebooks/demo_kairos.ipynb` en Colab: *Archivo → Subir cuaderno*, o desde GitHub.
2. En la primera celda cambien `REPO_URL` por la dirección de este repositorio.
3. *Entorno de ejecución → Ejecutar todas*.

### En su computador
```bash
pip install -r requirements.txt
python demo.py                              # semana de ejemplo: comparación, plan, alertas y calendario
python -m pytest -q                         # pruebas automáticas (86 pruebas)
python experimentos/comparar_algoritmos.py  # experimento completo (alrededor de 1 minuto)
python experimentos/verificar_fuerza_bruta.py  # exacta contra fuerza bruta en 640 instancias diminutas
python experimentos/explorar_dataset_pomodoro.py  # dataset seleccionado (la primera vez necesita internet)
python experimentos/explorar_dataset_sip.py # dataset de contraste SiP (necesita internet)
```

## Usar sus propios datos

1. Copien `datos/ejemplo` en `datos/privados/mi_semana`. La carpeta `datos/privados/` está en `.gitignore` y **no se sube**.
2. Editen los archivos con el mismo formato:
   - `tareas.csv`: `id,nombre,tipo,duracion_min,fecha_limite,prioridad`. La fecha va como `2026-10-28 07:00` y la prioridad de 1 a 5.
   - `bloques_fijos.csv`: `nombre,dia_semana,hora_inicio,hora_fin`. Por ejemplo: `Cálculo,lunes,07:00,09:00`.
   - `configuracion.json`: fecha de inicio, días, horario del día, tamaño del bloque, tope diario y descanso.
3. Ejecuten `python demo.py datos/privados/mi_semana`.

## Estructura

```
kairos/
├── kairos/                 código del agente
│   ├── modelo.py           qué es un problema: tareas, bloques fijos, calendario en bloques de 30 min
│   ├── datos.py            lectura de CSV y JSON
│   ├── restricciones.py    reglas R1 a R4 y validador independiente
│   ├── voraz.py            tres reglas voraces (línea base)
│   ├── busqueda.py         búsqueda exacta (BPP con memoria) y fuerza bruta de control
│   ├── planificador.py     ejecuta cualquier estrategia y mide su tiempo
│   ├── metricas.py         métricas del plan
│   ├── reporte.py          plan en tabla y alertas
│   ├── escenarios.py       casos didácticos y escenarios sintéticos
│   ├── duraciones.py       módulo de aprendizaje: dataset Pomodoro, línea base, regresión y k-NN
│   └── visualizacion.py    calendario del plan y gráficas del experimento
├── datos/
│   ├── ejemplo/            semana de ejemplo (sintética)
│   ├── plantillas/         plantillas vacías y registro de duraciones
│   └── externos/           copia local de datasets públicos (se descarga; no se sube)
├── experimentos/           scripts reproducibles del experimento
├── resultados/             tablas y figuras generadas
├── notebooks/              cuaderno de demostración (con salidas)
├── tests/                  pruebas automáticas (pytest)
└── demo.py                 demostración por consola
```

## Limitaciones conocidas

- **Duraciones:** se asume que la duración estimada por el estudiante es correcta. La gente suele subestimarla (falacia de planificación).
- **Tareas indivisibles:** cada tarea es un solo bloque continuo. Las tareas largas se dividen a mano en sesiones (por ejemplo, "parte 1" y "parte 2").
- **Prioridades:** todas las prioridades valen lo mismo sin importar la duración. Una tarea corta y una larga con prioridad 4 aportan igual.
- **Escala:** la búsqueda exacta crece de forma exponencial. Más allá de unas 16 a 18 tareas habría que usar búsqueda local u otra heurística.
- **Validez externa:** los resultados vienen de escenarios sintéticos. Falta probar con estudiantes reales.

## Próximos pasos

1. **Datos propios:** cada integrante registra sus tareas reales (duración estimada y real) con `datos/plantillas/registro_duraciones.csv`.
2. **Módulo de aprendizaje:** aplicar a esos registros el mismo proceso que ya corre sobre el dataset Pomodoro (partición temporal, línea base, regresión lineal y k-NN, MAE y MSE) y conectar la duración corregida al planificador.
3. **Evaluación con usuarios:** medir cuánto del plan se cumple de verdad.
4. **Escalabilidad:** comparar con búsqueda local cuando haya más de unas 16 tareas.
5. **Proyección:** entrada de tareas en lenguaje natural e integración con la app móvil.

## Datos y privacidad

- Los datos reales de los integrantes (horarios y registros) van en `datos/privados/` y **no se suben**.
- En el registro de duraciones se usan códigos (A, B, C) en lugar de nombres.
- El dataset Pomodoro es público, pero su repositorio no declara licencia. Lo usamos solo con fines académicos, citando la fuente. El código lo descarga a `datos/externos/`, que **no se sube**.
- El dataset SiP tiene licencia CC BY-NC-ND 4.0. El script lo descarga desde la fuente y **no** se guarda una copia modificada en este repositorio.

## Referencias principales

- S. Russell y P. Norvig, *Artificial Intelligence: A Modern Approach*, 4.ª ed. Pearson, 2021.
- R. Buehler, D. Griffin y M. Ross, "Exploring the 'planning fallacy': Why people underestimate their task completion times", *J. Pers. Soc. Psychol.*, vol. 67, n.º 3, pp. 366–381, 1994.
- D. M. Jones y R. Borgatti, "The Renzo Pomodoro dataset: a conversation", borrador, dic. 2019. Datos y artículo: https://github.com/Derek-Jones/renzo-pomodoro
- D. M. Jones y S. Cullum, "A conversation around the analysis of the SiP effort estimation dataset", arXiv:1901.01621, 2019. Datos: https://github.com/Derek-Jones/SiP_dataset

La lista completa en formato IEEE está en el documento de avance.
