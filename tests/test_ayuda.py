# ==============================================================================
# Archivo  : tests/test_ayuda.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.1.0 | 2026-11-05 | Prueba de avisos de GitHub (> [!WARNING]).
#   v1.0.0 | 2026-11-05 | Creación. Pruebas del parser de Markdown, del
#          |            | servicio de ayuda (GitHub / copia local) y de su
#          |            | controlador, sin red ni interfaz gráfica.
# ==============================================================================
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from generador_croquis.config import directorio_docs
from generador_croquis.controller.ayuda import ControladorAyuda
from generador_croquis.domain import ActualizacionError
from generador_croquis.services.ayuda import ServicioAyuda
from generador_croquis.services.markdown import (
    BloqueCodigo,
    Cita,
    Encabezado,
    Imagen,
    Lista,
    Parrafo,
    Separador,
    Tabla,
    ancla_github,
    parsear,
    parsear_inline,
    texto_plano,
)

# ── parser ──────────────────────────────────────────────────────────────────

MARKDOWN = """<!--
cabecera oculta
-->
# Título principal

Texto con **negrita**, *cursiva*, `código` y [enlace](https://x.org).
Sigue el párrafo.

> Nota importante
> en dos líneas.

1. Primero
2. Segundo
   - Sub-elemento
3. Tercero

| Columna A | Columna B |
|---|---|
| a \\| b | [ver](#seccion) |

![Logo](img/logo.png)

---

```bash
uv sync
```
"""


def test_parsear_estructura():
    tipos = [type(b) for b in parsear(MARKDOWN).bloques]
    assert tipos == [Encabezado, Parrafo, Cita, Lista, Tabla, Imagen, Separador, BloqueCodigo]


def test_comentarios_html_se_ignoran():
    assert "oculta" not in str(parsear(MARKDOWN).bloques)


def test_parrafo_multilinea_y_formato_inline():
    parrafo = parsear(MARKDOWN).bloques[1]
    assert texto_plano(parrafo.contenido).endswith("Sigue el párrafo.")
    formatos = {f.texto: f for f in parrafo.contenido}
    assert formatos["negrita"].negrita
    assert formatos["cursiva"].cursiva
    assert formatos["código"].codigo
    assert formatos["enlace"].enlace == "https://x.org"


def test_lista_con_subelementos():
    lista = parsear(MARKDOWN).bloques[3]
    assert lista.ordenada
    assert [texto_plano(e) for e in lista.elementos] == [
        "Primero",
        "Segundo",
        "◦ Sub-elemento",
        "Tercero",
    ]


def test_tabla_con_barra_escapada_y_enlace():
    tabla = parsear(MARKDOWN).bloques[4]
    assert [texto_plano(c) for c in tabla.cabecera] == ["Columna A", "Columna B"]
    assert texto_plano(tabla.filas[0][0]) == "a | b"
    assert tabla.filas[0][1][0].enlace == "#seccion"


def test_cita_e_imagen_y_codigo():
    bloques = parsear(MARKDOWN).bloques
    assert isinstance(bloques[2], Cita)
    assert texto_plano(bloques[2].contenido[0]) == "Nota importante en dos líneas."
    assert bloques[5] == Imagen("Logo", "img/logo.png")
    assert bloques[7].texto == "uv sync"


@pytest.mark.parametrize(
    ("titulo", "ancla"),
    [
        ("1. ¿Qué hace el programa?", "1-qué-hace-el-programa"),
        ("8. Solución de problemas", "8-solución-de-problemas"),
        ("Archivo de registro", "archivo-de-registro"),
    ],
)
def test_anclas_como_github(titulo, ancla):
    assert ancla_github(titulo) == ancla


def test_enlace_con_formato_dentro():
    (fragmento,) = parsear_inline("[**Releases**](https://r)")
    assert fragmento.negrita and fragmento.enlace == "https://r"


