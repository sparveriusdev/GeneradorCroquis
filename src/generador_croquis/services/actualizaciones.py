# ==============================================================================
# Archivo  : src/generador_croquis/services/actualizaciones.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Consulta el último release de GitHub, lo
#          |            | compara con la versión instalada y elige el
#          |            | ejecutable de la plataforma actual para descargarlo.
# ==============================================================================
"""Comprobación y descarga de nuevas versiones publicadas en GitHub."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from generador_croquis import __version__
from generador_croquis.config import SUFIJOS_EJECUTABLE, URL_API_ULTIMO_RELEASE
from generador_croquis.data.http import Reportar, TransporteHttp
from generador_croquis.domain.exceptions import ActualizacionError
from generador_croquis.domain.models import Descarga, InfoRelease, ResultadoActualizacion
from generador_croquis.domain.version import Version


class ServicioActualizaciones:
    """Caso de uso: "¿hay una versión nueva? → descargarla"."""

    def __init__(
        self,
        transporte: TransporteHttp,
        version_actual: str = __version__,
        plataforma: str = sys.platform,
        url_api: str = URL_API_ULTIMO_RELEASE,
    ):
        self._transporte = transporte
        self._actual = Version.parse(version_actual)
        self._sufijo = SUFIJOS_EJECUTABLE.get(plataforma)
        self._url_api = url_api

    @property
    def version_actual(self) -> Version:
        return self._actual

    def consultar(self) -> ResultadoActualizacion:
        datos = self._transporte.obtener_json(self._url_api)
        return ResultadoActualizacion(actual=self._actual, ultimo=self._interpretar(datos))

    def descargar(
        self, release: InfoRelease, carpeta: Path, reportar: Reportar | None = None
    ) -> Path:
        if release.descarga is None:
            raise ActualizacionError(
                "No hay un ejecutable para este sistema en esa versión.\n"
                "Descárguelo manualmente desde la página del release."
            )
        destino = Path(carpeta) / release.descarga.nombre
        return self._transporte.descargar(release.descarga.url, destino, reportar)

    def _interpretar(self, datos: Any) -> InfoRelease:
        try:
            version = Version.parse(str(datos["tag_name"]))
            url_pagina = str(datos["html_url"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ActualizacionError("GitHub devolvió un release con formato inesperado.") from exc

        descarga = None
        if self._sufijo:
            for asset in datos.get("assets") or []:
                nombre = str(asset.get("name", ""))
                if nombre.endswith(self._sufijo):
                    descarga = Descarga(
                        nombre, str(asset["browser_download_url"]), int(asset.get("size") or 0)
                    )
                    break
        return InfoRelease(version, url_pagina, str(datos.get("body") or ""), descarga)
