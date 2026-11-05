# ==============================================================================
# Archivo  : src/generador_croquis/view/componentes.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.1.0 | 2026-11-05 | PaginaDesplazable (pantallas bajas, p. ej. 768 px)
#          |            | y TablaClaveValor con ajuste de texto al ancho real.
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
        super().__init__(parent, style="Card.TFrame", padding=(20, 14))
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
    """Lista de pares etiqueta/valor alineados en dos columnas.

    El texto de los valores se ajusta al ancho disponible para no desbordar la tarjeta.
    """

    def __init__(self, parent: tk.Misc, vacio: str):
        super().__init__(parent, style="CardInner.TFrame")
        self.columnconfigure(1, weight=1)
        self._vacio = vacio
        self._valores: list[ttk.Label] = []
        self._anchos: list[ttk.Label] = []  # etiquetas que ocupan todo el ancho
        self.bind("<Configure>", self._ajustar, add="+")
        self.mostrar([])

    def mostrar(self, filas: Sequence[tuple[str, str]], avisos: Sequence[str] = ()) -> None:
        for hijo in self.winfo_children():
            hijo.destroy()
        self._valores, self._anchos = [], []
        if not filas:
            vacio = ttk.Label(self, text=self._vacio, style="CardBody.TLabel", justify="left")
            vacio.grid(row=0, column=0, columnspan=2, sticky="w")
            self._anchos.append(vacio)
        for i, (clave, valor) in enumerate(filas):
            ttk.Label(self, text=clave, style="Key.TLabel").grid(
                row=i, column=0, sticky="nw", padx=(0, 16), pady=3
            )
            etiqueta = ttk.Label(self, text=valor, style="Value.TLabel", justify="left")
            etiqueta.grid(row=i, column=1, sticky="w", pady=3)
            self._valores.append(etiqueta)
        for j, aviso in enumerate(avisos, start=len(filas)):
            etiqueta = ttk.Label(self, text=f"⚠  {aviso}", style="Warning.TLabel", justify="left")
            etiqueta.grid(row=j, column=0, columnspan=2, sticky="ew", pady=(8, 0))
            self._anchos.append(etiqueta)
        self.after_idle(self._ajustar)

    def _ajustar(self, _evento: tk.Event | None = None) -> None:
        ancho = self.winfo_width()
        if ancho <= 1:
            return
        claves = self.grid_bbox(0, 0)[2] if self._valores else 0
        for etiqueta in self._valores:
            etiqueta.configure(wraplength=max(ancho - claves - 24, 120))
        for etiqueta in self._anchos:
            etiqueta.configure(wraplength=max(ancho - 24, 160))


class PaginaDesplazable(ttk.Frame):
    """Contenedor con barra de desplazamiento vertical que solo aparece si hace falta.

    Coloque los widgets dentro de ``.contenido``; su ancho sigue al de la ventana.
    """

    def __init__(self, parent: tk.Misc, fondo: str):
        super().__init__(parent)
        self._lienzo = tk.Canvas(self, highlightthickness=0, borderwidth=0, background=fondo)
        self._barra = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self._lienzo.yview,
            style="Material.Vertical.TScrollbar",
        )
        self._lienzo.configure(yscrollcommand=self._barra.set)
        self._lienzo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.contenido = ttk.Frame(self._lienzo)
        self._ventana = self._lienzo.create_window((0, 0), window=self.contenido, anchor="nw")
        self.contenido.bind("<Configure>", self._actualizar)
        self._lienzo.bind("<Configure>", self._actualizar)
        # Un manejador global que solo actúa si el puntero está sobre esta página.
        for evento in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self._lienzo.bind_all(evento, self._desplazar, add="+")

    def _actualizar(self, _evento: tk.Event | None = None) -> None:
        alto_lienzo = self._lienzo.winfo_height()
        alto_contenido = self.contenido.winfo_reqheight()
        # El contenido ocupa al menos todo el alto visible (para que las filas elásticas crezcan).
        self._lienzo.itemconfigure(
            self._ventana, width=self._lienzo.winfo_width(), height=max(alto_contenido, alto_lienzo)
        )
        self._lienzo.configure(scrollregion=(0, 0, 0, max(alto_contenido, alto_lienzo)))
        if alto_contenido > alto_lienzo + 1:
            self._barra.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            self._barra.pack_forget()
            self._lienzo.yview_moveto(0)

    def _desplazar(self, evento: tk.Event) -> None:
        if not self._barra.winfo_ismapped() or not self.winfo_ismapped():
            return
        debajo = self.winfo_containing(evento.x_root, evento.y_root)
        if debajo is None or not str(debajo).startswith(str(self)):
            return
        if evento.num == 4:
            paso = -3
        elif evento.num == 5:
            paso = 3
        else:
            paso = (-1 if evento.delta > 0 else 1) * (1 if abs(evento.delta) < 120 else 3)
        self._lienzo.yview_scroll(paso, "units")
