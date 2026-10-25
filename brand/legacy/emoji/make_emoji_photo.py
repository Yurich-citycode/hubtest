#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_emoji_photo.py
===================

Собирает премиум-эмодзи 100x100 (WEBP lossless) для статуса в Телеграме
ИЗ ИСХОДНЫХ ФОТО, лежащих в КОРНЕ репозитория:

    CityCode.png    -> brand/emoji/citycode.webp   (синяя плитка логотипа)
    keychain.webp   -> brand/emoji/keys.webp        (брелок-карабин с бирками)
    yurichhub.jpg   -> brand/emoji/yurichhub.webp   (блок надписи «YuRich Hub»)

Общий конвейер (как в исходном описании):
  1. Кроп по объекту.
  2. Чёрный фон -> прозрачность заливкой ОТ УГЛОВ (floodfill), чтобы
     чёрный карабин и тёмные бирки не превратились в «призраков»
     (глобальное «убрать всё чёрное» их бы стёрло; floodfill убирает
     только фон, связанный с углами кадра).
  3. Вписывание объекта в квадрат.
  4. Даунскейл рабочих 600 px -> 100 px фильтром LANCZOS
     + контраст / насыщенность / UnsharpMask (чтобы мелочь не поплыла).
  5. Сохранение WEBP lossless, ровно 100x100, до 64 КБ.

Некоторые исходники уже приходят с готовым альфа-каналом (например
keychain.webp и CityCode.png). Для них floodfill не нужен — скрипт это
определяет автоматически и использует имеющуюся прозрачность, а логика
floodfill остаётся для «сырых» фото на чёрном фоне.

Запуск:
    pip install --break-system-packages pillow
    python3 brand/emoji/make_emoji_photo.py

Полезные флаги:
    --preview     дополнительно сохранить *_preview_x4.png (400x400)
                  и общий contact-sheet emoji_preview.png
