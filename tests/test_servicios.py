# ==============================================================================
# Archivo  : tests/test_servicios.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Pruebas de preparación, agrupación,
#          |            | lectura de fuentes y renderizado.
# ==============================================================================
from __future__ import annotations

import zipfile

import geopandas as gpd
import pytest
from shapely.geometry import LineString, box

from generador_croquis.data import LectorCapas
from generador_croquis.data.fuentes import LecturaFuente
from generador_croquis.domain import (
    ArchivoInvalidoError,
    CapaSinPoligonosError,
    FormatoNoSoportadoError,
    OperacionCanceladaError,
    SeleccionCampos,
)
from generador_croquis.rendering import RenderizadorMatplotlib
from generador_croquis.services import agrupar_construcciones, preparar_capa


def nunca_preguntar(*_args):
    raise AssertionError("No debía pedir selección")


# ── preparación ─────────────────────────────────────────────────────────────


def test_preparar_reproyecta_capas_geograficas():
    gdf = gpd.GeoDataFrame(geometry=[box(-75.7, 4.8, -75.69, 4.81)], crs="EPSG:4326")
    capa = preparar_capa(LecturaFuente(gdf, "geo"))
    assert capa.gdf.crs.to_epsg() == 9377
    assert any("reproyectó" in a for a in capa.avisos)


def test_preparar_descarta_no_poligonos():
    gdf = gpd.GeoDataFrame(
        geometry=[box(0, 0, 1, 1), LineString([(0, 0), (1, 1)]), None], crs="EPSG:9377"
    )
    assert preparar_capa(LecturaFuente(gdf, "x")).num_poligonos == 1


def test_preparar_falla_sin_poligonos():
    gdf = gpd.GeoDataFrame(geometry=[LineString([(0, 0), (1, 1)])], crs="EPSG:9377")
    with pytest.raises(CapaSinPoligonosError):
        preparar_capa(LecturaFuente(gdf, "x"))


def test_preparar_avisa_sin_crs():
    gdf = gpd.GeoDataFrame(geometry=[box(0, 0, 1, 1)])
    assert preparar_capa(LecturaFuente(gdf, "x")).avisos


# ── agrupación ──────────────────────────────────────────────────────────────


def test_agrupar_por_campo(capa_ejemplo):
    construcciones = agrupar_construcciones(capa_ejemplo, SeleccionCampos("codigo", "num_pisos"))
    a, b = construcciones
    assert (a.identificador, a.num_partes, a.pisos) == ("A", 2, 3)
    assert a.area_total == pytest.approx(70)
    assert (b.identificador, b.num_partes, b.pisos) == ("B", 1, None)  # "x" no es numérico
    assert a.descripcion_pisos == "3 pisos"


def test_agrupar_sin_campo_un_croquis_por_poligono(capa_ejemplo):
    construcciones = agrupar_construcciones(capa_ejemplo, SeleccionCampos())
    assert [c.identificador for c in construcciones] == ["0", "1", "2"]


# ── lectura de fuentes ──────────────────────────────────────────────────────


def test_leer_shapefile(shapefile):
    lectura = LectorCapas().leer(shapefile, nunca_preguntar)
    assert len(lectura.gdf) == 3
    assert lectura.nombre == "construcciones.shp"


def test_leer_zip_con_shapefile(zip_shapefile):
    lectura = LectorCapas().leer(zip_shapefile, nunca_preguntar)
    assert len(lectura.gdf) == 3
    assert lectura.nombre == "datos.zip > carpeta/construcciones.shp"


def test_leer_gdb_pide_capa(gdb):
    preguntas = []

    def selector(titulo, mensaje, opciones):
        preguntas.append(opciones)
        return "otra_capa"

    lectura = LectorCapas().leer(gdb, selector)
    assert preguntas == [["construcciones", "otra_capa"]]
    assert lectura.nombre == "datos.gdb > otra_capa"


def test_leer_gdb_cancelado(gdb):
    with pytest.raises(OperacionCanceladaError):
        LectorCapas().leer(gdb, lambda *_: None)


def test_zip_invalido(tmp_path):
    falso = tmp_path / "falso.zip"
    falso.write_text("no soy un zip")
    with pytest.raises(ArchivoInvalidoError):
        LectorCapas().leer(falso, nunca_preguntar)


def test_zip_sin_datos(tmp_path):
    vacio = tmp_path / "vacio.zip"
    with zipfile.ZipFile(vacio, "w") as zf:
        zf.writestr("leeme.txt", "hola")
    with pytest.raises(ArchivoInvalidoError, match="No se encontró"):
        LectorCapas().leer(vacio, nunca_preguntar)


def test_zip_slip_rechazado(tmp_path):
    malicioso = tmp_path / "malicioso.zip"
    with zipfile.ZipFile(malicioso, "w") as zf:
        zf.writestr("../fuera.shp", "x")
    with pytest.raises(ArchivoInvalidoError, match="insegura"):
        LectorCapas().leer(malicioso, nunca_preguntar)


def test_formato_no_soportado(tmp_path):
    otro = tmp_path / "datos.csv"
    otro.write_text("a,b")
    with pytest.raises(FormatoNoSoportadoError):
        LectorCapas().leer(otro, nunca_preguntar)


# ── renderizado ─────────────────────────────────────────────────────────────


def test_renderizar_y_exportar(capa_ejemplo, tmp_path):
    construcciones = agrupar_construcciones(capa_ejemplo, SeleccionCampos("codigo"))
    renderizador = RenderizadorMatplotlib()
    figura = renderizador.renderizar(construcciones)
    visibles = [ax for ax in figura.axes if ax.axison]
    assert len(visibles) == 2

    tamano = tuple(figura.get_size_inches())
    figura.set_size_inches(3, 3)  # simula que la vista previa la redimensionó
    destino = tmp_path / "croquis.png"
    renderizador.exportar(figura, destino)
    assert destino.stat().st_size > 0
    assert tuple(figura.get_size_inches()) == (3, 3)
    assert tamano != (3, 3)


def test_renderizar_vacio_falla():
    with pytest.raises(ValueError):
        RenderizadorMatplotlib().renderizar([])
