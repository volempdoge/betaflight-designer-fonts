"""The OSD icon catalogue, and the OpenType features that reach it."""

from __future__ import annotations

import io

import pytest
import uharfbuzz as hb
from conftest import FONT_DIR
from fontTools.ttLib import TTFont

import symbols
from bf2font import CHARS, PUA_BASE, Glyph, build_font, parse_mcm


@pytest.fixture(scope="session")
def glyphs() -> list[Glyph]:
    return parse_mcm(FONT_DIR / "default.mcm")


@pytest.fixture(scope="session")
def font(glyphs: list[Glyph]) -> TTFont:
    return build_font(glyphs, family="Test Font", ttf=True).font


@pytest.fixture(scope="session")
def shaper(font: TTFont) -> hb.Font:
    data = io.BytesIO()
    font.save(data)
    return hb.Font(hb.Face(data.getvalue()))


def shape(font: TTFont, shaper: hb.Font, text: str) -> list[str]:
    """The glyphs a renderer actually puts on the page for `text`."""
    order = font.getGlyphOrder()
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(shaper, buffer)
    return [order[info.codepoint] for info in buffer.glyph_infos]


def test_every_symbol_is_a_character_of_the_font() -> None:
    for symbol in symbols.SYMBOLS:
        assert 0 <= symbol.index < CHARS, symbol.name


def test_names_are_unique_and_typeable() -> None:
    names = [symbol.name for symbol in symbols.SYMBOLS]
    assert len(set(names)) == len(names)
    for name in names:
        assert name.replace("_", "").isalnum() and name.islower(), name


def test_the_logo_is_the_last_96_characters() -> None:
    logo = [s for s in symbols.SYMBOLS if s.group == "logo"]
    assert len(logo) == CHARS - symbols.LOGO_START
    assert [s.index for s in logo] == list(range(symbols.LOGO_START, CHARS))


def test_no_symbol_claims_a_blank_character(glyphs: list[Glyph]) -> None:
    """A name for an empty cell would be a promise the font cannot keep.

    The logo is the exception: it is one picture, and some of its tiles are
    blank on purpose.
    """
    for symbol in symbols.SYMBOLS:
        if symbol.group != "logo":
            assert not glyphs[symbol.index].is_blank, symbol.name


def test_aliases_point_at_the_character_they_describe(font: TTFont) -> None:
    cmap = font.getBestCmap()
    for codepoint, index in symbols.ALIASES.items():
        assert cmap[codepoint] == f"bf{index:02X}", hex(codepoint)


def test_every_symbol_keeps_its_private_use_codepoint(font: TTFont) -> None:
    cmap = font.getBestCmap()
    for symbol in symbols.SYMBOLS:
        assert cmap[PUA_BASE + symbol.index] == f"bf{symbol.index:02X}"


@pytest.mark.parametrize(
    "name", ["battery", "home", "sat_left", "arrow_n", "logo_00", "flag"]
)
def test_typing_a_name_produces_the_icon(
    font: TTFont, shaper: hb.Font, name: str
) -> None:
    index = symbols.BY_NAME[name].index
    assert shape(font, shaper, f":{name}:") == [f"bf{index:02X}"]


def test_every_ligature_resolves(font: TTFont, shaper: hb.Font) -> None:
    for token, index in symbols.ligatures().items():
        assert shape(font, shaper, token) == [f"bf{index:02X}"], token


def test_ordinary_text_is_left_alone(font: TTFont, shaper: hb.Font) -> None:
    """The ligatures all start with a colon; a clock must survive one."""
    assert shape(font, shaper, "12:30:45") == [
        "bf31",
        "bf32",
        "bf3A",
        "bf33",
        "bf30",
        "bf3A",
        "bf34",
        "bf35",
    ]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Æ", ["bf41", "bf45"]),
        ("ß", ["bf53", "bf53"]),
        ("Œ", ["bf4F", "bf45"]),
        ("™", ["bf54", "bf4D"]),
        ("№", ["bf4E", "uni00B0"]),
        ("½", ["bf31", "bf2F", "bf32"]),
        ("©", ["bf28", "bf43", "bf29"]),
    ],
)
def test_spelled_out_characters_expand(
    font: TTFont, shaper: hb.Font, text: str, expected: list[str]
) -> None:
    assert shape(font, shaper, text) == expected


def test_a_font_without_ascii_has_no_ligatures(glyphs: list[Glyph]) -> None:
    """Without ASCII there is no colon to type, so the feature is pointless."""
    font = build_font(glyphs, family="T", ttf=True, ascii_cmap=False).font
    assert "GSUB" not in font
