# ==============================================================================
# Archivo  : src/generador_croquis/view/__init__.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Capa de presentación (Tkinter).
# ==============================================================================
"""Vistas Tkinter. Es la única capa que importa tkinter."""

from generador_croquis.view.ventana_principal import VentanaPrincipal

__all__ = ["VentanaPrincipal"]
