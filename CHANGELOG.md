# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Numeración [SemVer](https://semver.org/lang/es/): MAYOR.MENOR.PARCHE.

## [1.1.0] - 2026-11-22

Incluye lo que se había preparado como 1.0.2 (nunca se publicó con ese número) más Ventas.

### Agregado
- **Ventas, Abonos y Cierre de mes** (especificación v1.1 aprobada):
  - La app crea las hojas `Ventas`, `Abonos` y `Cierres` al final del libro, con un botón en la
    pestaña Ventas. No toca las demás hojas.
  - Botón **Vender** en la ficha de cada producto: vendedora, cantidad, precio (con descuento),
    costo fijado al momento de vender, fecha y nota. No deja vender más de lo que hay en esa
    ubicación y muestra la utilidad y el reparto antes de confirmar. Opción para no descontar la
    existencia si ya se había bajado a mano.
  - **Convertir una cotización en venta**, repartiendo el descuento de la cotización entre las
    líneas.
  - Pestaña **Ventas**: saldo de cada vendedora, lista con filtros por mes y vendedora, totales
    (ventas, utilidad, parte de las vendedoras y tuya) y **Anular** mientras el mes no esté
    cerrado (puede devolver la existencia).
  - **Abonos**: registrar abonos, saldo inicial e historial (el historial se ve en gris y no
    cuenta en el saldo). Se pueden borrar mientras su mes no esté cerrado.
  - **Cierre de mes**: resumen por vendedora y Casa, confirmar el cierre (queda fijo en la hoja
    Cierres y marca el mes en Ventas y Abonos), **Marcar pagado** y PDF del cierre.
  - Ajustes → **Ventas**: % de reparto de Urania e Isabel y fecha de inicio del registro.
- **Eliminar producto** desde su ficha. Borra la fila de Inventario y sube las de abajo
  ajustando sus fórmulas, como "Eliminar fila" de Excel. Si el producto tiene compras, pide
  confirmar que también se borran de Compras. Si la hoja tiene algo que la app no sabe mover
  sin riesgo (celdas combinadas, formato condicional, validaciones, tablas, comentarios,
  imágenes o fórmulas de otras hojas que apuntan a esas filas), no borra nada y lo explica.
- Constante `APP_VERSION`, visible en la bienvenida y en Ajustes → Acerca de.
- `CHANGELOG.md`, `docs/DISENO.md`, `README.md`, `package.json` (scripts `build`, `format`,
  `test`), `.prettierrc` y pruebas de `core.js` y `ventas-core.js` en `test/`.

### Corregido
- **Solo se podía crear un producto; los siguientes no se guardaban.** La app comparaba la
  etiqueta de versión del archivo (`cTag`) que devuelve OneDrive al subir con la que devuelve
  al consultar justo antes del siguiente guardado. Si no coincidían, mostraba "El archivo
  cambió en OneDrive" y no guardaba. Eso pasaba en tres casos:
  - OneDrive procesa el archivo después de subirlo y le cambia el `cTag` sin cambiar los datos;
  - el Excel se abrió en Excel (que recalcula y guarda solo) entre dos cambios de la app;
  - se hacían dos cambios seguidos mientras el primero todavía se estaba subiendo.
- Si el archivo no traía tabla de textos compartidos (`sharedStrings.xml`), no se podía
  escribir texto. Ahora la app la crea.

### Cambiado
- Guardado nuevo: si el archivo cambió en OneDrive, la app descarga la versión nueva y vuelve
  a aplicar encima los cambios pendientes (combina en lugar de rechazar). Solo se detiene si un
  cambio ya no se puede aplicar (por ejemplo, el producto se borró en Excel).
- El aviso "el archivo había cambiado en OneDrive" solo aparece si los datos cambiaron de verdad
  afuera, no cuando OneDrive solo procesó el archivo.
- Los guardados ya no se cruzan: si hay uno en curso, el siguiente espera y sale junto.
- Los cambios sin guardar se copian en el navegador. Si la sesión vence antes de guardar, al
  volver a entrar la app ofrece aplicarlos.
- En la ficha del producto, los botones − y + quedan para corregir conteos; las ventas se
  registran con **Vender**.
- Fuentes separados por responsabilidad: `src/index.src.html` (HTML), `src/styles.css`,
  `src/core.js` + `src/ventas-core.js` (Excel) y la interfaz en seis archivos dentro de
  `src/app/`. `build.js` los une en `index.html`, en la raíz del repositorio. La app compilada
  sigue siendo un solo archivo.
- Código reformateado con Prettier (ancho 100, comillas simples) y comentado en español:
  encabezado por archivo, separadores por sección y JSDoc por función.

## [1.0.1] - 2026-11

### Cambiado
- Cerrar sesión ya no olvida el archivo elegido.

### Agregado
- Ajustes → **Explorar mis carpetas** y **Abrir desde enlace**, porque el buscador de
  OneDrive a veces no devuelve el archivo.

## [1.0.0] - 2026-11

### Agregado
- Primera versión: buscar productos, editar existencias, precio y notas, registrar compras
  (recalcula el costo promedio), cotizaciones en PDF y modo de prueba con un archivo local.
