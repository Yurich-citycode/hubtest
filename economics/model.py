#!/usr/bin/env python3
"""
Модель экономики v1.1 — считает всё до копейки из economics/params.json.

Каждая формула записана ОДИН раз строкой вида "ROUND({price_basic}/12,2)".
Из этой строки получается:
  • точный расчёт в Python (Decimal, округление как в Excel — половина вверх);
  • живая формула в Excel (economics/build_model.py);
  • проверка: tools/check.py пересчитывает Excel независимым движком и сверяет с Python.

Запуск:  python economics/model.py        → economics/out/model.json + печать ключевых чисел
"""
from __future__ import annotations

import json
import os
import re
from decimal import ROUND_HALF_UP, Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
PARAMS = os.path.join(HERE, "params.json")
OUT_DIR = os.path.join(HERE, "out")

# (key, label, unit, formula, how) — unit: ₽ | % | шт | дн | раз | XP
UNIT = {
    "cc": ("Членство: цена в день, комиссия, налог, сколько остаётся", [
        ("basic_month", "Basic в месяц", "₽", "ROUND({price_basic}/12,2)", "цена ÷ 12"),
        ("basic_day", "Basic в день", "₽", "ROUND({price_basic}/{days_year},2)", "цена ÷ 365"),
        ("founder_month", "«Основатели» в месяц", "₽", "ROUND({price_founder}/12,2)", "цена ÷ 12"),
        ("founder_day", "«Основатели» в день", "₽", "ROUND({price_founder}/{days_year},2)", "цена ÷ 365"),
        ("acq_card_eff", "Карты: комиссия с НДС", "%", "{acq_card}*(1+{acq_vat})", "3,5% × 1,22"),
        ("acq_blend", "Комиссия в среднем (доля СБП из параметров)", "%", "{sbp_share}*{acq_sbp}+(1-{sbp_share})*{acq_card_eff}", "смесь СБП и карт"),
        ("basic_fee_sbp", "Basic: комиссия СБП", "₽", "ROUND({price_basic}*{acq_sbp},2)", "5 108 × 0,7%"),
        ("basic_fee_card", "Basic: комиссия карты", "₽", "ROUND({price_basic}*{acq_card_eff},2)", "5 108 × 4,27%"),
        ("basic_tax_npd", "Basic: налог НПД 4%", "₽", "ROUND({price_basic}*{npd_ind},2)", "с полной суммы"),
        ("basic_tax_usn", "Basic: налог УСН 6% (если ИП)", "₽", "ROUND({price_basic}*{usn},2)", "до вычета взносов"),
        ("basic_net_npd_sbp", "Basic: остаётся (НПД + СБП)", "₽", "{price_basic}-{basic_fee_sbp}-{basic_tax_npd}", "основной вариант"),
        ("basic_net_npd_card", "Basic: остаётся (НПД + карта)", "₽", "{price_basic}-{basic_fee_card}-{basic_tax_npd}", "если платят картой"),
        ("basic_net_usn_sbp", "Basic: остаётся (ИП УСН + СБП)", "₽", "{price_basic}-{basic_fee_sbp}-{basic_tax_usn}", "после перехода на ИП"),
        ("founder_kit_cost", "«Основатели»: себестоимость набора (паспорт + брелок)", "₽", "{passport_cost}+{keychain_cost}", "выдаём физически"),
        ("founder_kit_retail", "«Основатели»: набор по рознице", "₽", "{passport_price}+{keychain_price}", "что человек получает в рублях"),
        ("founder_fee_sbp", "«Основатели»: комиссия СБП", "₽", "ROUND({price_founder}*{acq_sbp},2)", ""),
        ("founder_tax_npd", "«Основатели»: налог НПД 4%", "₽", "ROUND({price_founder}*{npd_ind},2)", ""),
        ("founder_net_npd_sbp", "«Основатели»: остаётся (НПД + СБП − набор)", "₽", "{price_founder}-{founder_fee_sbp}-{founder_tax_npd}-{founder_kit_cost}", ""),
        ("founder_extra", "«Основатели» дороже Basic на", "₽", "{price_founder}-{price_basic}", ""),
        ("tranche_seats", "Мест в транше", "шт", "{seats_basic}+{seats_founder}", "250 + 50"),
        ("tranche_gross", "Транш: выручка", "₽", "{seats_basic}*{price_basic}+{seats_founder}*{price_founder}", "250 × 5 108 + 50 × 15 108"),
        ("tranche_net_npd_sbp", "Транш: остаётся (НПД + СБП − наборы)", "₽", "{seats_basic}*{basic_net_npd_sbp}+{seats_founder}*{founder_net_npd_sbp}", ""),
        ("npd_headroom", "Запас до лимита НПД в год продажи транша", "₽", "{npd_limit}-{tranche_gross}", "всё сверх — уже ИП"),
        ("v10_typo", "Ошибка годовой модели v1.0 (300 × 5 108)", "₽", "{tranche_gross}-{tranche_seats}*{price_basic}", "v1.0 недосчитал"),
    ]),
    "member": ("Честно для участника: сколько возвращают привилегии", [
        ("saving_min", "Экономия в год при 3%", "₽", "{spend}*12*{priv_min}", "7 000 × 12 × 3%"),
        ("saving_avg", "Экономия в год при 5%", "₽", "{spend}*12*{priv_avg}", "7 000 × 12 × 5%"),
        ("saving_max", "Экономия в год при 7%", "₽", "{spend}*12*{priv_max}", "7 000 × 12 × 7%"),
        ("payback_avg", "Привилегии при 5% возвращают от цены Basic", "%", "ROUND({saving_avg}/{price_basic},4)", "остальное — события и люди"),
        ("breakeven_min", "Basic окупается привилегиями при расходе (3%)", "₽", "ROUND({price_basic}/12/{priv_min},2)", "в месяц"),
        ("breakeven_avg", "Basic окупается привилегиями при расходе (5%)", "₽", "ROUND({price_basic}/12/{priv_avg},2)", "в месяц"),
        ("breakeven_max", "Basic окупается привилегиями при расходе (7%)", "₽", "ROUND({price_basic}/12/{priv_max},2)", "в месяц"),
        ("founder_breakeven_avg", "«Основатели» окупаются привилегиями при расходе (5%)", "₽", "ROUND({price_founder}/12/{priv_avg},2)", "в месяц — это статус, не скидка"),
    ]),
    "partner": ("Честно для партнёра: что стоит привилегия и что даёт клуб", [
        ("seats_per_partner", "Мест на одного партнёра", "шт", "FLOOR({partner_turnover}/{spend},1)", "доп. оборот ÷ расход участника (правило v1.0)"),
        ("partner_priv_cost", "Партнёр отдаёт привилегией в месяц", "₽", "{partner_turnover}*{priv_avg}", "оборот × 5%"),
        ("partner_new_profit", "Партнёр получает маржи с новых гостей в месяц", "₽", "{partner_turnover}*{partner_new_share}*{partner_margin}", "оборот × доля новых × маржа"),
        ("partner_gain", "Итог партнёра в месяц", "₽", "{partner_new_profit}-{partner_priv_cost}", ""),
        ("partner_gain_year", "Итог партнёра в год", "₽", "{partner_gain}*12", ""),
        ("partner_breakeven_share", "Партнёр в плюсе, если новых гостей не меньше", "%", "ROUND({priv_avg}/{partner_margin},4)", "привилегия ÷ маржа"),
        ("partners_for_founders", "Партнёров нужно, чтобы открыть 50 мест «Основатели»", "шт", "CEILING({seats_founder}/{seats_per_partner},1)", ""),
        ("partners_for_tranche", "Партнёров нужно на весь транш", "шт", "CEILING({tranche_seats}/{seats_per_partner},1)", "это два «С» логотипа"),
        ("seats_open", "Можно продать мест сейчас", "шт", "MIN({tranche_seats},{partners_signed}*{seats_per_partner})", "15 × подписанные партнёры"),
        ("club_turnover_full", "Оборот клуба у партнёров при 300 участниках", "₽", "{tranche_seats}*{spend}", "в месяц, это НЕ наш доход"),
    ]),
    "refund": ("Возврат (ст. 32 ЗоЗПП): пропорционально дням минус фактические расходы", [
        ("refund_days_left", "Пример: осталось дней", "дн", "{days_year}-{refund_days_used}", ""),
        ("refund_basic_unused", "Basic: стоимость неиспользованных дней", "₽", "ROUND({price_basic}*{refund_days_left}/{days_year},2)", ""),
        ("refund_basic", "Basic: к возврату", "₽", "MAX(0,{refund_basic_unused}-{basic_fee_sbp})", "минус комиссия, которую уже взяли"),
        ("refund_founder_unused", "«Основатели»: стоимость неиспользованных дней", "₽", "ROUND({price_founder}*{refund_days_left}/{days_year},2)", ""),
        ("refund_founder", "«Основатели»: к возврату", "₽", "MAX(0,{refund_founder_unused}-{founder_fee_sbp}-{founder_kit_cost})", "минус комиссия и себестоимость выданного набора"),
    ]),
    "xpmoney": ("XP и приглашения в рублях", [
        ("ref_bonus_value", "+30 дней за оплатившего приглашённого стоят", "₽", "ROUND({price_basic}*{ref_days}/{days_year},2)", "5 108 × 30 ÷ 365"),
        ("ref_bonus_share", "Это от цены Basic", "%", "ROUND({ref_bonus_value}/{price_basic},4)", "как комиссия за привод"),
        ("ref_bonus_year_max", "Максимум в год на одного участника (6 приглашённых)", "₽", "ROUND({price_basic}*{ref_days}*{ref_max}/{days_year},2)", ""),
        ("grant_value", "Грант за 7000 XP стоит", "₽", "ROUND({price_basic}*{grant_days}/{days_year},2)", "12 месяцев Basic"),
        ("grant_seats", "Грантов на транш максимум", "шт", "FLOOR({tranche_seats}*{grant_quota},1)", "10% мест"),
        ("grant_max_forgone", "Недополученная выручка, если все гранты заняты и транш продан", "₽", "{grant_seats}*{grant_value}", "раньше чем через ~14 месяцев не наступит"),
        ("grant_min_days", "Минимум дней одними кнопками до 7000", "дн", "CEILING(({xp_grant}-10)/{xp_daily_cap},1)", "старт паспорта = 10 XP"),
    ]),
    "ads": ("Реклама: цена = охват × CPM, но не ниже минимума", [
        ("ad_post", "Пост в канале", "₽", "MAX({ad_min_post},ROUND({ad_views_post}*{ad_cpm}/1000,-2))", "охват × CPM ÷ 1000, до сотни"),
        ("ad_post_p", "Пост — партнёру", "₽", "ROUND({ad_post}*(1-{ad_partner_disc}),2)", "−50%"),
        ("ad_card", "«Рекомендуем» в категории, 7 дней", "₽", "MAX({ad_min_card},ROUND({ad_views_card}*{ad_cpm}/1000,-2))", "показы × CPM ÷ 1000"),
        ("ad_card_p", "«Рекомендуем» — партнёру", "₽", "ROUND({ad_card}*(1-{ad_partner_disc}),2)", ""),
        ("ad_guide", "Подборка (3 места)", "₽", "{ad_guide_place}*{ad_guide_min}", "+1 000 за каждое место сверх"),
        ("ad_guide_p", "Подборка — партнёру", "₽", "ROUND({ad_guide}*(1-{ad_partner_disc}),2)", ""),
        ("ad_route_p", "Маршрут — партнёру", "₽", "ROUND({ad_route}*(1-{ad_partner_disc}),2)", ""),
        ("ad_event_p", "Анонс — партнёру (после бесплатного в месяц)", "₽", "ROUND({ad_event}*(1-{ad_partner_disc}),2)", ""),
        ("ad_post_net", "Пост: остаётся (НПД 6% с бизнеса + 3% сбор)", "₽", "{ad_post}-ROUND({ad_post}*{npd_biz},2)-ROUND({ad_post}*{ad_levy},2)", "оплата переводом, без эквайринга"),
        ("ad_post_p_net", "Пост партнёру: остаётся", "₽", "{ad_post_p}-ROUND({ad_post_p}*{npd_biz},2)-ROUND({ad_post_p}*{ad_levy},2)", ""),
        ("shoot_net", "Съёмка: остаётся", "₽", "{shoot_price}*(1-{shoot_cost})-ROUND({shoot_price}*{npd_biz},2)", "минус 40% оператору и 6%"),
        ("shoot_partner_net", "Съёмка партнёру: остаётся", "₽", "{shoot_partner}*(1-{shoot_cost})-ROUND({shoot_partner}*{npd_biz},2)", ""),
    ]),
    "merch": ("Мерч: только через ИП (самозанятый не может перепродавать товары)", [
        ("passport_net", "Физический паспорт: остаётся", "₽", "{passport_price}-ROUND({passport_price}*{acq_sbp},2)-ROUND({passport_price}*{usn},2)-{passport_cost}", "СБП, УСН 6%, себестоимость"),
        ("keychain_net", "Брелок: остаётся", "₽", "{keychain_price}-ROUND({keychain_price}*{acq_sbp},2)-ROUND({keychain_price}*{usn},2)-{keychain_cost}", ""),
        ("hoodie_net", "Худи: остаётся", "₽", "{hoodie_price}-ROUND({hoodie_price}*{acq_sbp},2)-ROUND({hoodie_price}*{usn},2)-{hoodie_cost}", ""),
    ]),
}

