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
  2. Toon-clean: медиана по RGB убирает AI-зерно («грязь»)
     с генераций (двойной проход на сыром разрешении + один
     после ink-буста). Альфа не трогается.
  3. Ink-буст (только варианты в шапках): степенная кривая
     приводит серые контуры и линзы к «жирному чёрному» стилю
     базового WALLY; насыщенные цвета не трогаются.
  4. Ресайз LANCZOS -> 512.
  5. Белый стикер-контур: дилатация альфы MaxFilter, подложка белым.
  6. Вписывание в квадрат 512×512 по центру, заполнение ~90%.
  7. Даунскейл до 100×100 LANCZOS + UnsharpMask только по RGB
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
    # (имя, подпись, эмодзи для привязки, ink/cel-обработка)
    # ink=True — вариант с «мягкой» генерацией: медиана + cel-выравнивание
    # тонов (все текущие raw чистые, флаг выключен)
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


def toon_clean(img, passes=1):
    """
    Убрать AI-зерно («грязь») с генераций: медианный фильтр по RGB.
    Альфа не трогается, чтобы не размыть край. Медиана убирает
    одиночные тёмные/светлые speckle'ы, но сохраняет плоские цвета
    и контуры.
    """
    r, g, b, a = img.split()
    rgb = Image.merge("RGB", (r, g, b))
    for _ in range(passes):
        rgb = rgb.filter(ImageFilter.MedianFilter(3))
    r2, g2, b2 = rgb.split()
    return Image.merge("RGBA", (r2, g2, b2, a))


