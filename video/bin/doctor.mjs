#!/usr/bin/env node
/**
 * Doctor: проверяет, что видео-конвейер YurichHub готов к работе.
 * Запуск:  node bin/doctor.mjs   (или npm run doctor)
 */
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const VIDEO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const HUB_ROOT = path.resolve(VIDEO_ROOT, '..');

const ok = (s) => `✓ ${s}`;
const bad = (s) => `✗ ${s}`;

const lines = [];
let failures = 0;

function check(label, fn) {
  try {
    const out = fn();
    lines.push(`  ${ok(label)}${out ? '  ' + out : ''}`);
  } catch (err) {
    failures += 1;
    lines.push(`  ${bad(label)}  ${err.message}`);
  }
}

function tryRequire(mod, what) {
  try {
    return require(mod);
  } catch {
    throw new Error(`нет пакета ${mod} — запусти bash setup.sh (${what})`);
  }
}

// Node ----------------------------------------------------------------------
check('Node.js', () => {
  const major = Number(process.versions.node.split('.')[0]);
  if (major < 22) throw new Error(`нужен Node >= 22, стоит ${process.versions.node}`);
  return `v${process.versions.node}`;
});

// npm-пакеты -----------------------------------------------------------------
const deps = {};
check('HyperFrames CLI', () => {
  const bin = path.join(VIDEO_ROOT, 'node_modules/.bin/hyperframes');
  if (!fs.existsSync(bin)) throw new Error('нет node_modules/.bin/hyperframes — запусти bash setup.sh');
  return require('hyperframes/package.json').version;
});
check('GSAP (npm)', () => (deps.gsap = tryRequire('gsap/package.json').version));
check('Chromium (npm)', () => {
  // package.json не виден через require (exports-карта), читаем напрямую
  const p = path.join(VIDEO_ROOT, 'node_modules/@sparticuz/chromium/package.json');
  if (!fs.existsSync(p)) throw new Error('нет node_modules/@sparticuz/chromium — запусти bash setup.sh');
  return (deps.chromium = JSON.parse(fs.readFileSync(p, 'utf8')).version);
});
check('FFmpeg (npm)', () => (deps.ffmpeg = tryRequire('@ffmpeg-installer/ffmpeg/package.json').version));
check('FFprobe (npm)', () => (deps.ffprobe = tryRequire('@ffprobe-installer/ffprobe/package.json').version));

// Окружение ------------------------------------------------------------------
let env = null;
check('Окружение (.runtime/env.json)', () => {
  const p = path.join(VIDEO_ROOT, '.runtime/env.json');
  if (!fs.existsSync(p)) throw new Error('нет файла — запусти node bin/provision.mjs');
  env = JSON.parse(fs.readFileSync(p, 'utf8'));
  return 'готово';
});

if (env) {
  check('Chromium запускается', () => {
    const out = execFileSync(env.browser, ['--version'], {
      env: { ...process.env, LD_LIBRARY_PATH: env.libDir },
      encoding: 'utf8',
    }).trim();
    return out;
  });
  check('FFmpeg запускается', () => execFileSync(env.ffmpeg, ['-version'], { encoding: 'utf8' }).split('\n')[0].slice(0, 60));
  check('FFprobe запускается', () => execFileSync(env.ffprobe, ['-version'], { encoding: 'utf8' }).split('\n')[0].slice(0, 60));
}

// Вендоренный контент ---------------------------------------------------------
check('vendor/gsap.min.js', () => {
  const p = path.join(VIDEO_ROOT, 'vendor/gsap.min.js');
  if (!fs.existsSync(p)) throw new Error('нет файла — запусти node bin/provision.mjs');
  return `${(fs.statSync(p).size / 1024).toFixed(0)} KB`;
});

const skillGroups = [
  ['hyperframes', 'router + домены + воркфлоу HyperFrames'],
  ['taste-skill', 'Taste Skill — анти-слоп для фронтенда'],
  ['impeccable', 'Impeccable — 24 команды дизайна'],
  ['remotion', 'Remotion — видео на React'],
  ['emil', 'скиллы Эмиля Ковальски — анимация и UI'],
];
check('Скиллы (5 наборов)', () => {
  const missing = skillGroups.filter(([dir]) => !fs.existsSync(path.join(VIDEO_ROOT, 'skills', dir)));
  if (missing.length) throw new Error(`нет: ${missing.map(([d]) => d).join(', ')}`);
  return skillGroups.map(([d]) => d).join(', ');
});

// Проекты и ассеты -------------------------------------------------------------
check('Проекты (композиции)', () => {
  const dir = path.join(VIDEO_ROOT, 'projects');
  const projects = fs.existsSync(dir) ? fs.readdirSync(dir).filter((p) => fs.existsSync(path.join(dir, p, 'index.html'))) : [];
  if (!projects.length) throw new Error('нет ни одного projects/*/index.html');
  return projects.join(', ');
});

check('Бренд-канон', () => {
  const style = path.join(HUB_ROOT, 'brand/YURICHHUB-STYLE.md');
  const fonts = path.join(HUB_ROOT, 'brand/covers/fonts');
  if (!fs.existsSync(style)) throw new Error('нет brand/YURICHHUB-STYLE.md');
  const n = fs.readdirSync(fonts).length;
  return `канон на месте, ${n} шрифтов в brand/covers/fonts`;
});

check('Каталог рендеров', () => {
  const dir = path.join(VIDEO_ROOT, 'renders');
  fs.mkdirSync(dir, { recursive: true });
  return dir;
});

// Вывод -----------------------------------------------------------------------
console.log('\nYurichHub video · doctor\n');
console.log(lines.join('\n'));
console.log(
  failures === 0
    ? '\n  Всё на месте. Рендер: bash bin/hf.sh render projects/yurichhub-intro -o renders/out.mp4\n'
    : `\n  Проблем: ${failures}. Сначала: bash setup.sh\n`,
);
process.exitCode = failures === 0 ? 0 : 1;
