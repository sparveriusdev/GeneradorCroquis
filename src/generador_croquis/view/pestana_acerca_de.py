# ==============================================================================
# Archivo  : src/generador_croquis/view/pestana_acerca_de.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
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

from generador_croquis import __app_name__, __version__
from generador_croquis.config import (
    AUTORES,
    LICENCIA,
    URL_LICENCIA,
    URL_MANUAL,
    URL_REPOSITORIO,
)
from generador_croquis.view.estilos import FUENTE, SECUNDARIO

if TYPE_CHECKING:
    from generador_croquis.controller.acerca_de import ControladorAcercaDe

COLOR_ENLACE = "#1f6feb"


class PestanaAcercaDe(ttk.Frame):
    """Implementación Tkinter de :class:`~generador_croquis.controller.VistaAcercaDe`."""

    def __init__(self, parent: tk.Misc):
        super().__init__(parent, padding=20)
        self._controlador: ControladorAcercaDe | None = None
        self.estado = tk.StringVar(value="Pulse «Comprobar actualizaciones» para consultar GitHub.")
        self._construir()

    def conectar(self, controlador: ControladorAcercaDe) -> None:
        self._controlador = controlador

    # ── construcción ─────────────────────────────────────────────────────────

    def _construir(self) -> None:
        ttk.Label(self, text=__app_name__, style="Title.TLabel").pack(pady=(0, 2))
        ttk.Label(self, text=f"Versión {__version__}", style="Subtitle.TLabel").pack()
        ttk.Label(
            self,
            text="Genera croquis técnicos acotados de construcciones a partir de\n"
            "Shapefile, archivos .zip o File Geodatabase.",
            justify="center",
        ).pack(pady=(10, 15))

        creditos = ttk.LabelFrame(
            self, text="  Créditos  ", style="Section.TLabelframe", padding=15
        )
        creditos.pack(fill=tk.X, pady=(0, 10))
        for autor in AUTORES:
            ttk.Label(creditos, text=autor.nombre, font=(FUENTE, 10, "bold")).pack(anchor="w")
            if autor.enlace:
                self._enlace(creditos, autor.rol, autor.enlace).pack(anchor="w", pady=(0, 8))
            else:
                ttk.Label(creditos, text=autor.rol, foreground=SECUNDARIO).pack(
                    anchor="w", pady=(0, 8)
                )

        enlaces = ttk.Frame(self)
        enlaces.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(enlaces, text="Licencia:").pack(side=tk.LEFT)
        self._enlace(enlaces, LICENCIA, URL_LICENCIA).pack(side=tk.LEFT, padx=(4, 20))
        self._enlace(enlaces, "Manual de uso", URL_MANUAL).pack(side=tk.LEFT)

        repo = ttk.LabelFrame(self, text="  Versiones  ", style="Section.TLabelframe", padding=15)
        repo.pack(fill=tk.X)
        self._enlace(repo, URL_REPOSITORIO, URL_REPOSITORIO).pack(anchor="w", pady=(0, 10))

        botones = ttk.Frame(repo)
        botones.pack(fill=tk.X)
        self.btn_comprobar = ttk.Button(
            botones, text="Comprobar actualizaciones", command=self._comprobar
        )
        self.btn_comprobar.pack(side=tk.LEFT)
        self.btn_descargar = ttk.Button(
            botones, text="Descargar nueva versión", command=self._descargar, state="disabled"
        )
        self.btn_descargar.pack(side=tk.LEFT, padx=8)
        ttk.Button(botones, text="Ver versiones en GitHub", command=self._ver_releases).pack(
            side=tk.RIGHT
        )

        ttk.Label(repo, textvariable=self.estado, wraplength=640, justify="left").pack(
            anchor="w", pady=(10, 4)
        )
        self.progreso = ttk.Progressbar(repo, mode="indeterminate", maximum=1.0)
        self.progreso.pack(fill=tk.X)

    def _enlace(self, parent: tk.Misc, texto: str, url: str) -> ttk.Label:
        etiqueta = ttk.Label(parent, text=texto, foreground=COLOR_ENLACE, cursor="hand2")
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
        else:
            self.btn_descargar.config(text="Descargar nueva versión", state="disabled")

    def comprobando(self, activo: bool) -> None:
        self.btn_comprobar["state"] = "disabled" if activo else "normal"
        if activo:
            self.btn_descargar["state"] = "disabled"
            if str(self.progreso["mode"]) == "indeterminate":
                self.progreso.start()
        else:
            self.progreso.stop()

    def mostrar_progreso(self, fraccion: float | None) -> None:
        self.progreso.stop()
        if fraccion is None:
            self.progreso.config(mode="indeterminate", value=0)
        else:
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
