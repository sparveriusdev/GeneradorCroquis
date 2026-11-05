# ==============================================================================
# Archivo  : src/generador_croquis/controller/acerca_de.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Controlador de la pestaña "Acerca de":
#          |            | comprueba la última versión en GitHub y descarga el
#          |            | ejecutable nuevo en segundo plano (EjecutorTareas
#          |            | inyectado, la interfaz no se congela).
# ==============================================================================
"""Controlador de la pestaña "Acerca de" y de las actualizaciones."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Protocol, TypeVar

from generador_croquis.config import URL_RELEASES, URL_REPOSITORIO
from generador_croquis.data.http import Reportar
from generador_croquis.domain.exceptions import CroquisError
from generador_croquis.domain.models import ResultadoActualizacion
from generador_croquis.services.actualizaciones import ServicioActualizaciones

log = logging.getLogger(__name__)
T = TypeVar("T")


class EjecutorTareas(Protocol):
    """Ejecuta trabajo lento fuera del hilo de la interfaz.

    Los callbacks ``al_terminar``, ``al_fallar`` y ``al_progresar`` deben
    invocarse en el hilo de la interfaz.
    """

    def ejecutar(
        self,
        tarea: Callable[[Reportar], T],
        al_terminar: Callable[[T], None],
        al_fallar: Callable[[Exception], None],
        al_progresar: Callable[[float], None] | None = None,
    ) -> None: ...


class VistaAcercaDe(Protocol):
    def mostrar_estado(self, texto: str) -> None: ...

    def ofrecer_descarga(self, version: str | None) -> None: ...

    def comprobando(self, activo: bool) -> None: ...

    def mostrar_progreso(self, fraccion: float | None) -> None: ...

    def pedir_carpeta(self) -> str | None: ...

    def abrir_url(self, url: str) -> None: ...

    def mostrar_error(self, titulo: str, mensaje: str) -> None: ...

    def mostrar_exito(self, titulo: str, mensaje: str) -> None: ...


class ControladorAcercaDe:
    def __init__(
        self, vista: VistaAcercaDe, servicio: ServicioActualizaciones, ejecutor: EjecutorTareas
    ):
        self._vista = vista
        self._servicio = servicio
        self._ejecutor = ejecutor
        self.resultado: ResultadoActualizacion | None = None

    def comprobar(self) -> None:
        self._vista.comprobando(True)
        self._vista.ofrecer_descarga(None)
        self._vista.mostrar_estado("Consultando GitHub...")
        self._ejecutor.ejecutar(
            lambda _reportar: self._servicio.consultar(),
            self._al_consultar,
            self._fallo("No se pudo comprobar la versión"),
        )

    def descargar(self) -> None:
        if self.resultado is None or not self.resultado.hay_nueva:
            return
        release = self.resultado.ultimo
        if release.descarga is None:
            self._vista.abrir_url(release.url_pagina)
            return
        carpeta = self._vista.pedir_carpeta()
        if not carpeta:
            return
        self._vista.comprobando(True)
        self._vista.mostrar_progreso(0.0)
        self._vista.mostrar_estado(f"Descargando {release.descarga.nombre}...")
        self._ejecutor.ejecutar(
            lambda reportar: self._servicio.descargar(release, Path(carpeta), reportar),
            self._al_descargar,
            self._fallo("No se pudo descargar la nueva versión"),
            self._vista.mostrar_progreso,
        )

    def abrir_repositorio(self) -> None:
        self._vista.abrir_url(URL_REPOSITORIO)

    def abrir_releases(self) -> None:
        url = self.resultado.ultimo.url_pagina if self.resultado else URL_RELEASES
        self._vista.abrir_url(url)

    # ── callbacks ────────────────────────────────────────────────────────────

    def _al_consultar(self, resultado: ResultadoActualizacion) -> None:
        self.resultado = resultado
        self._vista.comprobando(False)
        ultima = resultado.ultimo.version
        if resultado.hay_nueva:
            self._vista.mostrar_estado(
                f"Hay una nueva versión disponible: v{ultima} (instalada: v{resultado.actual})."
            )
            self._vista.ofrecer_descarga(str(ultima))
        else:
            self._vista.mostrar_estado(
                f"Tiene la última versión (v{resultado.actual}). Publicada en GitHub: v{ultima}."
            )

    def _reofrecer_descarga(self) -> None:
        if self.resultado and self.resultado.hay_nueva:
            self._vista.ofrecer_descarga(str(self.resultado.ultimo.version))

    def _al_descargar(self, ruta: Path) -> None:
        self._vista.comprobando(False)
        self._reofrecer_descarga()
        self._vista.mostrar_progreso(None)
        self._vista.mostrar_estado(f"Descarga completada: {ruta}")
        self._vista.mostrar_exito(
            "Descarga completada",
            f"La nueva versión se guardó en:\n{ruta}\n\n"
            "Cierre esta aplicación y ejecute el archivo descargado.",
        )

    def _fallo(self, contexto: str) -> Callable[[Exception], None]:
        def manejar(exc: Exception) -> None:
            self._vista.comprobando(False)
            self._reofrecer_descarga()
            self._vista.mostrar_progreso(None)
            if isinstance(exc, CroquisError):
                log.warning("%s: %s", contexto, exc)
            else:
                log.error("%s", contexto, exc_info=exc)
            self._vista.mostrar_estado(f"{contexto}.")
            self._vista.mostrar_error("Actualizaciones", f"{contexto}:\n\n{exc}")

        return manejar
