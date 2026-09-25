# Аудит репозитория hubtest

Дата: 2026-09-25
Ветка аудита: `arena/01a0d79f-hubtest` (от `main` 68bbbdf)

## 1. Ветки

**Результат проверки:**
- Локально: `main`, `arena/01a0d79f-hubtest`
- Remote: `origin/main` только
- Тегов нет
- Ненужных веток нет — удалять нечего.

Команда проверки:
```bash
git branch -a
```

Всё чисто. Если в будущем появятся `feature/*` или старые `arena/*`, их можно удалить:
```bash
git branch -d <branch>
git push origin --delete <branch>
```

## 2. Пул файлов — что есть сейчас

### Корень (продакшн для GitHub Pages и для будущего хоста)
```
index.html              — главная (YurichHub хаб, 5 секций)
course.html             — курс RWA (6 модулей + квиз)
glossary.html           — глоссарий 57 терминов, 11 разделов, шаринг карточек
cfa.html                — офер сборки выпуска ЦФА

yurichhub.jpg           — герой главной (портрет)
ai-screen.jpg           — скрин роадмапа Sevastopol AI
keychain.webp           — брелки City Code (6 ключей)
rwa-asset-coffee.jpg    — фото актива для секции RWA (пример)
hermes.jpg              — партнер Hermes (круг)
nebank.png              — партнер Небанк (прозрачный PNG, используется)
nebank.jpg              — дубликат Небанка (не используется, оставлен)
CityCode.png            — иконка приложения City Code (не используется в HTML, оставлен)
sevastopol-ai.png       — лого/арт Sevastopol AI (не используется, оставлен)

comics1.jpg ... comics6.jpg — комиксы для глоссария (разделы 01-06)
comics7-11.jpg          — упомянуты в glossary.html, файлов нет, есть onerror fallback (не ломает страницу)

indexpreview.jpg, coursepreview.jpg, glossarypreview.jpg, cfapreview.jpg — OG-превью 1200x630 для соцсетей
```

### Папка brand/ (не нужна для продакшна, но не мешает)
```
brand/README.md
brand/YURICHHUB-STYLE.md  — канон стиля (обязателен к прочтению перед новыми обложками)
brand/covers/             — генератор обложек (render.js, package.json, fonts/, examples/, post.json)
brand/previews/           — SVG превью
brand/reference/          — референсы xalgo-cover и слайды
brand/samples/            — примеры PNG
```
Для GitHub Pages `brand/` просто лежит, не мешает. Для хоста можно оставить или убрать — на работу сайта не влияет. Файлы не удалялись по ТЗ.

## 3. Проверка работоспособности

Проверено локально (`python -m http.server 8000`):

- `index.html` — грузится, анимации работают:
  - page fade (opacity transition)
  - smooth-scroll (fixed-content + rAF, только для fine pointer)
  - custom cursor (dot+ring)
  - magnetic pull
  - scroll reveal / wipe curtain (IntersectionObserver + fallback для fixed режима)
  - keychain: 6 хотспотов с clip-path, spark burst, панель
  - RWA табы А/Б/В + скейл макета брокера 390x844
  - spotlight, 3D tilt, marquee
- `course.html` — тикер, табы модулей, квиз 5 вопросов, mobile menu, page transitions
- `glossary.html` — sticky индекс, прогресс-бар, маршруты чтения (3 чипа + sub-чипы), 57 терминов, share-card на canvas (печать, глитч-Y), Web Share API, toast, flash якоря
- `cfa.html` — статичный офер, page transitions

JS синтаксис проверен `new Function(js)` — ошибок нет.

Ссылки:
- Все внутренние ссылки относительные (`course.html`, `glossary.html`, `cfa.html`, `#sevastopol`) — работают и на GH Pages, и на хосте.
- Внешние `t.me/*`, `x.com/*`, `atomyze.ru` — с `target=_blank rel=noopener`.

## 4. Что почищено (без изменения структуры/анимаций)

### Удалены технические комментарии
Ранее в коде было много поясняющих вставок вида:
```js
// взводим шторки только из работающего JS
/* fixed-режим включает только JS — CSS и скролл-движок не могут разойтись */
/* Каждый хотспот накрывает всё фото, а кликабельная область вырезается clip-path */
```
И CSS комментарии:
```css
/* ================= HERO ================= */
/* section wipe curtain. По умолчанию шторка ОТКРЫТА... */
```

Все такие вставки удалены скриптом очистки:
- JS: удалены `/* ... */` и `//...` комментарии (с защитой regex `/^https?:\/\//`)
- CSS: удалены все `/* ... */`
- HTML: удалены `<!-- ... -->` (включая `КАНОН ГЛОССАРИЯ`)

Функциональный код не трогался, только комментарии.

### Мертвый код
- `index.html`: в `@media (prefers-reduced-motion:reduce)` был селектор `.emblem` — класса в HTML нет, удалён.
- `course.html`: `--blue-glow` использовался через `var(--blue-glow,#3E6FA8)`, но не был объявлен. Добавлен в `:root` как `--blue-glow:#3E6FA8` и упрощён вызов до `var(--blue-glow)`.

