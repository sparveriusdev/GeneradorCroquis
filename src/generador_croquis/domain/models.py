# ==============================================================================
# Archivo  : src/generador_croquis/domain/models.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.1.0 | 2026-11-05 | Añade InfoRelease, Descarga y ResultadoActualizacion
#          |            | para la comprobación de nuevas versiones.
#   v1.0.0 | 2026-11-05 | Creación. Modelo de datos explícito (Cota,
#          |            | Construccion, CapaCargada, ResumenCapa,
#          |            | SeleccionCampos) que reemplaza los diccionarios y
#          |            | variables sueltas de generador_v1.py.
# ==============================================================================
"""Entidades del dominio. Inmutables y sin dependencias de interfaz gráfica."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from typing import TYPE_CHECKING

from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

from generador_croquis.domain.version import Version

if TYPE_CHECKING:
    import geopandas as gpd
    from shapely.geometry.base import BaseGeometry

Punto = tuple[float, float]


@dataclass(frozen=True)
class Cota:
    """Medida de un lado de un polígono, lista para ser dibujada."""

    longitud: float
    posicion: Punto
    rotacion: float

    @property
    def texto(self) -> str:
        return f"{self.longitud:.2f} m"


@dataclass(frozen=True)
class Construccion:
    """Una construcción: uno o más polígonos que comparten identificador."""

    identificador: str
    partes: tuple[Polygon | MultiPolygon, ...]
    pisos: int | None = None

    @property
    def num_partes(self) -> int:
        return len(self.partes)

    @property
    def area_total(self) -> float:
        return sum(p.area for p in self.partes)

    @property
    def perimetro_total(self) -> float:
        return sum(p.length for p in self.partes)

    @cached_property
    def union(self) -> BaseGeometry:
        return unary_union(list(self.partes))

    @property
    def descripcion_pisos(self) -> str | None:
        if self.pisos is None:
            return None
        return f"{self.pisos} piso{'s' if self.pisos != 1 else ''}"


@dataclass(frozen=True)
class SeleccionCampos:
    """Campos de la capa elegidos por el usuario para agrupar y leer pisos."""

    campo_id: str | None = None
    campo_pisos: str | None = None


@dataclass(frozen=True)
class CapaCargada:
    """Capa de polígonos lista para procesar (limpia y en unidades métricas)."""

    gdf: gpd.GeoDataFrame
    nombre: str
    avisos: tuple[str, ...] = field(default_factory=tuple)

    @property
    def campos(self) -> list[str]:
        geom = self.gdf.geometry.name
        return [c for c in self.gdf.columns if c != geom]

    @property
    def num_poligonos(self) -> int:
        return len(self.gdf)

    def contar_construcciones(self, campo_id: str | None) -> int:
        if campo_id and campo_id in self.gdf.columns:
            return int(self.gdf[campo_id].nunique(dropna=False))
        return self.num_poligonos


@dataclass(frozen=True)
class ResumenCapa:
    """Información descriptiva de una capa cargada y los campos sugeridos."""

    capa: CapaCargada
    campo_id_sugerido: str | None
    campo_pisos_sugerido: str | None

    def como_texto(self) -> str:
        capa = self.capa
        lineas = [
            f"Archivo: {capa.nombre}",
            f"Total de polígonos: {capa.num_poligonos}",
            f"CRS: {capa.gdf.crs}",
            f"Columnas: {', '.join(capa.campos)}",
            *capa.avisos,
        ]
        if self.campo_id_sugerido:
            n = capa.contar_construcciones(self.campo_id_sugerido)
            lineas.append(f"Construcciones únicas (por '{self.campo_id_sugerido}'): {n}")
        else:
            lineas.append(f"Construcciones: {capa.num_poligonos} (sin agrupar)")
        return "\n".join(lineas)


@dataclass(frozen=True)
class Descarga:
    """Archivo descargable de un release (ejecutable de una plataforma)."""

    nombre: str
    url: str
    tamano: int


@dataclass(frozen=True)
class InfoRelease:
    """Release publicado en GitHub."""

    version: Version
    url_pagina: str
    notas: str = ""
    descarga: Descarga | None = None


@dataclass(frozen=True)
class ResultadoActualizacion:
    """Resultado de comparar la versión instalada con el último release."""

    actual: Version
    ultimo: InfoRelease

    @property
    def hay_nueva(self) -> bool:
        return self.ultimo.version > self.actual
