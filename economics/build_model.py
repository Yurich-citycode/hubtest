#!/usr/bin/env python3
"""
Собирает economics/Экономика_экосистемы.xlsx — модель с формулами.

Жёлтые ячейки — допущения: меняешь их прямо в Excel / Google Sheets, остальное
пересчитывается само. Этот скрипт нужен только чтобы пересобрать файл с нуля
(или поменять структуру). Запуск: python economics/build_model.py

Листы:
  «Сценарии»     — 5 стадий: 5/100, 10/500, 30/5 000, 60/15 000, 3 города
  «Доли партнёров» — калькулятор долей стратегических партнёров (Slicing Pie)
  «Прайс»        — цены на всё в одном месте (партнёр / не партнёр)
  «XP»           — сроки до рангов на текущей и предложенной калибровке
"""
from __future__ import annotations

import os
import re

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Экономика_экосистемы.xlsx")

SCEN = ["S1 · Пилот", "S2 · Сеть", "S3 · Город", "S4 · Зрелый город", "S5 · 3 города"]
SCEN_SUB = ["5 партнёров · 100 юзеров", "10 партнёров · 500 юзеров", "30 партнёров · 5 000 юзеров",
            "60 партнёров · 15 000 юзеров", "150 партнёров · 50 000 юзеров"]
COLS = ["C", "D", "E", "F", "G"]

