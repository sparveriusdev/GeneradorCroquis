<!--
==============================================================================
Archivo  : CONTRIBUTING.md
Proyecto : Generador de Croquis
------------------------------------------------------------------------------
CHANGELOG (versión interna del documento)
  v1.0.0 | 2026-11-05 | Creación. Guía de contribución: entorno con uv, flujo
         |            | de ramas y PR, Conventional Commits, estándares de
         |            | código, cabeceras, pruebas, versionado y releases.
==============================================================================
-->
# Cómo contribuir

¡Gracias por querer mejorar el Generador de Croquis! Esta guía explica cómo preparar el entorno
y qué se espera de cada cambio.

## Reportar errores o proponer mejoras

Abra un *issue* en <https://github.com/sparveriusdev/GeneradorCroquis/issues> con:

- **Versión** del programa (pestaña *Acerca de*) y sistema operativo.
- **Pasos para reproducir** el problema y qué esperaba que pasara.
- El archivo de registro `~/.generador_croquis/croquis.log`.
- Si es posible, un `.zip` **pequeño** con datos de ejemplo. **No suba datos personales ni
  catastrales reales sin autorización**: recorte o anonimice la capa.

## Preparar el entorno

Requisitos: [uv](https://docs.astral.sh/uv/) y Git.

```bash
git clone https://github.com/sparveriusdev/GeneradorCroquis.git
cd GeneradorCroquis
uv sync                    # crea .venv con dependencias y herramientas de desarrollo
uv run generador-croquis   # ejecuta la aplicación
```

## Flujo de trabajo

1. Cree una rama desde `main` con un nombre descriptivo:
   `feat/exportar-dxf`, `fix/cotas-multipoligono`, `docs/manual-gdb`.
2. Haga cambios pequeños y enfocados (un tema por *pull request*).
3. Antes de subir, verifique que todo pase:

   ```bash
   uv run ruff format .
   uv run ruff check .
   uv run pytest
   ```

4. Abra un *pull request* hacia `main`. El CI ejecuta lint y pruebas en Linux, Windows y macOS;
   debe quedar en verde antes de fusionar.

### Mensajes de commit

Se usa [Conventional Commits](https://www.conventionalcommits.org/es/v1.0.0/):

| Tipo | Uso | Efecto en la versión |
|---|---|---|
| `feat:` | Funcionalidad nueva | MINOR |
| `fix:` | Corrección de un error | PATCH |
| `docs:` | Solo documentación | — |
| `refactor:` | Cambio interno sin alterar el comportamiento | — |
| `test:` | Pruebas | — |
| `ci:` / `build:` | Flujos de GitHub Actions / empaquetado | — |
| `chore:` | Mantenimiento (dependencias, release) | — |

Un cambio incompatible se marca con `!` (`feat!: …`) o con `BREAKING CHANGE:` en el cuerpo, e
implica subir la versión MAJOR.

## Estándares de código

### Arquitectura

Respete las capas descritas en el [README](README.md#arquitectura). Reglas principales:

- **`domain/`** no importa nada de las demás capas del proyecto.
- **`services/`** contiene la lógica de negocio y **no importa tkinter**.
- **`view/`** es la **única** capa que importa tkinter.
- Los controladores dependen de **protocolos** (`VistaCroquis`, `VistaAcercaDe`,
  `EjecutorTareas`), no de clases Tk.
- Las dependencias se crean e inyectan en `app.py` (raíz de composición).
- Las constantes y parámetros van en `config.py`, no repartidos por el código.
- Para un **formato de entrada nuevo**, cree una clase que cumpla `FuenteDatos` en
  `data/fuentes.py` y regístrela en `LectorCapas`; no modifique las fuentes existentes.

### Estilo

- Formato y lint con **ruff** (configuración en `pyproject.toml`, líneas de 100 caracteres).
- Anotaciones de tipo en funciones públicas.
- Nombres de dominio en **español**, coherentes con el código existente.
- Los errores que el usuario debe ver se lanzan como subclases de `CroquisError` con un mensaje
  claro; los fallos inesperados se dejan propagar para que el controlador los registre en el log.

### Cabeceras con changelog (obligatorio)

**Todo archivo nuevo o modificado** debe actualizar su cabecera, agregando la entrada más
reciente **arriba**:

```python
# ==============================================================================
# Archivo  : src/generador_croquis/ruta/archivo.py
# Proyecto : Generador de Croquis
# ------------------------------------------------------------------------------
# CHANGELOG (versión interna del documento)
#   v1.1.0 | AAAA-MM-DD | Qué cambió y por qué.
#   v1.0.0 | 2026-11-05 | Creación.
# ==============================================================================
```

- La **versión interna del documento** es independiente de la versión de la aplicación:
  PATCH para correcciones menores, MINOR para cambios o añadidos, MAJOR para reescrituras.
- En Markdown se usa el mismo bloque dentro de `<!-- … -->`; en YAML/TOML, con `#`.
- Se exceptúan los archivos generados (`uv.lock`) y los que no admiten comentarios.

### Pruebas

- Toda funcionalidad nueva o corrección debe venir con pruebas en `tests/`.
- La lógica de negocio se prueba **sin interfaz gráfica**; los controladores, con vistas falsas
  (ver `tests/test_controlador.py` y `tests/test_actualizaciones.py`).
- Las pruebas **no deben acceder a internet**: use transportes HTTP falsos.
- Los datos geográficos de prueba se generan en *fixtures* (`tests/conftest.py`), no se suben
  archivos binarios.

## Versionado y publicación (mantenedores)

La versión sigue [SemVer](https://semver.org/lang/es/) y vive solo en
`src/generador_croquis/__init__.py`.

1. Actualice `__version__` (y su cabecera).
2. En `CHANGELOG.md`, mueva lo de `[Unreleased]` a una sección `## [X.Y.Z] - AAAA-MM-DD` y
   agregue el enlace al final del archivo.
3. Commit y tag:

   ```bash
   git commit -am "chore(release): vX.Y.Z"
   git tag -a vX.Y.Z -m "vX.Y.Z"
   git push origin main --tags
   ```

4. El flujo **Release** valida que el tag coincida con `__version__`, prueba, construye los
   ejecutables de Windows, Linux y macOS y publica el release con las notas del CHANGELOG.

> Para construir el ejecutable localmente use un Python de python.org o del sistema, no el
> que descarga uv (ver [README](README.md#construir-el-ejecutable-localmente)).

## Licencia

Al contribuir, acepta que su aporte se distribuya bajo la misma licencia del proyecto
(ver [LICENSE](LICENSE)).
