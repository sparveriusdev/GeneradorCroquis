# ==============================================================================
# Archivo  : src/generador_croquis/controller/__init__.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Capa de control (MVC).
# ==============================================================================
"""Controladores: coordinan vista y casos de uso."""

from generador_croquis.controller.controlador import ControladorCroquis, EstadoSesion
from generador_croquis.controller.vista import VistaCroquis

__all__ = ["ControladorCroquis", "EstadoSesion", "VistaCroquis"]
