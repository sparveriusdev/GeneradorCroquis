# ==============================================================================
# Archivo  : src/generador_croquis/services/__init__.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.1.0 | 2026-11-05 | Exporta ServicioActualizaciones.
#   v1.0.0 | 2026-11-05 | Creación. Capa de lógica de negocio.
# ==============================================================================
"""Lógica de negocio: geometría, detección de campos, preparación y agrupación."""

from generador_croquis.services.actualizaciones import ServicioActualizaciones
from generador_croquis.services.agrupacion import agrupar_construcciones
from generador_croquis.services.deteccion_campos import (
    detectar_campo,
    detectar_campo_id,
    detectar_campo_pisos,
)
from generador_croquis.services.geometria import calcular_cotas, poligonos_de
from generador_croquis.services.preparacion import preparar_capa
from generador_croquis.services.servicio_croquis import ServicioCroquis

__all__ = [
    "ServicioActualizaciones",
    "ServicioCroquis",
    "agrupar_construcciones",
    "calcular_cotas",
    "detectar_campo",
    "detectar_campo_id",
    "detectar_campo_pisos",
    "poligonos_de",
    "preparar_capa",
]
