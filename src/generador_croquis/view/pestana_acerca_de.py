# ==============================================================================
# Archivo  : src/generador_croquis/view/pestana_acerca_de.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v2.0.0 | 2026-11-05 | Rediseño Material: cabecera con logo, tarjetas de
#          |            | créditos y de actualizaciones en dos columnas,
#          |            | botones Filled/Tonal/Text, progreso lineal.
#   v1.1.0 | 2026-11-05 | Muestra la licencia (GPL-3.0) y enlace al manual.
#   v1.0.0 | 2026-11-05 | Creación. Pestaña "Acerca de": versión instalada,
#          |            | créditos, enlace al repositorio, comprobación de
#          |            | nuevas versiones en GitHub y descarga con barra de
#          |            | progreso. Implementa VistaAcercaDe.
# ==============================================================================
"""Pestaña "Acerca de"."""

from __future__ import annotations

import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import TYPE_CHECKING

from PIL import Image, ImageTk

from generador_croquis import __app_name__, __version__
from generador_croquis.config import (
    ARCHIVO_LOGO,
    AUTORES,
    LICENCIA,
    URL_LICENCIA,
    URL_MANUAL,
    URL_REPOSITORIO,
)
from generador_croquis.view.componentes import Chip, Tarjeta
from generador_croquis.view.estilos import TemaMaterial

if TYPE_CHECKING:
    from generador_croquis.controller.acerca_de import ControladorAcercaDe


