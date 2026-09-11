"""Geometric shapes, box drawing and shade blocks.

Overlays get built out of rules and markers as much as out of letters, and the
OSD fonts have none. Box drawing runs edge to edge so a frame joins up across
cells; the shapes sit on the same maths axis as + and =, so a bullet list or a
row of markers lines up with the text beside it.
"""

from __future__ import annotations

from .shapes import (
    CHAR_H,
    CHAR_W,
    SAFE_X,
    Core,
    Geometry,
    Pixels,
    box,
    clip,
    line,
    render,
    ring,
    triangle,
)

NAMES = {
    0x2500: "box drawings light horizontal",
    0x2502: "box drawings light vertical",
    0x250C: "box drawings light down and right",
    0x2510: "box drawings light down and left",
    0x2514: "box drawings light up and right",
    0x2518: "box drawings light up and left",
    0x251C: "box drawings light vertical and right",
    0x2524: "box drawings light vertical and left",
    0x252C: "box drawings light down and horizontal",
    0x2534: "box drawings light up and horizontal",
    0x253C: "box drawings light vertical and horizontal",
    0x2550: "box drawings double horizontal",
    0x2551: "box drawings double vertical",
    0x2554: "box drawings double down and right",
    0x2557: "box drawings double down and left",
    0x255A: "box drawings double up and right",
    0x255D: "box drawings double up and left",
    0x2560: "box drawings double vertical and right",
    0x2563: "box drawings double vertical and left",
    0x2566: "box drawings double down and horizontal",
    0x2569: "box drawings double up and horizontal",
    0x256C: "box drawings double vertical and horizontal",
    0x2580: "upper half block",
    0x2584: "lower half block",
    0x2588: "full block",
    0x258C: "left half block",
    0x2590: "right half block",
    0x2591: "light shade",
    0x2592: "medium shade",
    0x2593: "dark shade",
    0x25A0: "black square",
    0x25A1: "white square",
    0x25B2: "black up-pointing triangle",
    0x25B6: "black right-pointing triangle",
    0x25BC: "black down-pointing triangle",
    0x25C0: "black left-pointing triangle",
    0x25C6: "black diamond",
    0x25C7: "white diamond",
    0x25CB: "white circle",
    0x25CF: "black circle",
    0x2605: "black star",
    0x2606: "white star",
    0x2713: "check mark",
    0x2717: "ballot x",
}

# A five pointed star does not fall out of a rule, so it is drawn once and
# reused; a marker carries no stroke weight to inherit anyway.
STAR = [
    "....#....",
    "....#....",
    "...###...",
    "#########",
    ".#######.",
    "..#####..",
    "..##.##..",
    ".##...##.",
    "##.....##",
]


def _pattern(rows: list[str], x: int, y: int) -> Core:
    return {
        (x + col, y + row)
        for row, text in enumerate(rows)
        for col, mark in enumerate(text)
        if mark == "#"
    }


def _erode(core: Core) -> Core:
    """Cells with a neighbour missing -- the rim of a solid shape."""
    return {
        cell
        for cell in core
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
        if (cell[0] + dx, cell[1] + dy) not in core
    }


def _rounded(core: Core, x0: int, x1: int, y0: int, y1: int) -> Core:
    return core - {(x, y) for x in (x0, x1) for y in (y0, y1)}


def _rules(g: Geometry) -> dict[int, Core]:
    """Box drawing: full-cell runs, so a frame joins across cells."""
    w = g.weight
    cx, cy = (CHAR_W - w) // 2, (CHAR_H - w) // 2
    thin = max(1, w - 1)
    gap = max(2, w)
    left, right = cx - (gap + thin) // 2, cx + (gap + thin + 1) // 2
    upper, lower = cy - (gap + thin) // 2, cy + (gap + thin + 1) // 2

    def v(x: int, y0: int, y1: int, weight: int) -> Core:
        return box(x, x + weight - 1, y0, y1)

    def h(y: int, x0: int, x1: int, weight: int) -> Core:
        return box(x0, x1, y, y + weight - 1)

    def single(arms: str) -> Core:
        out: Core = set()
        if "n" in arms:
            out |= v(cx, 0, cy + w - 1, w)
        if "s" in arms:
            out |= v(cx, cy, CHAR_H - 1, w)
        if "w" in arms:
            out |= h(cy, 0, cx + w - 1, w)
        if "e" in arms:
            out |= h(cy, cx, CHAR_W - 1, w)
        return out

    def double(arms: str) -> Core:
        """Two parallel runs per arm; each wall stops where another crosses."""
        out: Core = set()
        vertical, horizontal = "n" in arms or "s" in arms, "e" in arms or "w" in arms
        for x, side in ((left, "w"), (right, "e")):
            if not vertical:
                continue
            top_end = CHAR_H - 1 if "s" in arms else lower + thin - 1
            bottom_start = 0 if "n" in arms else upper
            # The wall on the far side of a tee runs straight through.
            through = side not in arms and horizontal
            if "n" in arms:
                out |= v(x, 0, upper + thin - 1 if not through else top_end, thin)
            if "s" in arms:
                out |= v(x, lower if not through else bottom_start, CHAR_H - 1, thin)
            if not horizontal:
                out |= v(x, 0, CHAR_H - 1, thin)
        for y, side in ((upper, "n"), (lower, "s")):
            if not horizontal:
                continue
            through = side not in arms and vertical
            if "w" in arms:
                far = right + thin - 1 if through else left + thin - 1
                out |= h(y, 0, far, thin)
            if "e" in arms:
                out |= h(y, right if not through else left, CHAR_W - 1, thin)
            if not vertical:
                out |= h(y, 0, CHAR_W - 1, thin)
        return out

    return {
        0x2500: single("ew"),
        0x2502: single("ns"),
        0x250C: single("se"),
        0x2510: single("sw"),
        0x2514: single("ne"),
        0x2518: single("nw"),
        0x251C: single("nse"),
        0x2524: single("nsw"),
        0x252C: single("sew"),
        0x2534: single("new"),
        0x253C: single("nsew"),
        0x2550: double("ew"),
        0x2551: double("ns"),
        0x2554: double("se"),
        0x2557: double("sw"),
        0x255A: double("ne"),
        0x255D: double("nw"),
        0x2560: double("nse"),
        0x2563: double("nsw"),
        0x2566: double("sew"),
        0x2569: double("new"),
        0x256C: double("nsew"),
    }


