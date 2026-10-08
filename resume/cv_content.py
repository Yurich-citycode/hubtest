# -*- coding: utf-8 -*-
"""
Содержание резюме: Pavel Yurich Vasilkovsky → Head of RWA, Solana Foundation.

Правится только этот файл. Верстка — в build_cv.py.
Разметка: **жирный** внутри текста и пунктов, ссылки — в поле "links".
"""

CONTENT = {
    # ─────────────────────────────────────────────────────────────── ENGLISH
    "en": {
        "file": "Pavel-Yurich-Vasilkovsky-Head-of-RWA-EN.pdf",
        "title": "Pavel Yurich Vasilkovsky — Curriculum Vitae — Head of RWA",
        "lang": "en-GB",
        "name": "PAVEL YURICH VASILKOVSKY",
        "role": "RWA Tokenization & Growth Lead",
        "subrole": "Issuer pipeline · post-launch TVL growth · liquidity & market structure · Solana",
        "contacts": [
            ("web3yurich@gmail.com", "mailto:web3yurich@gmail.com"),
            ("@PavelYuRichRWA (X)", "https://x.com/PavelYuRichRWA"),
            ("@PavelYuRichRWA (Telegram)", "https://t.me/PavelYuRichRWA"),
            ("linkedin.com/in/paul-yurich-vasilkovsky", "https://www.linkedin.com/in/paul-yurich-vasilkovsky/"),
            ("github.com/Yurich-citycode", "https://github.com/Yurich-citycode"),
            ("t.me/YuRichRWA", "https://t.me/YuRichRWA"),
        ],
        "availability": "Remote (UTC+3) · Open to relocation — New York · Available to travel 25–40%",
        "sections": [
            {
                "label": "Profile",
                "blocks": [
                    {"kind": "text", "body":
                        "RWA operator who builds tokenized products and then owns their growth. **10+ years** shipping "
                        "production software, the last two dedicated entirely to real-world-asset tokenization: issuer "
                        "structuring under a regulated digital-rights regime, instrument design, liquidity incentives and "
                        "distribution. Built a working city-economy tokenization stack from zero — an open city guide, a paid "
                        "membership circle and a revenue-share instrument structured together with an operator from the national "
                        "registry — and took that design to real, revenue-generating businesses. I understand the machinery that "
                        "decides who can hold an asset at all — allowlists, transfer restrictions, KYC/KYB gates — because I have "
                        "operated on both sides of it, and I know where tokenized products actually die after launch: liquidity, "
                        "secondary-market design and distribution, not the smart contract."},
                ],
            },
            {
                "label": "Core Expertise",
                "blocks": [
                    {"kind": "kv", "items": [
                        ["Tokenization & product", "RWA issuance structuring · instrument design (monetary claims, revenue share, funds) · NAV and redemption mechanics · issuer pipeline qualification · post-launch growth playbooks · TVL/AUM metrics"],
                        ["Liquidity & market structure", "Market-maker relationships · DEX/AMM integrations · yield strategies for tokenized collateral · secondary-market development · oracle and liquidation mechanics"],
                        ["Institutional & compliance", "Operator-registry issuance workflow · qualified / non-qualified investor limits · allowlists and transfer restrictions · sanctions and KYC screening reality · jurisdiction mapping (US / EU / CIS) · partner success and KPI reporting"],
                        ["Technical", "Solana (SPL tokens, transfer-fee and holder-incentive mechanics, tooling) · Python · TypeScript / Node.js · Docker · APIs and data pipelines · AI-assisted delivery · GitHub CI"],
                    ]},
                ],
            },
            {
                "label": "Experience & Impact",
                "blocks": [
                    {"kind": "roles", "items": [
                        {
                            "org": "RWA Structuring & Tokenization Practice",
                            "dates": "2025 — present",
                            "meta": "Founder & Lead — independent advisory for real-economy issuers",
                            "bullets": [
                                "Built an end-to-end issuance service for businesses: qualification diagnostics → structure → operator onboarding → placement support → holder reporting. Commercial model: fixed-fee diagnostics, fixed structuring fee, **success fee on placed volume**.",
                                "Designed the full issuance pattern for a revenue-share instrument: issuer entity, operator from the Bank of Russia registry under **259-FZ (digital financial assets)**, the instrument as a monetary claim, unit nominal, payout schedule from venue revenue, limits for non-qualified investors.",
                                "Assembled and qualified a pipeline of **dozens of business owners** with live revenue and legal entities; applied a hard against-the-alternative test (does the tokenized structure beat a plain loan?) to keep the pipeline honest.",
                                "Isolated the real growth bottleneck and built the process around it: technology deploys in weeks, whereas a business owner's consent to put revenue into a regulated instrument takes months. **Trust is the growth lever**; code is not.",
                            ],
                        },
                        {
                            "org": "City AI + City Code",
                            "dates": "2026 — present",
                            "meta": "Founder & Product Lead — city-economy tokenization stack, built in public",
                            "bullets": [
                                "**City AI (open layer):** Telegram bot on Python / aiogram 3 in Docker, Google Sheets as the live data store, Cloudflare Worker for community submissions — **200+ food venues, 100+ locations**, routes and events, XP mechanics, resident-contributed content, zero barrier to entry.",
                                "**City Code (closed layer):** paid membership circle built on six keys — rules, partner perks, the partner network itself, closed events, market insights, member community. Converts free reach into recurring revenue and into standing with local businesses.",
                                "**City RWA (ownership layer):** structuring a share of a real venue's revenue as a digital financial instrument — the pilot that proves the model on one asset type before scaling across others.",
                                "Growth logic that transfers to any RWA issuer: **open → enter → own**. Each layer funds the next; community and revenue exist before any token does — the reverse of how most tokenization projects are built.",
                            ],
                        },
                        {
                            "org": "RWA Research, Market Education & Distribution",
                            "dates": "2024 — present",
                            "meta": "Author & publisher — EN/RU",
                            "bullets": [
                                "Book-course **“RWA: We Explain” — 13 chapters**, a **76-term glossary** and a **6-module course** with assessment; deliberately no price calls and no signals. Used as market education for non-institutional audiences and as sales-enablement material for owners weighing an issuance.",
                                "Published analysis of the adoption gap that RWA growth teams are paid to close: the market multiplied roughly 5× in a year to $25–35B, still **under 1% of global stocks and bonds**, with institutions capturing most of it. Argued and evidenced where retail access actually comes from.",
                                "Built the publishing and design system behind it: JSON-driven cover renderer (Node.js + SVG + @resvg/resvg-js), strict brand canon, parallel EN/RU content pipeline, GitHub Pages distribution.",
                            ],
                        },
                        {
                            "org": "Solana Ecosystem",
                            "dates": "2026 — present",
                            "meta": "Builder — tooling, incentives, community assets",
                            "bullets": [
                                "Ship and operate Solana-side tooling: **SPL token launches**, holder-reward and **transfer-fee redistribution** mechanics, Telegram trading and notification bot infrastructure in Python.",
                                "**Superteam Earn** contributor; built community assets and custom emoji/sticker packs for RWA Foundation (@RWAFoundation_) — early-stage, retail-facing RWA community building.",
                                "Track the Solana RWA stack closely: tokenized treasuries and funds, transfer restrictions in the Token Extensions style, DeFi integrations, RWA market dashboards (RWA.xyz) and ecosystem programmes.",
                            ],
                        },
                        {
                            "org": "Software Engineering",
                            "dates": "10+ years",
                            "meta": "Full-cycle delivery",
                            "bullets": [
                                "10+ years of full-cycle delivery: requirements, architecture, implementation, deployment, operations, tests, secrets management. Comfortable being the sole technical owner of a product.",
                                "Python (aiogram, automation, data tooling) · JavaScript / TypeScript and Node.js (rendering, tooling) · Docker · REST APIs · Google Workspace API · Cloudflare Workers · GitHub Actions · Google Colab. AI-assisted development as a delivery multiplier.",
                            ],
                        },
                    ]},
                ],
            },
            {
                "label": "Professional Development",
                "blocks": [
                    {"kind": "bullets", "items": [
                        "**RWA & tokenization:** tokenized treasuries, private credit, funds, real estate, commodities — instrument mechanics end to end.",
                        "**Digital-asset regulation:** 259-FZ (digital financial assets) and 282-FZ (digital currency), operator-registry mechanics, qualified / non-qualified investor regimes, sanctions and payment-rail reality across the CIS.",
                        "**DeFi market structure:** AMM vs. order book, oracles, liquidation engines, yield strategies, market making.",
                        "**Solana development track** and AI-assisted product delivery; continuous self-directed study with published output at every stage.",
                    ]},
                ],
            },
            {
                "label": "Languages",
                "blocks": [
                    {"kind": "text", "body": "**Russian** — native  ·  **English** — C1, full professional proficiency"},
                ],
            },
            {
                "label": "Selected Publications",
                "blocks": [
                    {"kind": "bullets", "items": [
                        "**“RWA. Мы объясняем”** — 13-chapter book-course on tokenization, 2026.",
                        "**RWA Glossary** — 76 terms covering instruments, funds, risks, access and the CIS/CFA regimes.",
                        "**“YuRich RWA” course** — 6 modules plus knowledge assessment.",
                        "**X @PavelYuRichRWA · Telegram t.me/YuRichRWA** — RWA market analysis in English and Russian, built in public.",
                    ]},
                ],
            },
        ],
        "footer_left": "Pavel Yurich Vasilkovsky — Head of RWA application",
    },

    # ─────────────────────────────────────────────────────────────── РУССКИЙ
    "ru": {
        "file": "Pavel-Yurich-Vasilkovsky-Head-of-RWA-RU.pdf",
        "title": "Павел Юрич Васильковский — Резюме — Head of RWA",
        "lang": "ru-RU",
        "name": "ПАВЕЛ ЮРИЧ ВАСИЛЬКОВСКИЙ",
        "role": "RWA: токенизация и рост продуктов",
        "subrole": "Пайплайн эмитентов · рост TVL после запуска · ликвидность и структура рынка · Solana",
        "contacts": [
            ("web3yurich@gmail.com", "mailto:web3yurich@gmail.com"),
            ("@PavelYuRichRWA (X)", "https://x.com/PavelYuRichRWA"),
            ("@PavelYuRichRWA (Telegram)", "https://t.me/PavelYuRichRWA"),
            ("linkedin.com/in/paul-yurich-vasilkovsky", "https://www.linkedin.com/in/paul-yurich-vasilkovsky/"),
            ("github.com/Yurich-citycode", "https://github.com/Yurich-citycode"),
            ("t.me/YuRichRWA", "https://t.me/YuRichRWA"),
        ],
        "availability": "Удалённо (UTC+3) · Готов к релокации — Нью-Йорк · Готов к командировкам 25–40% времени",
        "sections": [
            {
                "label": "Профиль",
                "blocks": [
                    {"kind": "text", "body":
                        "Оператор RWA: строю токенизированные продукты и сам отвечаю за их рост. **10+ лет** в разработке и выпуске "
                        "продакшн-систем, последние два года — целиком в токенизации реальных активов: конструкция выпуска в "
                        "регулируемом режиме цифровых прав, дизайн инструмента, ликвидность и дистрибуция. С нуля собрал работающий "
                        "стек токенизации городской экономики: открытый городской гид, платный закрытый круг и инструмент на долю "
                        "выручки, собранный вместе с оператором из реестра регулятора, — и вывел этот дизайн на реальный бизнес с "
                        "живой выручкой. Понимаю механику, которая решает, кто вообще может держать актив: allowlist, ограничения "
                        "передачи, KYC/KYB — прошёл это с обеих сторон. Знаю, где продукты умирают после запуска: ликвидность, "
                        "вторичный рынок и дистрибуция, а не смарт-контракт."},
                ],
            },
            {
                "label": "Компетенции",
                "blocks": [
                    {"kind": "kv", "items": [
                        ["Токенизация и продукт", "Конструкция выпуска RWA · дизайн инструмента (денежное требование, доля выручки, фонды) · NAV и механика погашения · квалификация пайплайна эмитентов · playbook роста после запуска · метрики TVL/AUM"],
                        ["Ликвидность и рынок", "Маркет-мейкеры · интеграции с DEX/AMM · yield-сценарии для токенизированного обеспечения · развитие вторичного рынка · оракулы и ликвидационные механики"],
                        ["Институции и комплаенс", "Работа с оператором из реестра · лимиты квал/неквал · allowlist и трансферные ограничения · санкционный и KYC-скрининг · карта юрисдикций (US / EU / СНГ) · partner success и отчётность по KPI"],
                        ["Технологии", "Solana (SPL-токены, механики transfer fee и вознаграждения держателей, тулинг) · Python · TypeScript / Node.js · Docker · API и пайплайны данных · ИИ-assisted разработка · GitHub CI"],
                    ]},
                ],
            },
            {
                "label": "Опыт и результаты",
                "blocks": [
                    {"kind": "roles", "items": [
                        {
                            "org": "Практика конструирования выпусков RWA",
                            "dates": "2025 — н. в.",
                            "meta": "Основатель и руководитель — независимый консалтинг для эмитентов реального сектора",
                            "bullets": [
                                "Собрал сквозную услугу для бизнеса: диагностика → разбор → конструкция → посадка на оператора → сопровождение размещения → отчётность держателям. Модель: фикс за диагностику, фикс за сборку, **процент с фактически привлечённого объёма**.",
                                "Разработал полный шаблон выпуска на долю выручки: эмитент — юрлицо, оператор из реестра Банка России в рамках **259-ФЗ (цифровые финансовые активы)**, инструмент — денежное требование, номинал единицы, график выплат из выручки точки, лимиты для неквалифицированных инвесторов.",
                                "Собрал и квалифицировал пайплайн из **десятков собственников** с живой выручкой и юрлицом; ввёл жёсткую проверку «токен дешевле обычного займа?» — она держит пайплайн честным.",
                                "Нашёл настоящий барьер роста и построил процесс вокруг него: технология разворачивается неделями, а согласие собственника отдать долю выручки в регулируемый инструмент — месяцами. **Доверие и есть рычаг роста**; код — нет.",
                            ],
                        },
                        {
                            "org": "City AI + City Code",
                            "dates": "2026 — н. в.",
                            "meta": "Основатель и продакт-лид — стек токенизации городской экономики, разработка в публичном режиме",
                            "bullets": [
                                "**City AI (открытый слой):** телеграм-бот на Python / aiogram 3 в Docker, Google-таблица как живое хранилище, Cloudflare Worker для заявок от жителей — **200+ точек еды, 100+ локаций**, маршруты и события, XP-механика, места добавляют сами горожане, нулевой порог входа.",
                                "**City Code (закрытый слой):** платный круг на шести ключах — правила, скидки у партнёров, сам партнёрский круг, закрытые мероприятия, рыночная аналитика, сообщество участников. Превращает бесплатный охват в регулярную выручку и в доверие локального бизнеса.",
                                "**City RWA (слой владения):** конструкция доли выручки реальной точки как цифрового финансового инструмента — пилот, который доказывает модель на одном классе активов до масштабирования на другие.",
                                "Логика роста, переносимая на любого эмитента RWA: **открыть → войти → владеть**. Каждый слой финансирует следующий; сообщество и выручка появляются до токена — обратный порядок по отношению к большинству проектов токенизации.",
                            ],
                        },
                        {
                            "org": "Исследование рынка RWA, обучение и дистрибуция контента",
                            "dates": "2024 — н. в.",
                            "meta": "Автор и издатель — EN/RU",
                            "bullets": [
                                "Книга-курс **«RWA. Мы объясняем» — 13 глав**, **глоссарий на 76 терминов** и **курс из 6 модулей** с проверкой знаний; намеренно без прогнозов цены и сигналов. Используется как обучение рынка для неинституциональной аудитории и как sales enablement для собственников, которые взвешивают выпуск.",
                                "Опубликовал разбор разрыва доступа, который как раз и закрывают growth-команды RWA: рынок вырос примерно в 5 раз за год до $25–35 млрд, но это **меньше 1% мирового рынка акций и облигаций**, и основную часть держат институты. Показал и обосновал, откуда берётся розничный доступ.",
                                "Построил издательскую и дизайн-систему: рендер обложек из JSON (Node.js + SVG + @resvg/resvg-js), строгий бренд-канон, параллельный контент-пайплайн EN/RU, распространение через GitHub Pages.",
                            ],
                        },
                        {
                            "org": "Экосистема Solana",
                            "dates": "2026 — н. в.",
                            "meta": "Билдер — тулинг, механики вознаграждения, ассеты для комьюнити",
                            "bullets": [
                                "Пишу и эксплуатирую инструменты на стороне Solana: **запуски SPL-токенов**, механики вознаграждения держателей и **перераспределения transfer fee**, инфраструктура телеграм-ботов для торговли и уведомлений на Python.",
                                "Участник **Superteam Earn**; собрал ассеты для комьюнити и кастомные эмодзи-паки для RWA Foundation (@RWAFoundation_) — ранняя розничная сборка RWA-сообщества.",
                                "Плотно слежу за RWA-стеком Solana: токенизированные трежерис и фонды, трансферные ограничения в стиле Token Extensions, интеграции с DeFi, рыночные дашборды (RWA.xyz) и экосистемные программы.",
                            ],
                        },
                        {
                            "org": "Разработка программного обеспечения",
                            "dates": "10+ лет",
                            "meta": "Полный цикл",
                            "bullets": [
                                "10+ лет полного цикла: требования, архитектура, реализация, деплой, эксплуатация, тесты, управление секретами. Комфортно быть единственным техническим владельцем продукта.",
                                "Python (aiogram, автоматизация, работа с данными) · JavaScript / TypeScript и Node.js (рендеринг, тулинг) · Docker · REST API · Google Workspace API · Cloudflare Workers · GitHub Actions · Google Colab. ИИ-assisted разработка как множитель скорости.",
                            ],
                        },
                    ]},
                ],
            },
            {
                "label": "Профессиональное развитие",
                "blocks": [
                    {"kind": "bullets", "items": [
                        "**RWA и токенизация:** токенизированные трежерис, частный кредит, фонды, недвижимость, сырьё — механика инструментов от начала до конца.",
                        "**Регулирование цифровых активов:** 259-ФЗ (ЦФА) и 282-ФЗ (цифровые валюты), механика реестра операторов, режимы квал/неквал, санкционная реальность и платёжные рельсы в СНГ.",
                        "**Структура рынка DeFi:** AMM против книги заявок, оракулы, ликвидационные движки, yield-стратегии, маркет-мейкинг.",
                        "**Трек разработки на Solana** и ИИ-assisted продуктовая разработка; непрерывное самообразование с публичным результатом на каждом этапе.",
                    ]},
                ],
            },
            {
                "label": "Языки",
                "blocks": [
                    {"kind": "text", "body": "**Русский** — родной  ·  **Английский** — C1, свободный рабочий уровень"},
                ],
            },
            {
                "label": "Публикации",
                "blocks": [
                    {"kind": "bullets", "items": [
                        "**«RWA. Мы объясняем»** — книга-курс из 13 глав о токенизации, 2026.",
                        "**Глоссарий RWA** — 76 терминов: инструменты, фонды, риски, доступ, режимы СНГ/ЦФА.",
                        "**Курс «YuRich RWA»** — 6 модулей плюс проверка знаний.",
                        "**X @PavelYuRichRWA · Telegram t.me/YuRichRWA** — аналитика рынка RWA на английском и русском, разработка в публичном режиме.",
                    ]},
                ],
            },
        ],
        "footer_left": "Павел Юрич Васильковский — отклик на Head of RWA",
    },
}
