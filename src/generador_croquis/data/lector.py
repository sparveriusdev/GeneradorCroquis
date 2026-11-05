# ==============================================================================
# Archivo  : src/generador_croquis/data/lector.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Repositorio que elige la fuente adecuada
#          |            | para una ruta (registro de estrategias inyectable).
# ==============================================================================
"""Lector de capas: punto único de acceso a las fuentes de datos."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from generador_croquis.data.fuentes import (
    FuenteDatos,
    FuenteGdb,
    FuenteShapefile,
    FuenteZip,
    LecturaFuente,
    Selector,
)
from generador_croquis.domain.exceptions import FormatoNoSoportadoError


class LectorCapas:
    """Selecciona la estrategia de lectura según la ruta recibida."""

    def __init__(self, fuentes: Sequence[FuenteDatos] | None = None):
        self._fuentes: tuple[FuenteDatos, ...] = tuple(
            fuentes if fuentes is not None else (FuenteZip(), FuenteShapefile(), FuenteGdb())
        )

    def leer(self, ruta: str | Path, selector: Selector) -> LecturaFuente:
        ruta = Path(ruta)
        for fuente in self._fuentes:
            if fuente.puede_abrir(ruta):
                return fuente.leer(ruta, selector)
        raise FormatoNoSoportadoError(
            f"Formato no soportado: '{ruta.name}'.\nUse .zip, .shp o una carpeta .gdb"
        )