def draw_shades(img, min_area=40, gap=18):
    """
    Рисует сигнатурные БОЛЬШИЕ чёрные очки-полосу с белыми
    зигзаг-бликами — как у базового WALLY (модели на вариантах с
    шапками упорно рисуют мелкие очки/глаза, которые не читаются
    в 100 px).

    Позиция глаз находится по тёмным кластерам в зоне лица
    (36-60% высоты, 25-75% ширины контента). Кластеры, касающиеся
    границ зоны (шляпа сверху, уши по бокам), отбрасываются.
    Если уже есть широкая тёмная полоса (очки есть) — ничего не
    рисуем.
    """
    a = img.split()[3]
    bbox = a.point(lambda v: 255 if v > 8 else 0).getbbox()
    if not bbox:
        return img
    x0, y0, x1, y1 = bbox
    W, H = x1 - x0, y1 - y0
    zx0, zx1 = x0 + int(W * 0.25), x0 + int(W * 0.75)
    zy0, zy1 = y0 + int(H * 0.36), y0 + int(H * 0.60)

    px = img.load()
    dark = set()
    for y in range(zy0, zy1):
        for x in range(zx0, zx1):
            r, g, b, al = px[x, y]
            if al > 150 and (r + g + b) < 450:
                dark.add((x, y))
    if not dark:
        return img

    # связные компоненты (8-связность, BFS)
    seen = set()
    comps = []
    for p in sorted(dark):
        if p in seen:
            continue
        stack, comp = [p], []
        seen.add(p)
        while stack:
            q = stack.pop()
            comp.append(q)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    n = (q[0] + dx, q[1] + dy)
                    if n in dark and n not in seen:
                        seen.add(n)
                        stack.append(n)
        comps.append(comp)
    boxes = []
    for c in comps:
        if len(c) < min_area:
            continue
        bx0, by0 = min(p[0] for p in c), min(p[1] for p in c)
        bx1, by1 = max(p[0] for p in c), max(p[1] for p in c)
        # отбрасываем то, что касается границ зоны (шляпа/уши)
        if by0 <= zy0 or bx0 <= zx0 or bx1 >= zx1:
            continue
        # и слишком вытянутое по вертикали (шляпа спускается)
        if by1 - by0 > 70:
            continue
        boxes.append((bx0, by0, bx1, by1))
    if not boxes:
        return img

    # объединяем близкие боксы (два глаза могут быть одной деталью)
    def merge(boxes):
        out = []
        for b in sorted(boxes):
            for i, o in enumerate(out):
                if b[0] <= o[2] + gap and o[0] <= b[2] + gap and \
                   b[1] <= o[3] + gap and o[1] <= b[3] + gap:
                    out[i] = (min(o[0], b[0]), min(o[1], b[1]),
                              max(o[2], b[2]), max(o[3], b[3]))
                    break
            else:
                out.append(b)
        return out

    boxes = merge(merge(boxes))
    # уже есть широкая полоса очков — не рисуем
    if boxes[0][2] - boxes[0][0] > W * 0.42:
        return img

    # итоговая плашка: объединение двух самых крупных кластеров
    boxes.sort(key=lambda b: (b[2] - b[0]) * (b[3] - b[1]), reverse=True)
    eyes = boxes[:2]
    ex0 = min(b[0] for b in eyes) - 14
    ex1 = max(b[2] for b in eyes) + 14
    ey0 = min(b[1] for b in eyes) - 8
    ey1 = max(b[3] for b in eyes) + 10

    # сигнатурные очки — БОЛЬШИЕ, как у базового WALLY (~60% ширины
    # лица): если детект нашёл мало — расширяем до минимума
    cx = (ex0 + ex1) // 2
    min_w = int(W * 0.45)
    if ex1 - ex0 < min_w:
        ex0, ex1 = cx - min_w // 2, cx + min_w // 2
    ex0 = max(ex0, x0 + int(W * 0.10))
    ex1 = min(ex1, x1 - int(W * 0.10))
    min_h = int(H * 0.10)
    if ey1 - ey0 < min_h:
        cy = (ey0 + ey1) // 2
        ey0, ey1 = cy - min_h // 2, cy + min_h // 2
    # не залезаем на шапку сверху и на рот снизу
    ey0 = max(ey0, y0 + int(H * 0.32))
    ey1 = min(ey1, y0 + int(H * 0.63))

    d = ImageDraw.Draw(img)
    rh = ey1 - ey0
    d.rounded_rectangle((ex0, ey0, ex1, ey1), radius=min(28, rh // 2),
                        fill=(0, 0, 0, 255))

    # белые зигзаг-блики по центру каждого глаза
    centers = [((b[0] + b[2]) // 2, (b[1] + b[3]) // 2) for b in eyes]
    for cx, cy in centers:
        pts = []
        for i in range(5):
            pts.append((cx - 18 + i * 9, cy - 9 + (18 if i % 2 else 0)))
        d.line(pts, fill=(255, 255, 255, 255), width=7, joint="curve")
    return img


def cel_flatten(img, edge_thresh=120, spread=32, vote=9):
    """
    Приводит вариант в шапке к ПЛОСКОМУ мультяшному стилю базового
    WALLY (у него кожа — ровная серебристая заливка без полутеней).

    Шаги:
      1. Нейтральные пиксели вне ЖЁСТКИХ краёв (защищаются только
         AA-переходы с контрастом > edge_thresh — контуры, зигзаг)
         снапятся к двум тонам: чёрный (25..145) и кожа (145..232).
      2. Голосование: медиана карты тонов чинит границы зон.
      3. Морфологическое ОТКРЫТИЕ масок (эрозия+дилатация):
         в чёрном выживает только толще ~10 px — контуры, линзы,
         чёрные шляпы; тонкие серые морщины/полутени (3-8 px)
         стираются безусловно, какой бы длинной ни была линия.
         Тонкие (<6 px) островки кожи внутри чёрного тоже убираются.
      4. Насыщенные цвета (оранжевая кепка, золото), белые детали
         (зубы, зигзаг) и AA-переходы не трогаются вовсе.

    Так уходит серая «грязь» — нарисованные шумные полутени и
    морщины, которых нет в плоском стиле базового WALLY.
    """
    lum = img.convert("RGB").convert("L")
    med5 = lum.filter(ImageFilter.MedianFilter(5))
    rng = ImageChops.subtract(med5.filter(ImageFilter.MaxFilter(3)),
                              med5.filter(ImageFilter.MinFilter(3)))
    rng_px = rng.load()
    px = img.load()
    w, h = img.size

    # тон кожи: медианный RGB нейтральных пикселей яркости 190..235
    sample = []
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            r, g, b, a = px[x, y]
            if a > 150 and max(r, g, b) - min(r, g, b) <= spread:
                l = (r + g + b) // 3
                if 190 <= l <= 235:
                    sample.append((r, g, b))
    if sample:
        n = len(sample)
        skin = tuple(sorted(c[i] for c in sample)[n // 2] for i in range(3))
    else:
        skin = (203, 206, 213)

    # карта тонов: 0 = чёрный, 255 = кожа, 128 = не снаплено
    tone = Image.new("L", (w, h), 128)
    tpx = tone.load()
    snapped = Image.new("L", (w, h), 0)   # маска: что реально снапили
    spx = snapped.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a <= 8 or rng_px[x, y] > edge_thresh:
                continue
            if max(r, g, b) - min(r, g, b) > spread:
                continue
            l = (r + g + b) // 3
            if 25 <= l < 145:
                tpx[x, y] = 0
                spx[x, y] = 255
            elif 145 <= l <= 232:
                tpx[x, y] = 255
                spx[x, y] = 255

    # голосование большинством (чинит границы зон)
    tone = tone.filter(ImageFilter.MedianFilter(vote))
    tpx = tone.load()

    # морфологическое открытие: чёрное толще ~10 px, кожа толще ~6 px
    black_ok = tone.point(lambda v: 255 if v == 0 else 0) \
                   .filter(ImageFilter.MinFilter(11)) \
                   .filter(ImageFilter.MaxFilter(11))
    skin_ok = tone.point(lambda v: 255 if v == 255 else 0) \
                  .filter(ImageFilter.MinFilter(7)) \
                  .filter(ImageFilter.MaxFilter(7))
    bok = black_ok.load()
    sok = skin_ok.load()

    black = 30
    for y in range(h):
        for x in range(w):
            if not spx[x, y]:
                continue                     # не снаплено — не трогаем
            r, g, b, a = px[x, y]
            if bok[x, y]:
                px[x, y] = (black, black, black, a)
            elif sok[x, y]:
                px[x, y] = (*skin, a)
            # открытие съело обе зоны (не должно случаться) — кожа
            else:
                px[x, y] = (*skin, a)
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

    if ink:
        # зернистость сырой генерации убираем на её же разрешении,
        # двойным проходом медианы
        img = toon_clean(img, passes=2)

    # рабочий размер 512 (LANCZOS сглаживает жёсткую границу floodfill)
    if max(img.size) != MASTER:
        img = img.resize(
            (round(img.width * MASTER / max(img.size)),
             round(img.height * MASTER / max(img.size))), Image.LANCZOS)

    if ink:
        # сигнатурные большие чёрные очки (если их нет)
        img = draw_shades(img)
        # плоская мультяшная заливка (контур/кожа/белое) + чистка
        # возможных speckle на границах тонов. Нарисованная плашка
        # очков и белые зигзаги выравниванием не трогаются.
        img = toon_clean(cel_flatten(img))
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
