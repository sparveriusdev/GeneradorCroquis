# ==============================================================================
# Archivo  : src/generador_croquis/view/pestana_ayuda.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Pestaña "Ayuda": muestra el manual de uso
#          |            | (GitHub o copia local) con indicador de origen,
#          |            | botones para recargar y abrir en GitHub.
#          |            | Implementa VistaAyuda.
# ==============================================================================
"""Pestaña "Ayuda"."""

from __future__ import annotations

import tkinter as tk
import webbrowser
from tkinter import ttk
from typing import TYPE_CHECKING

from generador_croquis.view.componentes import Chip
from generador_croquis.view.estilos import TemaMaterial
from generador_croquis.view.markdown_tk import VisorMarkdown

if TYPE_CHECKING:
    from generador_croquis.controller.ayuda import ControladorAyuda
    from generador_croquis.services.ayuda import ManualAyuda


class PestanaAyuda(ttk.Frame):
    def __init__(self, parent: tk.Misc, tema: TemaMaterial):
        super().__init__(parent, padding=(24, 16, 24, 20))
        self._controlador: ControladorAyuda | None = None
        self._manual: ManualAyuda | None = None
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        barra = ttk.Frame(self)
        barra.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ttk.Label(barra, text="Manual de uso", style="Headline.TLabel").pack(side=tk.LEFT)
        self.chip = Chip(barra, "Cargando…")
        self.chip.pack(side=tk.LEFT, padx=12)
        ttk.Button(
            barra, text="Abrir en GitHub", style="Outlined.TButton", command=self._abrir_github
        ).pack(side=tk.RIGHT)
        self.btn_recargar = ttk.Button(
            barra, text="Recargar", style="Text.TButton", command=self._recargar
        )
        self.btn_recargar.pack(side=tk.RIGHT, padx=6)

        tarjeta = ttk.Frame(self, style="Card.TFrame", padding=2)
        tarjeta.grid(row=1, column=0, sticky="nsew")
        self.progreso = ttk.Progressbar(
            tarjeta, mode="indeterminate", style="Material.Horizontal.TProgressbar"
        )
        self.visor = VisorMarkdown(tarjeta, tema, self._resolver_imagen)
        self.visor.pack(fill=tk.BOTH, expand=True, padx=1, pady=(1, 8))

    def conectar(self, controlador: ControladorAyuda) -> None:
        self._controlador = controlador

    def al_mostrarse(self) -> None:
        if self._controlador:
            self._controlador.asegurar_cargado()

    def _resolver_imagen(self, relativa: str):
        return self._manual.ruta_imagen(relativa) if self._manual else None

    def _recargar(self) -> None:
        if self._controlador:
            self._controlador.recargar()

    def _abrir_github(self) -> None:
        if self._controlador:
            self._controlador.abrir_en_github()

    # ── VistaAyuda ───────────────────────────────────────────────────────────

    def mostrar_cargando(self) -> None:
        self.chip.mostrar("Cargando…")
        self.btn_recargar.state(["disabled"])
        self.progreso.pack(fill=tk.X, side=tk.TOP, before=self.visor, padx=12, pady=(10, 0))
        self.progreso.start(12)
        if self._manual is None:
            self.visor.mostrar_mensaje("Obteniendo el manual de uso…")

    def mostrar_manual(self, manual: ManualAyuda) -> None:
        self._manual = manual
        self._terminar_carga()
        if manual.desde_github:
            self.chip.mostrar("✓ Versión más reciente (GitHub)", "ok")
        else:
            self.chip.mostrar("Copia incluida · sin conexión")
        self.visor.mostrar(manual.documento, manual.url_base)

    def mostrar_error_carga(self, mensaje: str) -> None:
        self._terminar_carga()
        self.chip.mostrar("No disponible")
        self.visor.mostrar_mensaje(f"No se pudo cargar el manual.\n\n{mensaje}")

    def abrir_url(self, url: str) -> None:
        webbrowser.open(url)

    def _terminar_carga(self) -> None:
        self.progreso.stop()
        self.progreso.pack_forget()
        self.btn_recargar.state(["!disabled"])
