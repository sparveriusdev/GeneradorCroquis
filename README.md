<!--
==============================================================================
Archivo  : README.md
Proyecto : Generador de Croquis
------------------------------------------------------------------------------
CHANGELOG (versión interna del documento)
  v1.2.0 | 2026-11-05 | Enlaces al manual de uso, CONTRIBUTING y licencia GPL-3.0.
  v1.1.0 | 2026-11-05 | Documenta la pestaña "Acerca de" y las actualizaciones.
  v1.0.0 | 2026-11-05 | Creación. Descripción, instalación, uso, arquitectura,
         |            | desarrollo con uv, versionado SemVer, convención de
         |            | cabeceras, proceso de release multiplataforma y créditos.
==============================================================================
-->
# Generador de Croquis

Aplicación de escritorio que genera **croquis técnicos acotados** de construcciones a partir
de datos vectoriales (Shapefile, `.zip` o File Geodatabase). Agrupa los polígonos que comparten
un identificador y produce una lámina con un croquis por construcción: medida de cada lado,
número de pisos, área y perímetro.

## Características

- Entradas: `.shp`, `.zip` (con shapefiles y/o `.gdb` en cualquier subcarpeta) y carpetas `.gdb`.
- Detección automática del campo identificador y del campo de pisos (editables).
- Reproyección automática a **EPSG:9377** (MAGNA-SIRGAS Origen Nacional) cuando la capa está
  en coordenadas geográficas, para que las cotas salgan en metros.
- Soporte de polígonos con huecos (patios) y multipolígonos.
- Vista previa con zoom y exportación a PNG, JPG, PDF o SVG (300 dpi).

## Descarga (usuarios finales)

En la sección **Releases** del repositorio están los ejecutables de cada versión:

| Sistema | Archivo | Cómo abrirlo |
|---|---|---|
| Windows 10/11 (64 bits) | `GeneradorCroquis-X.Y.Z-windows-x64.exe` | Doble clic. Si SmartScreen avisa: *Más información → Ejecutar de todas formas*. |
| Linux x64 | `GeneradorCroquis-X.Y.Z-linux-x64.tar.gz` | `tar xzf …` y luego `./GeneradorCroquis` |
| macOS (Apple Silicon) | `GeneradorCroquis-X.Y.Z-macos-arm64.zip` | Descomprimir; la primera vez: clic derecho → *Abrir*. |

`SHA256SUMS.txt` permite verificar la integridad de las descargas.

> Los ejecutables no están firmados digitalmente, por eso Windows y macOS muestran
> una advertencia la primera vez.

## Uso

> 📘 Guía completa para usuarios: **[Manual de uso](docs/MANUAL_DE_USO.md)**
> (instalación, preparación de datos, lectura de croquis y solución de problemas).

1. **Buscar archivo...** (`.zip` / `.shp`) o **Abrir GDB...** (carpeta `.gdb`).
2. Si hay varias capas o archivos, elegir uno en el diálogo.
3. Revisar el **campo identificador** (agrupa polígonos de la misma construcción) y el
   **campo de pisos**. `(ninguno)` dibuja un croquis por polígono.
4. **Generar Croquis** → se abre la vista previa.
5. **Guardar Imagen** para exportar.

Desde la terminal también se puede abrir un archivo directamente:

```bash
generador-croquis ruta/a/datos.zip
generador-croquis --version
```

Los errores se registran en `~/.generador_croquis/croquis.log`.

### Actualizaciones (pestaña «Acerca de»)

La pestaña **Acerca de** muestra la versión instalada y los créditos. **Comprobar
actualizaciones** consulta el último release publicado en GitHub. Si hay uno más reciente,
**Descargar vX.Y.Z** guarda el ejecutable de su sistema en la carpeta que elija; luego basta con
cerrar la aplicación y abrir el archivo descargado. La aplicación solo se conecta a internet
cuando se pulsa ese botón.

## Desarrollo

¿Quiere contribuir? Lea **[CONTRIBUTING.md](CONTRIBUTING.md)**.