# (key, label, unit, kind, values-or-formula, note)
# kind: hdr — заголовок, in — допущение (жёлтое), calc — формула, out — итог (жирный)
R = [
    ("h_scale", "МАСШТАБ", "", "hdr", None, ""),
    ("partners", "Партнёров City Code (точек)", "шт", "in", [5, 10, 30, 60, 150], "Физические точки с привилегией"),
    ("mau", "Пользователей Sevastopol AI в месяц (MAU)", "чел", "in", [100, 500, 5000, 15000, 50000], "Активные в боте за 30 дней"),
    ("cities", "Городов", "шт", "in", [1, 1, 1, 1, 3], ""),

    ("h_cc", "CITY CODE · ЧЛЕНСТВО", "", "hdr", None, ""),
    ("price_basic", "Цена Basic", "₽/год", "in", [5108] * 5, "Зафиксировано в CITY CODE v1.0"),
    ("price_founder", "Цена «Основатели»", "₽/год", "in", [15108] * 5, "Зафиксировано v1.0, цена навсегда"),
    ("founder_seats", "Мест «Основатели»", "шт", "in", [50, 50, 50, 50, 150], "50 на город"),
    ("conv", "Конверсия MAU → участник", "%", "in", [0.05, 0.04, 0.035, 0.03, 0.03], "Допущение. Проверить на пилоте"),
    ("direct", "Участники из личного окружения / офлайн-продаж", "чел", "in", [10, 30, 60, 80, 150], "Основатели продаются руками, не ботом"),
    ("cap_pp", "Ёмкость: участников на 1 партнёра", "чел", "in", [15] * 5, "Сколько гостей точка выдерживает без перегрузки"),
    ("m_demand", "Спрос на членство", "чел", "calc", "={mau}*{conv}+{direct}", ""),
    ("m_cap", "Потолок по ёмкости партнёров", "чел", "calc", "={partners}*{cap_pp}", "Правило v1.0: рост через партнёров"),
    ("members", "Участников City Code", "чел", "out", "=ROUND(MIN({m_demand},{m_cap}),0)", ""),
    ("founders", "  из них «Основатели»", "чел", "calc", "=MIN({founder_seats},{members})", "Первые места продаются как Основатели"),
    ("basic", "  из них Basic", "чел", "calc", "={members}-{founders}", ""),
    ("rev_memb_y", "Выручка членства за год", "₽/год", "calc", "={founders}*{price_founder}+{basic}*{price_basic}", ""),
    ("rev_memb", "Выручка членства в месяц", "₽/мес", "out", "={rev_memb_y}/12", ""),

    ("h_net", "ПАРТНЁРСКАЯ СЕТЬ (оборот партнёров — НЕ наш доход)", "", "hdr", None, ""),
    ("spend", "Средний расход участника у партнёров", "₽/мес", "in", [7000] * 5, "Из v1.0"),
    ("priv", "Средняя привилегия", "%", "in", [0.05] * 5, "v1.0: 3–7%"),
    ("net_turn", "Оборот сети через участников", "₽/мес", "calc", "={members}*{spend}", ""),
    ("turn_pp", "Доп. оборот на 1 партнёра", "₽/мес", "calc", "={net_turn}/{partners}", "Сравни с выручкой точки"),
    ("saving", "Экономия участника на привилегиях за год", "₽/год", "calc", "={spend}*12*{priv}", ""),
    ("payback", "Окупаемость Basic скидками", "раз", "calc", "={saving}/{price_basic}", "<1 — ценность должна быть в людях и событиях"),

    ("h_sai", "SEVASTOPOL AI · РЕКЛАМА И КОНТЕНТ", "", "hdr", None, ""),
    ("ads_n", "Платных размещений в месяц", "шт", "in", [2, 5, 15, 30, 80], "Маркированная реклама, см. «Прайс»"),
    ("ads_check", "Средний чек размещения", "₽", "in", [3000, 5000, 10000, 15000, 15000], "Растёт с аудиторией"),
    ("rev_ads", "Выручка рекламы SAI", "₽/мес", "calc", "={ads_n}*{ads_check}", ""),
    ("shoots_n", "Съёмок для заведений в месяц", "шт", "in", [0, 2, 4, 8, 20], "С партнёром по оборудованию"),
    ("shoot_price", "Цена съёмки", "₽", "in", [10000, 12000, 15000, 15000, 15000], ""),
    ("rev_content", "Выручка контент-продакшна", "₽/мес", "calc", "={shoots_n}*{shoot_price}", ""),

    ("h_ev", "СОБЫТИЯ CITY CODE", "", "hdr", None, ""),
    ("ev_n", "Платных событий в месяц", "шт", "in", [0, 1, 2, 4, 10], ""),
    ("ev_people", "Гостей на событии", "чел", "in", [0, 20, 35, 50, 50], ""),
    ("ev_ticket", "Билет", "₽", "in", [1500, 1500, 2000, 2000, 2000], ""),
    ("rev_events", "Выручка событий", "₽/мес", "calc", "={ev_n}*{ev_people}*{ev_ticket}", ""),

    ("h_merch", "МЕРЧ И ФИЗИЧЕСКИЙ ПАСПОРТ", "", "hdr", None, ""),
    ("mr_members", "Доля участников, купивших в месяц", "%", "in", [0.03] * 5, ""),
    ("mr_mau", "Доля MAU, купивших в месяц", "%", "in", [0.001] * 5, ""),
    ("m_check", "Средний чек мерча", "₽", "in", [2500] * 5, "Паспорт 1 500, худи 4 900, брелок 1 200"),
    ("rev_merch", "Выручка мерча", "₽/мес", "calc", "=({members}*{mr_members}+{mau}*{mr_mau})*{m_check}", ""),

    ("h_rwa", "YURICHRWA И ЦФА (отдельный контур, личная экспертиза)", "", "hdr", None, ""),
    ("cfa_rev_n", "Разборов ЦФА в год (80 000 ₽)", "шт", "in", [1, 2, 4, 6, 10], ""),
    ("cfa_build_n", "Сборок выпуска в год (~325 000 ₽)", "шт", "in", [0, 1, 2, 3, 5], "Середина 250–400 тыс."),
    ("rev_cfa", "Выручка ЦФА-услуг (среднемесячно)", "₽/мес", "calc", "=({cfa_rev_n}*80000+{cfa_build_n}*325000)/12", "Не зависит от SAI напрямую"),
    ("rwa_subs", "Подписчиков YuRichRWA", "чел", "in", [1000, 2000, 5000, 10000, 20000], ""),
    ("rwa_view", "Охват поста", "%", "in", [0.3] * 5, ""),
    ("rwa_cpm", "CPM ниши RWA/крипто", "₽", "in", [1500] * 5, "Проверить по прайсам похожих каналов"),
    ("rwa_posts", "Рекламных постов в месяц", "шт", "in", [0, 1, 3, 5, 8], "Не больше 1 на 6–8 своих"),
    ("rev_rwa_ads", "Выручка рекламы YuRichRWA", "₽/мес", "calc", "={rwa_subs}*{rwa_view}*{rwa_cpm}/1000*{rwa_posts}", ""),

    ("h_total", "ВЫРУЧКА (без расходов)", "", "hdr", None, ""),
    ("rev_total", "Вся выручка", "₽/мес", "out", "={rev_memb}+{rev_ads}+{rev_content}+{rev_events}+{rev_merch}+{rev_cfa}+{rev_rwa_ads}", ""),
    ("rev_city", "  из неё город (SAI + CC)", "₽/мес", "calc", "={rev_memb}+{rev_ads}+{rev_content}+{rev_events}+{rev_merch}", ""),
    ("rev_total_y", "Вся выручка за год", "₽/год", "out", "={rev_total}*12", ""),

    ("h_cost", "РАСХОДЫ В МЕСЯЦ", "", "hdr", None, ""),
    ("c_infra", "Сервер, домены, сервисы", "₽/мес", "in", [1500, 2500, 6000, 15000, 40000], ""),
    ("ai_mau", "AI (Кира) на 1 MAU", "₽", "in", [0, 0, 3, 3, 3], "Кира включается с S3"),
    ("c_ai", "AI / API", "₽/мес", "calc", "={mau}*{ai_mau}", ""),
    ("c_team", "Команда (контент, продажи, поддержка, разработка)", "₽/мес", "in", [0, 30000, 140000, 400000, 1200000], "S1 — всё сам"),
    ("c_mkt", "Маркетинг: посевы, QR, печать", "₽/мес", "in", [10000, 30000, 100000, 200000, 600000], ""),
    ("c_legal", "Бухгалтерия и юрист", "₽/мес", "in", [5000, 10000, 20000, 40000, 100000], ""),
    ("c_ip", "Защита прав (ТЗ, ПО, БД) — разово, на 12 мес.", "₽/мес", "in", [12500, 12500, 0, 0, 25000], "~150 тыс. РФ; S5 — международка"),
    ("c_ip_fee", "Фикс. взносы ИП за себя", "₽/мес", "in", [4750] * 5, "~55–60 тыс./год, уточнять"),
    ("acq_rate", "Эквайринг", "%", "in", [0.03] * 5, ""),
    ("c_acq", "Комиссия за приём платежей", "₽/мес", "calc", "={acq_rate}*({rev_memb}+{rev_events}+{rev_merch})", ""),
    ("ev_cost", "Себестоимость событий", "%", "in", [0.65] * 5, "Аренда, еда, ведущий"),
    ("merch_cogs", "Себестоимость мерча", "%", "in", [0.45] * 5, ""),
    ("shoot_cost", "Себестоимость съёмки", "%", "in", [0.4] * 5, "Оператор / доля партнёра"),
    ("c_cogs", "Себестоимость (события, мерч, съёмки)", "₽/мес", "calc", "={rev_events}*{ev_cost}+{rev_merch}*{merch_cogs}+{rev_content}*{shoot_cost}", ""),
    ("c_adlevy", "Отчисление 3% с интернет-рекламы", "₽/мес", "calc", "=0.03*({rev_ads}+{rev_rwa_ads})", "ст. 18.2 закона «О рекламе»"),
    ("tax_rate", "Налог УСН «доходы»", "%", "in", [0.06] * 5, ""),
    ("c_tax", "Налог", "₽/мес", "calc", "={rev_total}*{tax_rate}", ""),
    ("c_total", "Все расходы", "₽/мес", "out", "={c_infra}+{c_ai}+{c_team}+{c_mkt}+{c_legal}+{c_ip}+{c_ip_fee}+{c_acq}+{c_cogs}+{c_adlevy}+{c_tax}", ""),

    ("h_res", "РЕЗУЛЬТАТ (с расходами)", "", "hdr", None, ""),
    ("profit", "Прибыль в месяц", "₽/мес", "out", "={rev_total}-{c_total}", ""),
    ("profit_y", "Прибыль за год", "₽/год", "out", "={profit}*12", ""),
    ("margin", "Маржа", "%", "calc", "=IF({rev_total}=0,0,{profit}/{rev_total})", ""),
    ("profit_city", "Прибыль города без ЦФА-услуг", "₽/мес", "out", "={profit}-{rev_cfa}*(1-{tax_rate})", "Сколько зарабатывает сама городская часть"),

    ("h_load", "НАГРУЗКА (часы в месяц)", "", "hdr", None, ""),
    ("l_support", "Поддержка пользователей и участников", "ч", "calc", "=({mau}*0.02+{members}*0.1)*0.25", "2% MAU и 10% участников пишут, 15 мин на обращение"),
    ("l_partner", "Работа с партнёрами", "ч", "calc", "={partners}*3", "3 ч на точку: условия, персонал, визиты"),
    ("l_moder", "Модерация мест и предложений", "ч", "calc", "={mau}*0.01*0.2", ""),
    ("l_content", "Контент: посты, обложки, события", "ч", "in", [20, 30, 60, 100, 250], ""),
    ("l_events", "События", "ч", "calc", "={ev_n}*12", "12 ч на событие"),
    ("l_total", "Всего часов", "ч", "out", "={l_support}+{l_partner}+{l_moder}+{l_content}+{l_events}", ""),
    ("l_fte", "Людей на полный день (160 ч)", "чел", "out", "={l_total}/160", ""),
]


