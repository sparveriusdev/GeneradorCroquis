"""
GENERADOR DE CROQUIS DE CONSTRUCCIONES (versión corregida)
===========================================================
Lee un Shapefile (.shp), un .zip con shapefile o GDB, o una carpeta .gdb,
agrupa los polígonos por identificador (misma construcción) y genera una
imagen con un croquis técnico por cada construcción.

USO (recomendado, desde CMD o PowerShell para ver cualquier error):
    python croquis_generator.py

Requisitos: Python 3.9 a 3.12 de 64 bits (con tcl/tk incluido).
Las librerías se instalan solas en la primera ejecución.
"""

import subprocess
import sys
import os
import platform
import struct
import traceback
import datetime

# Evita errores de codificación en consolas de Windows
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

LOG_ERRORES = os.path.join(os.path.expanduser("~"), "croquis_error.log")


def pausar_y_salir(mensaje, codigo=1):
    """Muestra un mensaje y espera Enter para que la consola NO se cierre sola."""
    print("\n" + "=" * 60)
    print(mensaje)
    print("=" * 60)
    try:
        input("\nPresione Enter para cerrar...")
    except Exception:
        pass
    sys.exit(codigo)


def registrar_error(texto):
    try:
        with open(LOG_ERRORES, "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}]\n{texto}\n")
    except Exception:
        pass


# ─────────────────────────────────────────────
# VERIFICACIONES DEL ENTORNO
# ─────────────────────────────────────────────

def verificar_entorno():
    print("\n" + "=" * 60)
    print("  GENERADOR DE CROQUIS DE CONSTRUCCIONES")
    print("=" * 60)
    version = sys.version_info
    bits = struct.calcsize("P") * 8
    print(f"\n  Python {version.major}.{version.minor}.{version.micro} "
          f"({bits} bits) en {platform.system()}")

    if version < (3, 9):
        pausar_y_salir("Python demasiado antiguo. Instale Python 3.10, 3.11 o 3.12 "
                       "de 64 bits desde python.org")
    if bits != 64:
        pausar_y_salir("Está usando Python de 32 bits. geopandas/pyogrio no tienen "
                       "versiones para 32 bits.\nInstale Python de 64 bits desde "
                       "python.org (recomendado 3.10, 3.11 o 3.12).")
    if version >= (3, 13):
        print("\n  [AVISO] Python 3.13 o superior: si falla la instalación de "
              "librerías,\n          use Python 3.11 o 3.12.")

    # tkinter no se instala con pip: se verifica aparte
    try:
        import tkinter  # noqa: F401
    except ImportError:
        sistema = platform.system()
        if sistema == "Windows":
            ayuda = ("Reinstale Python desde python.org y marque la opción\n"
                     "'tcl/tk and IDLE' en la instalación personalizada.")
        elif sistema == "Darwin":
            ayuda = "Ejecute en la terminal:  brew install python-tk"
        else:
            ayuda = "Ejecute en la terminal:  sudo apt install python3-tk"
        pausar_y_salir("Falta 'tkinter' (la interfaz gráfica).\n\n" + ayuda)


# ─────────────────────────────────────────────
# INSTALADOR AUTOMÁTICO DE DEPENDENCIAS
# ─────────────────────────────────────────────

def instalar_dependencias():
    """Verifica e instala las librerías necesarias (sin fiona: ya no hace falta)."""
    paquetes = {
        "numpy": "numpy",
        "matplotlib": "matplotlib",
        "shapely": "shapely",
        "pyproj": "pyproj",
        "pyogrio": "pyogrio",
        "geopandas": "geopandas",
    }

    faltantes = []
    for modulo, paquete in paquetes.items():
        try:
            __import__(modulo)
        except ImportError:
            faltantes.append(paquete)

    if not faltantes:
        print("\n  [OK] Todas las dependencias ya están instaladas.\n")
        return

    print(f"\n  Paquetes a instalar: {', '.join(faltantes)}\n")

    # Actualizar pip primero (evita muchos fallos con wheels)
    print("  -> Actualizando pip...")
    subprocess.call(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    for paquete in faltantes:
        print(f"  -> Instalando {paquete}...")
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "install", paquete],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if proc.returncode != 0:
            detalle = (proc.stderr or proc.stdout or "")[-1500:]
            registrar_error(f"Fallo instalando {paquete}\n{detalle}")
            pausar_y_salir(
                f"No se pudo instalar '{paquete}'.\n\n"
                f"Intente manualmente en CMD:\n"
                f"    python -m pip install --upgrade pip\n"
                f"    python -m pip install {paquete}\n\n"
                f"Detalle del error:\n{detalle}\n\n"
                f"(También se guardó en {LOG_ERRORES})"
            )
        print(f"    [OK] {paquete}")

    print("\n  [OK] Dependencias instaladas correctamente.\n")


