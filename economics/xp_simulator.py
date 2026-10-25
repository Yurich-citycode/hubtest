#!/usr/bin/env python3
"""
Симулятор XP City Passport на НАСТОЯЩЕМ коде бота.

Не копирует константы руками: импортирует sevastopolaibot.py из репозитория
SevastopolAIbot, подменяет часы (datetime) и прогоняет типовых пользователей
день за днём. Так видно, через сколько дней реально берутся пороги
100 / 300 / 800 / 2000 / 4000 / 7000 XP и когда открывается грант City Code.

Запуск:
    git clone https://github.com/Yurich-citycode/SevastopolAIbot.git ../SevastopolAIbot
    pip install "aiogram>=3.7,<4" pandas openpyxl requests python-dotenv
    python economics/xp_simulator.py --bot ../SevastopolAIbot          # таблица в консоль
    python economics/xp_simulator.py --bot ../SevastopolAIbot --md out.md

Профили описаны в PERSONAS ниже — меняй частоты и смотри, как сдвигаются сроки.
"""
from __future__ import annotations

import argparse
import importlib.util
import logging
import os
import random
import sys
import tempfile
from datetime import datetime as _real_dt, timedelta
from types import SimpleNamespace

START = _real_dt(2026, 11, 1, 12, 0, 0)
HORIZON_DAYS = 365 * 6


class _Clock:
    now = START


class FakeDT(_real_dt):
    @classmethod
    def now(cls, tz=None):  # noqa: D401
        return _Clock.now


def load_bot(path: str):
    os.environ.setdefault("TG_TOKEN", "")
    os.environ["STATE_FILE"] = os.path.join(tempfile.mkdtemp(), "state.json")
    spec = importlib.util.spec_from_file_location("sai_bot", os.path.join(path, "sevastopolaibot.py"))
    mod = importlib.util.module_from_spec(spec)
    logging.disable(logging.CRITICAL)
    spec.loader.exec_module(mod)
    mod.datetime = FakeDT
    mod.save_state = lambda: None  # не пишем файл на каждый клик
    return mod


# ── профили ──────────────────────────────────────────────────────────────
# buttons: какие кнопки нажимает в день визита (XP_ACTIVITY_REWARDS, каждая 1 раз/день)
# visits_per_week: сколько дней в неделю заходит
# monthly: verified-действия в месяц {ACTION: штук}; referrals_per_month — приглашённые друзья
PERSONAS = [
    dict(key="tourist", name="Турист / редкий гость", visits_per_week=1,
         buttons=["BTN_MAIN_MENU", "BTN_FOOD", "BTN_LOCATIONS"], monthly={}, referrals_per_month=0),
    dict(key="local", name="Житель: заходит 3 раза в неделю", visits_per_week=3,
         buttons=["BTN_MAIN_MENU", "BTN_FOOD", "BTN_EVENTS"], monthly={}, referrals_per_month=0),
    dict(key="active", name="Активный: 5 дней в неделю, всё меню", visits_per_week=5,
         buttons=["BTN_MAIN_MENU", "BTN_FOOD", "BTN_LOCATIONS", "BTN_ROUTES", "BTN_EVENTS", "NEARBY_FOOD"],
         monthly={}, referrals_per_month=0),
    dict(key="max_buttons", name="Фармер кнопок: каждый день все 8 действий", visits_per_week=7,
         buttons=["BTN_MAIN_MENU", "BTN_FOOD", "BTN_LOCATIONS", "BTN_ROUTES", "BTN_EVENTS",
                  "NEARBY_FOOD", "GEO_FIND", "SUGGEST_PLACE"], monthly={}, referrals_per_month=0),
    dict(key="contributor", name="Вкладчик города: активный + 2 места + 1 событие + 1 друг в месяц",
         visits_per_week=5,
         buttons=["BTN_MAIN_MENU", "BTN_FOOD", "BTN_LOCATIONS", "BTN_ROUTES", "BTN_EVENTS", "NEARBY_FOOD"],
         monthly={"PLACE_ACCEPTED": 2, "EVENT_CHECKIN": 1}, referrals_per_month=1),
    dict(key="ambassador", name="Амбассадор: вкладчик + 4 места + 2 события + 3 друга в месяц",
         visits_per_week=6,
         buttons=["BTN_MAIN_MENU", "BTN_FOOD", "BTN_LOCATIONS", "BTN_ROUTES", "BTN_EVENTS", "NEARBY_FOOD"],
         monthly={"PLACE_ACCEPTED": 4, "EVENT_CHECKIN": 2}, referrals_per_month=3),
    dict(key="partner", name="Партнёр-точка: житель + узел подключён (+200) и жив каждый месяц (+80)",
         visits_per_week=3, buttons=["BTN_MAIN_MENU", "BTN_FOOD", "BTN_EVENTS"],
         monthly={"__NODE__": 1}, referrals_per_month=0),
]


# ── предложение по перекалибровке (см. docs/ECOSYSTEM.md, раздел XP) ─────────
# Кнопки дают привычку, но не ранг: потолок 10 XP/день, сырой «предложить место» = 0.
# Ранг City Code должен давать вклад в город, а не нажатия.
PROPOSAL = {
    "activity": {"BTN_MAIN_MENU": 1, "BTN_FOOD": 2, "BTN_LOCATIONS": 2, "BTN_ROUTES": 2,
                 "BTN_EVENTS": 2, "NEARBY_FOOD": 1, "GEO_FIND": 1, "SUGGEST_PLACE": 0},
    "daily_cap": 10,
    "verified": {"PLACE_ACCEPTED": 60, "ROUTE_ACCEPTED": 100, "EVENT_CHECKIN": 80},
}


