# Instrucciones para el agente (reservas-lab)

Este archivo es leído automáticamente por Claude Code al iniciar una sesión en este repositorio.

## Contexto
- La especificación está en `README.md` (sección "Especificación"). Leerla antes de cambiar código.
- No modificar la especificación sin avisar y explicar el motivo; los cambios de reglas los decide la persona autora.

## Stack y estructura
- Python 3.13, solo biblioteca estándar para la aplicación (`sqlite3`, `argparse`, `datetime`, `zoneinfo`).
- Pruebas con `pytest` (única dependencia, en `requirements.txt`).
- Entorno virtual en `.venv/`. Ejecutar pruebas con: `.venv\Scripts\python -m pytest -v`
- Interfaz: consola (CLI). Persistencia: SQLite en `data/reservas.db`.
- Código en `src/reservas/`, pruebas en `tests/`, inventario inicial en `data/inventario.json`.

## Reglas de dominio (adaptación específica)
- Superposición: dos reservas de la MISMA unidad se superponen si
  `nuevo_inicio < fin_existente AND nuevo_fin > inicio_existente`.
  Por lo tanto los límites consecutivos (fin == inicio) están PERMITIDOS.
- Solo cuentan las reservas con estado `activa`; las `cancelada` nunca bloquean.
- La consulta de disponibilidad DEBE usar la misma función de superposición que la creación de reservas (no duplicar lógica).
- Cancelar solo cambia el estado a `cancelada`; nunca borrar filas ni modificar id, unidad, solicitante, inicio o fin.
- Fechas en formato `YYYY-MM-DD HH:MM`, zona horaria America/Argentina/Buenos_Aires.

## Pruebas
- Toda regla nueva o cambiada debe tener su prueba en `tests/`.
- Las pruebas deben usar una base de datos temporal (`tmp_path`), nunca `data/reservas.db`.
- No dar una tarea por terminada sin ejecutar las pruebas y reportar el resultado real.

## Procedimiento de progreso (obligatorio)
Al terminar cada tarea, agregar una entrada al final de `docs/PROGRESO.md` con:
fecha, tarea pedida, archivos modificados, decisiones tomadas, comando de pruebas ejecutado y su resultado, pendientes.

## Prohibido
- Hacer `git commit`, `git push` o cambiar de rama (lo hace la persona autora tras revisar).
- Borrar `data/reservas.db` o datos de reservas.
- Instalar paquetes o agregar dependencias sin pedir aprobación.
- Incluir datos personales reales: usar solicitantes ficticios.