verificar_entorno()
instalar_dependencias()


# ─────────────────────────────────────────────
# IMPORTACIONES (ya instaladas)
# ─────────────────────────────────────────────

import math
import tempfile
import shutil
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

import numpy as np
import geopandas as gpd
import pyogrio
import matplotlib
try:
    matplotlib.use("TkAgg")
except Exception:
    pass
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

# CRS proyectado de Colombia (MAGNA-SIRGAS Origen Nacional, en metros)
EPSG_METROS = 9377
MAX_CONSTRUCCIONES_AVISO = 30


# ─────────────────────────────────────────────
# LECTURA DE DATOS
# ─────────────────────────────────────────────

def leer_capa(ruta, capa=None):
    """Lee una capa con pyogrio; si la versión de geopandas no lo soporta, usa el motor por defecto."""
    kwargs = {}
    if capa:
        kwargs["layer"] = capa
    try:
        return gpd.read_file(ruta, engine="pyogrio", **kwargs)
    except (ValueError, TypeError, ImportError):
        return gpd.read_file(ruta, **kwargs)


def listar_capas_gdb(ruta_gdb):
    """Lista las capas de un GDB usando pyogrio."""
    try:
        return [str(c[0]) for c in pyogrio.list_layers(ruta_gdb)]
    except Exception as e:
        raise ValueError(
            f"No se pudo leer el GDB: {e}\n\n"
            "Verifique que sea una File Geodatabase (.gdb) válida y completa."
        )


def extraer_zip(ruta_zip):
    """
    Extrae el .zip a una carpeta temporal y busca shapefiles (.shp) y GDB (.gdb)
    en cualquier nivel de carpetas.
    Devuelve (temp_dir, lista_shp, lista_gdb).
    """
    temp_dir = tempfile.mkdtemp(prefix="croquis_")
    try:
        with zipfile.ZipFile(ruta_zip, "r") as zf:
            zf.extractall(temp_dir)
    except zipfile.BadZipFile:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise ValueError("El archivo seleccionado no es un .zip válido.")
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise

    lista_shp, lista_gdb = [], []
    for raiz, dirs, archivos in os.walk(temp_dir):
        if "__MACOSX" in raiz:
            continue
        for d in dirs:
            if d.lower().endswith(".gdb"):
                lista_gdb.append(os.path.join(raiz, d))
        for f in archivos:
            if f.lower().endswith(".shp") and not f.startswith("._"):
                lista_shp.append(os.path.join(raiz, f))

    # Un shapefile necesita al menos .shx y .dbf junto al .shp
    shp_validos, faltantes = [], []
    for shp in lista_shp:
        base = os.path.splitext(shp)[0]
        existentes = {e.lower() for e in os.listdir(os.path.dirname(shp))
                      if os.path.splitext(e)[0] == os.path.basename(base)}
        if not os.path.exists(base + ".dbf") and ".dbf" not in {os.path.splitext(e)[1] for e in existentes}:
            faltantes.append(f"{os.path.basename(shp)} (falta .dbf)")
        else:
            shp_validos.append(shp)

    if not shp_validos and not lista_gdb:
        shutil.rmtree(temp_dir, ignore_errors=True)
        detalle = ("\nArchivos .shp incompletos: " + ", ".join(faltantes)) if faltantes else ""
        raise FileNotFoundError(
            "No se encontró ningún .shp ni .gdb válido dentro del .zip." + detalle
        )
    return temp_dir, shp_validos, lista_gdb


