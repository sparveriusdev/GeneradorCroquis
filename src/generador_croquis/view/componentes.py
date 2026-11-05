# ==============================================================================
# Archivo  : src/generador_croquis/view/componentes.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Componentes Material reutilizables:
#          |            | Tarjeta, BarraNavegacion (pestañas con indicador),
#          |            | Chip, CampoSeleccion (combo + texto de ayuda) y
#          |            | TablaClaveValor.
# ==============================================================================
"""Componentes visuales reutilizables (estilo Material Design 3)."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable, Sequence
from tkinter import ttk


class Tarjeta(ttk.Frame):
    """Tarjeta con contorno, título opcional y descripción. Use ``.cuerpo`` como contenedor."""

    def __init__(
        self,
        parent: tk.Misc,
        titulo: str | None = None,
        descripcion: str | None = None,
        icono: str | None = None,
    ):
        super().__init__(parent, style="Card.TFrame", padding=(20, 18))
        self.columnconfigure(0, weight=1)
        fila = 0
        if titulo:
            texto = f"{icono}  {titulo}" if icono else titulo
            ttk.Label(self, text=texto, style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
            fila += 1
        if descripcion:
            self.descripcion = ttk.Label(
                self, text=descripcion, style="CardBody.TLabel", wraplength=420, justify="left"
            )
            self.descripcion.grid(row=fila, column=0, sticky="w", pady=(2, 0))
            self.bind("<Configure>", self._ajustar_texto, add="+")
            fila += 1
        self.cuerpo = ttk.Frame(self, style="CardInner.TFrame")
        self.cuerpo.grid(row=fila, column=0, sticky="nsew", pady=(14 if fila else 0, 0))
        self.rowconfigure(fila, weight=1)

    def _ajustar_texto(self, evento: tk.Event) -> None:
        self.descripcion.configure(wraplength=max(evento.width - 40, 200))


class Chip(ttk.Label):
    """Etiqueta pequeña de estado (Material "assist/suggestion chip")."""

    ESTILOS = {
        "ok": "ChipOk.TLabel",
        "neutral": "ChipNeutral.TLabel",
        "version": "ChipVersion.TLabel",
    }

    def __init__(self, parent: tk.Misc, texto: str = "", tipo: str = "neutral"):
        super().__init__(parent, text=texto, style=self.ESTILOS[tipo])

    def mostrar(self, texto: str, tipo: str = "neutral") -> None:
        self.configure(text=texto, style=self.ESTILOS[tipo])


class BarraNavegacion(ttk.Frame):
    """Pestañas Material: texto + indicador inferior en la pestaña activa."""

    def __init__(
        self,
        parent: tk.Misc,
        contenedor: ttk.Frame,
        al_cambiar: Callable[[str], None] | None = None,
    ):
        super().__init__(parent)
        self._contenedor = contenedor
        self._contenedor.rowconfigure(0, weight=1)
        self._contenedor.columnconfigure(0, weight=1)
        self._pestanas: dict[str, tuple[ttk.Label, ttk.Frame, tk.Misc]] = {}
        self._al_cambiar = al_cambiar
        self.actual: str | None = None
        barra = ttk.Frame(self)
        barra.pack(side=tk.TOP, anchor="w", padx=16)
        self._barra = barra
        ttk.Frame(self, style="Divider.TFrame", height=1).pack(side=tk.TOP, fill=tk.X)

    def agregar(self, clave: str, texto: str, pagina: tk.Misc) -> None:
        columna = ttk.Frame(self._barra)
        columna.pack(side=tk.LEFT)
        etiqueta = ttk.Label(columna, text=texto, style="Tab.TLabel", cursor="hand2")
        etiqueta.pack()
        indicador = ttk.Frame(columna, style="IndicadorOff.TFrame", height=3)
        indicador.pack(fill=tk.X, padx=12)
        etiqueta.bind("<Button-1>", lambda _e: self.seleccionar(clave))
        pagina.grid(in_=self._contenedor, row=0, column=0, sticky="nsew")
        self._pestanas[clave] = (etiqueta, indicador, pagina)
        if self.actual is None:
            self.seleccionar(clave)

    def seleccionar(self, clave: str) -> None:
        for nombre, (etiqueta, indicador, pagina) in self._pestanas.items():
            activa = nombre == clave
            etiqueta.configure(style="TabActive.TLabel" if activa else "Tab.TLabel")
            indicador.configure(style="Indicador.TFrame" if activa else "IndicadorOff.TFrame")
            if activa:
                pagina.tkraise()
        cambio = clave != self.actual
        self.actual = clave
        if cambio and self._al_cambiar:
            self._al_cambiar(clave)


class CampoSeleccion(ttk.Frame):
    """Etiqueta + combo de solo lectura + texto de ayuda + chip de detección."""

    def __init__(self, parent: tk.Misc, etiqueta: str, ayuda: str, variable: tk.StringVar):
        super().__init__(parent, style="CardInner.TFrame")
        self.columnconfigure(0, weight=1)
        cabecera = ttk.Frame(self, style="CardInner.TFrame")
        cabecera.grid(row=0, column=0, sticky="ew")
        ttk.Label(cabecera, text=etiqueta, style="Key.TLabel").pack(side=tk.LEFT)
        self.chip = Chip(cabecera)
        self.combo = ttk.Combobox(self, textvariable=variable, state="disabled")
        self.combo.grid(row=1, column=0, sticky="ew", pady=(6, 4))
        ttk.Label(self, text=ayuda, style="Helper.TLabel", wraplength=520, justify="left").grid(
            row=2, column=0, sticky="w"
        )

    def configurar(self, opciones: Sequence[str], nota: str, detectado: bool) -> None:
        self.combo.configure(values=list(opciones), state="readonly")
        self.chip.mostrar(nota, "ok" if detectado else "neutral")
        self.chip.pack(side=tk.RIGHT)


class TablaClaveValor(ttk.Frame):
    """Lista de pares etiqueta/valor alineados en dos columnas."""

    def __init__(self, parent: tk.Misc, vacio: str):
        super().__init__(parent, style="CardInner.TFrame")
        self.columnconfigure(1, weight=1)
        self._vacio = vacio
        self.mostrar([])

    def mostrar(self, filas: Sequence[tuple[str, str]], avisos: Sequence[str] = ()) -> None:
        for hijo in self.winfo_children():
            hijo.destroy()
        if not filas:
            ttk.Label(
                self, text=self._vacio, style="CardBody.TLabel", wraplength=360, justify="left"
            ).grid(row=0, column=0, columnspan=2, sticky="w")
            return
        for i, (clave, valor) in enumerate(filas):
            ttk.Label(self, text=clave, style="Key.TLabel").grid(
                row=i, column=0, sticky="nw", padx=(0, 16), pady=3
            )
            ttk.Label(self, text=valor, style="Value.TLabel", wraplength=320, justify="left").grid(
                row=i, column=1, sticky="w", pady=3
            )
        for j, aviso in enumerate(avisos, start=len(filas)):
            ttk.Label(
                self, text=f"⚠  {aviso}", style="Warning.TLabel", wraplength=420, justify="left"
            ).grid(row=j, column=0, columnspan=2, sticky="ew", pady=(8, 0))
