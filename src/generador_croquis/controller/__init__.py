# ==============================================================================
# Archivo  : src/generador_croquis/controller/__init__.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.2.0 | 2026-11-05 | Exporta ControladorAyuda y VistaAyuda.
#   v1.1.0 | 2026-11-05 | Exporta el controlador "Acerca de" y sus protocolos.
#   v1.0.0 | 2026-11-05 | Creación. Capa de control (MVC).
# ==============================================================================
"""Controladores: coordinan vista y casos de uso."""

from generador_croquis.controller.acerca_de import (
    ControladorAcercaDe,
    EjecutorTareas,
    VistaAcercaDe,
)
from generador_croquis.controller.ayuda import ControladorAyuda, VistaAyuda
from generador_croquis.controller.controlador import ControladorCroquis, EstadoSesion
from generador_croquis.controller.vista import VistaCroquis

__all__ = [
    "ControladorAcercaDe",
    "ControladorAyuda",
    "ControladorCroquis",
    "EjecutorTareas",
    "EstadoSesion",
    "VistaAcercaDe",
    "VistaAyuda",
    "VistaCroquis",
]
