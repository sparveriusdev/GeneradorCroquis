# ==============================================================================
# Archivo  : src/generador_croquis/view/ventana_principal.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.1.0 | 2026-11-05 | Organiza la ventana en pestañas (ttk.Notebook):
#          |            | "Generador" y "Acerca de" (PestanaAcercaDe).
#   v1.0.0 | 2026-11-05 | Creación. Vista pasiva extraída de
#          |            | AplicacionCroquis: solo construye widgets, reenvía
#          |            | eventos al controlador e implementa VistaCroquis.
#          |            | Muestra la versión de la app en el título.
# ==============================================================================
"""Ventana principal de la aplicación (vista del patrón MVC)."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Sequence
from tkinter import filedialog, messagebox, ttk
from typing import TYPE_CHECKING

from generador_croquis import __app_name__, __version__
from generador_croquis.config import FORMATOS_EXPORTACION, OPCION_NINGUNO
from generador_croquis.view.dialogos import DialogoSeleccion, VentanaFigura
from generador_croquis.view.estilos import FUENTE, FUENTE_MONO, aplicar_estilos, centrar
from generador_croquis.view.pestana_acerca_de import PestanaAcercaDe

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from generador_croquis.controller.controlador import ControladorCroquis


class VentanaPrincipal:
    """Implementación Tkinter de :class:`~generador_croquis.controller.VistaCroquis`."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self._controlador: ControladorCroquis | None = None
        self._ventana_figura: VentanaFigura | None = None

        self.root.title(f"{__app_name__} v{__version__}")
        self.root.minsize(640, 560)
        aplicar_estilos(root)
        centrar(root, 800, 740)

        self.ruta_archivo = tk.StringVar()
        self.campo_id = tk.StringVar()
        self.campo_pisos = tk.StringVar()
        self._construir()

    def conectar(self, controlador: ControladorCroquis) -> None:
        self._controlador = controlador
        self.root.protocol("WM_DELETE_WINDOW", self._al_cerrar)

    # ── construcción de widgets ──────────────────────────────────────────────

    def _construir(self) -> None:
        self.pestanas = ttk.Notebook(self.root)
        self.pestanas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        main = ttk.Frame(self.pestanas, padding=20)
        self.pestanas.add(main, text="  Generador  ")
        self.acerca_de = PestanaAcercaDe(self.pestanas)
        self.pestanas.add(self.acerca_de, text="  Acerca de  ")

        ttk.Label(main, text=__app_name__, style="Title.TLabel").pack(pady=(0, 2))
        ttk.Label(
            main,
            text="Genera croquis técnicos desde Shapefile (.zip / .shp) o GDB (.gdb)",
            style="Subtitle.TLabel",
        ).pack(pady=(0, 15))

        f_arch = self._seccion(main, "Archivo de entrada")
        fila = ttk.Frame(f_arch)
        fila.pack(fill=tk.X)
        ttk.Entry(fila, textvariable=self.ruta_archivo, font=(FUENTE, 9), state="readonly").pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10)
        )
        ttk.Button(
            fila, text="Buscar archivo...", style="Browse.TButton", command=self._buscar_archivo
        ).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(
            fila, text="Abrir GDB...", style="Browse.TButton", command=self._buscar_gdb
        ).pack(side=tk.RIGHT)

        f_conf = self._seccion(main, "Configuración")
        self.combo_id, self.nota_id = self._fila_combo(
            f_conf, "Campo identificador (agrupar):", self.campo_id
        )
        self.combo_pisos, self.nota_pisos = self._fila_combo(
            f_conf, "Campo de pisos:", self.campo_pisos
        )

        f_info = self._seccion(main, "Información del archivo")
        self.text_info = tk.Text(
            f_info,
            height=9,
            font=(FUENTE_MONO, 9),
            bg="#ffffff",
            fg="#495057",
            relief="flat",
            padx=10,
            pady=10,
            state="disabled",
            wrap="word",
        )
        self.text_info.pack(fill=tk.BOTH, expand=True)

        f_btn = ttk.Frame(main)
        f_btn.pack(fill=tk.X, pady=(10, 0))
        self.btn_generar = ttk.Button(
            f_btn,
            text="Generar Croquis",
            style="Action.TButton",
            command=self._generar,
            state="disabled",
        )
        self.btn_generar.pack(side=tk.LEFT, padx=(0, 10))
        self.btn_guardar = ttk.Button(
            f_btn,
            text="Guardar Imagen",
            style="Action.TButton",
            command=self._guardar,
            state="disabled",
        )
        self.btn_guardar.pack(side=tk.LEFT)

        self.progreso = ttk.Progressbar(main, mode="indeterminate")
        self.progreso.pack(fill=tk.X, pady=(10, 0))

    @staticmethod
    def _seccion(parent: tk.Misc, titulo: str) -> ttk.LabelFrame:
        marco = ttk.LabelFrame(
            parent, text=f"  {titulo}  ", style="Section.TLabelframe", padding=15
        )
        marco.pack(fill=tk.X, pady=(0, 10))
        return marco

    @staticmethod
    def _fila_combo(
        parent: tk.Misc, texto: str, variable: tk.StringVar
    ) -> tuple[ttk.Combobox, ttk.Label]:
        fila = ttk.Frame(parent)
        fila.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(fila, text=texto, width=30).pack(side=tk.LEFT, padx=(0, 10))
        combo = ttk.Combobox(fila, textvariable=variable, state="disabled", width=25)
        combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        nota = ttk.Label(fila, text="", style="Nota.TLabel")
        nota.pack(side=tk.LEFT, padx=(10, 0))
        return combo, nota

    # ── eventos de usuario → controlador ─────────────────────────────────────

    def _buscar_archivo(self) -> None:
        ruta = filedialog.askopenfilename(
            parent=self.root,
            title="Seleccionar archivo (.zip o .shp)",
            filetypes=[
                ("ZIP o Shapefile", "*.zip *.shp"),
                ("Archivos ZIP", "*.zip"),
                ("Archivos Shapefile", "*.shp"),
                ("Todos los archivos", "*.*"),
            ],
        )
        self._cargar(ruta)

    def _buscar_gdb(self) -> None:
        self._cargar(
            filedialog.askdirectory(parent=self.root, title="Seleccionar carpeta GDB (.gdb)")
        )

    def _cargar(self, ruta: str) -> None:
        if ruta and self._controlador:
            self.ruta_archivo.set(ruta)
            self._controlador.cargar_archivo(ruta)

    def _generar(self) -> None:
        if self._controlador:
            self._controlador.generar(self.campo_id.get(), self.campo_pisos.get())

    def _guardar(self) -> None:
        if self._controlador:
            ruta = filedialog.asksaveasfilename(
                parent=self.root,
                title="Guardar imagen",
                defaultextension=".png",
                filetypes=list(FORMATOS_EXPORTACION),
            )
            self._controlador.guardar(ruta)

    def _al_cerrar(self) -> None:
        if self._controlador:
            self._controlador.cerrar()
        self.root.destroy()

    # ── implementación de VistaCroquis ───────────────────────────────────────

    def mostrar_info(self, texto: str) -> None:
        self.text_info.config(state="normal")
        self.text_info.delete("1.0", tk.END)
        self.text_info.insert("1.0", texto)
        self.text_info.config(state="disabled")

    def mostrar_error(self, titulo: str, mensaje: str) -> None:
        messagebox.showerror(titulo, mensaje, parent=self.root)

    def mostrar_aviso(self, titulo: str, mensaje: str) -> None:
        messagebox.showwarning(titulo, mensaje, parent=self.root)

    def mostrar_exito(self, titulo: str, mensaje: str) -> None:
        messagebox.showinfo(titulo, mensaje, parent=self.root)

    def confirmar(self, titulo: str, mensaje: str) -> bool:
        return messagebox.askyesno(titulo, mensaje, parent=self.root)

    def seleccionar_opcion(self, titulo: str, mensaje: str, opciones: Sequence[str]) -> str | None:
        return DialogoSeleccion(self.root, titulo, mensaje, opciones).mostrar()

    def configurar_campos(
        self,
        campos: Sequence[str],
        campo_id: str | None,
        campo_pisos: str | None,
        nota_id: str,
        nota_pisos: str,
    ) -> None:
        valores = [OPCION_NINGUNO, *campos]
        for combo, var, valor, nota, texto in (
            (self.combo_id, self.campo_id, campo_id, self.nota_id, nota_id),
            (self.combo_pisos, self.campo_pisos, campo_pisos, self.nota_pisos, nota_pisos),
        ):
            combo["values"] = valores
            combo["state"] = "readonly"
            var.set(valor or OPCION_NINGUNO)
            nota.config(text=texto)

    def habilitar_generar(self, habilitado: bool) -> None:
        self.btn_generar["state"] = "normal" if habilitado else "disabled"

    def habilitar_guardar(self, habilitado: bool) -> None:
        self.btn_guardar["state"] = "normal" if habilitado else "disabled"

    def ocupado(self, activo: bool) -> None:
        if activo:
            self.progreso.start()
            self.root.config(cursor="watch")
        else:
            self.progreso.stop()
            self.root.config(cursor="")
        self.root.update_idletasks()

    def mostrar_figura(self, figura: Figure) -> None:
        self.cerrar_figura()
        self._ventana_figura = VentanaFigura(
            self.root, figura, titulo=f"Croquis — {self.ruta_archivo.get()}"
        )

    def cerrar_figura(self) -> None:
        if self._ventana_figura is not None:
            self._ventana_figura.cerrar()
            self._ventana_figura = None
