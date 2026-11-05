# ==============================================================================
# Archivo  : src/generador_croquis/view/ejecutor_tk.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Implementación Tk de EjecutorTareas: la
#          |            | tarea corre en un hilo y los resultados vuelven al
#          |            | hilo de la interfaz a través de una cola revisada
#          |            | con after() (Tk no es seguro entre hilos).
# ==============================================================================
"""Ejecución de tareas en segundo plano para Tkinter."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from collections.abc import Callable
from typing import Any

_INTERVALO_MS = 100


class EjecutorTk:
    def __init__(self, root: tk.Misc):
        self._root = root
        self._cola: queue.Queue[Callable[[], None]] = queue.Queue()
        self._root.after(_INTERVALO_MS, self._procesar)

    def ejecutar(
        self,
        tarea: Callable[[Callable[[float], None]], Any],
        al_terminar: Callable[[Any], None],
        al_fallar: Callable[[Exception], None],
        al_progresar: Callable[[float], None] | None = None,
    ) -> None:
        def reportar(fraccion: float) -> None:
            if al_progresar:
                self._cola.put(lambda: al_progresar(fraccion))

        def trabajo() -> None:
            try:
                resultado = tarea(reportar)
            except Exception as exc:  # se entrega al hilo de la interfaz
                # `exc` se borra al salir del except: se captura como argumento por defecto.
                self._cola.put(lambda error=exc: al_fallar(error))
            else:
                self._cola.put(lambda: al_terminar(resultado))

        threading.Thread(target=trabajo, daemon=True).start()

    def _procesar(self) -> None:
        try:
            while True:
                self._cola.get_nowait()()
        except queue.Empty:
            pass
        if self._root.winfo_exists():
            self._root.after(_INTERVALO_MS, self._procesar)
