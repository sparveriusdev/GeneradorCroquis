# ==============================================================================
# Archivo  : tests/test_uso.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-06 | Creación. Campo de uso: dominios de la GDB (XML de
#          |            | GDB_Items), traducción de códigos, detección,
#          |            | agrupación, convenciones y flujo del controlador.
# ==============================================================================
from __future__ import annotations

import math

import geopandas as gpd
import pytest
from shapely.geometry import box

from generador_croquis.config import Configuracion
from generador_croquis.controller import ControladorCroquis
from generador_croquis.data import LectorCapas, leer_dominios
from generador_croquis.data.dominios import dominios_desde_items
from generador_croquis.domain import Construccion, SeleccionCampos, SignificadoPisos
from generador_croquis.domain.models import CapaCargada, codigo_texto
from generador_croquis.rendering import RenderizadorMatplotlib
from generador_croquis.services import (
    ServicioCroquis,
    agrupar_construcciones,
    detectar_campo_uso,
)

# Definiciones XML como las que ArcGIS guarda en la tabla de sistema GDB_Items.
CAPA_XML = """<DEFeatureClassInfo xsi:type='typens:DEFeatureClassInfo'
 xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'
 xmlns:typens='http://www.esri.com/schemas/ArcGIS/10.8'>
 <Name>u_lc_unidadconstruccion</Name><GPFieldInfoExs>
 <GPFieldInfoEx><Name>CODIGO</Name><FieldType>esriFieldTypeString</FieldType></GPFieldInfoEx>
 <GPFieldInfoEx><Name>USO</Name><DomainName>lc_usouconstipo</DomainName></GPFieldInfoEx>
 <GPFieldInfoEx><Name>TIPO</Name><DomainName>sin_definir</DomainName></GPFieldInfoEx>
 </GPFieldInfoExs></DEFeatureClassInfo>"""
DOMINIO_XML = """<GPCodedValueDomain2 xsi:type='typens:GPCodedValueDomain2'
 xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'
 xmlns:xs='http://www.w3.org/2001/XMLSchema'>
 <DomainName>lc_usouconstipo</DomainName><CodedValues>
 <CodedValue><Name>(Residencial) Vivienda hasta 3 pisos</Name><Code xsi:type='xs:int'>11</Code>
 </CodedValue>
 <CodedValue><Name>(Anexo) Ramadas - Cobertizos - Caneyes</Name><Code>93</Code></CodedValue>
 </CodedValues></GPCodedValueDomain2>"""
USOS = {
    "11": "(Residencial) Vivienda hasta 3 pisos",
    "93": "(Anexo) Ramadas - Cobertizos - Caneyes",
}


def test_dominios_desde_items_asocia_campo_y_dominio():
    items = [
        ("u_lc_unidadconstruccion", CAPA_XML),
        ("lc_usouconstipo", DOMINIO_XML),
        ("otra", math.nan),  # filas sin definición (NaN) se ignoran
        (math.nan, "<no es xml"),
    ]
    assert dominios_desde_items(items, "U_LC_UNIDADCONSTRUCCION") == {"USO": USOS}
    assert dominios_desde_items(items, "otra_capa") == {}


def test_leer_dominios_sin_gdb_devuelve_vacio(shapefile):
    assert leer_dominios(shapefile, "construcciones") == {}


def test_gdb_sin_dominios_se_lee_igual(gdb):
    lectura = LectorCapas().leer(gdb, lambda t, m, o: "construcciones")
    assert lectura.dominios == {}
    assert len(lectura.gdf) == 3


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [(11, "11"), (11.0, "11"), (2.5, "2.5"), (" Vivienda ", "Vivienda"), ("", None)]
    + [(None, None), (math.nan, None)],
)
def test_codigo_texto(valor, esperado):
    assert codigo_texto(valor) == esperado


def capa_con_uso(dominios=None) -> CapaCargada:
    gdf = gpd.GeoDataFrame(
        {"codigo": ["A", "A", "B"], "piso": [2, 1, 1], "USO": [93.0, 11.0, None]},
        geometry=[box(0, 0, 4, 4), box(0, 0, 10, 5), box(20, 0, 26, 4)],
        crs="EPSG:9377",
    )
    return CapaCargada(gdf=gdf, nombre="usos", dominios=dominios or {})


def test_texto_valor_usa_el_dominio_o_el_valor():
    capa = capa_con_uso({"USO": USOS})
    assert capa.texto_valor("USO", 11.0) == USOS["11"]
    assert capa.texto_valor("USO", 99) == "99"  # código sin descripción: tal cual
    assert capa.texto_valor("OTRO", "Comercio") == "Comercio"
    assert capa.texto_valor("USO", None) is None


