#!/usr/bin/env node
/**
 * YurichHub post cover renderer.
 * House chassis from index.html + the X ALGO HACK v2 cover (1600×900).
 *
 *   node render.js examples/xalgo.json
 *   node render.js examples/xalgo.json --out ../samples/xalgo.png
 *
 * Spec: ../YURICHHUB-STYLE.md
 */
'use strict';

const { Resvg } = require('@resvg/resvg-js');
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const FONTS = fs.readdirSync(path.join(ROOT, 'fonts')).filter(f => f.endsWith('.ttf')).map(f => path.join(ROOT, 'fonts', f));

const C = {
  bg: '#0A0A0A',
  ink: '#F3F1EA',
  dim: '#8C8C8C',
  body: '#C4C4C4',
  lime: '#D7FF3D',
  gold: '#C8A24A',
  pink: '#E8377E',
  bronze: '#C98A4E',
  slate: '#2E3D52',
  card: '#101010',
  line: 'rgba(243,241,234,0.14)',
};

const COLOR = {
  lime: C.lime,
  gold: C.gold,
  pink: C.pink,
  bronze: C.bronze,
  slate: C.slate,
  ink: C.ink,
  dim: C.dim,
  body: C.body,
};

/** Module accent. Chassis never changes. Accent is the lead card and the footer note. Series name stays lime. */
const MODULES = {
  hub:        { accent: 'lime',   series: { ru: 'YURICHHUB', en: 'YURICHHUB' }, note: { ru: 'ЭКОСИСТЕМА // СЕВАСТОПОЛЬ', en: 'ECOSYSTEM // SEVASTOPOL' } },
  sevastopol: { accent: 'gold',   series: { ru: 'SEVASTOPOL AI', en: 'SEVASTOPOL AI' }, note: { ru: '01 ОТКРЫТИЕ // ГОРОД, КОТОРЫЙ ОТВЕЧАЕТ', en: '01 OPEN // THE CITY THAT ANSWERS' } },
  citycode:   { accent: 'lime',   series: { ru: 'CITY CODE', en: 'CITY CODE' }, note: { ru: '02 ПРИНАДЛЕЖНОСТЬ // НЕ ПРОМОКОД', en: '02 BELONGING // NOT A DISCOUNT CARD' } },
  rwa:        { accent: 'bronze', series: { ru: 'CRIMEA RWA', en: 'CRIMEA RWA' }, note: { ru: '03 ВЛАДЕНИЕ // СНАЧАЛА АКТИВ', en: '03 OWNERSHIP // ASSET FIRST' } },
  course:     { accent: 'pink',   series: { ru: 'YURICH RWA', en: 'YURICH RWA' }, note: { ru: 'КУРС // БЕЗ СИГНАЛОВ', en: 'COURSE // NO SIGNALS' } },
  glossary:   { accent: 'pink',   series: { ru: 'ГЛОССАРИЙ', en: 'GLOSSARY' }, note: { ru: 'СЛОВАРЬ RWA // 57 ТЕРМИНОВ', en: 'RWA GLOSSARY // 57 TERMS' } },
  cfa:        { accent: 'pink',   series: { ru: 'ЦФА', en: 'CFA' }, note: { ru: 'СБОРКА ВЫПУСКА // НЕ ОПЕРАТОР', en: 'ISSUE ASSEMBLY // NOT THE OPERATOR' } },
  research:   { accent: 'lime',   series: { ru: 'РАЗБОР', en: 'BREAKDOWN' }, note: { ru: 'РАЗБОР // ПО ОТКРЫТОМУ КОДУ', en: 'BREAKDOWN // STRAIGHT FROM THE CODE' } },
};

const STAT_CYCLE = ['lime', 'ink', 'pink', 'gold'];

function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function hasCyr(s) {
  return /[А-Яа-яЁё]/.test(String(s || ''));
}

/** Advance ratios measured from these exact font files (letter-spacing excluded). */
function advance(fam, text) {
  const t = String(text);
  let em = 0.50;
  if (fam === 'Anton') em = 0.44;
  else if (fam === 'Oswald') em = hasCyr(t) ? 0.56 : 0.45;
  else if (fam === 'Inter') em = hasCyr(t) ? 0.56 : 0.50;
  else if (fam === 'Archivo') em = 0.52;
  return t.length * em;
}

