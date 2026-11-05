# ==============================================================================
# Archivo  : src/generador_croquis/rendering/__init__.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Capa de dibujo de croquis.
# ==============================================================================
"""Dibujo de croquis."""

from generador_croquis.rendering.renderizador import Renderizador, RenderizadorMatplotlib

__all__ = ["Renderizador", "RenderizadorMatplotlib"]
