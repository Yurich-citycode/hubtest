# Заметки студии: находки и решения

Здесь копятся выводы, которые не хочется терять: что проверено, что сломано на сайте, что
заменяет недоступные сервисы.

## 1. На сайте русские заголовки идут не в брендовом шрифте

**Что не так.** `index.html` и соседние страницы просят у Google Fonts набор `Anton` + `Archivo`
и объявляют:

```css
--font-display:'Anton', sans-serif;
--font-sans:'Archivo', sans-serif;
```

Anton — латинский: кириллицы в нём нет (проверено fontkit по файлу канона `anton-400.ttf`:
`А` U+0410, `Я` U+042F, `Ё` U+0401 — глифов нет). Archivo в файлах канона — тоже без кириллицы.

**Проверка.** Отрендерили «ГОРОД ОТВЕЧАЕТ» в Chromium тремя стеками и сравнили попиксельно:

| Стек | Отличие от `sans-serif` |
| --- | --- |
| `'Anton', sans-serif` | **0.0 %** — то же самое изображение |
| `'Oswald'` | 3.3 % — другой шрифт |

Плюс `document.fonts.check("64px Anton", "ГОРОД")` возвращает `false`.

**Вывод.** Русский текст на сайте рисует системный шрифт: браузер подставляет его, потому что
в Anton нет нужных глифов. Канон (`brand/YURICHHUB-STYLE.md`, раздел 4) требует другое:
кириллический дисплей — **Oswald 700 с обводкой 2.8 % кегля**, текст — **Inter**. Генератор
обложек `brand/covers/render.js` делает именно так, поэтому обложки выглядят каноном, а страницы
сайта — нет.

**Как починить (не сделано, это правка сайта, а не студии).** Подключить Oswald и Inter
и развести стеки по языку, как в `video/bin/prepare-site-copy.mjs`:

```css
/* латиница — Anton, кириллица — Oswald: разводим через unicode-range */
@font-face{font-family:'Anton';src:url(fonts/anton-400.woff2) format('woff2');unicode-range:U+0000-024F,U+1E00-1EFF;}
@font-face{font-family:'Anton';src:url(fonts/oswald-700.woff2) format('woff2');unicode-range:U+0400-04FF,U+2116;}
```

То же для текстового стека: Archivo на латинице, Inter на кириллице.

## 2. Песочница: чем заменили недоступное

| Нужно | Обычный путь | Наш путь |
| --- | --- | --- |
| Chromium | `npx puppeteer browsers install chrome` (Google CDN) | npm-пакет `@sparticuz/chromium` + `bin/al2023.tar.br` для libnspr4/libnss3 |
| FFmpeg, FFprobe | `apt install ffmpeg` | npm-пакеты `@ffmpeg-installer` / `@ffprobe-installer` |
| GSAP | CDN `<script src="https://cdn.jsdelivr.net/...">` | `vendor/gsap.min.js` из npm |
| Шрифты | Google Fonts | файлы канона из `brand/covers/fonts` |

Браузер без библиотек падает с `error while loading shared libraries: libnspr4.so` — лечится
`LD_LIBRARY_PATH=/tmp/yurichhub-video/lib`, который выдаёт `bin/provision.mjs`.

## 3. Превью-студия HyperFrames слушает только localhost

`hyperframes preview` жёстко биндится на `127.0.0.1` (в коде — `hostname: "127.0.0.1"`), поэтому
живое превью в браузере не открывалось бы. Решение — `bin/preview-proxy.mjs`: слушает `0.0.0.0`
и проксирует HTTP и WebSocket на студию. Порт студии не меняется, правки в HTML подхватываются
автоматически.

## 4. Как проверять кадр, а не верить глазам

`hyperframes check` ловит то, что глазами на контактном листе не видно: перекрытие текстовых
блоков, вылет за маску, невидимую заливку, контраст по WCAG. Полезные ручки:

- `data-layout-allow-overlap` — на **сам текстовый блок**, участвующий в задуманной слоистости
  (глитч-слои). На обёртку не поможет: флаг не наследуется.
- `data-layout-allow-overflow` — намеренный вылет из бокса (маска с запасом под выносные элементы).
- `data-layout-ignore` — служебный слой (градиентная подложка) вообще вне аудита.

Порядок важен: сначала вычищаются ошибки `lint`, иначе `check` молча отключает аудит раскладки
и контраста и показывает «0 проверок», что легко принять за чистый результат.
