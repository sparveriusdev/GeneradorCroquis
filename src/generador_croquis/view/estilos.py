# ==============================================================================
# Archivo  : src/generador_croquis/view/estilos.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v2.2.0 | 2026-11-05 | Estilo de opción excluyente (Card.TRadiobutton).
#   v2.1.0 | 2026-11-05 | Estilos para casilla (Card.TCheckbutton) y campo
#          |            | numérico (TSpinbox) con contorno.
#   v2.0.0 | 2026-11-05 | Reescritura: tema Material Design 3 para ttk.
#          |            | Tokens de color y tipografía (Roboto), botones
#          |            | Filled / Tonal / Outlined / Text y tarjetas con
#          |            | esquinas redondeadas (imágenes generadas con
#          |            | Pillow), campos con contorno, progreso lineal,
#          |            | barras de desplazamiento delgadas.
#   v1.0.0 | 2026-11-05 | Creación. Estilos ttk y paleta de la interfaz,
#          |            | extraídos de AplicacionCroquis._crear_interfaz().
# ==============================================================================
"""Tema visual Material Design 3 para la interfaz Tkinter.

Todos los colores, tamaños y fuentes salen de :data:`COLORES` y :class:`Tipografia`;
ningún otro módulo de la vista debe usar valores literales.
"""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from dataclasses import dataclass
from tkinter import ttk

from PIL import Image, ImageDraw, ImageTk

from generador_croquis.view.fuentes import (
    FAMILIA_MEDIA,
    FAMILIA_MONO_PREFERIDAS,
    FAMILIA_PRINCIPAL,
    FAMILIAS_RESPALDO,
    elegir_familia,
)


@dataclass(frozen=True)
class Colores:
    """Esquema de color claro Material 3 derivado del azul del logo (#3397ED)."""

    primary: str = "#0061A4"
    on_primary: str = "#FFFFFF"
    primary_container: str = "#D1E4FF"
    on_primary_container: str = "#001D36"
    secondary_container: str = "#D7E3F7"
    on_secondary_container: str = "#101C2B"
    surface: str = "#F8F9FF"
    surface_container: str = "#ECEEF4"
    surface_container_lowest: str = "#FFFFFF"
    on_surface: str = "#191C20"
    on_surface_variant: str = "#43474E"
    outline: str = "#74777F"
    outline_variant: str = "#C4C6CF"
    error: str = "#BA1A1A"
    success: str = "#1E6B35"
    success_container: str = "#C8EFCF"
    warning_container: str = "#FFE8C2"
    on_warning_container: str = "#4A2800"
    disabled_container: str = "#E1E2E8"
    disabled_content: str = "#8F9199"


COLORES = Colores()


@dataclass(frozen=True)
class Tipografia:
    """Escala tipográfica Material adaptada a escritorio (tamaños en puntos)."""

    familia: str
    familia_media: str
    familia_mono: str

    def media(self, tamano: int) -> tuple:
        """Peso 500 de Material; si la familia Medium no existe se usa negrita."""
        if self.familia_media != self.familia:
            return (self.familia_media, tamano)
        return (self.familia, tamano, "bold")

    @property
    def headline(self) -> tuple:
        return (self.familia, 18)

    @property
    def title_large(self) -> tuple:
        return (self.familia, 15)

    @property
    def title_medium(self) -> tuple:
        return self.media(11)

    @property
    def body_large(self) -> tuple:
        return (self.familia, 11)

    @property
    def body_medium(self) -> tuple:
        return (self.familia, 10)

    @property
    def body_small(self) -> tuple:
        return (self.familia, 9)

    @property
    def label_large(self) -> tuple:
        return self.media(10)

    @property
    def label_medium(self) -> tuple:
        return self.media(9)

    @property
    def mono(self) -> tuple:
        return (self.familia_mono, 9)


