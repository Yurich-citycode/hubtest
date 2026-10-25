#!/usr/bin/env python3
"""
Сборка всего из одного источника — economics/params.json.

    python tools/build.py

Что делает (по порядку):
  1. economics/model.py      → economics/out/model.json (все расчёты до копейки)
  2. economics/build_model.py → economics/Экономика_экосистемы.xlsx (живые формулы)
  3. docs/**/*.md            → заполняет блоки <!-- AUTO:имя --> … <!-- /AUTO:имя --> свежими цифрами
  4. ЗАПУСК.html             → один рабочий файл: чек-лист, калькуляторы, сценарии, XP, тексты, все документы
  5. studio/Студия.html      → студия шаблонов одним файлом (шрифты, картинки, скрипты внутри)

Зависимости: openpyxl (для Excel). Проверка после сборки: python tools/check.py
"""
from __future__ import annotations

import base64
import hashlib
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "economics"))
import model as M  # noqa: E402

XP_JSON = os.path.join(ROOT, "economics", "out", "xp_sim.json")
MODEL_JSON = os.path.join(ROOT, "economics", "out", "model.json")
DOC_DIRS = ["docs", "docs/legal"]


# ═════════════════════════ AUTO-блоки ═════════════════════════
def F(R, key):
    """Значение показателя из модели в формате документа."""
    meta = {k: (u) for g in M.UNIT.values() for k, _, u, _, _ in g[1]}
    return M.fmt(R["unit"][key], meta[key])


def P_(R, key, unit="₽"):
    return M.fmt(R["params"][key], unit)


def md_key(P, R):
    u = lambda k: F(R, k)  # noqa: E731
    p = R["params"]
    seats_open = int(R["unit"]["seats_open"])
    n = lambda k: int(R["unit"][k])  # noqa: E731
    lines = [
        f"- **Цены (v1.0, не меняются):** Basic {P_(R, 'price_basic')} в год ({u('basic_day')} в день), «Основатели» {P_(R, 'price_founder')} в год ({u('founder_day')} в день). Только годом.",
        f"- **Остаётся тебе с одного Basic:** {u('basic_net_npd_sbp')} (самозанятый + СБП) · {u('basic_net_npd_card')} (если картой) · {u('basic_net_usn_sbp')} (ИП + СБП).",
        f"- **«Основатели»:** остаётся {u('founder_net_npd_sbp')} после налога, комиссии и набора (себестоимость набора {u('founder_kit_cost')}, по рознице {u('founder_kit_retail')}).",
        f"- **Места:** {n('seats_per_partner')} на партнёра. Подписано партнёров: {int(p['partners_signed'])} → можно продать **{seats_open} мест**. «Основатели» открываются с {n('partners_for_founders')} партнёров, весь транш — {n('partners_for_tranche')} партнёров.",
        f"- **Транш 300 мест:** {u('tranche_gross')} выручки, остаётся {u('tranche_net_npd_sbp')}. До лимита самозанятого (2,4 млн ₽ в год) запас {u('npd_headroom')} — реклама и ЦФА уже через ИП.",
        f"- **Партнёр** (при допущениях ниже): отдаёт привилегией {u('partner_priv_cost')} в месяц, получает маржи с новых гостей {u('partner_new_profit')} → **{u('partner_gain')} в месяц**. В плюсе, если новых гостей хотя бы {u('partner_breakeven_share')}.",
        f"- **Участник:** привилегии при 5% возвращают {u('payback_avg')} цены Basic ({u('saving_avg')} в год при расходе {P_(R, 'spend')} в месяц). Остальное — люди и события. Так и говорим.",
        f"- **Возврат** через {int(p['refund_days_used'])} дней: Basic {u('refund_basic')}, «Основатели» {u('refund_founder')}.",
        f"- **Реклама:** пост {u('ad_post')} (партнёру {u('ad_post_p')}), остаётся {u('ad_post_net')}. Без договора с ОРД и erid — ни одной рекламы.",
        f"- **XP:** 7000 XP = Basic на год ({u('grant_value')}), не больше {n('grant_seats')} грантов на транш. Пригласил оплатившего — +30 дней ({u('ref_bonus_value')}).",
    ]
    return "\n".join(lines)


