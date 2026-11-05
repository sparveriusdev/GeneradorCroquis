# ==============================================================================
# Archivo  : src/generador_croquis/config.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Centraliza las constantes que estaban
#          |            | dispersas en generador_v1.py (EPSG, umbrales, paletas,
#          |            | candidatos de campos, rutas de log) en objetos
#          |            | inmutables.
# ==============================================================================
"""Configuración de la aplicación: un único lugar para constantes y parámetros."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# CRS proyectado de Colombia (MAGNA-SIRGAS Origen Nacional, en metros).
EPSG_METROS: int = 9377

# Si hay más construcciones que esto, se pide confirmación antes de dibujar.
MAX_CONSTRUCCIONES_AVISO: int = 30

# Texto usado en los combos para indicar "sin campo".
OPCION_NINGUNO: str = "(ninguno)"

# Identificador que se asigna a los polígonos con ID vacío.
ID_VACIO: str = "SIN_ID"

DIRECTORIO_USUARIO: Path = Path.home() / ".generador_croquis"
ARCHIVO_LOG: Path = DIRECTORIO_USUARIO / "croquis.log"

CANDIDATOS_CAMPO_ID: tuple[str, ...] = (
    "id",
    "cod",
    "codigo",
    "code",
    "identificador",
    "id_const",
    "id_construccion",
    "construccion",
    "predio",
    "id_predio",
    "lote",
    "id_lote",
    "manzana",
    "ficha",
    "npn",
    "matricula",
    "objectid",
    "fid",
    "gid",
    "num",
    "numero",
)

CANDIDATOS_CAMPO_PISOS: tuple[str, ...] = (
    "pisos",
    "piso",
    "niveles",
    "nivel",
    "floors",
    "floor",
    "num_pisos",
    "n_pisos",
    "nro_pisos",
    "numero_pisos",
    "plantas",
    "planta",
    "npisos",
    "npiso",
    "altura",
)

FORMATOS_EXPORTACION: tuple[tuple[str, str], ...] = (
    ("PNG", "*.png"),
    ("JPEG", "*.jpg"),
    ("PDF", "*.pdf"),
    ("SVG", "*.svg"),
)


@dataclass(frozen=True)
class ParametrosCotas:
    """Parámetros geométricos para el cálculo de cotas."""

    desplazamiento_relativo: float = 0.15
    longitud_minima: float = 0.01


@dataclass(frozen=True)
class TemaCroquis:
    """Parámetros visuales del croquis (colores, tamaños, resolución)."""

    paleta_relleno: tuple[str, ...] = (
        "#3498db",
        "#2ecc71",
        "#e67e22",
        "#9b59b6",
        "#1abc9c",
        "#e74c3c",
        "#f39c12",
        "#34495e",
    )
    paleta_borde: tuple[str, ...] = (
        "#2c3e50",
        "#27ae60",
        "#d35400",
        "#8e44ad",
        "#16a085",
        "#c0392b",
        "#f1c40f",
        "#2c3e50",
    )
    fondo: str = "#FAFAFA"
    titulo: str = "CROQUIS DE CONSTRUCCIONES"
    color_titulo: str = "#1a1a2e"
    color_subtitulo: str = "#2c3e50"
    color_pie: str = "#7f8c8d"
    color_ejes: str = "#95a5a6"
    color_cota_texto: str = "#c0392b"
    color_cota_borde: str = "#e74c3c"
    color_etiqueta_fondo: str = "#f39c12"
    color_etiqueta_borde: str = "#e67e22"
    alfa_relleno: float = 0.20
    ancho_borde: float = 1.8
    tamano_vertice: float = 3.5
    tamano_fuente_cota: float = 6.5
    tamano_subplot_pulgadas: float = 6.0
    margen_relativo: float = 0.3
    margen_minimo: float = 0.5
    dpi_exportacion: int = 300


@dataclass(frozen=True)
class Configuracion:
    """Agrupa toda la configuración inyectable de la aplicación."""

    epsg_metros: int = EPSG_METROS
    max_construcciones_aviso: int = MAX_CONSTRUCCIONES_AVISO
    cotas: ParametrosCotas = field(default_factory=ParametrosCotas)
    tema: TemaCroquis = field(default_factory=TemaCroquis)
