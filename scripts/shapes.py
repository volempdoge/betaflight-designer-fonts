"""Pixel primitives shared by every composed glyph set.

The .mcm fonts are bitmaps: a white core wrapped in a black outline. Everything
this project draws -- Cyrillic capitals, accented Latin, punctuation, blocks --
is built the same way. Define the white core in cell coordinates, hand it to
`render()`, and the outline follows.

`Geometry` measures one font's own stroke weight, stem columns, bar rows and
slant off its Latin capitals, so a new glyph inherits the face it belongs to
instead of a shape invented here.
"""

from __future__ import annotations

from collections.abc import Iterable

CHAR_W, CHAR_H = 12, 18

Cell = tuple[int, int]  # (x, row), row 0 at the top
Pixels = list[list[int]]  # 0 black, 1 transparent, 2 white
Core = set[Cell]

BLACK, TRANSPARENT, WHITE = 0, 1, 2


def inside(cell: Cell) -> bool:
    return 0 <= cell[0] < CHAR_W and 0 <= cell[1] < CHAR_H


def outline(core: Core) -> Core:
    ring = {
        (x + dx, y + dy)
        for x, y in core
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
        if inside((x + dx, y + dy))
    }
    for x, y in core:
        for dx in (-1, 1):
            for dy in (-1, 1):
                corner = (x + dx, y + dy)
                square = all(c not in core for c in ((x + dx, y), (x, y + dy), corner))
                # A chamfer steps diagonally; a stroke terminal does not.
                terminal = (x + dx, y - dy) not in core and (x - dx, y + dy) not in core
                if inside(corner) and square and terminal:
                    ring.add(corner)
    return ring - core


def render(core: Core) -> Pixels:
    black = outline(core)
    return [
        [
            WHITE if (x, y) in core else BLACK if (x, y) in black else TRANSPARENT
            for x in range(CHAR_W)
        ]
        for y in range(CHAR_H)
    ]


def core_of(px: Pixels, value: int = WHITE) -> Core:
    return {(x, y) for y, row in enumerate(px) for x, v in enumerate(row) if v == value}


def mirror(core: Core) -> Core:
    lo, hi = min(x for x, _ in core), max(x for x, _ in core)
    return {(lo + hi - x, y) for x, y in core}


def shift(core: Core, dx: int = 0, dy: int = 0) -> Core:
    return {(x + dx, y + dy) for x, y in core}


SAFE_X = (1, CHAR_W - 2)
SAFE_Y = (1, CHAR_H - 2)


def splay(core: Core, gap: int) -> Core:
    """Push the halves of a glyph apart, keeping crossing runs joined.

    For a centre stem inside a Latin shape too narrow to take one (Ф, Ж).
    """
    lo, hi = min(x for x, _ in core), max(x for x, _ in core)
    gap = min(gap, lo - SAFE_X[0], SAFE_X[1] - hi)
    if gap <= 0:
        return core
    mid = (lo + hi + 1) / 2
    out: Core = set()
    for y in {y for _, y in core}:
        xs = [x for x, yy in core if yy == y]
        out |= {(x - gap if x < mid else x + gap, y) for x in xs}
        for run in runs(xs):
            if run[0] < mid <= run[-1]:
                out |= {(x, y) for x in range(run[0] - gap, run[-1] + gap + 1)}
    return out


def mirror_rows(core: Core, g: Geometry) -> Core:
    """Flip a letter left to right, then put the font's own slant back.

    A plain mirror reverses the slant; undoing that row by row from the measured
    slant avoids the rounding damage straightening would cause.
    """
    lo, hi = min(x for x, _ in core), max(x for x, _ in core)
    flipped = {(lo + hi - x, y) for x, y in core}
    if not g.slant:
        return flipped
    return {(x + 2 * g.at(y) - g.slant, y) for x, y in flipped}


def interior_stem(core: Core, weight: int) -> Core:
    """A stem down the middle of a shape, taken row by row.

    So the stem inside Ф and Ж follows the host's slant with no model of it.
    """
    stem: Core = set()
    for y in {y for _, y in core}:
        parts = runs([x for x, yy in core if yy == y])
        lo, hi = (
            (parts[0][-1] + 1, parts[-1][0] - 1)
            if len(parts) >= 2
            else (parts[0][0], parts[0][-1])
        )
        start = (lo + hi + 1 - weight) // 2
        stem |= {(start + i, y) for i in range(weight)}
    return stem


