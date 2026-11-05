# ==============================================================================
# Archivo  : src/generador_croquis/controller/ayuda.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Controlador de la pestaña Ayuda: carga el
#          |            | manual en segundo plano la primera vez que se abre
#          |            | la pestaña y permite recargarlo.
# ==============================================================================
"""Controlador de la pestaña "Ayuda"."""

from __future__ import annotations

import logging
from typing import Protocol

from generador_croquis.config import URL_MANUAL
from generador_croquis.controller.acerca_de import EjecutorTareas
from generador_croquis.services.ayuda import ManualAyuda, ServicioAyuda

log = logging.getLogger(__name__)


class VistaAyuda(Protocol):
    def mostrar_cargando(self) -> None: ...

    def mostrar_manual(self, manual: ManualAyuda) -> None: ...

    def mostrar_error_carga(self, mensaje: str) -> None: ...

    def abrir_url(self, url: str) -> None: ...


class ControladorAyuda:
    def __init__(self, vista: VistaAyuda, servicio: ServicioAyuda, ejecutor: EjecutorTareas):
        self._vista = vista
        self._servicio = servicio
        self._ejecutor = ejecutor
        self.manual: ManualAyuda | None = None
        self._cargando = False

    def asegurar_cargado(self) -> None:
        """Carga el manual solo la primera vez (al abrir la pestaña)."""
        if self.manual is None and not self._cargando:
            self.recargar()

    def recargar(self) -> None:
        self._cargando = True
        self._vista.mostrar_cargando()
        self._ejecutor.ejecutar(
            lambda _r: self._servicio.obtener(), self._al_cargar, self._al_fallar
        )

    def abrir_en_github(self) -> None:
        self._vista.abrir_url(URL_MANUAL)

    def _al_cargar(self, manual: ManualAyuda) -> None:
        self._cargando = False
        self.manual = manual
        self._vista.mostrar_manual(manual)

    def _al_fallar(self, exc: Exception) -> None:
        self._cargando = False
        log.warning("No se pudo cargar el manual: %s", exc)
        self._vista.mostrar_error_carga(str(exc))
