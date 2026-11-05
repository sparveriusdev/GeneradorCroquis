# ==============================================================================
# Archivo  : src/generador_croquis/rendering/coordenadas.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Formato de coordenadas con decimales
#          |            | automáticos según la separación entre marcas: en
#          |            | metros suele dar enteros (sin «.0000»); sin notación
#          |            | científica ni desplazamiento.
# ==============================================================================
"""Formato de las coordenadas de los ejes."""

from __future__ import annotations

from matplotlib.ticker import Formatter


def decimales_necesarios(paso: float, maximo: int) -> int:
    """Menor número de decimales que representa exactamente ``paso`` (hasta ``maximo``)."""
    for decimales in range(maximo + 1):
        if abs(round(paso, decimales) - paso) < 1e-6:  # tolera errores de coma flotante
            return decimales
    return maximo


class FormatoCoordenadas(Formatter):
    """Muestra solo los decimales que distinguen una marca de la siguiente.

    Con marcas cada 2 m: ``4811904``; cada 0,5 m: ``4811904.5``; cada 0,25 m: ``…904.25``.
    """

    def __init__(self, maximo_decimales: int = 4):
        self._maximo = maximo_decimales
        self.decimales = 0

    def set_locs(self, locs) -> None:
        super().set_locs(locs)
        valores = sorted(float(v) for v in locs)
        pasos = [b - a for a, b in zip(valores, valores[1:], strict=False) if b > a]
        self.decimales = decimales_necesarios(min(pasos), self._maximo) if pasos else 0

    def __call__(self, x: float, pos: int | None = None) -> str:
        return f"{x:.{self.decimales}f}"
