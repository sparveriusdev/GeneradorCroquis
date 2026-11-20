# ==============================================================================
# Archivo  : src/generador_croquis/services/servicio_croquis.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.3.0 | 2026-11-20 | Detecta el campo NPN al cargar (informalidades) e
#          |            | informa cuántos croquis tuvo la última figura.
#   v1.2.0 | 2026-11-06 | Sugiere el campo de uso al cargar la capa.
#   v1.1.0 | 2026-11-05 | generar_figura() recibe OpcionesAcotado e informa
#          |            | cuántas cotas no encontraron espacio libre.
#   v1.0.0 | 2026-11-05 | Creación. Fachada de casos de uso (cargar capa,
#          |            | construir croquis, exportar) que orquesta lector,
#          |            | servicios y renderizador inyectados.
# ==============================================================================
"""Casos de uso de la aplicación, independientes de la interfaz gráfica."""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING

from generador_croquis.config import Configuracion
from generador_croquis.data.fuentes import Selector
from generador_croquis.data.lector import LectorCapas
from generador_croquis.domain.exceptions import CroquisError
from generador_croquis.domain.models import (
    CapaCargada,
    Construccion,
    OpcionesAcotado,
    ResumenCapa,
    SeleccionCampos,
)
from generador_croquis.services.agrupacion import agrupar_construcciones
from generador_croquis.services.deteccion_campos import (
    detectar_campo_id,
    detectar_campo_npn,
    detectar_campo_pisos,
    detectar_campo_uso,
)
from generador_croquis.services.preparacion import preparar_capa

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from generador_croquis.rendering.renderizador import Renderizador


class ServicioCroquis:
    """Orquesta los pasos de negocio: leer → preparar → agrupar → dibujar."""

    def __init__(
        self, lector: LectorCapas, renderizador: Renderizador, config: Configuracion | None = None
    ):
        self._lector = lector
        self._renderizador = renderizador
        self._config = config or Configuracion()
        self.croquis_generados = 0  # de la última figura

    @property
    def config(self) -> Configuracion:
        return self._config

    def cargar(self, ruta: str | Path, selector: Selector) -> ResumenCapa:
        lectura = self._lector.leer(ruta, selector)
        capa = preparar_capa(lectura, self._config.epsg_metros)
        capa = dataclasses.replace(capa, campo_npn=detectar_campo_npn(capa.gdf))
        return ResumenCapa(
            capa=capa,
            campo_id_sugerido=detectar_campo_id(capa.campos),
            campo_pisos_sugerido=detectar_campo_pisos(capa.campos),
            campo_uso_sugerido=detectar_campo_uso(capa.campos),
        )

    def requiere_confirmacion(self, capa: CapaCargada, seleccion: SeleccionCampos) -> int | None:
        """Devuelve el número de construcciones si supera el umbral de aviso."""
        n = capa.contar_construcciones(seleccion.campo_id, seleccion.incluir_informales)
        return n if n > self._config.max_construcciones_aviso else None

    def construcciones(self, capa: CapaCargada, seleccion: SeleccionCampos) -> list[Construccion]:
        return agrupar_construcciones(capa, seleccion)

    def generar_figura(
        self,
        capa: CapaCargada,
        seleccion: SeleccionCampos,
        opciones: OpcionesAcotado | None = None,
    ) -> Figure:
        construcciones = self.construcciones(capa, seleccion)
        if not construcciones:  # p. ej. solo hay informalidades y no se pidió su croquis
            raise CroquisError(
                "No hay construcciones formales para dibujar.\n"
                "Marque «Croquis adicional de informalidades» para dibujar las informales."
            )
        figura = self._renderizador.renderizar(construcciones, opciones)
        self.croquis_generados = len(construcciones)
        return figura

    @property
    def cotas_sin_espacio(self) -> int:
        """Cotas de la última figura que no encontraron un espacio libre."""
        return int(getattr(self._renderizador, "cotas_sin_espacio", 0))

    def exportar(self, figura: Figure, ruta: str | Path) -> Path:
        ruta = Path(ruta)
        self._renderizador.exportar(figura, ruta)
        return ruta
