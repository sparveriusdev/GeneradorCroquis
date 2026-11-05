# ==============================================================================
# Archivo  : src/generador_croquis/__main__.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Permite `python -m generador_croquis` y sirve
#          |            | como script de entrada para PyInstaller (imports
#          |            | absolutos a propósito).
# ==============================================================================
"""Punto de entrada ejecutable del paquete."""

from generador_croquis.app import main

if __name__ == "__main__":
    raise SystemExit(main())
