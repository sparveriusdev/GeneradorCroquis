# ==============================================================================
# Archivo  : src/generador_croquis/view/fuentes.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Registra la fuente Roboto incluida en el
#          |            | paquete solo para este proceso (sin instalarla en
#          |            | el sistema): GDI en Windows, fontconfig en Linux y
#          |            | CoreText en macOS. Si falla, se usa la fuente del
#          |            | sistema más parecida. Activa DPI-awareness en
#          |            | Windows para que el texto se vea nítido.
# ==============================================================================
"""Carga de fuentes tipográficas propias."""

from __future__ import annotations

import ctypes
import ctypes.util
import logging
import sys
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path

log = logging.getLogger(__name__)

DIRECTORIO_FUENTES = Path(__file__).resolve().parent.parent / "assets" / "fonts"
FAMILIA_PRINCIPAL = "Roboto"
FAMILIA_MEDIA = "Roboto Medium"
FAMILIA_MONO_PREFERIDAS = ("Cascadia Mono", "Consolas", "SF Mono", "Menlo", "DejaVu Sans Mono")
FAMILIAS_RESPALDO = ("Segoe UI", "SF Pro Text", "Helvetica Neue", "Noto Sans", "DejaVu Sans")


def activar_dpi_windows() -> None:
    """Evita que Windows escale la ventana como mapa de bits (texto borroso)."""
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # type: ignore[attr-defined]
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()  # type: ignore[attr-defined]
        except Exception:
            log.debug("No se pudo activar DPI-awareness")


def registrar_fuentes(directorio: Path = DIRECTORIO_FUENTES) -> int:
    """Registra los .ttf del directorio para este proceso. Llamar antes de crear Tk()."""
    archivos = sorted(directorio.glob("*.ttf"))
    registradas = 0
    for archivo in archivos:
        try:
            if _registrar(archivo):
                registradas += 1
        except Exception:
            log.debug("No se pudo registrar %s", archivo, exc_info=True)
    log.info("Fuentes registradas: %d de %d", registradas, len(archivos))
    return registradas


def _registrar(archivo: Path) -> bool:
    if sys.platform == "win32":
        fr_private = 0x10
        return bool(ctypes.windll.gdi32.AddFontResourceExW(str(archivo), fr_private, 0))  # type: ignore[attr-defined]
    if sys.platform == "darwin":
        return _registrar_macos(archivo)
    return _registrar_fontconfig(archivo)


def _registrar_fontconfig(archivo: Path) -> bool:
    nombre = ctypes.util.find_library("fontconfig") or "libfontconfig.so.1"
    fc = ctypes.CDLL(nombre)
    fc.FcConfigGetCurrent.restype = ctypes.c_void_p
    fc.FcConfigAppFontAddFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    return bool(fc.FcConfigAppFontAddFile(fc.FcConfigGetCurrent(), str(archivo).encode()))


def _registrar_macos(archivo: Path) -> bool:
    cf = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
    ct = ctypes.CDLL("/System/Library/Frameworks/CoreText.framework/CoreText")
    cf.CFURLCreateFromFileSystemRepresentation.restype = ctypes.c_void_p
    cf.CFURLCreateFromFileSystemRepresentation.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.c_long,
        ctypes.c_bool,
    ]
    cf.CFRelease.argtypes = [ctypes.c_void_p]
    ct.CTFontManagerRegisterFontsForURL.restype = ctypes.c_bool
    ct.CTFontManagerRegisterFontsForURL.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_void_p,
    ]
    ruta = str(archivo).encode()
    url = cf.CFURLCreateFromFileSystemRepresentation(None, ruta, len(ruta), False)
    try:
        scope_proceso = 1  # kCTFontManagerScopeProcess
        return bool(ct.CTFontManagerRegisterFontsForURL(url, scope_proceso, None))
    finally:
        cf.CFRelease(url)


def elegir_familia(root: tk.Misc, preferidas: tuple[str, ...]) -> str:
    """Primera familia disponible de la lista (requiere una raíz Tk creada)."""
    disponibles = {f.lower() for f in tkfont.families(root)}
    for familia in preferidas:
        if familia.lower() in disponibles:
            return familia
    return tkfont.nametofont("TkDefaultFont", root).actual("family")
