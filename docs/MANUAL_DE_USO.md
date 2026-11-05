<!--
==============================================================================
Archivo  : docs/MANUAL_DE_USO.md
Proyecto : Generador de Croquis
------------------------------------------------------------------------------
CHANGELOG (versión interna del documento)
  v1.1.0 | 2026-11-05 | Actualizado a la interfaz 1.0.2 (Material Design):
         |            | nuevos nombres de botones, tarjetas, resumen,
         |            | barra de estado, pestaña Ayuda y capturas nuevas.
  v1.0.0 | 2026-11-05 | Creación. Manual de usuario para la versión 1.0.1 de
         |            | la aplicación: instalación, preparación de datos,
         |            | generación y exportación de croquis, actualizaciones
         |            | y solución de problemas.
==============================================================================
-->
# Manual de uso — Generador de Croquis

> Corresponde a la versión **1.0.2** de la aplicación.

## Contenido

1. [¿Qué hace el programa?](#1-qué-hace-el-programa)
2. [Instalación](#2-instalación)
3. [Preparar los datos](#3-preparar-los-datos)
4. [Generar croquis paso a paso](#4-generar-croquis-paso-a-paso)
5. [Cómo leer un croquis](#5-cómo-leer-un-croquis)
6. [Guardar y exportar](#6-guardar-y-exportar)
7. [Actualizar el programa](#7-actualizar-el-programa)
8. [Solución de problemas](#8-solución-de-problemas)

---

## 1. ¿Qué hace el programa?

El Generador de Croquis lee una capa de **polígonos** (construcciones, predios, edificaciones)
y produce una lámina con un **croquis técnico por construcción**. Cada croquis muestra:

- La planta de la construcción, con cada parte en un color distinto.
- La **medida de cada lado** en metros (cotas en rojo, por fuera del polígono).
- Los **huecos interiores** (patios, vacíos) con línea punteada.
- Una etiqueta con el **identificador** y el **número de pisos**.
- El **área total** y el **perímetro total** al pie del croquis.

![Ejemplo de croquis](img/ejemplo_croquis.png)

## 2. Instalación

No hace falta instalar Python ni ninguna librería. Descargue el archivo de su sistema desde la
página de **Releases** del repositorio:
<https://github.com/sparveriusdev/GeneradorCroquis/releases>

### Windows 10/11

1. Descargue `GeneradorCroquis-X.Y.Z-windows-x64.exe`.
2. Haga doble clic. Si aparece **"Windows protegió su PC"** (SmartScreen), pulse
   **Más información → Ejecutar de todas formas**. El aviso sale porque el ejecutable no tiene
   firma digital comercial.
3. Opcional: mueva el `.exe` a una carpeta fija (por ejemplo `C:\Programas\GeneradorCroquis`) y
   cree un acceso directo en el escritorio.

> La primera vez tarda unos segundos más en abrir: el ejecutable se descomprime en una
> carpeta temporal.

### macOS (Apple Silicon: M1, M2, M3…)

1. Descargue `GeneradorCroquis-X.Y.Z-macos-arm64.zip` y descomprímalo.
2. Arrastre `GeneradorCroquis.app` a **Aplicaciones**.
3. La primera vez: **clic derecho → Abrir → Abrir**. Si macOS no lo permite, vaya a
   **Ajustes del Sistema → Privacidad y seguridad** y pulse **Abrir igualmente**.

### Linux (x64)

```bash
tar xzf GeneradorCroquis-X.Y.Z-linux-x64.tar.gz
./GeneradorCroquis
```

### Verificar la descarga (opcional)

Cada release incluye `SHA256SUMS.txt` con la huella de cada archivo:

- Windows (PowerShell): `Get-FileHash .\GeneradorCroquis-X.Y.Z-windows-x64.exe`
- macOS / Linux: `shasum -a 256 GeneradorCroquis-X.Y.Z-*`

El valor debe coincidir con el que aparece en `SHA256SUMS.txt`.

## 3. Preparar los datos

### Formatos aceptados

| Formato | Cómo abrirlo | Notas |
|---|---|---|
| Shapefile (`.shp`) | **Abrir archivo…** | Deben estar en la misma carpeta, como mínimo, `.shp`, `.shx` y `.dbf`; conviene incluir también `.prj`. |
| Archivo `.zip` | **Abrir archivo…** | Puede contener shapefiles y/o carpetas `.gdb`, en cualquier subcarpeta. Si hay varios, el programa pregunta cuál usar. |
| File Geodatabase (`.gdb`) | **Abrir carpeta GDB…** | Seleccione la **carpeta** `.gdb`. Si tiene varias capas, el programa pregunta cuál usar. |

### Requisitos de la capa

- **Geometría de polígonos** (Polygon o MultiPolygon). Puntos y líneas se ignoran; si la capa no
  tiene polígonos, el programa lo avisa.
- **Sistema de coordenadas (CRS)**:
  - Si la capa está en un sistema **proyectado en metros** (por ejemplo MAGNA-SIRGAS /
    Origen Nacional, EPSG:9377), las medidas se usan tal cual.
  - Si está en **coordenadas geográficas** (grados, por ejemplo WGS84 / EPSG:4326), el programa
    la **reproyecta automáticamente a EPSG:9377** para obtener metros, y lo indica con un aviso
    en *Resumen de la capa*.
  - Si la capa **no tiene CRS** (falta el `.prj`), las medidas salen en las unidades originales
    del archivo y se muestra un aviso.

### Campos recomendados

| Campo | Para qué sirve | Nombres que se detectan solos |
|---|---|---|
| **Identificador** | Agrupa los polígonos que forman una misma construcción. | `id`, `cod`, `codigo`, `code`, `id_construccion`, `predio`, `lote`, `ficha`, `npn`, `matricula`, `objectid`… |
| **Pisos** | Número de pisos que se muestra en el croquis. | `pisos`, `piso`, `niveles`, `floors`, `num_pisos`, `nro_pisos`, `plantas`… |

Los nombres se reconocen sin distinguir mayúsculas y también como parte de un nombre más largo
(por ejemplo `COD_CONST` o `NUM_PISOS`). Si no se detectan, se eligen a mano en la lista.

> **Varias partes, una construcción:** si una construcción está dibujada en varios polígonos
> (por ejemplo, cuerpo principal y anexo), todos deben tener el **mismo valor** en el campo
> identificador. Si los pisos difieren entre partes, se muestra el valor **más alto**.

## 4. Generar croquis paso a paso

La ventana tiene tres pestañas: **Generador**, **Ayuda** (este manual) y **Acerca de**. En la
pestaña **Generador** el trabajo se hace en tres pasos, de arriba abajo, y la **barra de estado**
inferior indica siempre qué hacer a continuación.

![Pestaña Generador](img/pestana_generador.png)

1. **Datos de entrada.** Pulse **Abrir archivo…** (`.zip` / `.shp`) o **Abrir carpeta GDB…**
   (carpeta `.gdb`). Si el archivo tiene varias capas o conjuntos de datos, elija uno en la
   lista (doble clic o **Enter** para aceptar, **Escape** para cancelar).
2. **Campos de la capa.** El programa propone los campos y lo indica con la marca verde
   **Detectado automáticamente**. Cámbielos si no son los correctos:
   - *Identificador de la construcción*: los polígonos con el mismo valor se dibujan juntos.
     Con `(ninguno)` se dibuja un croquis por cada polígono.
   - *Número de pisos*: opcional; con `(ninguno)` los croquis no muestran pisos.

   La tarjeta **Resumen de la capa** muestra el archivo, el número de polígonos y de
   construcciones, el sistema de coordenadas y las columnas, junto con los avisos (por ejemplo,
   si la capa se reproyectó o no tiene sistema de coordenadas).
3. **Generar y exportar.** Pulse **Generar croquis**. Se abre una ventana con la lámina
   completa.
   - Si hay más de **30 construcciones**, el programa pide confirmación porque la imagen puede
     tardar y consumir mucha memoria. Para lotes grandes conviene filtrar la capa antes en un
     SIG (QGIS / ArcGIS).
4. **Explorar la vista previa** con la barra inferior de esa ventana:
   - 🔍 **Zoom**: dibuje un rectángulo sobre la zona a ampliar.
   - ✥ **Mover**: arrastre para desplazarse.
   - 🏠 **Inicio**: vuelve a la vista completa.

También puede abrir un archivo directamente desde la terminal:
`GeneradorCroquis ruta/al/archivo.zip`.

### La pestaña Ayuda

Muestra este mismo manual con formato. Al abrirla, el programa descarga de GitHub la versión
más reciente (marca verde **Versión más reciente (GitHub)**); si no hay internet, muestra la
copia incluida en el programa (**Copia incluida · sin conexión**). Los enlaces del índice
llevan a cada sección; **Recargar** vuelve a consultar y **Abrir en GitHub** lo abre en el
navegador.

![Pestaña Ayuda](img/pestana_ayuda.png)

## 5. Cómo leer un croquis

| Elemento | Significado |
|---|---|
| Título `Construcción: X  \|  N pisos  \|  M partes` | Identificador, pisos y número de polígonos que la forman. |
| Recuadro naranja | Identificador y pisos, dentro de la construcción. |
| Rótulos rojos (`10.00 m`) | Longitud de cada lado del contorno exterior, en metros, con dos decimales. |
| Línea punteada | Hueco interior (patio o vacío). Sus lados no se acotan. |
| Puntos en las esquinas | Vértices del polígono. |
| Pie del croquis | Área total (m²) y perímetro total (m), sumando todas las partes. |
| Ejes | Coordenadas del sistema de referencia de la capa (útiles para ubicar la construcción). |

> En construcciones con varias partes, el **área** y el **perímetro** son la suma de los de
> cada parte; los lados compartidos entre partes se cuentan en ambas.

## 6. Guardar y exportar

1. Después de generar, pulse **Exportar imagen…**.
2. Elija el nombre y el formato:

| Formato | Recomendado para |
|---|---|
| **PNG** | Uso general, documentos e informes (300 dpi). |
| **JPEG** | Archivos más livianos para correo. |
| **PDF** | Impresión y anexos técnicos; el texto se mantiene nítido a cualquier zoom. |
| **SVG** | Edición posterior en Inkscape, Illustrator o CAD. |

La imagen se exporta **siempre con su tamaño original**, aunque haya cambiado el tamaño de la
ventana de vista previa.

## 7. Actualizar el programa

![Pestaña Acerca de](img/pestana_acerca_de.png)

1. Abra la pestaña **Acerca de**. Ahí se ve la **versión instalada**, los créditos, la licencia
   y los enlaces al repositorio y a este manual.
2. Pulse **Buscar actualizaciones**. El programa consulta GitHub (necesita internet; es la
   única función que se conecta a la red).
3. Si hay una versión nueva, el botón cambia a **Descargar vX.Y.Z**. Púlselo y elija la carpeta
   donde guardarla; la barra muestra el avance.
4. Al terminar, **cierre el programa** y abra el archivo descargado. En Windows puede borrar el
   `.exe` anterior.

**Ver todas las versiones** abre en el navegador la página del release con las novedades de
cada versión.

## 8. Solución de problemas

| Problema | Causa probable | Solución |
|---|---|---|
| *"Shapefile incompleto: … (falta .dbf)"* | Faltan archivos compañeros del `.shp`. | Copie juntos `.shp`, `.shx`, `.dbf` y `.prj`, o comprímalos en un `.zip`. |
| *"No se encontró ningún .shp ni .gdb válido dentro del .zip"* | El `.zip` no tiene datos espaciales o están incompletos. | Revise el contenido del `.zip`. |
| *"La capa no contiene polígonos"* | Se eligió una capa de puntos o líneas. | Elija la capa de construcciones / polígonos. |
| *"No se pudo leer el GDB"* | Se seleccionó una carpeta que no es `.gdb` o la geodatabase está dañada. | Con **Abrir carpeta GDB…**, seleccione la carpeta que termina en `.gdb`. |
| Las medidas no parecen metros | La capa no tiene CRS (falta `.prj`). | Asigne el sistema de coordenadas en QGIS/ArcGIS y vuelva a exportar. |
| Hay un croquis por polígono en lugar de por construcción | El campo identificador está en `(ninguno)` o no es el correcto. | Elija el campo que identifica cada construcción. |
| *"No se pudo conectar con GitHub"* | Sin internet, proxy o firewall. | Revise la conexión o descargue manualmente desde la página de Releases. |
| *"GitHub limitó temporalmente las consultas"* | Demasiadas consultas desde la misma red en una hora. | Intente de nuevo más tarde. |
| Windows / macOS bloquea el programa al abrirlo | El ejecutable no está firmado. | Vea [Instalación](#2-instalación). |

### Archivo de registro

Los errores se guardan con detalle técnico en:

- **Windows:** `C:\Users\<usuario>\.generador_croquis\croquis.log`
- **macOS / Linux:** `~/.generador_croquis/croquis.log`

Al reportar un problema, adjunte ese archivo y, si es posible, un `.zip` con datos de ejemplo
en un *issue* del repositorio:
<https://github.com/sparveriusdev/GeneradorCroquis/issues>
