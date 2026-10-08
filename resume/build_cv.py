#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сборка резюме Pavel Yurich Vasilkovsky → Head of RWA (Solana Foundation).

    pip install --break-system-packages fpdf2
    python3 resume/build_cv.py

Результат:
    resume/Pavel-Yurich-Vasilkovsky-Head-of-RWA-EN.pdf
    resume/Pavel-Yurich-Vasilkovsky-Head-of-RWA-RU.pdf
    resume/CV-EN.md, resume/CV-RU.md   (тот же текст для ATS и LinkedIn)

Содержание правится в resume/cv_content.py, вёрстка — здесь.
"""

import os
import re
import sys

from fpdf import FPDF

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cv_content import CONTENT  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")

# ─────────────────────────────────────────────────────────────── палитра / метрика
INK = (17, 19, 26)            # почти чёрный
INK_SOFT = (74, 79, 94)       # основной серый тон
GRAY = (122, 128, 145)        # подписи
HAIR = (206, 210, 222)        # волосяные линии
ACCENT = (91, 61, 245)        # сдержанный акцент
PAGE_W, PAGE_H = 210.0, 297.0
ML, MR = 16.5, 16.5
MT, MB = 14.5, 13.0
CW = PAGE_W - ML - MR
LH = 4.35                     # интерлиньяж тела
LH_SM = 4.1


def _deaccent(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"\1", text)


class CV(FPDF):
    def __init__(self, meta, lang):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.meta = meta
        self.lang = lang
        self.set_margins(ML, MT, MR)
        self.set_auto_page_break(True, margin=MB)
        self.set_title(meta["title"])
        self.set_author("Pavel Yurich Vasilkovsky")
        self.set_subject("Curriculum Vitae — Head of RWA, Solana Foundation")
        self.set_keywords("RWA, tokenization, Solana, TVL, issuer pipeline, DeFi, CFA, "
                          "digital assets, institutional growth, liquidity")
        self.set_creator("resume/build_cv.py")
        self.set_lang(meta["lang"])
        self.set_text_color(*INK)
        # RU-текст длиннее в знаках — сажаем кегль и интерлиньяж плотнее, чтобы держать две страницы
        if lang == "ru":
            self.bsize, self.blh, self.blh_sm = 8.55, 4.12, 3.95
        else:
            self.bsize, self.blh, self.blh_sm = 9.0, LH, LH_SM
        self._register_fonts()

    # ————————————————————————————————————————————— шрифты
    def _register_fonts(self):
        f = lambda n: os.path.join(FONTS, n)  # noqa: E731
        self.add_font("Sans", "", f("IBMPlexSans_400Regular.ttf"))
        self.add_font("Sans", "B", f("IBMPlexSans_600SemiBold.ttf"))
        self.add_font("SansI", "B", f("IBMPlexSans_500Medium.ttf"))
        self.add_font("Serif", "", f("IBMPlexSerif_400Regular.ttf"))
        self.add_font("Serif", "B", f("IBMPlexSerif_600SemiBold.ttf"))
        self.add_font("Mono", "", f("IBMPlexMono_400Regular.ttf"))
        self.add_font("MonoM", "", f("IBMPlexMono_500Medium.ttf"))

    # ————————————————————————————————————————————— колонтитул
    def footer(self):
        if self.page_no() == 1:
            base = PAGE_H - MB
        else:
            base = PAGE_H - MB
        self.set_draw_color(*HAIR)
        self.set_line_width(0.2)
        self.line(ML, base, PAGE_W - MR, base)
        self.set_y(base + 1.0)
        self.set_font("Mono", "", 6.6)
        self.set_text_color(*GRAY)
        self.set_x(ML)
        self.cell(CW * 0.72, 3.6, self.meta["footer_left"], align="L")
        self.set_x(PAGE_W - MR - CW * 0.28)
        self.cell(CW * 0.28, 3.6, f"{self.page_no()} / {{nb}}", align="R")

    # ————————————————————————————————————————————— служебные рисовалки
    def rule(self, x1, x2, y, color=HAIR, w=0.2):
        self.set_draw_color(*color)
        self.set_line_width(w)
        self.line(x1, x2, y) if False else self.line(x1, y, x2, y)

    def text_block(self, body, x, y, w, size=None, lh=None, color=INK_SOFT, family="Sans"):
        size = self.bsize if size is None else size
        lh = self.blh if lh is None else lh
        self.set_xy(x, y)
        self.set_font(family, "", size)
        self.set_text_color(*color)
        self.multi_cell(w, lh, body, markdown=True)
        return self.get_y()

    def section(self, label):
        need = 22.0
        if self.get_y() + need > PAGE_H - MB - 6:
            self.add_page()
        y = self.get_y() + 5.0
        self.set_xy(ML, y)
        self.set_font("MonoM", "", 7.4)
        self.set_text_color(*ACCENT)
        if hasattr(self, "set_char_spacing"):
            self.set_char_spacing(0.45)
        lw = self.get_string_width(label.upper()) + 0.45 * len(label)
        self.cell(lw, 4.0, label.upper(), align="L")
        if hasattr(self, "set_char_spacing"):
            self.set_char_spacing(0.45)
        x_line = ML + lw + 3.0
        self.set_draw_color(*HAIR)
        self.set_line_width(0.2)
        self.line(x_line, y + 2.1, PAGE_W - MR, y + 2.1)
        if hasattr(self, "set_char_spacing"):
            self.set_char_spacing(0.0)
        self.set_y(y + 4.3)

    def bullets(self, items, x=ML, w=CW, size=None):
        size = self.bsize if size is None else size
        for it in items:
            if self.get_y() + 6.0 > PAGE_H - MB - 4:
                self.add_page()
            y = self.get_y()
            self.set_xy(x, y)
            self.set_font("Sans", "", size)
            self.set_text_color(*GRAY)
            self.cell(3.6, self.blh, "—", align="L")
            self.set_xy(x + 3.6, y)
            self.set_font("Sans", "", size)
            self.set_text_color(*INK_SOFT)
            self.multi_cell(w - 3.6, self.blh, it, markdown=True)
            self.set_y(self.get_y() + 1.9)

    def kv_rows(self, items, x=ML, w=CW, size=None, label_w=33.0):
        size = self.bsize if size is None else size
        for label, value in items:
            if self.get_y() + 8.0 > PAGE_H - MB - 4:
                self.add_page()
            y = self.get_y()
            self.set_xy(x, y)
            self.set_font("Sans", "B", size)
            self.set_text_color(*INK)
            self.multi_cell(label_w - 2.0, LH_SM, label, align="L")
            y_lab_end = self.get_y()
            self.set_xy(x + label_w, y)
            self.set_font("Sans", "", size)
            self.set_text_color(*INK_SOFT)
            self.multi_cell(w - label_w, LH_SM, value)
            self.set_y(max(self.get_y(), y_lab_end) + 1.9)

    def paragraphs(self, items, size=None, gap=2.2):
        """Абзацы свободного текста — без маркеров списка."""
        size = self.bsize if size is None else size
        for para in items:
            if self.get_y() + 9.0 > PAGE_H - MB - 4:
                self.add_page()
            y = self.get_y()
            self.set_xy(ML, y)
            self.set_font("Sans", "", size)
            self.set_text_color(*INK_SOFT)
            self.multi_cell(CW, self.blh, para, markdown=True)
            self.set_y(self.get_y() + gap)

    def role(self, item, size=None):
        size = self.bsize if size is None else size
        if self.get_y() + 20.0 > PAGE_H - MB - 4:
            self.add_page()
        y = self.get_y()
        # организация — слева, даты — справа по краю
        self.set_xy(ML, y)
        self.set_font("Sans", "B", 9.7)
        self.set_text_color(*INK)
        self.cell(CW - 30.0, 4.6, item["org"], align="L")
        self.set_xy(PAGE_W - MR - 30.0, y + 0.3)
        self.set_font("Mono", "", 7.2)
        self.set_text_color(*GRAY)
        self.cell(30.0, 4.2, item["dates"], align="R")
        # подзаголовок
        self.set_xy(ML, y + 4.5)
        self.set_font("SansI", "B", 8.5)
        self.set_text_color(*ACCENT)
        self.multi_cell(CW, 4.0, item["meta"])
        self.set_y(self.get_y() + 1.5)
        if item.get("paras"):
            self.paragraphs(item["paras"], size=size, gap=2.0)
        else:
            self.bullets(item.get("bullets", []), size=size)
        self.set_y(self.get_y() + 1.2)


def build(lang):
    meta = CONTENT[lang]
    pdf = CV(meta, lang)
    pdf.set_auto_page_break(False)
    pdf.add_page()

    # ── шапка
    y = MT + 1.2
    pdf.set_fill_color(*ACCENT)
    pdf.rect(ML, y, 17.0, 1.4, style="F")
    name_y = y + 3.4
    pdf.set_xy(ML, name_y)
    pdf.set_font("Serif", "B", 20.5)
    pdf.set_text_color(*INK)
    if hasattr(pdf, "set_char_spacing"):
        pdf.set_char_spacing(0.35)
    pdf.cell(CW, 10.0, meta["name"], align="L")
    if hasattr(pdf, "set_char_spacing"):
        pdf.set_char_spacing(0.0)

    y = name_y + 10.2
    pdf.set_xy(ML, y)
    pdf.set_font("MonoM", "", 8.0)
    pdf.set_text_color(*ACCENT)
    if hasattr(pdf, "set_char_spacing"):
        pdf.set_char_spacing(0.25)
    pdf.cell(CW, 4.4, meta["role"].upper(), align="L")
    if hasattr(pdf, "set_char_spacing"):
        pdf.set_char_spacing(0.0)
    y += 4.7
    pdf.set_xy(ML, y)
    pdf.set_font("Sans", "", 8.4)
    pdf.set_text_color(*INK_SOFT)
    pdf.cell(CW, 4.2, meta["subrole"], align="L")

    # ── контакты потоком, каждый со своей ссылкой; разделитель остаётся со следующим
    y += 5.0
    pdf.set_font("Sans", "", 8.1)
    sep = "  ·  "
    sepw = pdf.get_string_width(sep)
    x = ML
    pdf.set_xy(x, y)
    for i, (text, href) in enumerate(meta["contacts"]):
        w = pdf.get_string_width(text)
        lead = sepw if i else 0.0
        if x + lead + w > PAGE_W - MR:
            y += 4.1
            x = ML
            lead = 0.0
        pdf.set_xy(x, y)
        if lead:
            pdf.set_text_color(*GRAY)
            pdf.cell(lead, 4.1, sep)
            x += lead
            pdf.set_xy(x, y)
        pdf.set_text_color(*INK_SOFT)
        pdf.cell(w + 0.4, 4.1, text, link=href)
        x += w + 0.4
        pdf.set_xy(x, y)

    y += 4.6
    pdf.set_xy(ML, y)
    pdf.set_font("Sans", "B", 8.1)
    pdf.set_text_color(*INK)
    pdf.multi_cell(CW, 4.1, meta["availability"], markdown=True)
    y = pdf.get_y() + 2.0

    pdf.set_draw_color(*INK)
    pdf.set_line_width(0.35)
    pdf.line(ML, y, PAGE_W - MR, y)
    pdf.set_y(y + 0.5)
    pdf.set_auto_page_break(True, margin=MB)

    # ── секции
    for s in meta["sections"]:
        pdf.section(s["label"])
        for b in s["blocks"]:
            if b["kind"] == "text":
                pdf.set_y(pdf.text_block(b["body"], ML, pdf.get_y(), CW) + 1.2)
            elif b["kind"] == "bullets":
                pdf.bullets(b["items"])
            elif b["kind"] == "prose":
                pdf.paragraphs(b["items"])
            elif b["kind"] == "kv":
                pdf.kv_rows(b["items"], label_w=36.0 if lang == "ru" else 34.0)
            elif b["kind"] == "roles":
                for item in b["items"]:
                    pdf.role(item)

    out = os.path.join(HERE, meta["file"])
    pdf.output(out)
    return out, pdf.page_no()


def to_markdown(lang):
    meta = CONTENT[lang]
    L = []
    L.append(f"# {meta['name']}")
    L.append(f"**{meta['role']}**  ")
    L.append(f"{meta['subrole']}  ")
    L.append(" · ".join(t for t, _ in meta["contacts"]))
    L.append(f"{meta['availability']}")
    L.append("")
    for s in meta["sections"]:
        L.append(f"## {s['label']}")
        for b in s["blocks"]:
            if b["kind"] == "text":
                L.append(b["body"])
                L.append("")
            elif b["kind"] == "bullets":
                for it in b["items"]:
                    L.append(f"- {it}")
                L.append("")
            elif b["kind"] == "kv":
                for label, value in b["items"]:
                    L.append(f"- **{label}.** {value}")
                L.append("")
            elif b["kind"] == "prose":
                for para in b["items"]:
                    L.append(para)
                    L.append("")
            elif b["kind"] == "roles":
                for it in b["items"]:
                    L.append(f"### {it['org']} — {it['dates']}")
                    L.append(f"*{it['meta']}*")
                    L.append("")
                    if it.get("paras"):
                        for para in it["paras"]:
                            L.append(para)
                            L.append("")
                    else:
                        for bull in it.get("bullets", []):
                            L.append(f"- {bull}")
                        L.append("")
    path = os.path.join(HERE, f"CV-{lang.upper()}.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L).rstrip() + "\n")
    return path


if __name__ == "__main__":
    for lang in ("en", "ru"):
        out, pages = build(lang)
        md = to_markdown(lang)
        print(f"{lang.upper()}: {os.path.basename(out)} — {pages} стр. | {os.path.basename(md)}")
