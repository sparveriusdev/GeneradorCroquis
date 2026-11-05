<!--
==============================================================================
Archivo  : README.md
Proyecto : Generador de Croquis
------------------------------------------------------------------------------
CHANGELOG (versión interna del documento)
  v2.2.1 | 2026-11-05 | 1.2.1: vista desde arriba, cotas con color del piso y
         |            | enlace a la hoja de ruta (ROADMAP.md).
  v2.2.0 | 2026-11-05 | Características de la 1.2.0: convenciones por piso y
         |            | unidades superpuestas visibles.
  v2.1.0 | 2026-11-05 | Características de la 1.1.0: acotado por vértices
         |            | principales, color por unidad y cotas sin solapes.
  v2.0.0 | 2026-11-05 | Rediseño visual siguiendo el estilo del perfil del
         |            | autor: cabecera centrada con logo y badges, botones de
         |            | descarga por sistema, galería de capturas, diagramas
         |            | Mermaid de arquitectura y de release, tech stack con
         |            | badges y secciones técnicas plegables. Documenta la
         |            | interfaz Material, la pestaña Ayuda y el logo (1.0.2).
  v1.2.1 | 2026-11-05 | Título «Versionado» (cambio del autor).
  v1.2.0 | 2026-11-05 | Enlaces al manual de uso, CONTRIBUTING y licencia GPL-3.0.
  v1.1.0 | 2026-11-05 | Documenta la pestaña "Acerca de" y las actualizaciones.
  v1.0.0 | 2026-11-05 | Creación. Descripción, instalación, uso, arquitectura,
         |            | desarrollo con uv, versionado SemVer, convención de
         |            | cabeceras, proceso de release multiplataforma y créditos.
==============================================================================
-->
<div align="center">

<img src="src/generador_croquis/assets/logo.png" alt="Logo de Generador de Croquis" width="140" />

# Generador de Croquis

### 📐 Croquis técnicos acotados de construcciones, en un clic

Convierte capas de polígonos de **Shapefile**, **ZIP** o **File Geodatabase** en láminas
con la medida de cada lado, el área, el perímetro y el número de pisos.

