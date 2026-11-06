<!--
==============================================================================
Archivo  : ROADMAP.md
Proyecto : Generador de Croquis
------------------------------------------------------------------------------
CHANGELOG (versión interna del documento)
  v1.2.0 | 2026-11-06 | 1.4.0 publicada (uso en las convenciones);
         |            | GeoPackage pasa a 1.5.0 y GeoParquet a 1.6.0.
  v1.1.0 | 2026-11-06 | 1.3.0 publicada (etiqueta del ID afuera y
         |            | arrastrable); GeoPackage pasa a 1.4.0 y GeoParquet
         |            | a 1.5.0.
  v1.0.0 | 2026-11-05 | Creación. Versiones publicadas, plan de 1.3.0
         |            | (GeoPackage) y 1.4.0 (GeoParquet), pendientes
         |            | técnicos y agentes de apoyo propuestos.
==============================================================================
-->
# Hoja de ruta

Plan de las próximas versiones. Las fechas no son compromisos. Cuando una versión se publica,
su detalle pasa a [`CHANGELOG.md`](CHANGELOG.md) y aquí queda solo el resumen. El número de
versión sigue [SemVer](https://semver.org/lang/es/): funcionalidad nueva = MINOR,
correcciones = PATCH.

## ✅ Publicadas

| Versión | Tema principal |
|---|---|
| 1.0.0 | Programa estructurado (MVC), ejecutables para Windows, macOS y Linux, CI/CD. |
| 1.0.1 | Pestaña *Acerca de* con actualizaciones; manual, licencia GPL-3.0, CONTRIBUTING. |
| 1.0.2 | Interfaz Material Design, pestaña *Ayuda*, logo e iconos. |
| 1.1.0 | Acotado por vértices principales, color por unidad, cotas sin solapes. |
| 1.2.0 | Convenciones por piso, significado del campo de pisos, coordenadas sin decimales innecesarios. |
| 1.2.1 | Vista desde arriba (cada zona con el color del piso más alto) y cotas con el color del piso. |
| 1.3.0 | Etiqueta del identificador fuera de la construcción, con línea guía, y arrastrable en la vista previa. |
| 1.4.0 | Campo de uso en las convenciones, con la descripción del dominio de la GDB. |

## 🔜 1.5.0 · Soporte para GeoPackage (`.gpkg`)

**Objetivo:** abrir archivos GeoPackage como se abren hoy Shapefile y GDB.

- [ ] Nueva estrategia `FuenteGpkg` en `data/fuentes.py`, registrada en `LectorCapas`. Si el
      archivo tiene varias capas, el usuario elige una, igual que en la GDB.
- [ ] Detectar `.gpkg` dentro de los `.zip` (`FuenteZip`).
- [ ] *Abrir archivo…* acepta `.gpkg` (filtros del diálogo y textos de la interfaz).
- [ ] Pruebas con un GeoPackage generado en una *fixture*: una capa, varias capas, sin
      polígonos y capa con CRS geográfico.
- [ ] Manual (formatos aceptados), README y CHANGELOG.

**Viabilidad:** alta. GDAL/pyogrio ya incluye el controlador GPKG, así que no hay
dependencias nuevas ni aumento del tamaño del ejecutable.

## 🔜 1.6.0 · Soporte para GeoParquet (`.parquet`)

**Objetivo:** abrir capas en formato GeoParquet.

- [ ] **Decisión previa:** medir cuánto crece el ejecutable con `pyarrow` (se estima entre
      30 y 40 MB) y decidir si se incluye siempre o solo en una edición aparte.
- [ ] Estrategia `FuenteParquet` con `geopandas.read_parquet`. El CRS sale de los metadatos
      `geo`; si faltan, se avisa como hoy con las capas sin CRS.
- [ ] Detección dentro de los `.zip` y en el diálogo *Abrir archivo…*.
- [ ] Pruebas con un GeoParquet generado (con CRS y sin él) y prueba de humo del ejecutable
      en el CI.
- [ ] Manual, README y CHANGELOG.

## 🧰 Pendientes técnicos (sin versión asignada)

- [ ] Ayuda: un párrafo sangrado después de una viñeta queda pegado al texto de esa viñeta
      (por ejemplo, en el paso 2 del manual).
- [ ] Actualizar las *actions* de GitHub (`actions/checkout`, `setup-python`…) a versiones con
      Node 24, porque Node 20 está en desuso.
- [ ] Vista previa: volver a colocar las cotas al cambiar el tamaño de la ventana (hoy se
      colocan para el tamaño de exportación).
- [ ] Ejecutable para macOS Intel (hoy solo Apple Silicon).
- [ ] Firma de código para evitar los avisos de SmartScreen y Gatekeeper (requiere
      certificados).
- [ ] Revisar más adelante la detección de códigos LADM-COL como campo identificador
      (`CODIGO_UNIDAD_CONSTRUCCION`…). **Pospuesta** por decisión del usuario: en el catastro
      de Segovia esos códigos no siempre están bien formados.

## 🤖 Agentes de apoyo (propuestos)

Agentes del proyecto en `.claude/agents/`, con instrucciones fijas, para tareas repetitivas:

- **Revisor visual:** genera capturas de la aplicación y croquis con datos sintéticos, y
  revisa solapes, legibilidad, colores y textos antes de publicar.
- **Publicación:** recorre la lista de verificación (versión, CHANGELOG, manual y capturas,
  CI en verde) y prepara el tag. La publicación sigue requiriendo la confirmación del usuario.
- **Formatos de entrada:** plantilla para agregar una nueva `FuenteDatos` con sus pruebas
  (útil para 1.5.0 y 1.6.0).
