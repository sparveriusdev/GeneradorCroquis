# ==============================================================================
# Archivo  : tests/conftest.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Fixtures compartidos: capa de ejemplo,
#          |            | shapefile, zip y File Geodatabase generados al vuelo.
# ==============================================================================
"""Fixtures de pruebas."""

from __future__ import annotations

import os
import zipfile
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")  # las pruebas no necesitan pantalla

import geopandas as gpd
import pytest
from shapely.geometry import Polygon, box

from generador_croquis.domain.models import CapaCargada


@pytest.fixture
def gdf_ejemplo() -> gpd.GeoDataFrame:
    """Tres polígonos: dos pertenecen a la construcción 'A', uno a la 'B'."""
    return gpd.GeoDataFrame(
        {
            "codigo": ["A", "A", "B"],
            "num_pisos": [2, 3, "x"],
            "width": [1, 2, 3],
        },
        geometry=[box(0, 0, 10, 5), box(10, 0, 14, 5), Polygon([(20, 0), (26, 0), (23, 4)])],
        crs="EPSG:9377",
    )


@pytest.fixture
def capa_ejemplo(gdf_ejemplo) -> CapaCargada:
    return CapaCargada(gdf=gdf_ejemplo, nombre="ejemplo")


@pytest.fixture
def shapefile(tmp_path: Path, gdf_ejemplo) -> Path:
    ruta = tmp_path / "construcciones.shp"
    gdf_ejemplo.to_file(ruta, engine="pyogrio")
    return ruta


@pytest.fixture
def zip_shapefile(tmp_path: Path, shapefile: Path) -> Path:
    ruta = tmp_path / "datos.zip"
    with zipfile.ZipFile(ruta, "w") as zf:
        for archivo in shapefile.parent.glob(f"{shapefile.stem}.*"):
            zf.write(archivo, f"carpeta/{archivo.name}")
    return ruta


@pytest.fixture
def gdb(tmp_path: Path, gdf_ejemplo) -> Path:
    ruta = tmp_path / "datos.gdb"
    try:
        gdf_ejemplo.to_file(ruta, layer="construcciones", driver="OpenFileGDB", engine="pyogrio")
        gdf_ejemplo.to_file(ruta, layer="otra_capa", driver="OpenFileGDB", engine="pyogrio")
    except Exception as exc:  # GDAL < 3.6 no escribe OpenFileGDB
        pytest.skip(f"El GDAL instalado no permite escribir GDB: {exc}")
    return ruta
