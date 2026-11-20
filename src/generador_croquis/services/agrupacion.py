# ==============================================================================
# Archivo  : src/generador_croquis/services/agrupacion.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.4.0 | 2026-11-20 | Informalidades (NPN con 2 en la posición 22): nunca
#          |            | se mezclan con las construcciones formales aunque
#          |            | compartan identificador. Con incluir_informales se
#          |            | agrupan aparte (por predio e identificador), al
#          |            | final y con la construcción formal cercana como
#          |            | referencia; si no, se omiten.
#   v1.3.0 | 2026-11-06 | Uso de cada parte (campo_uso), traducido con el
#          |            | dominio de la capa y en el mismo orden que las partes.
#   v1.2.0 | 2026-11-05 | Transmite el significado del campo de pisos.
#   v1.1.0 | 2026-11-05 | Guarda el piso de cada parte y ordena las partes
#          |            | de abajo hacia arriba (colores fijos por piso).
#   v1.0.0 | 2026-11-05 | Creación. Regla de negocio "polígonos con el mismo
#          |            | identificador forman una construcción", extraída de
#          |            | generar_croquis(). Mejora: los pisos se leen con
#          |            | conversión numérica tolerante (valores no numéricos
#          |            | se ignoran en vez de anular todo el grupo).
# ==============================================================================
"""Agrupación de polígonos en construcciones."""

from __future__ import annotations

import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

from generador_croquis.config import DISTANCIA_REFERENCIA_INFORMAL
from generador_croquis.domain.models import CapaCargada, Construccion, SeleccionCampos
from generador_croquis.services.geometria import poligonos_de


def _piso(valor: object) -> int | None:
    numero = pd.to_numeric(pd.Series([valor]), errors="coerce").iloc[0]
    return None if pd.isna(numero) else int(numero)


def _pisos(valores: pd.Series) -> int | None:
    numericos = pd.to_numeric(valores, errors="coerce").dropna()
    return int(numericos.max()) if not numericos.empty else None


def _construccion(
    capa: CapaCargada,
    seleccion: SeleccionCampos,
    clave: str,
    grupo: gpd.GeoDataFrame,
    predio_informal: str | None = None,
    referencia: tuple[Polygon | MultiPolygon, ...] = (),
) -> Construccion:
    campo_pisos = seleccion.campo_pisos if seleccion.campo_pisos in grupo.columns else None
    campo_uso = seleccion.campo_uso if seleccion.campo_uso in grupo.columns else None
    partes = list(grupo.geometry)
    usos: list[str | None] = (
        [capa.texto_valor(campo_uso, v) for v in grupo[campo_uso]] if campo_uso else []
    )
    pisos_partes: list[int | None] = []
    if campo_pisos:
        pisos_partes = [_piso(v) for v in grupo[campo_pisos]]
        # De abajo hacia arriba (sin piso al final); estable para partes del mismo piso.
        orden = sorted(
            range(len(partes)), key=lambda i: (pisos_partes[i] is None, pisos_partes[i] or 0)
        )
        partes = [partes[i] for i in orden]
        pisos_partes = [pisos_partes[i] for i in orden]
        usos = [usos[i] for i in orden] if usos else []
    return Construccion(
        identificador=clave,
        partes=tuple(partes),
        pisos=_pisos(grupo[campo_pisos]) if campo_pisos else None,
        pisos_partes=tuple(pisos_partes),
        significado_pisos=seleccion.significado_pisos,
        usos_partes=tuple(usos),
        predio_informal=predio_informal,
        referencia=referencia,
    )


def _referencia(formales: gpd.GeoDataFrame, zona) -> tuple[Polygon | MultiPolygon, ...]:
    """Silueta de las construcciones formales cercanas a una informalidad."""
    cercanas = formales.geometry[formales.geometry.distance(zona) <= DISTANCIA_REFERENCIA_INFORMAL]
    if cercanas.empty:
        return ()
    return tuple(poligonos_de(unary_union(list(cercanas))))


def _orden(clave: str, sin_campo: bool) -> tuple:
    return (int(clave),) if sin_campo else (clave,)


def agrupar_construcciones(capa: CapaCargada, seleccion: SeleccionCampos) -> list[Construccion]:
    """Convierte la capa en una lista de construcciones ordenadas por identificador.

    Las informalidades van aparte, después de las formales, y solo si se piden.
    """
    gdf = capa.gdf
    sin_campo = not (seleccion.campo_id and seleccion.campo_id in gdf.columns)
    claves = capa.claves(seleccion.campo_id)
    predios = capa.predios_informales
    formal = predios.isna()

    formales = gdf[formal]
    construcciones = [
        _construccion(capa, seleccion, str(clave), grupo)
        for clave, grupo in formales.groupby(claves[formal], sort=True)
    ]
    construcciones.sort(key=lambda c: _orden(c.identificador, sin_campo))

    if seleccion.incluir_informales and not formal.all():
        informales = gdf[~formal]
        adicionales = [
            _construccion(
                capa,
                seleccion,
                str(clave),
                grupo,
                predio_informal=str(predio),
                referencia=_referencia(formales, unary_union(list(grupo.geometry))),
            )
            for (predio, clave), grupo in informales.groupby(
                [predios[~formal], claves[~formal]], sort=True
            )
        ]
        adicionales.sort(key=lambda c: (c.predio_informal, *_orden(c.identificador, sin_campo)))
        construcciones.extend(adicionales)
    return construcciones