def build():
    wb = Workbook()
    ws = wb.active
    ws.title = "Сценарии"
    yellow = PatternFill("solid", fgColor="FFF4C2")
    hdr_fill = PatternFill("solid", fgColor="111111")
    out_fill = PatternFill("solid", fgColor="EAF7C8")
    thin = Side(style="thin", color="DDDDDD")
    border = Border(bottom=thin)

    ws["A1"] = "Экономика экосистемы SevastopolAI · City Code · YuRichRWA"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = "Жёлтое — допущения, меняй их. Зелёное — итоги. Оборот партнёров ≠ наша выручка. Все цифры — модель, не факт."
    ws["A2"].font = Font(italic=True, color="666666")
    ws.append([])
    ws.append(["Показатель", "Ед."] + SCEN + ["Комментарий"])
    ws.append(["", ""] + SCEN_SUB + [""])
    for c in range(1, 9):
        ws.cell(4, c).font = Font(bold=True, color="FFFFFF")
        ws.cell(4, c).fill = hdr_fill
        ws.cell(5, c).font = Font(italic=True, color="666666", size=9)
    row_of: dict[str, int] = {}
    r = 6
    for key, *_ in R:
        row_of[key] = r
        r += 1
    r = 6
    pct_keys = {k for k, _, u, *_ in R if u == "%"}
    for key, label, unit, kind, val, note in R:
        ws.cell(r, 1, label)
        ws.cell(r, 2, unit)
        ws.cell(r, 8, note).font = Font(color="777777", size=9)
        if kind == "hdr":
            for c in range(1, 9):
                ws.cell(r, c).fill = PatternFill("solid", fgColor="2B2B2B")
                ws.cell(r, c).font = Font(bold=True, color="D7FF3D")
        else:
            for i, col in enumerate(COLS):
                cell = ws[f"{col}{r}"]
                if kind == "in":
                    cell.value = val[i]
                    cell.fill = yellow
                else:
                    cell.value = re.sub(r"\{(\w+)\}", lambda m: f"{col}{row_of[m.group(1)]}", val)
                    if kind == "out":
                        cell.fill = out_fill
                        cell.font = Font(bold=True)
                if key in pct_keys:
                    cell.number_format = "0.0%"
                elif key in ("payback", "l_fte"):
                    cell.number_format = "0.00"
                else:
                    cell.number_format = "# ##0"
                cell.border = border
            if kind == "out":
                ws.cell(r, 1).font = Font(bold=True)
        r += 1
    ws.column_dimensions["A"].width = 52
    ws.column_dimensions["B"].width = 8
    for col in COLS:
        ws.column_dimensions[col].width = 17
    ws.column_dimensions["H"].width = 48
    ws.freeze_panes = "C6"

    build_shares(wb)
    build_prices(wb)
    build_xp(wb)
    wb.save(OUT)
    return row_of


