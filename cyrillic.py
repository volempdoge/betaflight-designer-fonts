"""Cyrillic capitals drawn in the Betaflight OSD idiom.

A glyph is a white core wrapped in a black outline that, across all ten bundled
fonts, sits between the 4- and 8-neighbour dilation of the core. `outline()`
reproduces that, so a new letter only has to define its white core.
"""

from __future__ import annotations

from collections.abc import Iterable

CHAR_W, CHAR_H = 12, 18

Cell = tuple[int, int]  # (x, row), row 0 at the top
Pixels = list[list[int]]  # 0 black, 1 transparent, 2 white
Core = set[Cell]

BLACK, TRANSPARENT, WHITE = 0, 1, 2

# Codepoint -> the letter's key in the composed set.
UPPERCASE = {
    0x0410: "А",
    0x0411: "Б",
    0x0412: "В",
    0x0413: "Г",
    0x0414: "Д",
    0x0415: "Е",
    0x0416: "Ж",
    0x0417: "З",
    0x0418: "И",
    0x0419: "Й",
    0x041A: "К",
    0x041B: "Л",
    0x041C: "М",
    0x041D: "Н",
    0x041E: "О",
    0x041F: "П",
    0x0420: "Р",
    0x0421: "С",
    0x0422: "Т",
    0x0423: "У",
    0x0424: "Ф",
    0x0425: "Х",
    0x0426: "Ц",
    0x0427: "Ч",
    0x0428: "Ш",
    0x0429: "Щ",
    0x042A: "Ъ",
    0x042B: "Ы",
    0x042C: "Ь",
    0x042D: "Э",
    0x042E: "Ю",
    0x042F: "Я",
    0x0401: "Ё",
    0x0404: "Є",
    0x0406: "І",
    0x0407: "Ї",
    0x0490: "Ґ",
}
# Lowercase codepoint -> its capital, since the fonts have no lowercase.
LOWERCASE = {cp + 0x20: cp for cp in range(0x0410, 0x0430)}
LOWERCASE.update(
    {0x0451: 0x0401, 0x0454: 0x0404, 0x0456: 0x0406, 0x0457: 0x0407, 0x0491: 0x0490}
)

UKRAINIAN = "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ"

# Letters whose Betaflight Latin glyph already is the Cyrillic shape.
SAME_AS_LATIN = {
    "А": "A",
    "В": "B",
    "Е": "E",
    "І": "I",
    "К": "K",
    "М": "M",
    "Н": "H",
    "О": "O",
    "Р": "P",
    "С": "C",
    "Т": "T",
    "Х": "X",
    "У": "Y",
    "З": "3",
}
# Letters that are a Latin glyph flipped left to right.
MIRRORED = {"И": "N", "Я": "R"}


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


def phi(bowl: Core, weight: int) -> Core:
    """Ф: a bowl with a stem through it, poking out above and below."""
    spread = splay(bowl, needed_splay(bowl, weight))
    stem = interior_stem(spread, weight)
    top, bottom = min(y for _, y in stem), max(y for _, y in stem)
    out = spread | stem
    for row, beyond in ((top, top - 1), (bottom, bottom + 1)):
        if SAFE_Y[0] <= beyond <= SAFE_Y[1]:
            out |= {(x, beyond) for x, y in stem if y == row}
    return out


def breve(core: Core, g: Geometry) -> Core:
    """Й: И with the mark above it, sitting over the letter's own top row."""
    top = min(y for _, y in core)
    row = [x for x, y in core if y == top]
    lo, hi = min(row) + g.weight, max(row) - g.weight + 1
    return {(x, top - 1) for x in range(lo, hi)} | {(x, top - 2) for x in (lo, hi - 1)}