def test_manual_real_tiene_indice_navegable():
    """Cada enlace del índice del manual apunta a un encabezado existente."""
    docs = directorio_docs()
    assert docs is not None
    doc = parsear((docs / "MANUAL_DE_USO.md").read_text(encoding="utf-8"))
    anclas = {b.ancla for b in doc.bloques if isinstance(b, Encabezado)}
    indice = next(b for b in doc.bloques if isinstance(b, Lista) and b.ordenada)
    enlaces = [f.enlace[1:] for e in indice.elementos for f in e if f.enlace]
    assert len(enlaces) == 8
    assert set(enlaces) <= anclas
    for img in (b for b in doc.bloques if isinstance(b, Imagen)):
        assert (docs / img.ruta).is_file(), img.ruta


# ── servicio ────────────────────────────────────────────────────────────────


@dataclass
class TransporteTexto:
    texto: str | None = None
    pedidas: list = field(default_factory=list)

    def obtener_texto(self, url):
        self.pedidas.append(url)
        if self.texto is None:
            raise ActualizacionError("sin red")
        return self.texto


@pytest.fixture
def docs_local(tmp_path: Path) -> Path:
    (tmp_path / "MANUAL_DE_USO.md").write_text("# Copia local\n", encoding="utf-8")
    (tmp_path / "img").mkdir()
    (tmp_path / "img" / "a.png").write_bytes(b"png")
    return tmp_path


def test_manual_desde_github(docs_local):
    transporte = TransporteTexto("# Desde GitHub\n")
    manual = ServicioAyuda(transporte, "https://raw/manual.md", docs_local).obtener()
    assert manual.desde_github
    assert manual.documento.titulo == "Desde GitHub"
    assert transporte.pedidas == ["https://raw/manual.md"]


def test_manual_sin_conexion_usa_copia_local(docs_local):
    manual = ServicioAyuda(TransporteTexto(None), "u", docs_local).obtener()
    assert not manual.desde_github
    assert manual.documento.titulo == "Copia local"
    assert manual.ruta_imagen("img/a.png") == (docs_local / "img" / "a.png").resolve()
    assert manual.ruta_imagen("img/no_existe.png") is None


def test_manual_sin_conexion_ni_copia(tmp_path):
    servicio = ServicioAyuda(TransporteTexto(None), "u", tmp_path / "vacio")
    servicio._local = None
    with pytest.raises(ActualizacionError):
        servicio.obtener()


# ── controlador ─────────────────────────────────────────────────────────────


class EjecutorSincrono:
    def ejecutar(self, tarea, al_terminar, al_fallar, al_progresar=None):
        try:
            resultado = tarea(lambda _f: None)
        except Exception as exc:
            al_fallar(exc)
        else:
            al_terminar(resultado)


@dataclass
class VistaAyudaFalsa:
    eventos: list = field(default_factory=list)

    def mostrar_cargando(self):
        self.eventos.append("cargando")

    def mostrar_manual(self, manual):
        self.eventos.append(("manual", manual.documento.titulo))

    def mostrar_error_carga(self, mensaje):
        self.eventos.append(("error", mensaje))

    def abrir_url(self, url):
        self.eventos.append(("url", url))


def test_controlador_carga_una_sola_vez(docs_local):
    vista = VistaAyudaFalsa()
    transporte = TransporteTexto("# Manual\n")
    ctrl = ControladorAyuda(vista, ServicioAyuda(transporte, "u", docs_local), EjecutorSincrono())
    ctrl.asegurar_cargado()
    ctrl.asegurar_cargado()
    assert vista.eventos == ["cargando", ("manual", "Manual")]
    ctrl.recargar()
    assert len(transporte.pedidas) == 2


def test_controlador_informa_error(tmp_path):
    vista = VistaAyudaFalsa()
    servicio = ServicioAyuda(TransporteTexto(None), "u", tmp_path)
    servicio._local = None
    ControladorAyuda(vista, servicio, EjecutorSincrono()).asegurar_cargado()
    assert vista.eventos[0] == "cargando"
    assert vista.eventos[1][0] == "error"


def test_aviso_de_github_muestra_su_titulo():
    (cita,) = parsear("> [!WARNING]\n> Cuidado con la tolerancia.\n").bloques
    assert isinstance(cita, Cita)
    titulo, cuerpo = cita.contenido
    assert texto_plano(titulo) == "⚠️ Advertencia" and titulo[0].negrita
    assert texto_plano(cuerpo) == "Cuidado con la tolerancia."
