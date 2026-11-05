# ==============================================================================
# Archivo  : src/generador_croquis/services/agrupacion.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.1.0 | 2026-11-05 | Guarda el piso de cada parte y ordena las partes
#          |            | de abajo hacia arriba (colores fijos por piso).
#   v1.0.0 | 2026-11-05 | Creación. Regla de negocio "polígonos con el mismo
#          |            | identificador forman una construcción", extraída de
#          |            | generar_croquis(). Mejora: los pisos se leen con
#          |            | conversión numérica tolerante (valores no numéricos
#          |            | se ignoran en vez de anular todo el grupo).
# ==============================================================================
"""Agrupación de polígonos en construcciones."""

from __future__ import annotations

import pandas as pd

from generador_croquis.config import ID_VACIO
from generador_croquis.domain.models import CapaCargada, Construccion, SeleccionCampos


def _piso(valor: object) -> int | None:
    numero = pd.to_numeric(pd.Series([valor]), errors="coerce").iloc[0]
    return None if pd.isna(numero) else int(numero)


def _pisos(valores: pd.Series) -> int | None:
    numericos = pd.to_numeric(valores, errors="coerce").dropna()
    return int(numericos.max()) if not numericos.empty else None


def agrupar_construcciones(capa: CapaCargada, seleccion: SeleccionCampos) -> list[Construccion]:
    """Convierte la capa en una lista de construcciones ordenadas por identificador."""
    gdf = capa.gdf
    campo_id = seleccion.campo_id if seleccion.campo_id in gdf.columns else None
    campo_pisos = seleccion.campo_pisos if seleccion.campo_pisos in gdf.columns else None

    if campo_id:
        claves = gdf[campo_id].astype("string").fillna(ID_VACIO)
    else:
        claves = pd.Series([str(i) for i in range(len(gdf))], index=gdf.index)

    construcciones = []
    for clave, grupo in gdf.groupby(claves, sort=True):
        partes = list(grupo.geometry)
        pisos_partes: list[int | None] = []
        if campo_pisos:
            pisos_partes = [_piso(v) for v in grupo[campo_pisos]]
            # De abajo hacia arriba (sin piso al final); estable para partes del mismo piso.
            orden = sorted(
                range(len(partes)), key=lambda i: (pisos_partes[i] is None, pisos_partes[i] or 0)
            )
            partes = [partes[i] for i in orden]
            pisos_partes = [pisos_partes[i] for i in orden]
        construcciones.append(
            Construccion(
                identificador=str(clave),
                partes=tuple(partes),
                pisos=_pisos(grupo[campo_pisos]) if campo_pisos else None,
                pisos_partes=tuple(pisos_partes),
            )
        )
    if not campo_id:
        construcciones.sort(key=lambda c: int(c.identificador))
    return construcciones