# ── доли стратегических партнёров ─────────────────────────────────────────
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
        ws.cell(4, c).font = Font(bold=True, color="FFFFFF")
        ws.cell(4, c).fill = PatternFill("solid", fgColor="111111")
        ws.cell(4, c).alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[4].height = 48
    people = [
        ("YuRich (основатель)", "Продукт, бренд, бот, база, сайт, продажи", 150000, 0, 12, 1500000, 300000),
        ("Партнёр по оборудованию и контенту", "Камера, свет, звук, монтаж, съёмки", 0, 40000, 12, 0, 0),
        ("Партнёр по событиям и офису", "Площадка для событий, рабочее место", 0, 60000, 12, 0, 0),
        ("(резерв) Технический партнёр", "Разработка, сервер", 0, 0, 0, 0, 0),
    ]
    yellow = PatternFill("solid", fgColor="FFF4C2")
    for i, p in enumerate(people):
        r = 5 + i
        for c, v in enumerate(p, start=1):
            cell = ws.cell(r, c, v)
            if c >= 3:
                cell.fill = yellow
                cell.number_format = "# ##0"
        ws.cell(r, 8, f"=2*(C{r}+D{r})*E{r}+2*F{r}+4*G{r}").number_format = "# ##0"
        ws.cell(r, 9, f"=IF(SUM($H$5:$H$8)=0,0,H{r}/SUM($H$5:$H$8))").number_format = "0.0%"
    ws.cell(9, 7, "Итого").font = Font(bold=True)
    ws.cell(9, 8, "=SUM(H5:H8)").number_format = "# ##0"
    ws.cell(9, 9, "=SUM(I5:I8)").number_format = "0.0%"

    ws.cell(11, 1, "Ограничители (рекомендация)").font = Font(bold=True)
    rules = [
        "1. Пул стратегических партнёров — не больше 10–15% на всех. Если калькулятор даёт больше — часть вклада платим бартером (реклама, место в логотипе, мерч), а не долей.",
        "2. Вестинг 24–36 месяцев, первые 6–12 месяцев «клифф»: ушёл раньше — доли нет, вклад закрываем бартером.",
        "3. Доля возможна только в юрлице (ООО). Пока ты физлицо — опционный договор (ст. 429.2 ГК) или договор о выручке, и только после регистрации ООО — доля.",
        "4. Доля — в той компании, где лежат права (товарные знаки, ПО, база). Не дробить на «долю в боте» и «долю в клубе».",
        "5. Альтернатива доле — revenue share: % от выручки конкретного направления (например, 20–30% от съёмок, где работает оборудование партнёра), с потолком и сроком.",
    ]
    for i, t in enumerate(rules):
        ws.cell(12 + i, 1, t).alignment = Alignment(wrap_text=True)
        ws.merge_cells(start_row=12 + i, start_column=1, end_row=12 + i, end_column=9)
        ws.row_dimensions[12 + i].height = 32
    widths = [34, 36, 18, 18, 10, 20, 14, 16, 10]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


