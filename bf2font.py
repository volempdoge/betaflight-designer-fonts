#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "fonttools>=4.53",
#     "brotli>=1.1",
#     "pillow>=10.3",
# ]
# ///
"""Convert Betaflight (MAX7456 ``.mcm``) OSD fonts into sliced PNGs and font files.

Character memory holds 256 characters of 12x18 pixels, two bits per pixel:
0b00 black, 0b10 white, 0b01/0b11 transparent. Both colours survive as COLR/CPAL
glyphs -- base glyph is the silhouette, layer 0 paints it black, layer 1 paints
the white pixels on top (which also hides hairline seams between them).

Usage:
    uv run bf2font.py original_fonts/default.mcm
    uv run bf2font.py original_fonts/*.mcm -o output --scale 16
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from fontTools.colorLib.builder import buildCOLR, buildCPAL
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from PIL import Image

import cyrillic

# --- MAX7456 geometry --------------------------------------------------------

CHAR_W = 12
CHAR_H = 18
CHARS = 256
BYTES_PER_CHAR = 64  # 54 bytes of pixel data + 10 bytes of padding
PIXEL_BYTES = CHAR_W * CHAR_H * 2 // 8  # 54

BLACK, WHITE, TRANSPARENT = "black", "white", None

# --- font metrics ------------------------------------------------------------

PX = 100  # font units per OSD pixel
UPM = CHAR_H * PX  # 1800
DESCENT = 400  # cell sits from -400 up to +1400
ASCENT = UPM - DESCENT
ADVANCE = CHAR_W * PX  # 1200

PUA_BASE = 0xE000  # every character is also reachable at U+E000+index
# Pinned so head.created does not come from the clock: builds stay reproducible.
SOURCE_DATE_EPOCH = "1761690259"
VERSION = "1.000"
COPYRIGHT = (
    "Original font data from betaflight/betaflight-configurator, "
    "GNU General Public License v3.0."
)
LICENSE_TEXT = (
    "This font is derived from the Betaflight configurator OSD fonts and is "
    "distributed under the GNU General Public License v3.0. "
    "See https://www.gnu.org/licenses/gpl-3.0.html"
)


# --- .mcm parsing ------------------------------------------------------------


@dataclass
class Glyph:
    index: int
    pixels: list[list[int]]  # [row][col] -> 0 black, 1/3 transparent, 2 white

    def cells(self, *, value: int) -> set[tuple[int, int]]:
        """Cells of one colour, in y-up grid coordinates."""
        return {
            (x, CHAR_H - 1 - y)
            for y, row in enumerate(self.pixels)
            for x, v in enumerate(row)
            if v == value
        }

    def ink(self) -> set[tuple[int, int]]:
        """Every non-transparent cell (the silhouette)."""
        return self.cells(value=0) | self.cells(value=2)

    @property
    def is_blank(self) -> bool:
        return not any(v in (0, 2) for row in self.pixels for v in row)


def parse_mcm(path: Path) -> list[Glyph]:
    lines = path.read_text().splitlines()
    if not lines or lines[0].strip() != "MAX7456":
        raise ValueError(f"{path}: missing MAX7456 header")

    bits = [ln.strip() for ln in lines[1:] if ln.strip()]
    if len(bits) != CHARS * BYTES_PER_CHAR:
        raise ValueError(
            f"{path}: expected {CHARS * BYTES_PER_CHAR} data lines, got {len(bits)}"
        )
    if any(not re.fullmatch(r"[01]{8}", b) for b in bits):
        raise ValueError(f"{path}: data lines must be 8 binary digits")

    data = bytes(int(b, 2) for b in bits)
    glyphs = []
    for index in range(CHARS):
        chunk = data[index * BYTES_PER_CHAR : index * BYTES_PER_CHAR + PIXEL_BYTES]
        rows = []
        for y in range(CHAR_H):
            row = []
            for x in range(CHAR_W):
                bit = y * CHAR_W + x
                row.append((chunk[bit // 4] >> ((3 - bit % 4) * 2)) & 0b11)
            rows.append(row)
        glyphs.append(Glyph(index=index, pixels=rows))
    return glyphs


# --- pixels -> outlines ------------------------------------------------------


# Sharpest right turn first, so loops leaving a diagonal vertex never cross.
def _turns(d: tuple[int, int]) -> list[tuple[int, int]]:
    dx, dy = d
    return [(dy, -dx), (dx, dy), (-dy, dx), (-dx, -dy)]  # right, straight, left, back


def trace_contours(cells: set[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    """Trace a set of unit cells into closed polygons.

    Edges keep the fill on their left, so outer contours wind counter-clockwise
    and holes clockwise -- the PostScript/CFF convention.
    """
    edges: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for x, y in cells:
        if (x, y - 1) not in cells:
            edges.setdefault((x, y), []).append((x + 1, y))
        if (x + 1, y) not in cells:
            edges.setdefault((x + 1, y), []).append((x + 1, y + 1))
        if (x, y + 1) not in cells:
            edges.setdefault((x + 1, y + 1), []).append((x, y + 1))
        if (x - 1, y) not in cells:
            edges.setdefault((x, y + 1), []).append((x, y))

    contours = []
    while edges:
        start = next(iter(edges))
        point = start
        direction = (0, 0)
        contour: list[tuple[int, int]] = []
        while True:
            outgoing = edges.get(point)
            if not outgoing:
                break
            if len(outgoing) == 1 or direction == (0, 0):
                nxt = outgoing[0]
            else:
                candidates = {(e[0] - point[0], e[1] - point[1]): e for e in outgoing}
                nxt = next(candidates[t] for t in _turns(direction) if t in candidates)
            outgoing.remove(nxt)
            if not outgoing:
                del edges[point]
            contour.append(point)
            direction = (nxt[0] - point[0], nxt[1] - point[1])
            point = nxt
            if point == start:
                break
        if len(contour) >= 4:
            contours.append(_drop_collinear(contour))
    return contours


def _drop_collinear(contour: list[tuple[int, int]]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    n = len(contour)
    for i, cur in enumerate(contour):
        prev, nxt = contour[i - 1], contour[(i + 1) % n]
        if (cur[0] - prev[0]) * (nxt[1] - cur[1]) != (cur[1] - prev[1]) * (
            nxt[0] - cur[0]
        ):
            out.append(cur)
    return out


def to_font_units(
    contours: list[list[tuple[int, int]]],
) -> list[list[tuple[int, int]]]:
    """Grid coordinates -> font units."""
    return [[(x * PX, y * PX - DESCENT) for (x, y) in contour] for contour in contours]


# --- PNG output --------------------------------------------------------------

RGBA = {0: (0, 0, 0, 255), 2: (255, 255, 255, 255)}
TRANSPARENT_RGBA = (0, 0, 0, 0)


def glyph_image(glyph: Glyph, scale: int) -> Image.Image:
    img = Image.new("RGBA", (CHAR_W, CHAR_H), TRANSPARENT_RGBA)
    img.putdata([RGBA.get(v, TRANSPARENT_RGBA) for row in glyph.pixels for v in row])
    if scale != 1:
        img = img.resize((CHAR_W * scale, CHAR_H * scale), Image.Resampling.NEAREST)
    return img


def sheet_image(glyphs: list[Glyph], scale: int, columns: int = 16) -> Image.Image:
    rows = (len(glyphs) + columns - 1) // columns
    sheet = Image.new(
        "RGBA",
        (columns * CHAR_W * scale, rows * CHAR_H * scale),
        TRANSPARENT_RGBA,
    )
    for i, glyph in enumerate(glyphs):
        sheet.paste(
            glyph_image(glyph, scale),
            ((i % columns) * CHAR_W * scale, (i // columns) * CHAR_H * scale),
        )
    return sheet


# --- font building -----------------------------------------------------------


def glyph_name(index: int) -> str:
    return f"bf{index:02X}"


def unicode_name(codepoint: int) -> str:
    return f"uni{codepoint:04X}"


def cyrillic_glyphs(glyphs: list[Glyph]) -> dict[int, Glyph]:
    """Cyrillic capitals composed from this font's own Latin shapes."""
    latin = {chr(i): glyphs[i].pixels for i in range(0x20, 0x7F)}
    return {
        codepoint: Glyph(index=codepoint, pixels=pixels)
        for codepoint, pixels in cyrillic.glyphs(latin).items()
    }