SCEN = [
    ("h", "CITY CODE", "", None),
    ("m_demand", "Спрос на членство", "чел", "{mau}*{conv}+{direct}"),
    ("m_cap", "Потолок по партнёрам (15 на точку)", "чел", "{partners}*{seats_per_partner}"),
    ("members", "Участников", "чел", "ROUND(MIN({m_demand},{m_cap}),0)"),
    ("founders", "  из них «Основатели»", "чел", "MIN({founder_cap},{members})"),
    ("basic", "  из них Basic", "чел", "{members}-{founders}"),
    ("rev_memb", "Выручка членства", "₽/мес", "({founders}*{price_founder}+{basic}*{price_basic})/12"),
    ("net_turn", "Оборот клуба у партнёров (не наш доход)", "₽/мес", "{members}*{spend}"),
    ("turn_pp", "  на одного партнёра", "₽/мес", "{net_turn}/{partners}"),
    ("h", "ДРУГИЕ ДОХОДЫ", "", None),
    ("rev_pfee", "Взнос партнёров v2.0 (если решишь)", "₽/мес", "{partners}*{partner_fee_m}"),
    ("ad_check", "Средний чек размещения", "₽", "MAX({ad_min_post},ROUND({ads_views}*{ad_cpm}/1000,-2))*(1-{ads_partner_share}*{ad_partner_disc})"),
    ("rev_ads", "Реклама SAI", "₽/мес", "{ads_n}*{ad_check}"),
    ("rev_content", "Съёмки", "₽/мес", "{shoots_n}*{shoot_price}"),
    ("rev_events", "События", "₽/мес", "{ev_n}*{ev_people}*{ev_ticket}"),
    ("rev_merch", "Мерч", "₽/мес", "({members}*{mr_members}+{mau}*{mr_mau})*{m_check}"),
    ("rev_cfa", "ЦФА-услуги (среднемесячно)", "₽/мес", "({cfa_rev_n}*80000+{cfa_build_n}*325000)/12"),
    ("rev_rwa_ads", "Реклама YuRichRWA", "₽/мес", "{rwa_subs}*{rwa_view}*{rwa_cpm}/1000*{rwa_posts}"),
    ("rev_total", "ВСЯ ВЫРУЧКА", "₽/мес", "{rev_memb}+{rev_pfee}+{rev_ads}+{rev_content}+{rev_events}+{rev_merch}+{rev_cfa}+{rev_rwa_ads}"),
    ("rev_year", "Выручка за год", "₽/год", "{rev_total}*12"),
    ("h", "РАСХОДЫ", "", None),
    ("c_ai", "AI (Кира)", "₽/мес", "{mau}*{ai_mau}"),
    ("c_acq", "Приём платежей", "₽/мес", "{acq_blend}*({rev_memb}+{rev_events}+{rev_merch})"),
    ("c_cogs", "Себестоимость событий, мерча, съёмок", "₽/мес", "{rev_events}*{ev_cost}+{rev_merch}*{merch_cogs}+{rev_content}*{shoot_cost}"),
    ("c_adlevy", "Сбор 3% с рекламы", "₽/мес", "{ad_levy}*({rev_ads}+{rev_rwa_ads})"),
    ("c_ipfee", "Взносы ИП за себя", "₽/мес", "({ip_fixed}+MAX(0,{rev_year}-{ip_extra_from})*{ip_extra})/12"),
    ("c_tax", "УСН 6% минус взносы", "₽/мес", "MAX(0,{rev_total}*{usn}-{c_ipfee})"),
    ("c_total", "ВСЕ РАСХОДЫ", "₽/мес", "{c_infra}+{c_ai}+{c_team}+{c_mkt}+{c_legal}+{c_ipr}+{c_ipfee}+{c_acq}+{c_cogs}+{c_adlevy}+{c_tax}"),
    ("h", "РЕЗУЛЬТАТ", "", None),
    ("profit", "Прибыль в месяц (без зарплаты основателя)", "₽/мес", "{rev_total}-{c_total}"),
    ("profit_year", "Прибыль за год", "₽/год", "{profit}*12"),
    ("profit_city", "Прибыль города без ЦФА-услуг", "₽/мес", "{profit}-{rev_cfa}*(1-{usn})"),
    ("profit_city_nofee", "  …и без взноса партнёров (строго v1.0)", "₽/мес", "{profit_city}-{rev_pfee}*(1-{usn})"),
    ("l_total", "Часов работы в месяц", "ч", "({mau}*0.02+{members}*0.1)*0.25+{partners}*3+{mau}*0.01*0.2+{l_content}+{ev_n}*12"),
    ("fte", "Людей на полный день (160 ч)", "чел", "{l_total}/160"),
]


