# ==============================================================================
# Archivo  : src/generador_croquis/services/deteccion_campos.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
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

from generador_croquis.config import CANDIDATOS_CAMPO_ID, CANDIDATOS_CAMPO_PISOS

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
