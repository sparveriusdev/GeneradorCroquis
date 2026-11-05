# ==============================================================================
# Archivo  : tests/test_geometria.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Pruebas del cálculo de cotas.
# ==============================================================================
from __future__ import annotations

import pytest
from shapely.geometry import MultiPolygon, Point, box

from generador_croquis.services.geometria import (
    angulo_legible,
    calcular_cotas,
    poligonos_de,
)


def test_cotas_de_un_rectangulo():
    cotas = calcular_cotas(box(0, 0, 10, 5))
    assert sorted(round(c.longitud, 6) for c in cotas) == [5, 5, 10, 10]
    assert {c.texto for c in cotas} == {"10.00 m", "5.00 m"}


def test_cotas_quedan_fuera_del_poligono():
    poligono = box(0, 0, 10, 5)
    for cota in calcular_cotas(poligono):
        assert not poligono.contains(Point(cota.posicion))


def test_lados_degenerados_se_omiten():
    from shapely.geometry import Polygon

    poligono = Polygon([(0, 0), (10, 0), (10, 0.001), (10, 5), (0, 5)])
    assert len(calcular_cotas(poligono)) == 4


@pytest.mark.parametrize(
    ("entrada", "esperado"), [(0, 0), (90, 90), (135, -45), (-135, 45), (180, 0), (-90, -90)]
)
def test_angulo_legible(entrada, esperado):
    assert angulo_legible(entrada) == esperado


def test_poligonos_de():
    multi = MultiPolygon([box(0, 0, 1, 1), box(2, 2, 3, 3)])
    assert len(poligonos_de(multi)) == 2
    assert len(poligonos_de(box(0, 0, 1, 1))) == 1
    assert poligonos_de(Point(0, 0)) == []
    assert poligonos_de(None) == []