def test_agrupacion_guarda_el_uso_de_cada_parte_en_orden_de_piso():
    seleccion = SeleccionCampos("codigo", "piso", SignificadoPisos.UBICACION, "USO")
    a, b = agrupar_construcciones(capa_con_uso({"USO": USOS}), seleccion)
    assert a.pisos_partes == (1, 2)  # de abajo hacia arriba
    assert a.usos_partes == (USOS["11"], USOS["93"])
    assert [g.usos for g in a.grupos_por_piso()] == [(USOS["11"],), (USOS["93"],)]
    assert b.usos_partes == (None,)
    assert not b.con_uso


def test_sin_campo_de_uso_no_hay_usos():
    (a, _) = agrupar_construcciones(capa_con_uso(), SeleccionCampos("codigo", "piso"))
    assert a.usos_partes == ()


def test_varias_unidades_del_mismo_piso_listan_usos_distintos_una_vez():
    c = Construccion(
        "A",
        (box(0, 0, 1, 1), box(2, 0, 3, 1), box(4, 0, 5, 1)),
        pisos=1,
        pisos_partes=(1, 1, 1),
        significado_pisos=SignificadoPisos.UBICACION,
        usos_partes=("Vivienda", "Comercio", "Vivienda"),
    )
    (grupo,) = c.grupos_por_piso()
    assert grupo.usos == ("Vivienda", "Comercio")


def test_usos_partes_debe_tener_un_valor_por_parte():
    with pytest.raises(ValueError):
        Construccion("A", (box(0, 0, 1, 1),), usos_partes=("a", "b"))


@pytest.mark.parametrize(
    ("columnas", "esperado"),
    [
        (["IDENTIFICADOR", "PLANTA_UBICACION", "USO"], "USO"),
        (["codigo", "destino"], "destino"),
        (["codigo", "museo", "usuario"], None),  # «uso» solo coincide como palabra completa
    ],
)
def test_detectar_campo_uso(columnas, esperado):
    assert detectar_campo_uso(columnas) == esperado


def textos_convenciones(figura):
    return [t.get_text() for ax in figura.axes if ax.get_legend() for t in ax.get_legend().texts]


def test_convenciones_muestran_el_uso_debajo_del_piso():
    seleccion = SeleccionCampos("codigo", "piso", SignificadoPisos.UBICACION, "USO")
    construcciones = agrupar_construcciones(capa_con_uso({"USO": USOS}), seleccion)
    figura = RenderizadorMatplotlib().renderizar(construcciones)
    textos = textos_convenciones(figura)
    assert any(t.startswith("Piso 1 · ") and t.endswith("\n" + USOS["11"]) for t in textos)
    assert any(t.startswith("Piso 2 · ") and USOS["93"].split()[0] in t for t in textos)


def test_una_sola_unidad_con_uso_tiene_leyenda():
    c = Construccion("B", (box(0, 0, 6, 4),), usos_partes=("Comercio",))
    figura = RenderizadorMatplotlib().renderizar([c])
    assert textos_convenciones(figura) == ["Unidad 1 · 24.00 m²\nComercio"]


def test_usos_largos_se_parten_en_lineas():
    uso = "(Comercial) Centros comerciales y locales en propiedad horizontal"
    c = Construccion("B", (box(0, 0, 6, 4),), usos_partes=(uso,))
    (texto,) = textos_convenciones(RenderizadorMatplotlib().renderizar([c]))
    lineas = texto.split("\n")[1:]
    assert len(lineas) > 1 and " ".join(lineas) == uso


class VistaMinima:
    """Vista falsa con lo necesario para cargar y generar."""

    def __init__(self):
        self.campo_uso = "sin llamar"
        self.figuras = []

    def configurar_campos(self, campos, campo_id, campo_pisos, nota_id, nota_pisos, *uso):
        self.campo_uso = uso[0] if uso else None

    def mostrar_figura(self, figura):
        self.figuras.append(figura)

    def seleccionar_opcion(self, titulo, mensaje, opciones):
        return opciones[0]

    def confirmar(self, titulo, mensaje):
        return True

    def __getattr__(self, nombre):  # el resto de métodos de la vista no importan aquí
        return lambda *args, **kwargs: None


def test_controlador_sugiere_y_usa_el_campo_de_uso(tmp_path):
    ruta = tmp_path / "usos.shp"
    capa_con_uso().gdf.to_file(ruta, engine="pyogrio")
    vista = VistaMinima()
    servicio = ServicioCroquis(LectorCapas(), RenderizadorMatplotlib(), Configuracion())
    ctrl = ControladorCroquis(vista, servicio)
    ctrl.cargar_archivo(ruta)
    assert vista.campo_uso == "USO"
    ctrl.generar("codigo", "piso", True, "0.15", "ubicacion", "USO")
    (figura,) = vista.figuras
    textos = textos_convenciones(figura)
    assert any(t.endswith("\n11") for t in textos)  # shapefile: sin dominio, el código
