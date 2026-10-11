#!/usr/bin/env node
/**
 * Скриншоты секций сайта для видео.
 *
 * Зачем: нарезка full-page.png режет блоки по краям, а для видео нужны точные кадры
 * секций. Скрипт открывает страницу в локальном Chromium и снимает каждый указанный
 * элемент целиком (captureBeyondViewport), в 1920×1080, без скроллбаров.
 *
 *   node bin/capture-sections.mjs \
 *     --url http://127.0.0.1:8099/index.html \
 *     --out captures/site-index/sections \
 *     --sections top,sevastopol,citycode,rwa,course,cfa \
 *     --wait 2500
 *
 * Служебные кадры для видео живут в captures/ — это промежуточный артефакт,
 * в git он не едет.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';

const VIDEO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

const args = process.argv.slice(2);
const arg = (name, fallback) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback;
};

const url = arg('url');
if (!url) {
  console.error('Нужен --url. Пример: node bin/capture-sections.mjs --url http://127.0.0.1:8099/index.html --sections top,sevastopol');
  process.exit(1);
}
const outDir = path.resolve(VIDEO_ROOT, arg('out', 'captures/sections'));
const sections = arg('sections', 'top').split(',').map((s) => s.trim()).filter(Boolean);
const waitMs = Number(arg('wait', 2500));
const width = Number(arg('width', 1920));
const height = Number(arg('height', 1080));

const env = JSON.parse(fs.readFileSync(path.join(VIDEO_ROOT, '.runtime/env.json'), 'utf8'));
fs.mkdirSync(outDir, { recursive: true });

const browser = await puppeteer.launch({
  executablePath: env.browser,
  // Chromium из npm требует системные библиотеки, распакованные provision-скриптом
  env: { ...process.env, LD_LIBRARY_PATH: `${env.libDir}:${process.env.LD_LIBRARY_PATH || ''}` },
  args: ['--no-sandbox', '--disable-gpu', '--force-color-profile=srgb', '--hide-scrollbars'],
  headless: true,
});

try {
  const page = await browser.newPage();
  await page.setViewport({ width, height, deviceScaleFactor: 1 });
  await page.goto(url, { waitUntil: 'networkidle2', timeout: 120000 });
  // Даём странице доиграть входные анимации (на сайте хаба это .page-ready через JS)
  await new Promise((r) => setTimeout(r, waitMs));

  let done = 0;
  for (const id of sections) {
    const selector = id.startsWith('#') || id.startsWith('.') ? id : `#${id}`;
    const el = await page.$(selector);
    if (!el) {
      console.warn(`  ✗ нет элемента ${selector}`);
      continue;
    }

    // Сайт хаба — скролл-сцены: элементы живут в sticky-слоях и раскрываются по мере
    // прокрутки, поэтому снимаем не сам элемент, а вьюпорт после прокрутки к нему.
    await page.evaluate((sel) => {
      const node = document.querySelector(sel);
      const y = node.getBoundingClientRect().top + window.scrollY;
      window.scrollTo({ top: y, behavior: 'auto' });
    }, selector);
    await new Promise((r) => setTimeout(r, 900)); // даём доиграть reveal-анимации

    const file = path.join(outDir, `${id.replace(/^[#.]/, '')}.png`);
    await page.screenshot({ path: file });
    console.log(`  ✓ ${id}  ${width}×${height}  ${path.relative(VIDEO_ROOT, file)}`);
    done += 1;
  }
  console.log(`\nСнято секций: ${done} → ${path.relative(VIDEO_ROOT, outDir)}`);
} finally {
  await browser.close();
}
