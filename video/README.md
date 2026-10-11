# Видео-студия YurichHub

Здесь делаются видео для YurichHub: интро, вертикальные посты, разборы, анонсы. Всё в каноне
бренда (`brand/YURICHHUB-STYLE.md`), всё рендерится локально, без облаков и без интернета в момент рендера.

Разбор пяти репозиториев, из которых собрана студия, — в [STUDY.md](STUDY.md).

## Что внутри

```
video/
├── setup.sh              установка одной командой (npm + Chromium + FFmpeg + GSAP)
├── bin/                  provision, doctor, env.sh, обёртка hf.sh
├── skills/               вендоренные скиллы 5 репозиториев (см. skills/README.md)
├── projects/             композиции: HTML, шрифты, ассеты проекта
│   ├── yurichhub-intro/        интро 1920×1080, 12 с, три сцены
│   ├── site-tour/              тур по сайту 1920×1080, 50 с, пять глав
│   └── social-post-vertical/   вертикаль 1080×1920, 8 с, шаблон с переменными и батчем
├── frameworks/remotion/  второй движок: видео на React (Remotion)
├── captures/             кадры сайта для композиций (промежуточный артефакт)
├── vendor/               gsap.min.js — локально, без CDN
└── renders/              готовые MP4
```

## Два движка

| Движок | Когда брать | Команда |
| --- | --- | --- |
| **HyperFrames** (основной) | видео из HTML/CSS: постеры, титры, объяснялки, вертикальные серии, интерфейсные шоукейсы. Обязательные `data-*`-атрибуты, GSAP, детерминированный рендер | `bash bin/hf.sh render projects/<name>` |
| **Remotion** (второй) | когда нужна логика React: данные, карты, интерактив, покадровая математика, переиспользование компонентов | `cd frameworks/remotion && bash bin/remotion.sh render src/index.ts TitleOutro out/out.mp4` |

Оба движка проверены в этой песочнице: рендер MP4 реально работает.

## Быстрый старт

```bash
cd video
bash setup.sh        # один раз: поставит всё и напишет .runtime/env.json
npm run doctor       # проверит, что Chromium, FFmpeg, GSAP и скиллы на месте
```

Дальше — по проекту:

```bash
# проверки и кадры для глаз
bash bin/hf.sh lint      projects/yurichhub-intro
bash bin/hf.sh check     projects/yurichhub-intro     # lint + runtime + layout + контраст
bash bin/hf.sh snapshot  projects/yurichhub-intro --at 1.6,3.9,10.2

# рендер
bash bin/hf.sh render projects/yurichhub-intro -o renders/yurichhub-intro-1080p.mp4 --fps 30 --quality looks

# превью-студия (кликабельный редактор) — слушает 127.0.0.1:3002
bash bin/hf.sh preview projects/yurichhub-intro --port 3002 --foreground --no-open
```

### Живое превью в браузере

`hyperframes preview` слушает только `127.0.0.1`, а браузеру нужен адрес на `0.0.0.0`. Поэтому
студия выставляется наружу маленьким прокси (он же прокидывает WebSocket-обновления кадра):

```bash
# в одном процессе — студия, в другом — прокси
node bin/preview-proxy.mjs --port 3100 --target 3002
```

Порт `3100` показывается как живое превью, внутри всё работает как обычно: правки в HTML
перезагружаются сами, а таймлайн можно крутить мышью.

Внутри самих проектов можно короче: `cd projects/yurichhub-intro && npx hyperframes render .` —
но тогда окружение надо поднимать руками (`source ../../bin/env.sh`).

## Шаблон с переменными: вертикальные посты серией

`projects/social-post-vertical` — фабрика: один HTML, а тексты приходят из JSON. Так делаются
серии постов (ЦФА, RWA, курс), где меняются цифры и подписи, а каркас остаётся брендовым.

```bash
# один пост с другими текстами
bash bin/hf.sh render projects/social-post-vertical -o renders/out.mp4 \
  --variables '{"title":"НЕ|ТОКЕН","subtitle":"СБОРКА ВЫПУСКА ЦФА","stat1v":"80 000","stat1l":"РАЗБОР, РУБ.","stat1c":"#E8377E"}'

# серия: один рендер на каждую строку batch-файла
bash bin/hf.sh render projects/social-post-vertical \
  --batch projects/social-post-vertical/batch.example.json \
  --batch-concurrency 2 -o "renders/batch/{output}"
```

Вертикальный заголовок: разделитель `|` даёт вторую строку лаймом (`"СНАЧАЛА|АКТИВ"`).
Кегль подбирается по фактической ширине, поэтому длинный текст не вылезает за поле.
Пустое значение цифры убирает карточку из сетки.

## Тур по сайту: как снимаются кадры страниц

Ролик `projects/site-tour` собран из реальных кадров сайта-хаба. Порядок такой:

