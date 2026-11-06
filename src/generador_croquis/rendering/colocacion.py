# ==============================================================================
# Archivo  : src/generador_croquis/rendering/colocacion.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.2.0 | 2026-11-06 | colocar_fuera() busca en una rejilla sobre todo el
#          |            | croquis (no solo alrededor de su caja): cabe en
#          |            | croquis pequeños o con leyenda ancha y puede usar
#          |            | huecos como la muesca de una L, sin entrar en patios.
#   v1.1.0 | 2026-11-06 | colocar_fuera(): lleva la etiqueta del ID fuera del
#          |            | polígono, al hueco libre con la línea guía más corta
#          |            | y sin cruzar cotas; la línea termina en el punto
#          |            | interior más cercano. Si no hay hueco, se queda
#          |            | adentro. Mide solo el texto de una anotación (no su
#          |            | línea guía). Se quita reservar() (sin uso).
#   v1.0.0 | 2026-11-05 | Creación. Colocación de cotas sin solapes: prueba
#          |            | posiciones candidatas (afuera primero, a lo largo
#          |            | del lado y cada vez más lejos; adentro al final),
#          |            | mide cada etiqueta en píxeles y elige la primera
#          |            | libre. Si se aleja de su lado dibuja una línea guía.
# ==============================================================================
"""Colocación de etiquetas de cota sin solapes."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import shapely
from matplotlib.axes import Axes
from matplotlib.backend_bases import RendererBase
from matplotlib.text import Annotation, Text
from matplotlib.transforms import Bbox
from shapely.geometry import LineString, Point, Polygon, box
from shapely.geometry.base import BaseGeometry
from shapely.ops import nearest_points, unary_union

from generador_croquis.domain.models import Lado
from generador_croquis.services.geometria import angulo, angulo_legible, poligonos_de

FRACCIONES = (0.5, 0.35, 0.65, 0.2, 0.8)  # posiciones a lo largo del lado
HOLGURA_PX = 2.0  # espacio mínimo entre etiquetas
MARGEN_ANCLA_PX = 6.0  # la línea guía termina este tanto dentro del polígono
DISTANCIA_MINIMA_PX = 10.0  # hueco mínimo entre la construcción y la etiqueta del ID
PASO_REJILLA_PX = 6.0  # separación de las posiciones que se prueban para la etiqueta del ID
PENALIZACION_CRUCE_PX = 400.0  # una línea guía que cruza una cota «cuesta» esto de largo


@dataclass
class Candidato:
    fraccion: float
    anillo: int  # 0 = pegado al lado; mayores = más lejos
    afuera: bool


def _candidatos(anillos: int) -> list[Candidato]:
    orden = [Candidato(f, k, True) for k in range(anillos) for f in FRACCIONES]
    return orden + [Candidato(f, k, False) for k in range(anillos) for f in FRACCIONES]


def _area_solape(a: Bbox, b: Bbox) -> float:
    ancho = min(a.x1, b.x1) - max(a.x0, b.x0)
    alto = min(a.y1, b.y1) - max(a.y0, b.y0)
    return max(ancho, 0) * max(alto, 0)


class ColocadorEtiquetas:
    """Coloca etiquetas en un Axes evitando que se toquen entre sí o salgan del área."""

    def __init__(
        self, ax: Axes, renderer: RendererBase, separacion_px: float = 3.0, anillos: int = 4
    ):
        self._ax = ax
        self._renderer = renderer
        self._separacion = separacion_px
        self._anillos = anillos
        self.ocupadas: list[Bbox] = []
        self.sin_espacio = 0

    def _caja(self, texto: Text) -> Bbox:
        # Text.get_window_extent: en una anotación mide solo el texto, sin la línea guía.
        caja = Text.get_window_extent(texto, self._renderer)
        recuadro = texto.get_bbox_patch()
        if recuadro is not None:  # el recuadro redondeado sobresale del texto
            relleno = recuadro.get_boxstyle().pad * texto.get_fontsize()
            caja = caja.padded(self._renderer.points_to_pixels(relleno))
        return caja.padded(HOLGURA_PX)

    def _libre(self, caja: Bbox) -> bool:
        area = self._ax.bbox
        dentro = (
            caja.x0 >= area.x0 and caja.x1 <= area.x1 and caja.y0 >= area.y0 and caja.y1 <= area.y1
        )
        return dentro and not any(caja.overlaps(o) for o in self.ocupadas)

    def colocar(self, lado: Lado, texto: Text) -> bool:
        """Mueve ``texto`` a la primera posición libre junto a ``lado``.

        Devuelve False si no hubo posición libre (queda en la de menor solape).
        """
        datos_a_px = self._ax.transData
        texto.set_rotation(angulo_legible(angulo(lado.inicio, lado.fin)))
        # Normal exterior en píxeles (el aspecto es 1:1, pero se transforma por rigor).
        medio = lado.punto(0.5)
        p0 = datos_a_px.transform(medio)
        p1 = datos_a_px.transform((medio[0] + lado.normal[0], medio[1] + lado.normal[1]))
        nx, ny = p1[0] - p0[0], p1[1] - p0[1]
        norma = math.hypot(nx, ny) or 1.0
        nx, ny = nx / norma, ny / norma

        texto.set_position(medio)
        alto = texto.get_window_extent(self._renderer)
        # Grosor de la etiqueta medido en la dirección de la normal.
        grosor = abs(nx) * alto.width + abs(ny) * alto.height
        mejor: tuple[float, tuple[float, float], Candidato] | None = None

        for cand in _candidatos(self._anillos):
            base = datos_a_px.transform(lado.punto(cand.fraccion))
            distancia = self._separacion + grosor / 2 + cand.anillo * (grosor + HOLGURA_PX)
            signo = 1 if cand.afuera else -1
            px = (base[0] + signo * nx * distancia, base[1] + signo * ny * distancia)
            posicion = tuple(datos_a_px.inverted().transform(px))
            texto.set_position(posicion)
            caja = self._caja(texto)
            if self._libre(caja):
                self._fijar(lado, texto, caja, cand, posicion)
                return True
            solape = sum(_area_solape(caja, o) for o in self.ocupadas)
            if mejor is None or solape < mejor[0]:
                mejor = (solape, posicion, cand)

        assert mejor is not None
        _, posicion, cand = mejor
        texto.set_position(posicion)
        self._fijar(lado, texto, self._caja(texto), cand, posicion)
        self.sin_espacio += 1
        return False

    def colocar_fuera(self, texto: Annotation, zona: BaseGeometry) -> bool:
        """Lleva la etiqueta ``texto`` fuera de la construcción ``zona`` (en datos).

        Recorre una rejilla de posiciones sobre todo el croquis y, entre las libres (dentro del
        área, sin tocar etiquetas ya colocadas ni la construcción, patios incluidos), elige la
        más cercana a la construcción cuya línea guía no cruce otras etiquetas. La línea
        termina en el punto de ``zona`` más cercano, un poco hacia adentro. Si no hay hueco, la
        deja donde estaba y devuelve False.
        """
        datos_a_px = self._ax.transData

        def a_px(geom: BaseGeometry) -> BaseGeometry:
            return shapely.transform(geom, datos_a_px.transform)  # recibe un arreglo N×2

        poligonos = poligonos_de(zona) or [zona.envelope]
        silueta = a_px(unary_union([Polygon(p.exterior) for p in poligonos]))
        prohibida = silueta.buffer(DISTANCIA_MINIMA_PX)
        shapely.prepare(prohibida)
        # Un poco hacia adentro para que la línea guía cruce el borde y no muera en él.
        interior = a_px(zona).buffer(-MARGEN_ANCLA_PX)
        if interior.is_empty:
            interior = a_px(zona.representative_point())

        medida = self._caja(texto)
        ancho, alto = medida.width, medida.height
        area = self._ax.bbox
        xs = np.arange(area.x0 + ancho / 2, area.x1 - ancho / 2, PASO_REJILLA_PX)
        ys = np.arange(area.y0 + alto / 2, area.y1 - alto / 2, PASO_REJILLA_PX)
        cx, cy = (m.ravel() for m in np.meshgrid(xs, ys))
        x0, y0, x1, y1 = cx - ancho / 2, cy - alto / 2, cx + ancho / 2, cy + alto / 2
        # Libres de las etiquetas ya colocadas (mismo criterio que _libre, en lote).
        libre = np.ones(cx.shape, dtype=bool)
        for o in self.ocupadas:
            libre &= (x1 < o.x0) | (x0 > o.x1) | (y1 < o.y0) | (y0 > o.y1)
        rectangulos = shapely.box(x0[libre], y0[libre], x1[libre], y1[libre])
        fuera = ~shapely.intersects(prohibida, rectangulos)
        rectangulos = rectangulos[fuera]
        centros = np.column_stack([cx[libre][fuera], cy[libre][fuera]])
        distancias = shapely.distance(rectangulos, interior)

        mejor: tuple[float, Bbox, Point] | None = None
        for k in np.argsort(distancias, kind="stable"):
            if mejor is not None and distancias[k] >= mejor[0]:
                break  # las siguientes están más lejos: no pueden mejorar
            centro = Point(centros[k])
            ancla = nearest_points(interior, centro)[0]
            guia = LineString([centro, ancla])
            cruces = sum(guia.intersects(box(o.x0, o.y0, o.x1, o.y1)) for o in self.ocupadas)
            puntaje = float(distancias[k]) + cruces * PENALIZACION_CRUCE_PX
            if mejor is None or puntaje < mejor[0]:
                caja = Bbox.from_bounds(centro.x - ancho / 2, centro.y - alto / 2, ancho, alto)
                mejor = (puntaje, caja, ancla)

        if mejor is None:
            texto.set_position(texto.xy)
            return False
        _, caja, ancla = mejor
        a_datos = datos_a_px.inverted()
        texto.set_position(tuple(a_datos.transform((caja.x0 + ancho / 2, caja.y0 + alto / 2))))
        texto.xy = tuple(a_datos.transform((ancla.x, ancla.y)))
        self.ocupadas.append(caja)
        return True

    def _fijar(
        self, lado: Lado, texto: Text, caja: Bbox, cand: Candidato, posicion: tuple[float, float]
    ) -> None:
        self.ocupadas.append(caja)
        if cand.anillo > 0:  # se alejó del lado: línea guía hasta él
            origen = lado.punto(cand.fraccion)
            (linea,) = self._ax.plot(
                [origen[0], posicion[0]],
                [origen[1], posicion[1]],
                color=texto.get_color(),
                linewidth=0.6,
                alpha=0.75,
                zorder=5,
            )
            linea.set_in_layout(False)
