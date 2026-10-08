# Резюме → Head of RWA, Solana Foundation

Два PDF, один смысл: отклик на вакансию
[Head of RWA](https://jobs.ashbyhq.com/Solana%20Foundation/cb692853-04c1-4683-bb9a-8bb0783e2c1a)
(Solana Foundation, Business Development, New York, Full time).

| Файл | Что это |
|---|---|
| `Pavel-Yurich-Vasilkovsky-Head-of-RWA-EN.pdf` | основная версия для отправки в Ashby |
| `Pavel-Yurich-Vasilkovsky-Head-of-RWA-RU.pdf` | русская версия, тот же текст |
| `CV-EN.md`, `CV-RU.md` | тот же текст в markdown — для ATS-полей, LinkedIn и правок |
| `CV-PITCH.md` | питч, ответы для формы Ashby, cover note, истории для созвона |
| `cv_content.py` | весь текст резюме (правится только он) |
| `build_cv.py` | вёрстка PDF и markdown |
| `fonts/` | IBM Plex Serif / Sans / Mono, SIL OFL (`OFL.txt`) |

## Пересборка

```bash
pip install --break-system-packages fpdf2
python3 resume/build_cv.py
```

Скрипт печатает число страниц. Целевой объём — **2 страницы**; если текст
растёт, сокращать надо в `cv_content.py`, а не в вёрстке.

## Под что подогнано (требования вакансии → блоки резюме)

| Требование из вакансии | Где в резюме |
|---|---|
| 5+ лет product growth / BD в digital assets с ответственностью за TVL/AUM | «Что я приношу», опыт ChainZap / BYDFi / Web3Yurich |
| Полный жизненный цикл эмитента: пайплайн → запуск → пост-лонч → partner success | Web3Yurich Agency, CityCode (вместе с City AI) |
| GTM и growth-playbooks, масштабируемые на классы активов | «Из трек-рекорда»: TON, TRON, $ChillHouse, GmGn |
| Ликвидность: маркет-мейкеры, DeFi-интеграции, вторичный рынок, yield | профиль, «Что я приношу» (структура рынка изнутри — Web3YuRich) |
| Кастодианы, кошельки, дистрибуция, обучение рынка | «Публикации» + обучение рынка в «Что я приношу» |
| Работа с фаундерами и ранними стадиями + институциональные требования | пайплайн эмитентов, открытая и закрытая сторона продукта |
| Понимание Solana (розница + техника), активность в сообществе | GmGn — терминал на Solana; работа на Solana в CityCode |
| Travel 25–40% | шапка, строка доступности |

## Что внутри опыта

Роли из LinkedIn (ChainZap, CityCode, Web3Yurich Agency, BYDFi, Web3YuRich) —
в секции `Experience`, кейсы с цифрами — в `Selected Track Record`. Формулировка
про атрибуцию («цифры описывают результат проекта, роль была прямой и
определяющей») стоит в резюме сознательно: в этом секторе атрибуцию почти никогда
не фиксировали системно, и честная оговорка в разговоре сильнее, чем тишина.

## Что осталось дополнить

- **ChainZap** — что это за продукт и за какие метрики отвечает рост. Сейчас в
  тексте общая формулировка; после уточнения добавить одну строку с продуктом и
  метрикой в `cv_content.py`.
- При желании — вторая страница EN для самых сильных кейсов (запуск на TON, $CIS).

## Контакты в резюме

`web3yurich@gmail.com` · X/Telegram `@PavelYuRichRWA` ·
linkedin.com/in/paul-yurich-vasilkovsky · github.com/Yurich-citycode ·
`t.me/YuRichRWA`
