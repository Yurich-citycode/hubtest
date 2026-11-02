# ЗАДАЧА (открой эту инструкцию в сессии SevastopolAIbot)

1. Найди рядом файл `ai-bot-beta.patch`.
2. `git apply ai-bot-beta.patch` (в корне репозитория SevastopolAIbot).
3. Проверь: в `sevastopolaibot.py` в приветствии /start (переменная `welcome_text`) первой строкой идёт «🟡 Это бета-версия: база мест постоянно пополняется…». `python3 -m py_compile sevastopolaibot.py` — без ошибок.
4. Commit: «Бета: пометка в приветствии /start».
5. PR в main → merge. **Ничего, кроме патча, не трогай.**

После мерджа: перезапусти бота (одна команда) — бета-пометка появится у всех в /start.
