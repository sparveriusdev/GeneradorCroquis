# ==============================================================================
# Archivo  : src/generador_croquis/view/markdown_tk.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.2 | 2026-11-05 | La numeración de listas no cuenta las sub-viñetas.
#   v1.0.1 | 2026-11-05 | Párrafos de una cita separados por un solo salto
#          |            | (los avisos de GitHub quedaban con un hueco).
#   v1.0.0 | 2026-11-05 | Creación. Dibuja un Documento Markdown en un
#          |            | tk.Text con estilos Material: títulos, listas,
#          |            | tablas, citas, código, imágenes y enlaces (internos
#          |            | con desplazamiento a la sección, externos al
#          |            | navegador). Se redibuja al cambiar el ancho.
# ==============================================================================
"""Visor de Markdown para Tkinter."""

from __future__ import annotations

import tkinter as tk
import webbrowser
from collections.abc import Callable
from pathlib import Path
from tkinter import ttk

from PIL import Image, ImageTk

from generador_croquis.services.markdown import (
    BloqueCodigo,
    Cita,
    Documento,
    Encabezado,
    Fragmento,
    Imagen,
    Linea,
    Lista,
    Parrafo,
    Separador,
    Tabla,
    texto_plano,
)
from generador_croquis.view.estilos import TemaMaterial

MARGEN = 36
ANCHO_MAXIMO_IMAGEN = 900


