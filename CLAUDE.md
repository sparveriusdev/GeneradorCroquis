<!--
==============================================================================
Archivo  : CLAUDE.md
Proyecto : Generador de Croquis
------------------------------------------------------------------------------
CHANGELOG (versión interna del documento)
  v1.0.0 | 2026-11-05 | Creación. Guía para agentes: comandos, arquitectura,
         |            | convenciones, trampas conocidas y flujo de release.
==============================================================================
-->
# CLAUDE.md

Aplicación de escritorio (Tkinter, Material Design 3) que genera croquis acotados de
construcciones desde Shapefile, ZIP o File Geodatabase. Proyecto en español: código, mensajes,
documentación y commits. Detalle para usuarios en `README.md` y `docs/MANUAL_DE_USO.md`.

## Comandos

```bash
uv sync                                   # entorno .venv + herramientas de desarrollo
uv run generador-croquis [ruta]           # ejecutar (con guion); ruta opcional .zip/.shp/.gdb
uv run pytest                             # pruebas (sin red ni pantalla: MPLBACKEND=Agg)
uv run ruff check . && uv run ruff format --check .   # el CI exige ambos
uv run pyinstaller packaging/generador_croquis.spec --noconfirm   # ejecutable
uv run python packaging/generar_iconos.py # regenerar icono.ico/logo.png desde assets/logo.jpeg
```

Encadena las verificaciones con `&&`, nunca con `;`: si ruff falla no debe hacerse commit.

## Arquitectura (MVC por capas, `src/generador_croquis/`)

- `domain/`: entidades inmutables (`Construccion`, `Lado`, `GrupoPiso`, `OpcionesAcotado`,
  `SignificadoPisos`, `Version`) y excepciones (`CroquisError` = mensaje apto para el usuario).
  No importa de otras capas salvo `config`.
- `data/`: fuentes de datos por estrategia (`FuenteShapefile`, `FuenteGdb`, `FuenteZip` en
  `LectorCapas`) y `TransporteUrllib` (HTTP con certifi). Formato nuevo = clase nueva
  registrada, sin tocar las existentes.
- `services/`: lógica de negocio sin tkinter: geometría y vértices principales
  (Douglas-Peucker), detección de campos, agrupación, Markdown, ayuda y actualizaciones.
- `rendering/`: matplotlib **sin pyplot**. `RenderizadorMatplotlib` dibuja en dos fases:
  (1) geometría, leyenda y escala; (2) `fig.canvas.draw()` y luego `ColocadorEtiquetas` coloca
  las cotas midiendo en píxeles. Las cotas usan `set_in_layout(False)`.
- `controller/`: controladores que dependen de **protocolos** (`VistaCroquis`, `VistaAyuda`,
  `VistaAcercaDe`, `EjecutorTareas`), nunca de Tk. Se prueban con vistas falsas.
- `view/`: única capa que importa tkinter. Todo color y fuente sale de `TemaMaterial`
  (`view/estilos.py`); no uses literales. Trabajo lento en segundo plano con `EjecutorTk`
  (hilo + cola revisada con `after`: Tk no es seguro entre hilos).
- `app.py`: raíz de composición; crea e inyecta todo. `config.py`: constantes y parámetros.

Si agregas un método a un protocolo de vista, impleméntalo también en las vistas falsas de
`tests/`.

## Convenciones obligatorias

- **Cabecera con changelog en todo archivo nuevo o modificado**, la entrada más reciente
  arriba (versión interna del documento, independiente de la app). Formato en
  `CONTRIBUTING.md`. Excepciones: `LICENSE` (texto GPL literal), `uv.lock`, imágenes.
- **SemVer**: la versión vive solo en `src/generador_croquis/__init__.py`; cada versión va en
  `CHANGELOG.md` (Keep a Changelog). Funcionalidad nueva = MINOR, corrección = PATCH.
- Conventional Commits en español, con la línea `Co-Authored-By` del entorno.
- Cotas con punto decimal (`8.00 m`); la tolerancia de la interfaz acepta coma o punto.

## Trampas conocidas

- **Python de uv en Linux = Tcl/Tk 9 sin Xft**: la interfaz se ve con fuentes X antiguas y
  PyInstaller no empaqueta bien ese Tk. Para revisar la UI o construir el ejecutable usa el
  Python del sistema (`uv sync --python /usr/bin/python3.12`); el CI de release usa
  `actions/setup-python`. Las capturas de la UI deben hacerse con ese Python.
- Una `Figure` sin canvas no tiene renderer: el renderizador asocia `FigureCanvasAgg`. Las
  cotas se colocan para el tamaño original; `exportar()` restaura ese tamaño.
- `ttk.Frame` ignora `padding` en el estilo: pásalo al widget.
- En imágenes de elementos ttk (botones redondeados), el `padding` va en `element_create`, no
  en el estilo (si no, los botones crecen de alto).
- El campo de pisos puede ser **piso de la unidad** (`PLANTA_UBICACION`: color y leyenda por
  piso) o **total de pisos** (`NUMERO_PISOS`: título). Se elige con `SignificadoPisos`.
- No abrevies códigos catastrales tipo «inicio…final»: lo que distingue unidades está en el
  medio. Se parten en líneas (`partir`).

## Datos de prueba

- Las pruebas generan sus datos en fixtures (`tests/conftest.py`); no subas binarios.
- `tests/*.gdb/` y `tests/*.zip` son **datos catastrales reales** (están en `.gitignore`).
  Úsalos solo localmente; las imágenes de la documentación se hacen con datos sintéticos.
- No priorices `CODIGO_*` de LADM-COL en la detección del campo identificador: en el catastro
  de Segovia esos códigos no siempre están bien formados (decisión del usuario).

## Publicación

1. Verificación verde (ruff, formato y pytest) y capturas reales si cambió la UI o el dibujo.
2. Actualiza `__version__`, el `CHANGELOG.md`, el manual (y sus capturas) y el README si aplica.
3. Push a `main` y espera el CI (`.github/workflows/ci.yml`: Linux, Windows y macOS).
4. **Solo con confirmación del usuario**: `git tag -a vX.Y.Z` y push del tag.
   `release.yml` valida tag = `__version__`, construye `.exe`, Linux y `.app`, y publica el
   Release con notas del CHANGELOG, `SHA256SUMS.txt` y `LICENSE.txt`.

La pestaña Ayuda descarga `docs/MANUAL_DE_USO.md` de `main`: no subas a `main` documentación
de funciones que aún no están publicadas.
