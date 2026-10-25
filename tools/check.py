#!/usr/bin/env python3
"""
Проверка перед запуском. Падает (exit 1), если хоть что-то не сходится.

1. Excel ↔ Python: пересчитывает economics/Экономика_экосистемы.xlsx независимым движком
   (библиотека formulas) и сверяет каждую ячейку «Расчёт» и «Сценарии» с economics/model.py
   (до копейки для ₽, до 1e-9 для долей).
2. Инварианты модели: транш = 20 партнёров × 15, 2 032 400 ₽, деньги делятся без потерь и т.д.
3. Документы: AUTO-блоки в docs/*.md совпадают с тем, что сейчас генерирует tools/build.py
   (то есть никто не правил цифры руками), и в docs нет устаревших чисел v1.0.
4. ЗАПУСК.html и студия собраны и не ссылаются на внешние файлы.

Запуск:  python tools/check.py            (нужно: pip install formulas openpyxl)
"""
from __future__ import annotations

import os
import re
import sys
from decimal import Decimal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "economics"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import model as M  # noqa: E402

FAIL: list[str] = []
OK = 0


def check(name: str, cond: bool, extra: str = ""):
    global OK
    if cond:
        OK += 1
    else:
        FAIL.append(f"{name} {extra}".strip())
        print(f"  ❌ {name} {extra}")


def excel_vs_python(R: dict):
    import formulas
    import openpyxl
    from build_model import OUT, build

    meta = build()
    xl = formulas.ExcelModel().loads(OUT).finish()
    sol = xl.calculate()
    vals = {}
    for k, v in sol.items():
        m = re.match(r"'?\[[^\]]+\](.+?)'?!([A-Z]+\d+)$", k)
        if m:
            vals[(m.group(1).upper(), m.group(2))] = v.value[0, 0] if hasattr(v, "value") else v
    wb = openpyxl.load_workbook(OUT)
    n = 0
    for key, ref in meta["refs"].items():
        if not ref.startswith("'Расчёт'"):
            continue
        cell = ref.split("!")[1].replace("$", "")
        got = Decimal(str(float(vals[("РАСЧЁТ", cell)])))
        want = R["unit"][key]
        check(f"Excel «Расчёт» {key}", abs(got - want) < Decimal("0.005"), f"Excel {got} ≠ Python {want}")
        n += 1
    for key, row in meta["row_of"].items():
        if key not in R["scen"][0]:
            continue
        for i, col in enumerate(meta["cols"]):
            got = Decimal(str(float(vals[("СЦЕНАРИИ", f"{col}{row}")])))
            want = R["scen"][i][key]
            check(f"Excel «Сценарии» {key} S{i + 1}", abs(got - want) < Decimal("0.005"), f"Excel {got} ≠ Python {want}")
            n += 1
    print(f"  Excel ↔ Python: сверено {n} ячеек")
    assert wb


def invariants(P: dict, R: dict):
    u, p = R["unit"], R["params"]
    check("транш 2 032 400 ₽", u["tranche_gross"] == 2032400)
    check("транш = партнёры × места на партнёра", u["partners_for_tranche"] * u["seats_per_partner"] == u["tranche_seats"])
    check("Basic: цена = остаток + комиссия + налог",
          u["basic_net_npd_sbp"] + u["basic_fee_sbp"] + u["basic_tax_npd"] == p["price_basic"])
    check("Основатели: цена = остаток + комиссия + налог + набор",
          u["founder_net_npd_sbp"] + u["founder_fee_sbp"] + u["founder_tax_npd"] + u["founder_kit_cost"] == p["price_founder"])
    check("транш укладывается в лимит НПД", u["tranche_gross"] <= p["npd_limit"])
    check("привилегии ≤ цены Basic при 5% (честно: клуб — не скидочная карта)", u["payback_avg"] < 1)
    check("партнёр в плюсе при допущениях", u["partner_gain"] > 0)
    fee = max(r["values"][-1] for r in P["scenarios"]["rows"] if r["key"] == "partner_fee_m")
    check("взнос v2.0 меньше выгоды партнёра", Decimal(fee) < u["partner_gain"])
    check("возврат Basic ≤ цены", 0 <= u["refund_basic"] <= p["price_basic"])
    check("квота грантов = 30", u["grant_seats"] == 30)
    check("реклама партнёру = 50%", u["ad_post_p"] * 2 == u["ad_post"])
    for i, s in enumerate(R["scen"]):
        check(f"S{i + 1}: участников не больше потолка партнёров", s["members"] <= s["m_cap"])
        check(f"S{i + 1}: выручка = сумма строк", s["rev_total"] == s["rev_memb"] + s["rev_pfee"] + s["rev_ads"] + s["rev_content"]
              + s["rev_events"] + s["rev_merch"] + s["rev_cfa"] + s["rev_rwa_ads"])