# ── вычислитель: та же строка формулы, что уходит в Excel ─────────────────
def D(x) -> Decimal:
    return x if isinstance(x, Decimal) else Decimal(str(x))


def ROUND(x, n):
    return D(x).quantize(Decimal(1).scaleb(-int(n)), rounding=ROUND_HALF_UP)


def FLOOR(x, s):
    x, s = D(x), D(s)
    return (x / s).to_integral_value(rounding="ROUND_FLOOR") * s


def CEILING(x, s):
    x, s = D(x), D(s)
    return (x / s).to_integral_value(rounding="ROUND_CEILING") * s


def MAX(*a):
    return max(D(v) for v in a)


def MIN(*a):
    return min(D(v) for v in a)


KEY_RE = re.compile(r"\{(\w+)\}")
NUM_RE = re.compile(r"(?<![\w\"'.])(\d+(?:\.\d+)?)(?![\w\"'.])")


def to_python(formula: str) -> str:
    expr = NUM_RE.sub(r'D("\1")', formula)
    return KEY_RE.sub(lambda m: f'V["{m.group(1)}"]', expr)


def evaluate(formula: str, V: dict) -> Decimal:
    return D(eval(to_python(formula), {"D": D, "ROUND": ROUND, "FLOOR": FLOOR, "CEILING": CEILING,
                                        "MAX": MAX, "MIN": MIN}, {"V": V}))


