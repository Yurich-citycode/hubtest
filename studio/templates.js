/* ═══════════════════════════════════════════════════════════════════
   Реестр шаблонов. Каждый шаблон:
     id, brand, name, hint, formats[], fields[], defaults{}, render(d, H) → HTML
   Холст в em: 16:9 = 128×72, 1:1 = 72×72, 4:5 = 72×90, 9:16 = 72×128, A = 72×101.5
   H.fmt.key — текущий формат. H.* — помощники из app.js.
   Чтобы добавить шаблон — скопируй похожий и поменяй разметку.
   ═══════════════════════════════════════════════════════════════════ */
(function () {
  const P = 'assets/plates/';
  const EX = 'assets/examples/';
  const T = [];
  const add = (t) => T.push(t);

  // ───────────────────────── YuRichRWA: общий каркас ─────────────────────────
  const RWA_FIELDS = [
    { key: 'num', label: 'Номер выпуска', type: 'text', hint: 'Пусто — номер не показывается' },
    { key: 'date', label: 'Дата', type: 'text' },
    { key: 'sig', label: 'Подпись', type: 'text' },
    { key: 'bg', label: 'Свой фон (необязательно)', type: 'image' },
  ];
  function rwaFrame(d, H, rubric, inner) {
    const k = H.fmt.key, wide = k === '16x9';
    const pad = wide ? 6 : 5;
    return `
      <div class="plate" style="background-image:${H.url(d.bg || P + 'rwa-paper-16x9.jpg')}"></div>
      <div class="abs" style="left:${pad}em;top:${wide ? 4.6 : 4.2}em"><div class="tag"><span>${H.esc(rubric)}</span>${d.num ? `<em>№ ${H.esc(d.num)}</em>` : ''}</div></div>
      <div class="abs date" style="right:${pad + 1}em;top:${wide ? 5.4 : 5}em">${H.esc(d.date || '')}</div>
      ${inner}
      <div class="abs" style="left:${pad}em;bottom:${wide ? 4.4 : 4.2}em">${H.sig(d.sig)}</div>
      <div class="abs src chip" style="right:${pad}em;bottom:${wide ? 4.8 : 4.6}em">t.me/YuRichRWA</div>`;
  }

  // 1. RWA Early — сетка логотипов (как твои текущие обложки)
  add({
    id: 'rwa-early', story: 'box', brand: 'rwa', name: 'RWA Early · сетка проектов',
    hint: 'До 8 логотипов с подписями. Меняешь лого и имена — остальное держит шаблон.',
    formats: ['16x9', '1x1', '4x5', '9x16'],
    fields: [
      { key: 't1', label: 'Строка 1', type: 'text' },
      { key: 't2', label: 'Строка 2 (розовая)', type: 'text' },
      { key: 'sub', label: 'Подзаголовок', type: 'text' },
      { key: 'items', label: 'Проекты (до 8)', type: 'list', max: 8, item: [{ key: 'logo', type: 'image' }, { key: 'name', type: 'text', ph: 'Название' }] },
      { key: 'sig', label: 'Подпись', type: 'text' },
      { key: 'cross', label: 'Прицел справа', type: 'toggle' },
      { key: 'bg', label: 'Свой фон (необязательно)', type: 'image' },
    ],
    defaults: {
      t1: 'RWA', t2: 'Early', sub: 'Ранние проекты', sig: 'YuRichRWA', cross: true,
      items: [['index-network', 'Index Network'], ['eloscape', 'Eloscape'], ['ulys', 'Ulys'], ['treasures-finance', 'Treasures Finance'],
        ['elios', 'Elios'], ['preftrade', 'pref.trade'], ['river', 'River'], ['evolutfun', 'Evolut.fun']].map(([f, n]) => ({ logo: EX + f + '.jpg', name: n })),
    },
    render(d, H) {
      const k = H.fmt.key, items = (d.items || []).slice(0, 8), n = Math.max(items.length, 1);
      let cols = Math.min(4, n), scale = 1, top = 27.5, titleL = 6.4;
      if (k === '1x1') { top = 25; }
      if (k === '4x5') { top = 30; if (n <= 4) { cols = 2; scale = 1.45; } }
      if (k === '9x16') { cols = n <= 4 ? 2 : (n <= 6 ? 2 : 2); scale = n <= 4 ? 1.7 : 1.45; top = 33; }
      const tiles = items.map((it) => `<div class="tile"><div class="sq${it.logo ? '' : ' empty'}" style="${it.logo ? 'background-image:' + H.url(it.logo) : ''}"></div><div class="nm">${H.esc(it.name || '')}</div></div>`).join('');
      const wide = k === '16x9';
      const title = wide
        ? `<div class="abs" style="left:${titleL}em;top:4.4em"><div class="bars"><i></i><i></i><i></i></div></div>
           <div class="abs" style="left:2.4em;top:9.6em;font:400 5em Inter;color:#111">+</div>
           <div class="abs" style="left:${titleL}em;top:6.8em"><div class="disp t1">${H.esc(d.t1)}</div></div>
           <div class="abs" style="left:${titleL + 1.4}em;top:15.2em"><div class="disp t2">${H.esc(d.t2)}</div></div>
           <div class="abs" style="left:${titleL + 1.8}em;top:24.4em;width:30em">${H.swoosh('#FF1F8F', 30)}</div>
           <div class="abs sub" style="left:${titleL + 0.6}em;top:25.6em">${H.esc(d.sub)}</div>`
        : `<div class="abs" style="left:5em;top:4em"><div class="bars"><i></i><i></i><i></i></div></div>
           <div class="abs" style="left:5em;top:6.6em;display:flex;align-items:flex-end;gap:2.4em"><div class="disp t1" style="font-size:9.6em">${H.esc(d.t1)}</div><div class="disp t2" style="font-size:9em">${H.esc(d.t2)}</div></div>
           <div class="abs sub" style="left:5.4em;top:${k === '1x1' ? 17.6 : 18.4}em">${H.esc(d.sub)}</div>`;
      const sigPos = wide ? 'left:21em;bottom:4.4em' : 'left:5em;bottom:4.4em';
      return `
        <div class="plate" style="background-image:${H.url(d.bg || P + 'rwa-paper-16x9.jpg')}"></div>
        ${title}
        ${d.cross ? `<div class="abs" style="right:${wide ? 9 : 3}em;top:${wide ? 3.4 : 14.5}em;width:${wide ? 17 : 9}em;height:${wide ? 17 : 9}em">${H.crosshair('#D7FF3D')}</div>` : ''}
        ${wide ? `<div class="abs" style="left:57em;top:3.6em;width:22em;height:6em">${H.dots('#111', 22, 6)}</div>` : ''}
        <div class="abs" style="left:0;right:0;top:${top}em;display:flex;justify-content:center">
          <div class="tiles" style="font-size:${scale}em;grid-template-columns:repeat(${cols},13.4em)">${tiles}</div>
        </div>
        <div class="abs" style="${sigPos}">${H.sig(d.sig)}</div>
        ${wide ? '<div class="abs" style="left:3em;bottom:2.2em"><div class="hatch"><i></i><i></i><i></i><i></i><i></i></div></div>' : ''}`;
    },
  });

  // 2. Жёлтое / Розовое — фирменный разбор: что существует vs что работает
  add({
    id: 'rwa-split', story: 'box', brand: 'rwa', name: 'Жёлтое / Розовое · разбор проекта',
    hint: 'Твой метод из «Цифровых городов»: жёлтое существует, розовое работает.',
    formats: ['16x9', '1x1', '4x5', '9x16'],
    fields: [
      { key: 'title', label: 'Заголовок', type: 'textarea', hint: '*слово* — выделить розовым' },
      { key: 'y', label: 'Жёлтое — существует', type: 'textarea' },
      { key: 'p', label: 'Розовое — работает', type: 'textarea' },
      ...RWA_FIELDS,
    ],
    defaults: { num: '07', date: 'Октябрь 2026', sig: 'YuRichRWA', title: 'Токен есть.\n*Права* нет.',
      y: 'Сайт, рендер, токен в кошельке, цифра эмиссии, пресс-релиз.', p: 'Право записано, деньги дошли, касса платит, кто-то отвечает в суде.' },
    render(d, H) {
      const k = H.fmt.key, wide = k === '16x9';
      const titleBox = wide ? 'left:6em;top:12.5em;width:116em;height:17em' : `left:5em;top:11.5em;width:62em;height:${k === '1x1' ? 16 : 22}em`;
      const cards = wide
        ? `<div class="abs card yellow" style="left:6em;top:32em;width:55em;height:22em;transform:rotate(-1deg)"><h4>Жёлтое</h4><p>${H.rich(d.y)}</p></div>
           <div class="abs card pink" style="left:66em;top:32em;width:55em;height:22em;transform:rotate(1deg)"><h4>Розовое</h4><p>${H.rich(d.p)}</p></div>`
        : (() => { const t1 = k === '1x1' ? 29 : (k === '4x5' ? 36 : 42), h = k === '1x1' ? 15 : (k === '4x5' ? 19 : 25), g = h + 3;
          return `<div class="abs card yellow fit" style="left:5em;top:${t1}em;width:62em;height:${h}em;transform:rotate(-1deg)"><h4>Жёлтое</h4><p>${H.rich(d.y)}</p></div>
                  <div class="abs card pink fit" style="left:5em;top:${t1 + g}em;width:62em;height:${h}em;transform:rotate(1deg)"><h4>Розовое</h4><p>${H.rich(d.p)}</p></div>`; })();
      return rwaFrame(d, H, 'Жёлтое / Розовое', `
        <div class="abs fit" style="${titleBox}"><div class="disp title" style="font-size:${wide ? 7.2 : 6.6}em">${H.rich(d.title)}</div></div>
        ${cards}`);
    },
  });

  // 3. Механика сделки: Актив → Право → Деньги
  add({
    id: 'rwa-mech', story: 'box', brand: 'rwa', name: 'Механика · как устроена сделка',
    hint: 'Три шага: что за актив, какое право получает держатель, откуда деньги.',
    formats: ['16x9', '1x1', '4x5', '9x16'],
    fields: [
      { key: 'title', label: 'Заголовок', type: 'textarea', hint: '*слово* — розовым' },
      { key: 's1h', label: 'Шаг 1 — заголовок', type: 'text' }, { key: 's1', label: 'Шаг 1 — текст', type: 'textarea' },
      { key: 's2h', label: 'Шаг 2 — заголовок', type: 'text' }, { key: 's2', label: 'Шаг 2 — текст', type: 'textarea' },
      { key: 's3h', label: 'Шаг 3 — заголовок', type: 'text' }, { key: 's3', label: 'Шаг 3 — текст', type: 'textarea' },
      ...RWA_FIELDS,
    ],
    defaults: { num: '03', date: 'Октябрь 2026', sig: 'YuRichRWA', title: 'Что покупает\n*держатель* ЦФА',
      s1h: 'Актив', s1: 'Доля выручки кофейни за 12 месяцев', s2h: 'Право', s2: 'Денежное требование по решению о выпуске', s3h: 'Деньги', s3: 'Выплата раз в квартал из кассы точки' },
    render(d, H) {
      const k = H.fmt.key, wide = k === '16x9';
      const st = (i) => `<div class="st"><b>0${i}</b><h5>${H.esc(d['s' + i + 'h'])}</h5><p>${H.rich(d['s' + i])}</p></div>`;
      const chain = wide
        ? `<div class="abs chain" style="left:6em;right:6em;top:33em">${st(1)}<div class="arr">→</div>${st(2)}<div class="arr">→</div>${st(3)}</div>`
        : `<div class="abs chain" style="left:5em;right:5em;top:${k === '1x1' ? 25.5 : 33}em;flex-direction:column;align-items:stretch;gap:${k === '1x1' ? 1 : 2}em;font-size:${k === '1x1' ? 0.7 : 1}em">${st(1)}${st(2)}${st(3)}</div>`;
      return rwaFrame(d, H, 'Механика', `
        <div class="abs fit" style="${wide ? 'left:6em;top:12.5em;width:116em;height:18em' : 'left:5em;top:11.5em;width:62em;height:14em'}"><div class="disp title" style="font-size:${wide ? 7.4 : 6}em">${H.rich(d.title)}</div></div>
        ${chain}`);
    },
  });

  // 4. Цифра недели
  add({
    id: 'rwa-number', story: 'box', brand: 'rwa', name: 'Цифра недели',
    hint: 'Одна цифра рынка и две строки, почему она важна.',
    formats: ['16x9', '1x1', '4x5', '9x16'],
    fields: [
      { key: 'n', label: 'Цифра', type: 'text' },
      { key: 'unit', label: 'Подпись к цифре', type: 'text' },
      { key: 'title', label: 'Что это значит', type: 'textarea', hint: '*слово* — розовым' },
      { key: 'source', label: 'Источник', type: 'text' },
      ...RWA_FIELDS,
    ],
    defaults: { num: '12', date: 'Неделя 43 · 2026', sig: 'YuRichRWA', n: '$34', unit: 'млрд — RWA ончейн без стейблов', title: 'Рынок вырос.\n*Права* держателя — нет.', source: 'Источник: rwa.xyz' },
    render(d, H) {
      const k = H.fmt.key, wide = k === '16x9';
      return rwaFrame(d, H, 'Цифра недели', wide ? `
        <div class="abs fit" style="left:5em;top:12em;width:64em;height:30em;display:flex;align-items:flex-end"><div class="bignum" style="font-size:26em">${H.esc(d.n)}</div></div>
        <div class="abs" style="left:6.4em;top:44em;width:60em"><div class="lead" style="font-weight:800">${H.esc(d.unit)}</div></div>
        <div class="abs fit" style="left:72em;top:17em;width:50em;height:26em"><div class="disp title" style="font-size:6em">${H.rich(d.title)}</div></div>
        <div class="abs src" style="left:72em;top:47em">${H.esc(d.source)}</div>`
        : `
        <div class="abs fit" style="left:4em;top:12em;width:64em;height:${k === '1x1' ? 22 : 30}em;display:flex;align-items:flex-end"><div class="bignum" style="font-size:24em">${H.esc(d.n)}</div></div>
        <div class="abs" style="left:5.4em;top:${k === '1x1' ? 35 : 44}em;width:60em"><div class="lead" style="font-weight:800">${H.esc(d.unit)}</div></div>
        <div class="abs fit" style="left:5em;top:${k === '1x1' ? 41 : 52}em;width:62em;height:${k === '1x1' ? 15 : 24}em"><div class="disp title" style="font-size:5.6em">${H.rich(d.title)}</div></div>
        <div class="abs src" style="left:5.4em;top:${k === '1x1' ? 57.5 : (k === '4x5' ? 78 : 80)}em">${H.esc(d.source)}</div>`);
    },
  });

  // 5. RWA-радар — дайджест недели
  add({
    id: 'rwa-digest', story: 'box', brand: 'rwa', name: 'RWA-радар · дайджест',
    hint: 'Три–пять новостей недели. Сюда падает поток из TG и X после проверки.',
    formats: ['16x9', '1x1', '4x5', '9x16'],
    fields: [
      { key: 'title', label: 'Заголовок', type: 'text' },
      { key: 'lead', label: 'Подводка (только 16:9)', type: 'textarea', hint: '*слово* — розовым' },
      { key: 'items', label: 'Новости (до 5)', type: 'list', max: 5, item: [{ key: 't', type: 'text', ph: 'Что произошло' }, { key: 's', type: 'text', ph: 'Источник' }] },
      ...RWA_FIELDS,
    ],
    defaults: { num: '43', date: '19–25 окт 2026', sig: 'YuRichRWA', title: 'RWA за неделю', lead: 'Отбираю из TG и X.\nТолько то, что *меняет право* или деньги.',
      items: [{ t: 'Новый оператор ЦФА вошёл в реестр Банка России', s: 'cbr.ru' }, { t: 'Токенизированные трежерис перевалили новый рекорд', s: 'rwa.xyz' }, { t: 'Банк выпустил ЦФА на долю выручки сети кофеен', s: 'Telegram' }, { t: 'RWA Foundation: итоги хакатона', s: 'X' }] },
    render(d, H) {
      const k = H.fmt.key, wide = k === '16x9';
      const items = (d.items || []).slice(0, 5).map((it, i) => `<div class="it"><div class="n">${i + 1}</div><div class="tx">${H.esc(it.t)}<small>${H.esc(it.s || '')}</small></div></div>`).join('');
      return rwaFrame(d, H, 'RWA-радар', wide ? `
        <div class="abs" style="left:6em;top:12.5em;width:40em"><div class="disp title" style="font-size:7em">${H.rich(d.title)}</div></div>
        <div class="abs" style="left:6.4em;top:27em;width:34em">${H.swoosh('#FF1F8F', 30)}</div>
        <div class="abs" style="left:6.4em;top:33em;width:38em"><div class="lead">${H.rich(d.lead)}</div></div>
        <div class="abs digest fit" style="left:50em;top:12em;width:72em;height:46em">${items}</div>`
        : `
        <div class="abs" style="left:5em;top:11.5em;width:62em"><div class="disp title" style="font-size:6.4em">${H.rich(d.title)}</div></div>
        <div class="abs digest fit" style="left:5em;top:${k === '1x1' ? 20 : 22}em;width:62em;height:${k === '1x1' ? 39 : (k === '4x5' ? 56 : 92)}em">${items}</div>`);
    },
  });

  // 6. Универсальная обложка (статья, разбор проекта, лонгрид)
  add({
    id: 'rwa-cover', story: 'box', brand: 'rwa', name: 'Обложка-универсал · статья / разбор',
    hint: 'Заголовок, одна мысль и картинка проекта на скотче.',
    formats: ['16x9', '1x1', '4x5', '9x16'],
    fields: [
      { key: 'rubric', label: 'Рубрика', type: 'text' },
      { key: 'title', label: 'Заголовок', type: 'textarea', hint: '*слово* — розовым' },
      { key: 'lead', label: 'Одна мысль', type: 'textarea' },
      { key: 'pic', label: 'Картинка / логотип проекта', type: 'image' },
      ...RWA_FIELDS,
    ],
    defaults: { rubric: 'Разбор', num: '', date: 'Октябрь 2026', sig: 'YuRichRWA', title: 'Токен\nсработал.\n*Отопление* — нет.', lead: 'Изучил 45+ цифровых городов. Главный урок не про блокчейн, а про то, кто отвечает, когда реальный мир ломается.', pic: EX + 'river.jpg' },
    render(d, H) {
      const k = H.fmt.key, wide = k === '16x9';
      const pic = d.pic ? (wide
        ? `<div class="abs" style="left:84em;top:14em;width:34em;height:34em;transform:rotate(3deg);background:#111 center/cover no-repeat;background-image:${H.url(d.pic)};box-shadow:1em 1em 0 rgba(0,0,0,.2)"></div><div class="tape" style="left:96em;top:12.6em"></div>`
        : `<div class="abs" style="right:6em;top:${k === '1x1' ? 40 : 52}em;width:22em;height:22em;transform:rotate(4deg);background:#111 center/cover no-repeat;background-image:${H.url(d.pic)};box-shadow:.8em .8em 0 rgba(0,0,0,.2)"></div><div class="tape" style="right:12em;top:${k === '1x1' ? 39 : 51}em"></div>`) : '';
      const tw = d.pic && wide ? 74 : (wide ? 116 : 62);
      return rwaFrame(d, H, d.rubric || 'YuRichRWA', `
        <div class="abs fit" style="left:${wide ? 6 : 5}em;top:${wide ? 12.5 : 11.5}em;width:${tw}em;height:${wide ? 30 : (k === '1x1' ? 26 : 36)}em"><div class="disp title" style="font-size:${wide ? 8 : 7}em">${H.rich(d.title)}</div></div>
        <div class="abs fit" style="left:${wide ? 6.4 : 5.4}em;top:${wide ? 45 : (k === '1x1' ? 39 : 50)}em;width:${wide ? 70 : (d.pic ? 36 : 60)}em;height:${wide ? 11 : (k === '1x1' ? 15 : 24)}em"><div class="lead">${H.rich(d.lead)}</div></div>
        ${pic}`);
    },
  });

  // ───────────────────────── City Code ─────────────────────────
  const KEYS = {
    '01': { name: 'Code', c: '#F3F1EA', t: '#0B0D12' }, '02': { name: 'Privileges', c: '#1E2F7A', t: '#D7FF3D' },
    '03': { name: 'Partner Circle', c: '#D7FF3D', t: '#0B0D12' }, '04': { name: 'Events', c: '#2A2D33', t: '#D7FF3D' },
    '05': { name: 'Insights', c: '#2B4FD9', t: '#F3F1EA' }, '06': { name: 'Member Circle', c: '#FF5B23', t: '#0B0D12' },
  };
  const keyOpts = Object.entries(KEYS).map(([n, k]) => ({ v: n, l: `${n} · ${k.name}` }));
  const keyPill = (n) => { const k = KEYS[n] || KEYS['03']; return `<span class="key" style="background:${k.c};color:${k.t}"><i style="background:${k.t}"></i>${n} · ${k.name}</span>`; };
  const ccWM = () => '<div class="wm"><div class="dots"><i></i><i></i><i></i><i></i><i></i><i></i></div>CITY CODE</div>';
  const ccFoot = (l, r) => `<div class="foot"><span>${l}</span><span><b>${r}</b></span></div>`;
  const ccPlate = (d, H) => `<div class="plate" style="background-image:${H.url(d.bg || P + 'citycode-night-16x9.jpg')}"></div>`;
  const mosaicItems = (H) => ((H.shared('cc-mosaic') || {}).items || []);

  // 7. Мозаика партнёров в буквах C
  add({
    id: 'cc-mosaic', story: 'box', brand: 'cc', name: 'Partner Circle · мозаика в буквах C',
    hint: 'Здесь живёт список партнёров. Каждый новый — ячейка в «C». Карточка партнёра берёт логотипы отсюда.',
    formats: ['16x9', '1x1', '4x5', '9x16'],
    fields: [
      { key: 'title', label: 'Заголовок', type: 'textarea', hint: '*слово* — лаймом' },
      { key: 'perC', label: 'Ячеек в каждой C', type: 'select', options: [6, 8, 10, 12].map((v) => ({ v, l: String(v) })) },
      { key: 'rings', label: 'Колец', type: 'select', options: [{ v: 1, l: '1 кольцо' }, { v: 2, l: '2 кольца' }] },
      { key: 'items', label: 'Партнёры по порядку подключения', type: 'list', max: 24, item: [{ key: 'logo', type: 'image' }, { key: 'name', type: 'text', ph: 'Название' }] },
      { key: 'note', label: 'Подпись внизу', type: 'text' },
      { key: 'bg', label: 'Свой фон', type: 'image' },
    ],
    defaults: { title: 'Первые *20 мест*\nв логотипе', perC: 10, rings: 2, note: 'Ячейка — статус партнёра. Не продаётся.',
      items: [['instinct', 'Instinct'], ['transmuter', 'Transmuter'], ['silhouette', 'Silhouette'], ['if-market', 'If Market'], ['vauban', 'Vauban'], ['fystack', 'Fystack'], ['opendex', 'OpenDEX']].map(([f, n]) => ({ logo: EX + f + '.jpg', name: n })) },
    render(d, H) {
      const k = H.fmt.key, wide = k === '16x9';
      const total = (+d.perC || 10) * 2, items = (d.items || []).slice(0, total), filled = items.length;
      const svg = H.mosaic({ perC: +d.perC || 10, rings: +d.rings || 2, items });
      const names = items.map((it, i) => `<b>${String(i + 1).padStart(2, '0')}</b> ${H.esc(it.name || '')}`).join(' &nbsp;·&nbsp; ');
      if (wide) return `${ccPlate(d, H)}
        <div class="abs" style="left:6em;top:5em">${ccWM()}</div>
        <div class="abs" style="left:6em;top:13em">${keyPill('03')}</div>
        <div class="abs fit" style="left:6em;top:19.5em;width:44em;height:16em"><div class="h" style="font-size:4.6em">${H.rich(d.title)}</div></div>
        <div class="abs count" style="left:6em;top:37em">${filled} / ${total}<small>мест занято</small></div>
        <div class="abs names fit" style="left:6em;top:49em;width:42em;height:9em">${names}</div>
        <div class="abs" style="left:50em;top:7em;width:74em;height:52em">${svg}</div>
        <div class="abs" style="left:6em;right:6em;bottom:3.6em">${ccFoot('Севастополь · закрытый круг', H.esc(d.note))}</div>`;
      const mt = k === '1x1' ? 20.5 : (k === '4x5' ? 25 : 34), mh = k === '1x1' ? 30 : 34;
      return `${ccPlate(d, H)}
        <div class="abs" style="left:5em;top:4.4em">${ccWM()}</div>
        <div class="abs" style="right:5em;top:4em">${keyPill('03')}</div>
        <div class="abs fit" style="left:5em;top:10.5em;width:62em;height:${k === '1x1' ? 9 : 12}em"><div class="h" style="font-size:4.4em">${H.rich(d.title)}</div></div>
        <div class="abs" style="left:4em;right:4em;top:${mt}em;height:${mh}em">${svg}</div>
        <div class="abs count" style="left:5em;top:${mt + mh + 2}em">${filled} / ${total}<small>мест занято</small></div>
        ${k === '1x1' ? '' : `<div class="abs names fit" style="left:5em;top:${mt + mh + 13}em;width:62em;height:${k === '4x5' ? 9 : 40}em">${names}</div>`}
        <div class="abs" style="left:5em;right:5em;bottom:3.4em">${ccFoot('Закрытый круг', H.esc(d.note))}</div>`;
    },
  });

  // 8. Новый партнёр
  add({
    id: 'cc-partner', story: 'box', brand: 'cc', name: 'Новый партнёр · карточка',
    hint: 'Лого, привилегия, условия, номер ячейки. Остальные ячейки берутся из «мозаики».',
    formats: ['16x9', '1x1', '4x5', '9x16'],
    fields: [
      { key: 'logo', label: 'Логотип партнёра', type: 'image' },
      { key: 'name', label: 'Название', type: 'text' },
      { key: 'cat', label: 'Категория · район', type: 'text' },
      { key: 'priv', label: 'Привилегия', type: 'text', hint: 'v1.0: 3–7%' },
      { key: 'cond', label: 'Условия', type: 'textarea' },
      { key: 'addr', label: 'Адрес', type: 'text' },
      { key: 'cell', label: 'Номер ячейки', type: 'number' },
      { key: 'bg', label: 'Свой фон', type: 'image' },
    ],
    defaults: { logo: EX + 'opendex.jpg', name: 'Кофейня «Пример»', cat: 'Кофе · Центр', priv: '−5%', cond: 'Будни 8:00–16:00. На напитки и выпечку. Показать City Passport.', addr: 'ул. Большая Морская, 1', cell: 8 },
    render(d, H) {
      const k = H.fmt.key, wide = k === '16x9';
      const base = mosaicItems(H).slice();
      const cell = Math.max(1, +d.cell || 1);
      while (base.length < cell - 1) base.push({ name: '' });
      base[cell - 1] = { logo: d.logo, name: d.name };
      const perC = +((H.shared('cc-mosaic') || {}).perC) || 10;
      const items = base.slice(0, cell);
      const svg = H.mosaic({ perC, rings: +((H.shared('cc-mosaic') || {}).rings) || 2, items, highlight: cell - 1 });
      const total = perC * 2;
      if (wide) return `${ccPlate(d, H)}
        <div class="abs" style="left:6em;top:5em">${ccWM()}</div>
        <div class="abs kick" style="left:6em;top:14em">Новый партнёр</div>
        <div class="abs fit" style="left:6em;top:18em;width:60em;height:17em"><div class="h">${H.rich(d.name)}</div></div>
        <div class="abs meta" style="left:6em;top:36em">${H.esc(d.cat)}</div>
        <div class="abs priv" style="left:6em;top:41em"><div class="pc">${H.esc(d.priv)}</div><div class="cond">${H.rich(d.cond)}</div></div>
        <div class="abs meta" style="left:6em;top:58.4em;font-size:1.8em">${H.esc(d.addr)}</div>
        <div class="abs" style="left:68em;top:6em;width:56em;height:44em">${svg}</div>
        <div class="abs" style="left:68em;top:52em">${keyPill('03')}</div>
        <div class="abs count" style="left:100em;top:50.6em;font-size:1em"><span style="font:900 4em Unbounded">${String(cell).padStart(2, '0')}</span><span style="font:700 2em Unbounded;color:var(--dim)"> / ${total}</span></div>
        <div class="abs" style="left:6em;right:6em;bottom:3.6em">${ccFoot('Partner Circle · Севастополь', 'Привилегия — по City Passport')}</div>`;
      const mt = k === '1x1' ? 38 : (k === '4x5' ? 52 : 70);
      return `${ccPlate(d, H)}
        <div class="abs" style="left:5em;top:4.4em">${ccWM()}</div>
        <div class="abs kick" style="left:5em;top:11.5em">Новый партнёр · ячейка ${String(cell).padStart(2, '0')} / ${total}</div>
        <div class="abs fit" style="left:5em;top:15em;width:62em;height:${k === '1x1' ? 12 : 16}em"><div class="h" style="font-size:6.4em">${H.rich(d.name)}</div></div>
        <div class="abs meta" style="left:5em;top:${k === '1x1' ? 28 : 32}em">${H.esc(d.cat)} · ${H.esc(d.addr)}</div>
        <div class="abs priv" style="left:5em;top:${k === '1x1' ? 33 : 38}em;flex-direction:column;align-items:flex-start;gap:.6em"><div class="pc" style="font-size:${k === '1x1' ? 7 : 9}em">${H.esc(d.priv)}</div><div class="cond" style="max-width:${k === '1x1' ? 14 : 30}em">${H.rich(d.cond)}</div></div>
        <div class="abs" style="left:${k === '1x1' ? 30 : 4}em;right:4em;top:${mt}em;height:${k === '1x1' ? 24 : 32}em">${svg}</div>
        <div class="abs" style="left:5em;right:5em;bottom:3.4em">${ccFoot('Partner Circle', 'По City Passport')}</div>`;
    },
  });

  // 9. Событие City Code
  add({
    id: 'cc-event', brand: 'cc', name: 'Событие · закрытая встреча',
    hint: 'Фото, дата, место, количество мест.',
    formats: ['16x9', '1x1', '4x5', '9x16'],
    fields: [
      { key: 'photo', label: 'Фото', type: 'image' },
      { key: 'title', label: 'Название', type: 'textarea', hint: '*слово* — лаймом' },
      { key: 'date', label: 'Дата', type: 'text' },
      { key: 'time', label: 'Время', type: 'text' },
      { key: 'place', label: 'Место', type: 'text' },
      { key: 'seats', label: 'Мест', type: 'text' },
      { key: 'who', label: 'Кто может прийти', type: 'text' },
    ],
    defaults: { photo: EX + 'sample-event.jpg', title: 'Ужин\n*Partner Circle*', date: '14 ноября', time: '19:30', place: 'Терраса партнёра · Центр', seats: '24', who: 'Только участники City Code' },
    render(d, H) {
      const k = H.fmt.key, wide = k === '16x9';
      const ph = H.url(d.photo || P + 'citycode-night-16x9.jpg');
      if (wide) return `<div class="plate" style="background:#0B0D12"></div>
        <div class="abs photo" style="left:60em;top:0;right:0;bottom:0;background-image:${ph}"></div>
        <div class="abs" style="left:56em;top:0;width:16em;bottom:0;background:linear-gradient(90deg,#0B0D12,rgba(11,13,18,0))"></div>
        <div class="abs" style="left:6em;top:5em">${ccWM()}</div>
        <div class="abs" style="left:6em;top:13em">${keyPill('04')}</div>
        <div class="abs fit" style="left:6em;top:19em;width:56em;height:17em"><div class="h" style="font-size:6.6em">${H.rich(d.title)}</div></div>
        <div class="abs" style="left:6em;top:38em;font:900 5.2em Unbounded;color:var(--lime)">${H.esc(d.date)}</div>
        <div class="abs meta" style="left:6em;top:46.5em"><b>${H.esc(d.time)}</b> · ${H.esc(d.place)}<br>Мест: <b>${H.esc(d.seats)}</b> · ${H.esc(d.who)}</div>
        <div class="abs" style="left:6em;width:50em;bottom:3.6em">${ccFoot('Закрытый круг', 'Запись в чате Events')}</div>`;
      const ht = k === '1x1' ? 34 : (k === '4x5' ? 44 : 64);
      return `<div class="plate" style="background:#0B0D12"></div>
        <div class="abs photo" style="left:0;right:0;top:0;height:${ht + 4}em;background-image:${ph}"></div>
        <div class="abs" style="left:0;right:0;top:${ht - 14}em;height:18em;background:linear-gradient(180deg,rgba(11,13,18,0),#0B0D12)"></div>
        <div class="abs" style="left:5em;top:4.4em">${ccWM()}</div>
        <div class="abs" style="left:5em;top:${ht - 5}em">${keyPill('04')}</div>
        <div class="abs fit" style="left:5em;top:${ht + 1}em;width:62em;height:${k === '1x1' ? 12 : 16}em"><div class="h" style="font-size:5.6em">${H.rich(d.title)}</div></div>
        <div class="abs" style="left:5em;top:${ht + (k === '1x1' ? 14 : 19)}em;font:900 4.4em Unbounded;color:var(--lime)">${H.esc(d.date)} · ${H.esc(d.time)}</div>
        <div class="abs meta" style="left:5em;top:${ht + (k === '1x1' ? 20.5 : 26)}em;width:62em">${H.esc(d.place)} · Мест: <b>${H.esc(d.seats)}</b><br>${H.esc(d.who)}</div>
        <div class="abs" style="left:5em;right:5em;bottom:3.4em">${ccFoot('Закрытый круг', 'Запись в Events')}</div>`;
    },
  });

  // 10. Объявление по ветке (6 ключей)
  add({
    id: 'cc-key', story: 'box', brand: 'cc', name: 'Объявление · одна из 6 веток',
    hint: 'Code, Privileges, Partner Circle, Events, Insights, Member Circle — у каждой свой цвет ключа.',
    formats: ['16x9', '1x1', '4x5', '9x16'],
    fields: [
      { key: 'key', label: 'Ветка', type: 'select', options: keyOpts },
      { key: 'title', label: 'Заголовок', type: 'textarea', hint: '*слово* — лаймом' },
      { key: 'body', label: 'Текст', type: 'textarea' },
      { key: 'bg', label: 'Свой фон', type: 'image' },
    ],
    defaults: { key: '01', title: 'Правило\n*№ 1*', body: 'Привилегия действует только по City Passport и только в дни, которые выбрал партнёр. Спор с персоналом = выход из круга.' },
    render(d, H) {
      const k = H.fmt.key, wide = k === '16x9';
      return `${ccPlate(d, H)}
        <div class="abs bignum" style="right:${wide ? 2 : -2}em;top:${wide ? 8 : 14}em">${H.esc(d.key)}</div>
        <div class="abs" style="left:${wide ? 6 : 5}em;top:${wide ? 5 : 4.4}em">${ccWM()}</div>
        <div class="abs" style="left:${wide ? 6 : 5}em;top:${wide ? 14 : 12}em">${keyPill(d.key)}</div>
        <div class="abs fit" style="left:${wide ? 6 : 5}em;top:${wide ? 21 : 19}em;width:${wide ? 74 : 62}em;height:${wide ? 18 : 18}em"><div class="h">${H.rich(d.title)}</div></div>
        <div class="abs fit" style="left:${wide ? 6 : 5}em;top:${wide ? 41 : 40}em;width:${wide ? 70 : 62}em;height:${wide ? 14 : (k === '1x1' ? 20 : 34)}em"><div class="body">${H.rich(d.body)}</div></div>
        <div class="abs" style="left:${wide ? 6 : 5}em;right:${wide ? 6 : 5}em;bottom:${wide ? 3.6 : 3.4}em">${ccFoot('Севастополь · закрытый круг', 'City Code v1.0')}</div>`;
    },
  });

  // ───────────────────────── Sevastopol AI ─────────────────────────
  const BOT = 'https://t.me/SevastopolAIBot';
  const saiLogo = (H) => `<div class="logo"><img src="assets/logos/sevastopol-ai.jpg" alt=""><span>Sevastopol AI</span></div>`;
  const pin = '<svg viewBox="0 0 24 24" fill="none" stroke="#E6C878" stroke-width="2"><path d="M12 22s7-6.2 7-12a7 7 0 1 0-14 0c0 5.8 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/></svg>';
  const clock = '<svg viewBox="0 0 24 24" fill="none" stroke="#E6C878" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>';
  const deep = (src) => BOT + (src ? '?start=src_' + String(src).replace(/[^a-zA-Z0-9_]/g, '') : '');

  // 11. Карточка места
  add({
    id: 'sai-place', brand: 'sai', name: 'Карточка места',
    hint: 'Фото, название, адрес, часы. QR ведёт в бота с меткой — видно, откуда пришли.',
    formats: ['16x9', '1x1', '4x5', '9x16'],
    fields: [
      { key: 'photo', label: 'Фото места', type: 'image' },
      { key: 'cat', label: 'Категория', type: 'text' },
      { key: 'name', label: 'Название', type: 'textarea', hint: '*слово* — золотым курсивом' },
      { key: 'desc', label: 'Описание (1–2 фразы)', type: 'textarea' },
      { key: 'addr', label: 'Адрес · район', type: 'text' },
      { key: 'hours', label: 'Часы', type: 'text' },
      { key: 'partner', label: 'Партнёр City Code', type: 'toggle' },
      { key: 'src', label: 'Метка для QR (латиница)', type: 'text', hint: 'Пример: post_kofe1 → t.me/SevastopolAIBot?start=src_post_kofe1' },
    ],
    defaults: { photo: EX + 'sample-coffee.jpg', cat: 'Кофе · спешелти', name: 'Кофейня\n*у моря*', desc: 'Свой обжар, тихий двор и лучшие круассаны в Центре. Утром — без очереди.', addr: 'ул. Большая Морская, 1 · Центр', hours: 'Ежедневно 8:00–21:00', partner: true, src: 'card_demo' },
    render(d, H) {
      const k = H.fmt.key, wide = k === '16x9';
      const ph = H.url(d.photo || P + 'sevastopol-navy-16x9.jpg');
      const qr = H.qr(deep(d.src));
      if (wide) return `<div class="plate" style="background-image:${H.url(P + 'sevastopol-navy-16x9.jpg')}"></div>
        <div class="abs photo" style="left:0;top:0;width:62em;height:72em;background-image:${ph}"></div>
        <div class="frame" style="left:3em;top:3em;width:56em;height:66em"></div>
        ${d.partner ? '<div class="abs badge" style="left:5.4em;top:5.4em">Партнёр City Code</div>' : ''}
        <div class="abs" style="left:67em;top:5em">${saiLogo(H)}</div>
        <div class="abs cat" style="left:67em;top:16em">${H.esc(d.cat)}</div>
        <div class="abs fit" style="left:67em;top:19.5em;width:56em;height:18em"><div class="nm">${H.rich(d.name)}</div></div>
        <div class="abs fit" style="left:67em;top:39em;width:54em;height:9.6em"><div class="desc">${H.rich(d.desc)}</div></div>
        <div class="abs" style="left:67em;top:50em;width:40em;display:flex;flex-direction:column;gap:1em"><div class="row">${pin}<span>${H.esc(d.addr)}</span></div><div class="row">${clock}<span>${H.esc(d.hours)}</span></div></div>
        <div class="abs qr" style="right:5em;bottom:5em;width:12em;height:12em">${qr}</div>
        <div class="abs cta" style="left:67em;bottom:5.4em">Найти в боте →</div>`;
      const ht = k === '1x1' ? 30 : (k === '4x5' ? 42 : 62);
      return `<div class="plate" style="background-image:${H.url(P + 'sevastopol-navy-16x9.jpg')}"></div>
        <div class="abs photo" style="left:0;right:0;top:0;height:${ht + 6}em;background-image:${ph}"></div>
        <div class="abs" style="left:0;right:0;top:${ht - 12}em;height:18em;background:linear-gradient(180deg,rgba(9,17,31,0),#09111F)"></div>
        <div class="abs" style="left:0;right:0;top:0;height:14em;background:linear-gradient(180deg,rgba(9,17,31,.75),rgba(9,17,31,0))"></div>
        <div class="abs" style="left:4em;top:4em">${saiLogo(H)}</div>
        ${d.partner ? `<div class="abs badge" style="right:4em;top:5.2em">Партнёр City Code</div>` : ''}
        <div class="abs cat" style="left:5em;top:${ht}em">${H.esc(d.cat)}</div>
        <div class="abs fit" style="left:5em;top:${ht + 3}em;width:62em;height:${k === '1x1' ? 12 : 16}em"><div class="nm" style="font-size:6.8em">${H.rich(d.name)}</div></div>
        <div class="abs fit" style="left:5em;top:${ht + (k === '1x1' ? 16 : 20)}em;width:${k === '1x1' ? 46 : 62}em;height:${k === '1x1' ? 8 : 10}em"><div class="desc">${H.rich(d.desc)}</div></div>
        <div class="abs" style="left:5em;bottom:${k === '1x1' ? 5 : 6}em;width:44em;display:flex;flex-direction:column;gap:.8em"><div class="row">${pin}<span>${H.esc(d.addr)}</span></div><div class="row">${clock}<span>${H.esc(d.hours)}</span></div></div>
        <div class="abs qr" style="right:4.4em;bottom:4.4em;width:${k === '1x1' ? 12 : 14}em;height:${k === '1x1' ? 12 : 14}em">${qr}</div>`;
    },
  });

  // 12. Событие в городе
  add({
    id: 'sai-event', brand: 'sai', name: 'Событие в городе · афиша',
    hint: 'Большая дата, название, место, цена. Для канала и бота.',
    formats: ['16x9', '1x1', '4x5', '9x16'],
    fields: [
      { key: 'photo', label: 'Фото / афиша', type: 'image' },
      { key: 'day', label: 'Число', type: 'text' }, { key: 'mon', label: 'Месяц · день недели', type: 'text' },
      { key: 'cat', label: 'Категория', type: 'text' },
      { key: 'title', label: 'Название', type: 'textarea', hint: '*слово* — золотым курсивом' },
      { key: 'place', label: 'Место', type: 'text' }, { key: 'price', label: 'Цена', type: 'text' },
    ],
    defaults: { photo: EX + 'sample-sea.jpg', day: '08', mon: 'Ноября · суббота', cat: 'Концерт', title: 'Ундервуд\n*у моря*', place: 'Дворец культуры рыбаков', price: 'от 1 500 ₽' },
    render(d, H) {
      const k = H.fmt.key, wide = k === '16x9';
      const ph = H.url(d.photo || P + 'sevastopol-navy-16x9.jpg');
      if (wide) return `<div class="plate photo" style="background-image:${ph}"></div><div class="shade"></div>
        <div class="abs" style="left:6em;top:5em">${saiLogo(H)}</div>
        <div class="abs day" style="left:5.4em;top:14em">${H.esc(d.day)}</div>
        <div class="abs mon" style="left:6em;top:31.6em">${H.esc(d.mon)}</div>
        <div class="abs cat" style="left:6em;top:37.6em">${H.esc(d.cat)}</div>
        <div class="abs fit" style="left:6em;top:40.5em;width:60em;height:15em"><div class="nm">${H.rich(d.title)}</div></div>
        <div class="abs" style="left:6em;top:57em;display:flex;gap:3em"><div class="row">${pin}<span>${H.esc(d.place)}</span></div><div class="row" style="color:var(--gold2)">${H.esc(d.price)}</div></div>
        <div class="abs cta" style="right:6em;bottom:5em">Билеты — в боте</div>`;
      return `<div class="plate photo" style="background-image:${ph}"></div><div class="shade v"></div>
        <div class="abs" style="left:4em;top:4em">${saiLogo(H)}</div>
        <div class="abs" style="left:5em;bottom:${k === '1x1' ? 21 : 26}em;display:flex;align-items:flex-end;gap:1.6em"><div class="day" style="font-size:${k === '1x1' ? 13 : 16}em">${H.esc(d.day)}</div><div style="padding-bottom:1.6em"><div class="mon">${H.esc(d.mon)}</div><div class="cat" style="margin-top:.6em">${H.esc(d.cat)}</div></div></div>
        <div class="abs fit" style="left:5em;bottom:${k === '1x1' ? 9 : 12}em;width:62em;height:${k === '1x1' ? 11 : 14}em;display:flex;align-items:flex-end"><div class="nm" style="font-size:6.4em">${H.rich(d.title)}</div></div>
        <div class="abs" style="left:5em;right:5em;bottom:4.4em;display:flex;justify-content:space-between"><div class="row">${pin}<span>${H.esc(d.place)}</span></div><div class="row" style="color:var(--gold2)">${H.esc(d.price)}</div></div>`;
    },
  });

  // 13. Новость города
  add({
    id: 'sai-news', brand: 'sai', name: 'Новость города',
    hint: 'Фото + заголовок. Для канала Sevastopol AI и дубля новостей.',
    formats: ['16x9', '1x1', '4x5', '9x16'],
    fields: [
      { key: 'photo', label: 'Фото', type: 'image' },
      { key: 'tag', label: 'Плашка', type: 'text' },
      { key: 'title', label: 'Заголовок', type: 'textarea', hint: '*слово* — золотым курсивом' },
      { key: 'date', label: 'Дата', type: 'text' }, { key: 'source', label: 'Источник', type: 'text' },
    ],
    defaults: { photo: EX + 'sample-sea.jpg', tag: 'Новости города', title: 'На Приморском бульваре\nоткрыли *новую набережную*', date: '25 октября', source: 'по данным правительства Севастополя' },
    render(d, H) {
      const k = H.fmt.key, wide = k === '16x9';
      const ph = H.url(d.photo || P + 'sevastopol-navy-16x9.jpg');
      return `<div class="plate photo" style="background-image:${ph}"></div><div class="shade v"></div>
        <div class="abs" style="left:${wide ? 6 : 4}em;top:${wide ? 5 : 4}em">${saiLogo(H)}</div>
        <div class="abs badge" style="left:${wide ? 6 : 5}em;bottom:${wide ? 25 : (k === '1x1' ? 25 : 30)}em">${H.esc(d.tag)}</div>
        <div class="abs fit" style="left:${wide ? 6 : 5}em;bottom:${wide ? 9 : 9}em;width:${wide ? 100 : 62}em;height:${wide ? 14.5 : (k === '1x1' ? 14.5 : 19)}em;display:flex;align-items:flex-end"><div class="nm" style="font-size:${wide ? 6.6 : 6}em">${H.rich(d.title)}</div></div>
        <div class="abs foot" style="left:${wide ? 6 : 5}em;right:${wide ? 6 : 5}em;bottom:${wide ? 4.4 : 4}em"><span>${H.esc(d.date)} · ${H.esc(d.source)}</span><span><b>@Sevastopol_AI</b></span></div>`;
    },
  });

  // 14. QR-стойка для заведения (офлайн)
  add({
    id: 'sai-qr', brand: 'sai', name: 'QR-стойка для заведения · печать',
    hint: 'Тейбл-тент / наклейка на кассу. У каждой точки своя метка — считаем, откуда пришли люди.',
    formats: ['a6', '4x5', '1x1'],
    fields: [
      { key: 'h1', label: 'Вопрос', type: 'textarea' },
      { key: 'h2', label: 'Ответ', type: 'text' },
      { key: 'venue', label: 'Название точки', type: 'text', hint: 'Пусто — универсальная стойка' },
      { key: 'partner', label: 'Партнёр City Code', type: 'toggle' },
      { key: 'src', label: 'Метка точки (латиница)', type: 'text' },
      { key: 'b1', label: 'Пункт 1', type: 'text' }, { key: 'b2', label: 'Пункт 2', type: 'text' }, { key: 'b3', label: 'Пункт 3', type: 'text' },
    ],
    defaults: { h1: 'Где поесть?\nГде *закат*?\nКуда сходить?', h2: 'Спроси Sevastopol AI', venue: 'Кофейня у моря', partner: true, src: 'qr_kofe_u_morya', b1: 'Еда, места, маршруты — с фото и картой', b2: 'Маршруты, пляжи, закаты', b3: 'События города каждый день' },
    render(d, H) {
      const k = H.fmt.key;
      // раскладка по форматам: [вопрос top, высота, ответ top, QR top, QR size, пункты top | null]
      const L = { a6: [13, 21, 36, 40.5, 31, 75.5], '4x5': [12, 18, 31.5, 35.5, 27, 66], '1x1': [10.5, 13, 24.6, 28, 25, null] }[k];
      const [hT, hH, aT, qT, qS, bT] = L;
      const buls = [d.b1, d.b2, d.b3].filter(Boolean);
      return `<div class="plate" style="background-image:${H.url(P + 'sevastopol-navy-16x9.jpg')};background-position:92% center"></div>
        <div class="abs" style="inset:0;background:radial-gradient(ellipse at 50% 45%,rgba(9,17,31,.82) 0%,rgba(9,17,31,.55) 55%,rgba(9,17,31,.25) 100%)"></div>
        <div class="abs" style="left:0;right:0;top:${k === '1x1' ? 3.4 : 4.6}em;display:flex;justify-content:center">${saiLogo(H)}</div>
        <div class="abs fit" style="left:5em;right:5em;top:${hT}em;height:${hH}em;text-align:center"><div class="nm" style="font-size:${k === '1x1' ? 4.6 : 6}em">${H.rich(d.h1)}</div></div>
        <div class="abs cat" style="left:0;right:0;top:${aT}em;text-align:center;font-size:${k === '1x1' ? 1.6 : 1.9}em">${H.esc(d.h2)}</div>
        <div class="abs qr" style="left:calc(50% - ${qS / 2}em);top:${qT}em;width:${qS}em;height:${qS}em">${H.qr(deep(d.src))}</div>
        ${bT && buls.length ? `<div class="abs" style="left:0;right:0;top:${bT}em;display:flex;justify-content:center"><div class="bul" style="font-size:${k === 'a6' ? 1 : 0.9}em">${buls.map((b) => `<div><i></i>${H.esc(b)}</div>`).join('')}</div></div>` : ''}
        ${d.venue ? `<div class="abs" style="left:0;right:0;bottom:${k === '1x1' ? 3.6 : 8.4}em;display:flex;justify-content:center;align-items:center;gap:1.4em"><div class="desc" style="font-size:${k === '1x1' ? 1.6 : 1.8}em;color:var(--ink)">Вы в «${H.esc(d.venue)}»</div>${d.partner ? '<div class="badge">Партнёр City Code</div>' : ''}</div>` : ''}
        ${k === '1x1' ? '' : `<div class="abs foot" style="left:5em;right:5em;bottom:3.6em"><span>Бесплатно · в Telegram</span><span><b>@SevastopolAiBot</b></span></div>`}`;
    },
  });

  window.TEMPLATES = T;
  window.BRANDS = [
    { id: 'rwa', name: 'YuRichRWA' },
    { id: 'cc', name: 'City Code' },
    { id: 'sai', name: 'Sevastopol AI' },
  ];
})();
