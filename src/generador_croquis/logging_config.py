# ==============================================================================
# Archivo  : src/generador_croquis/logging_config.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Reemplaza registrar_error() por el módulo
#          |            | estándar logging con archivo rotativo en
#          |            | ~/.generador_croquis/croquis.log. Silencia los
#          |            | mensajes INFO de matplotlib (caché de fuentes).
# ==============================================================================
"""Configuración del registro de eventos y errores."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from generador_croquis.config import ARCHIVO_LOG

FORMATO = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def configurar_logging(archivo: Path = ARCHIVO_LOG, nivel: int = logging.INFO) -> None:
    """Envía los logs a un archivo rotativo y, si existe, a la consola."""
    handlers: list[logging.Handler] = []
    try:
        archivo.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(
            RotatingFileHandler(archivo, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        )
    except OSError:
        pass  # sin permisos de escritura: se continúa solo con consola
    if sys.stderr is not None:  # en ejecutables --windowed no hay consola
        handlers.append(logging.StreamHandler())
    logging.basicConfig(level=nivel, format=FORMATO, handlers=handlers, force=True)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)  # evita ruido de fuentes
