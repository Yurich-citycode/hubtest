#!/usr/bin/env python3
"""
Собирает economics/Экономика_экосистемы.xlsx из params.json и формул economics/model.py.

Все расчётные ячейки — живые формулы Excel. Меняешь жёлтую ячейку в листе «Параметры»
или «Сценарии» — Excel пересчитает всё сам. Но источник правды — params.json:
после правки в Excel перенеси число в params.json, иначе docs и ЗАПУСК.html разойдутся.

Запуск:  python economics/build_model.py
Проверка: python tools/check.py  (пересчитывает Excel независимым движком и сверяет с model.py)
"""
from __future__ import annotations

import json
import os
import re
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model as M  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Экономика_экосистемы.xlsx")
YELLOW = PatternFill("solid", fgColor="FFF4C2")
GREEN = PatternFill("solid", fgColor="EAF7C8")
DARK = PatternFill("solid", fgColor="111111")
SUB = PatternFill("solid", fgColor="2B2B2B")
WHITE = Font(bold=True, color="FFFFFF")
LIME = Font(bold=True, color="D7FF3D")
GREY = Font(color="777777", size=9)

FMT = {"₽": '#,##0.00" ₽"', "₽/мес": '#,##0" ₽"', "₽/год": '#,##0" ₽"', "%": "0.00%", "шт": "#,##0",
       "дн": "#,##0", "чел": "#,##0", "XP": "#,##0", "ч": "#,##0", "просм.": "#,##0", "показ": "#,##0"}


def excel_formula(formula: str, ref) -> str:
    return "=" + M.KEY_RE.sub(lambda m: ref(m.group(1)), formula)


