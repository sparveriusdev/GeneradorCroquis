# ==============================================================================
# Archivo  : src/generador_croquis/domain/exceptions.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Jerarquía de excepciones propia para
#          |            | distinguir errores esperados (mensaje al usuario) de
#          |            | fallos inesperados (log + traza).
# ==============================================================================
"""Excepciones del dominio."""


class CroquisError(Exception):
    """Error base esperado: su mensaje es apto para mostrarse al usuario."""


class OperacionCanceladaError(CroquisError):
    """El usuario canceló una selección interactiva."""


class FormatoNoSoportadoError(CroquisError):
    """La ruta no corresponde a ningún formato de entrada soportado."""


class ArchivoInvalidoError(CroquisError):
    """El archivo existe pero está corrupto, incompleto o no se puede leer."""


class CapaSinPoligonosError(CroquisError):
    """La capa seleccionada no contiene polígonos válidos."""
