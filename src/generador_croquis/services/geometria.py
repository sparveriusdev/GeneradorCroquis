# ==============================================================================
# Archivo  : src/generador_croquis/services/geometria.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v2.0.0 | 2026-11-05 | Acotado por vértices principales: Douglas-Peucker
#          |            | sobre el anillo cerrado, empezando en la esquina más
#          |            | marcada; los vértices de ajuste se agrupan en un solo
#          |            | lado cuya medida es la suma de sus tramos.
#          |            | calcular_lados() reemplaza a calcular_cotas(): la
#          |            | posición de la etiqueta pasa al renderizador. La
#          |            | normal exterior se obtiene de la orientación del
#          |            | anillo (antes del centroide, fallaba en polígonos
#          |            | cóncavos).
#   v1.0.0 | 2026-11-05 | Creación. Cálculo puro de cotas separado del dibujo
#          |            | (antes mezclado en dibujar_poligono_con_cotas). Ahora
#          |            | es testeable sin matplotlib.
# ==============================================================================
"""Funciones geométricas puras (sin dependencias de dibujo)."""

from __future__ import annotations

import math
from collections.abc import Sequence

from shapely.geometry import MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.geometry.polygon import orient

from generador_croquis.config import ParametrosCotas
from generador_croquis.domain.models import Lado, OpcionesAcotado, Punto


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


# ── vértices principales ────────────────────────────────────────────────────


def giro(anterior: Punto, vertice: Punto, siguiente: Punto) -> float:
    """Cambio de dirección en el vértice, en grados (0 = sigue recto)."""
    diferencia = angulo(vertice, siguiente) - angulo(anterior, vertice)
    return abs((diferencia + 180) % 360 - 180)


def distancia_a_segmento(p: Punto, a: Punto, b: Punto) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    largo2 = dx * dx + dy * dy
    if largo2 == 0:
        return longitud(p, a)
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / largo2))
    return longitud(p, (a[0] + t * dx, a[1] + t * dy))


def _douglas_peucker(
    puntos: Sequence[Punto], i: int, j: int, tolerancia: float, conservados: set[int]
) -> None:
    """Marca en ``conservados`` los puntos entre i y j que se apartan más que la tolerancia."""
    if j <= i + 1:
        return
    distancias = [
        (distancia_a_segmento(puntos[k], puntos[i], puntos[j]), k) for k in range(i + 1, j)
    ]
    maxima, k = max(distancias)
    if maxima > tolerancia:
        conservados.add(k)
        _douglas_peucker(puntos, i, k, tolerancia, conservados)
        _douglas_peucker(puntos, k, j, tolerancia, conservados)


def indices_principales(anillo: Sequence[Punto], tolerancia: float) -> list[int]:
    """Índices (ordenados) de los vértices principales de un anillo sin repetir el cierre.

    Un vértice es *de ajuste* si se aparta menos de ``tolerancia`` de la recta que une
    los vértices principales vecinos. Se parte de la esquina más marcada para que el
    punto inicial del anillo nunca sea un vértice de ajuste. Siempre quedan al menos 3.
    """
    n = len(anillo)
    if tolerancia <= 0 or n <= 3:
        return list(range(n))
    giros = [giro(anillo[i - 1], anillo[i], anillo[(i + 1) % n]) for i in range(n)]
    inicio = max(range(n), key=giros.__getitem__)
    orden = [(inicio + k) % n for k in range(n)]
    cadena = [anillo[i] for i in orden] + [anillo[inicio]]  # anillo cerrado
    conservados = {0}
    _douglas_peucker(cadena, 0, n, tolerancia, conservados)
    if len(conservados) < 3:  # polígono casi degenerado: las 3 esquinas más marcadas
        conservados = {orden.index(i) for i in sorted(range(n), key=giros.__getitem__)[-3:]}
    return sorted(orden[k] for k in conservados)


def _anillo_limpio(poligono: Polygon) -> list[Punto]:
    """Exterior en sentido antihorario, sin el punto de cierre ni vértices repetidos."""
    coords = list(orient(poligono, sign=1.0).exterior.coords)[:-1]
    limpio = [p for i, p in enumerate(coords) if i == 0 or p != coords[i - 1]]
    while len(limpio) > 1 and limpio[0] == limpio[-1]:
        limpio.pop()
    return limpio


def calcular_lados(
    poligono: Polygon,
    opciones: OpcionesAcotado | None = None,
    parametros: ParametrosCotas | None = None,
) -> list[Lado]:
    """Lados acotables del anillo exterior según las opciones de acotado."""
    opciones = opciones or OpcionesAcotado()
    parametros = parametros or ParametrosCotas()
    anillo = _anillo_limpio(poligono)
    n = len(anillo)
    if n < 3:
        return []
    tolerancia = opciones.tolerancia if opciones.solo_principales else 0.0
    indices = indices_principales(anillo, tolerancia)

    lados: list[Lado] = []
    for a, b in zip(indices, indices[1:] + indices[:1], strict=True):
        pasos = (b - a) % n or n
        tramo = [anillo[(a + k) % n] for k in range(pasos + 1)]
        recorrido = sum(longitud(p, q) for p, q in zip(tramo, tramo[1:], strict=False))
        inicio, fin = anillo[a], anillo[b]
        cuerda = longitud(inicio, fin)
        if cuerda < parametros.longitud_minima:
            continue
        # Anillo antihorario: la normal exterior es la dirección girada -90°.
        normal = ((fin[1] - inicio[1]) / cuerda, -(fin[0] - inicio[0]) / cuerda)
        lados.append(Lado(inicio, fin, recorrido, normal, pasos - 1))
    return lados
