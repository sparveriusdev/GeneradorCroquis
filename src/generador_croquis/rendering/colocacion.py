# ==============================================================================
# Archivo  : src/generador_croquis/rendering/colocacion.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
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

from matplotlib.axes import Axes
from matplotlib.backend_bases import RendererBase
from matplotlib.text import Text
from matplotlib.transforms import Bbox

from generador_croquis.domain.models import Lado
from generador_croquis.services.geometria import angulo, angulo_legible

FRACCIONES = (0.5, 0.35, 0.65, 0.2, 0.8)  # posiciones a lo largo del lado
HOLGURA_PX = 2.0  # espacio mínimo entre etiquetas


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

    def reservar(self, artista: Text) -> None:
        """Marca como ocupado el espacio de un texto ya dibujado (p. ej. la etiqueta del ID)."""
        self.ocupadas.append(artista.get_window_extent(self._renderer))

    def _caja(self, texto: Text) -> Bbox:
        return texto.get_window_extent(self._renderer).expanded(1.0, 1.0).padded(HOLGURA_PX)

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
