

# Especificación

## Problema

La coordinación de un laboratorio registra las reservas mediante mensajes y una planilla. Esto puede generar confusiones, como reservar la misma unidad en horarios que se superponen o que una reserva cancelada siga ocupando un horario. Se necesita un sistema sencillo que permita consultar la disponibilidad, crear y cancelar reservas sin perder el historial.

## Alcance

El sistema permitirá:

- Consultar la disponibilidad de una unidad para un día y horario determinados.
- Crear reservas indicando la unidad, el nombre del solicitante, la fecha y hora de inicio y la fecha y hora de fin.
- Cancelar reservas sin eliminar sus datos, dejando el horario disponible para una nueva reserva.
- Guardar las reservas y sus estados para recuperarlos al cerrar y volver a iniciar la aplicación.

El inventario de unidades ya está definido y se cargará inicialmente. No será necesario agregar, modificar ni eliminar unidades desde el sistema.

## Reglas

- Cada reserva tendrá un identificador propio y un estado que indique si está activa o cancelada.
- Una reserva activa ocupa el horario indicado. Una reserva cancelada deja de bloquearlo.
- No se podrán crear dos reservas activas de la misma unidad si sus horarios se superponen.
- Se permitirán reservas consecutivas. Por ejemplo, si una reserva termina a las 11:00, otra podrá comenzar a esa misma hora.
- Se podrán reservar unidades distintas en el mismo horario.
- Para crear una reserva, la unidad debe existir, el nombre del solicitante no puede estar vacío ni contener solamente espacios y las fechas y horas deben ser válidas.
- La fecha y hora de inicio deben ser anteriores a las de finalización.
- La consulta de disponibilidad deberá respetar las mismas reglas que la creación de reservas, para evitar que se informe como disponible un horario que no se puede reservar.
- Al cancelar una reserva, se conservarán su identificador y sus datos originales, y solo cambiará su estado.

## Supuestos

- Se utilizará la zona horaria de Argentina (America/Argentina/Buenos_Aires).
- Las fechas y horas se ingresarán en el formato `YYYY-MM-DD HH:MM`, por ejemplo, `2026-10-26 10:00`.
- No se establecerán restricciones adicionales para las reservas con fechas pasadas ni para su duración, siempre que se cumplan las demás reglas.
- El sistema utilizará las siguientes unidades precargadas: MIC-01, MIC-02, OSC-01, MUL-01 y FUE-01.
- Los datos se guardarán en un almacenamiento local que permita recuperarlos al reiniciar la aplicación.

## Criterios de aceptación

- CA1 - Rechazar horarios superpuestos: si MIC-01 tiene una reserva activa de 10:00 a 11:00, el sistema debe rechazar otra reserva de 10:30 a 11:30 para esa misma unidad.
- CA2 - Permitir reservas consecutivas: si MIC-01 tiene una reserva activa de 10:00 a 11:00, el sistema debe permitir otra de 11:00 a 12:00.
- CA3 - Permitir unidades distintas: si MIC-01 está reservada de 10:00 a 11:00, el sistema debe permitir una reserva de MIC-02 en ese mismo horario.
- CA4 - Cancelar sin perder el historial: al cancelar una reserva, el sistema debe conservar su identificador y sus datos, cambiar su estado a cancelada y liberar el horario.
- CA5 - Conservar los datos al reiniciar: después de cerrar y volver a iniciar la aplicación, las reservas activas y canceladas deben seguir disponibles.
- CA6 - Validar los datos ingresados: el sistema debe rechazar reservas con unidades inexistentes, nombres vacíos, fechas u horas inválidas o una fecha de inicio igual o posterior a la de finalización, mostrando un mensaje claro sobre el error.
- CA7 - Consultar disponibilidad correctamente: el sistema debe informar si una unidad está disponible para el horario solicitado, teniendo en cuenta las reservas activas y las reglas de superposición.


# Solución

## Estructura
```
data/inventario.json     inventario inicial (5 unidades)
data/reservas.db         base SQLite (se crea sola al primer uso; no se versiona)
src/reservas/modelo.py   reglas puras: formato de fecha, validación, se_superponen()
src/reservas/servicio.py persistencia SQLite y casos de uso (crear, cancelar, disponible, listar)
src/reservas/cli.py      interfaz de consola (argparse)
tests/test_reservas.py   33 pruebas automáticas
docs/PROGRESO.md         bitácora de progreso y decisiones
CLAUDE.md                instrucciones del agente
.claude/settings.json    permisos del agente
requirements.txt         dependencias fijadas (pytest y sus dependencias)
pytest.ini               configuración de pytest (pythonpath = src)
```

