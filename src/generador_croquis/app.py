# ==============================================================================
# Archivo  : src/generador_croquis/app.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.1.0 | 2026-11-05 | Conecta la pestaña "Acerca de" (servicio de
#          |            | actualizaciones, transporte HTTP y ejecutor Tk).
#   v1.0.0 | 2026-11-05 | Creación. Raíz de composición: construye e inyecta
#          |            | dependencias (lector, renderizador, servicio, vista,
#          |            | controlador). Elimina el auto-instalador por pip de
#          |            | generador_v1.py (las dependencias las gestiona uv o
#          |            | van incluidas en el ejecutable). Opción --version.
# ==============================================================================
"""Arranque de la aplicación."""

from __future__ import annotations

import argparse
import logging
import sys

from generador_croquis import __app_name__, __version__
from generador_croquis.config import ARCHIVO_LOG, Configuracion

log = logging.getLogger(__name__)


def _parsear_argumentos(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="generador-croquis", description=__app_name__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("archivo", nargs="?", help="Archivo .zip/.shp o carpeta .gdb a abrir")
    args, _desconocidos = parser.parse_known_args(argv)  # macOS puede añadir -psn_*
    return args


def _error_fatal(mensaje: str) -> None:
    """Informa un error sin depender de que la ventana principal exista."""
    if sys.stderr is not None:
        print(mensaje, file=sys.stderr)
    try:
        from tkinter import Tk, messagebox

        raiz = Tk()
        raiz.withdraw()
        messagebox.showerror(__app_name__, mensaje)
        raiz.destroy()
    except Exception:
        pass


def main(argv: list[str] | None = None) -> int:
    args = _parsear_argumentos(argv)

    from generador_croquis.logging_config import configurar_logging

    configurar_logging()
    log.info("Iniciando %s v%s", __app_name__, __version__)

    try:
        import tkinter as tk
    except ImportError:
        log.error("tkinter no está disponible en este intérprete de Python")
        if sys.stderr is not None:
            print("Falta 'tkinter'. En Linux: sudo apt install python3-tk", file=sys.stderr)
        return 1

    try:
        import matplotlib

        matplotlib.use("TkAgg")

        from generador_croquis.controller import ControladorAcercaDe, ControladorCroquis
        from generador_croquis.data import LectorCapas, TransporteUrllib
        from generador_croquis.rendering import RenderizadorMatplotlib
        from generador_croquis.services import ServicioActualizaciones, ServicioCroquis
        from generador_croquis.view import VentanaPrincipal
        from generador_croquis.view.ejecutor_tk import EjecutorTk

        config = Configuracion()
        servicio = ServicioCroquis(
            lector=LectorCapas(),
            renderizador=RenderizadorMatplotlib(config.tema, config.cotas),
            config=config,
        )
        root = tk.Tk()
        vista = VentanaPrincipal(root)
        controlador = ControladorCroquis(vista, servicio)
        vista.conectar(controlador)
        vista.acerca_de.conectar(
            ControladorAcercaDe(
                vista.acerca_de,
                ServicioActualizaciones(TransporteUrllib()),
                EjecutorTk(root),
            )
        )
        if args.archivo:
            vista.ruta_archivo.set(args.archivo)
            root.after(100, controlador.cargar_archivo, args.archivo)
        root.mainloop()
        return 0
    except Exception as exc:
        log.exception("Error inesperado")
        _error_fatal(f"Error inesperado:\n\n{exc}\n\n(Detalle en {ARCHIVO_LOG})")
        return 1
