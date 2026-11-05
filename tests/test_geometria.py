# ==============================================================================
# Archivo  : tests/test_geometria.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v2.0.0 | 2026-11-05 | Pruebas de vértices principales (Douglas-Peucker),
#          |            | lados como suma de tramos, normal exterior en
#          |            | polígonos cóncavos y validación de opciones.
#   v1.0.0 | 2026-11-05 | Creación. Pruebas del cálculo de cotas.
# ==============================================================================
from __future__ import annotations

import pytest
from shapely.geometry import MultiPolygon, Point, Polygon, box

from generador_croquis.domain import Lado, OpcionesAcotado, OpcionInvalidaError
from generador_croquis.services.geometria import (
    angulo_legible,
    calcular_lados,
    indices_principales,
    poligonos_de,
)

TODOS = OpcionesAcotado(solo_principales=False)

# Rectángulo 12 x 8 con vértices de ajuste casi alineados en todos sus lados.
CON_AJUSTES = Polygon(
    [
        (0, 0),
        (3.1, 0.04),
        (6.2, -0.03),
        (9.0, 0.02),
        (12, 0),
        (12.03, 2.6),
        (11.98, 5.1),
        (12, 8),
        (6, 8.05),
        (0, 8),
        (0.02, 4.3),
    ]
)
# Forma en L (cóncava): el entrante es una esquina real.
EN_L = Polygon([(0, 0), (10, 0), (10, 4), (4, 4), (4, 10), (0, 10)])


def medidas(lados: list[Lado]) -> list[float]:
    return sorted(round(lado.longitud, 2) for lado in lados)


def test_solo_vertices_principales_en_rectangulo_con_ajustes():
    lados = calcular_lados(CON_AJUSTES)
    assert len(lados) == 4
    assert sum(lado.intermedios for lado in lados) == len(CON_AJUSTES.exterior.coords) - 1 - 4


def test_longitud_es_la_suma_de_los_tramos():
    lados = calcular_lados(CON_AJUSTES)
    assert sum(lado.longitud for lado in lados) == pytest.approx(CON_AJUSTES.length)


def test_todos_los_vertices_si_se_desactiva():
    assert len(calcular_lados(CON_AJUSTES, TODOS)) == len(CON_AJUSTES.exterior.coords) - 1


def test_quiebre_real_corto_se_conserva_y_desaparece_con_tolerancia_grande():
    con_quiebre = Polygon([(0, 0), (12, 0), (12, 8), (8, 8), (8, 8.6), (0, 8.6)])
    assert 0.6 in medidas(calcular_lados(con_quiebre, OpcionesAcotado(tolerancia=0.15)))
    assert 0.6 not in medidas(calcular_lados(con_quiebre, OpcionesAcotado(tolerancia=1.0)))


def test_forma_en_l_conserva_sus_seis_esquinas():
    assert medidas(calcular_lados(EN_L)) == [4.0, 4.0, 6.0, 6.0, 10.0, 10.0]


def test_inicio_en_vertice_de_ajuste_no_cambia_el_resultado():
    anillo = list(CON_AJUSTES.exterior.coords)[:-1]
    rotado = anillo[2:] + anillo[:2]  # el primer punto ahora es un vértice de ajuste
    principales = {anillo[i] for i in indices_principales(anillo, 0.15)}
    principales_rotado = {rotado[i] for i in indices_principales(rotado, 0.15)}
    assert principales == principales_rotado == {(0, 0), (12, 0), (12, 8), (0, 8)}


def test_siempre_quedan_al_menos_tres_vertices():
    casi_plano = Polygon([(0, 0), (10, 0), (10, 0.05), (0, 0.05)])
    assert len(indices_principales(list(casi_plano.exterior.coords)[:-1], 1.0)) >= 3


def test_normal_apunta_hacia_afuera_incluso_en_poligonos_concavos():
    for poligono in (EN_L, CON_AJUSTES, box(0, 0, 10, 5)):
        for lado in calcular_lados(poligono):
            medio = lado.punto(0.5)
            afuera = Point(medio[0] + lado.normal[0] * 0.1, medio[1] + lado.normal[1] * 0.1)
            assert not poligono.contains(afuera), lado


def test_orientacion_del_anillo_no_importa():
    horario = Polygon(list(EN_L.exterior.coords)[::-1])
    assert medidas(calcular_lados(horario)) == medidas(calcular_lados(EN_L))


def test_lado_coincide_con_su_inverso():
    a = Lado((0, 0), (5, 0), 5.0, (0, -1))
    b = Lado((5.02, 0), (0, 0.01), 5.0, (0, 1))
    assert a.coincide_con(b, 0.05)
    assert not a.coincide_con(Lado((0, 0), (5, 0), 5.1, (0, -1)), 0.05)


@pytest.mark.parametrize("tolerancia", [-0.1, 11])
def test_tolerancia_fuera_de_rango(tolerancia):
    with pytest.raises(OpcionInvalidaError):
        OpcionesAcotado(tolerancia=tolerancia)


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