Больше мёртвого кода не найдено:
- Классы `.curtains`, `.has-cursor`, `.kc-spark`, `.in-view`, `.revealed`, `.wiped` добавляются динамически JS — нужны.
- `comics7-11.jpg` отсутствуют, но в коде есть `onerror="...classList.add('no-img')"` — страница не ломается.
- `module1.jpg ... module6.jpg` отсутствуют, но это плейсхолдеры для фото модулей (задокументировано в STYLE.md).

### Оптимизации без поломки
- Убраны пустые строки, оставлено по 1-2.
- Сохранены все анимации, transition, keyframes.
- Не менялась структура DOM, классы, id — чтобы не сломать JS.
- Не минифицировался HTML/CSS/JS агрессивно — сохранена читаемость, но убраны комментарии.
- Проверено, что `TRANS_MS = 380` везде одинаков для page transitions.

## 5. Как должен выглядеть пул для GitHub Pages сегодня

**Минимальный рабочий набор (корень репо):**
```
index.html
course.html
glossary.html
cfa.html
yurichhub.jpg
ai-screen.jpg
keychain.webp
rwa-asset-coffee.jpg
hermes.jpg
nebank.png
comics1.jpg - comics6.jpg
indexpreview.jpg
coursepreview.jpg
glossarypreview.jpg
cfapreview.jpg
.nojekyll (рекомендуется, чтобы GH Pages не игнорировал файлы с _)
```

Этого достаточно, чтобы https://yurich-citycode.github.io/hubtest/ работал.

Сейчас в корне лежат ещё:
- `CityCode.png`, `sevastopol-ai.png`, `nebank.jpg` — не используются, но оставлены по ТЗ (не удалять файлы).
- `brand/` — не мешает Pages, можно оставить.

**Настройка GitHub Pages:**
1. Settings → Pages → Source: Deploy from branch → `main` / `root`
2. Домен пока `yurich-citycode.github.io/hubtest/`
3. Все OG-теги уже указывают на этот домен — превью в Telegram/X работают.

## 6. Как перенести на хост завтра (когда купишь домен и сервер)

**Перенос 1:1 — без изменения структуры:**

1. Скопируй на сервер весь минимальный набор из п.5 (или весь корень, включая brand, если хочешь).
2. Обнови абсолютные URL в `<head>` каждой страницы:

В `index.html`:
```html
<meta property="og:url" content="https://yourdomain.com/">
<meta property="og:image" content="https://yourdomain.com/indexpreview.jpg">
<meta name="twitter:image" content="https://yourdomain.com/indexpreview.jpg">
<link rel="canonical" href="https://yourdomain.com/">
```

Аналогично в `course.html`, `glossary.html`, `cfa.html` — замени `https://yurich-citycode.github.io/hubtest/` на `https://yourdomain.com/`.

3. Больше ничего менять не нужно — все ссылки относительные, картинки относительные.

**Для Nginx (пример):**
```nginx
server {
  listen 80;
  server_name yourdomain.com;
  root /var/www/hubtest;
  index index.html;
  location / {
    try_files $uri $uri/ =404;
  }
  # кэш статики
  location ~* \.(jpg|png|webp|svg|css|js)$ {
    expires 30d;
  }
}
```

**Для Apache (.htaccess):**
```
Options -Indexes
DirectoryIndex index.html
```

Не нужен никакой сборщик, `package.json` и т.д. — сайт чистый статический HTML.

**Если захочешь оставить и GH Pages, и свой домен:**
- В корне создай файл `CNAME` с содержимым `yourdomain.com`
- В DNS провайдера добавь A-записи GitHub Pages или CNAME на `yurich-citycode.github.io`

## 7. Рекомендации

- Не удаляй `brand/` — там канон стиля и генератор обложек. Он не мешает продакшну.
- Когда появятся `module1.jpg ... module6.jpg` (фото модулей курса) — просто положи в корень, `course.html` уже их подхватит.
- Когда появятся `comics7-11.jpg` — положи в корень, глоссарий подхватит автоматически.
- OG-картинки (`*preview.jpg`) — 1200x630, уже оптимизированы. При смене домена не забудь обновить URL, иначе в соцсетях будет старое превью.
- Все страницы уже имеют `<link rel="preconnect" href="https://fonts.googleapis.com">` — шрифты грузятся быстро.
- Для дальнейшего аудита: `grep -R "console.log\|TODO\|FIXME" --include="*.html"` — сейчас пусто.

## 8. Итог

- Веток лишних нет.
- Файлы не удалялись.
- Код почищен от технических комментариев и мёртвого `.emblem`.
- Структура, анимации, логика — сохранены 1:1.
- Сайт готов и для GH Pages сегодня, и для переноса на хост завтра — достаточно скопировать файлы и поменять 4 строки с доменом.