def load_params(path: str = PARAMS) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def flat_params(P: dict) -> dict:
    return {it["key"]: D(it["value"]) for g in P["groups"] for it in g["items"]}


def compute(P: dict | None = None) -> dict:
    P = P or load_params()
    V = flat_params(P)
    unit = {}
    for gid, (title, rows) in UNIT.items():
        for key, label, u, f, how in rows:
            V[key] = evaluate(f, V)
            unit[key] = V[key]
    n = len(P["scenarios"]["names"])
    scen = []
    for i in range(n):
        S = dict(V)
        for r in P["scenarios"]["rows"]:
            S[r["key"]] = D(r["values"][i])
        for key, label, u, f in SCEN:
            if f:
                S[key] = evaluate(f, S)
        scen.append({k: S[k] for k, _, _, f in SCEN if f})
    return {"params": V, "unit": unit, "scen": scen}


# ── форматирование для docs и HTML ───────────────────────────────────────
def fmt(v, unit: str) -> str:
    v = D(v)
    if unit == "%":
        s = f"{(v * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):f}".rstrip("0").rstrip(".")
        return s.replace(".", ",") + "%"
    if unit in ("₽", "₽/мес", "₽/год"):
        q = v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        whole, frac = f"{q:.2f}".split(".")
        sign = "−" if whole.startswith("-") else ""
        whole = whole.lstrip("-")
        whole = f"{int(whole):,}".replace(",", " ")
        return f"{sign}{whole},{frac} ₽" if frac != "00" else f"{sign}{whole} ₽"
    if v == v.to_integral_value():
        return f"{int(v):,}".replace(",", " ") + (f" {unit}" if unit not in ("", "раз") else "")
    return f"{v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}".replace(".", ",") + (f" {unit}" if unit else "")


