# ЗАДАЧА (выполняй в сессии SevastopolAIbot)

**Подготовка (один раз, в начале):**
```bash
git clone -q --depth 1 -b arena/4247d834-hubtest https://github.com/Yurich-citycode/hubtest.git /tmp/kit
```
Файл лежит в `/tmp/kit/handoff/`.

1. `git apply /tmp/kit/handoff/ai-bot-beta.patch` (в корне репозитория SevastopolAIbot).
2. Проверь: в `sevastopolaibot.py` в приветствии /start (переменная `welcome_text`) первой строкой идёт «🟡 Это бета-версия: база мест постоянно пополняется…». `python3 -m py_compile sevastopolaibot.py` — без ошибок.
3. Commit: «Бета: пометка в приветствии /start».
4. PR в main → merge. **Ничего, кроме патча, не трогай.**

После мерджа: перезапусти бота (одна команда) — бета-пометка появится у всех в /start.