def ya(g: Geometry) -> Core:
    """Я drawn from bars and stems rather than mirrored from R.

    A mirror leans the wrong way, and the double shear that puts the lean back
    tears the bowl off the leg at whole-pixel steps -- so slanted faces use this.
    """
    w = g.weight
    waist = max(g.middle)
    # One knee, as in Л and Д: a straight run to the baseline reads too steep.
    knee = (waist + g.bottom + 1) // 2
    leg = {(x + w, y) for x, y in g.stem(g.left, waist + 1, knee)} | g.stem(
        g.left, knee + 1, g.bottom
    )
    return (
        g.bar("top", g.left[0], g.right[-1])
        | g.bar("mid", g.left[0], g.right[-1])
        | g.stem(g.left, g.top, waist)
        | g.stem(g.right)
        | leg
    )


def compose(
    latin: dict[str, Pixels], reserve: int = 0, slanted: bool = False
) -> dict[str, Core]:
    """Every supported capital, as a white core, in this font's idiom.

    `reserve` is how many columns the widest letters leave free, so a slanted
    font still has room once the composed glyph is leant back.
    """
    original = Geometry(latin)
    if original.slant:
        upright = compose(slope(latin, +1), reserve=abs(original.slant), slanted=True)
        leant = {ch: lean_core(core, original) for ch, core in upright.items()}
        # Built on the unstraightened font: these follow their source glyph's
        # own rows, which straightening would round apart.
        leant["И"] = mirror_rows(core_of(latin["N"]), original)
        leant["Й"] = leant["И"] | breve(leant["И"], original)
        leant["Ф"] = phi(core_of(latin["O"]), original.weight)
        return leant
    g = original
    w, top, bottom = g.weight, g.top, g.bottom
    left, right, centre = g.stem(g.left), g.stem(g.right), g.stem(g.centre)
    wide_l, wide_r = g.stem(g.wide_left), g.stem(g.wide_right)

    def strokes(core: Core) -> int:
        """The most separate white runs this shape has on any one row."""
        return max(
            len(runs([x for x, yy in core if yy == y])) for y in {y for _, y in core}
        )

    def clearance(core: Core) -> int:
        """How far this shape must open up to leave room for a centre stem.

        Only rows with two walls count: a closed O top or crossing X middle
        says nothing about where the sides sit.
        """
        need = 0
        for y in {y for _, y in core}:
            parts = runs([x for x, yy in core if yy == y])
            if len(parts) >= 2:
                need = max(need, parts[0][-1] - (g.centre[0] - 2))
        return max(0, need)

    out: dict[str, Core] = {}

    for cyr, lat in SAME_AS_LATIN.items():
        out[cyr] = g.core(lat)

    # З borrows the digit three, unless digits are taller than the caps (`large`).
    three = out["З"]
    if max(y for _, y in three) - min(y for _, y in three) != bottom - top:
        out["З"] = (
            g.bar("top")
            | g.bar("mid", g.left[0] + w, g.right[-1])
            | g.bar("bottom")
            | g.stem(g.right, top, bottom)
        )
    for cyr, lat in MIRRORED.items():
        out[cyr] = mirror_rows(g.core(lat), g)
    if slanted:
        out["Я"] = ya(g)

    out["Г"] = g.bar("top") | left
    out["П"] = g.bar("top") | left | right
    out["Ш"] = (
        wide_l | centre | wide_r | g.bar("bottom", g.wide_left[0], g.wide_right[-1])
    )

    def tailed(stems: Core, cols: list[int], wide: bool) -> Core:
        """Ц and Щ, with the spur that distinguishes them from П and Ш.

        With the baseline already on the last usable row, the letter moves up
        by one rather than lose the spur.
        """
        row = min(bottom + 1, SAFE_Y[1])
        lift = bottom + 1 - row
        body = {(x, y) for x, y in stems if y <= bottom - lift}
        bars = {
            (x, y - lift)
            for x, y in g.bar(
                "bottom",
                (g.wide_left if wide else g.left)[0],
                (g.wide_right if wide else g.right)[-1],
            )
        }
        return body | bars | {(x, row) for x in cols}

    out["Щ"] = tailed(wide_l | centre | wide_r, g.wide_right, wide=True)
    out["Ц"] = tailed(left | right, g.right, wide=False)
    # The waist bar has to reach both stems; E's own arm stops short of the right.
    out["Ч"] = (
        {c for c in left if c[1] <= max(g.middle)}
        | g.bar("mid", g.left[0], g.right[-1])
        | right
    )

    # Ь, Б and Ъ share one bowl drawn from the font's own bars and stems: B's
    # bowl fills the cell in some faces, leaving no room for Ъ's flag.
    def soft_sign(offset: int) -> Core:
        riser = {(x + offset, y) for x, y in left}
        wall = g.stem(g.right, g.middle[0], bottom)
        return (
            riser
            | wall
            | g.bar("mid", g.left[0] + offset, g.right[-1])
            | g.bar("bottom", g.left[0] + offset, g.right[-1])
        )

    out["Ь"] = soft_sign(0)
    out["Б"] = g.bar("top") | out["Ь"]
    out["Є"] = g.core("C") | {c for c in g.bar("mid") if c[0] <= g.right[-1] - w}
    out["Э"] = mirror(out["Є"])
    out["Ф"] = phi(g.core("O"), w)
    # X's arms converge on the middle, so a full-height stem makes Ж -- unless
    # the face is too narrow or slanted, where the squared form is used instead.
    cross = g.core("X")
    crossed = splay(cross, clearance(cross)) | centre
    squared = wide_l | centre | wide_r | g.bar("mid", g.wide_left[0], g.wide_right[-1])
    out["Ж"] = crossed if strokes(crossed) >= 3 else squared

    # Ю: stem, waist bar, and a narrow bowl between the centre and right stems.
    out["Ю"] = (
        wide_l
        | centre
        | wide_r
        | g.bar("top", g.centre[0], g.wide_right[-1])
        | g.bar("bottom", g.centre[0], g.wide_right[-1])
        | g.bar("mid", g.wide_left[0], g.centre[-1])
    )
    # Ы: the same bowl, mirrored onto the left, plus a free-standing stem.
    out["Ы"] = (
        wide_l
        | wide_r
        | g.stem(g.centre, g.middle[0], bottom)
        | g.bar("mid", g.wide_left[0], g.centre[-1])
        | g.bar("bottom", g.wide_left[0], g.centre[-1])
    )
    # Ъ is that bowl moved right, with a flag filling the gap it leaves.
    out["Ъ"] = soft_sign(w) | g.bar("top", g.left[0], g.left[0] + 2 * w - 1)

    # Л and Д: right stem plus a leg that steps left at the waist.
    knee = (top + bottom) // 2
    leg = {(x + w, y) for x, y in left if y < knee} | {c for c in left if c[1] >= knee}
    out["Л"] = right | leg | g.bar("top", g.left[0] + w)
    # Д is wider than the Latin box, so base and feet clamp to the usable space.
    base_l = max(SAFE_X[0] + reserve, g.left[0] - w)
    base_r = min(SAFE_X[1], g.right[-1] + w)
    foot_row = min(bottom + 1, SAFE_Y[1])
    lift = bottom + 1 - foot_row
    out["Д"] = (
        {(x, y) for x, y in right | leg if y < min(g.bottom_bar) - lift}
        | g.bar("top", g.left[0] + w)
        | {(x, y - lift) for x, y in g.bar("bottom", base_l, base_r)}
        | {
            (x, foot_row)
            for x in list(range(base_l, base_l + w))
            + list(range(base_r - w + 1, base_r + 1))
        }
    )

    out["Ї"] = out["І"] | g.marks(g.left + g.right)
    out["Ё"] = out["Е"] | g.marks(g.left + g.right)
    out["Й"] = out["И"] | breve(out["И"], g)
    out["Ґ"] = out["Г"] | g.marks(g.right)
    return out


def glyphs(latin: dict[str, Pixels]) -> dict[int, Pixels]:
    """Codepoint -> pixels, ready to hand to the font builder."""
    made = compose(latin)
    return {cp: render(made[letter]) for cp, letter in UPPERCASE.items()}
