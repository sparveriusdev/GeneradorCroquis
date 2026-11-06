# ==============================================================================
# Archivo  : src/generador_croquis/services/preparacion.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.1.0 | 2026-11-06 | Pasa a CapaCargada los dominios codificados de la fuente.
#   v1.0.0 | 2026-11-05 | Creación. Migrado desde preparar_gdf(): limpieza de
#          |            | geometrías y reproyección a metros; devuelve la
#          |            | entidad CapaCargada.
# ==============================================================================
"""Limpieza y normalización de capas antes de generar croquis."""

from __future__ import annotations

from generador_croquis.config import EPSG_METROS
from generador_croquis.data.fuentes import LecturaFuente
from generador_croquis.domain.exceptions import CapaSinPoligonosError
from generador_croquis.domain.models import CapaCargada

TIPOS_POLIGONO = ("Polygon", "MultiPolygon")


def preparar_capa(lectura: LecturaFuente, epsg_metros: int = EPSG_METROS) -> CapaCargada:
    """Deja solo polígonos válidos y garantiza unidades métricas si es posible."""
    gdf = lectura.gdf
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty]
    gdf = gdf[gdf.geom_type.isin(TIPOS_POLIGONO)].copy()
    if gdf.empty:
        raise CapaSinPoligonosError(
            "La capa no contiene polígonos (Polygon / MultiPolygon).\n"
            "Seleccione una capa de polígonos."
        )

    avisos: list[str] = []
    if gdf.crs is None:
        avisos.append(
            "AVISO: la capa no tiene CRS definido. Las cotas se calculan "
            "en las unidades originales (pueden no ser metros)."
        )
    elif gdf.crs.is_geographic:
        gdf = gdf.to_crs(epsg=epsg_metros)
        avisos.append(
            f"Capa en coordenadas geográficas: se reproyectó a "
            f"EPSG:{epsg_metros} para obtener cotas en metros."
        )

    return CapaCargada(
        gdf=gdf, nombre=lectura.nombre, avisos=tuple(avisos), dominios=lectura.dominios
    )