def seleccionar_de_lista(parent, titulo, mensaje, opciones):
    """Diálogo genérico para elegir un elemento de una lista."""
    if not opciones:
        return None
    if len(opciones) == 1:
        return opciones[0]

    dialogo = tk.Toplevel(parent)
    dialogo.title(titulo)
    dialogo.geometry("520x330")
    dialogo.resizable(False, False)
    dialogo.grab_set()
    dialogo.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() // 2) - 260
    y = parent.winfo_y() + (parent.winfo_height() // 2) - 165
    dialogo.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    tk.Label(dialogo, text=mensaje, font=("Segoe UI", 10), pady=10).pack()

    frame_lista = tk.Frame(dialogo)
    frame_lista.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
    scrollbar = tk.Scrollbar(frame_lista)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox = tk.Listbox(frame_lista, font=("Consolas", 9),
                         yscrollcommand=scrollbar.set, selectmode=tk.SINGLE,
                         exportselection=False)
    listbox.pack(fill=tk.BOTH, expand=True)
    scrollbar.config(command=listbox.yview)
    for opcion in opciones:
        listbox.insert(tk.END, opcion)
    listbox.select_set(0)

    resultado = [None]

    def confirmar():
        sel = listbox.curselection()
        if sel:
            resultado[0] = opciones[sel[0]]
        dialogo.destroy()

    frame_btns = tk.Frame(dialogo)
    frame_btns.pack(pady=10)
    tk.Button(frame_btns, text="Seleccionar", font=("Segoe UI", 9, "bold"),
              bg="#2c3e50", fg="white", padx=15, pady=5,
              command=confirmar).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_btns, text="Cancelar", font=("Segoe UI", 9),
              padx=15, pady=5, command=dialogo.destroy).pack(side=tk.LEFT, padx=5)

    dialogo.wait_window()
    return resultado[0]


def preparar_gdf(gdf):
    """
    Limpia geometrías, deja solo polígonos y reproyecta a metros si el CRS
    está en grados. Devuelve (gdf, aviso).
    """
    gdf = gdf[gdf.geometry.notna()].copy()
    gdf = gdf[~gdf.geometry.is_empty].copy()
    gdf = gdf[gdf.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    if gdf.empty:
        raise ValueError(
            "La capa no contiene polígonos (Polygon / MultiPolygon).\n"
            "Seleccione una capa de polígonos."
        )

    aviso = ""
    if gdf.crs is None:
        aviso = ("AVISO: la capa no tiene CRS definido. Las cotas se calculan "
                 "en las unidades originales (pueden no ser metros).")
    elif gdf.crs.is_geographic:
        gdf = gdf.to_crs(epsg=EPSG_METROS)
        aviso = (f"Capa en coordenadas geográficas: se reproyectó a "
                 f"EPSG:{EPSG_METROS} para obtener cotas en metros.")
    return gdf, aviso


# ─────────────────────────────────────────────
# FUNCIONES GEOMÉTRICAS
# ─────────────────────────────────────────────

def calcular_largo_lado(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def punto_medio(p1, p2):
    return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)


def angulo_lado(p1, p2):
    return math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))


def detectar_campo_id(gdf):
    """Detecta automáticamente el campo identificador de la construcción."""
    posibles = [
        "id", "cod", "codigo", "code", "identificador", "id_const",
        "id_construccion", "construccion", "predio", "id_predio",
        "lote", "id_lote", "manzana", "ficha", "npn", "matricula",
        "objectid", "fid", "gid", "num", "numero"
    ]
    columnas = [c for c in gdf.columns if c != "geometry"]
    columnas_lower = [c.lower() for c in columnas]

    for nombre in posibles:                       # coincidencia exacta
        if nombre in columnas_lower:
            return columnas[columnas_lower.index(nombre)]
    for nombre in posibles:                       # coincidencia parcial
        for i, col in enumerate(columnas_lower):
            if nombre in col:
                return columnas[i]
    return None