def md_unit(R: dict, gid: str) -> str:
    title, rows = UNIT[gid]
    out = ["| Показатель | Сумма | Как считается |", "|---|---:|---|"]
    for key, label, u, f, how in rows:
        out.append(f"| {label} | **{fmt(R['unit'][key], u)}** | {how} |")
    return "\n".join(out)


def md_scen(P: dict, R: dict, keys=None) -> str:
    names = P["scenarios"]["names"]
    out = ["| | " + " | ".join(names) + " |", "|---" + "|---:" * len(names) + "|"]
    for key, label, u, f in SCEN:
        if not f or (keys and key not in keys):
            continue
        vals = []
        for s in R["scen"]:
            v = s[key]
            if u in ("₽/мес", "₽/год", "₽"):
                vals.append(fmt(ROUND(v, 0), "₽"))
            elif u == "чел" and key == "fte":
                vals.append(fmt(ROUND(v, 2), ""))
            else:
                vals.append(fmt(ROUND(v, 0), ""))
        out.append(f"| {label} | " + " | ".join(vals) + " |")
    return "\n".join(out)


def md_params(P: dict, gid: str) -> str:
    g = next(g for g in P["groups"] if g["id"] == gid)
    mark = {"fact": "✅ факт", "decision": "📌 решение", "assumption": "🧪 допущение"}
    out = ["| Параметр | Значение | Статус | Источник |", "|---|---:|---|---|"]
    for it in g["items"]:
        u = it["unit"] if it["unit"] != "₽/мес" else "₽"
        val = fmt(it["value"], "%" if it["unit"] == "%" else ("₽" if it["unit"].startswith("₽") else it["unit"]))
        if it["unit"] in ("₽/мес", "₽/год"):
            val += it["unit"][1:]
        out.append(f"| {it['label']} | {val} | {mark[it['status']]} | {it['src']} |")
    return "\n".join(out)


def to_json(P: dict, R: dict) -> dict:
    labels = {}
    for gid, (title, rows) in UNIT.items():
        for key, label, u, f, how in rows:
            labels[key] = {"label": label, "unit": u, "formula": f, "how": how, "group": gid}
    return {
        "version": P["version"], "updated": P["updated"],
        "params": P,
        "unit": {k: float(v) for k, v in R["unit"].items()},
        "unit_meta": labels,
        "unit_groups": {gid: title for gid, (title, _) in UNIT.items()},
        "scen": [{k: float(v) for k, v in s.items()} for s in R["scen"]],
        "scen_meta": [{"key": k, "label": l, "unit": u, "formula": f} for k, l, u, f in SCEN],
    }


def main():
    P = load_params()
    R = compute(P)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "model.json"), "w", encoding="utf-8") as f:
        json.dump(to_json(P, R), f, ensure_ascii=False, indent=1)
    for gid in UNIT:
        print(f"\n## {UNIT[gid][0]}\n" + md_unit(R, gid))
    print("\n## Сценарии\n" + md_scen(P, R))


if __name__ == "__main__":
    main()
