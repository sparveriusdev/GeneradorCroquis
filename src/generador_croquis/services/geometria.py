# ==============================================================================
# Archivo  : src/generador_croquis/services/geometria.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Cálculo puro de cotas separado del dibujo
#          |            | (antes mezclado en dibujar_poligono_con_cotas). Ahora
#          |            | es testeable sin matplotlib.
# ==============================================================================
"""Funciones geométricas puras (sin dependencias de dibujo)."""

from __future__ import annotations

import math

from shapely.geometry import MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry

from generador_croquis.config import ParametrosCotas
from generador_croquis.domain.models import Cota, Punto


def longitud(p1: Punto, p2: Punto) -> float:
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def punto_medio(p1: Punto, p2: Punto) -> Punto:
    return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)


def angulo(p1: Punto, p2: Punto) -> float:
    """Ángulo del segmento en grados, en el rango (-180, 180]."""
    return math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))


def angulo_legible(grados: float) -> float:
    """Normaliza un ángulo a [-90, 90] para que el texto nunca quede al revés."""
    if grados > 90:
        return grados - 180
    if grados < -90:
        return grados + 180
    return grados


def poligonos_de(geom: BaseGeometry | None) -> list[Polygon]:
    """Descompone una geometría en sus polígonos no vacíos."""
    if isinstance(geom, Polygon):
        return [] if geom.is_empty else [geom]
    if isinstance(geom, MultiPolygon):
        return [p for p in geom.geoms if not p.is_empty]
    return []


def calcular_cotas(poligono: Polygon, parametros: ParametrosCotas | None = None) -> list[Cota]:
    """Calcula una cota por cada lado del anillo exterior, desplazada hacia afuera."""
    parametros = parametros or ParametrosCotas()
    coords = list(poligono.exterior.coords)
    centro = poligono.centroid
    cotas: list[Cota] = []

    for p1, p2 in zip(coords[:-1], coords[1:], strict=True):
        largo = longitud(p1, p2)
        if largo < parametros.longitud_minima:
            continue

        pm = punto_medio(p1, p2)
        nx, ny = -(p2[1] - p1[1]) / largo, (p2[0] - p1[0]) / largo
        # Orientar la normal hacia afuera del polígono.
        if nx * (pm[0] - centro.x) + ny * (pm[1] - centro.y) < 0:
            nx, ny = -nx, -ny

        desplazamiento = largo * parametros.desplazamiento_relativo
        cotas.append(
            Cota(
                longitud=largo,
                posicion=(pm[0] + nx * desplazamiento, pm[1] + ny * desplazamiento),
                rotacion=angulo_legible(angulo(p1, p2)),
            )
        )
    return cotas