def detectar_campo_pisos(gdf):
    """Detecta automáticamente el campo con el número de pisos."""
    posibles = [
        "pisos", "piso", "niveles", "nivel", "floors", "floor",
        "num_pisos", "n_pisos", "nro_pisos", "numero_pisos",
        "altura", "plantas", "planta", "npisos", "npiso"
    ]
    columnas = [c for c in gdf.columns if c != "geometry"]
    columnas_lower = [c.lower() for c in columnas]
    for nombre in posibles:
        for i, col in enumerate(columnas_lower):
            if nombre in col:
                return columnas[i]
    return None


def dibujar_poligono_con_cotas(ax, geom, color_fill, color_edge):
    """Dibuja un polígono con sus cotas (incluye huecos interiores)."""
    if isinstance(geom, MultiPolygon):
        poligonos = list(geom.geoms)
    elif isinstance(geom, Polygon):
        poligonos = [geom]
    else:
        return

    for poly in poligonos:
        if poly.is_empty:
            continue
        xs, ys = poly.exterior.xy
        ax.fill(xs, ys, alpha=0.20, color=color_fill, zorder=1)
        ax.plot(xs, ys, color=color_edge, linewidth=1.8, zorder=2)

        # Huecos interiores (patios, etc.)
        for hueco in poly.interiors:
            hx, hy = hueco.xy
            ax.plot(hx, hy, color=color_edge, linewidth=1.0,
                    linestyle="--", zorder=2)

        coords = list(poly.exterior.coords)
        centroid = poly.centroid

        for i in range(len(coords) - 1):
            p1, p2 = coords[i], coords[i + 1]
            largo = calcular_largo_lado(p1, p2)
            if largo < 0.01:
                continue

            pm = punto_medio(p1, p2)
            angulo = angulo_lado(p1, p2)

            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            nx, ny = -dy / largo, dx / largo

            # Orientar la cota hacia afuera del polígono
            if (nx * (pm[0] - centroid.x) + ny * (pm[1] - centroid.y)) < 0:
                nx, ny = -nx, -ny

            offset = largo * 0.15
            label_x = pm[0] + nx * offset
            label_y = pm[1] + ny * offset

            ang_text = angulo
            if ang_text > 90:
                ang_text -= 180
            elif ang_text < -90:
                ang_text += 180

            ax.annotate(
                f"{largo:.2f} m",
                xy=(label_x, label_y),
                fontsize=6.5, fontweight="bold", color="#c0392b",
                ha="center", va="center",
                rotation=ang_text, rotation_mode="anchor",
                bbox=dict(boxstyle="round,pad=0.12", facecolor="white",
                          edgecolor="#e74c3c", alpha=0.85, linewidth=0.5),
                zorder=5
            )

        for i in range(len(coords) - 1):
            ax.plot(coords[i][0], coords[i][1], "o",
                    color=color_edge, markersize=3.5, zorder=4)


