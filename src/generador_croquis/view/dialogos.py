# ==============================================================================
# Archivo  : src/generador_croquis/view/dialogos.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.2.0 | 2026-11-06 | Visor: aviso de que la etiqueta del identificador
#          |            | se puede arrastrar y de que «Guardar imagen»
#          |            | conserva la posición.
#   v1.1.0 | 2026-11-05 | Estilo Material: diálogo de selección con título,
#          |            | texto de apoyo, lista con contorno y acciones a la
#          |            | derecha.
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

from generador_croquis.view.estilos import TemaMaterial, centrar


class DialogoSeleccion:
    """Diálogo modal Material para elegir un elemento de una lista."""

    def __init__(
        self,
        parent: tk.Misc,
        tema: TemaMaterial,
        titulo: str,
        mensaje: str,
        opciones: Sequence[str],
    ):
        c, t = tema.c, tema.t
        self._opciones = list(opciones)
        self.resultado: str | None = None

        self._dlg = tk.Toplevel(parent, background=c.surface)
        self._dlg.title(titulo)
        self._dlg.transient(parent.winfo_toplevel())
        self._dlg.minsize(420, 320)
        centrar(self._dlg, 560, 420, relativo_a=parent)

        marco = ttk.Frame(self._dlg, padding=24)
        marco.pack(fill=tk.BOTH, expand=True)
        marco.columnconfigure(0, weight=1)
        marco.rowconfigure(2, weight=1)
        ttk.Label(marco, text=titulo, style="Headline.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(marco, text=mensaje, style="Body.TLabel", wraplength=500, justify="left").grid(
            row=1, column=0, sticky="w", pady=(6, 14)
        )

        lista_marco = tk.Frame(marco, background=c.outline_variant, padx=1, pady=1)
        lista_marco.grid(row=2, column=0, sticky="nsew")
        self._lista = tk.Listbox(
            lista_marco,
            font=t.body_medium,
            selectmode=tk.SINGLE,
            exportselection=False,
            activestyle="none",
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            background=c.surface_container_lowest,
            foreground=c.on_surface,
            selectbackground=c.primary_container,
            selectforeground=c.on_primary_container,
        )
        barra = ttk.Scrollbar(
            lista_marco, command=self._lista.yview, style="Material.Vertical.TScrollbar"
        )
        self._lista.configure(yscrollcommand=barra.set)
        barra.pack(side=tk.RIGHT, fill=tk.Y)
        self._lista.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=6)
        for opcion in self._opciones:
            self._lista.insert(tk.END, f"  {opcion}")
        self._lista.select_set(0)
        self._lista.focus_set()

        botones = ttk.Frame(marco)
        botones.grid(row=3, column=0, sticky="e", pady=(18, 0))
        ttk.Button(botones, text="Cancelar", style="Text.TButton", command=self._dlg.destroy).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(botones, text="Seleccionar", style="Filled.TButton", command=self._aceptar).pack(
            side=tk.LEFT
        )

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
    """Ventana con la figura de matplotlib y su barra de navegación (zoom, mover).

    La etiqueta naranja del identificador es arrastrable (``Annotation.draggable``): el
    renderizador la deja así y aquí solo se avisa al usuario.
    """

    AVISO = (
        "Puede arrastrar la etiqueta naranja del identificador para moverla (con Zoom y "
        "Mover desactivados). «Guardar imagen» conserva la posición."
    )

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
        aviso = ttk.Frame(self.ventana, style="Status.TFrame", padding=(12, 4))
        ttk.Label(aviso, text=self.AVISO, style="Status.TLabel").pack(side=tk.LEFT)
        aviso.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        canvas.draw_idle()

    def cerrar(self) -> None:
        if self.ventana.winfo_exists():
            self.ventana.destroy()
