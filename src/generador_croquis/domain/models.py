# ==============================================================================
# Archivo  : src/generador_croquis/domain/models.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.3.1 | 2026-11-05 | ResumenCapa.filas() acepta el campo de agrupación
#          |            | elegido y abrevia la lista de columnas.
#   v1.3.0 | 2026-11-05 | Lado reemplaza a Cota: guarda extremos, longitud
#          |            | (suma de tramos), normal exterior y vértices
#          |            | intermedios; la posición de la etiqueta la decide
#          |            | el renderizador. Nuevo OpcionesAcotado (validado).
#   v1.2.0 | 2026-11-05 | ResumenCapa.filas() reemplaza a como_texto(): la
#          |            | vista presenta el resumen como tabla.
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

from generador_croquis.config import TOLERANCIA_MAXIMA, TOLERANCIA_PRINCIPALES
from generador_croquis.domain.exceptions import OpcionInvalidaError
from generador_croquis.domain.version import Version

if TYPE_CHECKING:
    import geopandas as gpd
    from shapely.geometry.base import BaseGeometry

Punto = tuple[float, float]


@dataclass(frozen=True)
class Lado:
    """Lado acotable de un polígono, entre dos vértices principales.

    ``longitud`` es la suma de los tramos del borde entre ``inicio`` y ``fin``
    (incluye los vértices intermedios), así la suma de los lados coincide con
    el perímetro. ``normal`` es el vector unitario que apunta hacia afuera.
    """

    inicio: Punto
    fin: Punto
    longitud: float
    normal: Punto
    intermedios: int = 0

    @property
    def texto(self) -> str:
        return f"{self.longitud:.2f} m"

    def punto(self, fraccion: float) -> Punto:
        """Punto sobre la recta inicio-fin (0 = inicio, 1 = fin)."""
        return (
            self.inicio[0] + (self.fin[0] - self.inicio[0]) * fraccion,
            self.inicio[1] + (self.fin[1] - self.inicio[1]) * fraccion,
        )

    def coincide_con(self, otro: Lado, tolerancia: float) -> bool:
        """Mismo segmento (en cualquier sentido) y misma medida mostrada."""
        if self.texto != otro.texto:
            return False

        def cerca(a: Punto, b: Punto) -> bool:
            return abs(a[0] - b[0]) <= tolerancia and abs(a[1] - b[1]) <= tolerancia

        return (cerca(self.inicio, otro.inicio) and cerca(self.fin, otro.fin)) or (
            cerca(self.inicio, otro.fin) and cerca(self.fin, otro.inicio)
        )


@dataclass(frozen=True)
class OpcionesAcotado:
    """Cómo acotar: todos los vértices o solo los principales."""

    solo_principales: bool = True
    tolerancia: float = TOLERANCIA_PRINCIPALES

    def __post_init__(self) -> None:
        if not 0 <= self.tolerancia <= TOLERANCIA_MAXIMA:
            raise OpcionInvalidaError(
                f"La tolerancia debe estar entre 0 y {TOLERANCIA_MAXIMA:g} m."
            )


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

    COLUMNAS_VISIBLES = 6

    @property
    def num_construcciones(self) -> int:
        return self.capa.contar_construcciones(self.campo_id_sugerido)

    def filas(
        self, campo_id: str | None = None, usar_sugerido: bool = True
    ) -> list[tuple[str, str]]:
        """Datos principales de la capa como pares (etiqueta, valor).

        Por defecto describe la agrupación sugerida; con ``usar_sugerido=False``,
        la del ``campo_id`` indicado (``None`` = un croquis por polígono).
        """
        capa = self.capa
        campo = self.campo_id_sugerido if usar_sugerido else campo_id
        if campo:
            construcciones = f"{capa.contar_construcciones(campo)} (agrupadas por «{campo}»)"
        else:
            construcciones = f"{capa.num_poligonos} (un croquis por polígono)"
        crs = capa.gdf.crs
        campos = capa.campos
        columnas = ", ".join(campos[: self.COLUMNAS_VISIBLES])
        if len(campos) > self.COLUMNAS_VISIBLES:
            columnas += f" y {len(campos) - self.COLUMNAS_VISIBLES} más"
        return [
            ("Archivo", capa.nombre),
            ("Polígonos", str(capa.num_poligonos)),
            ("Construcciones", construcciones),
            ("Sistema de coordenadas", crs.to_string() if crs is not None else "Sin definir"),
            (f"Columnas ({len(campos)})", columnas or "—"),
        ]


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