[![Release](https://img.shields.io/github/v/release/sparveriusdev/GeneradorCroquis?style=flat&label=versión&color=0061A4)](https://github.com/sparveriusdev/GeneradorCroquis/releases/latest)
[![CI](https://img.shields.io/github/actions/workflow/status/sparveriusdev/GeneradorCroquis/ci.yml?branch=main&style=flat&label=CI&logo=githubactions&logoColor=white)](https://github.com/sparveriusdev/GeneradorCroquis/actions/workflows/ci.yml)
[![Descargas](https://img.shields.io/github/downloads/sparveriusdev/GeneradorCroquis/total?style=flat&label=descargas&color=2E7D32)](https://github.com/sparveriusdev/GeneradorCroquis/releases)
[![Licencia](https://img.shields.io/badge/licencia-GPL--3.0-blue?style=flat)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%20|%203.12%20|%203.13-3776AB?style=flat&logo=python&logoColor=white)](pyproject.toml)
[![Plataformas](https://img.shields.io/badge/plataformas-Windows%20|%20macOS%20|%20Linux-lightgrey?style=flat)](#-descarga)

<br/>

[![Descargar para Windows](https://img.shields.io/badge/Descargar-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/sparveriusdev/GeneradorCroquis/releases/latest)
[![Descargar para macOS](https://img.shields.io/badge/Descargar-macOS-000000?style=for-the-badge&logo=apple&logoColor=white)](https://github.com/sparveriusdev/GeneradorCroquis/releases/latest)
[![Descargar para Linux](https://img.shields.io/badge/Descargar-Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)](https://github.com/sparveriusdev/GeneradorCroquis/releases/latest)

[📘 Manual de uso](docs/MANUAL_DE_USO.md) ·
[📝 Novedades](CHANGELOG.md) ·
[🗺️ Hoja de ruta](ROADMAP.md) ·
[🐛 Reportar un problema](https://github.com/sparveriusdev/GeneradorCroquis/issues) ·
[🤝 Contribuir](CONTRIBUTING.md)

<br/>

<img src="docs/img/pestana_generador.png" alt="Pestaña Generador" width="820" />

</div>

---

## ✨ Características

| | |
|---|---|
| 📂 **Múltiples formatos** | `.shp`, `.zip` (con shapefiles o `.gdb` en cualquier subcarpeta) y carpetas File Geodatabase. Si hay varias capas, el programa pregunta cuál usar. |
| 🧠 **Detección automática** | Reconoce los campos de identificador (`codigo`, `npn`, `predio`, `objectid`…) y de pisos (`pisos`, `niveles`, `floors`…). |
| 🧱 **Agrupación inteligente** | Los polígonos con el mismo identificador forman una sola construcción, con todas sus partes. |
| 📏 **Acotado inteligente** | Solo se acotan los **vértices principales**: los de ajuste se agrupan y el lado mide la suma de sus tramos (tolerancia ajustable). |
| 🎨 **Un piso, un color** | Cada piso tiene siempre su color, y sus cotas también; un lado común se acota una vez, con el color del piso más alto. |
| 🗂️ **Convenciones por piso** | Leyenda con el color, el estilo de línea y el área de cada piso. Vista desde arriba: cada zona con el color del piso más alto, y contornos punteados para los pisos superiores. |
| 🧲 **Cotas sin solapes** | Cada etiqueta busca un hueco libre y, si se aleja, se une a su lado con una línea guía. |
| 🌐 **Medidas en metros** | Las capas en grados se reproyectan solas a **EPSG:9377** (MAGNA-SIRGAS Origen Nacional). |
| 🕳️ **Patios y multipolígonos** | Los huecos interiores se dibujan con línea punteada. |
| 🖼️ **Exportación profesional** | PNG, JPG, PDF o SVG a 300 dpi, listos para informes y anexos técnicos. |
| 🎨 **Interfaz Material Design** | Tipografía Roboto, tarjetas, pasos numerados y barra de estado que indica qué hacer después. |
| 📘 **Ayuda integrada** | El manual de uso dentro de la app, actualizado desde GitHub y disponible sin conexión. |
| 🔄 **Actualizaciones** | Comprueba y descarga la nueva versión para su sistema desde la propia aplicación. |
| 💻 **Multiplataforma** | Ejecutables para Windows, macOS y Linux. No requiere instalar Python. |

## 🖼️ Capturas

<div align="center">

| Croquis generado | Ayuda integrada | Acerca de y actualizaciones |
|:---:|:---:|:---:|
| <img src="docs/img/ejemplo_croquis.png" alt="Ejemplo de croquis" width="270" /> | <img src="docs/img/pestana_ayuda.png" alt="Pestaña Ayuda" width="270" /> | <img src="docs/img/pestana_acerca_de.png" alt="Pestaña Acerca de" width="270" /> |

</div>

## 📥 Descarga

Descargue el archivo de su sistema desde **[la última versión](https://github.com/sparveriusdev/GeneradorCroquis/releases/latest)**:

| Sistema | Archivo | Cómo abrirlo |
|---|---|---|
| 🪟 **Windows 10/11** (64 bits) | `GeneradorCroquis-X.Y.Z-windows-x64.exe` | Doble clic. Si SmartScreen avisa: *Más información → Ejecutar de todas formas*. |
| 🍎 **macOS** (Apple Silicon) | `GeneradorCroquis-X.Y.Z-macos-arm64.zip` | Descomprimir y, la primera vez, *clic derecho → Abrir*. |
| 🐧 **Linux** (x64) | `GeneradorCroquis-X.Y.Z-linux-x64.tar.gz` | `tar xzf …` y luego `./GeneradorCroquis` |

> [!NOTE]
> Los ejecutables no están firmados digitalmente, por eso Windows y macOS muestran una advertencia
> la primera vez. Puede verificar cada descarga con `SHA256SUMS.txt`.

## 🚀 Uso en 3 pasos

```mermaid
flowchart LR
    A["📂 <b>1. Abrir</b><br/>.shp · .zip · .gdb"] --> B["🧩 <b>2. Revisar campos</b><br/>identificador y pisos"]
    B --> C["📐 <b>3. Generar</b><br/>vista previa con zoom"]
    C --> D["💾 <b>Exportar</b><br/>PNG · JPG · PDF · SVG"]
```

1. **Abrir archivo…** o **Abrir carpeta GDB…**
2. Revise el *identificador de la construcción* y el *número de pisos* (se detectan solos).
3. **Generar croquis** y luego **Exportar imagen…**

También desde la terminal: `GeneradorCroquis ruta/datos.zip` · `GeneradorCroquis --version`

📘 La guía completa, con preparación de datos y solución de problemas, está en el
**[Manual de uso](docs/MANUAL_DE_USO.md)** y en la pestaña **Ayuda** de la aplicación.

## 🛠️ Tecnologías

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![GeoPandas](https://img.shields.io/badge/GeoPandas-139C5A?style=for-the-badge&logo=pandas&logoColor=white)
![Shapely](https://img.shields.io/badge/Shapely-4B8BBE?style=for-the-badge)
![GDAL](https://img.shields.io/badge/GDAL%20·%20pyogrio-5CAE58?style=for-the-badge)
![PROJ](https://img.shields.io/badge/PROJ%20·%20pyproj-2C6E9F?style=for-the-badge)
![Matplotlib](https://img.shields.io/badge/Matplotlib-11557C?style=for-the-badge)
![Tkinter](https://img.shields.io/badge/Tkinter%20·%20Material%203-0061A4?style=for-the-badge&logo=materialdesign&logoColor=white)
![uv](https://img.shields.io/badge/uv-DE5FE9?style=for-the-badge&logo=uv&logoColor=white)
![PyInstaller](https://img.shields.io/badge/PyInstaller-3E4C59?style=for-the-badge)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)
![Ruff](https://img.shields.io/badge/Ruff-D7FF64?style=for-the-badge&logo=ruff&logoColor=black)

</div>

## 🏗️ Arquitectura

Patrón **Modelo-Vista-Controlador** por capas, con dependencias que apuntan hacia el dominio y
se inyectan en `app.py`:

```mermaid
flowchart TB
    subgraph UI["🖥️ Vista · Tkinter + tema Material 3"]
        V1[Ventana principal] --- V2[Pestaña Ayuda] --- V3[Pestaña Acerca de]
    end
    subgraph CTRL["🎛️ Controladores"]
        C1[ControladorCroquis] --- C2[ControladorAyuda] --- C3[ControladorAcercaDe]
    end
    subgraph SRV["⚙️ Servicios · lógica de negocio"]
        S1[Preparación y agrupación] --- S2[Cotas y geometría] --- S3[Manual y actualizaciones]
    end
    subgraph DATA["📂 Datos"]
        D1[Shapefile · ZIP · GDB] --- D2[GitHub · HTTP]
    end
    R["🎨 Renderizado · matplotlib"]
    M[("🧱 Dominio<br/>Construccion · Cota · Version")]

    UI -- eventos --> CTRL
    CTRL -. "protocolos (VistaCroquis…)" .-> UI
    CTRL --> SRV
    SRV --> DATA
    SRV --> R
    SRV --> M
```

<details>
<summary><b>📁 Estructura del código</b></summary>

```
src/generador_croquis/
├── app.py                  # Raíz de composición: crea e inyecta dependencias
├── config.py               # Constantes y parámetros (tema del croquis, EPSG, URLs, créditos)
├── assets/                 # Logo, icono y fuentes Roboto (OFL)
├── domain/                 # MODELO: entidades inmutables, Version (SemVer) y excepciones
├── data/                   # Fuentes de datos (Strategy por formato) y transporte HTTP
├── services/               # Lógica de negocio: cotas, campos, agrupación, Markdown, ayuda, actualizaciones
├── rendering/              # Dibujo de croquis con matplotlib (sin pyplot)
├── controller/             # CONTROLADORES + protocolos de vista y del ejecutor de tareas
└── view/                   # VISTA Tkinter: tema Material, componentes, pestañas y visor Markdown
```

</details>

<details>
<summary><b>🧭 Principios SOLID y DRY aplicados</b></summary>

| Principio | Dónde |
|---|---|
| Responsabilidad única | Leer, preparar, agrupar, dibujar y mostrar viven en módulos distintos. |
| Abierto/cerrado | Un formato nuevo es otra clase `FuenteDatos` registrada en `LectorCapas`. |
| Sustitución de Liskov | Cualquier `Renderizador` o vista que cumpla el protocolo sirve; las pruebas usan vistas falsas. |
| Segregación de interfaces | Protocolos pequeños: `Selector`, `FuenteDatos`, `TransporteHttp`, `VistaCroquis`, `VistaAyuda`… |
| Inversión de dependencias | Los controladores dependen de protocolos, no de Tkinter; todo se inyecta en `app.py`. |
| DRY | Un solo algoritmo de detección de campos, manejo de errores centralizado y todos los colores y fuentes en un único tema. |

</details>

## 🧑‍💻 Desarrollo

Requisitos: [**uv**](https://docs.astral.sh/uv/) y Python 3.11 – 3.13 con tkinter.

```bash
git clone https://github.com/sparveriusdev/GeneradorCroquis.git
cd GeneradorCroquis
uv sync                      # entorno + dependencias + herramientas de desarrollo
uv run generador-croquis     # ejecuta la aplicación
uv run pytest                # pruebas
uv run ruff check . && uv run ruff format .
```

<details>
<summary><b>📦 Construir el ejecutable localmente</b></summary>

```bash
uv run pyinstaller packaging/generador_croquis.spec --noconfirm
# dist/: GeneradorCroquis.exe (Windows) · GeneradorCroquis (Linux) · GeneradorCroquis.app (macOS)
```

> [!IMPORTANT]
> El Python que descarga uv trae **Tcl/Tk 9**. PyInstaller todavía no lo empaqueta bien, y en
> Linux ese Tk no usa las fuentes del sistema (Xft), así que la interfaz se ve con tipografía
> básica. Para construir el ejecutable, o para revisar el diseño en Linux, use un Python de
> python.org o del sistema: `uv sync --python /usr/bin/python3.12`. El CI ya lo hace así.

Para regenerar los iconos tras cambiar `assets/logo.jpeg`:
`uv run python packaging/generar_iconos.py`

</details>

<details>
<summary><b>🔖 Versionado y publicación</b></summary>

La versión sigue [SemVer](https://semver.org/lang/es/) y vive en un solo lugar:
`src/generador_croquis/__init__.py`. Cada versión se documenta en [`CHANGELOG.md`](CHANGELOG.md).

```mermaid
flowchart LR
    T["🏷️ git tag vX.Y.Z"] --> V{"¿Tag = __version__?"}
    V -- sí --> P["🧪 Pruebas"]
    P --> W["🪟 .exe"] & L["🐧 Linux"] & M["🍎 .app"]
    W & L & M --> R["📦 GitHub Release<br/>+ notas del CHANGELOG<br/>+ SHA256SUMS + LICENSE"]
    V -- no --> X["❌ Falla"]
```

```bash
git commit -am "chore(release): vX.Y.Z"
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin main --tags
```

</details>

<details>
<summary><b>📝 Convención de cabeceras con changelog</b></summary>

Cada archivo nuevo o modificado lleva en su cabecera un changelog interno, con la entrada más
reciente arriba:

```python
# ==============================================================================
# Archivo  : src/generador_croquis/ejemplo.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.1.0 | 2026-12-01 | Descripción del cambio más reciente.
#   v1.0.0 | 2026-11-05 | Creación.
# ==============================================================================
```

En Markdown se usa el mismo bloque dentro de `<!-- … -->`. Más detalles en
[CONTRIBUTING.md](CONTRIBUTING.md).

</details>

## 👥 Créditos

<table>
  <tr>
    <td align="center" width="50%">
      <b>Gabriel Gómez Baena</b><br/>
      <sub>💡 Idea original y script base</sub>
    </td>
    <td align="center" width="50%">
      <a href="https://github.com/sparveriusdev"><img src="https://github.com/sparveriusdev.png" width="72" alt="David Vásquez" /></a><br/>
      <b>David Vásquez</b> · <a href="https://github.com/sparveriusdev">@sparveriusdev</a><br/>
      <sub>🏗️ Arquitectura y desarrollo de las nuevas versiones</sub>
    </td>
  </tr>
</table>

Tipografía [Roboto](https://github.com/googlefonts/roboto-3-classic) © The Roboto Project
Authors, bajo licencia SIL Open Font License 1.1.

## 📄 Licencia

Copyright © 2026 Gabriel Gómez Baena y David Vásquez.

Este programa es software libre: puede redistribuirlo y/o modificarlo bajo los términos de la
**Licencia Pública General GNU** publicada por la Free Software Foundation, ya sea la versión 3
de la licencia o (a su elección) cualquier versión posterior. Se distribuye con la esperanza de
que sea útil, pero **SIN NINGUNA GARANTÍA**. Consulte el archivo [LICENSE](LICENSE).

---

<div align="center">

### 📐 "Cada construcción tiene sus medidas; cada medida, su croquis"

Hecho en Colombia 🇨🇴 · ¿Le sirvió? Deje una ⭐ en el repositorio

</div>
