"""Reglas de dominio puras: formato de fechas, validación y superposición."""
import re
from datetime import datetime

FORMATO = "%Y-%m-%d %H:%M"
# Formato estricto: strptime por sí solo acepta variantes sin ceros (ej. "9:00").
_PATRON = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}")
ACTIVA = "activa"
CANCELADA = "cancelada"


class ReservaError(ValueError):
    """Error de validación o de regla de negocio, con mensaje claro."""


def parsear_fecha(texto, campo="fecha"):
    """Convierte 'YYYY-MM-DD HH:MM' (hora local de Buenos Aires) en datetime ingenuo."""
    if not isinstance(texto, str) or not _PATRON.fullmatch(texto):
        raise ReservaError(
            f"{campo} inválida: '{texto}'. Use el formato YYYY-MM-DD HH:MM"
        )
    try:
        return datetime.strptime(texto, FORMATO)
    except ValueError:
        raise ReservaError(
            f"{campo} inválida: '{texto}'. Use el formato YYYY-MM-DD HH:MM"
        ) from None


def validar_intervalo(inicio, fin):
    ini = parsear_fecha(inicio, "inicio")
    fi = parsear_fecha(fin, "fin")
    if ini >= fi:
        raise ReservaError("el inicio debe ser estrictamente anterior al fin")
    return ini, fi


def se_superponen(nuevo_inicio, nuevo_fin, existente_inicio, existente_fin):
    """Única función de superposición (la usan crear reserva y disponibilidad).

    Límites consecutivos (fin == inicio) NO se superponen.
    """
    return nuevo_inicio < existente_fin and nuevo_fin > existente_inicio
