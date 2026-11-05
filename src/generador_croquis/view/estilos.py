# ==============================================================================
# Archivo  : src/generador_croquis/view/estilos.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Estilos ttk y paleta de la interfaz,
#          |            | extraídos de AplicacionCroquis._crear_interfaz().
# ==============================================================================
"""Estilos visuales de la interfaz Tkinter."""

from __future__ import annotations

import contextlib
import tkinter as tk
from tkinter import ttk

FONDO = "#f0f2f5"
TEXTO = "#1a1a2e"
SECUNDARIO = "#6c757d"
SECCION = "#2c3e50"
EXITO = "#28a745"
FUENTE = "Segoe UI"
FUENTE_MONO = "Consolas"


def aplicar_estilos(root: tk.Misc) -> None:
    style = ttk.Style(root)
    with contextlib.suppress(tk.TclError):
        style.theme_use("clam")
    style.configure(".", background=FONDO)
    style.configure("TFrame", background=FONDO)
    style.configure("TLabel", background=FONDO)
    style.configure("Title.TLabel", font=(FUENTE, 16, "bold"), foreground=TEXTO)
    style.configure("Subtitle.TLabel", font=(FUENTE, 9), foreground=SECUNDARIO)
    style.configure("Nota.TLabel", foreground=EXITO)
    style.configure("Section.TLabelframe", background=FONDO)
    style.configure(
        "Section.TLabelframe.Label", font=(FUENTE, 10, "bold"), background=FONDO, foreground=SECCION
    )
    style.configure("Action.TButton", font=(FUENTE, 10, "bold"), padding=(20, 10))
    style.configure("Browse.TButton", font=(FUENTE, 9), padding=(10, 5))


def centrar(
    ventana: tk.Toplevel | tk.Tk, ancho: int, alto: int, relativo_a: tk.Misc | None = None
) -> None:
    """Centra una ventana en la pantalla o sobre otra ventana."""
    ventana.update_idletasks()
    if relativo_a is not None:
        x = relativo_a.winfo_rootx() + (relativo_a.winfo_width() - ancho) // 2
        y = relativo_a.winfo_rooty() + (relativo_a.winfo_height() - alto) // 2
    else:
        x = (ventana.winfo_screenwidth() - ancho) // 2
        y = (ventana.winfo_screenheight() - alto) // 2
    ventana.geometry(f"{ancho}x{alto}+{max(x, 0)}+{max(y, 0)}")
