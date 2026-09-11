"""Building the OpenType files."""

from __future__ import annotations

import pytest
from conftest import FONT_DIR
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from bf2font import (
    ADVANCE,
    ASCENT,
    DESCENT,
    PUA_BASE,
    UPM,
    Glyph,
    build_font,
    parse_mcm,
)


@pytest.fixture(scope="session")
def glyphs() -> list[Glyph]:
    return parse_mcm(FONT_DIR / "default.mcm")


def make(
    glyphs: list[Glyph],
    *,
    ttf: bool = True,
    mode: str = "color",
    ascii_cmap: bool = True,
    fold_lowercase: bool = True,
) -> TTFont:
    return build_font(
        glyphs,
        family="Test Font",
        ttf=ttf,
        mode=mode,
        ascii_cmap=ascii_cmap,
        fold_lowercase=fold_lowercase,
    ).font


@pytest.fixture(scope="session")
def colour_ttf(glyphs: list[Glyph]) -> TTFont:
    return make(glyphs)


@pytest.mark.parametrize("ttf", [True, False], ids=["glyf", "cff"])
def test_colour_font_has_two_layers_per_character(
    glyphs: list[Glyph], ttf: bool
) -> None:
    font = make(glyphs, ttf=ttf)
    assert font["COLR"].version == 0
    non_blank = sum(not g.is_blank for g in glyphs)
    assert len(font["COLR"].ColorLayers) == non_blank
    layers = font["COLR"].ColorLayers["bf41"]
    assert [(layer.name, layer.colorID) for layer in layers] == [
        ("bf41.black", 0),
        ("bf41.white", 1),
    ]


def test_palette_is_black_then_white(colour_ttf: TTFont) -> None:
    black, white = colour_ttf["CPAL"].palettes[0]
    assert (black.red, black.green, black.blue, black.alpha) == (0, 0, 0, 255)
    assert (white.red, white.green, white.blue, white.alpha) == (255, 255, 255, 255)


@pytest.mark.parametrize("mode", ["shadow", "fill"])
def test_flat_fonts_carry_no_colour_tables(glyphs: list[Glyph], mode: str) -> None:
    font = make(glyphs, mode=mode)
    assert "COLR" not in font
    assert "CPAL" not in font


def test_flat_fonts_reproduce_the_colour_layers(glyphs: list[Glyph]) -> None:
    """Shadow is the base glyph, Fill is the white layer, so stacking matches."""
    colour = make(glyphs)
    shadow, fill = make(glyphs, mode="shadow"), make(glyphs, mode="fill")
    base = colour.getGlyphSet()
    for name, other, layer in (
        ("shadow", shadow.getGlyphSet(), "bf41"),
        ("fill", fill.getGlyphSet(), "bf41.white"),
    ):
        want, got = BoundsPen(base), BoundsPen(other)
        base[layer].draw(want)
        other["bf41"].draw(got)
        assert want.bounds == got.bounds, name


@pytest.mark.parametrize("mode", ["color", "shadow", "fill"])
@pytest.mark.parametrize("ttf", [True, False], ids=["glyf", "cff"])
def test_metrics_are_identical_across_modes(
    glyphs: list[Glyph], mode: str, ttf: bool
) -> None:
    """Stacked text layers only line up if every build shares its metrics."""
    font = make(glyphs, mode=mode, ttf=ttf)
    assert font["head"].unitsPerEm == UPM
    assert font["hhea"].ascender == ASCENT
    assert font["hhea"].descender == -DESCENT
    assert {font["hmtx"][n][0] for n in font.getGlyphOrder()} == {ADVANCE}


@pytest.mark.parametrize("ttf", [True, False], ids=["glyf", "cff"])
def test_left_side_bearing_matches_xmin(glyphs: list[Glyph], ttf: bool) -> None:
    """TrueType positions glyphs by lsb: a wrong one shifts the whole glyph."""
    font = make(glyphs, ttf=ttf)
    glyph_set = font.getGlyphSet()
    for name in font.getGlyphOrder():
        pen = BoundsPen(glyph_set)
        glyph_set[name].draw(pen)
        expected = 0 if pen.bounds is None else pen.bounds[0]
        assert font["hmtx"][name][1] == expected, name


def test_character_map(colour_ttf: TTFont) -> None:
    cmap = colour_ttf.getBestCmap()
    assert cmap[0x41] == "bf41", "A is typed normally"
    assert cmap[PUA_BASE + 0x01] == "bf01", "symbols live in the private use area"
    assert len(cmap) == 256 + (0x7E - 0x20 + 1) + 1, "PUA + ASCII + nbsp"


def test_lowercase_folds_onto_uppercase(colour_ttf: TTFont) -> None:
    cmap = colour_ttf.getBestCmap()
    assert cmap[ord("a")] == cmap[ord("A")] == "bf41"


def test_literal_ascii_keeps_the_symbol_slots(glyphs: list[Glyph]) -> None:
    cmap = make(glyphs, fold_lowercase=False).getBestCmap()
    assert cmap[ord("a")] == "bf61" != cmap[ord("A")]


def test_ascii_map_can_be_turned_off(glyphs: list[Glyph]) -> None:
    cmap = make(glyphs, ascii_cmap=False).getBestCmap()
    assert 0x41 not in cmap
    assert cmap[PUA_BASE + 0x41] == "bf41"


def test_name_table(colour_ttf: TTFont) -> None:
    assert colour_ttf["name"].getDebugName(1) == "Test Font"
    assert "GNU General Public License" in colour_ttf["name"].getDebugName(13)
