#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сборка PDF-книги «RWA. Мы объясняем» из markdown-исходников в папке book/.

Запуск:
    pip install --break-system-packages fpdf2 font-roboto
    python3 book/build_pdf.py

Результат: book/RWA-мы-объясняем.pdf
Markdown-файлы скрипт только читает и никогда не меняет.
"""

import os
import re
import sys

from fpdf import FPDF

# ---------------------------------------------------------------- пути / шрифты
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "RWA-мы-объясняем.pdf")

try:
    import font_roboto
    FONT_DIR = os.path.join(os.path.dirname(font_roboto.__file__), "files")
except Exception:
    FONT_DIR = "/usr/local/lib/python3.11/dist-packages/font_roboto/files"

# ---------------------------------------------------------------- дизайн
PW, PH = 176.02, 250.11          # формат полосы, мм
FRAME = 9.0                      # отступ рамки
ML, MR = 14.0, 14.0              # поля набора
CW = PW - ML - MR                # ширина колонки
BODY_TOP = 23.0
BODY_BOTTOM = 224.0

CREAM = (241, 232, 216)
BLACK = (26, 24, 21)
PINK = (236, 42, 100)
YELLOW = (244, 196, 36)
WHITE = (255, 255, 255)

LH = 6.6                         # интерлиньяж основного текста
BODY_PT = 11

PARTS = [
    ("I", "ОСНОВЫ", ["ch01-truba.md", "ch02-klyuchi.md", "ch03-rynok.md"]),
    ("II", "АКТИВЫ", ["ch04-veksel.md", "ch05-zarplata.md", "ch06-raspiska.md",
                      "ch07-yunity.md", "ch08-nomerok.md", "ch09-relsy.md"]),
    ("III", "ИНФРАСТРУКТУРА", ["ch10-provodka.md"]),
    ("IV", "СНГ И ЦФА", ["ch11-rezba.md", "ch12-dvory.md"]),
    ("V", "ИТОГ", ["ch13-flag.md"]),
]

CODEWORDS = ["ТРУБА", "КЛЮЧИ", "РЫНОК", "ВЕКСЕЛЬ", "ЗАРПЛАТА", "РАСПИСКА",
             "ЮНИТЫ", "НОМЕРОК", "РЕЛЬСЫ", "ПРОВОДКА", "РЕЗЬБА", "ДВОРЫ", "ФЛАГ"]


# ---------------------------------------------------------------- утилиты текста
def clean(s):
    """Чистим то, чего нет в Roboto / что не нужно в вёрстке."""
    s = s.replace("→", "»").replace("←", "«")
    s = s.replace("\u00a0", " ").replace("\u2011", "-")
    return s.strip()


def md_inline(s):
    """*курсив* -> __курсив__ (формат markdown у fpdf2); **жирный** оставляем."""
    s = clean(s)
    s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"__\1__", s)
    return s


def plain(s):
    return re.sub(r"[*_`]", "", clean(s))


def sp(s, gap=" "):
    """Разрядка: Р А З Р Я Д К А."""
    return gap.join(list(s))


# ---------------------------------------------------------------- парсинг md
def read(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return f.read()


def parse_chapter(fname):
    """-> dict(num, title, codeword, chips[(label,value)], thesis, kicker, blocks[])"""
    raw = read(fname)
    lines = raw.split("\n")
    ch = {"chips": [], "thesis": "", "codeword": "", "kicker": "", "blocks": []}

    m = re.match(r"#\s*(\d+)\s*·\s*(.+)", lines[0])
    ch["num"], ch["title"] = m.group(1), clean(m.group(2))

    i = 1
    body = []
    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith("> **[ТИТУЛЬНАЯ ПОЛОСА]"):
            i += 1
            while i < len(lines) and lines[i].startswith(">"):
                t = clean(lines[i].lstrip("> ").strip())
                if t.startswith("Кодовое слово"):
                    ch["codeword"] = plain(t.split(":", 1)[1])
                elif t.startswith("Плашки"):
                    for part in t.split(":", 1)[1].split("·"):
                        part = part.strip()
                        mm = re.match(r"\*\*(.+?)\*\*\s*(.*)", part)
                        if mm:
                            ch["chips"].append((plain(mm.group(1)), plain(mm.group(2))))
                elif t.startswith("Тезис"):
                    ch["thesis"] = plain(t.split(":", 1)[1])
                i += 1
            continue
        body.append(ln)
        i += 1

    # кикер — первая строка вида **Глава 01 · Основы**
    for j, ln in enumerate(body):
        if re.match(r"\*\*Глава\s*\d+\s*·", ln.strip()):
            ch["kicker"] = plain(ln)
            body = body[j + 1:]
            break

    ch["blocks"] = parse_blocks(body)
    return ch


def parse_blocks(lines):
    """Список блоков: ('h2',txt) ('p',txt) ('plashka',[строки]) ('slot',kind,txt) ('itog',txt)"""
    blocks, buf, quote = [], [], []

    def flush_p():
        if buf:
            blocks.append(("p", " ".join(x.strip() for x in buf).strip()))
            buf.clear()

    def flush_q():
        if not quote:
            return
        head = quote[0]
        rest = [q for q in quote[1:] if q.strip()]
        if head.startswith("**[ПЛАШКА"):
            blocks.append(("plashka", rest))
        elif head.startswith("**ИТОГ"):
            txt = plain(head)
            txt = re.sub(r"^ИТОГ\s*[—–-]\s*", "", txt)
            blocks.append(("itog", txt))
        else:
            m = re.match(r"\*\*\[([А-ЯA-Z/\-]+)[:\]]?\s*(.*)", head, re.S)
            kind = "СХЕМА"
            if m:
                k = m.group(1)
                kind = "ФОТО" if "ФОТО" in k else "СХЕМА"
            desc = plain(head)
            desc = re.sub(r"^\[?[А-ЯA-Z/\-]+\s*[:]?\s*", "", desc).strip("[] ")
            blocks.append(("slot", kind, desc))
        quote.clear()

    for ln in lines:
        s = ln.rstrip()
        if s.startswith(">"):
            flush_p()
            quote.append(clean(s.lstrip("> ").strip()) if s.strip() != ">" else "")
            continue
        flush_q()
        if not s.strip():
            flush_p()
        elif s.startswith("## "):
            flush_p()
            blocks.append(("h2", plain(s[3:])))
        elif s.startswith("#"):
            flush_p()
        elif s.strip() == "---":
            flush_p()
        else:
            buf.append(clean(s))
    flush_p()
    flush_q()
    return blocks


def parse_front():
    raw = read("00-front.md")
    out = {}
    cur = None
    for ln in raw.split("\n"):
        if ln.startswith("## "):
            cur = plain(ln[3:])
            out[cur] = []
        elif cur:
            out[cur].append(ln)
    res = {}
    for k, v in out.items():
        res[k] = parse_blocks(v)
    return res


def parse_back():
    raw = read("14-back.md")
    terms, dalshe, kolofon = [], [], []
    sec = None
    for ln in raw.split("\n"):
        if ln.startswith("# "):
            sec = plain(ln[2:])
            continue
        s = ln.strip()
        if sec and sec.startswith("СЛОВАРЬ"):
            m = re.match(r"\*\*(.+?)\*\*\s*[—–-]\s*(.+)", clean(s))
            if m:
                terms.append((plain(m.group(1)), plain(m.group(2))))
        elif sec == "ЧТО ДАЛЬШЕ":
            if s and s != "---":
                dalshe.append(clean(s))
        elif sec == "КОЛОФОН":
            if s and s != "---":
                kolofon.append(plain(s))
    return terms, dalshe, kolofon


# ---------------------------------------------------------------- PDF
class Book(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format=(PW, PH))
        self.set_auto_page_break(False)
        self.set_margins(ML, BODY_TOP, MR)
        for style, fn in (("", "Regular"), ("B", "Bold"), ("I", "Italic"), ("BI", "BoldItalic")):
            self.add_font("Rb", style, os.path.join(FONT_DIR, "Roboto-%s.ttf" % fn))
        self.add_font("Bk", "", os.path.join(FONT_DIR, "Roboto-Black.ttf"))
        self.add_font("Bk", "B", os.path.join(FONT_DIR, "Roboto-Black.ttf"))
        self.set_title("RWA. Мы объясняем")
        self.set_author("YuRich")
        self.running = None          # (chapter caption) для колонтитулов
        self.folio = True

    # -- фон и рамка
    def base(self):
        self.set_fill_color(*CREAM)
        self.rect(0, 0, PW, PH, "F")
        self.set_draw_color(*BLACK)
        self.set_line_width(0.4)
        self.rect(FRAME, FRAME, PW - 2 * FRAME, PH - 2 * FRAME)
        self.set_line_width(0.2)

    def blank(self):
        self.add_page()
        self.base()

    # -- текстовая полоса с колонтитулами
    def text_page(self):
        self.blank()
        if self.running:
            self.set_font("Rb", "B", 7)
            self.set_text_color(*BLACK)
            self.set_xy(ML, 13.0)
            self.cell(CW / 2, 4, sp("RWA / ЦФА"), align="L")
            self.set_xy(ML + CW / 2, 13.0)
            self.cell(CW / 2, 4, sp(self.running), align="R")
            self.set_draw_color(*BLACK)
            self.set_line_width(0.5)
            self.line(ML, 18.2, PW - MR, 18.2)
            self.set_line_width(0.2)
        self.footer_bar()
        self.set_xy(ML, BODY_TOP)

    def footer_bar(self):
        y = 229.5
        self.set_draw_color(*BLACK)
        self.set_line_width(0.5)
        self.line(ML, y, PW - MR, y)
        self.set_line_width(0.2)
        self.set_font("Rb", "B", 13)
        self.set_text_color(*BLACK)
        self.set_xy(ML, y + 2.2)
        self.cell(30, 7, "YuRich", align="L")
        w = self.get_string_width("YuRich")
        self.set_text_color(*PINK)
        self.set_xy(ML + w, y + 2.2)
        self.cell(6, 7, "|", align="L")
        if self.folio:
            self.set_font("Rb", "B", 14)
            self.set_text_color(*PINK)
            self.set_xy(PW - MR - 30, y + 2.2)
            self.cell(30, 7, str(self.page_no()), align="R")
        self.set_text_color(*BLACK)

    # -- сервис
    def need(self, h):
        if self.get_y() + h > BODY_BOTTOM:
            self.text_page()
            return True
        return False

    def lines_count(self, txt, w, size, style="", markdown=True):
        self.set_font("Rb", style, size)
        ls = self.multi_cell(w, LH, txt, align="J", dry_run=True, output="LINES",
                             markdown=markdown)
        return max(1, len(ls))

    def shadow_rect(self, x, y, w, h, fill, off=1.6, shadow=BLACK, border=True):
        self.set_fill_color(*shadow)
        self.rect(x + off, y + off, w, h, "F")
        self.set_fill_color(*fill)
        self.set_draw_color(*BLACK)
        self.set_line_width(0.5)
        self.rect(x, y, w, h, "DF" if border else "F")
        self.set_line_width(0.2)

    def chip(self, x, y, text, size=9, fill=YELLOW, fg=BLACK, padx=2.6, h=6.2):
        self.set_font("Rb", "B", size)
        w = self.get_string_width(text) + 2 * padx
        self.set_fill_color(*fill)
        self.set_draw_color(*BLACK)
        self.set_line_width(0.4)
        self.rect(x, y, w, h, "DF")
        self.set_line_width(0.2)
        self.set_text_color(*fg)
        self.set_xy(x, y)
        self.cell(w, h, text, align="C")
        self.set_text_color(*BLACK)
        return w

    def dashed_rect(self, x, y, w, h):
        self.set_draw_color(*BLACK)
        self.set_line_width(0.4)
        self.set_dash_pattern(dash=1.4, gap=1.4)
        self.rect(x, y, w, h)
        self.set_dash_pattern()
        self.set_line_width(0.2)


# ---------------------------------------------------------------- страницы
def cover(p):
    p.blank()
    p.folio = False
    p.set_text_color(*BLACK)
    p.set_font("Rb", "B", 16)
    p.set_xy(ML + 2, 17)
    p.cell(80, 8, "МЫ ОБЪЯСНЯЕМ")

    p.set_font("Bk", "", 78)
    x, y = ML + 1, 28.0
    p.set_text_color(*PINK)
    p.set_xy(x + 2.4, y + 2.4)
    p.cell(120, 28, "RWA*")
    p.set_text_color(*BLACK)
    p.set_xy(x, y)
    p.cell(120, 28, "RWA*")

    y = 100.0
    step = 7.4
    for i, w in enumerate(CODEWORDS):
        p.set_font("Rb", "B", 10.5)
        p.set_text_color(*(PINK if i % 2 else BLACK))
        p.set_xy(ML + 2, y)
        p.cell(CW - 4, 5, "%02d %s" % (i + 1, w))
        p.set_draw_color(*BLACK)
        p.set_line_width(0.4)
        p.line(ML + 2, y + 5.6, PW - MR - 2, y + 5.6)
        y += step

    p.set_text_color(*BLACK)
    p.set_font("Rb", "B", 10.5)
    p.set_xy(ML + 2, 206)
    p.multi_cell(CW - 4, 5.8,
                 "Книга-курс. Тринадцать глав. Без сигналов.\n"
                 "Жёлтое существует. Розовое работает.")
    p.set_font("Rb", "B", 8)
    p.set_xy(ML + 2, 222)
    p.cell(60, 5, sp("YURICH · 2026", " "))
    p.folio = True


def front_page(p, title, blocks):
    p.running = None
    p.text_page()
    p.set_font("Bk", "", 24)
    p.set_text_color(*BLACK)
    p.set_xy(ML, 20)
    p.multi_cell(CW, 11, title)
    p.set_y(p.get_y() + 5)
    p.set_draw_color(*PINK)
    p.set_line_width(1.2)
    p.line(ML, p.get_y(), ML + 28, p.get_y())
    p.set_line_width(0.2)
    p.set_y(p.get_y() + 6)
    for b in blocks:
        if b[0] == "p":
            body_par(p, b[1])


def body_par(p, txt, size=BODY_PT, style="", gap=3.2):
    """Абзац с выключкой по формату и перетеканием на следующую полосу."""
    t = md_inline(txt)
    p.set_font("Rb", style, size)
    lines = p.multi_cell(CW, LH, t, align="J", dry_run=True, output="LINES", markdown=True)
    lines = [l for l in lines]
    while lines:
        if p.get_y() + LH * 2 > BODY_BOTTOM:
            p.text_page()
        fit = max(1, int((BODY_BOTTOM - p.get_y()) // LH))
        chunk, lines = lines[:fit], lines[fit:]
        p.set_font("Rb", style, size)
        p.set_text_color(*BLACK)
        p.set_x(ML)
        p.multi_cell(CW, LH, " ".join(x.strip() for x in chunk), align="J", markdown=True,
                     new_x="LMARGIN", new_y="NEXT")
    p.set_y(p.get_y() + gap)


def h2(p, txt):
    p.need(16)
    p.set_y(p.get_y() + 3.0)
    p.set_font("Bk", "", 14)
    p.set_text_color(*BLACK)
    p.set_x(ML)
    p.multi_cell(CW, 7.2, txt)
    p.set_y(p.get_y() + 2.6)


def block_plashka(p, rows):
    items, caption = [], None
    for r in rows:
        if re.match(r"^\*[^*].*\*$", r) or (r.startswith("*") and not r.startswith("**")):
            caption = plain(r)
        else:
            m = re.match(r"\*\*(.+?)\*\*\s*[—–-]?\s*(.*)", clean(r))
            if m:
                items.append((plain(m.group(1)), plain(m.group(2))))
            elif r.strip():
                items.append((plain(r), ""))

    if len(items) == 2:
        h = 24.0
        total = h + (7.0 if caption else 0) + 6
        p.need(total)
        y = p.get_y()
        gap = 3.0
        w = (CW - gap) / 2
        for k, (label, val) in enumerate(items):
            x = ML + k * (w + gap)
            fill = YELLOW if k == 0 else PINK
            fg = BLACK if k == 0 else WHITE
            p.shadow_rect(x, y, w, h, fill)
            p.set_text_color(*fg)
            p.set_font("Rb", "B", 13)
            p.set_xy(x + 4, y + 4.5)
            p.cell(w - 8, 7, label)
            p.set_font("Rb", "", 10.5)
            p.set_xy(x + 4, y + 12.5)
            p.multi_cell(w - 8, 5, val)
            p.set_draw_color(*(BLACK if k == 0 else WHITE))
            p.set_line_width(0.9)
            p.line(x + 4, y + h - 3.4, x + w * 0.62, y + h - 3.4)
            p.set_line_width(0.2)
        yy = y + h
        if caption:
            p.set_fill_color(*BLACK)
            p.rect(ML, yy, CW, 7.0, "F")
            p.set_text_color(*WHITE)
            p.set_font("Rb", "B", 8.5)
            p.set_xy(ML + 4, yy)
            p.cell(CW - 8, 7.0, caption)
            yy += 7.0
        p.set_text_color(*BLACK)
        p.set_y(yy + 5)
        return

    # нейтральный бокс
    p.set_font("Rb", "", 10)
    hh = 5.5
    body_rows = []
    for label, val in items:
        body_rows.append((label, val))
    h = 5 + len(body_rows) * (hh + 1.4) + (6 if caption else 0)
    p.need(h + 6)
    y = p.get_y()
    p.shadow_rect(ML, y, CW, h, CREAM, off=1.4)
    p.set_fill_color(*BLACK)
    p.rect(ML, y, 3.0, h, "F")
    yy = y + 3.4
    for label, val in body_rows:
        p.set_font("Rb", "B", 10)
        p.set_text_color(*BLACK)
        p.set_xy(ML + 6.5, yy)
        lw = p.get_string_width(label + " ")
        p.cell(lw, hh, label)
        p.set_font("Rb", "", 10)
        p.set_xy(ML + 6.5 + lw, yy)
        p.multi_cell(CW - 12 - lw, hh, val)
        yy += hh + 1.4
    if caption:
        p.set_font("Rb", "I", 9)
        p.set_text_color(*PINK)
        p.set_xy(ML + 6.5, yy - 0.5)
        p.cell(CW - 12, 5, caption)
        p.set_text_color(*BLACK)
    p.set_y(y + h + 5)


def block_slot(p, kind, desc):
    p.set_font("Rb", "", 9.5)
    n = len(p.multi_cell(CW - 14, 5, clean(desc), dry_run=True, output="LINES", markdown=False))
    h = 14 + max(1, n) * 5
    p.need(h + 6)
    y = p.get_y()
    p.dashed_rect(ML, y, CW, h)
    p.chip(ML + 4, y + 4, "МЕСТО: " + kind, size=8, h=5.6)
    p.set_font("Rb", "", 9.5)
    p.set_text_color(70, 66, 60)
    p.set_xy(ML + 7, y + 11.5)
    p.multi_cell(CW - 14, 5, clean(desc))
    p.set_text_color(*BLACK)
    p.set_y(y + h + 5)


def block_itog(p, txt):
    p.set_font("Rb", "B", 10.5)
    inner = CW - 34
    n = len(p.multi_cell(inner, 5.4, txt, dry_run=True, output="LINES", markdown=False))
    h = max(11.5, 6 + n * 5.4)
    p.need(h + 6)
    y = p.get_y()
    p.shadow_rect(ML, y, CW, h, BLACK)
    p.chip(ML + 3, y + (h - 6.6) / 2, "ИТОГ", size=10, h=6.6)
    p.set_text_color(*WHITE)
    p.set_font("Rb", "B", 10.5)
    p.set_xy(ML + 28, y + (h - n * 5.4) / 2)
    p.multi_cell(inner, 5.4, txt)
    p.set_text_color(*BLACK)
    p.set_y(y + h + 5)


def part_page(p, roman, name, chapters):
    p.running = None
    p.blank()
    p.footer_bar()
    p.set_font("Rb", "B", 9)
    p.set_text_color(*BLACK)
    p.set_xy(ML, 24)
    p.cell(60, 5, sp("ЧАСТЬ"))

    p.set_font("Bk", "", 96)
    p.set_text_color(*PINK)
    p.set_xy(ML + 3.0, 36)
    p.cell(120, 34, roman)
    p.set_text_color(*BLACK)
    p.set_xy(ML, 33)
    p.cell(120, 34, roman)

    p.set_font("Bk", "", 26)
    p.set_xy(ML, 92)
    p.multi_cell(CW, 12, name)

    y = 130.0
    for ch in chapters:
        p.set_font("Rb", "B", 11)
        p.set_text_color(*PINK)
        p.set_xy(ML, y)
        p.cell(11, 6, ch["num"])
        p.set_text_color(*BLACK)
        p.set_xy(ML + 11, y)
        p.multi_cell(CW - 11, 6, ch["title"].capitalize())
        y = max(p.get_y(), y + 6) + 0.4
        p.set_draw_color(*BLACK)
        p.set_line_width(0.4)
        p.line(ML, y, PW - MR, y)
        y += 3.6


def chapter_title_page(p, ch, roman):
    p.running = None
    p.blank()
    p.chip(ML, 18, ch["num"], size=11, h=8.0)

    p.set_font("Bk", "", 30)
    p.set_text_color(*BLACK)
    p.set_xy(ML, 30)
    p.multi_cell(CW, 13, ch["title"])
    y = p.get_y() + 2

    hook = ch["thesis"].strip()
    if hook:
        parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", hook) if s.strip()]
        p.set_font("Rb", "B", 11)
        p.set_text_color(*PINK)
        p.set_xy(ML, y)
        p.multi_cell(CW, 6, parts[-1])
        p.set_text_color(*BLACK)

    rows = ch["chips"]
    rh = 9.2
    h = rows and (len(rows) * rh + 4) or 0
    top = 118.0
    if rows:
        p.shadow_rect(ML, top, CW, h, CREAM, off=2.2)
        p.set_fill_color(*BLACK)
        p.rect(ML, top, 3.0, h, "F")
        yy = top + 2
        for k, (label, val) in enumerate(rows):
            p.set_font("Rb", "B", 10)
            p.set_text_color(*BLACK)
            p.set_xy(ML + 7, yy)
            p.cell(CW * 0.5, rh, label)
            p.set_font("Rb", "", 9.5)
            p.set_xy(ML + CW * 0.5, yy)
            p.cell(CW * 0.5 - 6, rh, val, align="R")
            if k < len(rows) - 1:
                p.set_draw_color(150, 143, 130)
                p.set_dash_pattern(dash=0.8, gap=1.2)
                p.line(ML + 7, yy + rh, PW - MR - 6, yy + rh)
                p.set_dash_pattern()
            yy += rh

    p.set_font("Rb", "B", 11)
    p.set_text_color(*BLACK)
    p.set_xy(ML, top + h + 5)
    p.multi_cell(CW, 6, ch["thesis"])

    # футер полосы главы
    y = 229.5
    p.set_draw_color(*BLACK)
    p.set_line_width(0.5)
    p.line(ML, y, PW - MR, y)
    p.set_line_width(0.2)
    p.set_font("Rb", "B", 8)
    p.set_xy(ML, y + 3)
    p.cell(60, 5, sp("YURICH RWA"))
    p.set_xy(PW - MR - 60, y + 3)
    p.cell(60, 5, sp("ЧАСТЬ " + roman), align="R")


def chapter_body(p, ch):
    p.running = "%s %s" % (ch["num"], ch["title"])
    p.text_page()
    if ch["kicker"]:
        p.set_font("Rb", "B", 9.5)
        p.set_text_color(*PINK)
        p.set_x(ML)
        p.cell(CW, 5.4, ch["kicker"])
        p.set_y(p.get_y() + 6.4)
        p.set_text_color(*BLACK)
    first = True
    for b in ch["blocks"]:
        if b[0] == "p":
            body_par(p, b[1], style="B" if first else "")
            first = False
        elif b[0] == "h2":
            h2(p, b[1])
        elif b[0] == "plashka":
            block_plashka(p, b[1])
        elif b[0] == "slot":
            block_slot(p, b[1], b[2])
        elif b[0] == "itog":
            block_itog(p, b[1])


def toc_page(p, entries):
    p.running = "СОДЕРЖАНИЕ"
    p.text_page()
    p.set_font("Bk", "", 24)
    p.set_text_color(*BLACK)
    p.set_xy(ML, 21)
    p.cell(CW, 12, "ТРИНАДЦАТЬ ГЛАВ")
    y = 40.0
    part_seen = set()
    for num, title, pageno, partname in entries:
        if partname not in part_seen:
            part_seen.add(partname)
            p.set_font("Rb", "B", 8)
            p.set_text_color(120, 112, 100)
            p.set_xy(ML, y + 1)
            p.cell(CW, 5, sp(partname))
            y += 7.5
        p.set_draw_color(*BLACK)
        p.set_line_width(0.4)
        p.line(ML, y, PW - MR, y)
        p.set_font("Rb", "B", 10.5)
        p.set_text_color(*PINK)
        p.set_xy(ML, y + 1.6)
        p.cell(10, 6, num)
        p.set_text_color(*BLACK)
        p.set_xy(ML + 10, y + 1.6)
        p.cell(CW - 26, 6, title.capitalize())
        p.set_font("Rb", "B", 10.5)
        p.set_xy(PW - MR - 16, y + 1.6)
        p.cell(16, 6, str(pageno) if pageno else "", align="R")
        y += 9.2
    p.set_text_color(*BLACK)


def glossary(p, terms):
    p.running = "СЛОВАРЬ ПОД РУКОЙ"
    p.text_page()
    p.set_font("Bk", "", 24)
    p.set_xy(ML, 21)
    p.cell(CW, 12, "СЛОВАРЬ ПОД РУКОЙ")
    p.set_y(40)
    p.set_font("Rb", "I", 9.5)
    p.set_text_color(*PINK)
    p.set_x(ML)
    p.multi_cell(CW, 5, "Короткие определения на языке этой книги. Полный глоссарий: t.me/YuRichRWA")
    p.set_text_color(*BLACK)
    p.set_y(p.get_y() + 4)
    for term, d in terms:
        p.set_font("Rb", "", 9.5)
        n = len(p.multi_cell(CW - 4, 5.0, d, dry_run=True, output="LINES", markdown=False))
        if p.get_y() + 5.6 + n * 5.0 > BODY_BOTTOM:
            p.text_page()
        y = p.get_y()
        p.set_font("Rb", "B", 10)
        p.set_text_color(*BLACK)
        p.set_xy(ML, y)
        p.cell(CW, 5.4, term)
        p.set_draw_color(*PINK)
        p.set_line_width(0.6)
        p.line(ML, y + 5.4, ML + 10, y + 5.4)
        p.set_line_width(0.2)
        p.set_font("Rb", "", 9.5)
        p.set_xy(ML + 4, y + 6.0)
        p.multi_cell(CW - 4, 5.0, d)
        p.set_y(p.get_y() + 3.2)


def ending(p, dalshe, kolofon):
    p.running = "ЧТО ДАЛЬШЕ"
    p.text_page()
    p.set_font("Bk", "", 24)
    p.set_xy(ML, 21)
    p.cell(CW, 12, "ЧТО ДАЛЬШЕ")
    p.set_y(42)
    for par in dalshe:
        body_par(p, par)

    # колофон
    p.running = None
    p.blank()
    p.footer_bar()
    p.set_font("Bk", "", 20)
    p.set_xy(ML, 150)
    p.cell(CW, 10, "КОЛОФОН")
    p.set_y(165)
    p.set_font("Rb", "", 10)
    for ln in kolofon:
        if "t.me" in ln or "Севастополь" in ln:
            continue
        p.set_x(ML)
        p.multi_cell(CW, 5.6, ln)
    p.set_y(p.get_y() + 6)
    p.set_font("Rb", "B", 11)
    p.set_text_color(*PINK)
    p.set_x(ML)
    p.cell(CW, 6, "t.me/YuRichRWA · Севастополь · 2026")
    p.set_text_color(*BLACK)


# ---------------------------------------------------------------- сборка
def build(toc_numbers=None):
    front = parse_front()
    terms, dalshe, kolofon = parse_back()
    chapters = {}
    for roman, pname, files in PARTS:
        for f in files:
            chapters[f] = parse_chapter(f)

    p = Book()
    cover(p)
    front_page(p, "КАК СМОТРЕТЬ ЭТУ КНИГУ", front.get("КАК СМОТРЕТЬ ЭТУ КНИГУ", []))
    front_page(p, "ОТ АВТОРА", front.get("ОТ АВТОРА", []))

    entries = []
    for roman, pname, files in PARTS:
        for f in files:
            ch = chapters[f]
            entries.append((ch["num"], ch["title"], (toc_numbers or {}).get(ch["num"], 0),
                            "ЧАСТЬ %s · %s" % (roman, pname)))
    toc_page(p, entries)

    starts = {}
    for roman, pname, files in PARTS:
        part_page(p, roman, pname, [chapters[f] for f in files])
        for f in files:
            ch = chapters[f]
            chapter_title_page(p, ch, roman)
            starts[ch["num"]] = p.page_no()
            chapter_body(p, ch)

    glossary(p, terms)
    ending(p, dalshe, kolofon)
    return p, starts


def main():
    _, starts = build()             # первый проход — узнаём номера полос
    p, _ = build(starts)            # второй — с настоящим содержанием
    p.output(OUT)
    print("OK:", OUT, "полос:", p.page_no())


if __name__ == "__main__":
    main()
