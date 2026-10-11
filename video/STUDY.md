# Разбор пяти репозиториев

Проверено 11 октября 2026 через GitHub API и npm. Звёзды — на сегодня, у тебя в посте были близкие
числа (59,5K / 62,7K / 94K / 78,8K / 44,6K), с тех пор счётчики немного уехали.

| Репозиторий | ⭐ сегодня | Лицензия | Язык | Роль в нашей студии |
| --- | --- | --- | --- | --- |
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | 60 765 | Apache-2.0 | TypeScript | основной движок: HTML → MP4 |
| [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | 63 234 | своя (не OSS) | TypeScript | второй движок: видео на React |
| [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) | 94 657 | MIT | JavaScript | вкус к интерфейсам и графике, анти-слоп |
| [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | 79 787 | Apache-2.0 | JavaScript | аудит и полировка дизайна, 24 команды |
| [emilkowalski/skills](https://github.com/emilkowalski/skills) | 45 280 | MIT | Markdown | движение и UI-детали: что и как анимировать |

Итого у нас в `video/skills/` лежит 62 скилла из этих пяти наборов, с лицензиями рядом.

---

## 1. HyperFrames — «пиши HTML, получай видео»

**Что это.** Открытый фреймворк HeyGen: HTML-страница становится детерминированным MP4. Композиция —
это HTML-файл, где тайминг объявлен `data-*`-атрибутами (`data-start`, `data-duration`,
`data-track-index`), анимация — GSAP-таймлайн, зарегистрированный как `window.__timelines[id]`.
Рендер: headless Chrome (покадрово) + FFmpeg.

**Что подтвердилось на практике.**

- Ставится из npm: `npm i hyperframes` (v0.8.147), CLI богатый: `render`, `preview` (студия-редактор),
  `lint`, `check` (lint + runtime + layout + контраст), `snapshot`, `beats`, `transcribe`, `catalog`.
- Уважает переменные окружения `HYPERFRAMES_BROWSER_PATH`, `HYPERFRAMES_FFMPEG_PATH`,
  `HYPERFRAMES_FFPROBE_PATH` — благодаря этому работает в закрытой песочнице с нашим Chromium и FFmpeg.
- В команде нет `ffmpeg` и браузера — HyperFrames сам их не тащит; в обычной системе ставятся
  `apt install ffmpeg` и `npx hyperframes browser`, у нас — через npm (см. README).
- Рендер: 12 с в 1920×1080@30 — 33 секунды на двух ядрах (software GL, покадровые скриншоты).
  Формат капчур-режима в отчёте: `screenshot capture · software gpu` — это медленный, но рабочий путь.
- `check` реально строгий: нашёл перекрытия глитч-слоёв и вылет текста из маски. Лечится
  `data-layout-allow-overlap` (на сам текстовый блок, не на обёртку) и запасом внутри маски.
  После правок: `0 errors`, контраст `54/54 WCAG AA`.
- Батч: `--batch rows.json -o "renders/{output}"` — один рендер на строку. Проверено, три видео за минуту.
- 21 скилл: роутер `hyperframes`, домены (`-core`, `-animation`, `-keyframes`, `-creative`, `-audio`,
  `-cli`, `-registry`, `-studio`, `media-use`) и воркфлоу (`product-launch-video`, `faceless-explainer`,
  `motion-graphics`, `embedded-captions`, `talking-head-recut`, `music-to-video`, `slideshow`,
  `pr-to-video`, `general-video`, `remotion-to-hyperframes`, `figma`).

**Что взяли.** Все 21 скилл + лицензию. Движок — из npm, в `video/node_modules`.

**Наши ограничения.** Никаких CDN и внешних API внутри композиции: рендер должен работать офлайн.
Всё, что нужно кадру, лежит в `projects/<name>/assets`.

## 2. Remotion — видео на React

**Что это.** Тот же принцип «код → кадр», но источник истины — React-компонент, а рендер идёт через
свой бандлер + Chrome + FFmpeg. Сильная сторона — вычисления: данные, карты, покадровая логика,
переиспользуемые компоненты, миллионы рендеров на своём железе.

**Что подтвердилось.**

- `npx remotion render` в этой песочнице работает: браузер подставляется флагом
  `--browser-executable=/tmp/chromium` (наша npm-сборка). FFmpeg Remotion находит сам —
  его npm-пакеты тянут статические бинарники, доступ к ним через `--browser-executable` не нужен.
- Версия 4.0.534; в репозитории 12 пользовательских скиллов (`remotion-create`,
  `remotion-best-practices`, `remotion-render`, `remotion-captions`, `remotion-multimedia`,
  `remotion-interactivity`, `remotion-maps`, `remotion-markup`, `remotion-saas`, `remotion-studio`,
  `remotion-docs`, `remotion-upgrade`). Скиллы лежат в `packages/skills/skills`, а в `.agents/skills`
  на них сделаны симлинки — качали первое.

**Важно про лицензию.** Remotion — не open source в строгом смысле: лицензия своя, для компаний
размером больше порога нужна платная. Для канала и небольших проектов всё свободно, но если
масштабировать рендер-ферму на «миллионы видео», сначала читать `LICENSE.md`. Поэтому основной
движок у нас HyperFrames (Apache-2.0), а Remotion — инструмент второго выбора.

**Что взяли.** 12 скиллов + лицензию. Рабочий проект — `video/frameworks/remotion`
(React 19, TypeScript, конфиг) с примером `TitleOutro` в каноне бренда.

## 3. Taste Skill — «вкус» для фронтенда

**Что это.** Набор агентных скиллов, который не даёт агенту скатиться в шаблонный SaaS-вид:
читает бриф, выводит дизайн-язык, крутит три ручки (`VARIANCE` / `MOTION` / `DENSITY`),
требует канонический GSAP-код и запрещает типовые штампы.

**Что внутри.** 13 скиллов: v2-по-умолчанию (`design-taste-frontend`) и v1 для пиновки,
`gpt-taste` для Codex, `image-to-code`, `redesign-existing-projects`, `high-end-visual-design`,
`minimalist-ui`, `industrial-brutalist-ui`, `stitch-design-taste`, `full-output-enforcement`,
`imagegen-frontend-web/-mobile`, `brandkit`.

**Полезное для нас.** Раздел про GSAP-скелеты и правила гигиены (только `transform`/`opacity`,
секвенции на таймлайне, никаких «дёрганых» кривых) — прямо про наши видео и страницы.
`image-to-code` и `brandkit` пригодятся, когда будем делать картинки-референсы для видео.

**Осторожно.** У репозитория в README есть дисклеймер: официального токена у проекта нет,
всё, что использует имя автора в крипте, — не связано с ним. Мы просто читаем скиллы.
Не ставить в промпты «сделай в стиле taste-skill» как бренд: стиль у нас Юры, вкус — оттуда.

## 4. Impeccable — дизайн-ревизия и полировка

**Что это.** Одна скилл-команда `/impeccable` с 24 подкомандами (`craft`, `shape`, `critique`,
`audit`, `polish`, `bolder`, `quieter`, `distill`, `animate`, `colorize`, `typeset`, `layout`,
`harden`, `onboard`, `delight`, `overdrive`, `clarify`, `adapt`, `optimize`, `live`, `generate`…)
и 59 детерминированных правил-детекторов «следов ИИ» в вёрстке: Inter на всё, фиолетово-синие
градиенты, карточки в карточках, серый текст на цветном фоне, скруглённый квадрат над заголовком.

**Что внутри и как ставится.** Скилл в репозитории — это `SKILL.md` и `reference/*.md` (мы взяли
именно их). Полный CLI `npx impeccable install` тянет платформенный бинарь движка через
optional-зависимости npm (`@impeccable/cli-linux-x64` и другие) — в нашей песочнице доступен,
но для него нужен харнесс агента (`.claude`, `.codex`, `.cursor`), поэтому в репозиторий мы его
не кладём: ставится по месту, когда понадобится живой аудит в браузере.

**Как используем.** Для нас это ревизор: перед публикацией страницы/видео-графики прогоняем
мысленно чек-лист и команду `audit` по тексту скилла. Плюс полезный словарь: «сделай тише»,
«усиль», «доведи до сути» — теперь у нас есть общий язык с агентом.

## 5. Skills Эмиля Ковальски — движение и детали

**Что это.** 15 коротких скиллов от инженера, который работал в Vercel и Linear. Не про «красиво»,
а про правильные мелочи: `ease-out` на вход, полупрозрачная тень вместо бордера, длина анимации,
жест на телефоне, что анимировать не надо.

**Что внутри.** `emil-design-eng`, `animate`, `animate-expo`, `review-animations`,
`improve-animations`, `find-animation-opportunities`, `animation-performance`, `animation-vocabulary`,
`apple-design`, `pick-ui-library`, `prototype`, `mobile-native`, `break-ui`, `ask-sonner`, `write-swift`.

**Как используем.** Это наш рецензент движения: `animate` — когда строим новую анимацию,
`review-animations` — когда проверяем готовую, `animation-performance` — когда кадры падают.
Словарь (`animation-vocabulary`) помогает формулировать правки: не «сделай плавнее», а
«пружина с damping побольше», «ease-out 200 мс», «вход по y, без скейла».

---

## Что из этого сделано руками

1. **Окружение.** `video/setup.sh` + `bin/provision.mjs` ставят Chromium, FFmpeg, FFprobe и GSAP
   из npm и пишут `video/.runtime/env.json`. Проблема, которую это решает: в песочнице нет apt
   и закрыты Google CDN и релизы GitHub.
2. **Скиллы.** 62 скилла вендорены в `video/skills/<набор>/` с лицензиями и таблицей коммитов.
3. **Интро** (`projects/yurichhub-intro`) — три сцены, вайпы, глитч, карточки модулей, подвал.
   Длительность 12 с, 1920×1080@30. Прошло `check` без замечаний.
4. **Вертикальный шаблон** (`projects/social-post-vertical`) — 1080×1920, переменные и батч,
   автоподбор кегля заголовка, самособирающиеся карточки. Отрендерены три поста серией.
5. **Remotion-полоса** (`frameworks/remotion`) — рабочий проект с титрами в каноне: если
   понадобится логика React, всё готово.

## Что можно делать дальше (по скиллам HyperFrames)

| Задача | Воркфлоу | Что нужно от нас |
| --- | --- | --- |
| Разбор PR из этого репозитория | `pr-to-video` | ссылка на PR, `gh` уже настроен |
| Видео-презентация сайта хаба | `product-launch-video` | URL страницы, 30–90 с |
| Объяснялка концепции RWA | `faceless-explainer` | текст, 30–90 с |
| Вертикальные посты серией | наш `social-post-vertical` | JSON с текстами |
| Моушн-графика: цифра, тезис | `motion-graphics` | число и подпись, до 10 с |
| Субтитры и нарезка подкаста | `embedded-captions`, `talking-head-recut` | исходное видео |
| Питч-дека со слайдами | `slideshow` | тема и структура |
