# ==============================================================================
# Archivo  : tests/test_deteccion_campos.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Pruebas de detección automática de campos.
# ==============================================================================
from __future__ import annotations

import pytest

from generador_croquis.services.deteccion_campos import detectar_campo_id, detectar_campo_pisos


@pytest.mark.parametrize(
    ("columnas", "esperado"),
    [
        (["nombre", "CODIGO", "geometry"], "CODIGO"),  # exacta, sin mayúsculas
        (["OBJECTID", "id"], "id"),  # prioridad de candidatos
        (["codigo_predio", "area"], "codigo_predio"),  # parcial
        (["width", "area"], None),  # "id" no coincide con "width"
        (["ID_EDIFICIO", "area"], "ID_EDIFICIO"),  # "id" como palabra
        (["area", "geometry"], None),
    ],
)
def test_detectar_campo_id(columnas, esperado):
    assert detectar_campo_id(columnas) == esperado


@pytest.mark.parametrize(
    ("columnas", "esperado"),
    [
        (["codigo", "NUM_PISOS"], "NUM_PISOS"),
        (["codigo", "pisos"], "pisos"),
        (["Floors"], "Floors"),
        (["codigo", "area"], None),
    ],
)
def test_detectar_campo_pisos(columnas, esperado):
    assert detectar_campo_pisos(columnas) == esperado
