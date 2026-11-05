# ==============================================================================
# Archivo  : src/generador_croquis/domain/__init__.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.1.0 | 2026-11-05 | Exporta Version y las entidades de actualización.
#   v1.0.0 | 2026-11-05 | Creación. Expone el modelo de datos y las excepciones
#          |            | del dominio.
# ==============================================================================
"""Capa de dominio: entidades y excepciones, sin dependencias de UI."""

from generador_croquis.domain.exceptions import (
    ActualizacionError,
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
    Descarga,
    InfoRelease,
    ResultadoActualizacion,
    ResumenCapa,
    SeleccionCampos,
)
from generador_croquis.domain.version import Version

__all__ = [
    "ActualizacionError",
    "ArchivoInvalidoError",
    "CapaCargada",
    "CapaSinPoligonosError",
    "Construccion",
    "Cota",
    "CroquisError",
    "Descarga",
    "FormatoNoSoportadoError",
    "InfoRelease",
    "OperacionCanceladaError",
    "ResultadoActualizacion",
    "ResumenCapa",
    "SeleccionCampos",
    "Version",
]