def md_price_list(P, R):
    u = lambda k: F(R, k)  # noqa: E731
    rows = [
        ("Членство Basic, 12 месяцев", P_(R, "price_basic"), "—", "Участник", "НПД или ИП · СБП"),
        ("Членство «Основатели», 12 месяцев", P_(R, "price_founder"), "—", "Участник", "НПД или ИП · СБП · набор — после ИП"),
        ("Вход партнёра в первый транш", P_(R, "partner_fee"), "—", "—", "без комиссии клубу"),
        ("Пост в канале Sevastopol AI (охват × CPM, не ниже минимума)", u("ad_post"), u("ad_post_p"), "Бизнес", "ОРД + erid"),
        ("«Рекомендуем» в категории бота, 7 дней", u("ad_card"), u("ad_card_p"), "Бизнес", "ОРД + erid"),
        (f"Подборка ({int(R['params']['ad_guide_min'])} места, +{P_(R, 'ad_guide_place')} за каждое сверх)", u("ad_guide"), u("ad_guide_p"), "Бизнес", "ОРД + erid"),
        ("Включение в маршрут (только если место реально по пути)", P_(R, "ad_route"), u("ad_route_p"), "Бизнес", "ОРД + erid"),
        ("Анонс события", P_(R, "ad_event"), f"1-й в месяц бесплатно, далее {u('ad_event_p')}", "Бизнес", "ОРД + erid (бесплатный тоже)"),
        (f"Съёмка заведения ({M.fmt(R['params']['shoot_cost'], '%')} — оператору и технике)", P_(R, "shoot_price"), P_(R, "shoot_partner"), "Бизнес", "ИП"),
        ("Паспорт-книжка", P_(R, "passport_price"), "—", "Участник", "только ИП (товар)"),
        ("Брелок «6 ключей»", P_(R, "keychain_price"), "—", "Участник", "только ИП"),
        ("Худи (участникам −10%)", P_(R, "hoodie_price"), "—", "Участник", "только ИП, предзаказ"),
        ("ЦФА: разбор / сборка / посадка на площадку / сопровождение", "80 000 ₽ / 250–400 тыс. ₽ / 200–350 тыс. ₽ / 40 000 ₽ в мес.", "—", "Бизнес", "ИП"),
    ]
    out = ["| Что | Цена | Партнёру City Code | Кто платит | Как |", "|---|---:|---:|---|---|"]
    out += [f"| {a} | **{b}** | {c} | {d} | {e} |" for a, b, c, d, e in rows]
    return "\n".join(out)


def md_scen_inputs(P):
    S = P["scenarios"]
    names = S["names"]
    out = ["| Допущение | " + " | ".join(names) + " |", "|---" + "|---:" * len(names) + "|"]
    for r in S["rows"]:
        u = r["unit"]
        vals = [M.fmt(v, "%" if u == "%" else ("₽" if u.startswith("₽") else "")) for v in r["values"]]
        out.append(f"| {r['label']} | " + " | ".join(vals) + " |")
    return "\n".join(out)


def md_scen_findings(P, R):
    names = [n.split(" · ")[0] for n in P["scenarios"]["names"]]
    sc = R["scen"]
    rub = lambda v: M.fmt(M.ROUND(v, 0), "₽")  # noqa: E731
    plus_strict = [names[i] for i, s in enumerate(sc) if s["profit_city_nofee"] > 0]
    minus_strict = [names[i] for i, s in enumerate(sc) if s["profit_city_nofee"] <= 0]
    plus_fee = [names[i] for i, s in enumerate(sc) if s["profit_city"] > 0]
    total_plus = [names[i] for i, s in enumerate(sc) if s["profit"] > 0]
    lines = [
        f"- **Вся экосистема** (с ЦФА-услугами и рекламой) в плюсе в: {', '.join(total_plus) or 'нигде'}. S1: {rub(sc[0]['profit'])} в месяц.",
        f"- **Городская часть строго по v1.0** (без ЦФА и без взноса партнёров) в плюсе только в: {', '.join(plus_strict) or 'нигде'}; в минусе: {', '.join(minus_strict) or 'нигде'} "
        "(" + "; ".join(names[i] + " " + rub(s["profit_city_nofee"]) for i, s in enumerate(sc)) + ").",
        f"- **С взносом партнёра** (строка «Взнос партнёров v2.0») городская часть в плюсе в: {', '.join(plus_fee) or 'нигде'}.",
        f"- **Нагрузка:** от {M.fmt(M.ROUND(sc[0]['fte'], 2), '')} до {M.fmt(M.ROUND(sc[-1]['fte'], 2), '')} человек на полный день.",
    ]
    return "\n".join(lines)


