# ==============================================================================
# Archivo  : tests/test_acotado.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.2.0 | 2026-11-05 | Convenciones por piso, colores fijos por piso,
#          |            | unidades superpuestas discontinuas, cota común gris,
#          |            | decimales automáticos en los ejes.
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
from generador_croquis.rendering.coordenadas import decimales_necesarios

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


def test_cotas_con_el_color_de_su_unidad_y_comunes_en_gris():
    _, figura = renderizar(Construccion("A", (UNIDAD_1, UNIDAD_2)))
    colores = {t.get_color() for t in cotas_de(figura)}
    assert colores == {TEMA.paleta_borde[0], TEMA.paleta_borde[1], TEMA.color_cota_comun}
    for texto in cotas_de(figura):
        assert texto.get_bbox_patch().get_edgecolor()[:3] == pytest.approx(
            tuple(int(texto.get_color()[i : i + 2], 16) / 255 for i in (1, 3, 5))
        )
    (comun,) = [t for t in cotas_de(figura) if t.get_text() == "8.60 m"]
    assert comun.get_color() == TEMA.color_cota_comun


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


def test_ejes_en_metros_sin_decimales_innecesarios():
    lejos = Polygon([(4811900 + x, 2340500 + y) for x, y in UNIDAD_1.exterior.coords])
    _, figura = renderizar(Construccion("A", (lejos,)))
    figura.canvas.draw()
    ax = figura.axes[0]
    etiquetas = [e.get_text() for e in ax.get_xticklabels() + ax.get_yticklabels() if e.get_text()]
    assert etiquetas
    assert all("e" not in e and "." not in e for e in etiquetas)  # p. ej. «4811904»
    assert any(e.startswith("48119") for e in etiquetas)  # coordenada completa
    assert ax.xaxis.get_offset_text().get_text() == ""


@pytest.mark.parametrize(
    ("paso", "esperado"),
    [(2.0, 0), (0.5, 1), (0.25, 2), (1.9999999999, 0), (0.0001, 4), (0.00001, 4)],
)
def test_decimales_necesarios(paso, esperado):
    assert decimales_necesarios(paso, 4) == esperado


# ── convenciones y pisos ────────────────────────────────────────────────────

PLANTA = box(0, 0, 12, 8)


def leyenda(figura):
    legend = figura.axes[0].get_legend()
    return None if legend is None else [t.get_text() for t in legend.get_texts()]


def test_sin_convenciones_con_una_sola_unidad():
    _, figura = renderizar(Construccion("A", (PLANTA,)))
    assert leyenda(figura) is None


def test_convenciones_por_piso_con_area():
    c = Construccion("A", (PLANTA, PLANTA, box(0, 0, 6, 8)), pisos=3, pisos_partes=(1, 2, 3))
    _, figura = renderizar(c)
    assert leyenda(figura) == [
        "Piso 1 · 96.00 m²",
        "Piso 2 · 96.00 m²",
        "Piso 3 · 48.00 m²",
        "Cota común a varias unidades",
    ]


def test_convenciones_sin_campo_de_pisos():
    # Dos unidades contiguas: comparten la pared x = 12 (8,00 m), que es una cota común.
    _, figura = renderizar(Construccion("A", (PLANTA, box(12, 0, 15, 8))))
    assert leyenda(figura) == [
        "Unidad 1 · 96.00 m²",
        "Unidad 2 · 24.00 m²",
        "Cota común a varias unidades",
    ]


def test_color_fijo_por_piso():
    """El piso 2 usa el segundo color aunque sea la única unidad dibujada con el piso 3."""
    c = Construccion("A", (PLANTA, box(0, 0, 6, 8)), pisos=3, pisos_partes=(2, 3))
    _, figura = renderizar(c)
    bordes = {
        linea.get_color() for linea in figura.axes[0].get_lines() if linea.get_linewidth() > 1
    }
    assert TEMA.paleta_borde[1] in bordes and TEMA.paleta_borde[2] in bordes
    assert TEMA.paleta_borde[0] not in bordes


def test_unidad_superpuesta_discontinua_y_sin_relleno():
    c = Construccion("A", (PLANTA, box(0, 0, 6, 8)), pisos=2, pisos_partes=(1, 2))
    _, figura = renderizar(c)
    ax = figura.axes[0]
    contornos = [lin for lin in ax.get_lines() if lin.get_linestyle() != "None"]
    estilos = {lin.get_color(): lin.get_linestyle() for lin in contornos}
    assert estilos[TEMA.paleta_borde[0]] == "-"
    assert estilos[TEMA.paleta_borde[1]] == "--"
    assert len(ax.patches) == 1  # solo el piso 1 tiene relleno


def test_agrupacion_ordena_partes_de_abajo_hacia_arriba():
    import geopandas as gpd

    from generador_croquis.domain import CapaCargada, SeleccionCampos
    from generador_croquis.services import agrupar_construcciones

    gdf = gpd.GeoDataFrame(
        {"cod": ["X", "X", "X"], "planta": [3, 1, 2]},
        geometry=[box(0, 0, 4, 4), box(0, 0, 10, 10), box(0, 0, 6, 6)],
        crs="EPSG:9377",
    )
    (c,) = agrupar_construcciones(CapaCargada(gdf, "t"), SeleccionCampos("cod", "planta"))
    assert c.pisos_partes == (1, 2, 3)
    assert [p.area for p in c.partes] == [100, 36, 16]


def test_una_sola_unidad_usa_el_primer_color_aunque_tenga_tres_pisos():
    _, figura = renderizar(Construccion("A", (PLANTA,), pisos=3, pisos_partes=(3,)))
    assert {t.get_color() for t in cotas_de(figura)} == {TEMA.paleta_borde[0]}
