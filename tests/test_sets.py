"""The character sets composed on top of the source font.

test_cyrillic.py covers the Cyrillic in detail; these are the rules every
composed set has to keep, whichever set it is.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path

import pytest
from conftest import font_paths, rasterise

from bf2font import (
    CHAR_H,
    CHAR_W,
    SETS,
    Glyph,
    build_font,
    composed_glyphs,
    folds,
    latin_shapes,
    parse_mcm,
    trace_contours,
)
from scripts import accents, blocks, greek, punctuation
from scripts.shapes import SAFE_X, SAFE_Y, WHITE, core_of, shift

# blocks is the one set that runs to the cell wall on purpose: a frame has to
# join up with the cell next to it.
DRAWN_TO_THE_EDGE = {"blocks"}
SET_NAMES = sorted(SETS)


def latin_of(path: Path) -> dict[str, list[list[int]]]:
    return latin_shapes(parse_mcm(path))


@pytest.fixture(scope="session")
def clarity() -> dict[str, list[list[int]]]:
    return latin_of(Path("original_fonts/clarity.mcm"))


@pytest.mark.parametrize("path", font_paths(), ids=lambda p: p.stem)
@pytest.mark.parametrize("name", SET_NAMES)
def test_every_font_composes_every_character(path: Path, name: str) -> None:
    made = SETS[name].glyphs(latin_of(path))
    assert made, name
    for codepoint, px in made.items():
        where = f"{name} U+{codepoint:04X}"
        assert len(px) == CHAR_H and all(len(r) == CHAR_W for r in px), where
        assert any(v == WHITE for row in px for v in row), f"{where} is blank"


@pytest.mark.parametrize("path", font_paths(), ids=lambda p: p.stem)
@pytest.mark.parametrize("name", sorted(set(SET_NAMES) - DRAWN_TO_THE_EDGE))
def test_composed_characters_keep_a_row_for_their_outline(
    path: Path, name: str
) -> None:
    """White on the cell wall has no room left for the black outline.

    Every face leaves at least three rows above its cap line and one below, and
    the marks that need more than that move the letter rather than spill.
    """
    for codepoint, px in SETS[name].glyphs(latin_of(path)).items():
        white = [
            (x, y) for y, row in enumerate(px) for x, v in enumerate(row) if v == WHITE
        ]
        outside = [
            cell
            for cell in white
            if not (SAFE_X[0] - 1 <= cell[0] <= SAFE_X[1] + 1)
            or not (SAFE_Y[0] - 1 <= cell[1] <= SAFE_Y[1] + 1)
        ]
        assert not outside, f"{name} U+{codepoint:04X} reaches {outside}"
        walls = [c for c in white if c[0] in (0, CHAR_W - 1) or c[1] in (0, CHAR_H - 1)]
        assert not walls, f"{name} U+{codepoint:04X} touches the cell wall at {walls}"


@pytest.mark.parametrize("path", font_paths(), ids=lambda p: p.stem)
@pytest.mark.parametrize("name", SET_NAMES)
def test_characters_are_all_distinct(path: Path, name: str) -> None:
    """Two codepoints drawing the same shape means one of them lost a detail.

    The deliberate pairs are aliases: Eth and D with stroke are one letter in
    two blocks, as are the two euro signs.
    """
    allowed = {frozenset({0x00D0, 0x0110}), frozenset({0x20A0, 0x20AC})}
    seen: dict[frozenset[tuple[int, int]], int] = {}
    for codepoint, core in SETS[name].cores(latin_of(path)).items():
        key = frozenset(core)
        twin = seen.get(key)
        if twin is not None:
            assert frozenset({twin, codepoint}) in allowed, (
                f"U+{twin:04X} and U+{codepoint:04X} are the same shape"
            )
        seen[key] = codepoint


@pytest.mark.parametrize("name", SET_NAMES)
def test_characters_have_the_names_unicode_gives_them(name: str) -> None:
    """A typo in a codepoint is otherwise invisible until someone types it."""
    described = getattr(SETS[name], "NAMES", None)
    if described is None:
        pytest.skip(f"{name} names its characters by the letter, not the codepoint")
    for codepoint, description in described.items():
        assert unicodedata.name(chr(codepoint)).lower() == description


@pytest.mark.parametrize("path", font_paths(), ids=lambda p: p.stem)
def test_glyphs_vectorise_losslessly(path: Path) -> None:
    """Composed bitmaps must survive the outline tracer like any other."""
    for glyph in composed_glyphs(parse_mcm(path)).values():
        for cells in (glyph.ink(), glyph.cells(value=2)):
            assert rasterise(trace_contours(cells)) == cells, hex(glyph.index)


def test_accents_are_the_letter_plus_a_mark(
    clarity: dict[str, list[list[int]]],
) -> None:
    """An accented letter is its letter, whole, plus the mark.

    The letter may have moved a row to make room for a mark below it, so the
    match allows for that, but nothing may be dropped from the letter itself.
    """
    made = accents.cores(clarity)
    for codepoint, (letter, mark) in accents.COMPOSED.items():
        base = core_of(clarity[letter])
        shape = made[codepoint]
        moved = [dy for dy in (0, -1, -2, 1, 2) if shift(base, 0, dy) <= shape]
        assert moved, f"U+{codepoint:04X} does not contain a whole {letter}"
        assert len(shape) > len(base), f"U+{codepoint:04X} added no {mark}"


def test_greek_reuses_the_letters_the_font_already_has(
    clarity: dict[str, list[list[int]]],
) -> None:
    made = greek.cores(clarity)
    for codepoint, letter in greek.AS_LATIN.items():
        assert made[codepoint] == core_of(clarity[letter])


def test_lowercase_folds_onto_the_capitals() -> None:
    """The fonts have no lowercase in any script, so it all folds."""
    for name in SET_NAMES:
        lower = getattr(SETS[name], "LOWERCASE", {})
        made = SETS[name].cores(latin_of(Path("original_fonts/clarity.mcm")))
        for small, capital in lower.items():
            assert capital in made or 0x20 <= capital <= 0x7E, hex(small)


def test_spelled_out_characters_expand_to_characters_the_font_has(
    clarity: dict[str, list[list[int]]],
) -> None:
    glyphs = parse_mcm(Path("original_fonts/clarity.mcm"))
    made = composed_glyphs(glyphs)
    for codepoint, text in folds().items():
        assert codepoint not in made, f"U+{codepoint:04X} is both drawn and spelled"
        for ch in text:
            assert ord(ch) in made or 0x20 <= ord(ch) <= 0x7E, f"{text!r} needs {ch!r}"


def test_blocks_run_to_the_cell_wall() -> None:
    """Box drawing that stops short of the wall leaves gaps in a frame."""
    made = blocks.cores(latin_of(Path("original_fonts/clarity.mcm")))
    horizontal = made[0x2500]
    assert {x for x, _ in horizontal} == set(range(CHAR_W))
    assert {y for _, y in made[0x2502]} == set(range(CHAR_H))
    assert len(made[0x2588]) == CHAR_W * CHAR_H, "the full block fills the cell"


def test_punctuation_dashes_are_three_widths(
    clarity: dict[str, list[list[int]]],
) -> None:
    made = punctuation.cores(clarity)
    hyphen = core_of(clarity["-"])
    widths = [
        len({x for x, _ in shape}) for shape in (hyphen, made[0x2013], made[0x2014])
    ]
    assert widths[0] < widths[1] < widths[2], widths


def test_a_set_can_be_left_out() -> None:
    glyphs = parse_mcm(Path("original_fonts/clarity.mcm"))
    made = composed_glyphs(glyphs, ("punctuation",))
    assert 0x2014 in made and 0x0410 not in made


def test_composed_glyphs_are_ordinary_glyphs() -> None:
    made = composed_glyphs(parse_mcm(Path("original_fonts/clarity.mcm")))
    assert all(isinstance(g, Glyph) for g in made.values())
    assert not any(g.is_blank for g in made.values())


def test_the_font_carries_every_composed_character() -> None:
    glyphs = parse_mcm(Path("original_fonts/clarity.mcm"))
    cmap = build_font(glyphs, family="T", ttf=True).font.getBestCmap()
    for codepoint in composed_glyphs(glyphs):
        assert codepoint in cmap, hex(codepoint)
    for codepoint in folds():
        assert codepoint in cmap, hex(codepoint)