def build() -> dict:
    P = M.load_params()
    R = M.compute(P)
    wb = Workbook()
    refs: dict[str, str] = {}

    # ── README
    ws = wb.active
    ws.title = "Как читать"
    lines = [
        ("Экономика SevastopolAI · City Code · YuRichRWA — v" + P["version"] + " от " + P["updated"], True),
        ("Источник правды — economics/params.json. Этот файл собирается скриптом economics/build_model.py.", False),
        ("Жёлтое — вводные (можно менять здесь, но потом перенеси в params.json). Зелёное — итоги. Всё остальное — формулы.", False),
        ("Проверка: python tools/check.py — пересчитывает этот файл независимым движком и сверяет с economics/model.py до копейки.", False),
        ("Оборот партнёров ≠ наша выручка. Сценарии — модель, не факт. Зарплата основателя не учтена.", False),
        ("", False),
        ("Листы: Параметры → Расчёт (юнит-экономика до копейки) → Сценарии S1–S5 → XP → Доли партнёров.", False),
    ]
    for i, (t, b) in enumerate(lines, start=1):
        ws.cell(i, 1, t).font = Font(bold=b, size=14 if b else 11)
    ws.column_dimensions["A"].width = 130

    # ── Параметры
    wp = wb.create_sheet("Параметры")
    wp.append(["Ключ", "Параметр", "Ед.", "Значение", "Статус", "Источник"])
    for c in range(1, 7):
        wp.cell(1, c).font, wp.cell(1, c).fill = WHITE, DARK
    r = 2
    status = {"fact": "факт", "decision": "решение", "assumption": "допущение"}
    for g in P["groups"]:
        wp.cell(r, 2, g["title"]).font = LIME
        for c in range(1, 7):
            wp.cell(r, c).fill = SUB
        r += 1
        for it in g["items"]:
            wp.cell(r, 1, it["key"]).font = GREY
            wp.cell(r, 2, it["label"])
            wp.cell(r, 3, it["unit"])
            cell = wp.cell(r, 4, it["value"])
            cell.fill = YELLOW
            cell.number_format = FMT.get(it["unit"], "#,##0.##")
            wp.cell(r, 5, status[it["status"]])
            wp.cell(r, 6, it["src"]).font = GREY
            refs[it["key"]] = f"'Параметры'!$D${r}"
            r += 1
    for col, w in zip("ABCDEF", (18, 58, 8, 16, 12, 70)):
        wp.column_dimensions[col].width = w
    wp.freeze_panes = "A2"

    # ── Расчёт
    wu = wb.create_sheet("Расчёт")
    wu.append(["Ключ", "Показатель", "Ед.", "Значение", "Как считается", "Формула"])
    for c in range(1, 7):
        wu.cell(1, c).font, wu.cell(1, c).fill = WHITE, DARK
    r = 2
    for gid, (title, rows) in M.UNIT.items():
        wu.cell(r, 2, title).font = LIME
        for c in range(1, 7):
            wu.cell(r, c).fill = SUB
        r += 1
        for key, label, u, f, how in rows:
            refs[key] = f"'Расчёт'!$D${r}"
            r += 1
    r = 2
    for gid, (title, rows) in M.UNIT.items():
        r += 1
        for key, label, u, f, how in rows:
            wu.cell(r, 1, key).font = GREY
            wu.cell(r, 2, label)
            wu.cell(r, 3, u)
            cell = wu.cell(r, 4, excel_formula(f, lambda k: refs[k].replace("'Расчёт'!", "")))
            cell.number_format = FMT.get(u, "#,##0.00")
            cell.fill = GREEN
            wu.cell(r, 5, how).font = GREY
            wu.cell(r, 6, f).font = GREY
            r += 1
    for col, w in zip("ABCDEF", (22, 62, 6, 18, 44, 70)):
        wu.column_dimensions[col].width = w
    wu.freeze_panes = "A2"

    # ── Сценарии
    wsn = wb.create_sheet("Сценарии")
    S = P["scenarios"]
    cols = [get_column_letter(3 + i) for i in range(len(S["names"]))]
    wsn.cell(1, 1, "Сценарии роста. Жёлтое — вводные сценария; цены, налоги и комиссии берутся из «Параметры» и «Расчёт».").font = Font(italic=True, color="666666")
    wsn.cell(3, 1, "Показатель")
    wsn.cell(3, 2, "Ед.")
    for i, n in enumerate(S["names"]):
        wsn.cell(3, 3 + i, n)
        wsn.cell(4, 3 + i, S["subs"][i]).font = Font(italic=True, color="666666", size=9)
    for c in range(1, 4 + len(cols)):
        wsn.cell(3, c).font, wsn.cell(3, c).fill = WHITE, DARK
    row_of: dict[str, int] = {}
    r = 5
    wsn.cell(r, 1, "ВВОДНЫЕ СЦЕНАРИЯ").font = LIME
    for c in range(1, 4 + len(cols)):
        wsn.cell(r, c).fill = SUB
    r += 1
    for it in S["rows"]:
        row_of[it["key"]] = r
        wsn.cell(r, 1, it["label"])
        wsn.cell(r, 2, it["unit"])
        wsn.cell(r, 3 + len(cols), it.get("note", "")).font = GREY
        for i, v in enumerate(it["values"]):
            cell = wsn.cell(r, 3 + i, v)
            cell.fill = YELLOW
            cell.number_format = FMT.get(it["unit"], "#,##0.###")
        r += 1
    calc_start = r
    for key, label, u, f in M.SCEN:
        if f:
            row_of[key] = r
        r += 1
    r = calc_start
    for key, label, u, f in M.SCEN:
        if not f:
            wsn.cell(r, 1, label).font = LIME
            for c in range(1, 4 + len(cols)):
                wsn.cell(r, c).fill = SUB
            r += 1
            continue
        wsn.cell(r, 1, label)
        wsn.cell(r, 2, u)
        for i, col in enumerate(cols):
            def ref(k, col=col):
                return f"{col}{row_of[k]}" if k in row_of else refs[k]
            cell = wsn.cell(r, 3 + i, excel_formula(f, ref))
            cell.number_format = FMT.get(u, "#,##0.00") if key != "fte" else "0.00"
            if label.isupper() or key in ("members", "profit", "profit_city", "fte"):
                cell.fill = GREEN
                wsn.cell(r, 1).font = Font(bold=True)
        r += 1
    wsn.column_dimensions["A"].width = 50
    wsn.column_dimensions["B"].width = 8
    for col in cols:
        wsn.column_dimensions[col].width = 17
    wsn.column_dimensions[get_column_letter(3 + len(cols))].width = 50
    wsn.freeze_panes = "C5"

    build_xp(wb)
    build_shares(wb)
    wb.save(OUT)
    return {"refs": refs, "row_of": row_of, "cols": cols}


