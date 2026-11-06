# ==============================================================================
# Archivo  : src/generador_croquis/view/ventana_principal.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v2.3.0 | 2026-11-06 | Selector «Uso» (opcional): el uso de cada unidad
#          |            | aparece en las convenciones.
#   v2.2.0 | 2026-11-05 | Opción «El campo indica: piso de la unidad / total
#          |            | de pisos», propuesta al elegir el campo de pisos.
#   v2.1.0 | 2026-11-05 | Página Generador desplazable (pantallas bajas); el
#          |            | resumen sigue al campo identificador elegido.
#          |            | Sección «Acotado» en la tarjeta de campos: casilla
#          |            | «Acotar solo vértices principales» y tolerancia (m).
#   v2.0.0 | 2026-11-05 | Rediseño Material Design 3: barra superior con logo
#          |            | y versión, navegación con indicador (Generador /
#          |            | Ayuda / Acerca de), flujo en tarjetas numeradas,
#          |            | resumen en tabla, barra de estado con progreso
#          |            | lineal, icono de la aplicación y textos revisados.
#   v1.1.0 | 2026-11-05 | Organiza la ventana en pestañas (ttk.Notebook):
#          |            | "Generador" y "Acerca de" (PestanaAcercaDe).
#   v1.0.0 | 2026-11-05 | Creación. Vista pasiva extraída de
#          |            | AplicacionCroquis: solo construye widgets, reenvía
#          |            | eventos al controlador e implementa VistaCroquis.
#          |            | Muestra la versión de la app en el título.
# ==============================================================================
"""Ventana principal de la aplicación (vista del patrón MVC)."""

from __future__ import annotations

import sys
import tkinter as tk
from collections.abc import Sequence
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import TYPE_CHECKING

from PIL import Image, ImageTk

from generador_croquis import __app_name__, __version__
from generador_croquis.config import (
    ARCHIVO_ICONO_ICO,
    ARCHIVO_LOGO,
    FORMATOS_EXPORTACION,
    OPCION_NINGUNO,
    TOLERANCIA_MAXIMA,
    TOLERANCIA_PRINCIPALES,
)
from generador_croquis.domain.models import SignificadoPisos
from generador_croquis.view.componentes import (
    BarraNavegacion,
    CampoSeleccion,
    Chip,
    PaginaDesplazable,
    TablaClaveValor,
    Tarjeta,
)
from generador_croquis.view.dialogos import DialogoSeleccion, VentanaFigura
from generador_croquis.view.estilos import TemaMaterial, centrar
from generador_croquis.view.pestana_acerca_de import PestanaAcercaDe
from generador_croquis.view.pestana_ayuda import PestanaAyuda

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from generador_croquis.controller.controlador import ControladorCroquis

SIN_ARCHIVO = "Ningún archivo seleccionado"


def aplicar_icono(ventana: tk.Tk | tk.Toplevel) -> list[ImageTk.PhotoImage]:
    """Pone el logo como icono de la ventana. Devuelve las imágenes para retenerlas."""
    imagenes: list[ImageTk.PhotoImage] = []
    try:
        if sys.platform == "win32" and ARCHIVO_ICONO_ICO.is_file():
            ventana.iconbitmap(default=str(ARCHIVO_ICONO_ICO))
        if ARCHIVO_LOGO.is_file():
            logo = Image.open(ARCHIVO_LOGO)
            imagenes = [
                ImageTk.PhotoImage(logo.resize((s, s), Image.LANCZOS), master=ventana)
                for s in (256, 64, 32, 16)
            ]
            ventana.iconphoto(True, *imagenes)
    except (tk.TclError, OSError):
        pass
    return imagenes


