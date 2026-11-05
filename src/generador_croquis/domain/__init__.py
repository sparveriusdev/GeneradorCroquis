# ==============================================================================
# Archivo  : src/generador_croquis/domain/__init__.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Expone el modelo de datos y las excepciones
#          |            | del dominio.
# ==============================================================================
"""Capa de dominio: entidades y excepciones, sin dependencias de UI."""

from generador_croquis.domain.exceptions import (
    ArchivoInvalidoError,
    CapaSinPoligonosError,
    CroquisError,
    FormatoNoSoportadoError,
    OperacionCanceladaError,
)
from generador_croquis.domain.models import (
    CapaCargada,
    Construccion,
    Cota,
    ResumenCapa,
    SeleccionCampos,
)

__all__ = [
    "ArchivoInvalidoError",
    "CapaCargada",
    "CapaSinPoligonosError",
    "Construccion",
    "Cota",
    "CroquisError",
    "FormatoNoSoportadoError",
    "OperacionCanceladaError",
    "ResumenCapa",
    "SeleccionCampos",
]
