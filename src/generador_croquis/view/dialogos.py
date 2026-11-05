# ==============================================================================
# Archivo  : src/generador_croquis/view/dialogos.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Diálogo de selección (antes
#          |            | seleccionar_de_lista) y ventana de vista previa
#          |            | de la figura embebida en Tk (reemplaza plt.show).
#          |            | Mejoras: doble clic / Enter para aceptar, Escape
#          |            | para cancelar, barra de zoom de matplotlib.
# ==============================================================================
"""Diálogos y ventanas secundarias."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Sequence
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from generador_croquis.view.estilos import FUENTE, FUENTE_MONO, centrar


class DialogoSeleccion:
    """Diálogo modal para elegir un elemento de una lista."""

    def __init__(self, parent: tk.Misc, titulo: str, mensaje: str, opciones: Sequence[str]):
        self._opciones = list(opciones)
        self.resultado: str | None = None

        self._dlg = tk.Toplevel(parent)
        self._dlg.title(titulo)
        self._dlg.resizable(False, False)
        self._dlg.transient(parent.winfo_toplevel())
        centrar(self._dlg, 520, 330, relativo_a=parent)

        ttk.Label(self._dlg, text=mensaje, font=(FUENTE, 10)).pack(pady=10)

        marco = ttk.Frame(self._dlg)
        marco.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        barra = ttk.Scrollbar(marco)
        barra.pack(side=tk.RIGHT, fill=tk.Y)
        self._lista = tk.Listbox(
            marco,
            font=(FUENTE_MONO, 9),
            yscrollcommand=barra.set,
            selectmode=tk.SINGLE,
            exportselection=False,
        )
        self._lista.pack(fill=tk.BOTH, expand=True)
        barra.config(command=self._lista.yview)
        for opcion in self._opciones:
            self._lista.insert(tk.END, opcion)
        self._lista.select_set(0)
        self._lista.focus_set()

        botones = ttk.Frame(self._dlg)
        botones.pack(pady=10)
        ttk.Button(botones, text="Seleccionar", command=self._aceptar).pack(side=tk.LEFT, padx=5)
        ttk.Button(botones, text="Cancelar", command=self._dlg.destroy).pack(side=tk.LEFT, padx=5)

        self._lista.bind("<Double-Button-1>", lambda _e: self._aceptar())
        self._dlg.bind("<Return>", lambda _e: self._aceptar())
        self._dlg.bind("<Escape>", lambda _e: self._dlg.destroy())

    def mostrar(self) -> str | None:
        self._dlg.grab_set()
        self._dlg.wait_window()
        return self.resultado

    def _aceptar(self) -> None:
        seleccion = self._lista.curselection()
        if seleccion:
            self.resultado = self._opciones[seleccion[0]]
        self._dlg.destroy()


class VentanaFigura:
    """Ventana con la figura de matplotlib y su barra de navegación (zoom, mover)."""

    def __init__(self, parent: tk.Misc, figura: Figure, titulo: str = "Croquis"):
        self.ventana = tk.Toplevel(parent)
        self.ventana.title(titulo)
        ancho = int(self.ventana.winfo_screenwidth() * 0.8)
        alto = int(self.ventana.winfo_screenheight() * 0.8)
        centrar(self.ventana, ancho, alto)

        canvas = FigureCanvasTkAgg(figura, master=self.ventana)
        barra = NavigationToolbar2Tk(canvas, self.ventana, pack_toolbar=False)
        barra.update()
        barra.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        canvas.draw_idle()

    def cerrar(self) -> None:
        if self.ventana.winfo_exists():
            self.ventana.destroy()