## Decisiones técnicas
- Python, solo biblioteca estándar (`sqlite3`, `argparse`, `datetime`, `json`); `pytest` como única dependencia.
- SQLite: reservas y estados persisten en `data/reservas.db`. La tabla guarda `id` (autoincremental, nunca se reutiliza), `unidad`, `solicitante`, `inicio`, `fin` y `estado` (`activa`/`cancelada`).
- Una única función `se_superponen` (`nuevo_inicio < fin_existente AND nuevo_fin > inicio_existente`) la usan la creación y la consulta de disponibilidad.
- Fechas `YYYY-MM-DD HH:MM`, hora local de Buenos Aires, guardadas sin conversión (Argentina no tiene horario de verano; `zoneinfo` no se usa porque en Windows requeriría instalar `tzdata`).
- El formato de fecha es estricto (`YYYY-MM-DD HH:MM`, con ceros, sin espacios ni segundos): `datetime.strptime` por sí solo aceptaría `9:00` o `2026-1-5`, por lo que se valida antes con una expresión regular.
- Fechas pasadas y duración: sin restricciones (según la especificación).
- Cancelar solo cambia `estado`; no se borran filas.

## Requisitos previos y versiones
Python 3.13.6; pytest 9.2.0 (`requirements.txt`). Probado en Windows 11.

