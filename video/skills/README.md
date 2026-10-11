# Вендоренные скиллы

Здесь лежат наборы агентных скиллов, взятые из пяти публичных репозиториев. Это «мозг» видео-студии: правила, по которым агент делает видео, интерфейсы и графику без слопа.

Апстримы не редактируются — только читаются. Если правим под себя, пишем в `video/NOTES.md`, а не внутрь чужого SKILL.md.

## Что откуда взято

| Папка | Репозиторий | Коммит | Лицензия | Взято |
| --- | --- | --- | --- | --- |
| `hyperframes/` | [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | `2fbaef6` | Apache-2.0 | Весь набор: роутер `hyperframes`, 8 доменных скиллов (`hyperframes-core/-animation/-keyframes/-creative/-audio/-cli/-registry/-studio`), `media-use` и 9 воркфлоу (product-launch-video, faceless-explainer, motion-graphics, embedded-captions, talking-head-recut, music-to-video, slideshow, pr-to-video, general-video, remotion-to-hyperframes, figma) |
| `taste-skill/` | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) | `717446e` | MIT | Все 13 скиллов: `taste-skill` v2 + v1, `gpt-tasteskill`, `image-to-code-skill`, `redesign-skill`, `soft-skill`, `minimalist-skill`, `brutalist-skill`, `output-skill`, `stitch-skill`, `imagegen-frontend-web/-mobile`, `brandkit` |
| `impeccable/` | [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | `c63b8dd` | Apache-2.0 | Скилл `impeccable` целиком: `SKILL.md` + 24 команды в `reference/` (craft, audit, critique, polish, animate, typeset, layout, live…) + degraded-агенты |
| `remotion/` | [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | `9fdd1fc` | Remotion License | 12 пользовательских скиллов из `packages/skills`: `remotion-create`, `remotion-best-practices`, `remotion-render`, `remotion-captions`, `remotion-interactivity`, `remotion-multimedia`, `remotion-markup`, `remotion-maps`, `remotion-saas`, `remotion-studio`, `remotion-docs`, `remotion-upgrade` |
| `emil/` | [emilkowalski/skills](https://github.com/emilkowalski/skills) | `2d22863` | MIT | Все 15 скиллов: `emil-design-eng`, `animate`, `animate-expo`, `review-animations`, `improve-animations`, `find-animation-opportunities`, `animation-performance`, `animation-vocabulary`, `apple-design`, `pick-ui-library`, `prototype`, `mobile-native`, `break-ui`, `ask-sonner`, `write-swift` |

Дата снятия: 11 октября 2026. Лицензии скопированы в каждую папку рядом со скиллами — при распространении они должны ехать вместе с кодом.

## Как этим пользуются

Скиллы — это инструкции для агента, а не библиотеки. Рабочий цикл:

1. Перед задачей читаем нужный SKILL.md: для видео — `hyperframes/hyperframes/SKILL.md` (роутер) и `hyperframes/hyperframes-core/SKILL.md` (контракт композиции).
2. Для движения и анимации — `emil/animate/SKILL.md` и `emil/review-animations/SKILL.md`.
3. Для новых страниц и интерфейсов — `taste-skill/taste-skill/SKILL.md`, для аудита — `impeccable/SKILL.md`.
4. Если видео собирается на React, а не на HTML — `remotion/remotion-create/SKILL.md`.

## Обновление

Апстримы живут быстро, поэтому периодически перекачиваем:

```bash
cd /tmp && git clone --filter=blob:none --sparse --depth 1 https://github.com/heygen-com/hyperframes hf
cd hf && git sparse-checkout set --no-cone '/skills/' '/LICENSE'
```

Дальше копируем в `video/skills/<папка>/` и обновляем коммит в таблице выше.

Для HyperFrames есть и штатный путь без вендоринга — он ставит свежую версию из `main`:

```bash
npx hyperframes skills update            # ядро
npx hyperframes skills update <workflow> # конкретный воркфлоу (product-launch-video и т.д.)
```