class PestanaAcercaDe(ttk.Frame):
    """Implementación Tkinter de :class:`~generador_croquis.controller.VistaAcercaDe`."""

    def __init__(self, parent: tk.Misc, tema: TemaMaterial):
        super().__init__(parent, padding=(24, 20, 24, 16))
        self._tema = tema
        self._controlador: ControladorAcercaDe | None = None
        self.estado = tk.StringVar(
            value="Pulse «Buscar actualizaciones» para consultar la última versión publicada."
        )
        self._construir()

    def conectar(self, controlador: ControladorAcercaDe) -> None:
        self._controlador = controlador

    # ── construcción ─────────────────────────────────────────────────────────

    def _construir(self) -> None:
        self.columnconfigure(0, weight=1, uniform="col")
        self.columnconfigure(1, weight=1, uniform="col")

        cabecera = ttk.Frame(self)
        cabecera.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        if ARCHIVO_LOGO.is_file():
            logo = Image.open(ARCHIVO_LOGO).resize((88, 88), Image.LANCZOS)
            self._logo = ImageTk.PhotoImage(logo, master=self)
            tk.Label(
                cabecera, image=self._logo, background=self._tema.c.surface, borderwidth=0
            ).pack(side=tk.LEFT, padx=(0, 18))
        textos = ttk.Frame(cabecera)
        textos.pack(side=tk.LEFT, fill=tk.X, expand=True)
        fila = ttk.Frame(textos)
        fila.pack(anchor="w")
        ttk.Label(fila, text=__app_name__, style="Headline.TLabel").pack(side=tk.LEFT)
        Chip(fila, f"Versión {__version__}", "version").pack(side=tk.LEFT, padx=12)
        ttk.Label(
            textos,
            text="Genera croquis técnicos acotados de construcciones a partir de Shapefile, "
            "archivos .zip o File Geodatabase: medidas de cada lado, área, perímetro y pisos.",
            style="Body.TLabel",
            wraplength=640,
            justify="left",
        ).pack(anchor="w", pady=(6, 8))
        enlaces = ttk.Frame(textos)
        enlaces.pack(anchor="w")
        for texto, url in (
            ("Repositorio en GitHub", URL_REPOSITORIO),
            ("Manual de uso", URL_MANUAL),
            (f"Licencia: {LICENCIA}", URL_LICENCIA),
        ):
            self._enlace(enlaces, texto, url, "TLabel").pack(side=tk.LEFT, padx=(0, 18))

        # Créditos
        creditos = Tarjeta(self, "Créditos")
        creditos.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        for autor in AUTORES:
            ttk.Label(creditos.cuerpo, text=autor.nombre, style="CardTitle.TLabel").pack(anchor="w")
            if autor.enlace:
                self._enlace(creditos.cuerpo, autor.rol, autor.enlace).pack(
                    anchor="w", pady=(2, 14)
                )
            else:
                ttk.Label(creditos.cuerpo, text=autor.rol, style="CardBody.TLabel").pack(
                    anchor="w", pady=(2, 14)
                )

        # Actualizaciones
        versiones = Tarjeta(
            self,
            "Actualizaciones",
            "La aplicación solo se conecta a internet cuando usted lo pide.",
        )
        versiones.grid(row=1, column=1, sticky="nsew")
        cuerpo = versiones.cuerpo
        cuerpo.columnconfigure(0, weight=1)
        ttk.Label(
            cuerpo, textvariable=self.estado, style="Card.TLabel", wraplength=380, justify="left"
        ).grid(row=0, column=0, sticky="w")
        self.progreso = ttk.Progressbar(
            cuerpo, mode="indeterminate", maximum=1.0, style="Material.Horizontal.TProgressbar"
        )
        botones = ttk.Frame(cuerpo, style="CardInner.TFrame")
        botones.grid(row=2, column=0, sticky="w", pady=(14, 0))
        self.btn_comprobar = ttk.Button(
            botones, text="Buscar actualizaciones", style="Tonal.TButton", command=self._comprobar
        )
        self.btn_comprobar.pack(side=tk.LEFT)
        self.btn_descargar = ttk.Button(
            botones, text="Descargar", style="Filled.TButton", command=self._descargar
        )
        ttk.Button(
            cuerpo,
            text="Ver todas las versiones",
            style="TextCard.TButton",
            command=self._ver_releases,
        ).grid(row=3, column=0, sticky="w", pady=(8, 0))

    def _enlace(
        self, parent: tk.Misc, texto: str, url: str, estilo: str = "Link.TLabel"
    ) -> ttk.Label:
        etiqueta = ttk.Label(
            parent, text=texto, style=estilo, cursor="hand2", foreground=self._tema.c.primary
        )
        etiqueta.bind("<Button-1>", lambda _e: self.abrir_url(url))
        return etiqueta

    # ── eventos → controlador ────────────────────────────────────────────────

    def _comprobar(self) -> None:
        if self._controlador:
            self._controlador.comprobar()

    def _descargar(self) -> None:
        if self._controlador:
            self._controlador.descargar()

    def _ver_releases(self) -> None:
        if self._controlador:
            self._controlador.abrir_releases()

    # ── implementación de VistaAcercaDe ──────────────────────────────────────

    def mostrar_estado(self, texto: str) -> None:
        self.estado.set(texto)

    def ofrecer_descarga(self, version: str | None) -> None:
        if version:
            self.btn_descargar.config(text=f"Descargar v{version}", state="normal")
            self.btn_descargar.pack(side=tk.LEFT, padx=(10, 0))
        else:
            self.btn_descargar.pack_forget()

    def comprobando(self, activo: bool) -> None:
        self.btn_comprobar["state"] = "disabled" if activo else "normal"
        if activo:
            self.btn_descargar["state"] = "disabled"
            self.progreso.grid(row=1, column=0, sticky="ew", pady=(12, 0))
            if str(self.progreso["mode"]) == "indeterminate":
                self.progreso.start(12)
        else:
            self.progreso.stop()
            self.progreso.grid_remove()

    def mostrar_progreso(self, fraccion: float | None) -> None:
        self.progreso.stop()
        if fraccion is None:
            self.progreso.config(mode="indeterminate", value=0)
        else:
            self.progreso.grid(row=1, column=0, sticky="ew", pady=(12, 0))
            self.progreso.config(mode="determinate", value=fraccion)

    def pedir_carpeta(self) -> str | None:
        inicial = Path.home() / "Downloads"
        return (
            filedialog.askdirectory(
                parent=self,
                title="Carpeta donde guardar la nueva versión",
                initialdir=inicial if inicial.is_dir() else Path.home(),
            )
            or None
        )

    def abrir_url(self, url: str) -> None:
        webbrowser.open(url)

    def mostrar_error(self, titulo: str, mensaje: str) -> None:
        messagebox.showerror(titulo, mensaje, parent=self)

    def mostrar_exito(self, titulo: str, mensaje: str) -> None:
        messagebox.showinfo(titulo, mensaje, parent=self)