## Instalación
```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

## Carga inicial y reinicio de datos
El inventario se lee de `data/inventario.json` en cada ejecución. La base se crea automáticamente al primer comando. **Reiniciar los datos = borrar manualmente `data/reservas.db`, lo que elimina TODAS las reservas y su historial.** La aplicación no ofrece ese comando.

## Comandos
Desde la raíz del repositorio (PowerShell):
```powershell
$env:PYTHONPATH = "src"
.venv\Scripts\python -m reservas unidades
.venv\Scripts\python -m reservas crear MIC-01 "Ana Prueba" "2026-10-26 10:00" "2026-10-26 11:00"
.venv\Scripts\python -m reservas disponibilidad MIC-01 "2026-10-26 11:00" "2026-10-26 12:00"
.venv\Scripts\python -m reservas cancelar 1
.venv\Scripts\python -m reservas listar [--unidad MIC-01]
```
Las opciones globales `--db` e `--inventario` (antes del comando) permiten usar otros archivos.

## Pruebas
```powershell
.venv\Scripts\python -m pytest -v
```
Usan una base temporal (`tmp_path`), nunca `data/reservas.db`. Cubren: creación válida, superposición (5 variantes), límites consecutivos (antes y después), unidades distintas, entradas inválidas (15 casos, incluido el formato estricto de fecha), cancelación que conserva el registro y libera el horario, coherencia entre disponibilidad y creación, creaciones simultáneas del mismo horario (solo una gana), persistencia tras reiniciar y CLI (incluye error de base de datos).
Resultado de la última ejecución: **33 passed** (Python 3.13.6, pytest 9.2.0).

Trazabilidad criterio de aceptación → prueba (`tests/test_reservas.py`):

| Criterio | Pruebas |
|---|---|
| CA1 Rechazar superposición | `test_rechaza_superposicion` (5 variantes) |
| CA2 Reservas consecutivas | `test_permite_reserva_consecutiva_despues`, `..._antes` |
| CA3 Unidades distintas | `test_unidades_distintas_mismo_horario` |
| CA4 Cancelar sin perder historial | `test_cancelar_conserva_registro_y_libera_horario`, `test_cancelar_inexistente_o_repetida_falla` |
| CA5 Conservar datos al reiniciar | `test_persistencia_activas_y_canceladas_tras_reiniciar` + procedimiento manual (abajo) |
| CA6 Validar entradas | `test_entradas_invalidas_se_rechazan` (15 casos), `test_cli_reinicio_y_errores` |
| CA7 Consultar disponibilidad | `test_disponibilidad_coincide_con_creacion`, `test_disponibilidad_otra_unidad_y_validaciones` |

En Linux/macOS los comandos son equivalentes: `.venv/bin/python` en lugar de `.venv\Scripts\python` y `export PYTHONPATH=src`.

## Ejemplo de entrada y salida
```
> crear MIC-01 "Ana Prueba" "2026-10-26 10:00" "2026-10-26 11:00"
Reserva #1 creada: MIC-01 2026-10-26 10:00 -> 2026-10-26 11:00
> crear MIC-01 "Carla Prueba" "2026-10-26 10:30" "2026-10-26 11:30"
Error: MIC-01 ya está reservada del 2026-10-26 10:00 al 2026-10-26 11:00 (reserva #1)   (código de salida 1)
> disponibilidad MIC-01 "2026-10-26 11:00" "2026-10-26 12:00"
MIC-01 DISPONIBLE (2026-10-26 11:00 -> 2026-10-26 12:00)
```

## Verificación manual de reinicio (CA5)
Procedimiento: ejecutar cada comando como proceso separado sobre la misma base (`--db ruta.db`).
1. `crear MIC-01 ...10:00-11:00` → #1; `crear OSC-01 ...10:00-11:00` → #2; `cancelar 2`.
2. En un proceso nuevo, `listar`. **Esperado:** #1 `[activa]`, #2 `[cancelada]`, con sus datos intactos.
3. `disponibilidad MIC-01 11:00-12:00` y `disponibilidad OSC-01 10:00-11:00`. **Esperado:** ambas DISPONIBLE.

**Observado (2026-11-06):** coincidió con lo esperado en los tres pasos (detalle en `docs/PROGRESO.md`). Además lo cubre `test_persistencia_activas_y_canceladas_tras_reiniciar`.

## Pendientes y limitaciones
- Sin administración de inventario, autenticación ni notificaciones (fuera de alcance).
- Concurrencia: `crear` verifica el conflicto y escribe dentro de una transacción `BEGIN IMMEDIATE`, por lo que dos procesos no pueden crear reservas superpuestas sobre el mismo archivo SQLite. No se contempla concurrencia distribuida (fuera de alcance).
- Los acentos de los mensajes no se verificaron en una consola de Windows con otra codificación (la captura del agente mostró `�`).

# Preparación del agente

- **Entorno:** Visual studio code como editar con extension Claude Code. Versión del entorno: no visible para el agente. **Modelo:** `claude-sonnet-5-5` (Sonnet 5.5), según el prompt de sistema de la sesión. Función: implementar, escribir pruebas y ejecutarlas sobre el repositorio con herramientas reales (lectura/escritura de archivos y shell). Motivo de la elección: actualmente dispongo de una cuenta pro en claude y era el modelo disponible por defecto en mi cuenta de Claude Code y es adecuado para programar y ejecutar pruebas, y me parece suficiente en este caso para este tipo de actividad, quizas en actividades mas complejas podria elegir opus con un nivel medio. Nota: el código, las pruebas y la documentación se hicieron con `claude-sonnet-5-5`; solo el último paso (completar los enlaces a commits del README) se hizo con `claude-opus-5-5`, tras cambiar de modelo con `/model`.
- **Instrucciones:** [`CLAUDE.md`](CLAUDE.md), que el agente lee al iniciar. Extracto de la adaptación específica: «dos reservas de la MISMA unidad se superponen si `nuevo_inicio < fin_existente AND nuevo_fin > inicio_existente`. Por lo tanto los límites consecutivos (fin == inicio) están PERMITIDOS» y «La consulta de disponibilidad DEBE usar la misma función de superposición que la creación de reservas».
- **Contexto suministrado:** especificación del README, `CLAUDE.md`, la consigna (PDF) y el estado del repositorio. **Excluido:** datos personales reales y secretos (`Read(./.env)` denegado).
- **Permisos** ([`.claude/settings.json`](.claude/settings.json)): permitidos `pytest`, `python -m reservas`, `git status/diff/log`; denegados `git commit/push/reset`, `rm`, `del`, `pip install` y lectura de `.env`.
- **Controles aplicados (evidencia real):** la instalación de `pytest` se aprobó explícitamente; un comando con `rm` fue denegado y se repitió sin él; los commits los hace la autora tras revisar el diff.
- **Adaptación específica con evidencia de uso:** la regla de superposición está en `src/reservas/modelo.py` (`se_superponen`) y probada en `tests/test_reservas.py` (`test_rechaza_superposicion`, `test_permite_reserva_consecutiva_*`, `test_disponibilidad_coincide_con_creacion`).
- **Retención del progreso:** [`docs/PROGRESO.md`](docs/PROGRESO.md), con una entrada por tarea (procedimiento obligatorio de `CLAUDE.md`).


# Registro de decisiones y delegación

## Decisiones significativas
| Decisión | Motivo | Alternativa | Consecuencia |
|---|---|---|---|
| SQLite | Persistencia sin dependencias, en la biblioteca estándar | JSON/CSV | Consultas simples; archivo binario no versionado |
| Hora local sin zona (texto) | `zoneinfo` sin `tzdata` falla en Windows; sin horario de verano en Argentina | Instalar `tzdata` | Sin dependencia extra; no hay conversión de zonas |
| `src/reservas/` | Carpeta ya creada por la autora | `reservas/` en la raíz | Se corrigió `CLAUDE.md`; se usa `PYTHONPATH=src` |
| Formato de fecha estricto (regex) | Cumplir el formato de la especificación; `strptime` era permisivo (hallado en la revisión) | Aceptar variantes y normalizar | Entradas como `9:00` se rechazan con mensaje claro |
| `BEGIN IMMEDIATE` en `crear` | Evitar que dos procesos creen reservas superpuestas (verificar e insertar eran pasos separados) | Dejarlo como limitación | Prueba con 8 hilos; falla si se quita el bloqueo |
| Rechazar cancelar dos veces | Evita ocultar errores de uso | Cancelación idempotente | Mensaje claro, código de salida 1 |

## Episodio 1 — Núcleo de reglas y pruebas
- **Objetivo/requisito:** rechazar superposiciones, permitir consecutivas y unidades distintas, validar entradas (CA1, CA2, CA3, CA6, CA7).
- **Contexto e instrucción:** `CLAUDE.md` (fórmula de superposición, «misma función» para disponibilidad).
- **Acción del agente:** `modelo.py`, `servicio.py` y `tests/test_reservas.py`. Primera corrida: 24 passed, 2 failed; una falla era una prueba mal escrita (`listar()[-1]` asumía orden de creación y `listar` ordena por inicio) y se corrigió usando el id devuelto por `crear`. En una revisión posterior (pedida por la autora) se detectó que `strptime` aceptaba fechas fuera del formato (`9:00`, `2026-1-5`, espacios alrededor); se agregó validación estricta con regex y 5 casos de prueba nuevos.
- **Decisión humana:** Acepté. Revisé que se_superponen coincide con la regla de la especificación y que los ejemplos de las pruebas (10:30–11:30 rechazado, 11:00–12:00 permitido) son los de la consigna. Pedí una revisión adicional, de la que salió la corrección del formato estricto de fecha, que también acepté porque hace cumplir el formato de la especificación.
- **Evidencia:** `src/reservas/modelo.py`, `tests/test_reservas.py`, commits [8a8dc66](https://github.com/afjantus/reservas-lab/commit/8a8dc66) (reglas) y [9ad2280](https://github.com/afjantus/reservas-lab/commit/9ad2280) (pruebas).

## Episodio 2 — Persistencia SQLite y CLI
- **Objetivo/requisito:** guardar reservas y estados, cancelar sin borrar (CA4, CA5).
- **Contexto e instrucción:** `CLAUDE.md` («Cancelar solo cambia el estado a `cancelada`; nunca borrar filas»).
- **Acción del agente:** tabla `reservas` con `CHECK` de estado, `cancelar` con `UPDATE`, CLI con `argparse`. La prueba del CLI detectó que `cli.ejecutar` fijaba `sys.stdout` al definir la función; se corrigió resolviéndolo al llamar. En la misma revisión se detectó que verificar el conflicto e insertar eran pasos separados (posible carrera entre procesos); se encapsuló en `BEGIN IMMEDIATE` con `rollback` ante error, se agregó la prueba `test_creaciones_simultaneas_del_mismo_horario_solo_una_gana` (comprobado que falla 6 de 6 veces sin el bloqueo) y la CLI ahora captura `sqlite3.Error` en vez de mostrar un traceback.
- **Decisión humana:**  Acepté. Verifiqué que cancelar solo hace UPDATE y no borra filas. Acepté la transacción BEGIN IMMEDIATE porque el agente demostró que la prueba fallaba sin ella
- **Evidencia:** `src/reservas/servicio.py`, `src/reservas/cli.py`, `test_cancelar_conserva_registro_y_libera_horario`, commits [8a8dc66](https://github.com/afjantus/reservas-lab/commit/8a8dc66) (persistencia) y [9ad2280](https://github.com/afjantus/reservas-lab/commit/9ad2280) (CLI y prueba de concurrencia).

## Episodio 3 — Verificación de reinicio y límite de zona horaria
- **Objetivo/requisito:** CA5 comprobado con procesos reales; documentar la zona horaria.
- **Contexto e instrucción:** consigna («tras detener y reiniciar sin borrar datos») y `CLAUDE.md` (America/Argentina/Buenos_Aires).
- **Acción del agente:** detectó que `zoneinfo` no tiene la zona en este Windows, propuso guardar hora local sin conversión y ejecutó el procedimiento manual de reinicio (resultado coincidente con lo esperado).
- **Decisión humana:** Acepté guardar la hora local sin conversión en lugar de instalar tzdata, porque Argentina no tiene horario de verano y evita una dependencia. Aprobé la instalación de pytest. Revisé que el resultado de la verificación de reinicio coincidiera con lo esperado
- **Evidencia:** sección «Verificación manual de reinicio», `docs/PROGRESO.md`, `test_persistencia_activas_y_canceladas_tras_reiniciar`, commits [9ad2280](https://github.com/afjantus/reservas-lab/commit/9ad2280) (prueba de persistencia) y [00f6afe](https://github.com/afjantus/reservas-lab/commit/00f6afe) (procedimiento documentado).