# ── прайс ───────────────────────────────────────────────────────────────
PRICES = [
    ("City Code", "Членство Basic", "5 108 ₽/год", "—", "Зафиксировано v1.0"),
    ("City Code", "Членство «Основатели»", "15 108 ₽/год", "—", "50 мест, цена навсегда"),
    ("City Code", "Вход партнёра в Partner Circle", "0 ₽", "—", "v1.0: без комиссии и платы за вход"),
    ("City Code", "Ячейка в логотипе «C»", "не продаётся", "—", "Статус партнёра, первые 20 мест"),
    ("City Code", "Спонсорство закрытого события", "10–30 тыс. ₽", "20–50 тыс. ₽", "Партнёр / внешний бренд"),
    ("Sevastopol AI", "Карточка места в боте", "0 ₽", "0 ₽", "Редакционный отбор. Деньги не влияют на попадание"),
    ("Sevastopol AI", "«Рекомендуем» в категории, 7 дней (с пометкой «Реклама»)", "1 500 ₽", "3 000 ₽", "Цена S1–S2, растёт с MAU"),
    ("Sevastopol AI", "Пост в канале Sevastopol AI", "1 500–2 500 ₽", "3 000–5 000 ₽", "Маркировка erid обязательна"),
    ("Sevastopol AI", "Подборка / гид (3–5 мест)", "5 000 ₽", "10 000–15 000 ₽", "Спецпроект"),
    ("Sevastopol AI", "Включение точки в маршрут", "3 000 ₽", "5 000 ₽", "Только если точка реально по пути"),
    ("Sevastopol AI", "Анонс события в боте и канале", "1 раз в мес. бесплатно", "1 500 ₽", ""),
    ("Sevastopol AI", "Фото/видео-съёмка заведения", "8 000 ₽", "12 000–20 000 ₽", "С партнёром по оборудованию"),
    ("Sevastopol AI", "QR-стойка в заведении", "бесплатно", "—", "Это наш канал привлечения, не их реклама"),
    ("Мерч", "Физический City Passport", "1 500 ₽", "1 500 ₽", "Себестоимость ~400 ₽"),
    ("Мерч", "Брелок «6 ключей»", "1 200 ₽", "1 200 ₽", ""),
    ("Мерч", "Худи City Code", "4 900 ₽", "4 900 ₽", "Участникам −10%"),
    ("ЦФА (YuRich)", "Созвон", "0 ₽", "0 ₽", "30–40 мин"),
    ("ЦФА (YuRich)", "Разбор", "80 000 ₽", "80 000 ₽", "1–2 недели"),
    ("ЦФА (YuRich)", "Сборка выпуска", "250–400 тыс. ₽", "250–400 тыс. ₽", "2–4 недели"),
    ("ЦФА (YuRich)", "Посадка на площадку", "200–350 тыс. ₽", "200–350 тыс. ₽", "На сайте не указана — добавить"),
    ("ЦФА (YuRich)", "Сопровождение", "40 000 ₽/мес", "40 000 ₽/мес", ""),
    ("ЦФА (YuRich)", "% за привлечённый спрос", "3–7%", "3–7%", "Только если спрос мой"),
]