"""

import argparse
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

# ---------------------------------------------------------------------------
# Пути
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

OUT_SIZE = 100          # финальный размер эмодзи (Telegram: 100x100)
WORK_SIZE = 600         # рабочий размер для качественного даунскейла
MAX_BYTES = 64 * 1024   # лимит Telegram: 64 КБ


# ---------------------------------------------------------------------------
# Утилиты
# ---------------------------------------------------------------------------
def _src(name):
    return os.path.join(REPO_ROOT, name)


def content_bbox(img, alpha_thresh=8):
    """BBox непрозрачной области (alpha > thresh)."""
    a = img.split()[3]
    mask = a.point(lambda v: 255 if v > alpha_thresh else 0)
    return mask.getbbox()


def floodfill_black_to_alpha(rgb, tol=40):
    """
    Убрать ЧЁРНЫЙ ФОН заливкой от четырёх углов и вернуть RGBA.

    Заливаем сентинел-цветом области, связанные с углами и близкие к
    цвету угла (в пределах tol). Только эти пиксели становятся
    прозрачными. Тёмные объекты в центре (карабин, бирки) не связаны
    с углами напрямую (их отделяет более светлый ободок/подсветка),
    поэтому они уцелеют.
    """
    rgb = rgb.convert("RGB")
    w, h = rgb.size
    work = rgb.copy()
    SENT = (255, 0, 255)  # маловероятная маджента как маркер фона
    corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    for c in corners:
        try:
            ImageDraw.floodfill(work, c, SENT, thresh=tol)
        except Exception:
            pass
    px = work.load()
    alpha = Image.new("L", (w, h), 255)
    ap = alpha.load()
    for y in range(h):
        for x in range(w):
            if px[x, y] == SENT:
                ap[x, y] = 0
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out


def has_real_alpha(img):
    """True, если у картинки уже есть содержательная прозрачность."""
    if img.mode != "RGBA":
        return False
    a = img.split()[3]
    lo, hi = a.getextrema()
    if lo > 8:
        return False
    # доля полностью прозрачных пикселей
    hist = a.histogram()
    transparent = sum(hist[0:9])
    total = img.size[0] * img.size[1]
    return transparent > total * 0.02


def looks_black_bg(rgb):
    """Углы близки к чёрному?"""
    rgb = rgb.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    return all(max(c) < 40 for c in corners)


def rounded_mask(size, radius):
    """Маска со скруглёнными углами (с анти-алиасингом через супер-сэмпл)."""
    ss = 4
    big = Image.new("L", (size[0] * ss, size[1] * ss), 0)
    d = ImageDraw.Draw(big)
    d.rounded_rectangle(
        [0, 0, size[0] * ss - 1, size[1] * ss - 1],
        radius=radius * ss,
        fill=255,
    )
    return big.resize(size, Image.LANCZOS)


def pad_to_square_transparent(img, pad_frac=0.06):
    """Вписать RGBA-объект в прозрачный квадрат с небольшим полем."""
    bb = content_bbox(img)
    if bb:
        img = img.crop(bb)
    w, h = img.size
    side = int(round(max(w, h) * (1 + pad_frac * 2)))
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - w) // 2, (side - h) // 2), img)
    return canvas


def pad_to_square_color(img, bg, margin=0.0):
    """Вписать RGB-объект в квадрат, добивая поля цветом фона bg.

    margin — доля дополнительного поля вокруг (0.16 = +16% по стороне),
    чтобы надпись не упиралась в края.
    """
    w, h = img.size
    side = int(round(max(w, h) * (1 + margin * 2)))
    canvas = Image.new("RGB", (side, side), bg)
    canvas.paste(img, ((side - w) // 2, (side - h) // 2))
    return canvas


def enhance_for_small(img, contrast=1.08, color=1.12, unsharp=(1.4, 130, 2)):
    """Контраст + насыщенность + UnsharpMask, сохраняя альфу."""
    if img.mode == "RGBA":
        rgb = img.convert("RGB")
        a = img.split()[3]
    else:
        rgb = img.convert("RGB")
        a = None
    rgb = ImageEnhance.Contrast(rgb).enhance(contrast)
    rgb = ImageEnhance.Color(rgb).enhance(color)
    rgb = rgb.filter(
        ImageFilter.UnsharpMask(radius=unsharp[0], percent=unsharp[1], threshold=unsharp[2])
    )
    if a is not None:
        rgb = rgb.convert("RGBA")
        rgb.putalpha(a)
    return rgb


def save_webp_under_limit(img, path):
    """Сохранить WEBP; сперва lossless, при переборе лимита — поджать."""
    img.save(path, "WEBP", lossless=True, quality=100, method=6)
    size = os.path.getsize(path)
    if size <= MAX_BYTES:
        return size, "lossless"
    # запас на всякий случай (для 100x100 практически недостижимо)
    for q in (100, 95, 90, 85, 80, 70):
        img.save(path, "WEBP", lossless=False, quality=q, method=6)
        size = os.path.getsize(path)
        if size <= MAX_BYTES:
            return size, f"lossy q{q}"
    return size, f"lossy q70 (>{MAX_BYTES})"


# ---------------------------------------------------------------------------
# Обработчики по объектам
# ---------------------------------------------------------------------------
def build_citycode():
    """Синяя плитка логотипа CityCode: кроп по синим пикселям, скруглённые углы."""
    img = Image.open(_src("CityCode.png")).convert("RGBA")

    if has_real_alpha(img):
        # плитка уже вырезана из чёрного фона — берём её альфу
        base = img
    else:
        # синие пиксели -> маска объекта, всё остальное прозрачно
        rgb = img.convert("RGB")
        px = rgb.load()
        w, h = rgb.size
        mask = Image.new("L", (w, h), 0)
        mp = mask.load()
        for y in range(h):
            for x in range(w):
                r, g, b = px[x, y]
                bright = (r + g + b) / 3
                if b > 90 and b > r + 25 and bright > 45:
                    mp[x, y] = 255
        base = rgb.convert("RGBA")
        base.putalpha(mask)

    bb = content_bbox(base)
    tile = base.crop(bb)

    # квадрат под плитку (плитка почти квадратная)
    w, h = tile.size
    side = max(w, h)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(tile, ((side - w) // 2, (side - h) // 2), tile)

    # рабочий размер + чистые скруглённые углы
    work = sq.resize((WORK_SIZE, WORK_SIZE), Image.LANCZOS)
    radius = int(WORK_SIZE * 0.17)
    rmask = rounded_mask((WORK_SIZE, WORK_SIZE), radius)
    work.putalpha(ImageChops.multiply(work.split()[3], rmask))

    small = work.resize((OUT_SIZE, OUT_SIZE), Image.LANCZOS)
    return enhance_for_small(small, contrast=1.06, color=1.14, unsharp=(1.2, 110, 2))


def build_keys():
    """Брелок-карабин с шестью бирками: чёрный фон -> прозрачность (floodfill)."""
    img = Image.open(_src("keychain.webp")).convert("RGBA")

    if has_real_alpha(img):
        base = img  # уже вырезан
    elif looks_black_bg(img):
        base = floodfill_black_to_alpha(img, tol=40)
    else:
        base = img

    sq = pad_to_square_transparent(base, pad_frac=0.05)
    work = sq.resize((WORK_SIZE, WORK_SIZE), Image.LANCZOS)
    small = work.resize((OUT_SIZE, OUT_SIZE), Image.LANCZOS)
    # бирки мелкие — держим резкость и насыщенность
    return enhance_for_small(small, contrast=1.10, color=1.16, unsharp=(1.5, 150, 2))


def build_yurichhub():
    """Блок надписи «YuRich Hub» с постера yurichhub.jpg."""
    img = Image.open(_src("yurichhub.jpg")).convert("RGB")
    W, H = img.size  # 640x640 ожидается

    # координаты блока «YuRich / Hub» (доли, чтобы не зависеть от точного
    # размера). Правый край обрезаем до руки на постере (~x=300 из 640),
    # чтобы в кадр не попали пальцы с кольцами и лицо.
    left = int(W * 0.028)
    top = int(H * 0.394)
    right = int(W * 0.459)
    bottom = int(H * 0.659)
    crop = img.crop((left, top, right, bottom)).copy()
    cw, ch = crop.size

    # Справа в блок заходит кисть руки с кольцами: снизу-справа (рядом с
    # коротким «Hub») и яркой подсветкой ПОД буквой «h» в «YuRich» —
    # то есть прямо за текстом. Поэтому: (1) заливаем всю «рукозону»
    # синтезированной бордовой «бумагой» (средний цвет + зерно из чистого
    # участка под «Hub»), а затем (2) возвращаем поверх только БЕЛЫЕ пиксели
    # букв — так «YuRich Hub» остаётся целым, а рука исчезает.
    import numpy as np
    arr = np.asarray(crop.convert("RGB")).astype(np.int16)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    letters = (mx > 165) & ((mx - mn) < 48)      # белые буквы (нейтральные)

    sample = np.asarray(
        crop.crop((int(cw * 0.16), int(ch * 0.86), int(cw * 0.58), ch)).convert("RGB")
    ).reshape(-1, 3)
    mean = sample.mean(axis=0)
    std = np.clip(sample.std(axis=0), 3, 18)

    rng = np.random.default_rng(7)
    grain = mean + rng.normal(0, 1, (ch, cw, 1)) * std
    gx = np.clip((np.arange(cw) - cw * 0.6) / (cw * 0.4), 0, 1)
    grain = grain * (1 - 0.14 * gx[None, :, None])   # правее — темнее
    grain = np.clip(grain, 0, 255)

    # «рукозона»: правая полоса (за «h») + нижний-правый угол (рядом с «Hub»)
    xx, yy = np.meshgrid(np.arange(cw), np.arange(ch))
    handzone = (xx >= cw * 0.80) | ((xx >= cw * 0.66) & (yy >= ch * 0.42))
    handzone &= ~letters                              # буквы не трогаем

    out = arr.astype(np.float64)
    m = handzone[..., None]
    out = np.where(m, grain, out)
    crop = Image.fromarray(np.clip(out, 0, 255).astype("uint8"))

    # цвет фона постера (тёмно-бордовый) — по верхне-левому уголку блока
    bg = img.getpixel((left + 3, top + 3))

    # поле вокруг надписи, чтобы буквы не упирались в края квадрата
    sq = pad_to_square_color(crop, bg, margin=0.16)
    work = sq.resize((WORK_SIZE, WORK_SIZE), Image.LANCZOS)
    small = work.resize((OUT_SIZE, OUT_SIZE), Image.LANCZOS)
    out = enhance_for_small(small, contrast=1.10, color=1.10, unsharp=(1.4, 140, 2))
    return out.convert("RGBA")  # единый формат на выходе


TARGETS = [
    ("citycode.webp", build_citycode),
    ("keys.webp", build_keys),
    ("yurichhub.webp", build_yurichhub),
]


# ---------------------------------------------------------------------------
# Превью
# ---------------------------------------------------------------------------
def make_previews(results):
    """*_preview_x4.png (400x400) + общий emoji_preview.png с шашечным фоном."""
    def checker(size, cell=16):
        bg = Image.new("RGBA", (size, size), (255, 255, 255, 255))
        d = ImageDraw.Draw(bg)
        c1, c2 = (235, 235, 235, 255), (205, 205, 205, 255)
        for y in range(0, size, cell):
            for x in range(0, size, cell):
                col = c1 if ((x // cell + y // cell) % 2 == 0) else c2
                d.rectangle([x, y, x + cell - 1, y + cell - 1], fill=col)
        return bg

    thumbs = []
    for name, path in results:
        img = Image.open(path).convert("RGBA")
        big = img.resize((OUT_SIZE * 4, OUT_SIZE * 4), Image.NEAREST)  # x4, честные пиксели
        bg = checker(OUT_SIZE * 4)
        bg.alpha_composite(big)
        pv = os.path.join(HERE, name.replace(".webp", "_preview_x4.png"))
        bg.convert("RGB").save(pv)
        thumbs.append((name, bg))

    # contact-sheet
    pad, label_h = 24, 30
    tw = OUT_SIZE * 4
    sheet_w = pad + len(thumbs) * (tw + pad)
    sheet_h = pad + label_h + tw + pad
    sheet = Image.new("RGB", (sheet_w, sheet_h), (250, 250, 250))
    d = ImageDraw.Draw(sheet)
    x = pad
    for name, bg in thumbs:
        d.text((x, pad), name, fill=(20, 20, 20))
        sheet.paste(bg.convert("RGB"), (x, pad + label_h))
        x += tw + pad
    sheet_path = os.path.join(HERE, "emoji_preview.png")
    sheet.save(sheet_path)
    return sheet_path


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Собрать премиум-эмодзи 100x100 WEBP.")
    ap.add_argument("--preview", action="store_true",
                    help="также сохранить превью x4 и contact-sheet")
    args = ap.parse_args()

    for req in ("CityCode.png", "keychain.webp", "yurichhub.jpg"):
        if not os.path.exists(_src(req)):
            sys.exit(f"[ОШИБКА] нет исходника в корне репо: {req}")

    results = []
    for name, fn in TARGETS:
        out_path = os.path.join(HERE, name)
        img = fn()
        assert img.size == (OUT_SIZE, OUT_SIZE), f"{name}: {img.size} != {OUT_SIZE}x{OUT_SIZE}"
        size, mode = save_webp_under_limit(img, out_path)
        ok = "OK" if size <= MAX_BYTES else "ПРЕВЫШЕН ЛИМИТ"
        print(f"  {name:16s} {img.size[0]}x{img.size[1]}  "
              f"{size/1024:6.1f} КБ  [{mode}]  {ok}")
        results.append((name, out_path))

    if args.preview:
        sheet = make_previews(results)
        print(f"  превью: {os.path.relpath(sheet, REPO_ROOT)} + *_preview_x4.png")

    print("Готово.")


if __name__ == "__main__":
    main()
