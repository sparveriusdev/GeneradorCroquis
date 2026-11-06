# ==============================================================================
# Archivo  : src/generador_croquis/data/__init__.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.2.0 | 2026-11-06 | Exporta leer_dominios y Dominios.
#   v1.1.0 | 2026-11-05 | Exporta el transporte HTTP (TransporteUrllib).
#   v1.0.0 | 2026-11-05 | Creación. Capa de acceso a datos (lectura de
#          |            | Shapefile, ZIP y File Geodatabase).
# ==============================================================================
"""Acceso a datos vectoriales."""

from generador_croquis.data.dominios import Dominios, leer_dominios
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
    "Dominios",
    "FuenteDatos",
    "FuenteGdb",
    "FuenteShapefile",
    "FuenteZip",
    "LectorCapas",
    "LecturaFuente",
    "Selector",
    "TransporteHttp",
    "TransporteUrllib",
    "leer_dominios",
]
