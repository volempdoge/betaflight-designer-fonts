"""Reading the MAX7456 .mcm character memory."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from conftest import font_paths

from bf2font import BYTES_PER_CHAR, CHAR_H, CHAR_W, CHARS, Glyph, parse_mcm


@pytest.mark.parametrize("path", font_paths(), ids=lambda p: p.stem)
def test_every_bundled_font_parses(path: Path) -> None:
    glyphs = parse_mcm(path)
    assert len(glyphs) == CHARS
    assert [g.index for g in glyphs] == list(range(CHARS))
    for glyph in glyphs:
        assert len(glyph.pixels) == CHAR_H
        assert all(len(row) == CHAR_W for row in glyph.pixels)
        assert all(0 <= v <= 3 for row in glyph.pixels for v in row)


def test_known_glyphs(default_glyphs: list[Glyph]) -> None:
    assert default_glyphs[0x20].is_blank, "0x20 is the space"
    assert not default_glyphs[0x41].is_blank, "0x41 is A"
    # A is drawn as white pixels surrounded by a black outline.
    assert default_glyphs[0x41].cells(value=2)
    assert default_glyphs[0x41].cells(value=0)


def test_ink_is_black_plus_white(default_glyphs: list[Glyph]) -> None:
    glyph = default_glyphs[0x41]
    assert glyph.ink() == glyph.cells(value=0) | glyph.cells(value=2)
    assert not glyph.cells(value=0) & glyph.cells(value=2)


def test_padding_is_ignored(tmp_path: Path) -> None:
    """Only the first 54 bytes of each character carry pixels."""
    source = font_paths()[0]
    lines = source.read_text().splitlines()
    mangled = list(lines)
    for index in range(CHARS):
        start = 1 + index * BYTES_PER_CHAR + 54
        for offset in range(10):
            mangled[start + offset] = "11111111"
    path = tmp_path / "mangled.mcm"
    path.write_text("\n".join(mangled))
    assert parse_mcm(path) == parse_mcm(source)


@pytest.mark.parametrize(
    ("mangle", "message"),
    [
        (lambda lines: ["NOTAFONT", *lines[1:]], "MAX7456"),
        (lambda lines: lines[:-1], "data lines"),
        (lambda lines: [*lines[:-1], "0000000x"], "binary digits"),
    ],
)
def test_rejects_broken_files(
    tmp_path: Path, mangle: Callable[[list[str]], list[str]], message: str
) -> None:
    lines = font_paths()[0].read_text().splitlines()
    path = tmp_path / "broken.mcm"
    path.write_text("\n".join(mangle(lines)))
    with pytest.raises(ValueError, match=message):
        parse_mcm(path)
