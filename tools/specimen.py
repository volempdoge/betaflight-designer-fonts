#!/usr/bin/env python3
"""Render the docs specimen images from the built fonts.

Stacks the flat `Shadow` and `Fill` families the way an app without colour font
support would, which is also the only way Pillow can show both colours.

    uv run tools/specimen.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bf2font import title_from_stem  # noqa: E402

SIZE = 48
MARGIN = 12
BACKGROUND = (24, 26, 34)

# (font, line). Every line is drawn in the face it names.
SETS_SPECIMEN = [
    ("clarity", "ŁÓDŹ ÄÖÜ ÇÃO ĄĘŚŹŻ ŠČŘŽ İĞŞ"),
    ("bold", "«ЦЕ — ТЕСТ…» “QUOTES” ¿QUÉ?"),
    ("impact", "5°C ±2 ≈50 ≠0 ≤9 €12 ₴300 £5 ¥7"),
    ("default", "┌──────────┐ ║ ╬ ▲▼◀▶ ★ ✓ ✗ ● ◆ █▓▒░"),
    ("vision", "ΔΩΣΦΨ · ΑΒΓΔΕΖΗΘ"),
]


def font_files(name: str, weight: str) -> Path:
    family = f"Betaflight OSD {title_from_stem(name)}".replace(" ", "")
    return ROOT / "output" / name / "fonts" / "ttf" / f"{family}{weight}.ttf"


def render(lines: list[tuple[str, str]], size: int = SIZE) -> Image.Image:
    faces = [
        (
            text,
            ImageFont.truetype(str(font_files(name, "Shadow")), size),
            ImageFont.truetype(str(font_files(name, "Fill")), size),
        )
        for name, text in lines
    ]
    step = size + size // 3
    width = max(int(shadow.getlength(text)) for text, shadow, _ in faces)
    image = Image.new(
        "RGB", (width + 2 * MARGIN, step * len(faces) + MARGIN), BACKGROUND
    )
    draw = ImageDraw.Draw(image)
    for row, (text, shadow, fill) in enumerate(faces):
        at = (MARGIN, MARGIN // 2 + row * step)
        draw.text(at, text, font=shadow, fill=(0, 0, 0))
        draw.text(at, text, font=fill, fill=(255, 255, 255))
    return image


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--output", type=Path, default=ROOT / "docs" / "sets.png")
    args = parser.parse_args(argv)
    render(SETS_SPECIMEN).save(args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
