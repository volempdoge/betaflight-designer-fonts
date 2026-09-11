"""Cyrillic capitals drawn in the Betaflight OSD idiom.

Each letter is composed from the shapes the font already has: its own stems,
bars, stroke weight and slant, measured by `shapes.Geometry`. Only the white
core is defined here; `shapes.render()` wraps it in the black outline.
"""

from __future__ import annotations

from .shapes import (
    SAFE_X,
    SAFE_Y,
    Core,
    Geometry,
    Pixels,
    core_of,
    interior_stem,
    lean_core,
    mirror,
    mirror_rows,
    needed_splay,
    render,
    runs,
    slope,
    splay,
)

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


def cores(latin: dict[str, Pixels]) -> dict[int, Core]:
    """Codepoint -> white core, the shape every other set is keyed by."""
    made = compose(latin)
    return {cp: made[letter] for cp, letter in UPPERCASE.items()}


def glyphs(latin: dict[str, Pixels]) -> dict[int, Pixels]:
    """Codepoint -> pixels, ready to hand to the font builder."""
    return {cp: render(core) for cp, core in cores(latin).items()}
