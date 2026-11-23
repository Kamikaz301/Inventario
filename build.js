/**
 * ============================================================================
 * build.js — Compila la app en un solo archivo
 * ============================================================================
 * Qué hace:
 *   Toma src/index.src.html e incrusta src/styles.css, JSZip 3.10.1,
 *   src/core.js + src/ventas-core.js y src/app/*.js (en orden) en sus marcadores. El resultado
 *   es index.html en la raíz del repositorio, que es lo que publica
 *   GitHub Pages.
 *
 * Depende de: Node.js y `npm install` (instala jszip@3.10.1).
 * Uso: node build.js
 * ============================================================================
 */
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');

let html = read('src/index.src.html');
const jszip = read('node_modules/jszip/dist/jszip.min.js');
// core.js y, a continuación, su extensión de ventas (mismo <script>).
const core = read('src/core.js') + '\n' + read('src/ventas-core.js');
const css = read('src/styles.css');

// Código de la interfaz, en este orden (comparten variables globales).
const APP_FILES = [
  'base.js',
  'onedrive.js',
  'inventario.js',
  'compra-cotizacion.js',
  'ventas.js',
  'ajustes-arranque.js',
];
const app = APP_FILES.map((f) => read('src/app/' + f)).join('\n');

// Un "</script" (o "</style") dentro del código cerraría la etiqueta antes de tiempo.
if (/<\/style/i.test(css)) throw new Error('styles.css contiene "</style"');
for (const [name, src] of [
  ['jszip', jszip],
  ['core', core],
  ['app', app],
]) {
  if (/<\/script/i.test(src)) throw new Error(name + ' contiene "</script"');
}

// Los marcadores deben existir una sola vez cada uno.
for (const marker of ['/*__CSS__*/', '/*__JSZIP__*/', '/*__CORE__*/', '/*__APP__*/']) {
  if (html.split(marker).length !== 2) throw new Error('Falta o se repite el marcador ' + marker);
}

// Se usan funciones de reemplazo para que los "$" del código no se interpreten.
html = html
  .replace('/*__CSS__*/', () => css)
  .replace('/*__JSZIP__*/', () => jszip)
  .replace('/*__CORE__*/', () => core)
  .replace('/*__APP__*/', () => app);

const version = (/const APP_VERSION = '([^']+)'/.exec(html) || [])[1] || '?';
fs.writeFileSync(path.join(ROOT, 'index.html'), html);
console.log(`index.html compilado · versión ${version} · ${(html.length / 1024).toFixed(0)} KB`);
