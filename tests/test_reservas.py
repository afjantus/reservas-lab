"""Pruebas de las reglas de reservas. Usan siempre una base temporal (tmp_path)."""
import threading

import pytest

from reservas.cli import construir_parser, ejecutar
from reservas.modelo import ReservaError
from reservas.servicio import INVENTARIO_POR_DEFECTO, Servicio

D = "2026-10-26"


@pytest.fixture
def db(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def s(db):
    servicio = Servicio(db, INVENTARIO_POR_DEFECTO)
    yield servicio
    servicio.cerrar()


def reservar_mic01(s):
    return s.crear("MIC-01", "Ana Prueba", f"{D} 10:00", f"{D} 11:00")


# --- creación válida ---
def test_creacion_valida_guarda_datos_y_estado_activa(s):
    rid = reservar_mic01(s)
    r = s.obtener(rid)
    assert r == {"id": rid, "unidad": "MIC-01", "solicitante": "Ana Prueba",
                 "inicio": f"{D} 10:00", "fin": f"{D} 11:00", "estado": "activa"}


def test_ids_distintos(s):
    assert reservar_mic01(s) != s.crear("MIC-02", "Beto Prueba", f"{D} 10:00", f"{D} 11:00")


# --- CA1: superposición ---
@pytest.mark.parametrize("ini,fin", [
    ("10:30", "11:30"),  # solapa el final
    ("09:30", "10:30"),  # solapa el inicio
    ("10:15", "10:45"),  # contenida
    ("09:00", "12:00"),  # contiene
    ("10:00", "11:00"),  # idéntica
])
def test_rechaza_superposicion(s, ini, fin):
    reservar_mic01(s)
    with pytest.raises(ReservaError, match="ya está reservada"):
        s.crear("MIC-01", "Otra Persona", f"{D} {ini}", f"{D} {fin}")
    assert len(s.listar()) == 1


# --- CA2: límites consecutivos ---
def test_permite_reserva_consecutiva_despues(s):
    reservar_mic01(s)
    s.crear("MIC-01", "Beto Prueba", f"{D} 11:00", f"{D} 12:00")


def test_permite_reserva_consecutiva_antes(s):
    reservar_mic01(s)
    s.crear("MIC-01", "Beto Prueba", f"{D} 09:00", f"{D} 10:00")


# --- CA3: unidades distintas ---
def test_unidades_distintas_mismo_horario(s):
    reservar_mic01(s)
    s.crear("MIC-02", "Beto Prueba", f"{D} 10:00", f"{D} 11:00")
    assert len(s.listar()) == 2


# --- CA4: cancelación ---
def test_cancelar_conserva_registro_y_libera_horario(s):
    rid = reservar_mic01(s)
    antes = s.obtener(rid)
    s.cancelar(rid)
    despues = s.obtener(rid)
    assert despues["estado"] == "cancelada"
    assert {k: v for k, v in despues.items() if k != "estado"} == \
           {k: v for k, v in antes.items() if k != "estado"}
    assert s.disponible("MIC-01", f"{D} 10:00", f"{D} 11:00")
    nuevo = s.crear("MIC-01", "Beto Prueba", f"{D} 10:00", f"{D} 11:00")
    assert nuevo != rid
    assert len(s.listar()) == 2  # no se borra ninguna fila


def test_cancelar_inexistente_o_repetida_falla(s):
    with pytest.raises(ReservaError, match="no existe"):
        s.cancelar(999)
    rid = reservar_mic01(s)
    s.cancelar(rid)
    with pytest.raises(ReservaError, match="ya está cancelada"):
        s.cancelar(rid)


# --- CA6: entradas inválidas ---
@pytest.mark.parametrize("unidad,solic,ini,fin,msg", [
    ("XXX-99", "Ana", f"{D} 10:00", f"{D} 11:00", "unidad desconocida"),
    ("MIC-01", "", f"{D} 10:00", f"{D} 11:00", "solicitante"),
    ("MIC-01", "    ", f"{D} 10:00", f"{D} 11:00", "solicitante"),
    ("MIC-01", "Ana", "2026-13-01 10:00", f"{D} 11:00", "inicio inválida"),
    ("MIC-01", "Ana", f"{D} 25:00", f"{D} 11:00", "inicio inválida"),
    ("MIC-01", "Ana", "2026-02-30 10:00", f"{D} 11:00", "inicio inválida"),
    ("MIC-01", "Ana", "26/10/2026 10:00", f"{D} 11:00", "inicio inválida"),
    ("MIC-01", "Ana", f"{D} 10:00", "no es fecha", "fin inválida"),
    # formato estricto YYYY-MM-DD HH:MM (sin variantes sin ceros, espacios ni segundos)
    ("MIC-01", "Ana", f"{D} 9:00", f"{D} 11:00", "inicio inválida"),
    ("MIC-01", "Ana", "2026-1-5 09:00", f"{D} 11:00", "inicio inválida"),
    ("MIC-01", "Ana", f" {D} 10:00", f"{D} 11:00", "inicio inválida"),
    ("MIC-01", "Ana", f"{D} 10:00", f"{D} 11:00:30", "fin inválida"),
    ("MIC-01", "Ana", f"{D}T10:00", f"{D} 11:00", "inicio inválida"),
    ("MIC-01", "Ana", f"{D} 11:00", f"{D} 10:00", "estrictamente anterior"),
    ("MIC-01", "Ana", f"{D} 10:00", f"{D} 10:00", "estrictamente anterior"),
])
def test_entradas_invalidas_se_rechazan(s, unidad, solic, ini, fin, msg):
    with pytest.raises(ReservaError, match=msg):
        s.crear(unidad, solic, ini, fin)
    assert s.listar() == []


# --- Concurrencia entre conexiones: la verificación y el INSERT son atómicos ---
def test_creaciones_simultaneas_del_mismo_horario_solo_una_gana(db):
    resultados = []

    def intentar(i):
        serv = Servicio(db, INVENTARIO_POR_DEFECTO)
        try:
            serv.crear("MIC-01", f"Persona Prueba {i}", f"{D} 10:00", f"{D} 11:00")
            resultados.append("ok")
        except ReservaError:
            resultados.append("rechazada")
        finally:
            serv.cerrar()

    hilos = [threading.Thread(target=intentar, args=(i,)) for i in range(8)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    assert sorted(resultados) == ["ok"] + ["rechazada"] * 7
    verif = Servicio(db, INVENTARIO_POR_DEFECTO)
    try:
        assert len(verif.listar("MIC-01")) == 1
    finally:
        verif.cerrar()


# --- CA7: disponibilidad usa las mismas reglas ---
def test_disponibilidad_coincide_con_creacion(s):
    reservar_mic01(s)
    casos = [("10:30", "11:30", False), ("11:00", "12:00", True),
             ("09:00", "10:00", True), ("10:00", "11:00", False)]
    for ini, fin, esperado in casos:
        assert s.disponible("MIC-01", f"{D} {ini}", f"{D} {fin}") is esperado
        if esperado:
            nuevo = s.crear("MIC-01", "Ana", f"{D} {ini}", f"{D} {fin}")
            s.cancelar(nuevo)
        else:
            with pytest.raises(ReservaError):
                s.crear("MIC-01", "Ana", f"{D} {ini}", f"{D} {fin}")


def test_disponibilidad_otra_unidad_y_validaciones(s):
    reservar_mic01(s)
    assert s.disponible("MIC-02", f"{D} 10:00", f"{D} 11:00")
    with pytest.raises(ReservaError):
        s.disponible("XXX-99", f"{D} 10:00", f"{D} 11:00")
    with pytest.raises(ReservaError):
        s.disponible("MIC-01", f"{D} 11:00", f"{D} 10:00")


# --- CA5: persistencia tras reiniciar ---
def test_persistencia_activas_y_canceladas_tras_reiniciar(db):
    s1 = Servicio(db, INVENTARIO_POR_DEFECTO)
    activa = s1.crear("MIC-01", "Ana Prueba", f"{D} 10:00", f"{D} 11:00")
    cancelada = s1.crear("OSC-01", "Beto Prueba", f"{D} 10:00", f"{D} 11:00")
    s1.cancelar(cancelada)
    s1.cerrar()  # "detener" la aplicación

    s2 = Servicio(db, INVENTARIO_POR_DEFECTO)  # "reiniciar" sobre el mismo archivo
    try:
        assert s2.obtener(activa)["estado"] == "activa"
        assert s2.obtener(cancelada)["estado"] == "cancelada"
        assert s2.obtener(cancelada)["solicitante"] == "Beto Prueba"
        assert not s2.disponible("MIC-01", f"{D} 10:30", f"{D} 11:30")  # activa sigue bloqueando
        assert s2.disponible("OSC-01", f"{D} 10:00", f"{D} 11:00")      # cancelada no bloquea
    finally:
        s2.cerrar()


# --- CLI (procesos de consola separados sobre la misma base) ---
def test_cli_error_de_base_de_datos_no_lanza_traceback(tmp_path, capsys):
    # --db apunta a un directorio: SQLite no puede abrirlo.
    args = construir_parser().parse_args(["--db", str(tmp_path), "listar"])
    assert ejecutar(args) == 1
    assert "Error al iniciar" in capsys.readouterr().err


def test_cli_reinicio_y_errores(db, capsys):
    def correr(*argv):
        return ejecutar(construir_parser().parse_args(["--db", str(db), *argv]))

    assert correr("crear", "MIC-01", "Ana Prueba", f"{D} 10:00", f"{D} 11:00") == 0
    assert "Reserva #1 creada" in capsys.readouterr().out
    assert correr("crear", "MIC-01", "Beto", f"{D} 10:30", f"{D} 11:30") == 1
    assert "ya está reservada" in capsys.readouterr().err
    assert correr("disponibilidad", "MIC-01", f"{D} 11:00", f"{D} 12:00") == 0
    assert "DISPONIBLE" in capsys.readouterr().out
    assert correr("cancelar", "1") == 0
    capsys.readouterr()
    assert correr("listar") == 0
    assert "[cancelada]" in capsys.readouterr().out
    assert correr("crear", "MIC-01", " ", f"{D} 10:00", f"{D} 11:00") == 1
    assert "solicitante" in capsys.readouterr().err