class VisorMarkdown(ttk.Frame):
    """Texto de solo lectura con barra de desplazamiento que muestra Markdown."""

    def __init__(
        self,
        parent: tk.Misc,
        tema: TemaMaterial,
        resolver_imagen: Callable[[str], Path | None] | None = None,
    ):
        super().__init__(parent, style="CardInner.TFrame")
        self._tema = tema
        self._resolver_imagen = resolver_imagen or (lambda _r: None)
        self._documento: Documento | None = None
        self._url_base = ""
        self._imagenes: list[ImageTk.PhotoImage] = []
        self._fuentes: dict[str, tuple] = {}
        self._enlaces = 0
        self._ultimo_ancho = 0
        self._redibujo: str | None = None

        c = tema.c
        self.texto = tk.Text(
            self,
            wrap="word",
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            background=c.surface_container_lowest,
            foreground=c.on_surface,
            padx=MARGEN,
            pady=24,
            cursor="arrow",
            font=tema.t.body_large,
            selectbackground=c.primary_container,
            insertwidth=0,
        )
        barra = ttk.Scrollbar(
            self, orient="vertical", command=self.texto.yview, style="Material.Vertical.TScrollbar"
        )
        self.texto.configure(yscrollcommand=barra.set)
        barra.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 4), pady=4)
        self.texto.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._configurar_etiquetas()
        self.texto.bind("<Configure>", self._al_redimensionar)
        self.texto.configure(state="disabled")

    # ── estilos de texto ─────────────────────────────────────────────────────

    def _configurar_etiquetas(self) -> None:
        c, t, txt = self._tema.c, self._tema.t, self.texto
        familia = t.familia
        txt.tag_configure(
            "h1", font=(familia, 22), foreground=c.on_surface, spacing1=4, spacing3=14
        )
        txt.tag_configure("h2", font=(familia, 16), foreground=c.primary, spacing1=22, spacing3=8)
        txt.tag_configure("h3", font=t.media(12), foreground=c.on_surface, spacing1=14, spacing3=6)
        txt.tag_configure("p", spacing1=2, spacing3=10, lmargin1=0, lmargin2=0)
        txt.tag_configure("li", tabs=("34",), spacing1=2, spacing3=4, lmargin1=14, lmargin2=34)
        txt.tag_configure("li2", tabs=("58",), spacing1=1, spacing3=3, lmargin1=40, lmargin2=58)
        txt.tag_configure("bala", foreground=c.primary)
        fondo_cita = TemaMaterial.mezclar(c.surface_container_lowest, c.primary_container, 0.6)
        txt.tag_configure(
            "cita",
            background=fondo_cita,
            lmargin1=16,
            lmargin2=16,
            rmargin=16,
            spacing1=8,
            spacing3=8,
            foreground=c.on_primary_container,
        )
        txt.tag_configure(
            "codigo_bloque",
            font=t.mono,
            background=c.surface_container,
            lmargin1=16,
            lmargin2=16,
            spacing1=6,
            spacing3=10,
        )
        txt.tag_configure("enlace", foreground=c.primary, underline=True)
        txt.tag_configure("centro", justify="center", spacing3=12)
        txt.tag_configure("hr", font=(familia, 4), spacing3=8)
        txt.tag_bind("enlace", "<Enter>", lambda _e: txt.configure(cursor="hand2"))
        txt.tag_bind("enlace", "<Leave>", lambda _e: txt.configure(cursor="arrow"))

    def _etiqueta_fuente(self, f: Fragmento, base: str) -> str:
        t, c = self._tema.t, self._tema.c
        tamanos = {"h1": 22, "h2": 16, "h3": 12, "cita": 11, "cuerpo": 11}
        tamano = tamanos.get(base, 11)
        nombre = f"f-{base}-{int(f.negrita)}{int(f.cursiva)}{int(f.codigo)}"
        if nombre not in self._fuentes:
            if f.codigo:
                fuente: tuple = (t.familia_mono, tamano - 1)
            else:
                # El tag de fragmento manda sobre el del bloque: h3 lleva aquí su peso medio.
                base_fuente = t.media(tamano) if base == "h3" else (t.familia, tamano)
                estilo = " ".join(x for x, ok in (("bold", f.negrita), ("italic", f.cursiva)) if ok)
                fuente = (base_fuente[0], tamano, estilo) if estilo else base_fuente
            self._fuentes[nombre] = fuente
            opciones: dict = {"font": fuente}
            if f.codigo:
                opciones["background"] = c.surface_container
            self.texto.tag_configure(nombre, **opciones)
            self.texto.tag_lower(nombre)  # que no tape fondos de bloque
        return nombre

    # ── API ──────────────────────────────────────────────────────────────────

    def mostrar(self, documento: Documento, url_base: str = "") -> None:
        self._documento = documento
        self._url_base = url_base
        self._dibujar()
        self.texto.yview_moveto(0)

    def mostrar_mensaje(self, texto: str) -> None:
        self._documento = None
        self.texto.configure(state="normal")
        self.texto.delete("1.0", tk.END)
        self.texto.insert(tk.END, texto, ("p",))
        self.texto.configure(state="disabled")

    # ── dibujo ───────────────────────────────────────────────────────────────

    def _al_redimensionar(self, evento: tk.Event) -> None:
        if abs(evento.width - self._ultimo_ancho) < 40 or self._documento is None:
            return
        if self._redibujo:
            self.after_cancel(self._redibujo)
        self._redibujo = self.after(250, self._redibujar_conservando_posicion)

    def _redibujar_conservando_posicion(self) -> None:
        posicion = self.texto.yview()[0]
        self._dibujar()
        self.texto.yview_moveto(posicion)

    def _ancho_util(self) -> int:
        self._ultimo_ancho = max(self.texto.winfo_width(), 400)
        return self._ultimo_ancho - 2 * MARGEN - 8

    def _dibujar(self) -> None:
        if self._documento is None:
            return
        txt = self.texto
        txt.configure(state="normal")
        txt.delete("1.0", tk.END)
        for ventana in txt.window_names():
            txt.nametowidget(ventana).destroy()
        for marca in txt.mark_names():
            if marca.startswith("ancla-"):
                txt.mark_unset(marca)
        self._imagenes.clear()
        ancho = self._ancho_util()
        for bloque in self._documento.bloques:
            self._dibujar_bloque(bloque, ancho)
        txt.configure(state="disabled")

    def _insertar_linea(self, linea: Linea, etiquetas: tuple[str, ...], base: str) -> None:
        for f in linea:
            tags = (*etiquetas, self._etiqueta_fuente(f, base))
            if f.enlace:
                tags = (*tags, "enlace", self._etiqueta_enlace(f.enlace))
            self.texto.insert(tk.END, f.texto, tags)

    def _etiqueta_enlace(self, url: str) -> str:
        self._enlaces += 1
        nombre = f"enlace-{self._enlaces}"
        self.texto.tag_bind(nombre, "<Button-1>", lambda _e: self._abrir_enlace(url))
        return nombre

    def _abrir_enlace(self, url: str) -> None:
        if url.startswith("#"):
            marca = f"ancla-{url[1:]}"
            if marca in self.texto.mark_names():
                self.texto.yview(marca)
            return
        if not url.startswith(("http://", "https://", "mailto:")):
            url = self._url_base + url
        webbrowser.open(url)

    def _dibujar_bloque(self, bloque, ancho: int) -> None:
        txt = self.texto
        if isinstance(bloque, Encabezado):
            etiqueta = f"h{min(bloque.nivel, 3)}"
            txt.mark_set(f"ancla-{bloque.ancla}", tk.END + "-1c")
            txt.mark_gravity(f"ancla-{bloque.ancla}", "left")
            self._insertar_linea(bloque.contenido, (etiqueta,), etiqueta)
            txt.insert(tk.END, "\n", (etiqueta,))
        elif isinstance(bloque, Parrafo):
            self._insertar_linea(bloque.contenido, ("p",), "cuerpo")
            txt.insert(tk.END, "\n", ("p",))
        elif isinstance(bloque, Lista):
            numero = bloque.inicio - 1
            for elemento in bloque.elementos:
                anidado = elemento and elemento[0].texto.startswith("◦ ")
                if not anidado:  # las sub-viñetas no cuentan en la numeración
                    numero += 1
                if anidado:
                    primero = Fragmento(
                        elemento[0].texto[2:],
                        elemento[0].negrita,
                        elemento[0].cursiva,
                        elemento[0].codigo,
                        elemento[0].enlace,
                    )
                    elemento = (primero, *elemento[1:])
                tag = "li2" if anidado else "li"
                marcador = "–\t" if anidado else (f"{numero}.\t" if bloque.ordenada else "•\t")
                txt.insert(tk.END, marcador, (tag, "bala"))
                self._insertar_linea(elemento, (tag,), "cuerpo")
                txt.insert(tk.END, "\n", (tag,))
            txt.insert(tk.END, "\n", ("hr",))
        elif isinstance(bloque, Cita):
            for parrafo in bloque.contenido:
                self._insertar_linea(parrafo, ("cita",), "cita")
                txt.insert(tk.END, "\n", ("cita",))  # el tag ya separa los párrafos
            txt.insert(tk.END, "\n", ("hr",))
        elif isinstance(bloque, BloqueCodigo):
            txt.insert(tk.END, bloque.texto + "\n", ("codigo_bloque",))
        elif isinstance(bloque, Tabla):
            txt.window_create(tk.END, window=self._crear_tabla(bloque, ancho))
            txt.insert(tk.END, "\n", ("p",))
        elif isinstance(bloque, Imagen):
            self._insertar_imagen(bloque, ancho)
        elif isinstance(bloque, Separador):
            txt.insert(tk.END, "\n", ("hr",))

    def _insertar_imagen(self, bloque: Imagen, ancho: int) -> None:
        txt = self.texto
        ruta = self._resolver_imagen(bloque.ruta)
        if ruta is None:
            frag = Fragmento(
                f"🖼  {bloque.alternativo or bloque.ruta} (ver en línea)", enlace=bloque.ruta
            )
            self._insertar_linea((frag,), ("centro",), "cuerpo")
            txt.insert(tk.END, "\n", ("centro",))
            return
        img = Image.open(ruta)
        limite = min(ancho, ANCHO_MAXIMO_IMAGEN, img.width)
        if img.width > limite:
            img = img.resize((limite, round(img.height * limite / img.width)), Image.LANCZOS)
        foto = ImageTk.PhotoImage(img, master=self)
        self._imagenes.append(foto)
        txt.insert(tk.END, "", ("centro",))
        txt.image_create(tk.END, image=foto)
        txt.insert(tk.END, "\n", ("centro",))
        if bloque.alternativo:
            frag = Fragmento(bloque.alternativo, cursiva=True)
            self._insertar_linea((frag,), ("centro",), "cuerpo")
            txt.insert(tk.END, "\n", ("centro",))

    def _crear_tabla(self, tabla: Tabla, ancho: int) -> tk.Frame:
        c, t = self._tema.c, self._tema.t
        columnas = len(tabla.cabecera)
        largos = [
            max(
                [len(texto_plano(tabla.cabecera[i]))]
                + [len(texto_plano(f[i])) for f in tabla.filas if i < len(f)]
            )
            for i in range(columnas)
        ]
        pesos = [min(max(n, 8), 60) for n in largos]
        anchos = [max(int(ancho * p / sum(pesos)) - 2, 60) for p in pesos]

        marco = tk.Frame(self.texto, background=c.outline_variant, padx=1, pady=1)
        for fila, celdas in enumerate((tabla.cabecera, *tabla.filas)):
            cabecera = fila == 0
            fondo = c.surface_container if cabecera else c.surface_container_lowest
            for col in range(columnas):
                contenido = celdas[col] if col < len(celdas) else ()
                etiqueta = tk.Label(
                    marco,
                    text=texto_plano(contenido),
                    justify="left",
                    anchor="nw",
                    wraplength=anchos[col] - 20,
                    background=fondo,
                    foreground=c.on_surface,
                    font=t.label_large if cabecera else t.body_medium,
                    padx=10,
                    pady=7,
                )
                enlaces = [f.enlace for f in contenido if f.enlace]
                if enlaces:
                    etiqueta.configure(foreground=c.primary, cursor="hand2")
                    etiqueta.bind("<Button-1>", lambda _e, u=enlaces[0]: self._abrir_enlace(u))
                etiqueta.grid(
                    row=fila,
                    column=col,
                    sticky="nsew",
                    padx=(0 if col == 0 else 1, 0),
                    pady=(0 if fila == 0 else 1, 0),
                )
        for col, w in enumerate(anchos):
            marco.grid_columnconfigure(col, minsize=w)
        # La rueda del ratón sobre la tabla debe desplazar el documento.
        for hijo in (marco, *marco.winfo_children()):
            hijo.bind(
                "<MouseWheel>",
                lambda e: self.texto.yview_scroll(
                    int(-e.delta / (120 if abs(e.delta) >= 120 else 1)), "units"
                ),
            )
            hijo.bind("<Button-4>", lambda _e: self.texto.yview_scroll(-3, "units"))
            hijo.bind("<Button-5>", lambda _e: self.texto.yview_scroll(3, "units"))
        return marco
