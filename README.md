# YurichHub — hubtest

Статический сайт-хаб: Sevastopol AI × City Code × Crimea RWA + курс RWA + глоссарий 57 терминов + офер ЦФА.

## Продакшн файлы (минимум для GitHub Pages и хоста)

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
comics1.jpg ... comics6.jpg
indexpreview.jpg
coursepreview.jpg
glossarypreview.jpg
cfapreview.jpg
.nojekyll
```

Всё остальное в корне (`CityCode.png`, `sevastopol-ai.png`, `nebank.jpg`, `brand/`) — не требуется для работы, но оставлено.


## Перенос на свой хост

1. Скопируй файлы из списка выше на сервер.
2. Замени в `<head>` каждой HTML-страницы `https://yurich-citycode.github.io/hubtest/` на `https://yourdomain.com/`
   - `og:url`, `og:image`, `twitter:image`, `canonical`
3. Готово — все ссылки относительные.

Подробный аудит: `AUDIT_REPORT.md`
Канон стиля обложек: `brand/YURICHHUB-STYLE.md`
