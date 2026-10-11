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

## Картинки и обложки

- `brand/YURICHHUB-STYLE.md` — канон стиля: цвета, шрифты, что можно и что нельзя
- `brand/covers/` — сборка обложек 1600×900 из JSON (`npm install && node render.js post.json`)
- `brand/samples/`, `brand/post-cards/`, `brand/reference/` — готовые обложки и карточки
- `brand/emoji/` — премиум-эмодзи для статуса из фото
- `comics1–6.jpg`, `*-preview.jpg` — картинки для ленты и превью страниц

## Книга

`book/` — «RWA мы объясняем»: главы в markdown, сборка PDF — `book/build_pdf.py`.

## Разное

- `rwa-series-posts.md` — серия постов про RWA с текстами и обложками
- `.nojekyll` — служебный файл GitHub Pages, чтобы отдавать файлы как есть