def build_prices(wb):
    ws = wb.create_sheet("Прайс")
    ws.append(["Продукт", "Формат", "Партнёр City Code", "Не партнёр", "Комментарий"])
    for c in range(1, 6):
        ws.cell(1, c).font = Font(bold=True, color="FFFFFF")
        ws.cell(1, c).fill = PatternFill("solid", fgColor="111111")
    for p in PRICES:
        ws.append(list(p))
    for col, w in zip("ABCDE", [16, 52, 22, 20, 48]):
        ws.column_dimensions[col].width = w


def build_xp(wb):
    ws = wb.create_sheet("XP")
    ws["A1"] = "Сроки до порогов XP (симуляция на настоящем коде бота: economics/xp_simulator.py)"
    ws["A1"].font = Font(bold=True, size=13)
    r = 3
    for title, fn in (("Сейчас (как в коде)", "xp_current.md"), ("Предложение: кнопки ≤10 XP/день, вклад весит больше", "xp_proposal.md")):
        ws.cell(r, 1, title).font = Font(bold=True)
        r += 1
        path = os.path.join(HERE, fn)
        if os.path.exists(path):
            for line in open(path, encoding="utf-8"):
                if line.startswith("|---"):
                    continue
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                for c, v in enumerate(cells, start=1):
                    ws.cell(r, c, v)
                r += 1
        r += 1
    ws.column_dimensions["A"].width = 60
    for col in "BCDEFG":
        ws.column_dimensions[col].width = 20


if __name__ == "__main__":
    build()
    print("OK →", OUT)
