# ==============================================================================
# Archivo  : src/generador_croquis/services/deteccion_campos.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.2.0 | 2026-11-06 | detectar_campo_uso() (USO, destino…).
#   v1.1.0 | 2026-11-05 | detectar_significado_pisos(): por el nombre del
#          |            | campo decide si indica el piso de la unidad
#          |            | (PLANTA_UBICACION) o el total de pisos (NUMERO_PISOS).
#   v1.0.0 | 2026-11-05 | Creación. Unifica detectar_campo_id y
#          |            | detectar_campo_pisos (código duplicado) en un único
#          |            | algoritmo. Mejora: los candidatos cortos (<= 3
#          |            | letras, p. ej. "id") solo coinciden por palabra
#          |            | completa, evitando falsos positivos como "width".
# ==============================================================================
"""Detección automática de campos relevantes en la tabla de atributos."""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence

from generador_croquis.config import (
    CANDIDATOS_CAMPO_ID,
    CANDIDATOS_CAMPO_PISOS,
    CANDIDATOS_CAMPO_USO,
)
from generador_croquis.domain.models import SignificadoPisos

_LONGITUD_MINIMA_SUBCADENA = 4


def _palabras(nombre: str) -> set[str]:
    return set(re.split(r"[^a-z0-9]+", nombre.lower())) - {""}


def _coincide_parcial(candidato: str, columna: str) -> bool:
    if len(candidato) < _LONGITUD_MINIMA_SUBCADENA:
        return candidato in _palabras(columna)
    return candidato in columna.lower()


def detectar_campo(columnas: Iterable[str], candidatos: Sequence[str]) -> str | None:
    """Busca la primera columna que coincida con algún candidato.

    Primero busca coincidencias exactas (sin distinguir mayúsculas) en el
    orden de prioridad de ``candidatos``; luego coincidencias parciales.
    """
    columnas = [c for c in columnas if c != "geometry"]
    por_minuscula = {c.lower(): c for c in reversed(columnas)}

    for candidato in candidatos:
        if candidato in por_minuscula:
            return por_minuscula[candidato]
    for candidato in candidatos:
        for columna in columnas:
            if _coincide_parcial(candidato, columna):
                return columna
    return None


def detectar_campo_id(columnas: Iterable[str]) -> str | None:
    return detectar_campo(columnas, CANDIDATOS_CAMPO_ID)


def detectar_campo_pisos(columnas: Iterable[str]) -> str | None:
    return detectar_campo(columnas, CANDIDATOS_CAMPO_PISOS)


def detectar_campo_uso(columnas: Iterable[str]) -> str | None:
    return detectar_campo(columnas, CANDIDATOS_CAMPO_USO)


# Palabras que delatan cada significado del campo de pisos (se comparan por palabra).
_PALABRAS_TOTAL = {
    "numero",
    "num",
    "nro",
    "no",
    "n",
    "total",
    "cantidad",
    "cant",
    "npisos",
    "numpisos",
    "totalpisos",
    "pisos",
    "niveles",
    "plantas",
}
_PALABRAS_UBICACION = {"planta", "ubicacion", "ubic", "nivel", "piso", "level", "floor"}


def detectar_significado_pisos(campo: str | None) -> SignificadoPisos:
    """Deduce si el campo indica el piso de la unidad o el total de pisos.

    ``PLANTA_UBICACION`` → piso de la unidad; ``NUMERO_PISOS`` → total. Si el nombre no es
    concluyente se asume el total (el caso más común en capas de construcciones).
    """
    if not campo:
        return SignificadoPisos.TOTAL
    palabras = _palabras(campo)
    if palabras & _PALABRAS_TOTAL:
        return SignificadoPisos.TOTAL
    if palabras & _PALABRAS_UBICACION:
        return SignificadoPisos.UBICACION
    return SignificadoPisos.TOTAL