def generar_croquis(gdf, campo_id=None, campo_pisos=None, ruta_salida=None):
    """Genera la figura con un croquis por construcción (agrupadas por ID)."""
    n_total = len(gdf)
    if n_total == 0:
        raise ValueError("El archivo no contiene polígonos.")

    gdf = gdf.copy()
    if campo_id and campo_id in gdf.columns:
        gdf[campo_id] = gdf[campo_id].fillna("SIN_ID").astype(str)
        grupos = gdf.groupby(campo_id, sort=True)
        ids_unicos = list(grupos.groups.keys())
    else:
        ids_unicos = list(range(n_total))
        grupos = None

    n_construcciones = len(ids_unicos)

    paleta_fill = ["#3498db", "#2ecc71", "#e67e22", "#9b59b6",
                   "#1abc9c", "#e74c3c", "#f39c12", "#34495e"]
    paleta_edge = ["#2c3e50", "#27ae60", "#d35400", "#8e44ad",
                   "#16a085", "#c0392b", "#f1c40f", "#2c3e50"]

    cols = max(1, math.ceil(math.sqrt(n_construcciones)))
    rows = max(1, math.ceil(n_construcciones / cols))

    fig, axes = plt.subplots(rows, cols,
                             figsize=(max(12, cols * 6), max(8, rows * 6)),
                             squeeze=False)
    fig.patch.set_facecolor("#FAFAFA")
    fig.suptitle("CROQUIS DE CONSTRUCCIONES", fontsize=18, fontweight="bold",
                 color="#1a1a2e", y=0.98)

    idx = 0
    for row in range(rows):
        for col in range(cols):
            ax = axes[row, col]
            if idx >= n_construcciones:
                ax.axis("off")
                continue

            id_actual = ids_unicos[idx]
            grupo = (grupos.get_group(id_actual) if grupos is not None
                     else gdf.iloc[[id_actual]])

            pisos = None
            if campo_pisos and campo_pisos in gdf.columns:
                try:
                    valores = grupo[campo_pisos].dropna()
                    if len(valores) > 0:
                        pisos = int(float(valores.max()))
                except (ValueError, TypeError):
                    pisos = None

            area_total, perimetro_total, todas_geoms = 0.0, 0.0, []
            for i, (_, feat) in enumerate(grupo.iterrows()):
                geom = feat.geometry
                if geom is None or geom.is_empty:
                    continue
                dibujar_poligono_con_cotas(ax, geom,
                                           paleta_fill[i % len(paleta_fill)],
                                           paleta_edge[i % len(paleta_edge)])
                area_total += geom.area
                perimetro_total += geom.length
                todas_geoms.append(geom)

            if not todas_geoms:
                ax.axis("off")
                idx += 1
                continue

            union_geom = unary_union(todas_geoms)
            centroid = union_geom.representative_point()  # siempre dentro de la figura

            info_text = f"{id_actual}"
            if pisos is not None:
                info_text += f'\n{pisos} piso{"s" if pisos != 1 else ""}'
            ax.text(centroid.x, centroid.y, info_text, ha="center", va="center",
                    fontsize=9, fontweight="bold", color="#1a1a2e",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="#f39c12",
                              edgecolor="#e67e22", alpha=0.85, linewidth=1),
                    zorder=6)

            titulo = f"Construcción: {id_actual}"
            if pisos is not None:
                titulo += f'  |  {pisos} piso{"s" if pisos != 1 else ""}'
            if len(grupo) > 1:
                titulo += f"  |  {len(grupo)} partes"
            ax.set_title(titulo, fontsize=9, fontweight="bold",
                         color="#2c3e50", pad=8)

            ax.text(0.5, -0.05,
                    f"Área total: {area_total:.2f} m²  |  Perímetro total: {perimetro_total:.2f} m",
                    ha="center", va="top", transform=ax.transAxes,
                    fontsize=7, color="#7f8c8d", style="italic")

            ax.set_aspect("equal")
            ax.grid(True, alpha=0.2, linestyle="--")
            ax.tick_params(labelsize=6, colors="#95a5a6")

            b = union_geom.bounds
            mx = max((b[2] - b[0]) * 0.3, 0.5)
            my = max((b[3] - b[1]) * 0.3, 0.5)
            ax.set_xlim(b[0] - mx, b[2] + mx)
            ax.set_ylim(b[1] - my, b[3] + my)

            idx += 1

    plt.tight_layout(rect=[0, 0.02, 1, 0.96])

    if ruta_salida:
        fig.savefig(ruta_salida, dpi=200, bbox_inches="tight",
                    facecolor="#FAFAFA", edgecolor="none")
    return fig


# ─────────────────────────────────────────────
# INTERFAZ GRÁFICA
# ─────────────────────────────────────────────

