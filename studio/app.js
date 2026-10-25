/* ═══════════════════════════════════════════════════════════════════
   Движок студии: форма → холст → PNG.
   Всё хранится в браузере (localStorage). Ничего не уходит на сервер.
   ?tpl=<id>&fmt=<key>&clean=1 — показать только холст (для проверки/печати).
   ═══════════════════════════════════════════════════════════════════ */
(function () {
  const FORMATS = {
    '16x9': { label: '16:9 · пост / обложка 1280×720', w: 1280, h: 720 },
    '1x1': { label: '1:1 · квадрат 1080×1080', w: 1080, h: 1080 },
    '4x5': { label: '4:5 · лента 1080×1350', w: 1080, h: 1350 },
    '9x16': { label: '9:16 · сторис 1080×1920', w: 1080, h: 1920 },
    'a6': { label: 'Печать A6/A5/A4 · 1240×1748', w: 1240, h: 1748 },
  };
  const KEY = 'studio.v1';
  const $ = (s, r = document) => r.querySelector(s);
  const el = (tag, attrs = {}, ...kids) => {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === 'class') e.className = v; else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else if (v !== undefined && v !== null) e.setAttribute(k, v);
    }
    kids.flat().forEach((c) => c != null && e.append(c.nodeType ? c : document.createTextNode(c)));
    return e;
  };
  const clone = (o) => JSON.parse(JSON.stringify(o));

  // ── состояние ──
  const T = window.TEMPLATES, byId = Object.fromEntries(T.map((t) => [t.id, t]));
  let st = { tpl: T[0].id, fmt: '16x9', data: {} };
  try { Object.assign(st, JSON.parse(localStorage.getItem(KEY) || '{}')); } catch (e) { /* пусто */ }
  const qs = new URLSearchParams(location.search);
  if (qs.get('tpl') && byId[qs.get('tpl')]) st.tpl = qs.get('tpl');
  if (qs.get('fmt') && FORMATS[qs.get('fmt')]) st.fmt = qs.get('fmt');
  const CLEAN = qs.has('clean');
  if (CLEAN) st.data = {}; // чистый режим — всегда демо-данные

  const dataOf = (id) => { const t = byId[id]; return Object.assign(clone(t.defaults), st.data[id] || {}); };
  const tpl = () => byId[st.tpl];
  if (!tpl().formats.includes(st.fmt)) st.fmt = tpl().formats[0];

  let saveT;
  function save() {
    if (CLEAN) return;
    clearTimeout(saveT);
    saveT = setTimeout(() => {
      try { localStorage.setItem(KEY, JSON.stringify(st)); msg(''); } catch (e) { msg('⚠ Память браузера заполнена: сохрани пресет в файл и удали лишние картинки.'); }
    }, 300);
  }
  function msg(t) { const m = $('#msg'); if (m) m.textContent = t; }

  // ── помощники для шаблонов ──
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const rich = (s) => esc(s).replace(/\*([^*]+)\*/g, '<span class="hl">$1</span>').replace(/\n/g, '<br>');
  const url = (s) => `url('${String(s).replace(/'/g, '%27').replace(/"/g, '%22')}')`;
  const swoosh = (c, w = 30) => `<svg class="swoosh" viewBox="0 0 300 30" preserveAspectRatio="none" style="width:${w}em;height:${w / 18}em"><path d="M4 22C70 9 170 3 296 11" stroke="${c}" stroke-width="7" fill="none" stroke-linecap="round"/><path d="M30 26C110 16 190 14 270 18" stroke="${c}" stroke-width="2.4" fill="none" stroke-linecap="round" opacity=".7"/></svg>`;
  const sig = (name) => `<div class="sig"><span class="ln"></span>by <b>${esc(name || 'YuRichRWA')}<svg viewBox="0 0 300 30" preserveAspectRatio="none"><path d="M4 20C80 6 180 2 296 12" stroke="#FF1F8F" stroke-width="9" fill="none" stroke-linecap="round"/></svg></b></div>`;
  const crosshair = (c) => `<svg viewBox="0 0 100 100" width="100%" height="100%"><g fill="none" stroke="${c}" stroke-linecap="round"><circle cx="50" cy="50" r="30" stroke-width="4"/><circle cx="50" cy="50" r="44" stroke-width="1.6" stroke-dasharray="4 5"/><path d="M50 2v30M50 68v30M2 50h30M68 50h30" stroke-width="4"/></g><circle cx="50" cy="50" r="3.4" fill="#111"/></svg>`;
  const dots = (c, cols, rows) => { let s = ''; for (let y = 0; y < rows; y++) for (let x = 0; x < cols; x++) s += `<circle cx="${x * 10 + 5}" cy="${y * 10 + 5}" r="1.5"/>`; return `<svg viewBox="0 0 ${cols * 10} ${rows * 10}" width="100%" height="100%" fill="${c}" opacity=".55">${s}</svg>`; };
  function qr(text) {
    const q = window.qrcode(0, 'M'); q.addData(text); q.make();
    const n = q.getModuleCount(); let p = '';
    for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) if (q.isDark(r, c)) p += `M${c} ${r}h1v1h-1z`;
    return `<svg viewBox="0 0 ${n} ${n}" shape-rendering="crispEdges"><path d="${p}" fill="#09111F"/></svg>`;
  }

  // Мозаика: две «C», каждая разбита на кольцевые секторы. Ячейка = партнёр.
  let uid = 0;
  function mosaic({ perC = 10, rings = 2, items = [], highlight = -1 }) {
    const id = 'm' + (++uid), R = 100, toR = Math.PI / 180;
    const radii = rings === 2 ? [[67, 100], [32, 65]] : [[42, 100]];
    const perRing = Math.round(perC / rings), a0 = -40, span = 280 / perRing, gap = 1.6;
    const centers = [[105, 105], [295, 105]];
    const P = (cx, cy, r, a) => [(cx + r * Math.cos(a * toR)).toFixed(2), (cy + r * Math.sin(a * toR)).toFixed(2)];
    let cells = '', defs = '', nodes = '', idx = 0;
    centers.forEach(([cx, cy]) => {
      radii.forEach(([ri, ro]) => {
        for (let s = 0; s < perRing; s++) {
          const ta = a0 - s * span - gap / 2, tb = a0 - (s + 1) * span + gap / 2;
          const [x1, y1] = P(cx, cy, ro, ta), [x2, y2] = P(cx, cy, ro, tb), [x3, y3] = P(cx, cy, ri, tb), [x4, y4] = P(cx, cy, ri, ta);
          const d = `M${x1} ${y1}A${ro} ${ro} 0 0 0 ${x2} ${y2}L${x3} ${y3}A${ri} ${ri} 0 0 1 ${x4} ${y4}Z`;
          const tm = (ta + tb) / 2, rm = (ri + ro) / 2, [mx, my] = P(cx, cy, rm, tm).map(Number);
          const sz = 0.8 * Math.min(ro - ri, 2 * rm * Math.sin(((ta - tb) / 2) * toR));
          const it = items[idx], hl = idx === highlight, num = idx + 1;
          if (it && (it.logo || it.name)) {
            cells += `<path d="${d}" fill="#F3F1EA" stroke="${hl ? '#D7FF3D' : 'rgba(243,241,234,.6)'}" stroke-width="${hl ? 3.2 : 0.8}" ${hl ? `filter="url(#${id}g)"` : ''}/>`;
            if (it.logo) {
              defs += `<clipPath id="${id}c${idx}"><rect x="${mx - sz / 2}" y="${my - sz / 2}" width="${sz}" height="${sz}" rx="${sz * 0.18}"/></clipPath>`;
              cells += `<image href="${esc(it.logo)}" x="${mx - sz / 2}" y="${my - sz / 2}" width="${sz}" height="${sz}" preserveAspectRatio="xMidYMid slice" clip-path="url(#${id}c${idx})"/>`;
            } else {
              cells += `<text x="${mx}" y="${my}" text-anchor="middle" dominant-baseline="central" font-family="Unbounded" font-weight="700" font-size="${sz * 0.42}" fill="#0B0D12">${esc((it.name || '').trim().slice(0, 2).toUpperCase())}</text>`;
            }
          } else {
            cells += `<path d="${d}" fill="rgba(243,241,234,.035)" stroke="${hl ? '#D7FF3D' : 'rgba(215,255,61,.38)'}" stroke-width="${hl ? 3 : 0.9}" stroke-dasharray="${hl ? '' : '3 3'}"/>`;
            cells += `<text x="${mx}" y="${my}" text-anchor="middle" dominant-baseline="central" font-family="Unbounded" font-weight="700" font-size="${sz * 0.34}" fill="rgba(243,241,234,.38)">${String(num).padStart(2, '0')}</text>`;
          }
          [[x1, y1], [x2, y2], [x3, y3], [x4, y4]].forEach(([x, y]) => { nodes += `<circle cx="${x}" cy="${y}" r="1.7"/>`; });
          idx++;
        }
      });
    });
    return `<svg viewBox="0 0 400 210" width="100%" height="100%" preserveAspectRatio="xMidYMid meet"><defs>${defs}<filter id="${id}g" x="-50%" y="-50%" width="200%" height="200%"><feDropShadow dx="0" dy="0" stdDeviation="4" flood-color="#D7FF3D" flood-opacity=".9"/></filter></defs>${cells}<g fill="#D7FF3D" opacity=".75">${nodes}</g></svg>`;
  }

  const helpers = (fmtKey) => ({ esc, rich, url, swoosh, sig, crosshair, dots, qr, mosaic, fmt: Object.assign({ key: fmtKey }, FORMATS[fmtKey]), shared: (id) => byId[id] ? dataOf(id) : null });

  // ── рендер холста ──
  function buildCanvas(id, fmtKey, data) {
    const t = byId[id], F = FORMATS[fmtKey];
    const cv = el('div', { class: `cv b-${t.brand}`, id: 'canvas' });
    cv.style.width = F.w + 'px'; cv.style.height = F.h + 'px'; cv.style.fontSize = (Math.min(F.w, F.h) / 72) + 'px';
    // Позиции и размеры в inline-style задаются в «дизайн-em» (1em = короткая сторона / 72).
    // Переводим их в px, чтобы они не зависели от шрифта самого элемента и от автоподгонки.
    const base = Math.min(F.w, F.h) / 72;
    const px = (v) => (parseFloat(v) * base).toFixed(2) + 'px';
    // Сторис: текстовые шаблоны берут раскладку 4:5 и встают по центру безопасной зоны,
    // фон растягивается на весь кадр 9:16.
    const boxed = fmtKey === '9x16' && t.story === 'box';
    const layoutKey = boxed ? '4x5' : fmtKey;
    const html = t.render(data, helpers(layoutKey)).replace(/style="([^"]*)"/g, (m, css) => 'style="' + css
      .replace(/(^|;|\s)(left|top|right|bottom|width|height)\s*:\s*(-?[\d.]+)em/g, (mm, pre, k, v) => `${pre}${k}:${px(v)}`)
      .replace(/calc\(50% - ([\d.]+)em\)/g, (mm, v) => `calc(50% - ${px(v)})`) + '"')
      // однофайловая сборка (Студия.html): картинки из assets/ подставляются как data: из window.STUDIO_ASSETS
      .replace(/assets\/[\w\/.-]+\.(?:jpe?g|png|webp|svg)/g, (m) => (window.STUDIO_ASSETS && window.STUDIO_ASSETS[m]) || m);
    if (boxed) {
      const bh = FORMATS['4x5'].h, off = (F.h - bh) / 2;
      cv.innerHTML = `<div class="storybox" style="position:absolute;left:0;top:${off}px;width:${F.w}px;height:${bh}px">${html}</div>`;
      cv.querySelectorAll('.storybox > .plate').forEach((p) => { p.style.top = -off + 'px'; p.style.bottom = -off + 'px'; });
    } else cv.innerHTML = html;
    return cv;
  }
  function autofit(root) {
    root.querySelectorAll('.fit').forEach((e) => {
      e.style.fontSize = '';
      let fs = parseFloat(getComputedStyle(e).fontSize), min = fs * 0.35, guard = 0;
      const over = () => {
        // один ребёнок — меряем его коробку (выносные элементы шрифта не считаем переполнением)
        if (e.children.length === 1) { const c = e.firstElementChild; return c.offsetHeight > e.clientHeight + 1 || c.scrollWidth > e.clientWidth + 1; }
        return e.scrollHeight > e.clientHeight + 1 || e.scrollWidth > e.clientWidth + 1;
      };
      while (over() && fs > min && guard++ < 60) { fs *= 0.95; e.style.fontSize = fs + 'px'; }
    });
  }
  let renderSeq = 0;
  async function render() {
    const seq = ++renderSeq, t = tpl(), F = FORMATS[st.fmt];
    const cv = buildCanvas(t.id, st.fmt, dataOf(t.id));
    const host = $('#stage');
    host.innerHTML = '';
    if (CLEAN) { host.append(cv); } else {
      const box = el('div'), wrap = el('div', { class: 'stage-scale' });
      const area = $('#stageWrap'), aw = area.clientWidth - 48, ah = area.clientHeight - 48;
      const s = Math.min(aw / F.w, ah / F.h, 1);
      box.style.width = F.w * s + 'px'; box.style.height = F.h * s + 'px';
      wrap.style.width = F.w + 'px'; wrap.style.height = F.h + 'px'; wrap.style.transform = `scale(${s})`; wrap.style.transformOrigin = '0 0';
      wrap.append(cv); box.append(wrap); host.append(box);
    }
    await document.fonts.ready;
    await Promise.all([...cv.querySelectorAll('img')].map((i) => i.complete ? 0 : new Promise((r) => { i.onload = i.onerror = r; })));
    if (seq !== renderSeq) return;
    autofit(cv);
    document.body.dataset.ready = '1';
  }

  // ── экспорт PNG ──
  let fontCSS = null;
  async function toPng(scale = 1) {
    const cv = $('#canvas'), F = FORMATS[st.fmt];
    await document.fonts.ready;
    if (fontCSS === null) { try { fontCSS = await window.htmlToImage.getFontEmbedCSS(cv); } catch (e) { fontCSS = ''; } }
    return window.htmlToImage.toPng(cv, { width: F.w, height: F.h, pixelRatio: scale, fontEmbedCSS: fontCSS || undefined, cacheBust: false });
  }
  window.studioExport = toPng; // для автотестов
  function download(dataUrl, name) { const a = el('a', { href: dataUrl, download: name }); document.body.append(a); a.click(); a.remove(); }
  async function exportPng() {
    if (location.protocol === 'file:') { alert('Экспорт работает только через сайт (GitHub Pages) или локальный сервер: python3 -m http.server. Подробности — в studio/README.md'); return; }
    msg('Готовлю PNG…');
    try { const url = await toPng(+$('#scale').value || 1); download(url, `${st.tpl}_${st.fmt}.png`); msg('Готово ✓'); } catch (e) { console.error(e); msg('Ошибка экспорта: ' + (e.message || e)); }
  }
  async function exportAll() {
    const keep = st.fmt;
    for (const f of tpl().formats) { st.fmt = f; await render(); await exportPng(); await new Promise((r) => setTimeout(r, 400)); }
    st.fmt = keep; buildBar(); render();
  }

  // ── картинки: сжимаем, чтобы влезало в память браузера ──
  function readImage(file) {
    return new Promise((res, rej) => {
      const fr = new FileReader();
      fr.onerror = rej;
      fr.onload = () => {
        const src = fr.result;
        if (file.type === 'image/svg+xml' || (file.size < 250000 && file.type !== 'image/heic')) return res(src);
        const im = new Image();
        im.onload = () => {
          const k = Math.min(1, 1800 / Math.max(im.width, im.height)), c = document.createElement('canvas');
          c.width = Math.round(im.width * k); c.height = Math.round(im.height * k);
          c.getContext('2d').drawImage(im, 0, 0, c.width, c.height);
          res(file.type === 'image/png' ? c.toDataURL('image/png') : c.toDataURL('image/jpeg', 0.88));
        };
        im.onerror = rej; im.src = src;
      };
      fr.readAsDataURL(file);
    });
  }
  function pickImage(cb) {
    const i = el('input', { type: 'file', accept: 'image/*' });
    i.onchange = async () => { if (i.files[0]) cb(await readImage(i.files[0])); };
    i.click();
  }

  // ── форма ──
  function setVal(key, v, rebuildForm) {
    const id = st.tpl; st.data[id] = Object.assign(dataOf(id), { [key]: v });
    save(); render(); if (rebuildForm) buildForm();
  }
  function imageInput(val, onSet) {
    const th = el('div', { class: 'thumb' }); if (val) th.style.backgroundImage = url((window.STUDIO_ASSETS && window.STUDIO_ASSETS[val]) || val);
    return el('div', { class: 'img-in' }, th,
      el('button', { type: 'button', onclick: () => pickImage(onSet) }, val ? 'Заменить' : 'Загрузить'),
      val ? el('button', { type: 'button', class: 'btn ghost', onclick: () => onSet('') }, 'Убрать') : null);
  }
  function buildForm() {
    const t = tpl(), d = dataOf(t.id), f = $('#form');
    f.innerHTML = '';
    f.append(el('div', { class: 'fld' }, el('div', { class: 'hint' }, t.hint || '')));
    t.fields.forEach((fd) => {
      const v = d[fd.key];
      const box = el('div', { class: 'fld' }, el('label', {}, fd.label));
      if (fd.type === 'text' || fd.type === 'number') {
        box.append(el('input', { type: fd.type, value: v ?? '', oninput: (e) => setVal(fd.key, fd.type === 'number' ? +e.target.value : e.target.value) }));
      } else if (fd.type === 'textarea') {
        const ta = el('textarea', { oninput: (e) => setVal(fd.key, e.target.value) }); ta.value = v ?? ''; box.append(ta);
      } else if (fd.type === 'select') {
        const s = el('select', { onchange: (e) => setVal(fd.key, isNaN(+e.target.value) || e.target.value.startsWith('0') ? e.target.value : +e.target.value) },
          fd.options.map((o) => { const op = el('option', { value: o.v }, o.l); if (String(o.v) === String(v)) op.selected = true; return op; }));
        box.append(s);
      } else if (fd.type === 'toggle') {
        const cb = el('input', { type: 'checkbox', onchange: (e) => setVal(fd.key, e.target.checked) }); cb.checked = !!v;
        box.append(el('label', { class: 'toggle' }, cb, 'Показывать'));
      } else if (fd.type === 'image') {
        box.append(imageInput(v, (val) => setVal(fd.key, val, true)));
      } else if (fd.type === 'list') {
        const arr = clone(v || []);
        const upd = (a) => setVal(fd.key, a, true);
        arr.forEach((it, i) => {
          const row = el('div', { class: 'row' });
          fd.item.forEach((sub) => {
            if (sub.type === 'image') row.append(imageInput(it[sub.key], (val) => { arr[i][sub.key] = val; upd(arr); }));
            else row.append(el('input', { type: 'text', placeholder: sub.ph || '', value: it[sub.key] ?? '', oninput: (e) => { arr[i][sub.key] = e.target.value; setVal(fd.key, clone(arr)); } }));
          });
          const ctl = el('div', { class: 'ctl' },
            el('button', { type: 'button', class: 'btn', title: 'Выше', onclick: () => { if (i) { [arr[i - 1], arr[i]] = [arr[i], arr[i - 1]]; upd(arr); } } }, '↑'),
            el('button', { type: 'button', class: 'btn', title: 'Ниже', onclick: () => { if (i < arr.length - 1) { [arr[i + 1], arr[i]] = [arr[i], arr[i + 1]]; upd(arr); } } }, '↓'),
            el('button', { type: 'button', class: 'btn', title: 'Удалить', onclick: () => { arr.splice(i, 1); upd(arr); } }, '✕'));
          box.append(el('div', { class: 'list-item' }, el('div', { class: 'row', style: 'justify-content:space-between;margin-bottom:6px;color:#8A9099;font-size:12px' }, `#${i + 1}`, ctl), row));
        });
        if (arr.length < (fd.max || 99)) box.append(el('button', { type: 'button', class: 'btn', onclick: () => { arr.push(Object.fromEntries(fd.item.map((s) => [s.key, '']))); upd(arr); } }, '+ Добавить'));
      }
      if (fd.hint) box.append(el('div', { class: 'hint' }, fd.hint));
      f.append(box);
    });
  }
  function buildSide() {
    const curBrand = tpl().brand;
    const b = $('#brands'); b.innerHTML = '';
    window.BRANDS.forEach((br) => b.append(el('button', { class: br.id === curBrand ? 'on' : '', onclick: () => { st.tpl = T.find((t) => t.brand === br.id).id; switchTpl(); } }, br.name)));
    const l = $('#tpls'); l.innerHTML = '';
    T.filter((t) => t.brand === curBrand).forEach((t) => l.append(el('button', { class: t.id === st.tpl ? 'on' : '', onclick: () => { st.tpl = t.id; switchTpl(); } }, t.name, el('small', {}, t.formats.map((f) => f.replace('x', ':')).join(' · ').replace('a6', 'печать')))));
  }
  function buildBar() {
    const s = $('#fmt'); s.innerHTML = '';
    tpl().formats.forEach((f) => { const o = el('option', { value: f }, FORMATS[f].label); if (f === st.fmt) o.selected = true; s.append(o); });
  }
  function switchTpl() { if (!tpl().formats.includes(st.fmt)) st.fmt = tpl().formats[0]; save(); buildSide(); buildBar(); buildForm(); render(); }

  // ── пресеты ──
  function savePreset() {
    const blob = new Blob([JSON.stringify({ tpl: st.tpl, data: dataOf(st.tpl) }, null, 1)], { type: 'application/json' });
    download(URL.createObjectURL(blob), `preset_${st.tpl}.json`);
  }
  function loadPreset() {
    const i = el('input', { type: 'file', accept: 'application/json' });
    i.onchange = async () => {
      try { const p = JSON.parse(await i.files[0].text()); if (!byId[p.tpl]) throw new Error('неизвестный шаблон'); st.tpl = p.tpl; st.data[p.tpl] = p.data; switchTpl(); msg('Пресет загружен ✓'); } catch (e) { msg('Не удалось прочитать пресет: ' + e.message); }
    };
    i.click();
  }
  function reset() { if (confirm('Вернуть демо-данные для этого шаблона?')) { delete st.data[st.tpl]; switchTpl(); } }

  // ── старт ──
  function init() {
    if (CLEAN) { document.body.innerHTML = '<div id="stage"></div>'; document.body.style.background = '#000'; render(); return; }
    $('#fmt').onchange = (e) => { st.fmt = e.target.value; save(); render(); };
    $('#export').onclick = exportPng;
    $('#exportAll').onclick = exportAll;
    $('#savePreset').onclick = savePreset;
    $('#loadPreset').onclick = loadPreset;
    $('#reset').onclick = reset;
    window.addEventListener('resize', () => render());
    buildSide(); buildBar(); buildForm(); render();
  }
  init();
})();
