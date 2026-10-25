#!/usr/bin/env python3
"""
Симулятор XP City Passport на НАСТОЯЩЕМ коде бота.

Не копирует константы руками: импортирует sevastopolaibot.py из репозитория
SevastopolAIbot, подменяет часы (datetime) и прогоняет типовых пользователей
день за днём. Так видно, через сколько дней реально берутся пороги
100 / 300 / 800 / 2000 / 4000 / 7000 XP и когда открывается грант City Code.

Запуск (из корня hubtest):
    git clone https://github.com/Yurich-citycode/SevastopolAIbot.git ../SevastopolAIbot
    pip install "aiogram>=3.7,<4" pandas openpyxl requests python-dotenv
    python economics/xp_simulator.py --bot ../SevastopolAIbot                       # бот как есть
    python economics/xp_simulator.py --bot ../SevastopolAIbot --bot-before /path/v1.0  # сравнение
Результат: economics/out/xp_sim.json (его читают tools/build.py и ЗАПУСК.html).

Профили описаны в PERSONAS ниже — меняй частоты и смотри, как сдвигаются сроки.
"""
from __future__ import annotations

import argparse
import json
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


def run(bot_path: str) -> dict:
    mod = load_bot(bot_path)
    names = [r for _, r in mod.XP_RANKS][1:] + ["City Code"]
    res = {"thresholds": list(mod.XP_LEVELS), "ranks": dict(zip(map(str, mod.XP_LEVELS), names)),
           "grant_days": getattr(mod, "CITYCODE_GRANT_DAYS", None),
           "daily_cap": getattr(mod, "DAILY_ACTIVITY_CAP", sum(mod.XP_ACTIVITY_REWARDS.values())),
           "activity": dict(mod.XP_ACTIVITY_REWARDS), "verified": dict(mod.XP_VERIFIED_REWARDS),
           "referral": [mod.REFERRAL_XP, mod.REFERRAL_BONUS_XP], "personas": []}
    for p in PERSONAS:
        r = simulate(mod, p)
        res["personas"].append({"key": p["key"], "name": p["name"],
                                "days": {str(t): r["reached"].get(t) for t in mod.XP_LEVELS}})
    return res


def table(res: dict) -> str:
    th = res["thresholds"]
    rows = ["| Профиль | " + " | ".join(f"{t} · {res['ranks'][str(t)]}" for t in th) + " |",
            "|---" * (len(th) + 1) + "|"]
    for p in res["personas"]:
        rows.append(f"| {p['name']} | " + " | ".join(fmt_days(p["days"][str(t)]) for t in th) + " |")
    return "\n".join(rows)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--bot", default=os.path.join(here, "..", "..", "SevastopolAIbot"), help="бот после патча (v1.1)")
    ap.add_argument("--bot-before", help="бот до патча (v1.0) — для сравнения")
    ap.add_argument("--json", default=os.path.join(here, "out", "xp_sim.json"))
    args = ap.parse_args()
    out = {"v11": run(args.bot)}
    if args.bot_before:
        out["v10"] = run(args.bot_before)
    os.makedirs(os.path.dirname(args.json), exist_ok=True)
    with open(args.json, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for k, v in out.items():
        print(f"\n## {k}\n" + table(v))


if __name__ == "__main__":
    main()