```bash
# 1. локальная копия страниц со вшитыми шрифтами канона (Anton — латиница, Oswald — кириллица)
node bin/prepare-site-copy.mjs                 # копия в /tmp/yurichhub-site

# 2. поднять копию
cd /tmp/yurichhub-site && python3 -m http.server 8099 --bind 127.0.0.1

# 3. снять секции в 1920×1080 (сайт на скролл-сценах, поэтому снимаем вьюпорт после прокрутки)
node bin/capture-sections.mjs \
  --url http://127.0.0.1:8099/index.html \
  --out captures/site-index/sections \
  --sections top,sevastopol,citycode,rwa,course,cfa

# 4. кадры раздела лежат в captures/, композиция читает их из projects/site-tour/assets/shots
```

`hyperframes capture` тоже работает и даёт больше (полная страница, токены, анимации, контактные
листы), но режет секции по краям — для чистовых кадров удобнее точечная съёмка элементов.

## Что уже отрендерено

| Файл | Что это |
| --- | --- |
| `renders/yurichhub-intro-1080p.mp4` | Интро 12 с: знак, «Открыть. Войти. Владеть.» с карточками модулей, формула и вход в канал |
| `renders/site-tour-1080p.mp4` | Тур по сайту 50 с: главная, Sevastopol AI, City Code, Crimea RWA, курс, ЦФА, финал |
| `renders/site-tour-1080p-web.mp4` | То же для веба: CRF 21, без звука, 11 МБ вместо 45 МБ |
| `renders/batch/cfa-ne-token.mp4` | Вертикальный пост: ЦФА, «Не токен», 80 000 / 0 / 259-ФЗ |
| `renders/batch/rwa-snachala-aktiv.mp4` | Вертикальный пост: Crimea RWA, «Сначала | актив», А/Б/В |
| `renders/batch/course-bez-signalov.mp4` | Вертикальный пост: курс, «Без | сигналов», шесть модулей |

Скорость в песочнице: 12 с в 1080p30 — около 33 с, 50 с в 1080p30 (двумя воркерами) — около 2,5 минут,
вертикаль 8 с — около 25 с.

## Находки и заметки

Смотри [NOTES.md](NOTES.md). Там же — деталь про русские заголовки сайта: Anton без кириллицы,
и кириллицу сейчас рисует системный шрифт вместо Oswald по канону.

## Как это устроено в песочнице

Песочница закрыта: нет `apt`, недоступны Google CDN (откуда Puppeteer качает Chrome) и релизы
GitHub (откуда Remotion качает FFmpeg). Доступны npm и github.com. Поэтому:

- **Chromium** — npm-пакет `@sparticuz/chromium`; системные `libnspr4`/`libnss3` лежат в нём же
  (`bin/al2023.tar.br`) и распаковываются в `/tmp/yurichhub-video/lib`, путь отдаётся через `LD_LIBRARY_PATH`
- **FFmpeg и FFprobe** — npm-пакеты `@ffmpeg-installer` / `@ffprobe-installer`
- **GSAP** — вендорится из `node_modules` в `vendor/gsap.min.js`; композиции не ходят в интернет
- **Шрифты** — только локальные файлы канона из `brand/covers/fonts`, копируются в `projects/*/assets/fonts`

Всё это поднимает `bash setup.sh`, пишет в `video/.runtime/env.json`, а `bin/env.sh` подставляет
переменные (`HYPERFRAMES_BROWSER_PATH`, `HYPERFRAMES_FFMPEG_PATH`, `HYPERFRAMES_FFPROBE_PATH`,
`LD_LIBRARY_PATH`) на время команды. В `git` из этого не попадает ничего: `.runtime/`, `node_modules/`
и `snapshots/` в `.gitignore`.

## Правила, которые не нарушаем

1. **Канон важнее красоты.** Цвета, шрифты, обводка `2.8%`, глитч `+6/+5` розовый при `0.7` и
   `−6/−4` лаймовый при `0.5`, два свечения по `0.05`, зерно `0.07`, поля `84` на 1920 —
   всё из `brand/YURICHHUB-STYLE.md`. Новый «свой» стиль на видео не придумываем.
2. **Только transform и opacity.** Никаких анимаций `width`, `top`, `margin`: движение не должно
   дёргаться. Кривые — ease-out, без отскока (скилл `emil/animate`).
3. **Никаких внешних CDN** в композиции: рендер должен работать офлайн и через год.
4. **Скиллы апстримов не редактируем.** Правки — в `NOTES.md` или в своих проектах.
5. **Лицензии уважаем.** HyperFrames и Impeccable — Apache-2.0, Taste Skill и Эмиль — MIT,
   Remotion — своя лицензия (см. STUDY.md): перед коммерческим использованием на большом
   масштабе читать `frameworks/remotion/` условия, для обычного ролика канала всё свободно.
