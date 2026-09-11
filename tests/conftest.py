"""Shared fixtures and the reference rasteriser used to check outlines."""

from __future__ import annotations

from pathlib import Path

import pytest

from bf2font import CHAR_H, CHAR_W, Glyph, parse_mcm

FONT_DIR = Path(__file__).resolve().parent.parent / "original_fonts"
Contour = list[tuple[int, int]]


def font_paths() -> list[Path]:
    return sorted(FONT_DIR.glob("*.mcm"))


@pytest.fixture(scope="session")
def default_glyphs() -> list[Glyph]:
    return parse_mcm(FONT_DIR / "default.mcm")


def winding(contours: list[Contour], px: float, py: float) -> int:
    """Winding number of `contours` around a point, for the non-zero fill rule."""
    total = 0
    for contour in contours:
        n = len(contour)
        for i in range(n):
            x1, y1 = contour[i]
            x2, y2 = contour[(i + 1) % n]
            side = (x2 - x1) * (py - y1) - (px - x1) * (y2 - y1)
            if y1 <= py < y2 and side > 0:
                total += 1
            elif y2 <= py < y1 and side < 0:
                total -= 1
    return total


def rasterise(contours: list[Contour]) -> set[tuple[int, int]]:
    """Fill `contours` back into the grid cells they cover."""
    return {
        (x, y)
        for x in range(CHAR_W)
        for y in range(CHAR_H)
        if winding(contours, x + 0.5, y + 0.5) != 0
    }
