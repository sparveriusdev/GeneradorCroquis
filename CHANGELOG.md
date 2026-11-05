<!--
==============================================================================
Archivo  : CHANGELOG.md
Proyecto : Generador de Croquis
------------------------------------------------------------------------------
CHANGELOG (versión interna del documento)
  v1.1.1 | 2026-11-05 | 1.0.1: documentación y licencia.
  v1.1.0 | 2026-11-05 | Añade la versión 1.0.1 de la aplicación.
  v1.0.0 | 2026-11-05 | Creación. Historial de versiones de la aplicación
         |            | (formato Keep a Changelog + SemVer). El flujo de
         |            | release extrae de aquí las notas de cada versión.
==============================================================================
-->
# Changelog

Todos los cambios relevantes de la **aplicación** se documentan aquí.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y versionado con [SemVer](https://semver.org/lang/es/).

## [Unreleased]

## [1.0.1] - 2026-11-05

### Añadido
- Pestaña **Acerca de**: versión instalada, créditos (Gabriel Gómez Baena, autor de la idea y del
  script base; David Vásquez, desarrollo de las nuevas versiones) y enlace al repositorio.
- Comprobación de nuevas versiones en GitHub. Si existe una más reciente, se puede descargar el
  ejecutable del sistema operativo actual con barra de progreso.
- La consulta y la descarga se ejecutan en segundo plano, sin congelar la interfaz.
- Manual de uso (`docs/MANUAL_DE_USO.md`), guía de contribución (`CONTRIBUTING.md`) y licencia
  **GNU GPL v3.0 o posterior** (`LICENSE`, también incluida en cada release).

### Corregido
- El nombre del archivo interno de un `.zip` se mostraba con `\` en Windows; ahora usa `/`
  en todos los sistemas.

## [1.0.0] - 2026-11-05

Primera versión como programa estructurado, a partir del script `generador_v1.py`
(conservado en `legacy/` como referencia).

### Añadido
- Arquitectura Modelo-Vista-Controlador con capas de dominio, datos, servicios y renderizado.
- Ejecutables para Windows (`.exe`), Linux y macOS (`.app`) generados por GitHub Actions.
- Vista previa del croquis dentro de la aplicación, con zoom y desplazamiento.
- Opción `--version` y posibilidad de abrir un archivo pasado como argumento.
- Registro de eventos en `~/.generador_croquis/croquis.log` (rotativo).
- Suite de pruebas automatizadas (pytest) y lint (ruff) en CI.
- Atajos en el diálogo de selección: doble clic / Enter para aceptar, Escape para cancelar.

### Cambiado
- El contenido de los `.zip` se extrae a un directorio temporal que se elimina en cuanto
  termina la lectura.
- Detección de campos unificada; los candidatos cortos (`id`, `fid`…) solo coinciden por
  palabra completa (antes `width` se detectaba como identificador).
- Los valores de pisos no numéricos se ignoran en lugar de anular el dato de todo el grupo.
- La imagen exportada conserva su tamaño original aunque se redimensione la vista previa.
- Un error al cargar un archivo ya no deja cargada una capa anterior.

### Eliminado
- Instalación automática de librerías con `pip` al arrancar (ahora las gestiona `uv`
  o vienen incluidas en el ejecutable).

### Seguridad
- Protección contra rutas maliciosas en archivos `.zip` (*zip slip*).

[Unreleased]: ../../compare/v1.0.1...HEAD
[1.0.1]: ../../releases/tag/v1.0.1
[1.0.0]: ../../releases/tag/v1.0.0