def _fills() -> dict[int, Core]:
    """Half blocks and shades, drawn to the cell edge so they tile."""
    full = box(0, CHAR_W - 1, 0, CHAR_H - 1)
    return {
        0x2588: full,
        0x2580: box(0, CHAR_W - 1, 0, CHAR_H // 2 - 1),
        0x2584: box(0, CHAR_W - 1, CHAR_H // 2, CHAR_H - 1),
        0x258C: box(0, CHAR_W // 2 - 1, 0, CHAR_H - 1),
        0x2590: box(CHAR_W // 2, CHAR_W - 1, 0, CHAR_H - 1),
        0x2591: {c for c in full if c[0] % 2 == 0 and c[1] % 2 == 0},
        0x2592: {c for c in full if (c[0] + c[1]) % 2 == 0},
        0x2593: {c for c in full if not (c[0] % 2 and c[1] % 2)},
    }


def _markers(g: Geometry) -> dict[int, Core]:
    """Squares, triangles, circles and ticks, centred on the maths axis."""
    w = g.weight
    middle = (g.top + g.bottom) // 2
    side = min(SAFE_X[1] - SAFE_X[0] + 1, g.bottom - g.top + 1)
    side -= 1 - side % 2  # an odd side has a centre column to point from
    x0 = (CHAR_W - side) // 2
    x1, y0, y1 = x0 + side - 1, middle - side // 2, middle + side // 2
    solid = box(x0, x1, y0, y1)
    diamond = {
        (x, y)
        for x in range(x0, x1 + 1)
        for y in range(y0, y1 + 1)
        if abs(x - (x0 + x1) // 2) + abs(y - middle) <= side // 2
    }
    star = _pattern(STAR, (CHAR_W - len(STAR[0])) // 2, middle - len(STAR) // 2)
    tick = line((x0, middle), (x0 + side // 3, y1), w) | line(
        (x0 + side // 3, y1), (x1, y0), w
    )
    return {
        0x25A0: solid,
        0x25A1: ring(x0, x1, y0, y1, w),
        0x25CF: _rounded(solid, x0, x1, y0, y1),
        0x25CB: _rounded(ring(x0, x1, y0, y1, w), x0, x1, y0, y1)
        | {(x, y) for x in (x0 + w, x1 - w) for y in (y0 + w, y1 - w)},
        0x25C6: diamond,
        0x25C7: diamond - {c for c in diamond if c not in _erode(diamond)},
        0x25B2: triangle(x0, x1, y0, y1, "up"),
        0x25BC: triangle(x0, x1, y0, y1, "down"),
        0x25C0: triangle(x0, x1, y0, y1, "left"),
        0x25B6: triangle(x0, x1, y0, y1, "right"),
        0x2605: star,
        0x2606: _erode(star),
        0x2713: tick,
        0x2717: line((x0, y0), (x1, y1), w) | line((x0, y1), (x1, y0), w),
    }


def cores(latin: dict[str, Pixels]) -> dict[int, Core]:
    """Codepoint -> white core."""
    g = Geometry(latin)
    out = {**_rules(g), **_fills(), **_markers(g)}
    return {cp: clip(core) for cp, core in out.items()}


def glyphs(latin: dict[str, Pixels]) -> dict[int, Pixels]:
    """Codepoint -> pixels, ready to hand to the font builder."""
    return {cp: render(core) for cp, core in cores(latin).items()}
