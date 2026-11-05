# ==============================================================================
# Archivo  : src/generador_croquis/data/fuentes.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Patrón Strategy para fuentes de datos
#          |            | (Shapefile, GDB, ZIP). Reemplaza el if/elif de
#          |            | cargar_archivo() de generador_v1.py. Mejoras: el ZIP
#          |            | se extrae en un directorio temporal que se borra al
#          |            | terminar la lectura, se valida .shx/.dbf, se protege
#          |            | contra rutas maliciosas (zip-slip) y la selección
#          |            | de capa/archivo se delega a un Selector inyectado.
# ==============================================================================
"""Fuentes de datos vectoriales soportadas.

Cada fuente implementa el protocolo :class:`FuenteDatos`. Para soportar un
formato nuevo basta con crear otra clase y registrarla en el
:class:`~generador_croquis.data.lector.LectorCapas` (principio abierto/cerrado).
"""

from __future__ import annotations

import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import geopandas as gpd
import pyogrio

from generador_croquis.domain.exceptions import (
    ArchivoInvalidoError,
    OperacionCanceladaError,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


class Selector(Protocol):
    """Pide al usuario elegir una opción. Devuelve None si cancela."""

    def __call__(self, titulo: str, mensaje: str, opciones: Sequence[str]) -> str | None: ...


@dataclass(frozen=True)
class LecturaFuente:
    """Resultado crudo de leer una fuente: el GeoDataFrame y un nombre legible."""

    gdf: gpd.GeoDataFrame
    nombre: str


class FuenteDatos(Protocol):
    """Contrato que debe cumplir cualquier fuente de datos."""

    def puede_abrir(self, ruta: Path) -> bool: ...

    def leer(self, ruta: Path, selector: Selector) -> LecturaFuente: ...


# ── utilidades compartidas (DRY) ────────────────────────────────────────────


def leer_capa(ruta: Path, capa: str | None = None) -> gpd.GeoDataFrame:
    """Lee una capa vectorial con el motor pyogrio."""
    try:
        return gpd.read_file(ruta, layer=capa, engine="pyogrio")
    except Exception as exc:  # pyogrio lanza varios tipos según el driver
        raise ArchivoInvalidoError(f"No se pudo leer '{ruta.name}': {exc}") from exc


def elegir(selector: Selector, titulo: str, mensaje: str, opciones: Sequence[str]) -> str:
    """Resuelve una elección: automática si hay una sola opción, si no pregunta."""
    if not opciones:
        raise ArchivoInvalidoError(f"No hay opciones disponibles: {titulo.lower()}.")
    if len(opciones) == 1:
        return opciones[0]
    elegido = selector(titulo, mensaje, list(opciones))
    if elegido is None:
        raise OperacionCanceladaError("Operación cancelada.")
    return elegido


def validar_shapefile(ruta_shp: Path) -> str | None:
    """Devuelve una descripción del problema si faltan archivos compañeros."""
    faltantes = [
        ext
        for ext in (".shx", ".dbf")
        if not any(p.suffix.lower() == ext for p in ruta_shp.parent.glob(f"{ruta_shp.stem}.*"))
    ]
    return f"{ruta_shp.name} (falta {', '.join(faltantes)})" if faltantes else None


# ── estrategias ─────────────────────────────────────────────────────────────


class FuenteShapefile:
    """Shapefile suelto (.shp con sus archivos compañeros)."""

    def puede_abrir(self, ruta: Path) -> bool:
        return ruta.is_file() and ruta.suffix.lower() == ".shp"

    def leer(self, ruta: Path, selector: Selector) -> LecturaFuente:
        problema = validar_shapefile(ruta)
        if problema:
            raise ArchivoInvalidoError(f"Shapefile incompleto: {problema}")
        return LecturaFuente(leer_capa(ruta), ruta.name)


class FuenteGdb:
    """Carpeta File Geodatabase (normalmente con extensión .gdb)."""

    def puede_abrir(self, ruta: Path) -> bool:
        return ruta.is_dir()

    def leer(self, ruta: Path, selector: Selector) -> LecturaFuente:
        capa = elegir(
            selector, "Seleccionar capa", "Seleccione la capa a utilizar:", self.listar_capas(ruta)
        )
        return LecturaFuente(leer_capa(ruta, capa), f"{ruta.name} > {capa}")

    @staticmethod
    def listar_capas(ruta: Path) -> list[str]:
        try:
            return [str(c[0]) for c in pyogrio.list_layers(ruta)]
        except Exception as exc:
            raise ArchivoInvalidoError(
                f"No se pudo leer el GDB: {exc}\n\n"
                "Verifique que sea una File Geodatabase (.gdb) válida y completa."
            ) from exc


class FuenteZip:
    """Archivo .zip que contiene shapefiles y/o File Geodatabases.

    Delega la lectura real en :class:`FuenteGdb` y :class:`FuenteShapefile`.
    """

    def __init__(self, gdb: FuenteGdb | None = None, shp: FuenteShapefile | None = None):
        self._gdb = gdb or FuenteGdb()
        self._shp = shp or FuenteShapefile()

    def puede_abrir(self, ruta: Path) -> bool:
        return ruta.is_file() and ruta.suffix.lower() == ".zip"

    def leer(self, ruta: Path, selector: Selector) -> LecturaFuente:
        # Los datos quedan en memoria tras la lectura: el temporal se borra al salir.
        with tempfile.TemporaryDirectory(prefix="croquis_") as tmp:
            destino = Path(tmp)
            self._extraer(ruta, destino)
            gdbs, shps, incompletos = self._buscar_contenido(destino)

            if not gdbs and not shps:
                detalle = (
                    f"\nShapefiles incompletos: {', '.join(incompletos)}" if incompletos else ""
                )
                raise ArchivoInvalidoError(
                    "No se encontró ningún .shp ni .gdb válido dentro del .zip." + detalle
                )

            opciones = {str(p.relative_to(destino)): p for p in (*gdbs, *shps)}
            elegido = elegir(
                selector,
                "Seleccionar contenido",
                "El .zip contiene varios conjuntos de datos.\nSeleccione uno:",
                list(opciones),
            )
            ruta_interna = opciones[elegido]
            fuente = self._gdb if ruta_interna in gdbs else self._shp
            lectura = fuente.leer(ruta_interna, selector)
            nombre_interno = lectura.nombre.replace(ruta_interna.name, elegido, 1)
            return LecturaFuente(lectura.gdf, f"{ruta.name} > {nombre_interno}")

    @staticmethod
    def _extraer(ruta: Path, destino: Path) -> None:
        try:
            with zipfile.ZipFile(ruta) as zf:
                raiz = destino.resolve()
                for miembro in zf.namelist():
                    if not (destino / miembro).resolve().is_relative_to(raiz):
                        raise ArchivoInvalidoError(f"Ruta insegura dentro del .zip: {miembro}")
                zf.extractall(destino)
        except zipfile.BadZipFile as exc:
            raise ArchivoInvalidoError("El archivo seleccionado no es un .zip válido.") from exc

    @staticmethod
    def _buscar_contenido(raiz: Path) -> tuple[list[Path], list[Path], list[str]]:
        def ignorado(p: Path) -> bool:
            return "__MACOSX" in p.parts or p.name.startswith("._")

        gdbs = sorted(
            p
            for p in raiz.rglob("*")
            if p.is_dir() and p.suffix.lower() == ".gdb" and not ignorado(p)
        )
        shps, incompletos = [], []
        for shp in sorted(raiz.rglob("*")):
            if not shp.is_file() or shp.suffix.lower() != ".shp" or ignorado(shp):
                continue
            if any(g in shp.parents for g in gdbs):
                continue
            problema = validar_shapefile(shp)
            if problema:
                incompletos.append(problema)
            else:
                shps.append(shp)
        return gdbs, shps, incompletos
