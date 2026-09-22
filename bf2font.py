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
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from fontTools.colorLib.builder import buildCOLR, buildCPAL
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from PIL import Image

from scripts import accents, blocks, cyrillic, greek, punctuation, symbols

# --- composed character sets -------------------------------------------------

# Everything beyond the 256 characters of the source font, drawn from the
# font's own shapes. Order matters only for reporting.
SETS = {
    "cyrillic": cyrillic,
    "accents": accents,
    "greek": greek,
    "punctuation": punctuation,
    "blocks": blocks,
}
DEFAULT_SETS = tuple(SETS)


def folds(sets: Sequence[str] = DEFAULT_SETS) -> dict[int, str]:
    """Codepoint -> the characters it is spelled with, across the named sets."""
    out: dict[int, str] = {}
    for name in sets:
        out.update(getattr(SETS[name], "FOLDS", {}))
    return out


def lowercase(sets: Sequence[str] = DEFAULT_SETS) -> dict[int, int]:
    """Lowercase codepoint -> its capital. Blocks and the like have none."""
    out: dict[int, int] = {}
    for name in sets:
        out.update(getattr(SETS[name], "LOWERCASE", {}))
    return out


# --- MAX7456 geometry --------------------------------------------------------

CHAR_W = 12
CHAR_H = 18
CHARS = 256
BYTES_PER_CHAR = 64  # 54 bytes of pixel data + 10 bytes of padding
PIXEL_BYTES = CHAR_W * CHAR_H * 2 // 8  # 54

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
    lines = path.read_text(encoding="utf-8").splitlines()
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


def latin_shapes(glyphs: list[Glyph]) -> dict[str, list[list[int]]]:
    """The font's own ASCII, keyed by character, for the composed sets."""
    return {chr(i): glyphs[i].pixels for i in range(0x20, 0x7F)}


def cap_height(glyphs: list[Glyph]) -> int:
    """OS/2 sCapHeight in font units, measured off the font's own H.

    The white core is the letter itself; the black cells around it are the
    outline the OSD draws for contrast, and are not part of the cap height.
    Ten faces run from 7 to 14 pixels, so this cannot be a constant. A font
    that has blanked its H keeps the value clarity measures.
    """
    core = glyphs[ord("H")].cells(value=2)
    if not core:
        return 13 * PX
    ys = [y for _, y in core]
    return (max(ys) - min(ys) + 1) * PX


def composed_glyphs(
    glyphs: list[Glyph], sets: Sequence[str] = DEFAULT_SETS
) -> dict[int, Glyph]:
    """Every glyph the named sets compose from this font's own shapes."""
    latin = latin_shapes(glyphs)
    out: dict[int, Glyph] = {}
    for name in sets:
        try:
            made = SETS[name].glyphs(latin)
        except (ValueError, IndexError, KeyError) as exc:
            raise ValueError(
                f"cannot compose the {name!r} set: {type(exc).__name__}: {exc}. "
                "The composed sets are traced off the font's own ASCII capitals, "
                "so a font that overwrites those slots with icons has nothing to "
                'trace -- re-run with --sets "" to convert it as is'
            ) from exc
        for codepoint, pixels in made.items():
            out[codepoint] = Glyph(index=codepoint, pixels=pixels)
    return out