def build_xp(wb):
    ws = wb.create_sheet("XP")
    path = os.path.join(HERE, "out", "xp_sim.json")
    ws.cell(1, 1, "Дней до порога XP — прогон типовых людей на НАСТОЯЩЕМ коде бота (economics/xp_simulator.py)").font = Font(bold=True, size=13)
    if not os.path.exists(path):
        ws.cell(3, 1, "Нет economics/out/xp_sim.json — запусти xp_simulator.py")
        return
    sim = json.load(open(path, encoding="utf-8"))
    r = 3
    for ver, title in (("v11", "v1.1 — после патча бота"), ("v10", "v1.0 — код бота до патча")):
        if ver not in sim:
            continue
        res = sim[ver]
        ws.cell(r, 1, title).font = Font(bold=True)
        r += 1
        ws.cell(r, 1, "Профиль")
        for i, t in enumerate(res["thresholds"]):
            ws.cell(r, 2 + i, f"{t} · {res['ranks'][str(t)]}")
        for c in range(1, 2 + len(res["thresholds"])):
            ws.cell(r, c).font, ws.cell(r, c).fill = WHITE, DARK
        r += 1
        for p in res["personas"]:
            ws.cell(r, 1, p["name"])
            for i, t in enumerate(res["thresholds"]):
                d = p["days"][str(t)]
                ws.cell(r, 2 + i, d if d is not None else "> 6 лет")
            r += 1
        r += 1
    ws.column_dimensions["A"].width = 70
    for i in range(2, 9):
        ws.column_dimensions[get_column_letter(i)].width = 18


def build_shares(wb):
    ws = wb.create_sheet("Доли партнёров")
    ws["A1"] = "Калькулятор долей: динамическая модель (Slicing Pie)"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = ("Вклад считается по рыночной цене. Неоплаченное время и ресурсы ×2, живые деньги ×4 (риск выше). "
                "Доля = вклад участника / сумма вкладов. Итог — ориентир для переговоров, а не автоматическое решение.")
    ws["A2"].alignment = Alignment(wrap_text=True)
    ws.merge_cells("A2:I2")
    ws.row_dimensions[2].height = 45
    head = ["Участник", "Роль", "Неоплач. время, ₽/мес (рынок)", "Ресурсы, ₽/мес (аренда по рынку)",
            "Месяцев", "Разовый вклад (IP, оборудование), ₽", "Деньги, ₽", "Вклад (слайсы)", "Доля"]
    ws.append([])
    ws.append(head)
    for c in range(1, 10):
        ws.cell(4, c).font, ws.cell(4, c).fill = WHITE, DARK
        ws.cell(4, c).alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[4].height = 48
    people = [
        ("YuRich (основатель)", "Продукт, бренд, бот, база, сайт, продажи", 150000, 0, 12, 1500000, 300000),
        ("Партнёр по оборудованию и контенту", "Камера, свет, звук, монтаж, съёмки", 0, 40000, 12, 0, 0),
        ("Партнёр по событиям и офису", "Площадка для событий, рабочее место", 0, 60000, 12, 0, 0),
        ("(резерв) Технический партнёр", "Разработка, сервер", 0, 0, 0, 0, 0),
    ]
    for i, p in enumerate(people):
        r = 5 + i
        for c, v in enumerate(p, start=1):
            cell = ws.cell(r, c, v)
            if c >= 3:
                cell.fill = YELLOW
                cell.number_format = "#,##0"
        ws.cell(r, 8, f"=2*(C{r}+D{r})*E{r}+2*F{r}+4*G{r}").number_format = "#,##0"
        ws.cell(r, 9, f"=IF(SUM($H$5:$H$8)=0,0,H{r}/SUM($H$5:$H$8))").number_format = "0.0%"
    ws.cell(9, 7, "Итого").font = Font(bold=True)
    ws.cell(9, 8, "=SUM(H5:H8)").number_format = "#,##0"
    ws.cell(9, 9, "=SUM(I5:I8)").number_format = "0.0%"
    ws.cell(11, 1, "Ограничители (рекомендация)").font = Font(bold=True)
    rules = [
        "1. Пул стратегических партнёров — не больше 10–15% на всех. Если калькулятор даёт больше — излишек платим revenue share, а не долей.",
        "2. Вестинг 24–36 месяцев, первые 6–12 месяцев «клифф»: ушёл раньше — доли нет, вклад закрываем выплатами по выручке.",
        "3. Доля возможна только в юрлице (ООО). Пока ты физлицо/ИП — опционный договор (ст. 429.2 ГК) или договор о выручке.",
        "4. Доля — в той компании, где лежат права (товарные знаки, ПО, база). Не дробить на «долю в боте» и «долю в клубе».",
        "5. Revenue share вместо доли: партнёру по оборудованию — 40% выручки со съёмок (= shoot_cost в params.json), площадке — 50% чистой выручки события.",
    ]
    for i, t in enumerate(rules):
        ws.cell(12 + i, 1, t).alignment = Alignment(wrap_text=True)
        ws.merge_cells(start_row=12 + i, start_column=1, end_row=12 + i, end_column=9)
        ws.row_dimensions[12 + i].height = 32
    for i, w in enumerate([34, 36, 18, 18, 10, 20, 14, 16, 10], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


if __name__ == "__main__":
    build()
    print("OK →", OUT)
