# ==============================================================================
# Archivo  : src/generador_croquis/data/__init__.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.1.0 | 2026-11-05 | Exporta el transporte HTTP (TransporteUrllib).
#   v1.0.0 | 2026-11-05 | Creación. Capa de acceso a datos (lectura de
#          |            | Shapefile, ZIP y File Geodatabase).
# ==============================================================================
"""Acceso a datos vectoriales."""

from generador_croquis.data.fuentes import (
    FuenteDatos,
    FuenteGdb,
    FuenteShapefile,
    FuenteZip,
    LecturaFuente,
    Selector,
)
from generador_croquis.data.http import TransporteHttp, TransporteUrllib
from generador_croquis.data.lector import LectorCapas

__all__ = [
    "FuenteDatos",
    "FuenteGdb",
    "FuenteShapefile",
    "FuenteZip",
    "LectorCapas",
    "LecturaFuente",
    "Selector",
    "TransporteHttp",
    "TransporteUrllib",
]