function fitSize(fam, text, maxW, pref, min) {
  const t = String(text || '');
  if (!t) return pref;
  const ls = 2;
  let size = pref;
  while (size > min && (advance(fam, t) * size + Math.max(0, t.length - 1) * ls) > maxW) size -= 1;
  return size;
}

let NOISE = '';
function noise(w, h) {
  if (NOISE) return NOISE;
  const nsvg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%" height="100%" filter="url(#n)" opacity="0.55"/></svg>`;
  NOISE = 'data:image/png;base64,' + new Resvg(nsvg, {}).render().asPng().toString('base64');
  return NOISE;
}

function render(spec) {
  const lang = spec.lang === 'en' ? 'en' : 'ru';
  const mod = MODULES[spec.module] || MODULES.hub;
  const accentName = spec.accent || mod.accent;
  const accent = COLOR[accentName] || C.lime;
  const layout = spec.layout || 'poster';
  const format = spec.format === 'square' ? 'square' : 'x';
  const W = format === 'square' ? 1080 : 1600;
  const H = format === 'square' ? 1080 : 900;
  const disp = lang === 'en' ? 'Anton' : 'Oswald';
  const sans = lang === 'en' ? 'Archivo' : 'Inter';
  const sansW = lang === 'en' ? 500 : 400;

  const series = spec.series || mod.series[lang];
  const note = spec.footerNote || mod.note[lang];
  const date = spec.date || '';

  const parts = [];
  const add = s => parts.push(s);

  add(`<rect width="${W}" height="${H}" fill="${C.bg}"/>`);
  // House glows are fixed. Module accent lives on the cards, not the background.
  // A pink or bronze ellipse at this opacity reads as a different poster. Don't.
  if (format === 'x') {
    add(`<ellipse cx="240" cy="80" rx="700" ry="420" fill="${C.lime}" opacity="0.05"/>`);
    add(`<ellipse cx="1420" cy="860" rx="720" ry="440" fill="${C.gold}" opacity="0.05"/>`);
  } else {
    add(`<ellipse cx="160" cy="60" rx="480" ry="320" fill="${C.lime}" opacity="0.05"/>`);
    add(`<ellipse cx="980" cy="1040" rx="520" ry="340" fill="${C.gold}" opacity="0.05"/>`);
  }

  if (layout === 'statement') statement(add, spec, { W, H, lang, disp, sans, sansW, accent });
  else poster(add, spec, { W, H, lang, disp, sans, sansW, accent, format });

  footer(add, { W, H, disp, sans, series, note, date, format, index: spec.index || '' });
  add(`<image x="0" y="0" width="${W}" height="${H}" href="${noise(W, H)}" opacity="0.07"/>`);

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${parts.join('')}</svg>`;
  const png = new Resvg(svg, {
    font: { fontFiles: FONTS, loadSystemFonts: false, defaultFontFamily: sans },
  }).render().asPng();
  return png;
}

function dispText(x, y, str, o) {
  const { size, fill, glitch, fam, ls = 1, stroke: doStroke = true } = o;
  // Poster card figures have no stroke. That is how xalgo-cover.png was built.
  // Headlines, the mark and statement figures keep the Oswald stroke.
  const sw = doStroke && fam === 'Oswald' ? Math.max(1, size * 0.028) : 0;
  let s = '';
  if (glitch) {
    const dx = size >= 120 ? 6 : 5;
    const dy = size >= 120 ? 5 : 4;
    s += `<text x="${x + dx}" y="${y + dy}" font-family="${fam}" font-weight="700" font-size="${size}" fill="${C.pink}" opacity="0.7" letter-spacing="${ls}">${esc(str)}</text>`;
    s += `<text x="${x - dx}" y="${y - (dy - 1)}" font-family="${fam}" font-weight="700" font-size="${size}" fill="${C.lime}" opacity="0.5" letter-spacing="${ls}">${esc(str)}</text>`;
  }
  const stroke = sw ? ` stroke="${fill}" stroke-width="${sw}"` : '';
  s += `<text x="${x}" y="${y}" font-family="${fam}" font-weight="700" font-size="${size}" fill="${fill}" letter-spacing="${ls}"${stroke}>${esc(str)}</text>`;
  return s;
}

function sansText(x, y, str, o) {
  const { size = 16, fam, fill = C.body, weight = 500, anchor = 'start', ls = 0, up = false } = o;
  const txt = up ? String(str).toUpperCase() : String(str);
  return `<text x="${x}" y="${y}" font-family="${fam}" font-weight="${weight}" font-size="${size}" fill="${fill}" text-anchor="${anchor}" letter-spacing="${ls}">${esc(txt)}</text>`;
}

function fitLabel(fam, text, maxW, prefSize, prefLs) {
  const t = String(text || '');
  let size = prefSize;
  let ls = prefLs;
  const width = () => advance(fam, t.toUpperCase()) * size + Math.max(0, t.length - 1) * ls;
  if (!t) return { size, ls };
  while (ls > 0.6 && width() > maxW) ls = Math.round((ls - 0.2) * 10) / 10;
  while (size > 10 && width() > maxW) size -= 0.5;
  return { size, ls };
}

function card(x, y, w, h, shadow) {
  let s = '';
  if (shadow) s += `<rect x="${x + 6}" y="${y + 6}" width="${w}" height="${h}" fill="${shadow}"/>`;
  s += `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${C.card}" stroke="${C.line}" stroke-width="1.5"/>`;
  return s;
}

function poster(add, spec, ctx) {
  const { W, H, disp, sans, format } = ctx;
  const M = format === 'square' ? 48 : 70;
  const inner = W - M * 2;

  if (spec.source) {
    const srcSize = format === 'square' ? 11 : 12;
    add(sansText(W - M, format === 'square' ? 78 : 106, spec.source, {
      size: srcSize, fam: sans, weight: 700, ls: format === 'square' ? 1.4 : 2, fill: C.dim, anchor: 'end', up: true,
    }));
  }

  const title = String(spec.title || '').toUpperCase();
  const maxTitle = format === 'square' ? 118 : 168;
  const minTitle = format === 'square' ? 54 : 64;
  let titleSize = fitSize(disp, title, inner - 8, maxTitle, minTitle);
  // Two lines if a single line would drop below the floor and the string has a space.
  let lines = [title];
  if (titleSize <= minTitle + 8 && title.includes(' ')) {
    const mid = splitEven(title);
    lines = mid;
    titleSize = Math.min(...lines.map(l => fitSize(disp, l, inner - 8, maxTitle, minTitle)));
  }

  const titleTop = format === 'square' ? 250 : 318;
  const titleStep = Math.round(titleSize * 0.92);
  lines.forEach((line, i) => {
    add(dispText(format === 'square' ? M - 2 : 66, titleTop + i * titleStep, line, {
      size: titleSize, fill: C.ink, glitch: spec.glitch !== false && i === 0, fam: disp, ls: 2,
    }));
  });

  const subY = titleTop + (lines.length - 1) * titleStep + Math.round(titleSize * 0.52);
  if (spec.subtitle) {
    const sub = String(spec.subtitle).toUpperCase();
    const subPref = format === 'square' ? 28 : 40;
    const subSize = fitSize(disp, sub, inner, subPref, 18);
    const subColor = COLOR[spec.subtitleColor] || C.gold;
    add(dispText(M, subY, sub, { size: subSize, fill: subColor, fam: disp, ls: 1 }));
  }

  const stats = (spec.stats || []).slice(0, 4);
  const squareRows = stats.length ? (stats.length <= 2 ? 1 : 2) : 0;
  const squareCardH = 148;
  const squareGap = 20;
  const squareCardsTop = squareRows
    ? (H - 108) - 28 - (squareRows * squareCardH + (squareRows - 1) * squareGap)
    : H - 140;

  if (stats.length && format === 'x') {
    const y = 500;
    const h = 150;
    const gap = 24;
    const cw = Math.floor((inner - gap * (stats.length - 1)) / stats.length);
    stats.forEach((st, i) => {
      const col = COLOR[st.color] || COLOR[STAT_CYCLE[i % 4]];
      const x = M + i * (cw + gap);
      add(card(x, y, cw, h, col));
      add(`<rect x="${x}" y="${y}" width="6" height="${h}" fill="${col}"/>`);
      const val = String(st.value);
      const valSize = fitSize(disp, val, cw - 48, 56, 28);
      // Canon RU baseline is 74, EN Anton is 78. No stroke on the figure.
      const valY = y + (disp === 'Oswald' ? 74 : 78);
      add(dispText(x + 26, valY, val, { size: valSize, fill: C.ink, fam: disp, ls: 1, stroke: false }));
      const lab = fitLabel(sans, st.label || '', cw - 52, 12.5, 2);
      const labY = y + (disp === 'Oswald' ? 116 : 120);
      add(sansText(x + 26, labY, st.label || '', {
        size: lab.size, fam: sans, weight: 700, ls: lab.ls, fill: C.dim, up: true,
      }));
    });
  } else if (stats.length && format === 'square') {
    const cols = stats.length <= 2 ? stats.length : 2;
    const cw = Math.floor((inner - squareGap * (cols - 1)) / cols);
    stats.forEach((st, i) => {
      const col = COLOR[st.color] || COLOR[STAT_CYCLE[i % 4]];
      const x = M + (i % cols) * (cw + squareGap);
      const y = squareCardsTop + Math.floor(i / cols) * (squareCardH + squareGap);
      add(card(x, y, cw, squareCardH, col));
      add(`<rect x="${x}" y="${y}" width="6" height="${squareCardH}" fill="${col}"/>`);
      const valSize = fitSize(disp, String(st.value), cw - 44, 52, 28);
      add(dispText(x + 24, y + 72, String(st.value), { size: valSize, fill: C.ink, fam: disp, ls: 1, stroke: false }));
      const lab = fitLabel(sans, st.label || '', cw - 48, 13, 1.4);
      add(sansText(x + 24, y + 112, st.label || '', {
        size: lab.size, fam: sans, weight: 700, ls: lab.ls, fill: C.dim, up: true,
      }));
    });
  }

  if (spec.body && format === 'x') {
    const body = String(spec.body);
    const size = 16.5;
    const maxChars = Math.floor(inner / (size * (hasCyr(body) ? 0.56 : 0.52)));
    const wrapped = wrap(body, maxChars).slice(0, 2);
    wrapped.forEach((ln, i) => {
      add(sansText(M + 2, 706 + i * 26, ln, { size, fam: sans, weight: 400, fill: C.body }));
    });
  } else if (spec.body && format === 'square') {
    const bodyY = (spec.subtitle ? subY : titleTop) + 44;
    const wrapped = wrap(String(spec.body), 42).slice(0, 3);
    wrapped.forEach((ln, i) => {
      const y = bodyY + i * 26;
      if (y < squareCardsTop - 8) {
        add(sansText(M, y, ln, { size: 18, fam: sans, weight: 400, fill: C.body }));
      }
    });
  }
}

function statement(add, spec, ctx) {
  const { W, disp, sans } = ctx;
  const M = 70;
  const inner = W - M * 2;

  if (spec.kicker) {
    const label = String(spec.kicker).toUpperCase();
    const size = 13;
    const wl = Math.round(label.length * size * 0.62 + 46);
    add(`<g transform="rotate(-1.6 ${M + 4} 108)">
      <rect x="${M + 4}" y="84" width="${wl}" height="34" fill="none" stroke="${C.line}" stroke-width="1.5"/>
      <rect x="${M + 13}" y="97" width="9" height="9" fill="${C.lime}"/>
      <text x="${M + 32}" y="108" font-family="${sans}" font-weight="700" font-size="${size}" letter-spacing="2.2" fill="${C.dim}">${esc(label)}</text>
    </g>`);
  }
  if (spec.source) {
    add(sansText(W - M, 106, spec.source, {
      size: 12, fam: sans, weight: 700, ls: 1.6, fill: C.dim, anchor: 'end', up: true,
    }));
  }

  const lines = (spec.lines && spec.lines.length ? spec.lines : [
    { text: spec.title || '', color: 'ink', glitch: spec.glitch !== false },
    spec.subtitle ? { text: spec.subtitle, color: 'gold' } : null,
  ].filter(Boolean)).slice(0, 3);

  let y = 300;
  lines.forEach((ln, i) => {
    const text = String(ln.text || '').toUpperCase();
    const pref = i === 2 ? 92 : 104;
    const size = fitSize(disp, text, inner, ln.size || pref, 42);
    const fill = COLOR[ln.color] || C.ink;
    add(dispText(M, y, text, { size, fill, glitch: !!ln.glitch, fam: disp, ls: 1 }));
    y += Math.round(size * 1.02);
  });

  const bodyLines = Array.isArray(spec.body) ? spec.body : wrap(String(spec.body || ''), 78);
  let by = Math.min(y + 28, 574);
  bodyLines.slice(0, 2).forEach(ln => {
    add(sansText(M + 2, by, ln, { size: 19, fam: sans, weight: 400, fill: C.body }));
    by += 28;
  });

  const stats = (spec.stats || []).slice(0, 4);
  if (stats.length) {
    const y0 = 668;
    const h = 112;
    add(`<line x1="${M}" y1="${y0}" x2="${W - M}" y2="${y0}" stroke="${C.line}" stroke-width="2"/>`);
    add(`<line x1="${M}" y1="${y0 + h}" x2="${W - M}" y2="${y0 + h}" stroke="${C.line}" stroke-width="2"/>`);
    const colW = inner / stats.length;
    stats.forEach((st, i) => {
      const x = M + i * colW;
      if (i) add(`<line x1="${x}" y1="${y0}" x2="${x}" y2="${y0 + h}" stroke="${C.line}" stroke-width="2"/>`);
      const col = COLOR[st.color] || COLOR[STAT_CYCLE[i % 4]];
      const valSize = fitSize(disp, String(st.value), colW - 40, 46, 26);
      add(dispText(x + 26, y0 + 58, String(st.value), { size: valSize, fill: col, fam: disp, ls: 1 }));
      add(sansText(x + 26, y0 + 90, st.label || '', {
        size: 12, fam: sans, weight: 700, ls: 1.6, fill: C.dim, up: true,
      }));
    });
  }

  if (spec.cta) {
    add(sansText(W - M, 800, spec.cta, {
      size: 14, fam: sans, weight: 800, ls: 2, fill: C.lime, anchor: 'end', up: true,
    }));
  }
}

function footer(add, o) {
  const { W, H, disp, sans, series, note, date, format, index } = o;
  const M = format === 'square' ? 48 : 70;
  const lineY = H - (format === 'square' ? 108 : 88);
  add(`<line x1="${M}" y1="${lineY}" x2="${W - M}" y2="${lineY}" stroke="${C.line}" stroke-width="2"/>`);
  const brandY = lineY + 44;
  const noteY = brandY + 20;
  const sw = disp === 'Oswald' ? 0.6 : 0;
  const stroke = sw ? ` stroke="${C.ink}" stroke-width="${sw}"` : '';
  add(`<text x="${M}" y="${brandY}" font-family="${disp}" font-weight="700" font-size="22" fill="${C.ink}" letter-spacing="1"${stroke}>YURICH<tspan fill="${C.lime}">HUB</tspan></text>`);
  if (note) {
    add(sansText(M, noteY, note, { size: 11, fam: sans, weight: 600, ls: 1.8, fill: C.dim, up: true }));
  }
  if (date) {
    add(sansText(W - M, brandY - 6, date, { size: 13, fam: sans, weight: 700, ls: 1.8, fill: C.dim, anchor: 'end', up: true }));
  }
  const right = index || series;
  if (right) {
    const size = fitSize(disp, String(right).toUpperCase(), 420, 20, 14);
    const sw = disp === 'Oswald' ? Math.max(0.5, size * 0.028) : 0;
    const stroke = sw ? ` stroke="${C.lime}" stroke-width="${sw}"` : '';
    add(`<text x="${W - M}" y="${noteY - 2}" font-family="${disp}" font-weight="700" font-size="${size}" fill="${C.lime}" text-anchor="end" letter-spacing="1"${stroke}>${esc(String(right).toUpperCase())}</text>`);
  }
}

function estimate(fam, text, size) {
  return advance(fam, text) * size + Math.max(0, text.length - 1);
}

function splitEven(text) {
  const words = text.split(/\s+/);
  if (words.length < 2) return [text];
  let best = 1;
  let bestDiff = Infinity;
  for (let i = 1; i < words.length; i++) {
    const a = words.slice(0, i).join(' ');
    const b = words.slice(i).join(' ');
    const d = Math.abs(a.length - b.length);
    if (d < bestDiff) { bestDiff = d; best = i; }
  }
  return [words.slice(0, best).join(' '), words.slice(best).join(' ')];
}

function wrap(str, max) {
  const words = String(str).split(/\s+/);
  const lines = [];
  let line = '';
  for (const w of words) {
    if ((line + ' ' + w).trim().length > max) {
      if (line) lines.push(line.trim());
      line = w;
    } else line += ' ' + w;
  }
  if (line.trim()) lines.push(line.trim());
  return lines;
}

function readSpec(file) {
  const raw = fs.readFileSync(file, 'utf8');
  return JSON.parse(raw);
}

function flagValue(args, name) {
  const i = args.indexOf(name);
  if (i === -1 || i + 1 >= args.length) return null;
  return args[i + 1];
}

function applyFlags(spec, args) {
  const map = {
    '--lang': 'lang',
    '--module': 'module',
    '--layout': 'layout',
    '--format': 'format',
    '--title': 'title',
    '--subtitle': 'subtitle',
    '--subtitle-color': 'subtitleColor',
    '--body': 'body',
    '--source': 'source',
    '--date': 'date',
    '--series': 'series',
    '--note': 'footerNote',
    '--index': 'index',
    '--kicker': 'kicker',
    '--cta': 'cta',
  };
  const stats = [];
  const lines = [];
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === '--no-glitch') { spec.glitch = false; continue; }
    if (a === '--glitch') { spec.glitch = true; continue; }
    if (a === '--out' || a === '--help' || a === '-h') { i++; continue; }
    if (a === '--stat') {
      const raw = args[++i] || '';
      const [value, label, color] = raw.split('|');
      stats.push({ value: value || '', label: label || '', color: color || undefined });
      continue;
    }
    if (a === '--line') {
      const raw = args[++i] || '';
      const [text, color, glitch] = raw.split('|');
      lines.push({ text: text || '', color: color || 'ink', glitch: glitch === 'glitch' });
      continue;
    }
    if (map[a]) spec[map[a]] = args[++i];
  }
  if (stats.length) spec.stats = stats;
  if (lines.length) spec.lines = lines;
  return spec;
}