class VentanaPrincipal:
    """Implementación Tkinter de :class:`~generador_croquis.controller.VistaCroquis`."""

    def __init__(self, root: tk.Tk, tema: TemaMaterial | None = None):
        self.root = root
        self.tema = tema or TemaMaterial(root)
        self._controlador: ControladorCroquis | None = None
        self._ventana_figura: VentanaFigura | None = None
        self._iconos = aplicar_icono(root)

        self.root.title(f"{__app_name__} {__version__}")
        self.root.minsize(880, 560)
        centrar(root, 1060, 860)

        self.ruta_archivo = tk.StringVar(value=SIN_ARCHIVO)
        self.campo_id = tk.StringVar()
        self.campo_pisos = tk.StringVar()
        self.campo_uso = tk.StringVar()
        self.significado_pisos = tk.StringVar(value=SignificadoPisos.TOTAL.value)
        self.solo_principales = tk.BooleanVar(value=True)
        self.tolerancia = tk.StringVar(value=f"{TOLERANCIA_PRINCIPALES:.2f}")
        self.estado = tk.StringVar()
        self._construir()

    def conectar(self, controlador: ControladorCroquis) -> None:
        self._controlador = controlador
        self.root.protocol("WM_DELETE_WINDOW", self._al_cerrar)
        controlador.iniciar()

    # ── construcción de widgets ──────────────────────────────────────────────

    def _construir(self) -> None:
        self._barra_superior().pack(side=tk.TOP, fill=tk.X)

        contenido = ttk.Frame(self.root)
        self.navegacion = BarraNavegacion(self.root, contenido, self._al_cambiar_pestana)
        self.navegacion.pack(side=tk.TOP, fill=tk.X)
        self._barra_estado().pack(side=tk.BOTTOM, fill=tk.X)
        contenido.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.generador = self._pagina_generador(contenido)
        self.ayuda = PestanaAyuda(contenido, self.tema)
        self.acerca_de = PestanaAcercaDe(contenido, self.tema)
        self.navegacion.agregar("generador", "Generador", self.generador)
        self.navegacion.agregar("ayuda", "Ayuda", self.ayuda)
        self.navegacion.agregar("acerca", "Acerca de", self.acerca_de)

    def _barra_superior(self) -> ttk.Frame:
        barra = ttk.Frame(self.root, style="AppBar.TFrame", padding=(20, 12))
        if ARCHIVO_LOGO.is_file():
            logo = Image.open(ARCHIVO_LOGO).resize((44, 44), Image.LANCZOS)
            self._logo = ImageTk.PhotoImage(logo, master=self.root)
            tk.Label(barra, image=self._logo, background=self.tema.c.primary, borderwidth=0).pack(
                side=tk.LEFT, padx=(0, 14)
            )
        textos = ttk.Frame(barra, style="AppBar.TFrame")
        textos.pack(side=tk.LEFT)
        ttk.Label(textos, text=__app_name__, style="AppTitle.TLabel").pack(anchor="w")
        ttk.Label(
            textos,
            text="Croquis técnicos acotados a partir de Shapefile, ZIP o GDB",
            style="AppSubtitle.TLabel",
        ).pack(anchor="w")
        Chip(barra, f"v{__version__}", "version").pack(side=tk.RIGHT)
        return barra

    def _barra_estado(self) -> ttk.Frame:
        barra = ttk.Frame(self.root, style="Status.TFrame")
        self.progreso = ttk.Progressbar(
            barra, mode="indeterminate", style="Material.Horizontal.TProgressbar"
        )
        self._linea_progreso = ttk.Frame(barra, style="Status.TFrame", height=4)
        self._linea_progreso.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(barra, textvariable=self.estado, style="Status.TLabel", padding=(20, 8)).pack(
            side=tk.LEFT
        )
        return barra

    def _pagina_generador(self, parent: ttk.Frame) -> ttk.Frame:
        desplazable = PaginaDesplazable(parent, self.tema.c.surface)
        pagina = ttk.Frame(desplazable.contenido, padding=(24, 14, 24, 12))
        pagina.pack(fill=tk.BOTH, expand=True)
        pagina.columnconfigure(0, weight=3, uniform="col")
        pagina.columnconfigure(1, weight=2, uniform="col")
        pagina.rowconfigure(1, weight=1)

        # 1. Datos de entrada
        entrada = Tarjeta(
            pagina,
            "1  Datos de entrada",
            "Abra un Shapefile (.shp), un archivo .zip que contenga shapefiles o "
            "geodatabases, o una carpeta File Geodatabase (.gdb).",
        )
        entrada.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        cuerpo = entrada.cuerpo
        cuerpo.columnconfigure(0, weight=1)
        self.entrada_ruta = ttk.Entry(cuerpo, textvariable=self.ruta_archivo, state="readonly")
        self.entrada_ruta.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        ttk.Button(
            cuerpo, text="Abrir archivo…", style="Filled.TButton", command=self._buscar_archivo
        ).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(
            cuerpo,
            text="Abrir carpeta GDB…",
            style="OutlinedCard.TButton",
            command=self._buscar_gdb,
        ).grid(row=0, column=2)

        # 2. Campos
        campos = Tarjeta(
            pagina,
            "2  Campos de la capa",
            "Indique cómo se agrupan los polígonos, de dónde salen los pisos y el uso.",
        )
        campos.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        campos.cuerpo.columnconfigure(0, weight=1)
        self.selector_id = CampoSeleccion(
            campos.cuerpo,
            "Identificador de la construcción",
            "Los polígonos con el mismo valor se dibujan juntos como una sola construcción. "
            f"Con {OPCION_NINGUNO} se dibuja un croquis por polígono.",
            self.campo_id,
        )
        self.selector_id.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self.selector_id.combo.bind("<<ComboboxSelected>>", self._al_cambiar_agrupacion)
        self.selector_pisos = CampoSeleccion(
            campos.cuerpo,
            "Pisos",
            "Piso de la unidad (p. ej. PLANTA_UBICACION): cada piso con su color y leyenda. "
            "Total de pisos (p. ej. NUMERO_PISOS): se muestra en el título.",
            self.campo_pisos,
        )
        self.selector_pisos.grid(row=1, column=0, sticky="ew")
        self.selector_pisos.combo.bind("<<ComboboxSelected>>", self._al_cambiar_campo_pisos)
        self._fila_significado(campos.cuerpo).grid(row=2, column=0, sticky="ew", pady=(6, 0))
        self.selector_uso = CampoSeleccion(
            campos.cuerpo,
            "Uso",
            "Uso de cada unidad (p. ej. USO). Se muestra en las convenciones de cada piso; "
            "en una GDB, con la descripción de su dominio.",
            self.campo_uso,
        )
        self.selector_uso.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        self._seccion_acotado(campos.cuerpo).grid(row=4, column=0, sticky="ew", pady=(12, 0))

        # Resumen
        resumen = Tarjeta(pagina, "Resumen de la capa")
        resumen.grid(row=1, column=1, sticky="nsew")
        self.tabla_resumen = TablaClaveValor(
            resumen.cuerpo, "Aquí aparecerán los datos del archivo cuando lo abra."
        )
        self.tabla_resumen.pack(fill=tk.BOTH, expand=True)

        # 3. Acciones
        acciones = ttk.Frame(pagina)
        acciones.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Label(acciones, text="3  Genere y exporte los croquis", style="Body.TLabel").pack(
            side=tk.LEFT
        )
        self.btn_guardar = ttk.Button(
            acciones,
            text="Exportar imagen…",
            style="Tonal.TButton",
            command=self._guardar,
            state="disabled",
        )
        self.btn_guardar.pack(side=tk.RIGHT)
        self.btn_generar = ttk.Button(
            acciones,
            text="Generar croquis",
            style="Filled.TButton",
            command=self._generar,
            state="disabled",
        )
        self.btn_generar.pack(side=tk.RIGHT, padx=(0, 10))
        return desplazable

    def _fila_significado(self, parent: ttk.Frame) -> ttk.Frame:
        fila = ttk.Frame(parent, style="CardInner.TFrame")
        ttk.Label(fila, text="El campo indica:", style="CardBody.TLabel").pack(
            side=tk.LEFT, padx=(0, 10)
        )
        self._opciones_significado = [
            ttk.Radiobutton(
                fila,
                text=texto,
                value=valor.value,
                variable=self.significado_pisos,
                style="Card.TRadiobutton",
            )
            for texto, valor in (
                ("Piso de la unidad", SignificadoPisos.UBICACION),
                ("Total de pisos", SignificadoPisos.TOTAL),
            )
        ]
        for opcion in self._opciones_significado:
            opcion.pack(side=tk.LEFT, padx=(0, 14))
            opcion.state(["disabled"])
        return fila

    def _al_cambiar_campo_pisos(self, _evento: tk.Event | None = None) -> None:
        if self._controlador:
            self._controlador.cambiar_campo_pisos(self.campo_pisos.get())

    def _seccion_acotado(self, parent: ttk.Frame) -> ttk.Frame:
        marco = ttk.Frame(parent, style="CardInner.TFrame")
        marco.columnconfigure(1, weight=1)
        ttk.Frame(marco, style="Divider.TFrame", height=1).grid(
            row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10)
        )
        ttk.Label(marco, text="Acotado", style="Key.TLabel").grid(row=1, column=0, sticky="w")
        ttk.Checkbutton(
            marco,
            text="Acotar solo vértices principales",
            variable=self.solo_principales,
            style="Card.TCheckbutton",
            command=self._al_cambiar_acotado,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))
        fila = ttk.Frame(marco, style="CardInner.TFrame")
        fila.grid(row=2, column=2, sticky="e", pady=(6, 0))
        ttk.Label(fila, text="Tolerancia", style="CardBody.TLabel").pack(side=tk.LEFT, padx=(0, 8))
        self.campo_tolerancia = ttk.Spinbox(
            fila,
            textvariable=self.tolerancia,
            from_=0.0,
            to=TOLERANCIA_MAXIMA,
            increment=0.05,
            width=6,
            justify="right",
        )
        self.campo_tolerancia.pack(side=tk.LEFT)
        ttk.Label(fila, text="m", style="CardBody.TLabel").pack(side=tk.LEFT, padx=(6, 0))
        ttk.Label(
            marco,
            text="Los vértices que se apartan menos que la tolerancia de la recta entre "
            "esquinas se consideran de ajuste: no se acotan y el lado mide la suma de sus "
            "tramos.",
            style="Helper.TLabel",
            wraplength=520,
            justify="left",
        ).grid(row=3, column=0, columnspan=3, sticky="w", pady=(6, 0))
        return marco

    def _al_cambiar_agrupacion(self, _evento: tk.Event | None = None) -> None:
        if self._controlador:
            self._controlador.cambiar_agrupacion(self.campo_id.get())

    def _al_cambiar_acotado(self) -> None:
        self.campo_tolerancia.state(["!disabled"] if self.solo_principales.get() else ["disabled"])

    # ── eventos de usuario → controlador ─────────────────────────────────────

    def _al_cambiar_pestana(self, clave: str) -> None:
        if clave == "ayuda":
            self.ayuda.al_mostrarse()

    def _buscar_archivo(self) -> None:
        ruta = filedialog.askopenfilename(
            parent=self.root,
            title="Abrir Shapefile o ZIP",
            filetypes=[
                ("Shapefile o ZIP", "*.zip *.shp"),
                ("Archivos ZIP", "*.zip"),
                ("Shapefile", "*.shp"),
                ("Todos los archivos", "*.*"),
            ],
        )
        self._cargar(ruta)

    def _buscar_gdb(self) -> None:
        self._cargar(filedialog.askdirectory(parent=self.root, title="Seleccione la carpeta .gdb"))

    def _cargar(self, ruta: str) -> None:
        if ruta and self._controlador:
            self.ruta_archivo.set(ruta)
            self.entrada_ruta.xview_moveto(1.0)  # muestra el nombre del archivo, no el inicio
            self._controlador.cargar_archivo(ruta)

    def _generar(self) -> None:
        if self._controlador:
            self._controlador.generar(
                self.campo_id.get(),
                self.campo_pisos.get(),
                self.solo_principales.get(),
                self.tolerancia.get(),
                self.significado_pisos.get(),
                self.campo_uso.get(),
            )

    def _guardar(self) -> None:
        if self._controlador:
            origen = Path(self.ruta_archivo.get())
            ruta = filedialog.asksaveasfilename(
                parent=self.root,
                title="Exportar croquis",
                defaultextension=".png",
                initialfile=f"croquis_{origen.stem}" if origen.stem else "croquis",
                filetypes=list(FORMATOS_EXPORTACION),
            )
            self._controlador.guardar(ruta)

    def _al_cerrar(self) -> None:
        if self._controlador:
            self._controlador.cerrar()
        self.root.destroy()

    # ── implementación de VistaCroquis ───────────────────────────────────────

    def mostrar_estado(self, texto: str) -> None:
        self.estado.set(texto)
        self.root.update_idletasks()

    def mostrar_resumen(self, filas: Sequence[tuple[str, str]], avisos: Sequence[str]) -> None:
        self.tabla_resumen.mostrar(filas, avisos)
        if not filas:
            self.ruta_archivo.set(SIN_ARCHIVO)

    def mostrar_error(self, titulo: str, mensaje: str) -> None:
        messagebox.showerror(titulo, mensaje, parent=self.root)

    def mostrar_aviso(self, titulo: str, mensaje: str) -> None:
        messagebox.showwarning(titulo, mensaje, parent=self.root)

    def mostrar_exito(self, titulo: str, mensaje: str) -> None:
        messagebox.showinfo(titulo, mensaje, parent=self.root)

    def confirmar(self, titulo: str, mensaje: str) -> bool:
        return messagebox.askyesno(titulo, mensaje, parent=self.root)

    def seleccionar_opcion(self, titulo: str, mensaje: str, opciones: Sequence[str]) -> str | None:
        return DialogoSeleccion(self.root, self.tema, titulo, mensaje, opciones).mostrar()

    def configurar_campos(
        self,
        campos: Sequence[str],
        campo_id: str | None,
        campo_pisos: str | None,
        nota_id: str,
        nota_pisos: str,
        campo_uso: str | None = None,
        nota_uso: str = "Opcional",
    ) -> None:
        valores = [OPCION_NINGUNO, *campos]
        self.selector_id.configurar(valores, nota_id, campo_id is not None)
        self.selector_pisos.configurar(valores, nota_pisos, campo_pisos is not None)
        self.selector_uso.configurar(valores, nota_uso, campo_uso is not None)
        self.campo_id.set(campo_id or OPCION_NINGUNO)
        self.campo_pisos.set(campo_pisos or OPCION_NINGUNO)
        self.campo_uso.set(campo_uso or OPCION_NINGUNO)

    def mostrar_significado_pisos(self, significado: SignificadoPisos, habilitado: bool) -> None:
        self.significado_pisos.set(significado.value)
        for opcion in self._opciones_significado:
            opcion.state(["!disabled"] if habilitado else ["disabled"])

    def habilitar_generar(self, habilitado: bool) -> None:
        self.btn_generar["state"] = "normal" if habilitado else "disabled"

    def habilitar_guardar(self, habilitado: bool) -> None:
        self.btn_guardar["state"] = "normal" if habilitado else "disabled"

    def ocupado(self, activo: bool) -> None:
        if activo:
            self._linea_progreso.pack_forget()
            self.progreso.pack(side=tk.TOP, fill=tk.X, before=self._primer_hijo_estado())
            self.progreso.start(12)
            self.root.config(cursor="watch")
        else:
            self.progreso.stop()
            self.progreso.pack_forget()
            self._linea_progreso.pack(side=tk.TOP, fill=tk.X, before=self._primer_hijo_estado())
            self.root.config(cursor="")
        self.root.update_idletasks()

    def _primer_hijo_estado(self) -> tk.Misc:
        return next(h for h in self.progreso.master.winfo_children() if isinstance(h, ttk.Label))

    def mostrar_figura(self, figura: Figure) -> None:
        self.cerrar_figura()
        nombre = Path(self.ruta_archivo.get()).name
        self._ventana_figura = VentanaFigura(self.root, figura, titulo=f"Croquis — {nombre}")

    def cerrar_figura(self) -> None:
        if self._ventana_figura is not None:
            self._ventana_figura.cerrar()
            self._ventana_figura = None
