#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_wally_emoji.py
===================

Собирает набор кастом-эмодзи Телеграма с WALLY — слоном RWA Foundation
(@RWAFoundation_). Персонаж снят с исходных фото в корне репозитория
(«слон эмодзи*.jpg»), генерации лежат в raw/ на белом фоне.

Исходники (raw/, белый фон):
    wally.png         — базовый образ по ТЗ
    wally_crown.png   — золотая корона
    wally_cap.png     — оранжевая кепка задом наперёд
    wally_tophat.png  — чёрный цилиндр с оранжевым кантом
    wally_party.png   — оранжевый колпак с золотым помпоном
    wally_grad.png    — магистерская шапочка с кисточкой

Результат:
    png512/*.png    — мастера 512×512: прозрачный фон + белый
                      стикер-контур ~9 px
    webp100/*.webp  — готовые к загрузке 100×100 WEBP (< 64 КБ)
    preview.png     — общий лист-превью (checkerboard + тёмная полоса)

Конвейер:
  1. Фон -> прозрачность заливкой ОТ УГЛОВ (floodfill с
     сентинел-цветом); работает и для белого, и для чёрного фона.
     Убирается только фон, связанный с краями кадра, поэтому белые
     бивни и зубы ВНУТРИ морды не страдают. У генераций с чёрным
     фоном родной внешний контур сливается с фоном — скрипт
     дорисовывает его заново (add_contour, BLACK_PX).
  2. Сглаживание альфы (гаусс) и ресайз LANCZOS -> 512.
  3. Белый стикер-контур: дилатация альфы MaxFilter, подложка белым.
  4. Вписывание в квадрат 512×512 по центру, заполнение ~90%.
  5. Даунскейл до 100×100 LANCZOS + UnsharpMask только по RGB
     (альфа не трогается, чтобы не было ореолов), WEBP lossless.

Запуск:
    pip install --break-system-packages pillow
    python3 brand/emoji/wally/make_wally_emoji.py
    python3 brand/emoji/wally/make_wally_emoji.py --preview
    python3 brand/emoji/wally/make_wally_emoji.py --only wally_crown
"""

import argparse
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------------------
# Пути и константы
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
PNG512 = os.path.join(HERE, "png512")
WEBP100 = os.path.join(HERE, "webp100")

MASTER = 512          # размер мастера-стикера
EMOJI = 100           # размер кастом-эмодзи Telegram
OUTLINE_PX = 9        # белый контур в масштабе 512 px
BLACK_PX = 13         # восстановленный чёрный контур (для тёмного фона)
FILL = 0.90           # какую долю канвы занимает контент
MAX_BYTES = 64 * 1024 # лимит Telegram для эмодзи
SENTINEL = (255, 0, 255)

STICKERS = [
    # (имя, подпись, эмодзи для привязки, ink-буст)
    ("wally",        "базовый WALLY",              "🐘", False),
    ("wally_crown",  "корона (кит-король)",        "👑", True),
    ("wally_cap",    "оранжевая кепка",            "🧢", True),
    ("wally_tophat", "цилиндр с оранжевым кантом", "🎩", True),
    ("wally_party",  "колпак с помпоном",          "🎉", True),
    ("wally_grad",   "магистерская шапочка",       "🎓", True),
]

# ---------------------------------------------------------------------------
# Утилиты
# ---------------------------------------------------------------------------
def _font(size, bold=True):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    for p in (
            f"/usr/share/fonts/truetype/dejavu/{name}",
            f"/usr/share/fonts/dejavu/{name}"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)


def content_bbox(alpha, thresh=8):
    """BBox пикселей альфы > thresh."""
    mask = alpha.point(lambda v: 255 if v > thresh else 0)
    return mask.getbbox()


def remove_bg(img):
    """
    Однотонный фон -> прозрачность (белый ИЛИ чёрный фон).

    Floodfill от углов и середин краёв сентинел-цветом. В альфу уходит
    только область, связанная с краями кадра, — внутренние светлые
    детали (бивни, зубы, блики на очках) остаются на месте.

    Тёмный фон — особый случай: внешний чёрный контур персонажа
    сливается с фоном и уходит вместе с ним, поэтому вызывающая
    сторона потом дорисовывает контур заново (add_contour).

    Возвращает (rgba, kept_fraction, corner, dark_bg).
    """
    rgba = img.convert("RGBA")
    a = rgba.split()[3]
    if a.getextrema()[0] < 64:          # исходник уже с прозрачностью
        return rgba, -1.0, None, False

    rgb = rgba.convert("RGB")
    w, h = rgb.size
    corners = [rgb.getpixel(p) for p in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
    corner = tuple(sum(c[i] for c in corners) // 4 for i in range(3))
    dark_bg = sum(corner) < 200         # чёрный/тёмный фон

    for thresh in (36, 26, 16, 10):
        work = rgb.copy()
        seeds = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
                 (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]
        for s in seeds:
            if work.getpixel(s) != SENTINEL:
                try:
                    ImageDraw.floodfill(work, s, SENTINEL, thresh=thresh)
                except Exception:
                    pass

        # маска «фон закрашен сентинелом» через попиксельное сравнение
        r, g, b = work.split()
        dr = ImageChops.difference(r, Image.new("L", work.size, SENTINEL[0]))
        dg = ImageChops.difference(g, Image.new("L", work.size, SENTINEL[1]))
        db = ImageChops.difference(b, Image.new("L", work.size, SENTINEL[2]))
        prod = ImageChops.multiply(ImageChops.multiply(dr, dg), db)
        # prod == 0 ровно там, где сентинел; инвертируем -> альфа
        alpha = prod.point(lambda v: 0 if v == 0 else 255)

        hist = alpha.histogram()
        kept = hist[255] / (w * h)
        lo, hi = (0.12, 0.985) if not dark_bg else (0.10, 0.90)
        if lo <= kept <= hi:
            # лёгкое сглаживание жёсткой границы заливки
            alpha = alpha.filter(ImageFilter.GaussianBlur(1.0))
            out = rgba.copy()
            out.putalpha(alpha)
            return out, kept, corner, dark_bg
        # иначе: заливка «утекла» внутрь персонажа или не нашла фон —
        # пробуем более строгий порог

    # ничего не вышло — отдаём как есть с предупреждением
    print("  !! фон не распознан, оставляю без прозрачности "
          f"(угол={corner})", file=sys.stderr)
    return rgba, 1.0, corner, dark_bg


def ink_boost(img, power=2.9, knee=178, spread=32):
    """
    Приводит мягкие серые контуры/линзы к «жирному чёрному» стилю
    базового WALLY (у второй модели генерации контуры выходят
    серыми ~90-130 вместо чёрных).

    Степенная кривая f(l) = l^power / knee^(power-1) применяется
    ТОЛЬКО к нейтральным пикселям (max-min <= spread): контуры,
    очки, серые тени. Насыщенные цвета — оранжевая кепка, золотая
    корона — не трогаются, чтобы не потерять фирменные цвета.
    Светлое (l >= knee) не меняется вовсе.
    """
    lut = [0] * 256
    for l in range(1, 256):
        lut[l] = l if l >= knee else min(255, round(l ** power / knee ** (power - 1)))
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 8 and max(r, g, b) - min(r, g, b) <= spread:
                l = (r + g + b) // 3
                if l:
                    s = lut[l] / l
                    px[x, y] = (round(r * s), round(g * s), round(b * s), a)
    return img


def add_contour(img, px, color=(0, 0, 0, 255)):
    """
    Контур цветом `color` строго ПОД персонажем: дилатация альфы.

    Так восстанавливается внешний чёрный контур у генераций с тёмным
    фоном (там родной контур сливается с фоном и уходит при заливке).
    """
    a = img.split()[3]
    dil = a.filter(ImageFilter.MaxFilter(2 * px + 1))
    ring = Image.new("RGBA", img.size, color)
    ring.putalpha(dil)
    return Image.alpha_composite(ring, img)


def add_white_outline(img, px=OUTLINE_PX):
    """Белый стикер-контур: дилатация альфы и белая подложка."""
    return add_contour(img, px, (255, 255, 255, 255))


def fit_square(img, size=MASTER, fill=FILL):
    """Кроп по контенту + вписывание в квадрат по центру."""
    bbox = content_bbox(img.split()[3])
    if bbox is None:
        return img.resize((size, size), Image.LANCZOS)
    img = img.crop(bbox)
    w, h = img.size
    target = int(size * fill)
    scale = target / max(w, h)
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    img = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(img, ((size - nw) // 2, (size - nh) // 2), img)
    return canvas


def to_emoji(master):
    """512 -> 100×100 с лёгкой резкостью по RGB (альфа не трогается)."""
    e = master.resize((EMOJI, EMOJI), Image.LANCZOS)
    r, g, b, a = e.split()
    rgb = Image.merge("RGB", (r, g, b)).filter(
        ImageFilter.UnsharpMask(radius=1.6, percent=55, threshold=2))
    return Image.merge("RGBA", (*rgb.split(), a))


def save_webp(img, path):
    img.save(path, "WEBP", lossless=True, method=6)
    if os.path.getsize(path) > MAX_BYTES:      # на 100×100 не случится
        img.save(path, "WEBP", quality=95, method=6)


# ---------------------------------------------------------------------------
# Превью-лист
# ---------------------------------------------------------------------------
def _checker(size, cell=16, c1=(255, 255, 255), c2=(228, 228, 232)):
    bg = Image.new("RGB", (size, size), c1)
    d = ImageDraw.Draw(bg)
    for y in range(0, size, cell):
        for x in range(0, size, cell):
            if (x // cell + y // cell) % 2 == 0:
                d.rectangle((x, y, x + cell - 1, y + cell - 1), fill=c2)
    return bg


def make_preview():
    cards = [n for n, _, _, _ in STICKERS
             if os.path.exists(os.path.join(PNG512, n + ".png"))]
    if not cards:
        print("нет png512 — сначала соберите набор", file=sys.stderr)
        return

    f_title = _font(30)
    f_label = _font(17)
    f_small = _font(14)

    cols = 3
    card, gap, margin = 224, 18, 26
    sticker = 180
    label_h = 30
    dark_h = 168

    title = "WALLY · RWA Foundation — кастом-эмодзи для Телеграма"
    tw = ImageDraw.Draw(Image.new("RGB", (10, 10))).textbbox((0, 0), title, font=f_title)[2]
    W = max(tw + 2 * margin,
            cols * card + (cols - 1) * gap + 2 * margin)
    rows = (len(cards) + cols - 1) // cols
    grid_h = rows * (card + label_h) + (rows - 1) * gap
    H = margin + 44 + grid_h + gap + 24 + dark_h + margin

    sheet = Image.new("RGB", (W, H), (250, 250, 248))
    d = ImageDraw.Draw(sheet)
    d.text(((W - tw) // 2, margin), title, fill=(20, 20, 24), font=f_title)

    y0 = margin + 44 + 12
    for i, name in enumerate(cards):
        cx = margin + (i % cols) * (card + gap)
        cy = y0 + (i // cols) * (card + label_h + gap)
        box = _checker(card)
        im = Image.open(os.path.join(PNG512, name + ".png")).convert("RGBA")
        im.thumbnail((sticker, sticker), Image.LANCZOS)
        box.paste(im, ((card - im.width) // 2, (card - im.height) // 2), im)
        sheet.paste(box, (cx, cy))
        d.rectangle((cx, cy, cx + card - 1, cy + card - 1),
                    outline=(200, 200, 205), width=1)
        title_ru = dict((n, t) for n, t, _, _ in STICKERS).get(name, name)
        d.text((cx + 6, cy + card + 6), f"{name}.png — {title_ru}",
               fill=(60, 60, 66), font=f_label)

    # тёмная полоса: как эмодзи выглядят в тёмном чате, 100 и 44 px
    dy = y0 + grid_h + gap + 24
    d.text((margin, dy - 22),
           "в чате: 100 px и 44 px на тёмном фоне",
           fill=(90, 90, 96), font=f_small)
    d.rectangle((margin, dy, W - margin, dy + dark_h - 12), fill=(24, 25, 29))
    x = margin + 18
    for name in cards:
        im100 = Image.open(os.path.join(WEBP100, name + ".webp")).convert("RGBA") \
            if os.path.exists(os.path.join(WEBP100, name + ".webp")) else None
        if im100 is None:
            continue
        sheet.paste(im100, (x, dy + 20), im100)
        im44 = im100.resize((44, 44), Image.LANCZOS)
        sheet.paste(im44, (x, dy + 20 + 100 + 12), im44)
        x += 100 + 34
        if x > W - margin - 100:
            x = margin + 18

    out = os.path.join(HERE, "preview.png")
    sheet.save(out, "PNG")
    print(f"превью: {out} ({sheet.size[0]}×{sheet.size[1]})")


# ---------------------------------------------------------------------------
# Основной конвейер
# ---------------------------------------------------------------------------
def build(name, report):
    src = os.path.join(RAW, name + ".png")
    if not os.path.exists(src):
        print(f"-- {name}: нет {src}, пропускаю", file=sys.stderr)
        return False

    ink = dict((n, i) for n, _, _, i in STICKERS).get(name, False)

    img = Image.open(src)
    raw_size = img.size
    img, kept, corner, dark_bg = remove_bg(img)

    # рабочий размер 512 (LANCZOS сглаживает жёсткую границу floodfill)
    if max(img.size) != MASTER:
        img = img.resize(
            (round(img.width * MASTER / max(img.size)),
             round(img.height * MASTER / max(img.size))), Image.LANCZOS)

    if ink:
        img = ink_boost(img)
    if dark_bg:
        # родной внешний контур съеден вместе с тёмным фоном —
        # рисуем заново, толщиной как у остальных стикеров набора
        img = add_contour(img, BLACK_PX, (0, 0, 0, 255))
    img = add_white_outline(img)
    master = fit_square(img)

    os.makedirs(PNG512, exist_ok=True)
    p_png = os.path.join(PNG512, name + ".png")
    master.save(p_png, "PNG")

    os.makedirs(WEBP100, exist_ok=True)
    p_webp = os.path.join(WEBP100, name + ".webp")
    save_webp(to_emoji(master), p_webp)

    report.append((name, raw_size, kept, dark_bg,
                   os.path.getsize(p_png), os.path.getsize(p_webp)))
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--preview", action="store_true",
                    help="собрать общий лист preview.png")
    ap.add_argument("--only", metavar="NAME",
                    help="пересобрать только один стикер (имя без .png)")
    args = ap.parse_args()

    names = ([args.only] if args.only else [n for n, _, _, _ in STICKERS])
    report = []
    for n in names:
        print(f"-- {n}")
        build(n, report)

    print()
    print(f"{'стикер':<14}{'сырой':<12}{'живого %':<10}{'фон':<8}"
          f"{'png512':<10}{'webp100':<10}")
    for name, raw_size, kept, dark, sb, sw in report:
        kp = f"{kept * 100:.0f}%" if kept >= 0 else "уже альфа"
        bg = "чёрный" if dark else "белый"
        print(f"{name:<14}{f'{raw_size[0]}x{raw_size[1]}':<12}{kp:<10}{bg:<8}"
              f"{sb // 1024} КБ{'':<4}{sw // 1024} КБ")
        if sw > MAX_BYTES:
            print(f"  !! {name}.webp тяжелее 64 КБ", file=sys.stderr)

    if args.preview or not args.only:
        make_preview()


if __name__ == "__main__":
    main()