def build_font(
    glyphs: list[Glyph],
    *,
    family: str,
    style: str = "Regular",
    ttf: bool,
    ascii_cmap: bool = True,
    fold_lowercase: bool = True,
    mode: str = "color",
    with_cyrillic: bool = True,
) -> FontBuilder:
    """Build one font.

    ``mode`` is ``color`` (two-layer COLR/CPAL) or the flat ``shadow``
    (silhouette) / ``fill`` (white pixels) pair, stacked by apps with no colour
    font support. All three share metrics, so the layers line up.
    """
    names = [glyph_name(g.index) for g in glyphs]
    order = [".notdef"]
    layers: dict[str, list[tuple[str, int]]] = {}
    outlines: dict[str, list[list[tuple[int, int]]]] = {".notdef": []}

    def add(name: str, ink: set[tuple[int, int]], white: set[tuple[int, int]]) -> None:
        silhouette = to_font_units(trace_contours(ink))
        white_contours = to_font_units(trace_contours(white))
        order.append(name)
        outlines[name] = white_contours if mode == "fill" else silhouette
        if mode != "color" or not ink:
            return
        order.extend((f"{name}.black", f"{name}.white"))
        outlines[f"{name}.black"] = silhouette
        outlines[f"{name}.white"] = white_contours
        layers[name] = [(f"{name}.black", 0), (f"{name}.white", 1)]

    for glyph, name in zip(glyphs, names, strict=True):
        add(name, glyph.ink(), glyph.cells(value=2))

    extra = cyrillic_glyphs(glyphs) if with_cyrillic else {}
    for codepoint, glyph in extra.items():
        add(unicode_name(codepoint), glyph.ink(), glyph.cells(value=2))

    cmap: dict[int, str] = {}
    for glyph, name in zip(glyphs, names, strict=True):
        cmap[PUA_BASE + glyph.index] = name
        if ascii_cmap and 0x20 <= glyph.index <= 0x7E:
            cmap[glyph.index] = name
    for codepoint in extra:
        cmap[codepoint] = unicode_name(codepoint)
    if fold_lowercase:
        # The fonts have no lowercase at all, Cyrillic included.
        for lower, upper in cyrillic.LOWERCASE.items():
            if upper in extra:
                cmap[lower] = unicode_name(upper)
    if ascii_cmap:
        cmap[0xA0] = cmap[0x20]
        if fold_lowercase:
            # a-z slots hold symbols, so a-z maps to the capitals instead;
            # the symbols stay reachable at U+E000+index.
            for index in range(ord("A"), ord("Z") + 1):
                cmap[index + 0x20] = glyph_name(index)

    fb = FontBuilder(UPM, isTTF=ttf)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)

    if ttf:
        pens = {}
        for name, contours in outlines.items():
            pen = TTGlyphPen(None)
            for contour in contours:
                # TrueType convention is the reverse of PostScript.
                pen.moveTo(contour[0])
                for point in reversed(contour[1:]):
                    pen.lineTo(point)
                pen.closePath()
            pens[name] = pen.glyph()
        fb.setupGlyf(pens)
    else:
        charstrings = {}
        for name, contours in outlines.items():
            pen = T2CharStringPen(ADVANCE, None)
            for contour in contours:
                pen.moveTo(contour[0])
                for point in contour[1:]:
                    pen.lineTo(point)
                pen.closePath()
            charstrings[name] = pen.getCharString()
        fb.setupCFF(
            f"{family}-{style}".replace(" ", ""),
            {"FullName": f"{family} {style}", "FamilyName": family, "Weight": style},
            charstrings,
            {},
        )

    # TrueType positions glyphs using hmtx lsb, so it has to match xMin exactly.
    fb.setupHorizontalMetrics(
        {
            name: (ADVANCE, min((x for c in outlines[name] for x, _ in c), default=0))
            for name in order
        }
    )
    fb.setupHorizontalHeader(ascent=ASCENT, descent=-DESCENT, lineGap=0)
    fb.setupNameTable(
        {
            "copyright": COPYRIGHT,
            "familyName": family,
            "styleName": style,
            "uniqueFontIdentifier": f"{family} {style}; {VERSION}",
            "fullName": f"{family} {style}",
            "version": f"Version {VERSION}",
            "psName": f"{family}-{style}".replace(" ", ""),
            "licenseDescription": LICENSE_TEXT,
            "licenseInfoURL": "https://www.gnu.org/licenses/gpl-3.0.html",
        }
    )
    fb.setupOS2(
        sTypoAscender=ASCENT,
        sTypoDescender=-DESCENT,
        sTypoLineGap=0,
        usWinAscent=ASCENT,
        usWinDescent=DESCENT,
        sCapHeight=13 * PX,
        sxHeight=9 * PX,
        achVendID="BFDF",
        panose={
            "bFamilyType": 2,  # latin text
            "bSerifStyle": 11,  # normal sans
            "bWeight": 6,
            "bProportion": 9,  # monospaced
            "bContrast": 0,
            "bStrokeVariation": 0,
            "bArmStyle": 0,
            "bLetterForm": 0,
            "bMidline": 0,
            "bXHeight": 0,
        },
    )
    fb.setupPost(isFixedPitch=1)
    if mode == "color":
        fb.font["COLR"] = buildCOLR(layers)
        fb.font["CPAL"] = buildCPAL([[(0, 0, 0, 1), (1, 1, 1, 1)]])
    return fb


