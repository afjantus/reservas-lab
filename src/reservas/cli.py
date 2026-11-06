"""Interfaz de consola."""
import argparse
import sqlite3
import sys

from .modelo import ReservaError
from .servicio import DB_POR_DEFECTO, INVENTARIO_POR_DEFECTO, Servicio


def construir_parser():
    p = argparse.ArgumentParser(prog="reservas", description="Reservas de laboratorio")
    p.add_argument("--db", default=str(DB_POR_DEFECTO), help="ruta de la base SQLite")
    p.add_argument("--inventario", default=str(INVENTARIO_POR_DEFECTO))
    sub = p.add_subparsers(dest="comando", required=True)
    sub.add_parser("unidades", help="listar el inventario")
    crear = sub.add_parser("crear", help="crear una reserva")
    crear.add_argument("unidad")
    crear.add_argument("solicitante")
    crear.add_argument("inicio", help="YYYY-MM-DD HH:MM")
    crear.add_argument("fin", help="YYYY-MM-DD HH:MM")
    cancelar = sub.add_parser("cancelar", help="cancelar una reserva")
    cancelar.add_argument("id", type=int)
    disp = sub.add_parser("disponibilidad", help="consultar disponibilidad")
    disp.add_argument("unidad")
    disp.add_argument("inicio")
    disp.add_argument("fin")
    listar = sub.add_parser("listar", help="listar reservas (todas, con estado)")
    listar.add_argument("--unidad")
    return p


def ejecutar(args, out=None):
    out = out or sys.stdout
    try:
        s = Servicio(args.db, args.inventario)
    except (OSError, ValueError, KeyError, sqlite3.Error) as e:
        print(f"Error al iniciar: {e}", file=sys.stderr)
        return 1
    try:
        if args.comando == "unidades":
            for uid, equipo in s.inventario.items():
                print(f"{uid}  {equipo}", file=out)
        elif args.comando == "crear":
            rid = s.crear(args.unidad, args.solicitante, args.inicio, args.fin)
            print(f"Reserva #{rid} creada: {args.unidad} {args.inicio} -> {args.fin}", file=out)
        elif args.comando == "cancelar":
            s.cancelar(args.id)
            print(f"Reserva #{args.id} cancelada", file=out)
        elif args.comando == "disponibilidad":
            ok = s.disponible(args.unidad, args.inicio, args.fin)
            estado = "DISPONIBLE" if ok else "OCUPADA"
            print(f"{args.unidad} {estado} ({args.inicio} -> {args.fin})", file=out)
        elif args.comando == "listar":
            for r in s.listar(args.unidad):
                print(f"#{r['id']} {r['unidad']} {r['inicio']} -> {r['fin']} "
                      f"{r['solicitante']} [{r['estado']}]", file=out)
        return 0
    except ReservaError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except sqlite3.Error as e:
        print(f"Error de base de datos: {e}", file=sys.stderr)
        return 1
    finally:
        s.cerrar()


def main(argv=None):
    return ejecutar(construir_parser().parse_args(argv))
