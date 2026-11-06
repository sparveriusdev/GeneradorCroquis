<!--
==============================================================================
Archivo  : CHANGELOG.md
Proyecto : Generador de Croquis
------------------------------------------------------------------------------
CHANGELOG (versión interna del documento)
  v1.6.0 | 2026-11-06 | Añade la versión 1.3.0 (etiqueta del ID afuera).
  v1.5.0 | 2026-11-05 | Añade la versión 1.2.1 (vista desde arriba).
  v1.4.0 | 2026-11-05 | Añade la versión 1.2.0 (convenciones por piso).
  v1.3.1 | 2026-11-05 | Pendientes: avisos de GitHub en la Ayuda, manual.
  v1.3.0 | 2026-11-05 | Añade la versión 1.1.0 (acotado inteligente).
  v1.2.0 | 2026-11-05 | Añade la versión 1.0.2 (rediseño Material Design).
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

## [1.3.0] - 2026-11-06

La etiqueta naranja del identificador ya no tapa la construcción ni sus cotas.

### Añadido
- En la vista previa se puede **arrastrar la etiqueta del identificador** con el ratón (con
  Zoom y Mover desactivados). La línea guía la sigue y **Exportar imagen…** guarda la nueva
  posición. Un aviso en la ventana lo recuerda.

### Cambiado
- La etiqueta del identificador se coloca **fuera de la construcción**, después de las cotas,
  en el hueco libre con la línea guía más corta y sin cruzar otras etiquetas. Una **línea
  guía** la une con un punto dentro de la construcción. Si no hay espacio afuera, queda
  adentro como antes.
- El recuadro de la etiqueta es más opaco, porque ya no va sobre el relleno.

## [1.2.1] - 2026-11-05

Mejora visual a partir de la retroalimentación de la oficina: en la 1.2.0 los pisos superiores
no tenían relleno y sus contornos de trazos alternados se leían como un achurado.

### Cambiado
- **Vista desde arriba**: todos los pisos vuelven a tener relleno de su color. Cada zona se
  pinta con el color claro del piso más alto que la cubre, sin mezclas de colores.
- Los contornos de los pisos superiores son **punteados** y de un solo color (antes, trazos
  de varios colores alternados).
- La **cota de un lado común** a varias unidades toma el color del piso más alto que tiene
  ese lado, el mismo de la zona vecina. Desaparecen las cotas grises y la entrada «Cota
  común» de la leyenda.

## [1.2.0] - 2026-11-05

### Añadido
- **Convenciones (leyenda)** en cada croquis con 2 o más unidades: color y estilo de línea de
  cada piso con su área (p. ej. «Piso 2 · 23.93 m²»), y la cota común.
- **Color fijo por piso**: las unidades se ordenan de abajo hacia arriba y el piso 1 es siempre
  azul, el 2 verde, el 3 rojo… en todos los croquis.
- **Unidades superpuestas visibles**: el piso inferior va con línea gruesa y relleno; los
  superiores con línea fina discontinua y sin relleno. Donde varios pisos coinciden, sus
  trazos se alternan para que se vean todos.
- Opción **El campo indica: Piso de la unidad / Total de pisos**, propuesta según el nombre
  del campo (`PLANTA_UBICACION` → piso de la unidad; `NUMERO_PISOS` → total). Con «piso de la
  unidad», cada croquis lleva el color de su piso y la leyenda **aunque tenga una sola unidad**
  (p. ej. al agrupar por `IDENTIFICADOR`), y el título dice «Piso 2» o «Pisos 1, 2».
- Manual: subsección **Vértices principales y tolerancia** con valores orientativos,
  procedimiento de ajuste y comparación visual.

### Cambiado
- Las **cotas comunes** a varias unidades se muestran en gris neutro (antes, con el color de
  la primera unidad).
- **Coordenadas de los ejes con decimales automáticos**: en metros se muestran enteras
  (`4811905`), sin «.0000»; solo aparecen decimales si las marcas están a menos de 1 m.