# --- driver ------------------------------------------------------------------


def title_from_stem(stem: str) -> str:
    return " ".join(part.capitalize() for part in re.split(r"[_\-\s]+", stem) if part)


def convert(
    source: Path,
    out_root: Path,
    *,
    scale: int,
    family_prefix: str,
    family: str | None,
    no_ascii: bool,
    literal_ascii: bool,
    layer_fonts: bool,
    with_cyrillic: bool,
    formats: list[str],
) -> None:
    glyphs = parse_mcm(source)
    name = source.stem
    family_name = family or f"{family_prefix} {title_from_stem(name)}".strip()
    out = out_root / name
    png_dir, font_dir = out / "png", out / "fonts"
    png_dir.mkdir(parents=True, exist_ok=True)
    # One directory per format: up to three families times four formats.
    for fmt in formats:
        (font_dir / fmt).mkdir(parents=True, exist_ok=True)

    ascii_cmap, fold_lowercase = not no_ascii, not literal_ascii
    variants = [("color", family_name)]
    if layer_fonts:
        variants += [
            ("shadow", f"{family_name} Shadow"),
            ("fill", f"{family_name} Fill"),
        ]

    for glyph in glyphs:
        glyph_image(glyph, scale).save(png_dir / f"{glyph.index:03d}.png")
    sheet_image(glyphs, scale).save(out / f"{name}_sheet.png")

    extra = cyrillic_glyphs(glyphs) if with_cyrillic else {}
    if extra:
        cyr_dir = png_dir / "cyrillic"
        cyr_dir.mkdir(exist_ok=True)
        for codepoint, glyph in extra.items():
            glyph_image(glyph, scale).save(cyr_dir / f"{codepoint:04X}.png")
        sheet_image(list(extra.values()), scale).save(out / f"{name}_cyrillic.png")

    (out / f"{name}.json").write_text(
        json.dumps(
            {
                "source": source.name,
                "family": family_name,
                "cell": {"width": CHAR_W, "height": CHAR_H},
                "png_scale": scale,
                "families": [n for _, n in variants],
                "ascii_cmap": ascii_cmap,
                "lowercase_folded_to_uppercase": ascii_cmap and fold_lowercase,
                "cyrillic": [
                    {
                        "codepoint": f"U+{cp:04X}",
                        "letter": cyrillic.UPPERCASE[cp],
                        "png": f"png/cyrillic/{cp:04X}.png",
                    }
                    for cp in sorted(extra)
                ],
                "characters": [
                    {
                        "index": g.index,
                        "png": f"png/{g.index:03d}.png",
                        "codepoint": f"U+{PUA_BASE + g.index:04X}",
                        "ascii": chr(g.index)
                        if ascii_cmap and 0x21 <= g.index <= 0x7E
                        else None,
                        "blank": g.is_blank,
                    }
                    for g in glyphs
                ],
            },
            indent=2,
        )
        + "\n"
    )

    needs_ttf = {"ttf", "woff", "woff2"} & set(formats)
    for mode, name_ in variants:
        stem = name_.replace(" ", "")
        if "otf" in formats:
            fb = build_font(
                glyphs,
                family=name_,
                ttf=False,
                mode=mode,
                ascii_cmap=ascii_cmap,
                fold_lowercase=fold_lowercase,
                with_cyrillic=with_cyrillic,
            )
            fb.save(str(font_dir / "otf" / f"{stem}.otf"))
        if needs_ttf:
            fb = build_font(
                glyphs,
                family=name_,
                ttf=True,
                mode=mode,
                ascii_cmap=ascii_cmap,
                fold_lowercase=fold_lowercase,
                with_cyrillic=with_cyrillic,
            )
            if "ttf" in formats:
                fb.font.flavor = None
                fb.save(str(font_dir / "ttf" / f"{stem}.ttf"))
            for web in ("woff", "woff2"):
                if web in formats:
                    fb.font.flavor = web
                    fb.save(str(font_dir / web / f"{stem}.{web}"))

    blanks = sum(g.is_blank for g in glyphs)
    cyr = f" + {len(extra)} Cyrillic" if extra else ""
    print(
        f"{source.name}: {CHARS - blanks}/{CHARS} characters{cyr} -> {out} "
        f"({', '.join(formats)})"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert Betaflight MAX7456 .mcm OSD fonts to PNGs and font files.",
    )
    parser.add_argument("sources", nargs="+", type=Path, help=".mcm files to convert")
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("output"), help="output directory"
    )
    parser.add_argument(
        "-s", "--scale", type=int, default=8, help="PNG pixel scale (default: 8)"
    )
    parser.add_argument(
        "--formats",
        default="otf,ttf,woff,woff2",
        help="comma separated subset of otf,ttf,woff,woff2",
    )
    parser.add_argument(
        "--family", help="exact font family name (single source files only)"
    )
    parser.add_argument(
        "--family-prefix",
        default="Betaflight OSD",
        help="prefix for the derived family name (default: 'Betaflight OSD')",
    )
    parser.add_argument(
        "--no-ascii-cmap",
        action="store_true",
        help="map characters only to U+E000+index, not to ASCII",
    )
    parser.add_argument(
        "--literal-ascii",
        action="store_true",
        help="keep a-z on their own (symbol) slots instead of folding them "
        "onto the uppercase glyphs",
    )
    parser.add_argument(
        "--no-cyrillic",
        dest="with_cyrillic",
        action="store_false",
        help="skip the Cyrillic capitals composed from each font's own shapes",
    )
    parser.add_argument(
        "--no-layer-fonts",
        dest="layer_fonts",
        action="store_false",
        help="skip the flat Shadow and Fill families built for apps that "
        "cannot render colour fonts",
    )
    args = parser.parse_args(argv)
    os.environ.setdefault("SOURCE_DATE_EPOCH", SOURCE_DATE_EPOCH)

    formats = [f.strip().lower() for f in args.formats.split(",") if f.strip()]
    unknown = set(formats) - {"otf", "ttf", "woff", "woff2"}
    if unknown:
        parser.error(f"unknown format(s): {', '.join(sorted(unknown))}")
    if args.scale < 1:
        parser.error("--scale must be >= 1")
    if args.family and len(args.sources) > 1:
        parser.error("--family can only be used with a single source file")

    for source in args.sources:
        convert(
            source,
            args.output,
            scale=args.scale,
            family_prefix=args.family_prefix,
            family=args.family,
            no_ascii=args.no_ascii_cmap,
            literal_ascii=args.literal_ascii,
            layer_fonts=args.layer_fonts,
            with_cyrillic=args.with_cyrillic,
            formats=formats,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
