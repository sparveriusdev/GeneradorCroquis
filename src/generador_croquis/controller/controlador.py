# ==============================================================================
# Archivo  : src/generador_croquis/controller/controlador.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.1.0 | 2026-11-05 | Separa el resumen de la capa (mostrar_resumen) de
#          |            | los mensajes de estado (mostrar_estado). Textos más
#          |            | claros que indican el siguiente paso al usuario.
#   v1.0.0 | 2026-11-05 | Creación. Extrae de AplicacionCroquis la lógica de
#          |            | flujo (cargar, generar, guardar) y el estado de la
#          |            | sesión. Manejo de errores unificado (DRY): errores
#          |            | esperados -> mensaje; inesperados -> log + mensaje.
# ==============================================================================
"""Controlador principal de la aplicación (MVC)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from generador_croquis.config import ARCHIVO_LOG, OPCION_NINGUNO
from generador_croquis.controller.vista import VistaCroquis
from generador_croquis.domain.exceptions import CroquisError, OperacionCanceladaError
from generador_croquis.domain.models import CapaCargada, SeleccionCampos
from generador_croquis.services.servicio_croquis import ServicioCroquis

if TYPE_CHECKING:
    from matplotlib.figure import Figure

log = logging.getLogger(__name__)

MENSAJE_INICIAL = "Abra un Shapefile, un .zip o una carpeta GDB para comenzar."


@dataclass
class EstadoSesion:
    """Estado mutable de la sesión de trabajo (modelo de la vista)."""

    capa: CapaCargada | None = None
    figura: Figure | None = None


def _normalizar_campo(valor: str | None) -> str | None:
    return None if not valor or valor == OPCION_NINGUNO else valor


def _plural(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


class ControladorCroquis:
    """Recibe eventos de la vista, invoca casos de uso y actualiza la vista."""

    def __init__(self, vista: VistaCroquis, servicio: ServicioCroquis):
        self._vista = vista
        self._servicio = servicio
        self.estado = EstadoSesion()

    # ── eventos de la vista ──────────────────────────────────────────────────

    def iniciar(self) -> None:
        self._vista.mostrar_estado(MENSAJE_INICIAL)

    def cargar_archivo(self, ruta: str | Path) -> None:
        self._vista.mostrar_estado(f"Leyendo «{Path(ruta).name}»…")
        if self._ejecutar("No se pudo abrir el archivo", lambda: self._cargar(ruta)):
            return
        # Error o cancelación: no se deja una capa a medias.
        self.estado.capa = None
        self._descartar_figura()
        self._vista.mostrar_resumen([], [])
        self._vista.habilitar_generar(False)

    def generar(self, campo_id: str | None, campo_pisos: str | None) -> None:
        capa = self.estado.capa
        if capa is None:
            self._vista.mostrar_aviso("Falta el archivo", "Primero abra un archivo de datos.")
            return

        seleccion = SeleccionCampos(_normalizar_campo(campo_id), _normalizar_campo(campo_pisos))
        n = self._servicio.requiere_confirmacion(capa, seleccion)
        if n is not None and not self._vista.confirmar(
            "Muchas construcciones",
            f"Se dibujarán {n} croquis en una sola lámina.\n"
            "Puede tardar y consumir bastante memoria.\n\n¿Desea continuar?",
        ):
            return

        def accion() -> None:
            self._descartar_figura()
            self._vista.mostrar_estado("Dibujando croquis…")
            self.estado.figura = self._servicio.generar_figura(capa, seleccion)
            self._vista.mostrar_figura(self.estado.figura)
            self._vista.habilitar_guardar(True)
            total = capa.contar_construcciones(seleccion.campo_id)
            self._vista.mostrar_estado(
                f"Listo: {_plural(total, 'croquis generado', 'croquis generados')}. "
                "Use «Exportar imagen» para guardarlos."
            )

        self._ejecutar("No se pudieron generar los croquis", accion)

    def guardar(self, ruta: str | Path | None) -> None:
        if self.estado.figura is None:
            self._vista.mostrar_aviso("Nada que exportar", "Primero genere los croquis.")
            return
        if not ruta:
            return
        figura = self.estado.figura

        def accion() -> None:
            destino = self._servicio.exportar(figura, ruta)
            self._vista.mostrar_estado(f"Imagen guardada en {destino}")
            self._vista.mostrar_exito("Imagen exportada", f"La imagen se guardó en:\n{destino}")

        self._ejecutar("No se pudo exportar la imagen", accion)

    def cerrar(self) -> None:
        self._descartar_figura()
        self.estado = EstadoSesion()

    # ── utilidades ───────────────────────────────────────────────────────────

    def _cargar(self, ruta: str | Path) -> None:
        resumen = self._servicio.cargar(ruta, self._vista.seleccionar_opcion)
        capa = resumen.capa
        self._descartar_figura()
        self.estado.capa = capa

        id_sug, pisos_sug = resumen.campo_id_sugerido, resumen.campo_pisos_sugerido
        nota_id = "Detectado automáticamente" if id_sug else "Elíjalo manualmente"
        nota_pisos = "Detectado automáticamente" if pisos_sug else "Opcional"
        self._vista.configurar_campos(capa.campos, id_sug, pisos_sug, nota_id, nota_pisos)
        self._vista.mostrar_resumen(resumen.filas(), list(capa.avisos))
        self._vista.habilitar_generar(True)
        self._vista.mostrar_estado(
            f"Archivo listo: {_plural(capa.num_poligonos, 'polígono', 'polígonos')}. "
            "Revise los campos y pulse «Generar croquis»."
        )

    def _descartar_figura(self) -> None:
        if self.estado.figura is not None:
            self._vista.cerrar_figura()
            self.estado.figura = None
            self._vista.habilitar_guardar(False)

    def _ejecutar(self, contexto: str, accion: Callable[[], None]) -> bool:
        """Ejecuta una acción mostrando progreso y traduce las excepciones a
        mensajes para el usuario. Devuelve True si terminó sin errores."""
        self._vista.ocupado(True)
        try:
            accion()
            return True
        except OperacionCanceladaError:
            self._vista.mostrar_estado("Operación cancelada.")
        except CroquisError as exc:
            log.warning("%s: %s", contexto, exc)
            self._vista.mostrar_error(contexto, str(exc))
            self._vista.mostrar_estado(f"{contexto}.")
        except Exception as exc:  # fallo inesperado: se registra la traza completa
            log.exception(contexto)
            self._vista.mostrar_error(
                "Error inesperado",
                f"{contexto}:\n\n{exc}\n\nEl detalle técnico quedó en:\n{ARCHIVO_LOG}",
            )
            self._vista.mostrar_estado(f"{contexto}.")
        finally:
            self._vista.ocupado(False)
        return False
