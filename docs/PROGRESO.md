# Registro de progreso

Archivo versionado donde el agente (y la autora) registran avances, decisiones y pendientes.
El agente agrega una entrada al terminar cada tarea, según el procedimiento de `CLAUDE.md`.

---

## 2026-11-06 — Preparación del agente
- Se crearon `CLAUDE.md` (instrucciones y adaptación específica de superposición/límites consecutivos),
  `.claude/settings.json` (permisos: pytest y lectura de git permitidos; commit, push, borrado e instalación denegados)
  y este archivo.
- Pendiente: implementación (episodio 1), persistencia y CLI (episodio 2), verificación de reinicio (episodio 3).

---

## 2026-11-06 — Implementación, persistencia, CLI y pruebas (episodios 1-3)
- **Tarea pedida:** realizar los pasos de la consigna: entorno, inventario, núcleo de reglas, persistencia SQLite, CLI, pruebas y verificación de reinicio.
- **Archivos:** `requirements.txt`, `pytest.ini`, `data/inventario.json`, `src/reservas/{__init__,modelo,servicio,cli,__main__}.py`, `tests/test_reservas.py`; `CLAUDE.md` (ruta del código corregida a `src/reservas/`).
- **Decisiones:**
  - Pytest 9.2.0 instalado en `.venv` con aprobación explícita de la autora (único paquete).
  - Código en `src/reservas/` (carpeta ya creada por la autora); se corrigió `CLAUDE.md`.
  - Fechas guardadas como texto `YYYY-MM-DD HH:MM` en hora local de Buenos Aires, sin conversión. No se usa `zoneinfo` porque en Windows falta la base `tzdata` (no se instaló); Argentina no tiene horario de verano.
  - Una sola función `se_superponen` (`modelo.py`), usada por `crear` y `disponible`.
  - IDs con `AUTOINCREMENT`: un id nunca se reutiliza. Cancelar solo hace `UPDATE estado`.
  - Cancelar una reserva ya cancelada se rechaza con mensaje claro.
- **Correcciones durante la tarea (reales):** la primera corrida dio 24 passed / 2 failed. (1) Prueba mal escrita: asumía que `listar()[-1]` era la última creada, pero ordena por inicio; se usa el id devuelto por `crear`. (2) `cli.ejecutar` fijaba `out=sys.stdout` al definir la función; se resuelve al llamar.
- **Comando de pruebas:** `.venv\Scripts\python -m pytest -v`
- **Resultado:** 26 passed in 0.29s (Python 3.13.6, pytest 9.2.0).
- **Verificación manual de reinicio** (procesos separados, base temporal): crear MIC-01 10:00-11:00 (#1) y OSC-01 10:00-11:00 (#2), cancelar #2, rechazo de MIC-01 10:30-11:30 (exit 1). En un proceso nuevo: `listar` muestra #1 [activa] y #2 [cancelada]; MIC-01 11:00-12:00 DISPONIBLE; OSC-01 10:00-11:00 DISPONIBLE. Coincide con lo esperado.
- **Pendientes:** revisión humana del diff y commits (hace la autora); completar decisiones humanas de los episodios en el README; revisar acentos en la consola de Windows (la captura del agente mostró `�`, no se verificó en consola UTF-8).

---

## 2026-11-06 — Revisión y endurecimiento
- **Tarea pedida:** la autora pidió revisar el código y corregir lo necesario para cerrar la actividad.
- **Archivos modificados:** `src/reservas/modelo.py`, `src/reservas/servicio.py`, `src/reservas/cli.py`, `tests/test_reservas.py`, `README.md`.
- **Hallazgos y decisiones (verificados):**
  1. `strptime` aceptaba `2026-10-26 9:00`, `2026-1-5 09:00` y espacios alrededor (comprobado ejecutándolo). Se exige el formato exacto con regex `\d{4}-\d{2}-\d{2} \d{2}:\d{2}`. No cambia la especificación: la hace cumplir.
  2. Verificar conflicto e insertar no era atómico. `crear` usa ahora `BEGIN IMMEDIATE` y `rollback` ante cualquier error.
  3. La CLI mostraba traceback ante errores de SQLite; ahora devuelve código 1 con mensaje.
  4. Se quitó un parámetro sin uso (`tmp_path`) de una prueba.
- **Pruebas nuevas:** 5 casos de formato estricto, `test_creaciones_simultaneas_del_mismo_horario_solo_una_gana` (8 hilos, 1 conexión cada uno), `test_cli_error_de_base_de_datos_no_lanza_traceback`. Comprobación de validez: con `BEGIN IMMEDIATE` quitado temporalmente la prueba de concurrencia falló 6 de 6 ejecuciones; se restauró.
- **Comando de pruebas:** `.venv\Scripts\python -m pytest -v`
- **Resultado:** 33 passed in 0.29s (Python 3.13.6, pytest 9.2.0). Prueba de concurrencia repetida 5 veces con el código final: 5 passed.
- **Pendientes:** revisión humana y commits (autora); completar `[completar]` del README.

---

## 2026-11-06 — Enlaces a commits en el README
- **Tarea pedida:** completar los `[commit: completar]` de los episodios con los hashes reales.
- **Archivos:** `README.md` (enlaces en episodios 1-3, nota de cambio de modelo, se quitó el pendiente de enlaces), `docs/PROGRESO.md`.
- **Decisiones:** cada episodio enlaza a los commits que contienen su código o prueba: `8a8dc66` (reglas y persistencia), `9ad2280` (CLI y pruebas), `00f6afe` (documentación). La autora completó el motivo del modelo y las decisiones humanas. Esta tarea se hizo con `claude-opus-5-5` (cambio con `/model`).
- **Comando de pruebas:** `.venv\Scripts\python -m pytest -q`
- **Resultado:** 33 passed in 0.28s.
- **Pendientes:** commit final y `git push` (autora); comprobar acceso al repo y enviar el email.
