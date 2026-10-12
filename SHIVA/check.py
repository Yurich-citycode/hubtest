#!/usr/bin/env python3
"""Static validation for the SHIVA campaign kit. Uses only the standard library."""
from __future__ import annotations

import json
import re
import struct
import subprocess
import tempfile
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SITE = HERE / "index.html"
POSTS = [HERE / "posts/week-01.md", HERE / "posts/week-02.md"]
SPECS = HERE / "cover-specs"
RENDERS = HERE / "covers"
CA = "3YhtPb2TTr671vg6zoStj2896sQoSSNBKyJzvzHQogib"
SHIB_CA = "shib5gSoVKPjwkXrxRk7SbQFzb2R9rQB3TgQWYX4RwW"


def check(ok: bool, label: str) -> None:
    if not ok:
        raise AssertionError(label)
    print(f"PASS · {label}")


def markdown_blocks(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    heading = ""
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#"):
            heading = line.strip()
        if line.strip().startswith("```"):
            body = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(lines[i])
                i += 1
            yield heading, "\n".join(body)
        i += 1


class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for key in ("href", "src"):
            value = a.get(key)
            if value:
                self.refs.append(value)


def main() -> None:
    html = SITE.read_text(encoding="utf-8")
    check(CA in html and SHIB_CA in html, "оба проверяемых адреса есть на сайте")
    check(html.rstrip().endswith("</html>"), "HTML закрыт")

    # Balance the structural tags that matter in this page.
    for tag in ("section", "div", "article", "details", "footer", "header", "nav", "form", "svg", "script", "style"):
        opened = len(re.findall(rf"<{tag}[\s>]", html))
        closed = len(re.findall(rf"</{tag}>", html))
        check(opened == closed, f"тег {tag}: {opened} открывающих / {closed} закрывающих")

    scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
    check(len(scripts) == 1, "один inline-script")
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as f:
        f.write(scripts[0])
        f.flush()
        result = subprocess.run(["node", "--check", f.name], capture_output=True, text=True)
        check(result.returncode == 0, "JavaScript проходит node --check")

    assets = Assets()
    assets.feed(html)
    missing = []
    for ref in assets.refs:
        if ref.startswith(("http://", "https://", "data:", "#", "mailto:", "tel:")):
            continue
        path = (SITE.parent / ref.split("?", 1)[0]).resolve()
        if not path.exists():
            missing.append(ref)
    check(not missing, "локальные ссылки сайта существуют" + (f": {missing}" if missing else ""))

    x_blocks: list[tuple[str, int]] = []
    tg_blocks: list[tuple[str, int]] = []
    for post_file in POSTS:
        for heading, body in markdown_blocks(post_file):
            if "X ·" in heading and "RU-зеркало треда" not in heading:
                x_blocks.append((heading, len(body)))
            if "TG ·" in heading:
                tg_blocks.append((heading, len(body)))
    x_over = [(h, n) for h, n in x_blocks if n > 280]
    tg_over = [(h, n) for h, n in tg_blocks if n > 4096]
    check(len(x_blocks) == 140, "в комплекте 140 готовых X-блоков")
    check(not x_over, "все X-блоки помещаются в 280 знаков")
    check(len(tg_blocks) == 42, "в комплекте 42 готовых TG-блока")
    check(not tg_over, "все TG-блоки помещаются в 4096 знаков")

    specs = sorted(SPECS.glob("*.json"))
    renders = sorted(RENDERS.glob("*.png"))
    check(len(specs) == 15, "15 JSON-спецификаций обложек")
    check(len(renders) == 15, "15 готовых PNG-обложек")
    for spec in specs:
        data = json.loads(spec.read_text(encoding="utf-8"))
        check(data.get("module") == "shiva", f"{spec.name}: модуль shiva")
    for render in renders:
        raw = render.read_bytes()[:24]
        check(raw[:8] == b"\x89PNG\r\n\x1a\n", f"{render.name}: валидная PNG-сигнатура")
        width, height = struct.unpack(">II", raw[16:24])
        check((width, height) == (1600, 900), f"{render.name}: 1600×900")

    print("\nSHIVA KIT: ВСЕ СТАТИЧЕСКИЕ ПРОВЕРКИ ПРОЙДЕНЫ")


if __name__ == "__main__":
    main()