def apply_proposal(mod):
    mod.XP_ACTIVITY_REWARDS.clear()
    mod.XP_ACTIVITY_REWARDS.update(PROPOSAL["activity"])
    mod.XP_VERIFIED_REWARDS.update(PROPOSAL["verified"])
    original = mod.award_activity_xp
    cap = PROPOSAL["daily_cap"]

    def capped(user, action):
        if mod.xp_today(user.id) >= cap:
            return 0
        got = original(user, action)
        over = mod.xp_today(user.id) - cap
        if over > 0:
            mod.PASSPORTS[user.id]["xp"] -= over
            today = mod.datetime.now().strftime("%Y-%m-%d")
            mod.PASSPORTS[user.id]["daily_xp"][today][action] -= over
            got -= over
        return got

    mod.award_activity_xp = capped


def simulate(mod, persona: dict, seed: int = 7) -> dict:
    rnd = random.Random(seed)
    mod.PASSPORTS.clear()
    mod.REFERRALS.clear()
    mod.ANALYTICS_ROWS.clear()
    uid = 900000001
    user = SimpleNamespace(id=uid, full_name=persona["name"], username="sim")
    _Clock.now = START
    mod.create_passport_if_not_exists(user)
    thresholds = list(mod.XP_LEVELS)
    reached: dict[int, int] = {}
    grant_day = None
    friend_seq = 0
    node_connected = False
    per_week = persona["visits_per_week"]
    for day in range(HORIZON_DAYS):
        _Clock.now = START + timedelta(days=day)
        # визит: выбираем дни недели детерминированно
        if (day % 7) < per_week:
            for b in persona["buttons"]:
                mod.award_activity_xp(user, b)
        # ежемесячные verified-действия раскидываем по месяцу
        dom = day % 30
        for action, n in persona["monthly"].items():
            for k in range(n):
                if dom == (k * 30 // max(n, 1)) + 3:
                    if action == "__NODE__":
                        node = "node-1"
                        act = "PARTNER_NODE_30D" if node_connected else "PARTNER_NODE_CONNECTED"
                        mod.award_verified_xp(uid, act, actor="admin", meta={"node_id": node})
                        node_connected = True
                    elif action == "EVENT_CHECKIN":
                        mod.award_verified_xp(uid, action, actor="admin", meta={"event_id": f"ev-{day}-{k}"})
                    else:
                        mod.award_verified_xp(uid, action, actor="admin")
        for k in range(persona["referrals_per_month"]):
            if dom == (k * 30 // max(persona["referrals_per_month"], 1)) + 10:
                friend_seq += 1
                fid = 800000000 + friend_seq
                # настоящий код: +25 рефереру сразу
                import asyncio
                asyncio.run(mod.process_referral(fid, uid))
                # бонус +40 «друг жив 7 дней»: считаем, что 60% друзей проходят антифарм
                if rnd.random() < 0.6:
                    mod.PASSPORTS[uid]["xp"] += mod.REFERRAL_BONUS_XP
                    mod.maybe_unlock_citycode_grant(uid)
        xp = mod.PASSPORTS[uid]["xp"]
        for t in thresholds:
            if t not in reached and xp >= t:
                reached[t] = day
        if grant_day is None and mod.PASSPORTS[uid].get("complimentary_granted"):
            grant_day = day
        if len(reached) == len(thresholds):
            break
    return {"persona": persona, "reached": reached, "grant_day": grant_day,
            "xp_end": mod.PASSPORTS[uid]["xp"], "thresholds": thresholds}


def fmt_days(d):
    if d is None:
        return "> 6 лет"
    if d < 60:
        return f"{d} дн."
    return f"{d} дн. (~{d / 30.4:.0f} мес.)" if d < 730 else f"{d} дн. (~{d / 365:.1f} г.)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bot", default=os.path.join(os.path.dirname(__file__), "..", "..", "SevastopolAIbot"))
    ap.add_argument("--md", help="сохранить таблицу в markdown-файл")
    ap.add_argument("--proposal", action="store_true", help="прогнать с предложенной перекалибровкой")
    args = ap.parse_args()
    mod = load_bot(args.bot)
    if args.proposal:
        apply_proposal(mod)
    ranks = {t: name for t, name in zip(mod.XP_LEVELS, [r for _, r in mod.XP_RANKS][1:] + ["City Code"])}
    head = "| Профиль | " + " | ".join(f"{t} XP · {ranks[t]}" for t in mod.XP_LEVELS) + " |"
    sep = "|---" * (len(mod.XP_LEVELS) + 1) + "|"
    rows = [head, sep]
    for p in PERSONAS:
        r = simulate(mod, p)
        rows.append(f"| {p['name']} | " + " | ".join(fmt_days(r["reached"].get(t)) for t in mod.XP_LEVELS) + " |")
    out = "\n".join(rows)
    print(out)
    max_daily = sum(mod.XP_ACTIVITY_REWARDS.values())
    if args.proposal:
        max_daily = min(max_daily, PROPOSAL["daily_cap"])
    print(f"\nПотолок за кнопки: {max_daily} XP/день → 7000 XP минимум за {(7000 - 10 + max_daily - 1) // max_daily} дней")
    if args.md:
        with open(args.md, "w", encoding="utf-8") as f:
            f.write(out + "\n")


if __name__ == "__main__":
    sys.exit(main())
