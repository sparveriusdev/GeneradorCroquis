# ==============================================================================
# Archivo  : src/generador_croquis/domain/version.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Value object Version con parseo y
#          |            | comparación según SemVer 2.0 (incluye prereleases).
# ==============================================================================
"""Versiones semánticas (SemVer 2.0)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import total_ordering

_PATRON = re.compile(
    r"^v?(?P<mayor>0|[1-9]\d*)\.(?P<menor>0|[1-9]\d*)\.(?P<parche>0|[1-9]\d*)"
    r"(?:-(?P<pre>[0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$"
)


@total_ordering
@dataclass(frozen=True)
class Version:
    """Versión SemVer comparable. Acepta el prefijo 'v' de los tags (v1.2.3)."""

    mayor: int
    menor: int
    parche: int
    prerelease: tuple[str, ...] = ()

    @classmethod
    def parse(cls, texto: str) -> Version:
        m = _PATRON.match(texto.strip())
        if not m:
            raise ValueError(f"'{texto}' no es una versión SemVer válida")
        pre = tuple(m["pre"].split(".")) if m["pre"] else ()
        return cls(int(m["mayor"]), int(m["menor"]), int(m["parche"]), pre)

    def __str__(self) -> str:
        base = f"{self.mayor}.{self.menor}.{self.parche}"
        return f"{base}-{'.'.join(self.prerelease)}" if self.prerelease else base

    def __lt__(self, otra: object) -> bool:
        if not isinstance(otra, Version):
            return NotImplemented
        if (self.mayor, self.menor, self.parche) != (otra.mayor, otra.menor, otra.parche):
            return (self.mayor, self.menor, self.parche) < (otra.mayor, otra.menor, otra.parche)
        # Una versión final es mayor que cualquiera de sus prereleases.
        if not self.prerelease or not otra.prerelease:
            return bool(self.prerelease) and not otra.prerelease
        return _clave_pre(self.prerelease) < _clave_pre(otra.prerelease)


def _clave_pre(identificadores: tuple[str, ...]) -> tuple[tuple[int, int | str], ...]:
    # Los identificadores numéricos van antes que los alfanuméricos (regla SemVer).
    return tuple((0, int(i)) if i.isdigit() else (1, i) for i in identificadores)
