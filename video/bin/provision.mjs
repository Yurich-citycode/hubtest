#!/usr/bin/env node
/**
 * Провизion окружения для рендера видео в песочнице.
 *
 * Проблема: в песочнице нет apt, недоступны storage.googleapis.com (откуда Puppeteer
 * тянет Chrome) и релизы GitHub (откуда Remotion тянет FFmpeg). Доступны только
 * registry.npmjs.org, github.com, pypi.org.
 *
 * Решение:
 *   1. Chromium — npm-пакет @sparticuz/chromium, он сам распаковывается в /tmp/chromium
 *   2. Системные библиотеки libnspr4/libnss3 и т.д. — внутри того же пакета
 *      (bin/al2023.tar.br), распаковываем в /tmp/yurichhub-video/lib и подкладываем
 *      через LD_LIBRARY_PATH
 *   3. FFmpeg и FFprobe — npm-пакеты @ffmpeg-installer / @ffprobe-installer
 *   4. GSAP — вендорим из node_modules в video/vendor, чтобы композиции не ходили в CDN
 *
 * Результат пишется в video/.runtime/env.json — им пользуются bin/env.sh и bin/doctor.mjs.
 */
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const VIDEO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const RUNTIME_DIR = path.join(VIDEO_ROOT, '.runtime');
const LIB_DIR = '/tmp/yurichhub-video/lib';
const TAR_PATH = '/tmp/yurichhub-video/al2023.tar';

const log = (s) => console.log(s);
const warn = (s) => console.warn(s);

function need(mod) {
  try {
    return require(mod);
  } catch {
    warn(`  ✗ нет пакета ${mod} — сначала npm install`);
    process.exitCode = 1;
    return null;
  }
}

fs.mkdirSync(RUNTIME_DIR, { recursive: true });

// 1. Chromium ---------------------------------------------------------------
log('Chromium:');
const chromium = need('@sparticuz/chromium');
let browserPath = null;
if (chromium) {
  browserPath = await chromium.default.executablePath();
  log(`  ✓ ${browserPath}`);

  // 2. Системные библиотеки --------------------------------------------------
  log('Системные библиотеки:');
  // require.resolve может вернуть собранный файл (build/index.js), поэтому ищем корень пакета явно
  const libArchive = path.join(VIDEO_ROOT, 'node_modules', '@sparticuz', 'chromium', 'bin', 'al2023.tar.br');
  if (fs.existsSync(libArchive)) {
    fs.mkdirSync(path.dirname(TAR_PATH), { recursive: true });
    fs.mkdirSync(LIB_DIR, { recursive: true });
    const raw = zlib.brotliDecompressSync(fs.readFileSync(libArchive));
    fs.writeFileSync(TAR_PATH, raw);
    execFileSync('tar', ['-xf', TAR_PATH, '-C', path.join(LIB_DIR, '..')]);
    const libs = fs.readdirSync(LIB_DIR).length;
    log(`  ✓ ${libs} файлов → ${LIB_DIR}`);
  } else {
    warn('  ✗ не найден al2023.tar.br в @sparticuz/chromium');
  }

  // Проверяем, что браузер вообще запускается
  try {
    const out = execFileSync(browserPath, ['--version'], {
      env: { ...process.env, LD_LIBRARY_PATH: LIB_DIR },
      encoding: 'utf8',
    }).trim();
    log(`  ✓ запускается: ${out}`);
  } catch (err) {
    warn(`  ✗ не запускается: ${String(err.message).split('\n')[0]}`);
  }
}

// 3. FFmpeg / FFprobe --------------------------------------------------------
log('FFmpeg:');
const ffmpeg = need('@ffmpeg-installer/ffmpeg');
const ffprobe = need('@ffprobe-installer/ffprobe');
const ffmpegPath = ffmpeg ? ffmpeg.path : null;
const ffprobePath = ffprobe ? ffprobe.path : null;
for (const [name, bin] of [['ffmpeg', ffmpegPath], ['ffprobe', ffprobePath]]) {
  if (!bin) continue;
  try {
    const out = execFileSync(bin, ['-version'], { encoding: 'utf8' }).split('\n')[0];
    log(`  ✓ ${name}: ${out.slice(0, 80)}`);
  } catch {
    warn(`  ✗ ${name} не запускается: ${bin}`);
  }
}

// 4. GSAP --------------------------------------------------------------------
log('GSAP:');
const vendorDir = path.join(VIDEO_ROOT, 'vendor');
fs.mkdirSync(vendorDir, { recursive: true });
let gsapVersion = null;
try {
  const gsapPkg = require('gsap/package.json');
  gsapVersion = gsapPkg.version;
  const src = require.resolve('gsap/dist/gsap.min.js');
  const dest = path.join(vendorDir, 'gsap.min.js');
  fs.copyFileSync(src, dest);
  log(`  ✓ vendor/gsap.min.js из gsap@${gsapVersion}`);
} catch {
  warn('  ✗ gsap не найден — npm install gsap');
}

// env.json -------------------------------------------------------------------
const env = {
  browser: browserPath,
  libDir: LIB_DIR,
  ffmpeg: ffmpegPath,
  ffprobe: ffprobePath,
  gsap: path.join(vendorDir, 'gsap.min.js'),
  gsapVersion,
  provisionedAt: new Date().toISOString(),
};
fs.writeFileSync(path.join(RUNTIME_DIR, 'env.json'), JSON.stringify(env, null, 2) + '\n');
log(`\nОкружение записано: video/.runtime/env.json`);
