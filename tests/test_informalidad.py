# ==============================================================================
# Archivo  : tests/test_informalidad.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-20 | Creación. Informalidades (posición 22 del NPN = 2):
#          |            | reglas del NPN, detección del campo, conteo,
#          |            | agrupación aparte con referencia formal, dibujo y
#          |            | flujo del controlador. Datos sintéticos.
# ==============================================================================
from __future__ import annotations

import geopandas as gpd
import pytest
from shapely.geometry import box

from generador_croquis.config import Configuracion
from generador_croquis.controller import ControladorCroquis
from generador_croquis.data import LectorCapas
from generador_croquis.domain import CroquisError, SeleccionCampos, SignificadoPisos
from generador_croquis.domain.models import CapaCargada, ResumenCapa
from generador_croquis.domain.npn import es_informal, es_npn, predio_informal
from generador_croquis.rendering import RenderizadorMatplotlib
from generador_croquis.services import (
    ServicioCroquis,
    agrupar_construcciones,
    detectar_campo_npn,
    detectar_campo_pisos,
)

# NPN ficticios con la estructura del catastro (30 caracteres).
FORMAL = "990010100001100050092000000000"
INFORMAL = "99001010000110005P001200000000"
OTRO_INFORMAL = "99001010000110005P002200000000"


@pytest.mark.parametrize(
    ("valor", "npn", "informal", "predio"),
    [
        (FORMAL, True, False, None),
        (INFORMAL, True, True, "P001"),
        (f" {INFORMAL} ", True, True, "P001"),
        (INFORMAL[:-1], False, False, None),  # 29 caracteres
        ("A" * 30, False, False, None),
        (None, False, False, None),
        (12345, False, False, None),
    ],
)
def test_reglas_del_npn(valor, npn, informal, predio):
    assert es_npn(valor) is npn
    assert es_informal(valor) is informal
    assert predio_informal(valor) == predio


def test_detectar_campo_npn_por_nombre_y_contenido():
    tabla = gpd.pd.DataFrame(
        {
            "IDENTIFICADOR": ["1", "1"],
            "OTRO": [FORMAL, INFORMAL],
            "CODIGO_UNIDAD_CONSTRUCCION": [FORMAL, INFORMAL],
        }
    ).astype("string")
    assert detectar_campo_npn(tabla) == "CODIGO_UNIDAD_CONSTRUCCION"  # nombre conocido primero
    assert detectar_campo_npn(tabla.drop(columns="CODIGO_UNIDAD_CONSTRUCCION")) == "OTRO"
    assert detectar_campo_npn(tabla[["IDENTIFICADOR"]]) is None


def test_codigos_mal_formados_no_son_npn():
    tabla = gpd.pd.DataFrame({"CODIGO": ["123", "abc", FORMAL]})
    assert detectar_campo_npn(tabla) is None  # menos del 90 % con forma de NPN


def test_pisos_prefiere_planta_ubicacion_a_altura():
    columnas = ["IDENTIFICADOR", "TIPO_PLANTA", "PLANTA_UBICACION", "ALTURA"]
    assert detectar_campo_pisos(columnas) == "PLANTA_UBICACION"
    assert detectar_campo_pisos(["codigo", "ALTURA"]) == "ALTURA"  # solo como último recurso


def capa_informal(**kwargs) -> CapaCargada:
    """Unidad formal «1» (pisos 1 y 2), anexo formal «2» e informal «1» (pisos 1 y 2)."""
    gdf = gpd.GeoDataFrame(
        {
            "IDENTIFICADOR": ["1", "1", "2", "1", "1"],
            "PLANTA_UBICACION": [1, 2, 1, 1, 2],
            "CODIGO_UNIDAD_CONSTRUCCION": [FORMAL, FORMAL, FORMAL, INFORMAL, INFORMAL],
        },
        geometry=[
            box(0, 0, 10, 8),
            box(0, 0, 10, 8),
            box(12, 0, 15, 3),
            box(20, 0, 26, 7),
            box(20, 0, 26, 7),
        ],
        crs="EPSG:9377",
    )
    return CapaCargada(gdf=gdf, nombre="informal", campo_npn="CODIGO_UNIDAD_CONSTRUCCION", **kwargs)


def seleccion(incluir: bool) -> SeleccionCampos:
    return SeleccionCampos(
        "IDENTIFICADOR", "PLANTA_UBICACION", SignificadoPisos.UBICACION, None, incluir
    )


def test_conteo_y_resumen_separan_las_informalidades():
    capa = capa_informal()
    assert capa.num_informales == 2
    assert capa.nombres_predios_informales == ["P001"]
    assert capa.contar_construcciones("IDENTIFICADOR") == 3
    assert capa.contar_construcciones("IDENTIFICADOR", informales=False) == 2
    filas = dict(ResumenCapa(capa, "IDENTIFICADOR", None).filas())
    assert filas["Construcciones"].startswith("2 ")
    assert filas["Informalidades"] == "2 polígonos (predio P001)"