def needed_splay(core: Core, weight: int) -> int:
    """How far to open a shape so a stem of `weight` fits with a gap each side."""
    worst = 0
    for y in {y for _, y in core}:
        parts = runs([x for x, yy in core if yy == y])
        if len(parts) >= 2:
            gap = parts[-1][0] - parts[0][-1] - 1
            worst = max(worst, -(-(weight + 2 - gap) // 2))
    return max(0, worst)


def runs(xs: Iterable[int]) -> list[list[int]]:
    out: list[list[int]] = []
    for x in sorted(xs):
        if out and x == out[-1][-1] + 1:
            out[-1].append(x)
        else:
            out.append([x])
    return out


class Geometry:
    """Stroke weight, stem columns and bar rows, measured off a font itself."""

    def __init__(self, latin: dict[str, Pixels]) -> None:
        self.latin = latin
        h = self.core("H")
        self.top = min(y for _, y in h)
        self.bottom = max(y for _, y in h)
        stems = runs({x for x, y in h if y == self.bottom})
        self.left, self.right = stems[0], stems[-1]
        self.weight = len(self.left)
        e = self.core("E")
        rows = sorted({y for _, y in e})
        width = {y: sum(1 for _, yy in e if yy == y) for y in rows}
        bars = [y for y in rows if width[y] > self.weight + 1]
        self.top_bar = [y for y in bars if y <= self.top + 2]
        self.bottom_bar = [y for y in bars if y >= self.bottom - 2]
        self.mid_bar = [y for y in bars if y not in self.top_bar + self.bottom_bar]
        self.middle = self.mid_bar or [(self.top + self.bottom) // 2]
        # Three-stem letters (Ж Ш Щ Ю Ы) need a box holding 3 stems and 2 gaps.
        lead = {y: min(x for x, yy in h if yy == y) for y in {y for _, y in h}}
        self.slant = lead[self.top] - lead[self.bottom]
        self.step = {y: lead[y] - lead[self.bottom] for y in lead}
        need = 3 * self.weight + 2
        box = max(need, self.right[-1] - self.left[0] + 1)
        box = min(box, CHAR_W - 2 - abs(self.slant))
        x0 = max(1, (CHAR_W - box - self.slant) // 2)
        self.wide_left = list(range(x0, x0 + self.weight))
        self.wide_right = list(range(x0 + box - self.weight, x0 + box))
        inner = (self.wide_left[-1] + self.wide_right[0] + 1) // 2
        self.centre = list(
            range(inner - self.weight // 2, inner - self.weight // 2 + self.weight)
        )

    def core(self, ch: str) -> Core:
        return core_of(self.latin[ch])

    def rows(self, ch: str, ys: list[int]) -> Core:
        return {(x, y) for x, y in self.core(ch) if y in ys}

    def cols(self, ch: str, xs: list[int]) -> Core:
        return {(x, y) for x, y in self.core(ch) if x in xs}

    def at(self, y: int) -> int:
        """The measured slant offset on row `y`, clamped to the cap box."""
        return self.step[min(max(y, self.top), self.bottom)]

    def lean(self, y: int) -> int:
        """How far a stem has shifted at row `y`, for a slanted font."""
        if not self.slant:
            return 0
        span = max(1, self.bottom - self.top)
        return round(
            self.slant * (self.bottom - min(max(y, self.top), self.bottom)) / span
        )

    def stem(
        self, xs: list[int], top: int | None = None, bottom: int | None = None
    ) -> Core:
        lo = self.top if top is None else top
        hi = self.bottom if bottom is None else bottom
        return {(x + self.lean(y), y) for x in xs for y in range(lo, hi + 1)}

    def bar(self, which: str, x0: int | None = None, x1: int | None = None) -> Core:
        ys = {"top": self.top_bar, "mid": self.middle, "bottom": self.bottom_bar}[which]
        if x0 is None and x1 is None:
            return self.rows("E", ys)
        lo = self.left[0] if x0 is None else x0
        hi = self.right[-1] if x1 is None else x1
        return {(x, y) for x in range(lo, hi + 1) for y in ys}

    def marks(self, xs: list[int]) -> Core:
        """Dots or ticks sitting above the cap line."""
        return {
            (x + self.lean(self.top), y)
            for x in xs
            for y in range(self.top - 2, self.top)
        }


def slope(latin: dict[str, Pixels], sign: int) -> dict[str, Pixels]:
    """Straighten a slanted font, or lean an upright one back over.

    Parts lifted from several letters meet at the wrong offsets in a slanted
    face, so composition happens upright and the result is leant back after.
    """
    g = Geometry(latin)
    if not g.slant:
        return latin
    out: dict[str, Pixels] = {}
    for ch, px in latin.items():
        rows: Pixels = [[TRANSPARENT] * CHAR_W for _ in range(CHAR_H)]
        for y, row in enumerate(px):
            shift_by = sign * (g.slant - g.lean(y))
            for x, v in enumerate(row):
                if v != TRANSPARENT and 0 <= x + shift_by < CHAR_W:
                    rows[y][x + shift_by] = v
        out[ch] = rows
    return out


def lean_core(core: Core, g: Geometry) -> Core:
    """Put the slant back on a core composed upright, keeping it in the cell."""
    if not g.slant:
        return core
    leaned = {(x - (g.slant - g.lean(y)), y) for x, y in core}
    lo, hi = min(x for x, _ in leaned), max(x for x, _ in leaned)
    nudge = max(0, SAFE_X[0] - lo) - max(0, hi - SAFE_X[1])
    return {(x + nudge, y) for x, y in leaned}


# --- drawing primitives ------------------------------------------------------
#
# Punctuation, blocks and accents are not in the source fonts, so they are drawn
# rather than borrowed. Sizes always come from `Geometry`, never from constants
# here, so a heavy face gets heavy punctuation.


def clip(core: Core) -> Core:
    return {cell for cell in core if inside(cell)}


def bounds(core: Core) -> tuple[int, int, int, int]:
    """(x0, x1, y0, y1), inclusive."""
    xs = [x for x, _ in core]
    ys = [y for _, y in core]
    return min(xs), max(xs), min(ys), max(ys)


def box(x0: int, x1: int, y0: int, y1: int) -> Core:
    return {(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)}


def ring(x0: int, x1: int, y0: int, y1: int, weight: int = 1) -> Core:
    """A hollow rectangle: the counter is what makes it read as a ring."""
    inner = box(x0 + weight, x1 - weight, y0 + weight, y1 - weight)
    return box(x0, x1, y0, y1) - inner


def flip_y(core: Core) -> Core:
    lo, hi = min(y for _, y in core), max(y for _, y in core)
    return {(x, lo + hi - y) for x, y in core}


def rotate(core: Core) -> Core:
    """Half a turn -- a comma becomes an opening quote."""
    return flip_y(mirror(core))


def place(core: Core, x: int | None = None, y: int | None = None) -> Core:
    """Move a shape so its top left corner lands where asked."""
    x0, _, y0, _ = bounds(core)
    return shift(core, 0 if x is None else x - x0, 0 if y is None else y - y0)


def fit_x(core: Core, lo: int = SAFE_X[0], hi: int = SAFE_X[1]) -> Core:
    """Nudge a shape sideways until it is back inside the safe box."""
    x0, x1, _, _ = bounds(core)
    return shift(core, max(0, lo - x0) - max(0, x1 - hi))


def centre_x(core: Core, lo: int = SAFE_X[0], hi: int = SAFE_X[1]) -> Core:
    x0, x1, _, _ = bounds(core)
    return shift(core, (lo + hi - x0 - x1) // 2)


def line(start: Cell, end: Cell, weight: int = 1) -> Core:
    """A straight run of cells, `weight` wide across the shallower axis."""
    (x0, y0), (x1, y1) = start, end
    steps = max(abs(x1 - x0), abs(y1 - y0))
    out: Core = set()
    for i in range(steps + 1):
        t = i / steps if steps else 0
        x = round(x0 + (x1 - x0) * t)
        y = round(y0 + (y1 - y0) * t)
        if abs(y1 - y0) > abs(x1 - x0):
            out |= {(x + k, y) for k in range(weight)}
        else:
            out |= {(x, y + k) for k in range(weight)}
    return out


def chevron(x0: int, x1: int, y0: int, y1: int, weight: int, point: str) -> Core:
    """A > or v, drawn as two runs meeting at the apex."""
    if point in ("left", "right"):
        apex = x0 if point == "left" else x1
        back = x1 if point == "left" else x0
        mid = (y0 + y1) // 2
        return line((back, y0), (apex, mid), weight) | line(
            (apex, mid), (back, y1), weight
        )
    apex = y0 if point == "up" else y1
    back = y1 if point == "up" else y0
    mid = (x0 + x1) // 2
    return line((x0, back), (mid, apex), weight) | line((mid, apex), (x1, back), weight)


def triangle(x0: int, x1: int, y0: int, y1: int, point: str) -> Core:
    """A solid arrowhead filling the given box."""
    out: Core = set()
    if point in ("up", "down"):
        rows = list(range(y0, y1 + 1))
        for i, y in enumerate(rows if point == "up" else rows[::-1]):
            grow = i / max(1, len(rows) - 1)
            half = round(grow * (x1 - x0) / 2)
            mid = (x0 + x1) // 2
            out |= {(x, y) for x in range(mid - half, mid + half + 1 + (x1 - x0) % 2)}
        return out
    cols = list(range(x0, x1 + 1))
    for i, x in enumerate(cols if point == "left" else cols[::-1]):
        grow = i / max(1, len(cols) - 1)
        half = round(grow * (y1 - y0) / 2)
        mid = (y0 + y1) // 2
        out |= {(x, y) for y in range(mid - half, mid + half + 1 + (y1 - y0) % 2)}
    return out


def wave(x0: int, x1: int, y: int, weight: int = 1) -> Core:
    """A tilde: up on the left, down on the right."""
    mid = (x0 + x1) // 2
    return (
        line((x0, y), (x0 + (mid - x0) // 2, y - 1), weight)
        | line((x0 + (mid - x0) // 2, y - 1), (mid + (x1 - mid) // 2, y + 1), weight)
        | line((mid + (x1 - mid) // 2, y + 1), (x1, y), weight)
    )
