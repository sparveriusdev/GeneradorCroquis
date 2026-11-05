# ==============================================================================
# Archivo  : src/generador_croquis/services/ayuda.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Obtiene el manual de uso desde GitHub
#          |            | (versión más reciente) y, sin conexión, usa la copia
#          |            | incluida en la aplicación.
# ==============================================================================
"""Caso de uso: obtener el manual de uso para la pestaña de Ayuda."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from generador_croquis.config import URL_DOCS_RAW, URL_MANUAL_RAW, directorio_docs
from generador_croquis.data.http import TransporteHttp
from generador_croquis.domain.exceptions import ActualizacionError
from generador_croquis.services.markdown import Documento, parsear

log = logging.getLogger(__name__)

NOMBRE_MANUAL = "MANUAL_DE_USO.md"


@dataclass(frozen=True)
class ManualAyuda:
    """Manual listo para mostrar."""

    documento: Documento
    desde_github: bool
    directorio_local: Path | None  # para resolver imágenes relativas
    url_base: str

    def ruta_imagen(self, relativa: str) -> Path | None:
        if self.directorio_local is None:
            return None
        ruta = (self.directorio_local / relativa).resolve()
        return ruta if ruta.is_file() else None


class ServicioAyuda:
    def __init__(
        self,
        transporte: TransporteHttp,
        url: str = URL_MANUAL_RAW,
        directorio_local: Path | None = None,
        url_base: str = URL_DOCS_RAW,
    ):
        self._transporte = transporte
        self._url = url
        self._local = directorio_local if directorio_local is not None else directorio_docs()
        self._url_base = url_base

    def obtener(self) -> ManualAyuda:
        try:
            texto = self._transporte.obtener_texto(self._url)
            return ManualAyuda(parsear(texto), True, self._local, self._url_base)
        except ActualizacionError as exc:
            log.info("Manual no disponible en GitHub (%s); se usa la copia local", exc)
        if self._local is None:
            raise ActualizacionError(
                "No se pudo descargar el manual de GitHub y esta instalación no incluye "
                "una copia local."
            )
        texto = (self._local / NOMBRE_MANUAL).read_text(encoding="utf-8")
        return ManualAyuda(parsear(texto), False, self._local, self._url_base)
