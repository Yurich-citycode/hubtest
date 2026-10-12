# YurichHub

Сайт-хаб: Севастополь AI, City Code, Crimea RWA — плюс курс по RWA, глоссарий терминов и офер ЦФА.

Открывается здесь: [yurich-citycode.github.io/YuRichHUB](https://yurich-citycode.github.io/YuRichHUB/)

## Страницы

| Страница | Что на ней |
| --- | --- |
| `index.html` | Главная: направления, проекты, ссылки |
| `course.html` | Курс «RWA с нуля» — шесть модулей |
| `glossary.html` | Глоссарий: 57 терминов |
| `cfa.html` | Офер ЦФА: калькулятор выплат и стресс-тесты |
| `digital-cities.html` | Отчёт «Цифровые города 2026» — 45+ кейсов, разбор OAZIS, серия постов. PDF для печати: `digital-cities.pdf` |
| `early-projects.html` | Лента ранних криптопроектов, рубрика RWA Early |
| `SHIVA/index.html` | Интерактивный SHIVA-сайт с заданиями и ачивками; `SHIVA/book.html` — русская мини-книга, `SHIVA/book-en.html` — английская версия и готовые X-треды |
| `shiva.html` | «Храм Шивы»: одностраничное вертикальное путешествие по мифу «Пепел и Рассвет» с 14 главами, испытаниями, Стеной и Котлом |

## Картинки и обложки

- `brand/YURICHHUB-STYLE.md` — канон стиля: цвета, шрифты, что можно и что нельзя
- `brand/covers/` — сборка обложек 1600×900 из JSON (`npm install && node render.js post.json`)
- `brand/samples/`, `brand/post-cards/`, `brand/reference/` — готовые обложки и карточки
- `brand/emoji/` — премиум-эмодзи для статуса из фото
- `comics1–6.jpg`, `*-preview.jpg` — картинки для ленты и превью страниц

## Книга

`book/` — «RWA мы объясняем»: главы в markdown, сборка PDF — `book/build_pdf.py`.

## Видео

`video/` — студия видео в каноне бренда: HyperFrames (HTML → MP4) и Remotion (React → MP4),
62 скилла из пяти открытых репозиториев и готовые ролики в `video/renders/`. Всё рендерится
локально, без облаков. Установка — `cd video && bash setup.sh`, разбор репозиториев — `video/STUDY.md`.

## Разное

- `rwa-series-posts.md` — серия постов про RWA с текстами и обложками
- `SHIVA/` — досье, концепция, план на 14 дней, готовые X/TG-посты и raid-kit для SHIVA
- `.nojekyll` — служебный файл GitHub Pages, чтобы отдавать файлы как есть
