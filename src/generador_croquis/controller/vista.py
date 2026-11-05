# ==============================================================================
# Archivo  : src/generador_croquis/controller/vista.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.1.0 | 2026-11-05 | mostrar_info -> mostrar_estado (barra de estado) y
#          |            | nuevo mostrar_resumen (tabla de datos de la capa).
#   v1.0.0 | 2026-11-05 | Creación. Contrato que debe cumplir cualquier vista
#          |            | (inversión de dependencias: el controlador no conoce
#          |            | Tkinter y puede probarse con una vista falsa).
# ==============================================================================
"""Protocolo de la vista consumido por el controlador."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from matplotlib.figure import Figure


class VistaCroquis(Protocol):
    """Operaciones que el controlador necesita de la interfaz de usuario."""

    def mostrar_estado(self, texto: str) -> None: ...

    def mostrar_resumen(self, filas: Sequence[tuple[str, str]], avisos: Sequence[str]) -> None: ...

    def mostrar_error(self, titulo: str, mensaje: str) -> None: ...

    def mostrar_aviso(self, titulo: str, mensaje: str) -> None: ...

    def mostrar_exito(self, titulo: str, mensaje: str) -> None: ...

    def confirmar(self, titulo: str, mensaje: str) -> bool: ...

    def seleccionar_opcion(
        self, titulo: str, mensaje: str, opciones: Sequence[str]
    ) -> str | None: ...

    def configurar_campos(
        self,
        campos: Sequence[str],
        campo_id: str | None,
        campo_pisos: str | None,
        nota_id: str,
        nota_pisos: str,
    ) -> None: ...

    def habilitar_generar(self, habilitado: bool) -> None: ...

    def habilitar_guardar(self, habilitado: bool) -> None: ...

    def ocupado(self, activo: bool) -> None: ...

    def mostrar_figura(self, figura: Figure) -> None: ...

    def cerrar_figura(self) -> None: ...
