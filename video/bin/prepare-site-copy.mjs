#!/usr/bin/env node
/**
 * Локальная копия сайта-хаба для съёмки кадров.
 *
 * Зачем копия, а не сам сайт: в песочнице заблокированы Google Fonts (шрифты не подгрузятся —
 * браузер подставит случайный шрифт, и кадр перестанет быть каноном). Скрипт собирает копию
 * страниц в /tmp, вшивает локальные шрифты из brand/covers/fonts и разводит латиницу с
 * кириллицей: Anton покрывает только латиницу, русский дисплей по канону — Oswald 700
 * (brand/YURICHHUB-STYLE.md, раздел 4).
 *
 *   node bin/prepare-site-copy.mjs                       # копия в /tmp/yurichhub-site
 *   node bin/prepare-site-copy.mjs --out /tmp/my-copy    # своя папка
 *
 * Дальше:  cd /tmp/yurichhub-site && python3 -m http.server 8099 --bind 127.0.0.1
 * и съёмка кадров:  node bin/capture-sections.mjs --url http://127.0.0.1:8099/index.html --sections top,sevastopol
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const VIDEO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const HUB_ROOT = path.resolve(VIDEO_ROOT, '..');

const args = process.argv.slice(2);
const arg = (name, fallback) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback;
};

const OUT = path.resolve(arg('out', '/tmp/yurichhub-site'));
const FONT_DIR = path.join(HUB_ROOT, 'brand/covers/fonts');

// Шрифты канона: файл → семейство, вес и диапазон символов
const FONTS = [
  { file: 'oswald-700.ttf', family: 'Oswald', weight: 700 },
  { file: 'inter-400.ttf', family: 'Inter', weight: 400 },
  { file: 'inter-600.ttf', family: 'Inter', weight: 600 },
  { file: 'inter-700.ttf', family: 'Inter', weight: 700 },
  { file: 'archivo-400.ttf', family: 'Archivo', weight: 400 },
  { file: 'archivo-500.ttf', family: 'Archivo', weight: 500 },
  { file: 'archivo-600.ttf', family: 'Archivo', weight: 600 },
  { file: 'archivo-700.ttf', family: 'Archivo', weight: 700 },
  { file: 'archivo-800.ttf', family: 'Archivo', weight: 800 },
  { file: 'anton-400.ttf', family: 'Anton', weight: 400 },
];

const LATIN = 'U+0000-024F,U+1E00-1EFF';
const CYRILLIC = 'U+0400-04FF,U+2116';

fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT, { recursive: true });

// 1. Страницы и медиа из корня репозитория
let pages = 0;
let assets = 0;
for (const entry of fs.readdirSync(HUB_ROOT, { withFileTypes: true })) {
  if (entry.isDirectory()) continue;
  const ext = path.extname(entry.name).toLowerCase();
  if (['.html', '.jpg', '.jpeg', '.png', '.webp', '.svg', '.pdf'].includes(ext)) {
    fs.copyFileSync(path.join(HUB_ROOT, entry.name), path.join(OUT, entry.name));
    if (ext === '.html') pages += 1;
    else assets += 1;
  }
}
// brand/ нужен страницам как brand/... — копируем выборочно то, что реально используется
const brandSrc = path.join(HUB_ROOT, 'brand');
const brandDst = path.join(OUT, 'brand');
if (fs.existsSync(brandSrc)) {
  fs.cpSync(brandSrc, brandDst, { recursive: true });
}

// 2. Шрифты
let css = '/* Локальные шрифты канона вместо Google Fonts: в песочнице CDN недоступен. */\n';
for (const font of FONTS) {
  fs.copyFileSync(path.join(FONT_DIR, font.file), path.join(OUT, font.file));
  if (font.family === 'Anton') {
    // Anton есть только в латинице: кириллицу отдаём Oswald по канону
    css += `@font-face{font-family:'Anton';src:url('${font.file}') format('truetype');font-weight:${font.weight};font-display:block;unicode-range:${LATIN};}\n`;
    css += `@font-face{font-family:'Anton';src:url('oswald-700.ttf') format('truetype');font-weight:${font.weight};font-display:block;unicode-range:${CYRILLIC};}\n`;
    continue;
  }
  css += `@font-face{font-family:'${font.family}';src:url('${font.file}') format('truetype');font-weight:${font.weight};font-display:block;}\n`;
}
fs.writeFileSync(path.join(OUT, 'local-fonts.css'), css);

// 3. Подмена ссылок на Google Fonts
let rewritten = 0;
for (const name of fs.readdirSync(OUT)) {
  if (!name.endsWith('.html')) continue;
  const file = path.join(OUT, name);
  let html = fs.readFileSync(file, 'utf8');
  const before = html;
  html = html.replace(/<link rel="preconnect" href="https?:\/\/fonts\.(googleapis|gstatic)\.com"[^>]*>\s*/g, '');
  html = html.replace(/<link href="https?:\/\/fonts\.googleapis\.com\/[^"]*" rel="stylesheet">/g, '<link href="local-fonts.css" rel="stylesheet">');
  if (html !== before) {
    fs.writeFileSync(file, html);
    rewritten += 1;
  }
}

const left = fs
  .readdirSync(OUT)
  .filter((n) => n.endsWith('.html'))
  .filter((n) => fs.readFileSync(path.join(OUT, n), 'utf8').includes('fonts.googleapis'));

console.log(`Копия сайта: ${OUT}`);
console.log(`  страниц: ${pages}, медиа: ${assets}, страниц с подменой шрифтов: ${rewritten}`);
if (left.length) {
  console.warn(`  ⚠ остались ссылки на Google Fonts: ${left.join(', ')}`);
  process.exitCode = 1;
} else {
  console.log('  ✓ внешних шрифтов не осталось');
}
console.log(`\nДальше:\n  cd ${OUT} && python3 -m http.server 8099 --bind 127.0.0.1`);
