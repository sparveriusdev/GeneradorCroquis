# ==============================================================================
# Archivo  : src/generador_croquis/config.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.4.1 | 2026-11-05 | Decimales y número de marcas de los ejes.
#   v1.4.0 | 2026-11-05 | ParametrosCotas: tolerancia de vértices principales
#          |            | (0,15 m), lado común y colocación sin solapes.
#          |            | Paleta de bordes legible (las cotas usan el color
#          |            | de su unidad); se eliminan color_cota_*.
#   v1.3.0 | 2026-11-05 | URL del manual en bruto (pestaña Ayuda), rutas de
#          |            | recursos (documentación local) y del logo.
#   v1.2.0 | 2026-11-05 | Añade LICENCIA (GPL-3.0) y URL del manual de uso.
#   v1.1.0 | 2026-11-05 | Añade repositorio de GitHub, URLs, tiempo de espera
#          |            | de red, nombres de ejecutables por plataforma y
#          |            | créditos de autoría.
#   v1.0.0 | 2026-11-05 | Creación. Centraliza las constantes que estaban
#          |            | dispersas en generador_v1.py (EPSG, umbrales, paletas,
#          |            | candidatos de campos, rutas de log) en objetos
#          |            | inmutables.
# ==============================================================================
"""Configuración de la aplicación: un único lugar para constantes y parámetros."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

# CRS proyectado de Colombia (MAGNA-SIRGAS Origen Nacional, en metros).
EPSG_METROS: int = 9377

# Si hay más construcciones que esto, se pide confirmación antes de dibujar.
MAX_CONSTRUCCIONES_AVISO: int = 30

# Distancia (m) por debajo de la cual un vértice se considera de ajuste y no se acota.
TOLERANCIA_PRINCIPALES: float = 0.15
TOLERANCIA_MAXIMA: float = 10.0

# Texto usado en los combos para indicar "sin campo".
OPCION_NINGUNO: str = "(ninguno)"

# Identificador que se asigna a los polígonos con ID vacío.
ID_VACIO: str = "SIN_ID"

DIRECTORIO_PAQUETE: Path = Path(__file__).resolve().parent
DIRECTORIO_ASSETS: Path = DIRECTORIO_PAQUETE / "assets"
ARCHIVO_LOGO: Path = DIRECTORIO_ASSETS / "logo.png"
ARCHIVO_ICONO_ICO: Path = DIRECTORIO_ASSETS / "icono.ico"


def directorio_docs() -> Path | None:
    """Carpeta docs/ incluida: dentro del ejecutable (PyInstaller) o en el repositorio."""
    candidatos = [
        Path(getattr(sys, "_MEIPASS", "")) / "docs",
        DIRECTORIO_PAQUETE.parent.parent / "docs",
    ]
    return next((c for c in candidatos if (c / "MANUAL_DE_USO.md").is_file()), None)


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

# ── GitHub / actualizaciones ────────────────────────────────────────────────
REPO_GITHUB: str = "sparveriusdev/GeneradorCroquis"
URL_REPOSITORIO: str = f"https://github.com/{REPO_GITHUB}"
URL_RELEASES: str = f"{URL_REPOSITORIO}/releases"
URL_MANUAL: str = f"{URL_REPOSITORIO}/blob/main/docs/MANUAL_DE_USO.md"
URL_LICENCIA: str = f"{URL_REPOSITORIO}/blob/main/LICENSE"
URL_MANUAL_RAW: str = f"https://raw.githubusercontent.com/{REPO_GITHUB}/main/docs/MANUAL_DE_USO.md"
URL_DOCS_RAW: str = f"https://raw.githubusercontent.com/{REPO_GITHUB}/main/docs/"
LICENCIA: str = "GNU GPL v3.0 o posterior"
URL_API_ULTIMO_RELEASE: str = f"https://api.github.com/repos/{REPO_GITHUB}/releases/latest"
TIEMPO_ESPERA_RED: float = 15.0

# Sufijo del nombre del ejecutable publicado por el CI para cada plataforma
# (debe coincidir con la matriz de .github/workflows/release.yml).
SUFIJOS_EJECUTABLE: dict[str, str] = {
    "win32": "windows-x64.exe",
    "linux": "linux-x64.tar.gz",
    "darwin": "macos-arm64.zip",
}


@dataclass(frozen=True)
class Autor:
    nombre: str
    rol: str
    enlace: str | None = None


AUTORES: tuple[Autor, ...] = (
    Autor("Gabriel Gómez Baena", "Autor de la idea original y del script base"),
    Autor(
        "David Vásquez",
        "Desarrollo de las nuevas versiones (@sparveriusdev)",
        "https://github.com/sparveriusdev",
    ),
)

FORMATOS_EXPORTACION: tuple[tuple[str, str], ...] = (
    ("PNG", "*.png"),
    ("JPEG", "*.jpg"),
    ("PDF", "*.pdf"),
    ("SVG", "*.svg"),
)


@dataclass(frozen=True)
class ParametrosCotas:
    """Parámetros del acotado: geometría y colocación de etiquetas."""

    longitud_minima: float = 0.01
    tolerancia_principales: float = TOLERANCIA_PRINCIPALES
    tolerancia_lado_comun: float = 0.05  # m: lados de unidades distintas que coinciden
    separacion_px: float = 3.0  # hueco entre el lado y su etiqueta
    anillos: int = 4  # distancias crecientes que se prueban antes de rendirse


@dataclass(frozen=True)
class TemaCroquis:
    """Parámetros visuales del croquis (colores, tamaños, resolución)."""

    # Una pareja borde/relleno por unidad. Los bordes son oscuros para que las cotas,
    # que usan el mismo color, se lean bien sobre fondo blanco.
    paleta_borde: tuple[str, ...] = (
        "#1565C0",
        "#2E7D32",
        "#C62828",
        "#6A1B9A",
        "#E65100",
        "#00838F",
        "#AD1457",
        "#4E342E",
    )
    paleta_relleno: tuple[str, ...] = (
        "#64B5F6",
        "#81C784",
        "#E57373",
        "#BA68C8",
        "#FFB74D",
        "#4DD0E1",
        "#F06292",
        "#A1887F",
    )
    fondo: str = "#FAFAFA"
    titulo: str = "CROQUIS DE CONSTRUCCIONES"
    color_titulo: str = "#1a1a2e"
    color_subtitulo: str = "#2c3e50"
    color_pie: str = "#7f8c8d"
    color_ejes: str = "#95a5a6"
    color_etiqueta_fondo: str = "#f39c12"
    color_etiqueta_borde: str = "#e67e22"
    alfa_relleno: float = 0.20
    ancho_borde: float = 1.8
    tamano_vertice: float = 4.5
    tamano_vertice_intermedio: float = 2.0
    tamano_fuente_cota: float = 6.5
    tamano_subplot_pulgadas: float = 6.0
    decimales_coordenadas: int = 4
    marcas_eje: int = 5
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
