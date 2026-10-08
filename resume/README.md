# Резюме → Head of RWA, Solana Foundation

Два PDF, один смысл: отклик на вакансию
[Head of RWA](https://jobs.ashbyhq.com/Solana%20Foundation/cb692853-04c1-4683-bb9a-8bb0783e2c1a)
(Solana Foundation, Business Development, New York, Full time).

| Файл | Что это |
|---|---|
| `Pavel-Yurich-Vasilkovsky-Head-of-RWA-EN.pdf` | основная версия для отправки в Ashby |
| `Pavel-Yurich-Vasilkovsky-Head-of-RWA-RU.pdf` | русская версия, тот же текст |
| `CV-EN.md`, `CV-RU.md` | тот же текст в markdown — для ATS-полей, LinkedIn и правок |
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
| 5+ лет product growth / BD в digital assets с ответственностью за TVL/AUM | профиль, `RWA Structuring & Tokenization Practice` |
| Полный жизненный цикл эмитента: пайплайн → запуск → пост-лонч → partner success | `RWA Structuring…` (сквозная услуга, пайплайн, KPI) |
| GTM и growth-playbooks, масштабируемые на классы активов | `City AI + City Code` (слои открыть → войти → владеть), playbook-строка в компетенциях |
| Ликвидность: маркет-мейкеры, DeFi-интеграции, вторичный рынок, yield | компетенции «Ликвидность и структура рынка» |
| Кастодианы, кошельки, дистрибуция, обучение рынка | `RWA Research, Market Education & Distribution` (книга, курс, глоссарий) |
| Работа с фаундерами и ранними стадиями + институциональные требования | пайплайн из десятков собственников; проверка «токен против займа» |
| Понимание Solana (розница + техника), активность в сообществе | `Solana Ecosystem` (SPL-токены, transfer fee, Superteam Earn, RWA Foundation) |
| Travel 25–40% | шапка, строка доступности |

## Что осталось дополнить

Раздел с реальными работодателями и годами из LinkedIn в песочницу не
попал (LinkedIn отдаёт 403 роботам). Сейчас опыт представлен проектными
ролями. Когда появится текст профиля — вставить в `cv_content.py` в секцию
`Experience & Impact` и пересобрать.

## Контакты в резюме

`web3yurich@gmail.com` · X/Telegram `@PavelYuRichRWA` ·
linkedin.com/in/paul-yurich-vasilkovsky · github.com/Yurich-citycode ·
`t.me/YuRichRWA`