def build_font(
    glyphs: list[Glyph],
    *,
    family: str,
    style: str = "Regular",
    ttf: bool,
    ascii_cmap: bool = True,
    fold_lowercase: bool = True,
    mode: str = "color",
    sets: Sequence[str] = DEFAULT_SETS,
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

    extra = composed_glyphs(glyphs, sets)
    for codepoint, glyph in extra.items():
        add(unicode_name(codepoint), glyph.ink(), glyph.cells(value=2))

    cmap: dict[int, str] = {}
    for glyph, name in zip(glyphs, names, strict=True):
        cmap[PUA_BASE + glyph.index] = name
        if ascii_cmap and 0x20 <= glyph.index <= 0x7E:
            cmap[glyph.index] = name
    if ascii_cmap:
        # Icons that are also a standard character -- the compass arrows, the
        # home symbol, degrees Celsius. A drawn glyph wins over an icon, so
        # these go in before the composed sets.
        for codepoint, index in symbols.ALIASES.items():
            cmap[codepoint] = glyph_name(index)
    for codepoint in extra:
        cmap[codepoint] = unicode_name(codepoint)
    if fold_lowercase:
        # The fonts have no lowercase at all, in any script.
        for lower, upper in lowercase(sets).items():
            if upper in extra:
                cmap[lower] = unicode_name(upper)
            elif ascii_cmap and 0x20 <= upper <= 0x7E:
                cmap[lower] = glyph_name(upper)
    if ascii_cmap:
        cmap[0xA0] = cmap[0x20]
        if fold_lowercase:
            # a-z slots hold symbols, so a-z maps to the capitals instead;
            # the symbols stay reachable at U+E000+index.
            for index in range(ord("A"), ord("Z") + 1):
                cmap[index + 0x20] = glyph_name(index)

    # Characters that are spelled out rather than drawn: the codepoint carries
    # a copy of the first letter's shape, and GSUB expands it to the rest.
    spelled = folds(sets) if ascii_cmap else {}
    spelled = {
        codepoint: text
        for codepoint, text in spelled.items()
        if all(ord(ch) in cmap for ch in text)
    }
    for codepoint, text in spelled.items():
        stand_in = extra.get(ord(text[0])) or glyphs[ord(text[0])]
        add(unicode_name(codepoint), stand_in.ink(), stand_in.cells(value=2))
        cmap[codepoint] = unicode_name(codepoint)

    fb = FontBuilder(UPM, isTTF=ttf)
    # fontTools packs GSUB with harfbuzz's repacker when uharfbuzz happens to
    # be importable, and with its own packer otherwise. Both produce the same
    # table, the same size, byte for byte differently -- which would make the
    # committed output/ depend on whether a dev extra is installed. Pin it.
    fb.font.cfg["fontTools.ttLib.tables.otBase:USE_HARFBUZZ_REPACKER"] = False
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
    caps = cap_height(glyphs)
    fb.setupOS2(
        sTypoAscender=ASCENT,
        sTypoDescender=-DESCENT,
        sTypoLineGap=0,
        usWinAscent=ASCENT,
        usWinDescent=DESCENT,
        sCapHeight=caps,
        # There is no lowercase in any script here: a-z fold onto the capitals,
        # so the x-height a renderer should use is the cap height.
        sxHeight=caps,
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
    feature_text = features(cmap, spelled) if ascii_cmap else ""
    if feature_text:
        addOpenTypeFeaturesFromString(fb.font, feature_text)
    return fb


def features(cmap: dict[int, str], spelled: dict[int, str]) -> str:
    """The OpenType features: icon ligatures, and the spelled-out characters.

    `liga` is on by default in every renderer that reads OpenType at all, which
    is what makes `:battery:` work by just typing it. `ccmp` runs earlier and
    is what turns one codepoint into several glyphs.
    """

    def run(text: str) -> str | None:
        if any(ord(ch) not in cmap for ch in text):
            return None
        return " ".join(cmap[ord(ch)] for ch in text)

    rules = []
    for token, index in symbols.ligatures().items():
        components = run(token)
        if components:
            rules.append(f"    sub {components} by {glyph_name(index)};")
    spellings = []
    for codepoint, text in spelled.items():
        components = run(text)
        if components:
            spellings.append(f"    sub {unicode_name(codepoint)} by {components};")

    blocks_out = []
    if spellings:
        blocks_out.append("feature ccmp {\n" + "\n".join(spellings) + "\n} ccmp;\n")
    if rules:
        blocks_out.append("feature liga {\n" + "\n".join(rules) + "\n} liga;\n")
    return "\n".join(blocks_out)


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
    sets: Sequence[str],
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

    composed = {set_name: composed_glyphs(glyphs, (set_name,)) for set_name in sets}
    for set_name, made in composed.items():
        set_dir = png_dir / set_name
        set_dir.mkdir(exist_ok=True)
        for codepoint, glyph in made.items():
            glyph_image(glyph, scale).save(set_dir / f"{codepoint:04X}.png")
        by_codepoint = [made[cp] for cp in sorted(made)]
        sheet_image(by_codepoint, scale).save(out / f"{name}_{set_name}.png")

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
                "sets": {
                    set_name: [
                        {
                            "codepoint": f"U+{cp:04X}",
                            "character": chr(cp),
                            "png": f"png/{set_name}/{cp:04X}.png",
                        }
                        for cp in sorted(made)
                    ]
                    for set_name, made in composed.items()
                },
                "spelled": {
                    f"U+{cp:04X}": text
                    for cp, text in sorted(folds(sets).items() if ascii_cmap else [])
                },
                "symbols": [
                    {
                        "index": symbol.index,
                        "name": symbol.name,
                        "group": symbol.group,
                        "label": symbol.label,
                        "ligature": f":{symbol.name}:",
                        "codepoint": f"U+{PUA_BASE + symbol.index:04X}",
                        "unicode": [f"U+{cp:04X}" for cp in symbol.unicode],
                        "png": f"png/{symbol.index:03d}.png",
                    }
                    for symbol in symbols.SYMBOLS
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
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
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
                sets=sets,
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
                sets=sets,
            )
            if "ttf" in formats:
                fb.font.flavor = None
                fb.save(str(font_dir / "ttf" / f"{stem}.ttf"))
            for web in ("woff", "woff2"):
                if web in formats:
                    fb.font.flavor = web
                    fb.save(str(font_dir / web / f"{stem}.{web}"))

    blanks = sum(g.is_blank for g in glyphs)
    added = sum(len(made) for made in composed.values())
    extra = f" + {added} composed" if added else ""
    print(
        f"{source.name}: {CHARS - blanks}/{CHARS} characters{extra} -> {out} "
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
        help="drop the ASCII cmap and the name ligatures; the composed "
        "sets keep their own codepoints",
    )
    parser.add_argument(
        "--literal-ascii",
        action="store_true",
        help="keep a-z on their own (symbol) slots instead of folding them "
        "onto the uppercase glyphs",
    )
    parser.add_argument(
        "--sets",
        default=",".join(DEFAULT_SETS),
        help="comma separated subset of "
        f"{','.join(DEFAULT_SETS)} -- the character sets composed from each "
        "font's own shapes (default: all of them, empty for none)",
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
    if not formats:
        parser.error("--formats needs at least one of otf,ttf,woff,woff2")
    sets = [s.strip().lower() for s in args.sets.split(",") if s.strip()]
    unknown = set(sets) - set(DEFAULT_SETS)
    if unknown:
        parser.error(f"unknown character set(s): {', '.join(sorted(unknown))}")
    if args.scale < 1:
        parser.error("--scale must be >= 1")
    if args.family and len(args.sources) > 1:
        parser.error("--family can only be used with a single source file")

    failed = 0
    for source in args.sources:
        try:
            convert(
                source,
                args.output,
                scale=args.scale,
                family_prefix=args.family_prefix,
                family=args.family,
                no_ascii=args.no_ascii_cmap,
                literal_ascii=args.literal_ascii,
                layer_fonts=args.layer_fonts,
                sets=sets,
                formats=formats,
            )
        except (OSError, ValueError, UnicodeDecodeError) as exc:
            print(f"{source}: {exc}", file=sys.stderr)
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