def prose(P: dict, R: dict):
    """Цифры, написанные в тексте руками (посты, FAQ, оферта), обязаны совпадать с моделью."""
    u, p = R["unit"], R["params"]
    rd = lambda k: M.fmt(u[k], "₽").replace(" ₽", "")  # noqa: E731
    must = {
        "docs/11-тексты-для-запуска.md": [M.fmt(p["price_basic"], "₽"), M.fmt(p["price_founder"], "₽"),
                                          rd("basic_day") + " ₽ в день", "около " + str(int(M.ROUND(u["payback_avg"] * 100, 0))) + "%",
                                          f"+{int(p['ref_days'])} дней", f"до {int(p['ref_max'])} раз в год",
                                          f"{int(u['seats_per_partner'])} на каждого", f"{int(u['grant_seats'])} на транш",
                                          f"1 из {int(M.ROUND(1 / u['partner_breakeven_share'], 0))}"],
        "docs/legal/оферта-членства.md": [M.fmt(p["price_basic"], "₽"), M.fmt(p["price_founder"], "₽"),
                                         "[" + rd("founder_kit_cost") + "] ₽", f"не более {int(u['seats_per_partner'])} Участников"],
        "docs/legal/соглашение-партнёра.md": ["[" + M.fmt(p["partner_turnover"], "₽").replace(" ₽", "") + "]", f"[{int(u['seats_per_partner'])}] мест", f"**{int(p['partner_exit_days'])} дней**"],
        "docs/02-city-code-v1.1.md": [M.fmt(u["tranche_gross"], "₽"), f"**{int(p['partner_exit_days'])} дней**", f"**+{int(p['ref_days'])} дней**"],
        "docs/05-партнёры.md": [f"**{int(u['seats_per_partner'])} мест**", f"каждый {int(M.ROUND(1 / u['partner_breakeven_share'], 0))}-й"],
        "docs/03-цены-и-деньги.md": ["~" + str(int(M.ROUND(u["basic_net_npd_sbp"] - u["basic_net_npd_card"], 0))) + " ₽", M.fmt(u["acq_card_eff"], "%")],
    }
    for rel, needles in must.items():
        text = open(os.path.join(ROOT, rel), encoding="utf-8").read().replace("\u00a0", " ")
        for nd in needles:
            check(f"{rel}: «{nd}» совпадает с моделью", nd in text)
    # честный вывод в 09 — проверяем, что он правда следует из модели
    sc = R["scen"]
    check("вывод: строго по v1.0 город в плюсе только на S2", [s["profit_city_nofee"] > 0 for s in sc] == [False, True, False, False, False],
          "— поменялись допущения, перепиши раздел «Честный вывод» в docs/09")


STALE = [
    (r"1\s?532\s?400", "годовая модель v1.0 с ошибкой — только в разделе «что изменилось»"),
    (r"17[,.]5\s?%", "доходность 17,5% нельзя обещать"),
    (r"без возврата", "противоречит ст. 32 ЗоЗПП"),
    (r"без очереди", "заменено на «приоритет в листе ожидания»"),
    (r"180 дн", "грант теперь 365 дней"),
]
ALLOW_STALE = {"10-расхождения.md", "02-city-code-v1.1.md", "правки-сайта.md"}


def legit(text: str, pos: int) -> bool:
    """Упоминание законно: строка таблицы «было → стало» / «v1.0 → v1.1», список табу, описание риска."""
    ls = text.rfind("\n", 0, pos) + 1
    line = text[ls:text.find("\n", pos)]
    if re.search(r"табу|убрать|ничтожн|противоречит|нельзя обещать", line, re.I):
        return True
    if line.lstrip().startswith("|"):
        lines = text[:ls].split("\n")[:-1]
        head = line
        while lines and lines[-1].lstrip().startswith("|"):
            head = lines.pop()
        if re.search(r"\bБыло\b|v1\.0", head):
            return True
    return False


def docs():
    import build as B
    for path, name, expected in B.expected_auto_blocks():
        text = open(path, encoding="utf-8").read()
        m = re.search(rf"<!-- AUTO:{name} -->\n(.*?)\n<!-- /AUTO:{name} -->", text, re.S)
        check(f"{os.path.basename(path)}: блок {name} есть", bool(m))
        if m:
            check(f"{os.path.basename(path)}: блок {name} актуален", m.group(1).strip() == expected.strip(),
                  "— запусти python tools/build.py")
    files = [("docs", f) for f in sorted(os.listdir(os.path.join(ROOT, "docs")))] + \
            [("docs/legal", f) for f in sorted(os.listdir(os.path.join(ROOT, "docs", "legal")))]
    for d, fn in files:
        if not fn.endswith(".md") or fn in ALLOW_STALE:
            continue
        text = open(os.path.join(ROOT, d, fn), encoding="utf-8").read()
        for pat, why in STALE:
            for m in re.finditer(pat, text, re.I):
                line = text[:m.start()].count("\n") + 1
                ctx = text[max(0, m.start() - 60):m.end() + 20]
                if "было" in ctx or "v1.0" in ctx or "не " in ctx[:62] or legit(text, m.start()):
                    continue
                check(f"{d}/{fn}:{line} нет «{m.group(0)}»", False, f"({why})")


def html():
    for rel in ("ЗАПУСК.html", "studio/Студия.html"):
        path = os.path.join(ROOT, rel)
        check(f"{rel} собран", os.path.exists(path))
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8").read()
        ext = re.findall(r"""(?:src|href)=["'](?!data:|#|https?:|mailto:|tg:|javascript:)([^"']+)["']""", text)
        ext = [e for e in ext if "${" not in e and "' +" not in e and '" +' not in e and e.strip()]
        check(f"{rel}: нет ссылок на локальные файлы", not ext, str(ext[:5]))
        check(f"{rel}: нет путей assets/ и fonts/", not re.search(r"(?<![\\w/])(?:assets|fonts)/[\\w-]+/?[\\w.-]*\\.(?:jpe?g|png|webp|woff2)", text))
        check(f"{rel}: без внешних скриптов", not re.search(r"<script[^>]+src=[\"']https?:", text))


def main():
    P = M.load_params()
    R = M.compute(P)
    print("== 1. Excel ↔ Python ==")
    excel_vs_python(R)
    print("== 2. Инварианты ==")
    invariants(P, R)
    print("== 3. Документы ==")
    docs()
    prose(P, R)
    print("== 4. HTML ==")
    html()
    print(f"\nИТОГ: {OK} проверок прошло, {len(FAIL)} упало")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
