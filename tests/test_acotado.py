# ==============================================================================
# Archivo  : tests/test_acotado.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.1.0 | 2026-11-05 | Ejes con 4 decimales y sin notación científica.
#   v1.0.0 | 2026-11-05 | Creación. Pruebas del acotado en la figura: cotas
#          |            | del color de su unidad, lado común acotado una vez,
#          |            | ninguna etiqueta solapada ni fuera del croquis.
# ==============================================================================
from __future__ import annotations

import itertools

import pytest
from shapely.geometry import Polygon, box

from generador_croquis.config import TemaCroquis
from generador_croquis.domain import Construccion, OpcionesAcotado
from generador_croquis.rendering import RenderizadorMatplotlib

TEMA = TemaCroquis()
# Unidad 1 (piso 1) con vértices de ajuste y unidad 2 (piso 2) superpuesta a la izquierda,
# que comparte con la 1 el lado izquierdo completo (8,60 m).
UNIDAD_1 = Polygon(
    [
        (0, 0),
        (3.1, 0.04),
        (6.2, -0.03),
        (9.0, 0.02),
        (12, 0),
        (12.03, 2.6),
        (11.98, 5.1),
        (12, 8),
        (8.0, 8.05),
        (8.0, 8.6),
        (0, 8.6),
        (0.02, 4.3),
    ]
)
UNIDAD_2 = Polygon([(0, 0), (3.1, 0.04), (6.2, -0.03), (6.2, 8.6), (0, 8.6), (0.02, 4.3)])


def cotas_de(figura):
    return [t for ax in figura.axes for t in ax.texts if t.get_gid() == "cota"]


def renderizar(*construcciones, opciones=None):
    renderizador = RenderizadorMatplotlib()
    figura = renderizador.renderizar(list(construcciones), opciones)
    return renderizador, figura


def test_cotas_con_el_color_de_su_unidad():
    _, figura = renderizar(Construccion("A", (UNIDAD_1, UNIDAD_2)))
    colores = {t.get_color() for t in cotas_de(figura)}
    assert colores == {TEMA.paleta_borde[0], TEMA.paleta_borde[1]}
    for texto in cotas_de(figura):
        assert texto.get_bbox_patch().get_edgecolor()[:3] == pytest.approx(
            tuple(int(texto.get_color()[i : i + 2], 16) / 255 for i in (1, 3, 5))
        )


def test_lado_comun_con_la_misma_medida_se_acota_una_vez():
    _, figura = renderizar(Construccion("A", (UNIDAD_1, UNIDAD_2)))
    textos = [t.get_text() for t in cotas_de(figura)]
    assert textos.count("8.60 m") == 1  # lado izquierdo, compartido por ambas unidades


def test_solo_principales_reduce_las_cotas():
    construccion = Construccion("A", (UNIDAD_1,))
    _, principales = renderizar(construccion)
    _, todos = renderizar(construccion, opciones=OpcionesAcotado(solo_principales=False))
    assert len(cotas_de(principales)) == 6
    assert len(cotas_de(todos)) == len(UNIDAD_1.exterior.coords) - 1


@pytest.mark.parametrize("solo_principales", [True, False])
def test_ninguna_cota_se_solapa_ni_sale_del_croquis(solo_principales):
    construcciones = [
        Construccion("A", (UNIDAD_1, UNIDAD_2), pisos=2),
        Construccion("B", (box(0, 0, 3, 2), box(0, 0, 1.5, 2))),
        Construccion("C", (Polygon([(0, 0), (10, 0), (10, 4), (4, 4), (4, 10), (0, 10)]),)),
    ]
    renderizador, figura = renderizar(
        *construcciones, opciones=OpcionesAcotado(solo_principales=solo_principales)
    )
    renderer = figura.canvas.get_renderer()
    figura.canvas.draw()
    assert renderizador.cotas_sin_espacio == 0
    for ax in figura.axes:
        cajas = [t.get_window_extent(renderer) for t in ax.texts if t.get_gid() == "cota"]
        for a, b in itertools.combinations(cajas, 2):
            assert not a.overlaps(b)
        for caja in cajas:
            assert ax.bbox.x0 <= caja.x0 and caja.x1 <= ax.bbox.x1
            assert ax.bbox.y0 <= caja.y0 and caja.y1 <= ax.bbox.y1


def test_ejes_con_coordenadas_completas_a_cuatro_decimales():
    lejos = Polygon([(4811900 + x, 2340500 + y) for x, y in UNIDAD_1.exterior.coords])
    _, figura = renderizar(Construccion("A", (lejos,)))
    figura.canvas.draw()
    ax = figura.axes[0]
    etiquetas = [e.get_text() for e in ax.get_xticklabels() + ax.get_yticklabels() if e.get_text()]
    assert etiquetas
    assert all("e" not in e and len(e.split(".")[1]) == 4 for e in etiquetas)
    assert ax.xaxis.get_offset_text().get_text() == ""
