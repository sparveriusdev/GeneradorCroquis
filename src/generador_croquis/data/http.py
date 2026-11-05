# ==============================================================================
# Archivo  : src/generador_croquis/data/http.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.1.0 | 2026-11-05 | Añade obtener_texto() (manual de ayuda desde GitHub).
#   v1.0.0 | 2026-11-05 | Creación. Transporte HTTP con la librería estándar
#          |            | (urllib) y certificados de certifi para que HTTPS
#          |            | funcione también dentro del ejecutable. Descarga a
#          |            | un archivo .part que solo se renombra al terminar.
# ==============================================================================
"""Acceso HTTP (consultas JSON y descarga de archivos)."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from generador_croquis import __version__
from generador_croquis.config import TIEMPO_ESPERA_RED
from generador_croquis.domain.exceptions import ActualizacionError

Reportar = Callable[[float], None]
"""Recibe el avance de una descarga como fracción entre 0 y 1."""

_TAMANO_BLOQUE = 64 * 1024


class TransporteHttp(Protocol):
    def obtener_json(self, url: str) -> Any: ...

    def obtener_texto(self, url: str) -> str: ...

    def descargar(self, url: str, destino: Path, reportar: Reportar | None = None) -> Path: ...


def _contexto_ssl() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:  # pragma: no cover - certifi es dependencia directa
        return ssl.create_default_context()


class TransporteUrllib:
    """Implementación de :class:`TransporteHttp` con urllib."""

    def __init__(self, tiempo_espera: float = TIEMPO_ESPERA_RED):
        self._tiempo_espera = tiempo_espera
        self._ssl = _contexto_ssl()
        self._cabeceras = {"User-Agent": f"GeneradorCroquis/{__version__}"}

    def _abrir(self, url: str, extra: dict[str, str] | None = None):
        peticion = urllib.request.Request(url, headers={**self._cabeceras, **(extra or {})})
        try:
            return urllib.request.urlopen(peticion, timeout=self._tiempo_espera, context=self._ssl)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise ActualizacionError("El recurso no existe en GitHub (404).") from exc
            if exc.code == 403:
                raise ActualizacionError(
                    "GitHub limitó temporalmente las consultas. Intente más tarde."
                ) from exc
            raise ActualizacionError(f"GitHub respondió con error {exc.code}.") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ActualizacionError(
                "No se pudo conectar con GitHub. Verifique su conexión a internet."
            ) from exc

    def obtener_json(self, url: str) -> Any:
        with self._abrir(url, {"Accept": "application/vnd.github+json"}) as respuesta:
            try:
                return json.load(respuesta)
            except ValueError as exc:
                raise ActualizacionError("Respuesta inválida de GitHub.") from exc

    def obtener_texto(self, url: str) -> str:
        with self._abrir(url) as respuesta:
            try:
                return respuesta.read().decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ActualizacionError("El documento recibido no es texto UTF-8.") from exc

    def descargar(self, url: str, destino: Path, reportar: Reportar | None = None) -> Path:
        temporal = destino.with_name(destino.name + ".part")
        try:
            with self._abrir(url) as respuesta, temporal.open("wb") as archivo:
                total = int(respuesta.headers.get("Content-Length") or 0)
                recibido = 0
                while bloque := respuesta.read(_TAMANO_BLOQUE):
                    archivo.write(bloque)
                    recibido += len(bloque)
                    if reportar and total:
                        reportar(min(recibido / total, 1.0))
            temporal.replace(destino)
        except OSError as exc:
            raise ActualizacionError(f"No se pudo guardar la descarga: {exc}") from exc
        finally:
            temporal.unlink(missing_ok=True)
        return destino
