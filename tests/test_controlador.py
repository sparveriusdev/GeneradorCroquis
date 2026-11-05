# ==============================================================================
# Archivo  : tests/test_controlador.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.3.0 | 2026-11-05 | Significado del campo de pisos (detección y envío).
#   v1.2.0 | 2026-11-05 | Prueba de la tolerancia de acotado (coma decimal
#          |            | y valores inválidos).
#   v1.1.0 | 2026-11-05 | Adapta la vista falsa a mostrar_estado/mostrar_resumen.
#   v1.0.0 | 2026-11-05 | Creación. Pruebas del controlador con una vista
#          |            | falsa (demuestra el desacople MVC).
# ==============================================================================
from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from generador_croquis.config import Configuracion
from generador_croquis.controller import ControladorCroquis
from generador_croquis.data import LectorCapas
from generador_croquis.rendering import RenderizadorMatplotlib
from generador_croquis.services import ServicioCroquis


@dataclass
class VistaFalsa:
    respuesta_confirmar: bool = True
    eventos: list[tuple] = field(default_factory=list)
    estado: str = ""
    resumen: list = field(default_factory=list)
    generar_habilitado: bool = False
    guardar_habilitado: bool = False
    figuras: list = field(default_factory=list)

    def mostrar_estado(self, texto):
        self.estado = texto

    def mostrar_resumen(self, filas, avisos):
        self.resumen = list(filas)

    def mostrar_error(self, titulo, mensaje):
        self.eventos.append(("error", mensaje))

    def mostrar_aviso(self, titulo, mensaje):
        self.eventos.append(("aviso", mensaje))

    def mostrar_exito(self, titulo, mensaje):
        self.eventos.append(("exito", mensaje))

    def confirmar(self, titulo, mensaje):
        self.eventos.append(("confirmar", mensaje))
        return self.respuesta_confirmar

    def seleccionar_opcion(self, titulo, mensaje, opciones):
        return opciones[0]

    def configurar_campos(self, campos, campo_id, campo_pisos, nota_id, nota_pisos):
        self.eventos.append(("campos", campo_id, campo_pisos, nota_id))

    def mostrar_significado_pisos(self, significado, habilitado):
        self.eventos.append(("significado", significado.value, habilitado))

    def habilitar_generar(self, habilitado):
        self.generar_habilitado = habilitado

    def habilitar_guardar(self, habilitado):
        self.guardar_habilitado = habilitado

    def ocupado(self, activo):
        pass

    def mostrar_figura(self, figura):
        self.figuras.append(figura)

    def cerrar_figura(self):
        pass


@pytest.fixture
def vista():
    return VistaFalsa()


def crear_controlador(vista, **config):
    servicio = ServicioCroquis(LectorCapas(), RenderizadorMatplotlib(), Configuracion(**config))
    return ControladorCroquis(vista, servicio)


def test_flujo_completo(vista, shapefile, tmp_path):
    ctrl = crear_controlador(vista)
    ctrl.cargar_archivo(shapefile)
    assert ("campos", "codigo", "num_pisos", "Detectado automáticamente") in vista.eventos
    assert vista.generar_habilitado
    assert ("Polígonos", "3") in vista.resumen
    assert ("Construcciones", "2 (agrupadas por «codigo»)") in vista.resumen
    assert vista.estado.startswith("Archivo listo: 3 polígonos")

    ctrl.generar("codigo", "num_pisos")
    assert len(vista.figuras) == 1
    assert vista.guardar_habilitado
    assert vista.estado.startswith("Listo: 2 croquis generados")

    destino = tmp_path / "salida.pdf"
    ctrl.guardar(destino)
    assert destino.exists()
    assert vista.eventos[-1][0] == "exito"


def test_error_de_carga_deshabilita_generar(vista, tmp_path):
    ctrl = crear_controlador(vista)
    malo = tmp_path / "malo.zip"
    malo.write_text("x")
    ctrl.cargar_archivo(malo)
    assert vista.eventos[-1][0] == "error"
    assert not vista.generar_habilitado
    assert ctrl.estado.capa is None
    assert vista.resumen == []


def test_generar_sin_capa_avisa(vista):
    crear_controlador(vista).generar(None, None)
    assert vista.eventos == [("aviso", "Primero abra un archivo de datos.")]


def test_confirmacion_de_muchas_construcciones(vista, shapefile):
    vista.respuesta_confirmar = False
    ctrl = crear_controlador(vista, max_construcciones_aviso=1)
    ctrl.cargar_archivo(shapefile)
    ctrl.generar("(ninguno)", "(ninguno)")
    assert vista.eventos[-1][0] == "confirmar"
    assert vista.figuras == []


@pytest.mark.parametrize("tolerancia", ["abc", "-1", "50"])
def test_tolerancia_invalida_avisa_y_no_genera(vista, shapefile, tolerancia):
    ctrl = crear_controlador(vista)
    ctrl.cargar_archivo(shapefile)
    ctrl.generar("codigo", None, True, tolerancia)
    assert vista.eventos[-1][0] == "aviso"
    assert vista.figuras == []


def test_tolerancia_con_coma_decimal(vista, shapefile):
    ctrl = crear_controlador(vista)
    ctrl.cargar_archivo(shapefile)
    ctrl.generar("codigo", None, True, "0,25")
    assert len(vista.figuras) == 1


def test_significado_de_pisos_se_detecta_al_cargar_y_al_cambiar(vista, shapefile):
    ctrl = crear_controlador(vista)
    ctrl.cargar_archivo(shapefile)  # campo sugerido: num_pisos → total
    assert ("significado", "total", True) in vista.eventos
    ctrl.cambiar_campo_pisos("PLANTA_UBICACION")
    assert vista.eventos[-1] == ("significado", "ubicacion", True)
    ctrl.cambiar_campo_pisos("(ninguno)")
    assert vista.eventos[-1] == ("significado", "total", False)


def test_generar_con_piso_de_la_unidad(vista, shapefile):
    ctrl = crear_controlador(vista)
    ctrl.cargar_archivo(shapefile)
    ctrl.generar("codigo", "num_pisos", True, "0.15", "ubicacion")
    assert len(vista.figuras) == 1
