# ==============================================================================
# Archivo  : src/generador_croquis/data/dominios.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-06 | Creación. Lee los dominios de valores codificados de
#          |            | una File Geodatabase (tabla GDB_Items) y los asocia
#          |            | a los campos de una capa: p. ej. USO 11 →
#          |            | «(Residencial) Vivienda hasta 3 pisos». Si no se
#          |            | pueden leer, devuelve un diccionario vacío.
# ==============================================================================
"""Dominios de valores codificados de una File Geodatabase.

ArcGIS guarda en la tabla de sistema ``GDB_Items`` la definición XML de cada capa (qué
dominio usa cada campo) y de cada dominio (pares código → descripción). GDAL permite leer
esa tabla con SQL, sin dependencias adicionales.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from collections.abc import Iterable, Mapping
from pathlib import Path

import pyogrio

log = logging.getLogger(__name__)

# campo → (código → descripción)
Dominios = Mapping[str, Mapping[str, str]]


def _local(etiqueta: str) -> str:
    """Nombre de la etiqueta sin espacio de nombres."""
    return etiqueta.rsplit("}", 1)[-1]


def _hijo(nodo: ET.Element, nombre: str) -> str | None:
    for hijo in nodo:
        if _local(hijo.tag) == nombre:
            return (hijo.text or "").strip()
    return None


def _codigos(raiz: ET.Element) -> dict[str, str]:
    codigos: dict[str, str] = {}
    for nodo in raiz.iter():
        if _local(nodo.tag) == "CodedValue":
            codigo, nombre = _hijo(nodo, "Code"), _hijo(nodo, "Name")
            if codigo is not None and nombre:
                codigos[codigo] = nombre
    return codigos


def _campos_con_dominio(raiz: ET.Element) -> dict[str, str]:
    campos: dict[str, str] = {}
    for nodo in raiz.iter():
        if _local(nodo.tag) == "GPFieldInfoEx":
            campo, dominio = _hijo(nodo, "Name"), _hijo(nodo, "DomainName")
            if campo and dominio:
                campos[campo] = dominio
    return campos


def dominios_desde_items(items: Iterable[tuple[object, object]], capa: str) -> Dominios:
    """Dominios de los campos de ``capa`` a partir de las filas (Name, Definition) de GDB_Items."""
    dominios: dict[str, dict[str, str]] = {}
    campos: dict[str, str] = {}
    for nombre, definicion in items:
        if not isinstance(definicion, str) or not definicion:  # filas sin definición: NaN
            continue
        nombre = nombre if isinstance(nombre, str) else None
        try:
            raiz = ET.fromstring(definicion)
        except ET.ParseError:
            continue
        tipo = _local(raiz.tag)
        if tipo.startswith("GPCodedValueDomain"):
            dominio = _hijo(raiz, "DomainName") or nombre
            if dominio:
                dominios[dominio] = _codigos(raiz)
        elif nombre and nombre.lower() == capa.lower():
            campos = _campos_con_dominio(raiz)
    return {campo: dominios[d] for campo, d in campos.items() if dominios.get(d)}


def leer_dominios(ruta: Path, capa: str) -> Dominios:
    """Dominios codificados de los campos de ``capa`` en la GDB ``ruta`` ({} si no hay)."""
    try:
        tabla = pyogrio.read_dataframe(
            ruta, sql="SELECT Name, Definition FROM GDB_Items", read_geometry=False
        )
        return dominios_desde_items(zip(tabla["Name"], tabla["Definition"], strict=True), capa)
    except Exception as exc:  # GDB sin tabla de sistema o driver sin soporte: sin dominios
        log.info("No se pudieron leer los dominios de %s: %s", ruta, exc)
        return {}