XP_LABELS = {
    "BTN_MAIN_MENU": "Главное меню (раз в день)", "BTN_FOOD": "Где поесть (раз в день)", "BTN_LOCATIONS": "Локации (раз в день)",
    "BTN_ROUTES": "Маршруты (раз в день)", "BTN_EVENTS": "События (раз в день)", "NEARBY_FOOD": "Рядом со мной (раз в день)",
    "GEO_FIND": "Поиск по гео (раз в день)", "SUGGEST_PLACE": "Нажать «Предложить место»",
    "PLACE_ACCEPTED": "Место принято — `/xp_place`", "PLACE_FIX_ACCEPTED": "Правка принята — `/xp_fix` (до 3 в день)",
    "ROUTE_ACCEPTED": "Маршрут принят — `/xp_route`", "REVIEW_ACCEPTED": "Отзыв принят — `/xp_review` (до 2 в день)",
    "EVENT_CHECKIN": "Чек-ин на событии — `/checkin`", "PARTNER_NODE_CONNECTED": "Партнёр-узел подключён — `/partner_node`",
    "PARTNER_NODE_30D": "Узел жив ещё 30 дней", "MEMBER_REFERRAL_PAID": "Приглашённый оплатил членство — `/paid … referrer`",
    "CLUB_APPLY": "Заявка в клуб", "CLUB_PAID_MONTH": "Оплата месяца клуба", "CLUB_PAID_YEAR": "Оплата года клуба",
    "CFA_CALL": "Созвон по ЦФА", "BOOK_PURCHASED": "Покупка книги", "CFA_REVIEW_PAID": "Оплачен разбор ЦФА",
    "CFA_ISSUED": "Выпуск ЦФА", "CFA_COUPON_PAID": "Выплата по ЦФА",
}


def md_xp_values(X):
    a, b = X["v10"], X["v11"]
    out = ["| Действие | v1.0 | **v1.1** |", "|---|---:|---:|"]
    for sect in ("activity", "verified"):
        keys = list(dict.fromkeys(list(a[sect]) + list(b[sect])))
        for k in keys:
            va, vb = a[sect].get(k), b[sect].get(k)
            if not va and not vb:
                continue
            out.append(f"| {XP_LABELS.get(k, k)} | {'—' if va is None else va} | **{'—' if vb is None else vb}** |")
    out.append(f"| Потолок XP за кнопки в день | {a['daily_cap']} | **{b['daily_cap']}** |")
    out.append(f"| Друг по ссылке / друг остался активным | +{a['referral'][0]} / +{a['referral'][1]} | **+{b['referral'][0]} / +{b['referral'][1]}** (только новые) |")
    out.append(f"| Грант за 7000 XP | {a['grant_days'] or 180} дней | **{b['grant_days']} дней, квота 30** |")
    return "\n".join(out)


def _days(d):
    return "> 6 лет" if d is None else f"{d}"


def md_xp_sim(X):
    a, b = X["v10"], X["v11"]
    th = b["thresholds"]
    old = {p["key"]: p for p in a["personas"]}
    head = "| Профиль | " + " | ".join(f"{t} {b['ranks'][str(t)]}" for t in th) + " | 7000 в v1.0 |"
    out = [head, "|---" + "|---:" * (len(th) + 1) + "|"]
    for p in b["personas"]:
        cells = [_days(p["days"][str(t)]) for t in th]
        cells[-1] = f"**{cells[-1]}**"
        out.append(f"| {p['name']} | " + " | ".join(cells) + f" | {_days(old[p['key']]['days']['7000'])} |")
    out.append("")
    out.append("Числа — дни от первого /start. «> 6 лет» — симуляция не дошла за 6 лет.")
    return "\n".join(out)


def blocks(P, R, X):
    B = {
        "key": lambda: md_key(P, R),
        "price_list": lambda: md_price_list(P, R),
        "scen": lambda: M.md_scen(P, R),
        "scen_inputs": lambda: md_scen_inputs(P),
        "scen_findings": lambda: md_scen_findings(P, R),
        "xp_values": lambda: md_xp_values(X),
        "xp_sim": lambda: md_xp_sim(X),
    }
    for gid in M.UNIT:
        B[f"unit_{gid}"] = (lambda g: lambda: f"**{M.UNIT[g][0]}**\n\n" + M.md_unit(R, g))(gid)
    for g in P["groups"]:
        B[f"params_{g['id']}"] = (lambda gg: lambda: f"**Параметры: {gg['title']}**\n\n" + M.md_params(P, gg["id"]))(g)
    return B