- Con «total de pisos», una construcción de una sola unidad usa siempre el primer color.
- **Etiqueta del identificador más pequeña** y semitransparente; los códigos largos se parten
  en varias líneas en lugar de ocupar todo el ancho del croquis.

### Corregido
- La pestaña Ayuda muestra los avisos de GitHub (`> [!WARNING]`, `[!NOTE]`…) con su título en
  lugar del marcador, y sin un hueco entre el título y el texto.
- Ayuda: las tablas dentro de una lista se dibujan como tabla, y la numeración de las listas
  ya no cuenta las sub-viñetas.

## [1.1.0] - 2026-11-05

### Añadido
- **Acotado por vértices principales**: los vértices de ajuste (los que se apartan menos que
  la tolerancia de la recta entre esquinas) ya no generan cotas; el lado se mide de esquina a
  esquina como la **suma de sus tramos**. Las esquinas reales y los quiebres cortos se
  conservan. Opción **Acotar solo vértices principales** con **tolerancia** ajustable
  (0,15 m por defecto, admite coma decimal).
- **Cotas del color de su unidad**: en construcciones con varias partes (p. ej. unidades
  superpuestas de distintos pisos) cada cota usa el color de su polígono.
- **Cotas sin solapes**: cada etiqueta se coloca en la primera posición libre (afuera del
  lado, desplazada a lo largo o más lejos, con línea guía). Si alguna no encuentra espacio,
  la barra de estado lo indica.
- Los lados comunes a varias unidades con la misma medida se acotan una sola vez.
- Vértices principales (puntos grandes) y de ajuste (puntos pequeños) se distinguen.
- La página Generador se desplaza en pantallas bajas (p. ej. portátiles de 768 px).

### Cambiado
- Paleta de unidades más oscura y legible sobre blanco (se quitó el amarillo).
- Ejes con coordenadas completas a 4 decimales, sin notación científica (antes «+4.81e6»);
  el área y el perímetro se muestran debajo de las coordenadas.
- El resumen de la capa se actualiza al cambiar el campo identificador y abrevia la lista de
  columnas.

### Corregido
- En polígonos cóncavos (forma de L, entrantes) algunas cotas podían quedar del lado de
  adentro: la dirección exterior ahora se calcula con la orientación del contorno.

## [1.0.2] - 2026-11-05

### Añadido
- **Rediseño de la interfaz con Material Design 3**: barra superior con el logo, navegación
  por pestañas con indicador, tarjetas, botones redondeados (con relleno, tonales, con contorno
  y de texto), campos con contorno, progreso lineal y barra de estado que indica el siguiente
  paso.
- Tipografía **Roboto** incluida en la aplicación (licencia SIL OFL 1.1), sin instalarla en el
  sistema. En Windows el texto se ve nítido en pantallas de alta resolución.
- **Logo e icono** de la aplicación en la ventana, la barra superior y los ejecutables
  (`.exe`, `.app` y Linux).
- Pestaña **Ayuda**: muestra el manual de uso con formato (títulos, tablas, imágenes, índice
  navegable). Descarga de GitHub la versión más reciente y, sin conexión, usa la copia incluida.
- **Resumen de la capa** en forma de tabla, con avisos destacados.

### Cambiado
- Textos de la interfaz más claros: pasos numerados, ayudas bajo cada campo y mensajes que
  indican qué hacer a continuación.
- Botones renombrados: *Abrir archivo…*, *Abrir carpeta GDB…*, *Generar croquis*,
  *Exportar imagen…*, *Buscar actualizaciones*.
- Al exportar se propone el nombre `croquis_<archivo>`.
- Manual de uso actualizado con la nueva interfaz y capturas nuevas.

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

[Unreleased]: ../../compare/v1.3.0...HEAD
[1.3.0]: ../../releases/tag/v1.3.0
[1.2.1]: ../../releases/tag/v1.2.1
[1.2.0]: ../../releases/tag/v1.2.0
[1.1.0]: ../../releases/tag/v1.1.0
[1.0.2]: ../../releases/tag/v1.0.2
[1.0.1]: ../../releases/tag/v1.0.1
[1.0.0]: ../../releases/tag/v1.0.0
