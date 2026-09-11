#!/usr/bin/env python3
"""Write docs/SYMBOLS.md and the logo strip from the symbol catalogue.

Run it after changing `symbols.py`:

    uv run tools/symbol_index.py
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import symbols  # noqa: E402
from bf2font import PUA_BASE, glyph_image, parse_mcm  # noqa: E402

REFERENCE = "clarity"  # the face the reference images are cut from


@dataclass(frozen=True)
class Language:
    """One translation of the reference page."""

    file: str
    header: str
    columns: str
    groups: dict[str, str]
    logo: str


ENGLISH = Language(
    file="SYMBOLS.md",
    header="""[← README](../README.md) · [Українською](SYMBOLS_UA.md)

# OSD symbols

The Betaflight fonts spend two thirds of their 256 characters on icons rather
than letters. Every one of them is reachable three ways: type its name between
colons, use its private use codepoint, or -- where the icon is also a standard
character -- type that character.

Images below are cut from `{reference}`; every font draws the same set in its
own weight.
""",
    columns="| | Type | Also at | Private use |",
    groups={
        "power": "Battery and power",
        "telemetry": "Telemetry",
        "navigation": "GPS and navigation",
        "arrows": "Arrows",
        "horizon": "Artificial horizon",
        "units": "Units",
        "time": "Time",
        "progress": "Progress bar",
        "sticks": "Stick overlay",
        "status": "Status",
    },
    logo=(
        "## The logo\n\n"
        "The last 96 characters are the Betaflight logo, cut into tiles "
        "{columns} wide and {rows} tall, in reading order: `:logo_00:` is the "
        "top left tile, `:logo_95:` the bottom right. Set them on consecutive "
        "lines with no line spacing and the picture comes back.\n\n"
        "![The Betaflight logo, assembled from its 96 tiles](logo.png)\n"
    ),
)

UKRAINIAN = Language(
    file="SYMBOLS_UA.md",
    header="""[← README](../README_UA.md) · [In English](SYMBOLS.md)

# Символи OSD

Дві третини з 256 символів шрифтів Betaflight — це іконки, а не літери. До
кожної з них є три шляхи: набрати назву між двокрапками, взяти кодову позицію
з приватної зони або — якщо іконка збігається зі стандартним символом —
набрати цей символ.

Зображення зняті зі шрифту `{reference}`; кожен шрифт малює той самий набір
своєю вагою.
""",
    columns="| | Набрати | Також на | Приватна зона |",
    groups={
        "power": "Батарея та живлення",
        "telemetry": "Телеметрія",
        "navigation": "GPS і навігація",
        "arrows": "Стрілки",
        "horizon": "Штучний горизонт",
        "units": "Одиниці",
        "time": "Час",
        "progress": "Смуга прогресу",
        "sticks": "Накладка стіків",
        "status": "Статус",
    },
    logo=(
        "## Логотип\n\n"
        "Останні 96 символів — логотип Betaflight, порізаний на плитки "
        "{columns} завширшки та {rows} заввишки, у порядку читання: "
        "`:logo_00:` — верхня ліва плитка, `:logo_95:` — нижня права. "
        "Постав їх у рядки без міжрядкового інтервалу — і картинка "
        "збереться.\n\n"
        "![Логотип Betaflight, зібраний із 96 плиток](logo.png)\n"
    ),
)
LANGUAGES = (ENGLISH, UKRAINIAN)


def table(group: str, columns: str) -> str:
    rows = [columns, "| --- | --- | --- | --- |"]
    for symbol in symbols.SYMBOLS:
        if symbol.group != group:
            continue
        image = (
            f'<img src="../output/{REFERENCE}/png/{symbol.index:03d}.png" width="24">'
        )
        also = ", ".join(
            f"`{chr(cp)}` U+{cp:04X}" if cp <= 0xFFFF else f"U+{cp:04X}"
            for cp in symbol.unicode
        )
        rows.append(
            f"| {image} | `:{symbol.name}:` | {also or '—'} | "
            f"`U+{PUA_BASE + symbol.index:04X}` |"
        )
    return "\n".join(rows)


def logo_strip(scale: int = 4) -> Image.Image:
    """The last 96 characters, assembled back into the Betaflight logo."""
    glyphs = parse_mcm(ROOT / "original_fonts" / f"{REFERENCE}.mcm")
    tiles = [glyphs[i] for i in range(symbols.LOGO_START, 0x100)]
    columns = symbols.LOGO_COLUMNS
    first = glyph_image(tiles[0], scale)
    width, height = first.size
    rows = (len(tiles) + columns - 1) // columns
    sheet = Image.new("RGBA", (columns * width, rows * height), (0, 0, 0, 0))
    for i, tile in enumerate(tiles):
        sheet.paste(
            glyph_image(tile, scale), ((i % columns) * width, (i // columns) * height)
        )
    return sheet


def document(language: Language) -> str:
    parts = [language.header.format(reference=REFERENCE)]
    for group, title in language.groups.items():
        parts.append(f"## {title}\n\n{table(group, language.columns)}\n")
    parts.append(
        language.logo.format(
            columns=symbols.LOGO_COLUMNS,
            rows=(0x100 - symbols.LOGO_START) // symbols.LOGO_COLUMNS,
        )
    )
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o", "--output", type=Path, default=ROOT / "docs", help="docs directory"
    )
    args = parser.parse_args(argv)
    written = []
    for language in LANGUAGES:
        path = args.output / language.file
        path.write_text(document(language))
        written.append(path)
    logo_strip().save(args.output / "logo.png")
    written.append(args.output / "logo.png")
    print(", ".join(str(p) for p in written))
    return 0


if __name__ == "__main__":
    sys.exit(main())