class TemaMaterial:
    """Aplica el tema a una raíz Tk y conserva las imágenes que usa."""

    RADIO_BOTON = 18
    RADIO_TARJETA = 12

    def __init__(self, root: tk.Tk):
        self.root = root
        self.c = COLORES
        familia = elegir_familia(root, (FAMILIA_PRINCIPAL, *FAMILIAS_RESPALDO))
        media = elegir_familia(root, (FAMILIA_MEDIA, familia))
        self.t = Tipografia(familia, media, elegir_familia(root, FAMILIA_MONO_PREFERIDAS))
        self._imagenes: list[ImageTk.PhotoImage] = []  # evita que el GC las libere
        self.style = ttk.Style(root)
        self._aplicar()

    # ── imágenes redondeadas ─────────────────────────────────────────────────

    def _rect(
        self,
        relleno: str | None,
        radio: int,
        borde: str | None = None,
        ancho: int = 64,
        alto: int = 44,
    ) -> ImageTk.PhotoImage:
        escala = 4  # sobremuestreo para bordes suaves
        img = Image.new("RGBA", (ancho * escala, alto * escala), (0, 0, 0, 0))
        dibujo = ImageDraw.Draw(img)
        caja = (0, 0, ancho * escala - 1, alto * escala - 1)
        if relleno is None and borde is None:
            pass  # imagen totalmente transparente
        elif borde:
            dibujo.rounded_rectangle(caja, radio * escala, fill=borde)
            interior = (escala, escala, ancho * escala - 1 - escala, alto * escala - 1 - escala)
            dibujo.rounded_rectangle(interior, (radio - 1) * escala, fill=relleno or (0, 0, 0, 0))
        else:
            dibujo.rounded_rectangle(caja, radio * escala, fill=relleno)
        foto = ImageTk.PhotoImage(img.resize((ancho, alto), Image.LANCZOS), master=self.root)
        self._imagenes.append(foto)
        return foto

    @staticmethod
    def mezclar(base: str, capa: str, opacidad: float) -> str:
        """Superpone ``capa`` sobre ``base`` (capas de estado Material: hover 8 %, pressed 12 %)."""
        b = [int(base[i : i + 2], 16) for i in (1, 3, 5)]
        c = [int(capa[i : i + 2], 16) for i in (1, 3, 5)]
        return "#" + "".join(
            f"{round(x + (y - x) * opacidad):02x}" for x, y in zip(b, c, strict=True)
        )

    def _estilo_boton(
        self,
        nombre: str,
        relleno: str | None,
        texto: str,
        borde: str | None = None,
        fondo: str | None = None,
    ) -> None:
        """Crea un estilo de botón redondeado con estados hover / pressed / disabled."""
        c, r = self.c, self.RADIO_BOTON
        fondo = fondo or c.surface
        base = relleno or fondo
        lado = 2 * r + 4
        transparente = relleno is None and borde is None  # botón de texto

        def img(color: str | None, contorno: str | None = borde) -> ImageTk.PhotoImage:
            return self._rect(color, r, contorno, ancho=lado, alto=lado)

        normal = img(None if transparente else base)
        hover = img(self.mezclar(base, texto, 0.08))
        pressed = img(self.mezclar(base, texto, 0.12))
        disabled = img(
            None if transparente else (c.disabled_container if relleno else base),
            c.disabled_container if borde else None,
        )
        elemento = f"{nombre}.bg"
        self.style.element_create(
            elemento,
            "image",
            normal,
            ("disabled", disabled),
            ("pressed", pressed),
            ("active", hover),
            border=r + 1,
            padding=(20, 10),
            sticky="nsew",
        )
        self.style.layout(
            f"{nombre}.TButton",
            [
                (
                    elemento,
                    {
                        "sticky": "nsew",
                        "children": [
                            (
                                "Button.padding",
                                {
                                    "sticky": "nsew",
                                    "children": [("Button.label", {"sticky": "nsew"})],
                                },
                            )
                        ],
                    },
                )
            ],
        )
        self.style.configure(
            f"{nombre}.TButton",
            foreground=texto,
            background=fondo,
            font=self.t.label_large,
            padding=0,
            anchor="center",
        )
        self.style.map(
            f"{nombre}.TButton",
            foreground=[("disabled", c.disabled_content)],
            background=[("active", fondo), ("pressed", fondo)],
        )

    # ── aplicación del tema ──────────────────────────────────────────────────

    def _aplicar(self) -> None:
        c, t, s = self.c, self.t, self.style
        s.theme_use("clam")
        self.root.configure(background=c.surface)
        for clase in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
            tkfont.nametofont(clase, self.root).configure(family=t.familia, size=10)
        self.root.option_add("*TCombobox*Listbox.font", t.body_medium)
        self.root.option_add("*TCombobox*Listbox.selectBackground", c.primary_container)
        self.root.option_add("*TCombobox*Listbox.selectForeground", c.on_primary_container)
        self.root.option_add("*TCombobox*Listbox.background", c.surface_container_lowest)
        self.root.option_add("*TCombobox*Listbox.relief", "flat")

        s.configure(
            ".",
            background=c.surface,
            foreground=c.on_surface,
            font=t.body_medium,
            bordercolor=c.outline_variant,
            focuscolor=c.primary,
            selectbackground=c.primary_container,
            selectforeground=c.on_primary_container,
        )

        # Superficies
        s.configure("TFrame", background=c.surface)
        s.configure("AppBar.TFrame", background=c.primary)
        s.configure("Divider.TFrame", background=c.outline_variant)
        s.configure("Indicador.TFrame", background=c.primary)
        s.configure("IndicadorOff.TFrame", background=c.surface)
        s.configure("Status.TFrame", background=c.surface_container)

        tarjeta = self._rect(
            c.surface_container_lowest, self.RADIO_TARJETA, c.outline_variant, ancho=48, alto=48
        )
        s.element_create("Card.bg", "image", tarjeta, border=self.RADIO_TARJETA + 1, sticky="nsew")
        s.layout(
            "Card.TFrame",
            [("Card.bg", {"sticky": "nsew", "children": [("Frame.padding", {"sticky": "nsew"})]})],
        )
        s.configure("Card.TFrame", background=c.surface)
        s.configure("CardInner.TFrame", background=c.surface_container_lowest)

        # Textos
        tarjeta_fondo = c.surface_container_lowest
        etiquetas = {
            "TLabel": (t.body_medium, c.on_surface, c.surface),
            "AppTitle.TLabel": (t.title_large, c.on_primary, c.primary),
            "AppSubtitle.TLabel": (t.body_small, c.primary_container, c.primary),
            "Headline.TLabel": (t.headline, c.on_surface, c.surface),
            "Body.TLabel": (t.body_medium, c.on_surface_variant, c.surface),
            "Status.TLabel": (t.body_medium, c.on_surface_variant, c.surface_container),
            "CardTitle.TLabel": (t.title_medium, c.on_surface, tarjeta_fondo),
            "Card.TLabel": (t.body_medium, c.on_surface, tarjeta_fondo),
            "CardBody.TLabel": (t.body_medium, c.on_surface_variant, tarjeta_fondo),
            "Helper.TLabel": (t.body_small, c.on_surface_variant, tarjeta_fondo),
            "Key.TLabel": (t.label_medium, c.on_surface_variant, tarjeta_fondo),
            "Value.TLabel": (t.body_medium, c.on_surface, tarjeta_fondo),
            "Warning.TLabel": (t.body_small, c.on_warning_container, c.warning_container),
            "Link.TLabel": (t.body_medium, c.primary, tarjeta_fondo),
            "Tab.TLabel": (t.label_large, c.on_surface_variant, c.surface),
            "TabActive.TLabel": (t.label_large, c.primary, c.surface),
            "ChipOk.TLabel": (t.label_medium, c.success, c.success_container),
            "ChipNeutral.TLabel": (t.label_medium, c.on_surface_variant, c.surface_container),
            "ChipVersion.TLabel": (t.label_medium, c.on_primary_container, c.primary_container),
        }
        for nombre, (fuente, color, fondo) in etiquetas.items():
            s.configure(nombre, font=fuente, foreground=color, background=fondo)
        for nombre in ("ChipOk.TLabel", "ChipNeutral.TLabel", "ChipVersion.TLabel"):
            s.configure(nombre, padding=(10, 3))
        s.configure("Warning.TLabel", padding=(10, 6))
        s.configure("Tab.TLabel", padding=(18, 12))
        s.configure("TabActive.TLabel", padding=(18, 12))

        # Botones
        self._estilo_boton("Filled", c.primary, c.on_primary)
        self._estilo_boton("Tonal", c.secondary_container, c.on_secondary_container)
        self._estilo_boton("Outlined", None, c.primary, borde=c.outline)
        self._estilo_boton(
            "OutlinedCard", None, c.primary, borde=c.outline, fondo=c.surface_container_lowest
        )
        self._estilo_boton("Text", None, c.primary)
        self._estilo_boton("TextCard", None, c.primary, fondo=c.surface_container_lowest)

        # Campos con contorno
        campo = {
            "fieldbackground": c.surface_container_lowest,
            "background": c.surface_container_lowest,
            "foreground": c.on_surface,
            "bordercolor": c.outline,
            "lightcolor": c.outline,
            "darkcolor": c.outline,
            "insertcolor": c.primary,
            "padding": (10, 7),
            "arrowcolor": c.on_surface_variant,
            "arrowsize": 14,
        }
        enfocado = [("focus", c.primary), ("disabled", c.outline_variant)]
        for nombre in ("TEntry", "TCombobox", "TSpinbox"):
            s.configure(nombre, **campo)
            s.map(
                nombre,
                bordercolor=enfocado,
                lightcolor=enfocado,
                darkcolor=enfocado,
                fieldbackground=[
                    ("disabled", c.surface),
                    ("readonly", c.surface_container_lowest),
                ],
                foreground=[("disabled", c.disabled_content)],
                selectbackground=[("readonly", c.surface_container_lowest)],
                selectforeground=[("readonly", c.on_surface)],
                background=[
                    ("active", c.surface_container_lowest),
                    ("readonly", c.surface_container_lowest),
                ],
            )

        # Casilla de verificación sobre tarjeta
        s.configure(
            "Card.TCheckbutton",
            background=c.surface_container_lowest,
            foreground=c.on_surface,
            font=t.body_medium,
            indicatorbackground=c.surface_container_lowest,
            indicatorforeground=c.on_primary,
            indicatormargin=(0, 0, 8, 0),
            focuscolor=c.surface_container_lowest,
        )
        s.map(
            "Card.TCheckbutton",
            background=[("active", c.surface_container_lowest)],
            indicatorbackground=[("selected", c.primary), ("active", c.primary_container)],
            indicatorforeground=[("selected", c.on_primary)],
        )

        # Opción excluyente sobre tarjeta (mismo lenguaje que la casilla)
        s.configure(
            "Card.TRadiobutton",
            background=c.surface_container_lowest,
            foreground=c.on_surface,
            font=t.body_medium,
            indicatorbackground=c.surface_container_lowest,
            indicatorforeground=c.primary,
            indicatormargin=(0, 0, 6, 0),
            focuscolor=c.surface_container_lowest,
        )
        s.map(
            "Card.TRadiobutton",
            background=[("active", c.surface_container_lowest)],
            foreground=[("disabled", c.disabled_content)],
            indicatorbackground=[("selected", c.primary), ("active", c.primary_container)],
            indicatorforeground=[("selected", c.on_primary)],
        )

        # Progreso lineal Material (4 px)
        s.configure(
            "Material.Horizontal.TProgressbar",
            thickness=4,
            troughcolor=c.primary_container,
            background=c.primary,
            bordercolor=c.primary_container,
            lightcolor=c.primary,
            darkcolor=c.primary,
        )

        # Barra de desplazamiento delgada, sin flechas
        s.layout(
            "Material.Vertical.TScrollbar",
            [
                (
                    "Vertical.Scrollbar.trough",
                    {
                        "sticky": "ns",
                        "children": [
                            ("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})
                        ],
                    },
                )
            ],
        )
        s.configure(
            "Material.Vertical.TScrollbar",
            troughcolor=c.surface_container_lowest,
            background=c.outline_variant,
            bordercolor=c.surface_container_lowest,
            lightcolor=c.outline_variant,
            darkcolor=c.outline_variant,
            gripcount=0,
            arrowsize=10,
        )
        s.map("Material.Vertical.TScrollbar", background=[("active", c.outline)])


def centrar(
    ventana: tk.Toplevel | tk.Tk, ancho: int, alto: int, relativo_a: tk.Misc | None = None
) -> None:
    """Centra una ventana en la pantalla o sobre otra ventana."""
    ventana.update_idletasks()
    ancho = min(ancho, ventana.winfo_screenwidth() - 40)
    alto = min(alto, ventana.winfo_screenheight() - 80)
    if relativo_a is not None:
        x = relativo_a.winfo_rootx() + (relativo_a.winfo_width() - ancho) // 2
        y = relativo_a.winfo_rooty() + (relativo_a.winfo_height() - alto) // 2
    else:
        x = (ventana.winfo_screenwidth() - ancho) // 2
        y = (ventana.winfo_screenheight() - alto) // 2
    ventana.geometry(f"{ancho}x{alto}+{max(x, 0)}+{max(y, 0)}")
