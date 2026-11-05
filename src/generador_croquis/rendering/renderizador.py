# ==============================================================================
# Archivo  : src/generador_croquis/rendering/renderizador.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v2.1.0 | 2026-11-05 | Ejes con coordenadas completas a 4 decimales, sin
#          |            | notación científica ni desplazamiento (+4.81e6). El
#          |            | pie de área/perímetro pasa a ser la etiqueta del eje
#          |            | X para no chocar con las coordenadas.
#   v2.0.0 | 2026-11-05 | Acotado en dos fases: primero geometría y escala,
#          |            | luego cotas colocadas sin solapes (Colocador-
#          |            | Etiquetas) medidas en píxeles. Cada cota usa el
#          |            | color de su unidad; los lados comunes a varias
#          |            | unidades con la misma medida se acotan una vez.
#          |            | Vértices principales grandes e intermedios
#          |            | pequeños. Recibe OpcionesAcotado.
#   v1.0.0 | 2026-11-05 | Creación. Migrado desde generar_croquis() y
#          |            | dibujar_poligono_con_cotas(). Cambios: usa
#          |            | matplotlib.figure.Figure (sin pyplot ni estado
#          |            | global, funciona sin pantalla), estilos desde
#          |            | TemaCroquis, un método por responsabilidad y
#          |            | protocolo Renderizador para poder sustituirlo.
#          |            | La exportación conserva el tamaño original de la
#          |            | figura aunque la vista previa se redimensione.
# ==============================================================================
"""Renderizado de construcciones a figuras de matplotlib."""

from __future__ import annotations

import logging
import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from weakref import WeakKeyDictionary

from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.text import Text
from matplotlib.ticker import FormatStrFormatter, MaxNLocator

from generador_croquis.config import ParametrosCotas, TemaCroquis
from generador_croquis.domain.models import Construccion, Lado, OpcionesAcotado
from generador_croquis.rendering.colocacion import ColocadorEtiquetas
from generador_croquis.services.geometria import calcular_lados, poligonos_de

log = logging.getLogger(__name__)


class Renderizador(Protocol):
    """Contrato de cualquier motor de dibujo de croquis."""

    def renderizar(
        self, construcciones: Sequence[Construccion], opciones: OpcionesAcotado | None = None
    ) -> Figure: ...

    def exportar(self, figura: Figure, ruta: Path) -> None: ...


@dataclass
class _CotaPendiente:
    lado: Lado
    color: str