Requisitos: [uv](https://docs.astral.sh/uv/) y Python 3.11 – 3.13 con tkinter.

```bash
uv sync                      # crea .venv e instala dependencias + herramientas de desarrollo
uv run generador-croquis     # ejecuta la aplicación
uv run pytest                # pruebas
uv run ruff check .          # lint
uv run ruff format .         # formato
```

### Construir el ejecutable localmente

```bash
uv run pyinstaller packaging/generador_croquis.spec --noconfirm
# Resultado en dist/: GeneradorCroquis.exe (Windows), GeneradorCroquis (Linux), GeneradorCroquis.app (macOS)
```

> **Importante:** el Python que descarga uv incluye Tcl/Tk 9, que PyInstaller todavía no
> empaqueta bien (el ejecutable arranca sin interfaz gráfica). Para construir, use un
> Python de python.org o del sistema:
> `uv sync --python /ruta/a/python3.12` (en Windows, por ejemplo, `--python C:\Python312\python.exe`).
> El CI ya lo hace así.

## Arquitectura

Patrón **Modelo-Vista-Controlador** con capas y dependencias que apuntan hacia el dominio:

```
src/generador_croquis/
├── app.py                 # Raíz de composición: crea e inyecta dependencias
├── config.py              # Constantes y parámetros (tema, cotas, EPSG, umbrales)
├── logging_config.py      # Log rotativo
├── domain/                # MODELO: entidades inmutables y excepciones
│   ├── models.py          #   Construccion, Cota, CapaCargada, ResumenCapa, SeleccionCampos
│   └── exceptions.py
├── data/                  # Acceso a datos (Strategy por formato)
│   ├── fuentes.py         #   FuenteShapefile, FuenteGdb, FuenteZip
│   ├── lector.py          #   LectorCapas: elige la fuente adecuada
│   └── http.py            #   TransporteUrllib: API de GitHub y descargas
├── services/              # LÓGICA DE NEGOCIO (sin interfaz)
│   ├── geometria.py       #   cálculo de cotas
│   ├── deteccion_campos.py
│   ├── preparacion.py     #   limpieza y reproyección
│   ├── agrupacion.py      #   polígonos → construcciones
│   ├── servicio_croquis.py#   fachada de casos de uso
│   └── actualizaciones.py #   último release vs. versión instalada
├── rendering/             # Dibujo con matplotlib (sin pyplot)
├── controller/            # CONTROLADORES + protocolos de vista
│   ├── controlador.py     #   generador de croquis
│   └── acerca_de.py       #   pestaña «Acerca de» y actualizaciones
└── view/                  # VISTA Tkinter (única capa que importa tkinter)
    ├── ventana_principal.py  # pestañas «Generador» y «Acerca de»
    ├── pestana_acerca_de.py
    └── ejecutor_tk.py     #   tareas en segundo plano sin congelar la interfaz
```

Cómo se aplican los principios **SOLID** y **DRY**:

| Principio | Dónde |
|---|---|
| Responsabilidad única | Leer, preparar, agrupar, dibujar y mostrar están en módulos distintos. |
| Abierto/cerrado | Un formato nuevo es una clase `FuenteDatos` más registrada en `LectorCapas`. |
| Sustitución de Liskov | Cualquier `Renderizador` o `VistaCroquis` sirve; las pruebas usan una vista falsa. |
| Segregación de interfaces | Protocolos pequeños: `Selector`, `FuenteDatos`, `Renderizador`, `VistaCroquis`. |
| Inversión de dependencias | El controlador depende de `VistaCroquis` (protocolo), no de Tkinter; todo se inyecta en `app.py`. |
| DRY | Un solo algoritmo de detección de campos, un único manejo de errores en el controlador y la configuración centralizada en `config.py`. |

## Versionado (SemVer)

- La versión vive en **un solo lugar**: `src/generador_croquis/__init__.py` (`__version__`).
  `pyproject.toml` la lee de ahí.
- `MAJOR.MINOR.PATCH`: MAJOR = cambios incompatibles, MINOR = funcionalidad nueva compatible,
  PATCH = correcciones. Prerelease: `1.1.0-rc.1`.
- Cada versión se documenta en `CHANGELOG.md`.

### Publicar una versión

```bash
# 1. Actualizar __version__ y mover las notas de [Unreleased] a la nueva sección en CHANGELOG.md
# 2. Confirmar y etiquetar
git commit -am "chore(release): v1.1.0"
git tag v1.1.0
git push origin main --tags
```

El flujo `Release` valida que el tag coincida con `__version__`, ejecuta las pruebas, construye
los ejecutables de Windows, Linux y macOS y publica un GitHub Release con las notas del
CHANGELOG y los binarios. También puede ejecutarse a mano (*Actions → Release → Run workflow*)
para obtener los binarios como artefactos sin publicar un release.

## Convención de cabeceras

Cada archivo nuevo o modificado lleva en su cabecera un **changelog interno** con la versión
del documento (independiente de la versión de la aplicación), la fecha y los cambios:

```python
# ==============================================================================
# Archivo  : src/generador_croquis/ejemplo.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.1.0 | 2026-12-01 | Descripción del cambio más reciente (va primero).
#   v1.0.0 | 2026-11-05 | Creación.
# ==============================================================================
```

En Markdown se usa el mismo bloque dentro de un comentario HTML `<!-- … -->`.

## Créditos

- **Gabriel Gómez Baena**: autor de la idea original y del script base (`legacy/generador_v1.py`).
- **David Vásquez** ([@sparveriusdev](https://github.com/sparveriusdev)): arquitectura y desarrollo
  de las nuevas versiones.

## Licencia

Copyright © 2026 Gabriel Gómez Baena y David Vásquez.

Este programa es software libre: puede redistribuirlo y/o modificarlo bajo los términos de la
**Licencia Pública General GNU** publicada por la Free Software Foundation, ya sea la versión 3
de la licencia o (a su elección) cualquier versión posterior. Se distribuye con la esperanza de
que sea útil, pero **SIN NINGUNA GARANTÍA**. Consulte el archivo [LICENSE](LICENSE).
