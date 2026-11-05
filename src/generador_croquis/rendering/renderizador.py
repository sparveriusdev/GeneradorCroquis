# ==============================================================================
# Archivo  : src/generador_croquis/rendering/renderizador.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
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

import math
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol
from weakref import WeakKeyDictionary

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from generador_croquis.config import ParametrosCotas, TemaCroquis
from generador_croquis.domain.models import Construccion
from generador_croquis.services.geometria import calcular_cotas, poligonos_de


class Renderizador(Protocol):
    """Contrato de cualquier motor de dibujo de croquis."""

    def renderizar(self, construcciones: Sequence[Construccion]) -> Figure: ...

    def exportar(self, figura: Figure, ruta: Path) -> None: ...


class RenderizadorMatplotlib:
    """Dibuja una cuadrícula con un croquis acotado por construcción."""

    def __init__(self, tema: TemaCroquis | None = None, cotas: ParametrosCotas | None = None):
        self._tema = tema or TemaCroquis()
        self._cotas = cotas or ParametrosCotas()
        self._tamanos: WeakKeyDictionary[Figure, tuple[float, ...]] = WeakKeyDictionary()

    # ── API pública ──────────────────────────────────────────────────────────

    def renderizar(self, construcciones: Sequence[Construccion]) -> Figure:
        if not construcciones:
            raise ValueError("No hay construcciones para dibujar.")
        t = self._tema
        n = len(construcciones)
        cols = max(1, math.ceil(math.sqrt(n)))
        filas = max(1, math.ceil(n / cols))
        lado = t.tamano_subplot_pulgadas

        fig = Figure(figsize=(max(12, cols * lado), max(8, filas * lado)), facecolor=t.fondo)
        fig.suptitle(t.titulo, fontsize=18, fontweight="bold", color=t.color_titulo, y=0.98)
        ejes = fig.subplots(filas, cols, squeeze=False).ravel()

        for ax, construccion in zip(ejes, construcciones, strict=False):
            self._dibujar_construccion(ax, construccion)
        for ax in ejes[n:]:
            ax.axis("off")

        # El motor "tight" recalcula márgenes en cada dibujo (p. ej. al redimensionar).
        fig.set_layout_engine("tight", rect=(0, 0.02, 1, 0.96))
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

    def _dibujar_construccion(self, ax: Axes, c: Construccion) -> None:
        t = self._tema
        if not c.partes:
            ax.axis("off")
            return
        for i, parte in enumerate(c.partes):
            self._dibujar_parte(
                ax,
                parte,
                t.paleta_relleno[i % len(t.paleta_relleno)],
                t.paleta_borde[i % len(t.paleta_borde)],
            )
        self._dibujar_etiqueta(ax, c)
        self._configurar_ejes(ax, c)

    def _dibujar_parte(self, ax: Axes, geom, color_relleno: str, color_borde: str) -> None:
        t = self._tema
        for poly in poligonos_de(geom):
            xs, ys = poly.exterior.xy
            ax.fill(xs, ys, alpha=t.alfa_relleno, color=color_relleno, zorder=1)
            ax.plot(xs, ys, color=color_borde, linewidth=t.ancho_borde, zorder=2)
            for hueco in poly.interiors:  # patios, vacíos interiores
                hx, hy = hueco.xy
                ax.plot(hx, hy, color=color_borde, linewidth=1.0, linestyle="--", zorder=2)
            ax.plot(xs[:-1], ys[:-1], "o", color=color_borde, markersize=t.tamano_vertice, zorder=4)
            for cota in calcular_cotas(poly, self._cotas):
                ax.annotate(
                    cota.texto,
                    xy=cota.posicion,
                    fontsize=t.tamano_fuente_cota,
                    fontweight="bold",
                    color=t.color_cota_texto,
                    ha="center",
                    va="center",
                    rotation=cota.rotacion,
                    rotation_mode="anchor",
                    bbox={
                        "boxstyle": "round,pad=0.12",
                        "facecolor": "white",
                        "edgecolor": t.color_cota_borde,
                        "alpha": 0.85,
                        "linewidth": 0.5,
                    },
                    zorder=5,
                )

    def _dibujar_etiqueta(self, ax: Axes, c: Construccion) -> None:
        t = self._tema
        punto = c.union.representative_point()  # siempre dentro de la figura
        texto = c.identificador + (f"\n{c.descripcion_pisos}" if c.pisos is not None else "")
        ax.text(
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
            zorder=6,
        )

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
        ax.text(
            0.5,
            -0.05,
            f"Área total: {c.area_total:.2f} m²  |  Perímetro total: {c.perimetro_total:.2f} m",
            ha="center",
            va="top",
            transform=ax.transAxes,
            fontsize=7,
            color=t.color_pie,
            style="italic",
        )

        ax.set_aspect("equal")
        ax.grid(True, alpha=0.2, linestyle="--")
        ax.tick_params(labelsize=6, colors=t.color_ejes)

        minx, miny, maxx, maxy = c.union.bounds
        mx = max((maxx - minx) * t.margen_relativo, t.margen_minimo)
        my = max((maxy - miny) * t.margen_relativo, t.margen_minimo)
        ax.set_xlim(minx - mx, maxx + mx)
        ax.set_ylim(miny - my, maxy + my)