function help() {
  console.log(`YurichHub cover

  node render.js examples/xalgo.json --out ../samples/xalgo.png
  node render.js post.json --title "НЕ ТОКЕН" --module cfa --out cover.png
  node render.js --module sevastopol --title "SEVASTOPOL AI" \\
      --subtitle "ГОРОД, КОТОРЫЙ ОТВЕЧАЕТ" \\
      --body "Не справочник на 200 позиций." \\
      --stat "160+|МЕСТ ЕДЫ|gold" --stat "55|ЛОКАЦИЙ|ink" \\
      --source "T.ME/SEVASTOPOLAIBOT" --date 09.2026 --out cover.png

Модули: ${Object.keys(MODULES).join(', ')}
Макеты: poster | statement
Форматы: x (1600x900) | square (1080x1080)
Цвета: lime, ink, pink, gold, bronze
--stat "цифра|подпись|цвет" можно повторять, до 4.
Спека: ../YURICHHUB-STYLE.md`);
}

function main() {
  const args = process.argv.slice(2);
  if (!args.length || args.includes('-h') || args.includes('--help')) {
    help();
    process.exit(args.length ? 0 : 1);
  }
  const file = args[0].endsWith('.json') ? args[0] : null;
  let spec = file
    ? readSpec(path.resolve(file))
    : { lang: 'ru', module: 'hub', layout: 'poster', format: 'x', glitch: true, stats: [] };
  spec = applyFlags(spec, args);
  if (!file && !spec.title && !(spec.lines && spec.lines.length)) {
    help();
    process.exit(1);
  }
  let out = flagValue(args, '--out') || '';
  const png = render(spec);
  if (!out) {
    const base = file ? path.basename(file, '.json') : 'cover';
    out = path.join(ROOT, 'out', base + '.png');
  }
  fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true });
  fs.writeFileSync(out, png);
  console.log(out, png.length);
}

if (require.main === module) main();

module.exports = { render, MODULES, C };
