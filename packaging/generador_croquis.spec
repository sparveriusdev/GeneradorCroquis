# -*- mode: python ; coding: utf-8 -*-
# ==============================================================================
# Archivo  : packaging/generador_croquis.spec
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.0.0 | 2026-11-05 | Creación. Especificación PyInstaller multiplataforma:
#          |            | Windows -> .exe de un solo archivo; Linux -> binario
#          |            | de un solo archivo; macOS -> bundle .app. Incluye
#          |            | datos de GDAL (pyogrio) y PROJ (pyproj).
# ==============================================================================
# Uso:  uv run pyinstaller packaging/generador_croquis.spec --noconfirm
import re
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

RAIZ = Path(SPECPATH).parent
SRC = RAIZ / "src"
VERSION = re.search(
    r'__version__\s*=\s*"([^"]+)"', (SRC / "generador_croquis" / "__init__.py").read_text()
).group(1)
NOMBRE = "GeneradorCroquis"

datas, binaries, hiddenimports = [], [], []
for paquete in ("pyogrio", "pyproj", "shapely", "geopandas"):
    d, b, h = collect_all(paquete)
    datas += d
    binaries += b
    hiddenimports += h
hiddenimports += ["matplotlib.backends.backend_tkagg"]

a = Analysis(
    [str(SRC / "generador_croquis" / "__main__.py")],
    pathex=[str(SRC)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["pytest", "IPython", "PyQt5", "PyQt6", "PySide6"],
    noarchive=False,
)
pyz = PYZ(a.pure)

if sys.platform == "darwin":
    # En macOS se genera un .app (modo carpeta, recomendado por PyInstaller).
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name=NOMBRE,
              console=False, upx=False)
    coll = COLLECT(exe, a.binaries, a.datas, name=NOMBRE, upx=False)
    app = BUNDLE(
        coll,
        name=f"{NOMBRE}.app",
        bundle_identifier="co.edu.utp.generadorcroquis",
        version=VERSION,
        info_plist={"NSHighResolutionCapable": True, "CFBundleShortVersionString": VERSION},
    )
else:
    # Windows y Linux: un único ejecutable portable.
    exe = EXE(
        pyz, a.scripts, a.binaries, a.datas, [],
        name=NOMBRE,
        console=False,  # sin ventana de consola; los errores van al log y a un diálogo
        upx=False,
        runtime_tmpdir=None,
    )