class RenderizadorMatplotlib:
    """Dibuja una cuadrícula con un croquis acotado por construcción."""

    def __init__(self, tema: TemaCroquis | None = None, cotas: ParametrosCotas | None = None):
        self._tema = tema or TemaCroquis()
        self._cotas = cotas or ParametrosCotas()
        self._tamanos: WeakKeyDictionary[Figure, tuple[float, ...]] = WeakKeyDictionary()
        self.cotas_sin_espacio = 0  # informe de la última figura

    # ── API pública ──────────────────────────────────────────────────────────

    def renderizar(
        self, construcciones: Sequence[Construccion], opciones: OpcionesAcotado | None = None
    ) -> Figure:
        if not construcciones:
            raise ValueError("No hay construcciones para dibujar.")
        opciones = opciones or OpcionesAcotado(tolerancia=self._cotas.tolerancia_principales)
        t = self._tema
        n = len(construcciones)
        cols = max(1, math.ceil(math.sqrt(n)))
        filas = max(1, math.ceil(n / cols))
        lado = t.tamano_subplot_pulgadas

        fig = Figure(figsize=(max(12, cols * lado), max(8, filas * lado)), facecolor=t.fondo)
        FigureCanvasAgg(fig)  # da un renderer para medir textos, aun sin ventana
        fig.suptitle(t.titulo, fontsize=18, fontweight="bold", color=t.color_titulo, y=0.98)
        ejes = fig.subplots(filas, cols, squeeze=False).ravel()
        # El motor "tight" recalcula márgenes en cada dibujo (p. ej. al redimensionar).
        fig.set_layout_engine("tight", rect=(0, 0.02, 1, 0.96))

        # Fase 1: geometría, etiqueta del ID y escala de cada croquis.
        pendientes: list[tuple[Axes, Text | None, list[_CotaPendiente]]] = []
        for ax, construccion in zip(ejes, construcciones, strict=False):
            pendientes.append((ax, *self._dibujar_construccion(ax, construccion, opciones)))
        for ax in ejes[n:]:
            ax.axis("off")

        # Fase 2: con la disposición definitiva, colocar las cotas sin solapes.
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        self.cotas_sin_espacio = 0
        for ax, etiqueta_id, cotas in pendientes:
            colocador = ColocadorEtiquetas(
                ax, renderer, self._cotas.separacion_px, self._cotas.anillos
            )
            if etiqueta_id is not None:
                colocador.reservar(etiqueta_id)
            for cota in cotas:
                colocador.colocar(cota.lado, self._crear_texto(ax, cota))
            self.cotas_sin_espacio += colocador.sin_espacio
        if self.cotas_sin_espacio:
            log.warning("%d cotas no encontraron un espacio libre", self.cotas_sin_espacio)

        self._tamanos[fig] = tuple(fig.get_size_inches())
        return fig

    def exportar(self, figura: Figure, ruta: Path) -> None:
        """Exporta siempre con el tamaño original, aunque la vista previa lo haya cambiado."""
        actual = tuple(figura.get_size_inches())
        figura.set_size_inches(self._tamanos.get(figura, actual), forward=False)
        try:
            figura.savefig(
                ruta,
                dpi=self._tema.dpi_exportacion,
                bbox_inches="tight",
                facecolor=self._tema.fondo,
                edgecolor="none",
            )
        finally:
            figura.set_size_inches(actual, forward=False)

    # ── piezas internas ──────────────────────────────────────────────────────

    def _dibujar_construccion(
        self, ax: Axes, c: Construccion, opciones: OpcionesAcotado
    ) -> tuple[Text | None, list[_CotaPendiente]]:
        t = self._tema
        if not c.partes:
            ax.axis("off")
            return None, []
        cotas: list[_CotaPendiente] = []
        for i, parte in enumerate(c.partes):
            borde = t.paleta_borde[i % len(t.paleta_borde)]
            relleno = t.paleta_relleno[i % len(t.paleta_relleno)]
            for lado in self._dibujar_parte(ax, parte, relleno, borde, opciones):
                comun = any(
                    lado.coincide_con(otra.lado, self._cotas.tolerancia_lado_comun)
                    for otra in cotas
                )
                if not comun:  # lado compartido con la misma medida: se acota una sola vez
                    cotas.append(_CotaPendiente(lado, borde))
        etiqueta = self._dibujar_etiqueta(ax, c)
        self._configurar_ejes(ax, c)
        return etiqueta, cotas

    def _dibujar_parte(
        self, ax: Axes, geom, color_relleno: str, color_borde: str, opciones: OpcionesAcotado
    ) -> list[Lado]:
        t = self._tema
        lados: list[Lado] = []
        for poly in poligonos_de(geom):
            xs, ys = poly.exterior.xy
            ax.fill(xs, ys, alpha=t.alfa_relleno, color=color_relleno, zorder=1)
            ax.plot(xs, ys, color=color_borde, linewidth=t.ancho_borde, zorder=2)
            for hueco in poly.interiors:  # patios, vacíos interiores
                hx, hy = hueco.xy
                ax.plot(hx, hy, color=color_borde, linewidth=1.0, linestyle="--", zorder=2)
            lados_poly = calcular_lados(poly, opciones, self._cotas)
            ax.plot(
                xs[:-1],
                ys[:-1],
                "o",
                color=color_borde,
                alpha=0.6,
                markersize=t.tamano_vertice_intermedio,
                zorder=3,
            )
            principales = [lado.inicio for lado in lados_poly]
            if principales:
                px, py = zip(*principales, strict=True)
                ax.plot(px, py, "o", color=color_borde, markersize=t.tamano_vertice, zorder=4)
            lados.extend(lados_poly)
        return lados

    def _crear_texto(self, ax: Axes, cota: _CotaPendiente) -> Text:
        texto = ax.text(
            *cota.lado.punto(0.5),
            cota.lado.texto,
            fontsize=self._tema.tamano_fuente_cota,
            fontweight="bold",
            color=cota.color,
            ha="center",
            va="center",
            rotation_mode="anchor",
            bbox={
                "boxstyle": "round,pad=0.15",
                "facecolor": "white",
                "edgecolor": cota.color,
                "alpha": 0.92,
                "linewidth": 0.6,
            },
            zorder=6,
            gid="cota",
        )
        texto.set_in_layout(False)  # no debe alterar los márgenes ya calculados
        return texto

    def _dibujar_etiqueta(self, ax: Axes, c: Construccion) -> Text:
        t = self._tema
        punto = c.union.representative_point()  # siempre dentro de la figura
        texto = c.identificador + (f"\n{c.descripcion_pisos}" if c.pisos is not None else "")
        etiqueta = ax.text(
            punto.x,
            punto.y,
            texto,
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color=t.color_titulo,
            bbox={
                "boxstyle": "round,pad=0.3",
                "facecolor": t.color_etiqueta_fondo,
                "edgecolor": t.color_etiqueta_borde,
                "alpha": 0.85,
                "linewidth": 1,
            },
            zorder=7,
        )
        etiqueta.set_in_layout(False)
        return etiqueta

    def _configurar_ejes(self, ax: Axes, c: Construccion) -> None:
        t = self._tema
        titulo = [f"Construcción: {c.identificador}"]
        if c.pisos is not None:
            titulo.append(c.descripcion_pisos)
        if c.num_partes > 1:
            titulo.append(f"{c.num_partes} partes")
        ax.set_title(
            "  |  ".join(titulo), fontsize=9, fontweight="bold", color=t.color_subtitulo, pad=8
        )
        # El pie va como etiqueta del eje X: el ajuste automático lo deja bajo las coordenadas.
        ax.set_xlabel(
            f"Área total: {c.area_total:.2f} m²  |  Perímetro total: {c.perimetro_total:.2f} m",
            fontsize=7,
            color=t.color_pie,
            style="italic",
            labelpad=6,
        )

        ax.set_aspect("equal")
        ax.grid(True, alpha=0.2, linestyle="--")
        ax.tick_params(labelsize=6, colors=t.color_ejes)
        # Coordenadas completas, sin notación científica ni desplazamiento (+4.81e6).
        formato = FormatStrFormatter(f"%.{t.decimales_coordenadas}f")
        for eje in (ax.xaxis, ax.yaxis):
            eje.set_major_formatter(formato)
            eje.set_major_locator(MaxNLocator(nbins=t.marcas_eje))
        ax.tick_params(axis="x", labelrotation=30)

        minx, miny, maxx, maxy = c.union.bounds
        mx = max((maxx - minx) * t.margen_relativo, t.margen_minimo)
        my = max((maxy - miny) * t.margen_relativo, t.margen_minimo)
        ax.set_xlim(minx - mx, maxx + mx)
        ax.set_ylim(miny - my, maxy + my)