AUTO_RE = re.compile(r"<!-- AUTO:(\w+) -->\n(.*?)<!-- /AUTO:\1 -->", re.S)


def doc_files():
    out = []
    for d in DOC_DIRS:
        full = os.path.join(ROOT, d)
        out += [os.path.join(full, f) for f in sorted(os.listdir(full)) if f.endswith(".md")]
    return out


def load_all():
    P = M.load_params()
    R = M.compute(P)
    X = json.load(open(XP_JSON, encoding="utf-8"))
    return P, R, X


def expected_auto_blocks():
    """[(путь, имя, ожидаемый markdown)] — для tools/check.py."""
    P, R, X = load_all()
    B = blocks(P, R, X)
    res = []
    for path in doc_files():
        text = open(path, encoding="utf-8").read()
        for m in AUTO_RE.finditer(text):
            name = m.group(1)
            res.append((path, name, B[name]() if name in B else f"⚠️ нет генератора для блока {name}"))
    return res


def fill_docs(P, R, X):
    B = blocks(P, R, X)
    n = 0
    for path in doc_files():
        text = open(path, encoding="utf-8").read()

        def rep(m):
            nonlocal n
            name = m.group(1)
            if name not in B:
                raise SystemExit(f"{path}: нет генератора для AUTO:{name}")
            n += 1
            return f"<!-- AUTO:{name} -->\n{B[name]().strip()}\n<!-- /AUTO:{name} -->"

        new = AUTO_RE.sub(rep, text)
        if new != text:
            open(path, "w", encoding="utf-8").write(new)
    return n


# ═════════════════════════ Markdown → HTML (минимальный, под наши документы) ═════════════════════════
def _inline(s: str) -> str:
    s = html.escape(s, quote=False)
    codes = []
    s = re.sub(r"`([^`]+)`", lambda m: codes.append(m.group(1)) or f"\x00{len(codes) - 1}\x00", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)([^*\n]+?)\*(?![\w*])", r"<i>\1</i>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    s = re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{codes[int(m.group(1))]}</code>", s)
    return s


def slug(s: str) -> str:
    return "h-" + hashlib.md5(s.encode()).hexdigest()[:8]