class AplicacionCroquis:
    def __init__(self, root):
        self.root = root
        self.root.title("Generador de Croquis de Construcciones")
        self.root.resizable(True, True)
        self.root.configure(bg="#f0f2f5")

        self.ruta_archivo = tk.StringVar()
        self.campo_id_var = tk.StringVar()
        self.campo_pisos_var = tk.StringVar()
        self.temp_dir = None
        self.gdf = None
        self.fig = None

        self._crear_interfaz()

    def _crear_interfaz(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"),
                        background="#f0f2f5", foreground="#1a1a2e")
        style.configure("Subtitle.TLabel", font=("Segoe UI", 9),
                        background="#f0f2f5", foreground="#6c757d")
        style.configure("Section.TLabelframe", background="#f0f2f5")
        style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"),
                        background="#f0f2f5", foreground="#2c3e50")
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"),
                        padding=(20, 10))
        style.configure("Browse.TButton", font=("Segoe UI", 9), padding=(10, 5))

        main = ttk.Frame(self.root, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Generador de Croquis",
                  style="Title.TLabel").pack(pady=(0, 2))
        ttk.Label(main, text="Genera croquis técnicos desde Shapefile (.zip / .shp) o GDB (.gdb)",
                  style="Subtitle.TLabel").pack(pady=(0, 15))

        # Archivo
        f_arch = ttk.LabelFrame(main, text="  Archivo de entrada  ",
                                style="Section.TLabelframe", padding=15)
        f_arch.pack(fill=tk.X, pady=(0, 10))
        fila = ttk.Frame(f_arch)
        fila.pack(fill=tk.X)
        ttk.Entry(fila, textvariable=self.ruta_archivo, font=("Segoe UI", 9),
                  state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(fila, text="Buscar archivo...", style="Browse.TButton",
                   command=self.buscar_archivo).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(fila, text="Abrir GDB...", style="Browse.TButton",
                   command=self.buscar_gdb).pack(side=tk.RIGHT)

        # Configuración
        f_conf = ttk.LabelFrame(main, text="  Configuración  ",
                                style="Section.TLabelframe", padding=15)
        f_conf.pack(fill=tk.X, pady=(0, 10))

        fila_id = ttk.Frame(f_conf)
        fila_id.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(fila_id, text="Campo identificador (agrupar):",
                  background="#f0f2f5").pack(side=tk.LEFT, padx=(0, 10))
        self.combo_id = ttk.Combobox(fila_id, textvariable=self.campo_id_var,
                                     state="disabled", width=25)
        self.combo_id.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.lbl_auto_id = ttk.Label(fila_id, text="", foreground="#28a745",
                                     background="#f0f2f5")
        self.lbl_auto_id.pack(side=tk.LEFT, padx=(10, 0))

        fila_pi = ttk.Frame(f_conf)
        fila_pi.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(fila_pi, text="Campo de pisos:",
                  background="#f0f2f5").pack(side=tk.LEFT, padx=(0, 10))
        self.combo_pisos = ttk.Combobox(fila_pi, textvariable=self.campo_pisos_var,
                                        state="disabled", width=25)
        self.combo_pisos.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.lbl_auto_pisos = ttk.Label(fila_pi, text="", foreground="#28a745",
                                        background="#f0f2f5")
        self.lbl_auto_pisos.pack(side=tk.LEFT, padx=(10, 0))

        # Info
        f_info = ttk.LabelFrame(main, text="  Información del archivo  ",
                                style="Section.TLabelframe", padding=15)
        f_info.pack(fill=tk.X, pady=(0, 10))
        self.text_info = tk.Text(f_info, height=9, font=("Consolas", 9),
                                 bg="#ffffff", fg="#495057", relief="flat",
                                 padx=10, pady=10, state="disabled", wrap="word")
        self.text_info.pack(fill=tk.X)

        # Botones
        f_btn = ttk.Frame(main)
        f_btn.pack(fill=tk.X, pady=(10, 0))
        self.btn_generar = ttk.Button(f_btn, text="Generar Croquis",
                                      style="Action.TButton",
                                      command=self.generar, state="disabled")
        self.btn_generar.pack(side=tk.LEFT, padx=(0, 10))
        self.btn_guardar = ttk.Button(f_btn, text="Guardar Imagen",
                                      style="Action.TButton",
                                      command=self.guardar_imagen, state="disabled")
        self.btn_guardar.pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(main, mode="indeterminate")
        self.progress.pack(fill=tk.X, pady=(10, 0))

    # ── Selección de archivos ──
    def buscar_archivo(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo (.zip o .shp)",
            filetypes=[("ZIP o Shapefile", "*.zip *.shp"),
                       ("Archivos ZIP", "*.zip"),
                       ("Archivos Shapefile", "*.shp"),
                       ("Todos los archivos", "*.*")]
        )
        if ruta:
            self.ruta_archivo.set(ruta)
            self.cargar_archivo(ruta)

    def buscar_gdb(self):
        ruta = filedialog.askdirectory(title="Seleccionar carpeta GDB (.gdb)")
        if ruta:
            self.ruta_archivo.set(ruta)
            self.cargar_archivo(ruta)

    def _limpiar_temp(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.temp_dir = None

    def cargar_archivo(self, ruta):
        self.actualizar_info("Cargando archivo...")
        self.progress.start()
        self.root.update()

        try:
            self._limpiar_temp()
            ext = Path(ruta).suffix.lower()
            nombre = Path(ruta).name
            gdf = None

            if ext == ".zip":
                self.temp_dir, lista_shp, lista_gdb = extraer_zip(ruta)
                if lista_gdb:
                    ruta_gdb = lista_gdb[0] if len(lista_gdb) == 1 else seleccionar_de_lista(
                        self.root, "Seleccionar GDB",
                        "El .zip contiene varios GDB.\nSeleccione uno:",
                        lista_gdb)
                    if ruta_gdb is None:
                        self.actualizar_info("Operación cancelada.")
                        return
                    capa = seleccionar_de_lista(
                        self.root, "Seleccionar capa",
                        "Seleccione la capa a utilizar:", listar_capas_gdb(ruta_gdb))
                    if capa is None:
                        self.actualizar_info("Operación cancelada.")
                        return
                    gdf = leer_capa(ruta_gdb, capa)
                    nombre = f"{nombre} > {capa}"
                else:
                    opciones = {os.path.relpath(p, self.temp_dir): p for p in lista_shp}
                    elegido = seleccionar_de_lista(
                        self.root, "Seleccionar shapefile",
                        "El .zip contiene varios shapefiles.\nSeleccione uno:",
                        list(opciones.keys()))
                    if elegido is None:
                        self.actualizar_info("Operación cancelada.")
                        return
                    gdf = leer_capa(opciones[elegido])
                    nombre = f"{nombre} > {elegido}"

            elif ext == ".shp":
                gdf = leer_capa(ruta)

            elif os.path.isdir(ruta):
                capa = seleccionar_de_lista(
                    self.root, "Seleccionar capa",
                    "Seleccione la capa a utilizar:", listar_capas_gdb(ruta))
                if capa is None:
                    self.actualizar_info("Operación cancelada.")
                    return
                gdf = leer_capa(ruta, capa)
                nombre = f"{nombre} > {capa}"
            else:
                raise ValueError(f"Formato no soportado: {ext}\n"
                                 "Use .zip, .shp o una carpeta .gdb")

            gdf, aviso = preparar_gdf(gdf)
            self.gdf = gdf

            campos = [c for c in gdf.columns if c != "geometry"]
            lineas = [f"Archivo: {nombre}",
                      f"Total de polígonos: {len(gdf)}",
                      f"CRS: {gdf.crs}",
                      f"Columnas: {', '.join(campos)}"]
            if aviso:
                lineas.append(aviso)

            opciones_combo = ["(ninguno)"] + campos
            self.combo_id["values"] = opciones_combo
            self.combo_id["state"] = "readonly"
            self.combo_pisos["values"] = opciones_combo
            self.combo_pisos["state"] = "readonly"

            campo_id = detectar_campo_id(gdf)
            if campo_id:
                self.campo_id_var.set(campo_id)
                n = gdf[campo_id].nunique()
                self.lbl_auto_id.config(text=f"Detectado ({n} construcciones)")
                lineas.append(f"Construcciones únicas (por '{campo_id}'): {n}")
            else:
                self.campo_id_var.set("(ninguno)")
                self.lbl_auto_id.config(text="No detectado")
                lineas.append(f"Construcciones: {len(gdf)} (sin agrupar)")

            campo_pisos = detectar_campo_pisos(gdf)
            if campo_pisos:
                self.campo_pisos_var.set(campo_pisos)
                self.lbl_auto_pisos.config(text="Detectado")
            else:
                self.campo_pisos_var.set("(ninguno)")
                self.lbl_auto_pisos.config(text="No detectado")

            self.actualizar_info("\n".join(lineas))
            self.btn_generar["state"] = "normal"

        except Exception as e:
            registrar_error(traceback.format_exc())
            messagebox.showerror("Error", f"No se pudo cargar el archivo:\n\n{e}")
            self.actualizar_info(f"Error: {e}")
            self.btn_generar["state"] = "disabled"
        finally:
            self.progress.stop()

    def actualizar_info(self, texto):
        self.text_info.config(state="normal")
        self.text_info.delete("1.0", tk.END)
        self.text_info.insert("1.0", texto)
        self.text_info.config(state="disabled")

    def generar(self):
        if self.gdf is None:
            messagebox.showwarning("Aviso", "Primero seleccione un archivo.")
            return

        campo_id = self.campo_id_var.get()
        campo_id = None if campo_id in ("", "(ninguno)") else campo_id
        campo_pisos = self.campo_pisos_var.get()
        campo_pisos = None if campo_pisos in ("", "(ninguno)") else campo_pisos

        n = self.gdf[campo_id].nunique() if campo_id else len(self.gdf)
        if n > MAX_CONSTRUCCIONES_AVISO:
            if not messagebox.askyesno(
                    "Muchas construcciones",
                    f"Se van a dibujar {n} croquis en una sola imagen.\n"
                    "Puede tardar mucho y consumir bastante memoria.\n\n"
                    "¿Desea continuar?"):
                return

        self.progress.start()
        self.root.update()
        try:
            if self.fig:
                plt.close(self.fig)
            self.fig = generar_croquis(self.gdf, campo_id=campo_id,
                                       campo_pisos=campo_pisos)
            plt.show(block=False)
            self.btn_guardar["state"] = "normal"
            self.actualizar_info(self.text_info.get("1.0", tk.END).strip()
                                 + "\n\nCroquis generados exitosamente.")
        except Exception as e:
            registrar_error(traceback.format_exc())
            messagebox.showerror("Error", f"Error al generar los croquis:\n\n{e}")
        finally:
            self.progress.stop()

    def guardar_imagen(self):
        if self.fig is None:
            messagebox.showwarning("Aviso", "Primero genere los croquis.")
            return
        ruta = filedialog.asksaveasfilename(
            title="Guardar imagen", defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"),
                       ("PDF", "*.pdf"), ("SVG", "*.svg")]
        )
        if ruta:
            try:
                self.fig.savefig(ruta, dpi=300, bbox_inches="tight",
                                 facecolor="#FAFAFA", edgecolor="none")
                messagebox.showinfo("Éxito", f"Imagen guardada en:\n{ruta}")
            except Exception as e:
                registrar_error(traceback.format_exc())
                messagebox.showerror("Error", f"No se pudo guardar:\n\n{e}")

    def cerrar(self):
        self._limpiar_temp()
        if self.fig:
            plt.close(self.fig)
        plt.close("all")
        self.root.destroy()


# ─────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────

def main():
    root = tk.Tk()
    ancho, alto = 780, 680
    x = (root.winfo_screenwidth() // 2) - (ancho // 2)
    y = (root.winfo_screenheight() // 2) - (alto // 2)
    root.geometry(f"{ancho}x{alto}+{max(x, 0)}+{max(y, 0)}")

    app = AplicacionCroquis(root)
    root.protocol("WM_DELETE_WINDOW", app.cerrar)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        detalle = traceback.format_exc()
        registrar_error(detalle)
        pausar_y_salir("ERROR INESPERADO:\n\n" + detalle +
                       f"\n(Guardado también en {LOG_ERRORES})")