def test_sin_campo_npn_todo_es_formal():
    capa = CapaCargada(gdf=capa_informal().gdf, nombre="x")
    assert capa.num_informales == 0
    assert "Informalidades" not in dict(ResumenCapa(capa, "IDENTIFICADOR", None).filas())


def test_el_croquis_formal_nunca_mezcla_la_informalidad():
    a, b = agrupar_construcciones(capa_informal(), seleccion(False))
    assert (a.identificador, a.num_partes, a.es_informal) == ("1", 2, False)
    assert b.identificador == "2"


def test_croquis_adicional_va_al_final_con_la_referencia_formal():
    *formales, extra = agrupar_construcciones(capa_informal(), seleccion(True))
    assert [c.identificador for c in formales] == ["1", "2"]
    assert (extra.identificador, extra.predio_informal, extra.pisos_partes) == ("1", "P001", (1, 2))
    assert not any(c.referencia for c in formales)
    assert sum(p.area for p in extra.referencia) == pytest.approx(80 + 9)  # unidad 1 + anexo
    assert extra.extension.bounds == (0, 0, 26, 8)


def test_cada_predio_informal_tiene_su_croquis():
    capa = capa_informal()
    capa.gdf.loc[4, "CODIGO_UNIDAD_CONSTRUCCION"] = OTRO_INFORMAL
    extras = [c for c in agrupar_construcciones(capa, seleccion(True)) if c.es_informal]
    assert [(c.predio_informal, c.num_partes) for c in extras] == [("P001", 1), ("P002", 1)]


def test_dibujo_del_croquis_informal():
    construcciones = agrupar_construcciones(capa_informal(), seleccion(True))
    figura = RenderizadorMatplotlib().renderizar(construcciones)
    ax = figura.axes[2]
    assert ax.get_title().startswith("INFORMALIDAD P001\nConstrucción: 1")
    textos = [t.get_text() for t in ax.get_legend().texts]
    assert textos[-1].startswith("Formal de referencia")
    # La etiqueta del ID no tapa la informalidad ni la construcción formal de referencia.
    (etiqueta,) = [t for t in ax.texts if t.get_gid() == "etiqueta_id"]
    x, y = etiqueta.get_position()
    assert not any(p.contains(gpd.points_from_xy([x], [y])[0]) for p in construcciones[2].partes)
    assert not any(
        p.contains(gpd.points_from_xy([x], [y])[0]) for p in construcciones[2].referencia
    )
    assert "INFORMALIDAD" not in figura.axes[0].get_title()


def test_solo_informalidades_sin_pedir_su_croquis_avisa():
    capa = capa_informal()
    solo = CapaCargada(gdf=capa.gdf.iloc[3:], nombre="x", campo_npn=capa.campo_npn)
    servicio = ServicioCroquis(LectorCapas(), RenderizadorMatplotlib())
    with pytest.raises(CroquisError, match="Croquis adicional"):
        servicio.generar_figura(solo, seleccion(False))
    servicio.generar_figura(solo, seleccion(True))
    assert servicio.croquis_generados == 1


class Vista:
    def __init__(self):
        self.informalidades = None
        self.estado = ""
        self.figuras = []

    def mostrar_informalidades(self, cantidad, detalle):
        self.informalidades = (cantidad, detalle)

    def mostrar_estado(self, texto):
        self.estado = texto

    def mostrar_figura(self, figura):
        self.figuras.append(figura)

    def seleccionar_opcion(self, titulo, mensaje, opciones):
        return opciones[0]

    def __getattr__(self, nombre):  # el resto de métodos de la vista no importan aquí
        return lambda *args, **kwargs: None


@pytest.mark.parametrize(("incluir", "croquis"), [(True, 3), (False, 2)])
def test_controlador_ofrece_y_genera_el_croquis_adicional(tmp_path, incluir, croquis):
    ruta = tmp_path / "informal.shp"
    # Shapefile: nombres de 10 caracteres; el NPN se detecta por el contenido.
    columnas = {
        "IDENTIFICADOR": "ID",
        "PLANTA_UBICACION": "PISO",
        "CODIGO_UNIDAD_CONSTRUCCION": "COD_UNIDAD",
    }
    capa_informal().gdf.rename(columns=columnas).to_file(ruta, engine="pyogrio")
    vista = Vista()
    servicio = ServicioCroquis(LectorCapas(), RenderizadorMatplotlib(), Configuracion())
    ctrl = ControladorCroquis(vista, servicio)
    ctrl.cargar_archivo(ruta)
    cantidad, detalle = vista.informalidades
    assert cantidad == 2 and "P001" in detalle and "COD_UNIDAD" in detalle
    ctrl.generar("ID", "PISO", True, "0.15", "ubicacion", None, incluir)
    assert vista.estado.startswith(f"Listo: {croquis} croquis generados")
    assert ("de informalidades" in vista.estado) is incluir


def test_capa_sin_informalidades_desactiva_la_opcion(shapefile):
    vista = Vista()
    ctrl = ControladorCroquis(vista, ServicioCroquis(LectorCapas(), RenderizadorMatplotlib()))
    ctrl.cargar_archivo(shapefile)
    assert vista.informalidades == (0, "Esta capa no tiene.")