def md_to_html(md: str) -> str:
    md = re.sub(r"<!--.*?-->\n?", "", md, flags=re.S)
    lines = md.split("\n")
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            j = i + 1
            buf = []
            while j < len(lines) and not lines[j].startswith("```"):
                buf.append(lines[j])
                j += 1
            out.append('<div class="code"><button class="copy" type="button">Копировать</button><pre>' + html.escape("\n".join(buf)) + "</pre></div>")
            i = j + 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", ln)
        if m:
            lvl = len(m.group(1))
            out.append(f'<h{lvl} id="{slug(m.group(2))}">{_inline(m.group(2))}</h{lvl}>')
            i += 1
            continue
        if ln.strip() == "---":
            out.append("<hr>")
            i += 1
            continue
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            cells = lambda r: [c.strip() for c in r.strip().strip("|").split("|")]  # noqa: E731
            head = cells(rows[0])
            aligns = ["r" if c.endswith(":") and not c.startswith(":") else "" for c in cells(rows[1])] if len(rows) > 1 else []
            t = ['<div class="tw"><table><thead><tr>' + "".join(f"<th>{_inline(c)}</th>" for c in head) + "</tr></thead><tbody>"]
            for r in rows[2:]:
                cs = cells(r)
                t.append("<tr>" + "".join(f'<td class="{aligns[k] if k < len(aligns) else ""}">{_inline(c)}</td>' for k, c in enumerate(cs)) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t))
            continue
        if ln.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip(">").strip())
                i += 1
            out.append("<blockquote>" + "<br>".join(_inline(b) for b in buf) + "</blockquote>")
            continue
        if re.match(r"^\s*([-*]|\d+\.)\s+", ln):
            stack = []  # (indent, tag)
            html_l = []
            while i < len(lines) and (re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]) or (lines[i].startswith("  ") and lines[i].strip() and stack)):
                l2 = lines[i]
                mm = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)", l2)
                if not mm:  # продолжение пункта
                    html_l[-1] = html_l[-1][:-5] + " " + _inline(l2.strip()) + "</li>"
                    i += 1
                    continue
                ind, mark, body = len(mm.group(1)), mm.group(2), mm.group(3)
                tag = "ol" if mark[0].isdigit() else "ul"
                while stack and stack[-1][0] > ind:
                    html_l.append(f"</{stack.pop()[1]}>")
                if not stack or stack[-1][0] < ind:
                    stack.append((ind, tag))
                    html_l.append(f"<{tag}>")
                cb = re.match(r"^\[( |x)\]\s+(.*)", body)
                if cb:
                    html_l.append(f'<li class="cb">{"☑" if cb.group(1) == "x" else "☐"} {_inline(cb.group(2))}</li>')
                else:
                    html_l.append(f"<li>{_inline(body)}</li>")
                i += 1
            while stack:
                html_l.append(f"</{stack.pop()[1]}>")
            out.append("".join(html_l))
            continue
        if not ln.strip():
            i += 1
            continue
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,4}\s|```|\||>|\s*([-*]|\d+\.)\s+|---$)", lines[i]):
            buf.append(lines[i])
            i += 1
        out.append("<p>" + "<br>".join(_inline(b) for b in buf) + "</p>")
    return "\n".join(out)


# ═════════════════════════ ЗАПУСК.html ═════════════════════════
def parse_checklist(md: str):
    sections, cur = [], None
    for ln in md.split("\n"):
        m = re.match(r"^###\s+(.*)", ln)
        if m:
            cur = {"title": m.group(1).strip(), "items": []}
            sections.append(cur)
            continue
        m = re.match(r"^- \[ \]\s+(.*)", ln)
        if m and cur is not None:
            t = m.group(1).strip()
            cur["items"].append({"id": hashlib.md5(t.encode()).hexdigest()[:10], "html": _inline(t)})
    return [s for s in sections if s["items"]]


def parse_texts(md: str):
    res = []
    for m in re.finditer(r"^##\s+(.*?)\n(.*?)```text\n(.*?)\n```", md, re.S | re.M):
        res.append({"title": m.group(1).strip(), "text": m.group(3)})
    return res


def b64(path):
    return base64.b64encode(open(path, "rb").read()).decode()


MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".svg": "image/svg+xml", ".woff2": "font/woff2"}


def data_uri(path):
    return f"data:{MIME[os.path.splitext(path)[1].lower()]};base64,{b64(path)}"


def font_css(families):
    """@font-face из studio/fonts для ЗАПУСК.html."""
    css = []
    fdir = os.path.join(ROOT, "studio", "fonts")
    for fam, files in families.items():
        for fn, w in files:
            p = os.path.join(fdir, fn)
            rng = "U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116" if "cyrillic" in fn else "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"
            css.append(f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:normal;font-display:swap;src:url({data_uri(p)}) format('woff2');unicode-range:{rng}}}")
    return "\n".join(css)


def build_zapusk(P, R, X):
    tpl = open(os.path.join(ROOT, "tools", "zapusk.template.html"), encoding="utf-8").read()
    docs = []
    for path in doc_files() + [os.path.join(ROOT, "bot", "README.md"), os.path.join(ROOT, "brand", "BRAND.md")]:
        md = open(path, encoding="utf-8").read()
        title = re.search(r"^#\s+(.*)", md, re.M).group(1)
        rel = os.path.relpath(path, ROOT)
        heads = [(slug(h), h) for h in re.findall(r"^##\s+(.*)", md, re.M)]
        docs.append({"id": "d" + hashlib.md5(rel.encode()).hexdigest()[:6], "file": rel, "title": title,
                     "heads": heads, "html": md_to_html(md)})
    start_md = open(os.path.join(ROOT, "docs", "00-СТАРТ-ЗАВТРА.md"), encoding="utf-8").read()
    texts_md = open(os.path.join(ROOT, "docs", "11-тексты-для-запуска.md"), encoding="utf-8").read()
    data = {
        "model": json.load(open(MODEL_JSON, encoding="utf-8")),
        "xp": X,
        "checklist": parse_checklist(start_md),
        "texts": parse_texts(texts_md),
        "docs": docs,
        "key_html": md_to_html(md_key(P, R)),
        "xp_values_html": md_to_html(md_xp_values(X)),
        "xp_sim_html": md_to_html(md_xp_sim(X)),
        "findings_html": md_to_html(md_scen_findings(P, R)),
        "built": P["updated"],
    }
    fonts = font_css({
        "Unbounded": [("unbounded-cyrillic-700-normal.woff2", 700), ("unbounded-latin-700-normal.woff2", 700)],
        "Inter": [("inter-cyrillic-400-normal.woff2", 400), ("inter-latin-400-normal.woff2", 400),
                  ("inter-cyrillic-600-normal.woff2", 600), ("inter-latin-600-normal.woff2", 600),
                  ("inter-cyrillic-800-normal.woff2", 800), ("inter-latin-800-normal.woff2", 800)],
    })
    js_data = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    out = tpl.replace("/*__FONTS__*/", fonts).replace("/*__DATA__*/null", js_data).replace("__VERSION__", f"v{P['version']} · {P['updated']}")
    path = os.path.join(ROOT, "ЗАПУСК.html")
    open(path, "w", encoding="utf-8").write(out)
    return path, len(out)


# ═════════════════════════ studio/Студия.html ═════════════════════════
def build_studio():
    sdir = os.path.join(ROOT, "studio")
    page = open(os.path.join(sdir, "index.html"), encoding="utf-8").read()
    css = open(os.path.join(sdir, "studio.css"), encoding="utf-8").read()
    css = re.sub(r"url\((?:['\"])?(fonts/[^)'\"]+)(?:['\"])?\)", lambda m: f"url({data_uri(os.path.join(sdir, m.group(1)))})", css)
    assets = {}
    for sub in ("plates", "examples", "logos"):
        d = os.path.join(sdir, "assets", sub)
        for fn in sorted(os.listdir(d)):
            if os.path.splitext(fn)[1].lower() in MIME:
                assets[f"assets/{sub}/{fn}"] = data_uri(os.path.join(d, fn))

    def js(name):
        s = open(os.path.join(sdir, name), encoding="utf-8").read()
        for k, v in assets.items():  # прямые пути в коде шаблонов → сразу data:
            s = s.replace(f'"{k}"', f'"{v}"').replace(f"'{k}'", f"'{v}'").replace(f'src="{k}"', f'src="{v}"')
        return s.replace("</script", "<\\/script")

    page = page.replace('<link rel="stylesheet" href="studio.css">', "<style>\n" + css + "\n</style>")
    asset_js = "window.STUDIO_ASSETS = " + json.dumps(assets) + ";"
    scripts = "".join(f"<script>\n{s}\n</script>\n" for s in [asset_js, js("vendor/qrcode.js"), js("vendor/html-to-image.js"), js("templates.js"), js("app.js")])
    page = re.sub(r'<script src="vendor/qrcode.js"></script>\s*<script src="vendor/html-to-image.js"></script>\s*<script src="templates.js"></script>\s*<script src="app.js"></script>\s*',
                  lambda m: scripts, page)
    assert "<script src=" not in page, "не все скрипты встроены"
    page = page.replace("<title>Студия шаблонов", "<title>Студия шаблонов (один файл)", 1)
    path = os.path.join(sdir, "Студия.html")
    open(path, "w", encoding="utf-8").write(page)
    return path, len(page)


# ═════════════════════════ main ═════════════════════════
def main():
    import runpy
    print("1/5 модель …")
    P = M.load_params()
    R = M.compute(P)
    os.makedirs(os.path.dirname(MODEL_JSON), exist_ok=True)
    json.dump(M.to_json(P, R), open(MODEL_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("2/5 Excel …")
    sys.argv = ["build_model.py"]
    runpy.run_path(os.path.join(ROOT, "economics", "build_model.py"), run_name="__main__")
    X = json.load(open(XP_JSON, encoding="utf-8"))
    print("3/5 документы …", fill_docs(P, R, X), "AUTO-блоков")
    p, n = build_zapusk(P, R, X)
    print(f"4/5 {os.path.relpath(p, ROOT)} — {n / 1024:.0f} КБ")
    p, n = build_studio()
    print(f"5/5 {os.path.relpath(p, ROOT)} — {n / 1024 / 1024:.1f} МБ")
    print("Готово. Проверка: python tools/check.py")


if __name__ == "__main__":
    main()
