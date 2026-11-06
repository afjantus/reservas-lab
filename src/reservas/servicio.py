"""Servicio de reservas: inventario, persistencia SQLite y reglas."""
import json
import sqlite3
from pathlib import Path

from .modelo import (ACTIVA, CANCELADA, FORMATO, ReservaError, parsear_fecha,
                     se_superponen, validar_intervalo)

RAIZ = Path(__file__).resolve().parents[2]
DB_POR_DEFECTO = RAIZ / "data" / "reservas.db"
INVENTARIO_POR_DEFECTO = RAIZ / "data" / "inventario.json"


def cargar_inventario(ruta=INVENTARIO_POR_DEFECTO):
    with open(ruta, encoding="utf-8") as f:
        return {u["id"]: u["equipo"] for u in json.load(f)}


class Servicio:
    def __init__(self, db_path=DB_POR_DEFECTO, inventario_path=INVENTARIO_POR_DEFECTO):
        self.inventario = cargar_inventario(inventario_path)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(db_path)
        self.con.row_factory = sqlite3.Row
        self.con.execute(
            """CREATE TABLE IF NOT EXISTS reservas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unidad TEXT NOT NULL,
                solicitante TEXT NOT NULL,
                inicio TEXT NOT NULL,
                fin TEXT NOT NULL,
                estado TEXT NOT NULL CHECK (estado IN ('activa', 'cancelada'))
            )"""
        )
        self.con.commit()

    def cerrar(self):
        self.con.close()

    def _validar_unidad(self, unidad):
        if unidad not in self.inventario:
            raise ReservaError(f"unidad desconocida: '{unidad}'")

    def _conflictos(self, unidad, ini, fi):
        """Reservas ACTIVAS de la unidad que se superponen con [ini, fi)."""
        filas = self.con.execute(
            "SELECT * FROM reservas WHERE unidad = ? AND estado = ?", (unidad, ACTIVA)
        ).fetchall()
        return [
            f for f in filas
            if se_superponen(ini, fi, parsear_fecha(f["inicio"]), parsear_fecha(f["fin"]))
        ]

    def disponible(self, unidad, inicio, fin):
        self._validar_unidad(unidad)
        ini, fi = validar_intervalo(inicio, fin)
        return not self._conflictos(unidad, ini, fi)

    def crear(self, unidad, solicitante, inicio, fin):
        self._validar_unidad(unidad)
        if not isinstance(solicitante, str) or not solicitante.strip():
            raise ReservaError("el solicitante no puede estar vacío")
        ini, fi = validar_intervalo(inicio, fin)
        # BEGIN IMMEDIATE toma el bloqueo de escritura antes de verificar, para que
        # la comprobación de conflicto y el INSERT sean atómicos entre procesos.
        self.con.execute("BEGIN IMMEDIATE")
        try:
            conflictos = self._conflictos(unidad, ini, fi)
            if conflictos:
                c = conflictos[0]
                raise ReservaError(
                    f"{unidad} ya está reservada del {c['inicio']} al {c['fin']} "
                    f"(reserva #{c['id']})"
                )
            cur = self.con.execute(
                "INSERT INTO reservas (unidad, solicitante, inicio, fin, estado) "
                "VALUES (?,?,?,?,?)",
                (unidad, solicitante.strip(), ini.strftime(FORMATO),
                 fi.strftime(FORMATO), ACTIVA),
            )
            self.con.commit()
            return cur.lastrowid
        except BaseException:
            self.con.rollback()
            raise

    def cancelar(self, reserva_id):
        fila = self.obtener(reserva_id)
        if fila["estado"] == CANCELADA:
            raise ReservaError(f"la reserva #{reserva_id} ya está cancelada")
        self.con.execute("UPDATE reservas SET estado = ? WHERE id = ?", (CANCELADA, reserva_id))
        self.con.commit()

    def obtener(self, reserva_id):
        fila = self.con.execute("SELECT * FROM reservas WHERE id = ?", (reserva_id,)).fetchone()
        if fila is None:
            raise ReservaError(f"no existe la reserva #{reserva_id}")
        return dict(fila)

    def listar(self, unidad=None):
        if unidad:
            self._validar_unidad(unidad)
            filas = self.con.execute(
                "SELECT * FROM reservas WHERE unidad = ? ORDER BY inicio, id", (unidad,))
        else:
            filas = self.con.execute("SELECT * FROM reservas ORDER BY inicio, id")
        return [dict(f) for f in filas]
