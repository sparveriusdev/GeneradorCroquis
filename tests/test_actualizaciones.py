# ==============================================================================
# Archivo  : tests/test_actualizaciones.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Pruebas de Version (SemVer), del servicio
#          |            | de actualizaciones y del controlador "Acerca de",
#          |            | con transporte HTTP, vista y ejecutor falsos.
# ==============================================================================
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from generador_croquis.controller import ControladorAcercaDe
from generador_croquis.domain import ActualizacionError, Version
from generador_croquis.services import ServicioActualizaciones

# ── Version ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("menor", "mayor"),
    [
        ("1.0.0", "1.0.1"),
        ("1.0.9", "1.1.0"),
        ("1.9.9", "2.0.0"),
        ("1.0.0-rc.1", "1.0.0"),
        ("1.0.0-alpha", "1.0.0-beta"),
        ("1.0.0-rc.2", "1.0.0-rc.10"),
        ("1.0.0-1", "1.0.0-alpha"),
    ],
)
def test_orden_semver(menor, mayor):
    assert Version.parse(menor) < Version.parse(mayor)


def test_parse_acepta_prefijo_v_y_metadatos():
    assert Version.parse("v1.2.3+build.5") == Version(1, 2, 3)
    assert str(Version.parse("1.2.3-rc.1")) == "1.2.3-rc.1"


@pytest.mark.parametrize("texto", ["1.0", "01.0.0", "version1", ""])
def test_parse_invalido(texto):
    with pytest.raises(ValueError):
        Version.parse(texto)


# ── servicio ────────────────────────────────────────────────────────────────


def release_json(tag="v1.2.0"):
    return {
        "tag_name": tag,
        "html_url": f"https://github.com/x/y/releases/tag/{tag}",
        "body": "notas",
        "assets": [
            {
                "name": f"GeneradorCroquis-{tag[1:]}-{sufijo}",
                "size": 10,
                "browser_download_url": f"https://descarga/{sufijo}",
            }
            for sufijo in ("windows-x64.exe", "linux-x64.tar.gz", "macos-arm64.zip")
        ],
    }


@dataclass
class TransporteFalso:
    respuesta: object = None
    error: Exception | None = None
    descargas: list = field(default_factory=list)

    def obtener_json(self, url):
        if self.error:
            raise self.error
        return self.respuesta

    def descargar(self, url, destino: Path, reportar=None):
        self.descargas.append(url)
        if reportar:
            reportar(0.5)
            reportar(1.0)
        destino.write_bytes(b"binario")
        return destino


@pytest.mark.parametrize(
    ("plataforma", "sufijo"),
    [("win32", "windows-x64.exe"), ("linux", "linux-x64.tar.gz"), ("darwin", "macos-arm64.zip")],
)
def test_consultar_elige_ejecutable_de_la_plataforma(plataforma, sufijo):
    servicio = ServicioActualizaciones(TransporteFalso(release_json()), "1.0.1", plataforma)
    resultado = servicio.consultar()
    assert resultado.hay_nueva
    assert resultado.ultimo.descarga.nombre.endswith(sufijo)


def test_sin_version_nueva():
    servicio = ServicioActualizaciones(TransporteFalso(release_json("v1.0.1")), "1.0.1", "linux")
    assert not servicio.consultar().hay_nueva


def test_plataforma_sin_ejecutable():
    servicio = ServicioActualizaciones(TransporteFalso(release_json()), "1.0.0", "freebsd")
    resultado = servicio.consultar()
    assert resultado.ultimo.descarga is None
    with pytest.raises(ActualizacionError):
        servicio.descargar(resultado.ultimo, Path("."))


def test_release_con_formato_inesperado():
    servicio = ServicioActualizaciones(TransporteFalso({"tag_name": "ultimo"}), "1.0.0", "linux")
    with pytest.raises(ActualizacionError):
        servicio.consultar()


# ── controlador ─────────────────────────────────────────────────────────────


class EjecutorSincrono:
    def ejecutar(self, tarea, al_terminar, al_fallar, al_progresar=None):
        try:
            resultado = tarea(al_progresar or (lambda _f: None))
        except Exception as exc:
            al_fallar(exc)
        else:
            al_terminar(resultado)


@dataclass
class VistaAcercaDeFalsa:
    carpeta: str | None = None
    estado: str = ""
    descarga_ofrecida: str | None = None
    progresos: list = field(default_factory=list)
    urls: list = field(default_factory=list)
    mensajes: list = field(default_factory=list)

    def mostrar_estado(self, texto):
        self.estado = texto

    def ofrecer_descarga(self, version):
        self.descarga_ofrecida = version

    def comprobando(self, activo):
        pass

    def mostrar_progreso(self, fraccion):
        self.progresos.append(fraccion)

    def pedir_carpeta(self):
        return self.carpeta

    def abrir_url(self, url):
        self.urls.append(url)

    def mostrar_error(self, titulo, mensaje):
        self.mensajes.append(("error", mensaje))

    def mostrar_exito(self, titulo, mensaje):
        self.mensajes.append(("exito", mensaje))


def crear(transporte, vista, version="1.0.1"):
    servicio = ServicioActualizaciones(transporte, version, "linux")
    return ControladorAcercaDe(vista, servicio, EjecutorSincrono())


def test_comprobar_y_descargar(tmp_path):
    vista = VistaAcercaDeFalsa(carpeta=str(tmp_path))
    transporte = TransporteFalso(release_json())
    ctrl = crear(transporte, vista)

    ctrl.comprobar()
    assert vista.descarga_ofrecida == "1.2.0"
    assert "v1.2.0" in vista.estado

    ctrl.descargar()
    assert transporte.descargas == ["https://descarga/linux-x64.tar.gz"]
    assert (tmp_path / "GeneradorCroquis-1.2.0-linux-x64.tar.gz").exists()
    assert vista.progresos == [0.0, 0.5, 1.0, None]
    assert vista.mensajes[-1][0] == "exito"


def test_comprobar_al_dia():
    vista = VistaAcercaDeFalsa()
    crear(TransporteFalso(release_json("v1.0.1")), vista).comprobar()
    assert vista.descarga_ofrecida is None
    assert "última versión" in vista.estado


def test_comprobar_sin_conexion():
    vista = VistaAcercaDeFalsa()
    crear(TransporteFalso(error=ActualizacionError("sin red")), vista).comprobar()
    assert vista.mensajes == [("error", "No se pudo comprobar la versión:\n\nsin red")]


def test_descarga_cancelada_no_descarga():
    vista = VistaAcercaDeFalsa(carpeta=None)
    transporte = TransporteFalso(release_json())
    ctrl = crear(transporte, vista)
    ctrl.comprobar()
    ctrl.descargar()
    assert transporte.descargas == []


def test_abrir_releases_usa_pagina_del_ultimo_release():
    vista = VistaAcercaDeFalsa()
    ctrl = crear(TransporteFalso(release_json()), vista)
    ctrl.abrir_releases()
    ctrl.comprobar()
    ctrl.abrir_releases()
    assert vista.urls[0].endswith("/releases")
    assert vista.urls[1].endswith("/releases/tag/v1.2.0")
