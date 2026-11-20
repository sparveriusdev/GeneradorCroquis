# ==============================================================================
# Archivo  : src/generador_croquis/domain/npn.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-20 | Creación. Número predial nacional (NPN) de 30
#          |            | caracteres: la posición 22 (condición de propiedad)
#          |            | igual a 2 indica una informalidad; las posiciones
#          |            | 18-21 identifican su predio (p. ej. P001).
# ==============================================================================
"""Reglas del número predial nacional (NPN) del catastro colombiano.

Estructura (30 caracteres): departamento (2), municipio (3), zona (2), sector (2), comuna (2),
barrio (2), manzana o vereda (4), terreno (4), condición de propiedad (1), edificio (2),
piso (2) y unidad predial (4). Una informalidad (mejora sobre un predio ajeno) lleva un 2 en
la condición de propiedad y, en el lugar del terreno, su propio número (p. ej. ``P001``).
"""

from __future__ import annotations

LONGITUD_NPN = 30
POSICION_CONDICION = 22  # 1 = primer carácter
CONDICION_INFORMAL = "2"
_TERRENO = slice(17, 21)  # posiciones 18 a 21


def es_npn(valor: object) -> bool:
    """True si ``valor`` tiene la forma de un NPN (30 caracteres, condición numérica)."""
    if not isinstance(valor, str):
        return False
    texto = valor.strip()
    return (
        len(texto) == LONGITUD_NPN
        and texto[:5].isdigit()
        and texto[POSICION_CONDICION - 1].isdigit()
    )


def es_informal(valor: object) -> bool:
    """True si el NPN indica una informalidad (condición de propiedad = 2)."""
    return es_npn(valor) and str(valor).strip()[POSICION_CONDICION - 1] == CONDICION_INFORMAL


def predio_informal(valor: object) -> str | None:
    """Número del predio informal (p. ej. ``P001``) o None si el NPN no es de una informalidad."""
    return str(valor).strip()[_TERRENO] if es_informal(valor) else None
