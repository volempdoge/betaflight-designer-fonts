"""Vectorising pixels into contours."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import font_paths, rasterise

from bf2font import (
    CHAR_H,
    DESCENT,
    PX,
    Glyph,
    parse_mcm,
    to_font_units,
    trace_contours,
)


def test_single_cell_is_a_square() -> None:
    contours = trace_contours({(3, 4)})
    assert len(contours) == 1
    assert set(contours[0]) == {(3, 4), (4, 4), (4, 5), (3, 5)}


def test_ring_has_an_outer_contour_and_a_hole() -> None:
    ring = {(x, y) for x in range(3) for y in range(3)} - {(1, 1)}
    contours = trace_contours(ring)
    assert len(contours) == 2
    assert rasterise(contours) == ring, "the hole must stay unfilled"


def test_diagonal_touch_yields_two_contours() -> None:
    """Two cells meeting at a corner must not be traced as one crossing loop."""
    contours = trace_contours({(0, 0), (1, 1)})
    assert len(contours) == 2
    assert rasterise(contours) == {(0, 0), (1, 1)}


def test_collinear_points_are_dropped() -> None:
    contours = trace_contours({(0, 0), (1, 0), (2, 0)})
    assert len(contours) == 1
    assert len(contours[0]) == 4, "a 3x1 bar is a rectangle, not six points"


def test_empty_input() -> None:
    assert trace_contours(set()) == []


@pytest.mark.parametrize("path", font_paths(), ids=lambda p: p.stem)
def test_outlines_rasterise_back_to_the_source_pixels(path: Path) -> None:
    """Both layers of all 256 characters must round-trip exactly."""
    for glyph in parse_mcm(path):
        for cells in (glyph.ink(), glyph.cells(value=2)):
            assert rasterise(trace_contours(cells)) == cells


def test_outer_contours_wind_counter_clockwise() -> None:
    """PostScript convention: positive area for the outer contour."""
    (contour,) = trace_contours({(0, 0), (1, 0), (0, 1), (1, 1)})
    area = sum(
        x1 * y2 - x2 * y1
        for (x1, y1), (x2, y2) in zip(contour, contour[1:] + contour[:1], strict=True)
    )
    assert area > 0


def test_font_units_place_the_cell_on_the_baseline(default_glyphs: list[Glyph]) -> None:
    contours = to_font_units(trace_contours(default_glyphs[0x41].ink()))
    ys = [y for contour in contours for _, y in contour]
    assert min(ys) >= -DESCENT
    assert max(ys) <= CHAR_H * PX - DESCENT
