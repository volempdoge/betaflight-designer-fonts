"""Cyrillic capitals composed from each font's own shapes."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import font_paths, rasterise

from bf2font import CHAR_H, CHAR_W, Glyph, build_font, composed_glyphs, parse_mcm
from scripts import cyrillic
from scripts.cyrillic import compose
from scripts.shapes import WHITE, Geometry, core_of, mirror, outline, runs


def latin_of(path: Path) -> dict[str, list[list[int]]]:
    glyphs = parse_mcm(path)
    return {chr(i): glyphs[i].pixels for i in range(0x20, 0x7F)}


@pytest.fixture(scope="session")
def clarity() -> dict[str, list[list[int]]]:
    return latin_of(Path("original_fonts/clarity.mcm"))


def test_alphabet_is_complete() -> None:
    assert len(cyrillic.UPPERCASE) == 37
    assert set(cyrillic.UKRAINIAN) <= set(cyrillic.UPPERCASE.values())
    assert len(cyrillic.LOWERCASE) == len(cyrillic.UPPERCASE)
    assert set(cyrillic.LOWERCASE.values()) == set(cyrillic.UPPERCASE)


@pytest.mark.parametrize("path", font_paths(), ids=lambda p: p.stem)
def test_every_font_composes_every_letter(path: Path) -> None:
    made = cyrillic.glyphs(latin_of(path))
    assert set(made) == set(cyrillic.UPPERCASE)
    for codepoint, px in made.items():
        letter = cyrillic.UPPERCASE[codepoint]
        assert len(px) == CHAR_H and all(len(r) == CHAR_W for r in px), letter
        assert any(v == WHITE for row in px for v in row), f"{letter} is blank"


def touches_edge(px: list[list[int]]) -> bool:
    return WHITE in (
        [px[0][x] for x in range(CHAR_W)]
        + [px[CHAR_H - 1][x] for x in range(CHAR_W)]
        + [row[0] for row in px]
        + [row[CHAR_W - 1] for row in px]
    )


@pytest.mark.parametrize("path", font_paths(), ids=lambda p: p.stem)
def test_composed_letters_fit_as_well_as_the_font_s_own(path: Path) -> None:
    """The outline wants a row and column of room around the core.

    The bar is what the font itself does: betaflight's own capitals already
    run into the cell wall.
    """
    latin = latin_of(path)
    native = any(
        touches_edge(px) for ch, px in latin.items() if ch.isalpha() or ch.isdigit()
    )
    clipped = [
        cyrillic.UPPERCASE[cp]
        for cp, px in cyrillic.glyphs(latin).items()
        if touches_edge(px)
    ]
    assert native or not clipped, (
        f"composed letters clip where Latin does not: {clipped}"
    )


def strokes(core: set[tuple[int, int]]) -> int:
    """The most separate white runs a shape has on any one row."""
    return max(
        len(runs([x for x, yy in core if yy == y])) for y in {y for _, y in core}
    )


@pytest.mark.parametrize("path", font_paths(), ids=lambda p: p.stem)
@pytest.mark.parametrize("letter", ["Ш", "Щ", "Ж", "Ю", "Ы"])
def test_three_stem_letters_keep_their_stems_apart(path: Path, letter: str) -> None:
    """Without the wider box (and Ж's squared fallback) the stems merge."""
    assert strokes(compose(latin_of(path))[letter]) >= 3


@pytest.mark.parametrize("path", font_paths(), ids=lambda p: p.stem)
def test_bowls_stay_hollow(path: Path) -> None:
    """Ф and О must keep a counter; a merged centre stem would fill them."""
    latin = latin_of(path)
    geometry = Geometry(latin)
    made = compose(latin)
    waist = (geometry.top + geometry.bottom) // 2
    for letter in ("Ф", "О", "Ю"):
        core = made[letter]
        assert len(runs([x for x, y in core if y == waist])) >= 2, letter


def test_outline_hugs_the_core(clarity: dict[str, list[list[int]]]) -> None:
    """Every outline cell touches the core, and the core is fully enclosed."""
    for core in compose(clarity).values():
        ring = outline(core)
        assert not ring & core
        for x, y in ring:
            assert any(
                (x + dx, y + dy) in core
                for dx, dy in (
                    (1, 0),
                    (-1, 0),
                    (0, 1),
                    (0, -1),
                    (1, 1),
                    (1, -1),
                    (-1, 1),
                    (-1, -1),
                )
            )


def test_reused_letters_are_the_font_s_own(clarity: dict[str, list[list[int]]]) -> None:
    made = compose(clarity)
    for cyr, lat in cyrillic.SAME_AS_LATIN.items():
        assert made[cyr] == core_of(clarity[lat]), cyr


def test_mirrored_letters_are_reflections(clarity: dict[str, list[list[int]]]) -> None:
    made = compose(clarity)
    for cyr, lat in cyrillic.MIRRORED.items():
        assert made[cyr] == mirror(core_of(clarity[lat])), cyr
        assert made[cyr] != core_of(clarity[lat]), f"{cyr} is symmetric?"


def test_glyphs_vectorise_losslessly() -> None:
    """The composed bitmaps must survive the outline tracer like any other."""
    glyphs = parse_mcm(Path("original_fonts/clarity.mcm"))
    for glyph in composed_glyphs(glyphs, ("cyrillic",)).values():
        for cells in (glyph.ink(), glyph.cells(value=2)):
            from bf2font import trace_contours

            assert rasterise(trace_contours(cells)) == cells


def test_font_carries_the_letters_at_their_real_codepoints() -> None:
    glyphs = parse_mcm(Path("original_fonts/clarity.mcm"))
    font = build_font(glyphs, family="T", ttf=True).font
    cmap = font.getBestCmap()
    assert cmap[0x0410] == "uni0410", "А"
    assert cmap[0x0490] == "uni0490", "Ґ"
    assert cmap[0x0430] == cmap[0x0410], "lowercase folds onto the capital"
    non_blank = sum(not g.is_blank for g in glyphs)
    assert len(font["COLR"].ColorLayers) > non_blank + len(cyrillic.UPPERCASE)


def test_cyrillic_can_be_turned_off() -> None:
    glyphs = parse_mcm(Path("original_fonts/clarity.mcm"))
    cmap = build_font(glyphs, family="T", ttf=True, sets=()).font.getBestCmap()
    assert 0x0410 not in cmap


def test_composed_glyphs_are_ordinary_glyphs() -> None:
    glyphs = parse_mcm(Path("original_fonts/clarity.mcm"))
    made = composed_glyphs(glyphs, ("cyrillic",))
    assert all(isinstance(g, Glyph) for g in made.values())
    assert not any(g.is_blank for g in made.values())


def test_generated_stems_follow_a_slanted_font() -> None:
    """betaflight is the one italic face; upright stems would look pasted on."""
    latin = latin_of(Path("original_fonts/betaflight.mcm"))
    geometry = Geometry(latin)
    assert geometry.slant > 0, "betaflight is slanted"
    stem = geometry.stem(geometry.left)
    at_top = min(x for x, y in stem if y == geometry.top)
    at_bottom = min(x for x, y in stem if y == geometry.bottom)
    assert at_top - at_bottom == geometry.slant


def test_upright_fonts_get_upright_stems() -> None:
    for path in font_paths():
        if path.stem == "betaflight":
            continue
        assert Geometry(latin_of(path)).slant == 0, path.stem


@pytest.mark.parametrize("path", font_paths(), ids=lambda p: p.stem)
def test_letters_are_all_distinct(path: Path) -> None:
    """Ъ/Ь, Щ/Ш, Ц/П differ by one detail a tight cell used to drop silently."""
    made = compose(latin_of(path))
    seen: dict[frozenset[tuple[int, int]], str] = {}
    for letter, core in made.items():
        key = frozenset(core)
        assert key not in seen, f"{letter} is identical to {seen.get(key)}"
        seen[key] = letter


@pytest.mark.parametrize("path", font_paths(), ids=lambda p: p.stem)
@pytest.mark.parametrize(("cyr", "lat"), list(cyrillic.MIRRORED.items()))
def test_mirrored_letters_are_actually_reversed(path: Path, cyr: str, lat: str) -> None:
    """И and Я must not come out as N and R.

    Re-aligning rows to their old left edge once cancelled the mirror on narrow
    rows, quietly leaving Я identical to R.
    """
    latin = latin_of(path)
    source = core_of(latin[lat])
    made = compose(latin)[cyr]
    if source == mirror(source):
        assert made == source, f"{lat} reads the same backwards; {cyr} should match"
    else:
        assert made != source, f"{cyr} came out identical to {lat}"


def test_mirrored_letters_keep_the_slant() -> None:
    """A plain mirror tips an italic face the wrong way; betaflight is italic."""
    latin = latin_of(Path("original_fonts/betaflight.mcm"))
    g = Geometry(latin)
    assert g.slant > 0
    for cyr in cyrillic.MIRRORED:
        made = compose(latin)[cyr]
        rows = sorted({y for _, y in made})
        at_top = min(x for x, y in made if y == rows[0])
        at_bottom = min(x for x, y in made if y == rows[-1])
        assert at_top > at_bottom, f"{cyr} leans the wrong way"


@pytest.mark.parametrize("path", font_paths(), ids=lambda p: p.stem)
def test_slant_is_measured_not_modelled(path: Path) -> None:
    """The slant is a staircase; a straight-line fit rounds strokes apart."""
    g = Geometry(latin_of(path))
    assert g.at(g.top) - g.at(g.bottom) == g.slant
    assert all(g.at(y) >= g.at(y + 1) for y in range(g.top, g.bottom))


def components(cells: set[tuple[int, int]]) -> int:
    """How many separate strokes a shape is made of, counting diagonals."""
    seen: set[tuple[int, int]] = set()
    found = 0
    for cell in cells:
        if cell in seen:
            continue
        found += 1
        stack = [cell]
        while stack:
            x, y = stack.pop()
            if (x, y) in seen or (x, y) not in cells:
                continue
            seen.add((x, y))
            stack += [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
    return found


@pytest.mark.parametrize("path", font_paths(), ids=lambda p: p.stem)
def test_letters_are_drawn_in_one_stroke(path: Path) -> None:
    """A letter's body must hang together, i.e. its parts actually meet.

    Ч lost its right stem to E's short middle arm; Я tore in half when a
    mirrored glyph was sheared back upright.
    """
    latin = latin_of(path)
    geometry = Geometry(latin)
    for letter, core in compose(latin).items():
        # Marks above the cap line (Ё Ї Й) stand apart on purpose, and Ы is two
        # strokes by design.
        body = {c for c in core if c[1] >= geometry.top}
        allowed = (1, 2) if letter == "Ы" else (1,)
        assert components(body) in allowed, f"{letter} is in {components(body)} pieces"
