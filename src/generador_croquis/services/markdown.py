# ==============================================================================
# Archivo  : src/generador_croquis/services/markdown.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.1 | 2026-11-05 | Las viñetas sangradas se tratan como sub-elementos.
#   v1.0.0 | 2026-11-05 | Creación. Parser de Markdown (subconjunto GFM usado
#          |            | en la documentación: encabezados, párrafos, listas,
#          |            | tablas, citas, código, imágenes, enlaces, negrita,
#          |            | cursiva). Produce bloques independientes de Tk.
#          |            | Anclas compatibles con las de GitHub.
# ==============================================================================
"""Conversión de Markdown a una estructura de bloques fácil de dibujar."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# ── estructura ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Fragmento:
    """Trozo de texto con un único formato."""

    texto: str
    negrita: bool = False
    cursiva: bool = False
    codigo: bool = False
    enlace: str | None = None


Linea = tuple[Fragmento, ...]


@dataclass(frozen=True)
class Encabezado:
    nivel: int
    contenido: Linea
    ancla: str


@dataclass(frozen=True)
class Parrafo:
    contenido: Linea


@dataclass(frozen=True)
class Lista:
    elementos: tuple[Linea, ...]
    ordenada: bool = False
    inicio: int = 1


@dataclass(frozen=True)
class Tabla:
    cabecera: tuple[Linea, ...]
    filas: tuple[tuple[Linea, ...], ...]


@dataclass(frozen=True)
class Cita:
    contenido: tuple[Linea, ...]


@dataclass(frozen=True)
class BloqueCodigo:
    texto: str


@dataclass(frozen=True)
class Imagen:
    alternativo: str
    ruta: str


@dataclass(frozen=True)
class Separador:
    pass


Bloque = Encabezado | Parrafo | Lista | Tabla | Cita | BloqueCodigo | Imagen | Separador


@dataclass
class Documento:
    bloques: list[Bloque] = field(default_factory=list)

    @property
    def titulo(self) -> str | None:
        for b in self.bloques:
            if isinstance(b, Encabezado) and b.nivel == 1:
                return texto_plano(b.contenido)
        return None


# ── utilidades ──────────────────────────────────────────────────────────────


def texto_plano(linea: Linea) -> str:
    return "".join(f.texto for f in linea)


def ancla_github(texto: str) -> str:
    """Genera el identificador de ancla igual que GitHub (minúsculas, guiones)."""
    texto = unicodedata.normalize("NFC", texto.strip().lower())
    texto = "".join(ch for ch in texto if ch.isalnum() or ch in " -_")
    return texto.replace(" ", "-")


_INLINE = re.compile(
    r"(?P<codigo>`[^`]+`)"
    r"|(?P<enlace>\[(?P<et>[^\]]+)\]\((?P<url>[^)\s]+)\))"
    r"|(?P<auto><(?P<autourl>https?://[^>\s]+)>)"
    r"|(?P<negrita>\*\*(?P<nt>.+?)\*\*)"
    r"|(?P<cursiva>(?<![\w*])\*(?P<ct>[^*\s][^*]*?)\*(?![\w*]))"
)


def parsear_inline(
    texto: str, negrita: bool = False, cursiva: bool = False, enlace: str | None = None
) -> Linea:
    """Convierte el formato en línea en fragmentos."""
    fragmentos: list[Fragmento] = []
    posicion = 0
    for m in _INLINE.finditer(texto):
        if m.start() > posicion:
            fragmentos.append(
                Fragmento(texto[posicion : m.start()], negrita, cursiva, enlace=enlace)
            )
        if m["codigo"]:
            fragmentos.append(Fragmento(m["codigo"][1:-1], negrita, cursiva, True, enlace))
        elif m["enlace"]:
            fragmentos.extend(parsear_inline(m["et"], negrita, cursiva, m["url"]))
        elif m["auto"]:
            fragmentos.append(Fragmento(m["autourl"], negrita, cursiva, enlace=m["autourl"]))
        elif m["negrita"]:
            fragmentos.extend(parsear_inline(m["nt"], True, cursiva, enlace))
        else:
            fragmentos.extend(parsear_inline(m["ct"], negrita, True, enlace))
        posicion = m.end()
    if posicion < len(texto):
        fragmentos.append(Fragmento(texto[posicion:], negrita, cursiva, enlace=enlace))
    return tuple(f for f in fragmentos if f.texto)


def _celdas(linea: str) -> list[str]:
    linea = linea.strip().strip("|")
    partes = re.split(r"(?<!\\)\|", linea)
    return [p.strip().replace("\\|", "|") for p in partes]


_COMENTARIO = re.compile(r"<!--.*?-->", re.S)
_ENCABEZADO = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_VINETA = re.compile(r"^\s*[-*+]\s+(.*)$")
_NUMERADA = re.compile(r"^\s*(\d+)[.)]\s+(.*)$")
_IMAGEN = re.compile(r"^!\[(?P<alt>[^\]]*)\]\((?P<src>[^)\s]+)\)\s*$")
_SEPARADOR_TABLA = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
_SEPARADOR = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")


def parsear(markdown: str) -> Documento:
    """Convierte texto Markdown en un :class:`Documento`."""
    lineas = _COMENTARIO.sub("", markdown).splitlines()
    doc = Documento()
    i = 0

    def es_inicio_de_bloque(linea: str) -> bool:
        return bool(
            not linea.strip()
            or _ENCABEZADO.match(linea)
            or _VINETA.match(linea)
            or _NUMERADA.match(linea)
            or linea.lstrip().startswith((">", "```", "|"))
            or _IMAGEN.match(linea.strip())
            or _SEPARADOR.match(linea)
        )

    while i < len(lineas):
        linea = lineas[i]
        if not linea.strip():
            i += 1
            continue

        if linea.lstrip().startswith("```"):
            i += 1
            codigo = []
            while i < len(lineas) and not lineas[i].lstrip().startswith("```"):
                codigo.append(lineas[i])
                i += 1
            doc.bloques.append(BloqueCodigo("\n".join(codigo)))
            i += 1
            continue

        if m := _ENCABEZADO.match(linea):
            contenido = parsear_inline(m[2])
            doc.bloques.append(
                Encabezado(len(m[1]), contenido, ancla_github(texto_plano(contenido)))
            )
            i += 1
            continue

        if _SEPARADOR.match(linea):
            doc.bloques.append(Separador())
            i += 1
            continue

        if m := _IMAGEN.match(linea.strip()):
            doc.bloques.append(Imagen(m["alt"], m["src"]))
            i += 1
            continue

        if (
            linea.lstrip().startswith("|")
            and i + 1 < len(lineas)
            and _SEPARADOR_TABLA.match(lineas[i + 1])
        ):
            cabecera = tuple(parsear_inline(c) for c in _celdas(linea))
            i += 2
            filas = []
            while i < len(lineas) and lineas[i].lstrip().startswith("|"):
                celdas = [parsear_inline(c) for c in _celdas(lineas[i])]
                celdas += [()] * (len(cabecera) - len(celdas))
                filas.append(tuple(celdas[: len(cabecera)]))
                i += 1
            doc.bloques.append(Tabla(cabecera, tuple(filas)))
            continue

        if linea.lstrip().startswith(">"):
            cita = []
            while i < len(lineas) and lineas[i].lstrip().startswith(">"):
                cita.append(lineas[i].lstrip()[1:].strip())
                i += 1
            parrafos, actual = [], []
            for c in cita:
                if c:
                    actual.append(c)
                elif actual:
                    parrafos.append(" ".join(actual))
                    actual = []
            if actual:
                parrafos.append(" ".join(actual))
            doc.bloques.append(Cita(tuple(parsear_inline(p) for p in parrafos)))
            continue

        if _VINETA.match(linea) or _NUMERADA.match(linea):
            ordenada = bool(_NUMERADA.match(linea))
            inicio = int(_NUMERADA.match(linea)[1]) if ordenada else 1
            elementos: list[str] = []
            while i < len(lineas):
                actual = lineas[i]
                sangrado = actual.startswith((" ", "\t")) and bool(elementos)
                m = _NUMERADA.match(actual) if ordenada else _VINETA.match(actual)
                if m and not sangrado:
                    elementos.append(m[m.lastindex])
                elif actual.strip() and sangrado:
                    if _VINETA.match(actual) or _NUMERADA.match(actual):
                        sub = _VINETA.match(actual) or _NUMERADA.match(actual)
                        elementos.append("◦ " + sub[sub.lastindex])
                    else:
                        elementos[-1] += " " + actual.strip()
                elif (
                    not actual.strip()
                    and i + 1 < len(lineas)
                    and (lineas[i + 1].startswith((" ", "\t")))
                ):
                    pass  # línea en blanco dentro de un elemento con bloque indentado
                else:
                    break
                i += 1
            doc.bloques.append(Lista(tuple(parsear_inline(e) for e in elementos), ordenada, inicio))
            continue

        parrafo = [linea.strip()]
        i += 1
        while i < len(lineas) and not es_inicio_de_bloque(lineas[i]):
            parrafo.append(lineas[i].strip())
            i += 1
        doc.bloques.append(Parrafo(parsear_inline(" ".join(parrafo))))

    return doc
