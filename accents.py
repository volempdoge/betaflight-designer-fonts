"""Accented Latin capitals, composed from each font's own letters.

Every one of the ten faces leaves at least three rows above its cap line, which
is where the marks go -- a letter is never squeezed to make room. The mark is
centred over the top of the letter it belongs to, so it follows the slant of a
slanted face without being told about it.

Letters that are a ligature rather than a mark (AE, OE, SS) are not drawn here:
the font builder folds them to the letters they stand for, which is what an
all-capitals face would do anyway.
"""

from __future__ import annotations

from shapes import (
    SAFE_X,
    SAFE_Y,
    Core,
    Geometry,
    Pixels,
    bounds,
    box,
    clip,
    core_of,
    fit_x,
    line,
    render,
    ring,
    shift,
)

# Codepoint -> (base capital, mark). The mark names are the Unicode ones.
COMPOSED: dict[int, tuple[str, str]] = {
    0x00C0: ("A", "grave"),
    0x00C1: ("A", "acute"),
    0x00C2: ("A", "circumflex"),
    0x00C3: ("A", "tilde"),
    0x00C4: ("A", "diaeresis"),
    0x00C5: ("A", "ring"),
    0x00C7: ("C", "cedilla"),
    0x00C8: ("E", "grave"),
    0x00C9: ("E", "acute"),
    0x00CA: ("E", "circumflex"),
    0x00CB: ("E", "diaeresis"),
    0x00CC: ("I", "grave"),
    0x00CD: ("I", "acute"),
    0x00CE: ("I", "circumflex"),
    0x00CF: ("I", "diaeresis"),
    0x00D1: ("N", "tilde"),
    0x00D2: ("O", "grave"),
    0x00D3: ("O", "acute"),
    0x00D4: ("O", "circumflex"),
    0x00D5: ("O", "tilde"),
    0x00D6: ("O", "diaeresis"),
    0x00D9: ("U", "grave"),
    0x00DA: ("U", "acute"),
    0x00DB: ("U", "circumflex"),
    0x00DC: ("U", "diaeresis"),
    0x00DD: ("Y", "acute"),
    0x0100: ("A", "macron"),
    0x0102: ("A", "breve"),
    0x0104: ("A", "ogonek"),
    0x0106: ("C", "acute"),
    0x010C: ("C", "caron"),
    0x010E: ("D", "caron"),
    0x0112: ("E", "macron"),
    0x0116: ("E", "dot"),
    0x0118: ("E", "ogonek"),
    0x011A: ("E", "caron"),
    0x011E: ("G", "breve"),
    0x0122: ("G", "cedilla"),
    0x012A: ("I", "macron"),
    0x012E: ("I", "ogonek"),
    0x0130: ("I", "dot"),
    0x0136: ("K", "cedilla"),
    0x0139: ("L", "acute"),
    0x013B: ("L", "cedilla"),
    0x013D: ("L", "caron"),
    0x0143: ("N", "acute"),
    0x0145: ("N", "cedilla"),
    0x0147: ("N", "caron"),
    0x014C: ("O", "macron"),
    0x0150: ("O", "double acute"),
    0x0154: ("R", "acute"),
    0x0158: ("R", "caron"),
    0x015A: ("S", "acute"),
    0x015E: ("S", "cedilla"),
    0x0160: ("S", "caron"),
    0x0162: ("T", "cedilla"),
    0x0164: ("T", "caron"),
    0x016A: ("U", "macron"),
    0x016E: ("U", "ring"),
    0x0170: ("U", "double acute"),
    0x0172: ("U", "ogonek"),
    0x0178: ("Y", "diaeresis"),
    0x0179: ("Z", "acute"),
    0x017B: ("Z", "dot"),
    0x017D: ("Z", "caron"),
    0x0218: ("S", "comma"),
    0x021A: ("T", "comma"),
}

# Letters carrying a stroke through the body rather than a mark above it.
STRUCK = {
    0x00D0: "eth",
    0x00D8: "slash",
    0x00DE: "thorn",
    0x0110: "eth",
    0x0141: "bar",
}

# Lowercase codepoint -> its capital, for the letters actually drawn here.
# Latin-1 pairs sit 0x20 apart, Latin Extended-A pairs next door to each other.
_CAPITALS = sorted(COMPOSED) + sorted(STRUCK)
LOWERCASE: dict[int, int] = {
    (cp + 0x20 if cp < 0x0100 else cp + 1): cp for cp in _CAPITALS
}
LOWERCASE[0x00FF] = 0x0178  # y with diaeresis is a capital of its own
LOWERCASE.pop(0x0179, None)  # ...so the slot after it is Z with acute, not that
LOWERCASE[0x0131] = ord("I")  # dotless i, in a font with no lowercase at all


def _crown(g: Geometry, base: Core) -> tuple[int, int]:
    """The column to centre a mark on, and the row it hangs from."""
    top = min(y for _, y in base)
    row = [x for x, y in base if y <= top + 1]
    return (min(row) + max(row)) // 2, top - 1


def _marks(g: Geometry, base: Core) -> dict[str, Core]:
    """Every mark, drawn over `base` in this font's weight."""
    cx, low = _crown(g, base)
    high = low - 1
    w = min(g.weight, 2)
    dot = box(cx - w + 1, cx, low - w + 1, low)
    return {
        "acute": line((cx - 1, low), (cx + 1, high), w),
        "grave": line((cx - 1, high), (cx + 1, low), w),
        "circumflex": line((cx - 2, low), (cx, high), 1)
        | line((cx, high), (cx + 2, low), 1),
        "caron": line((cx - 2, high), (cx, low), 1)
        | line((cx, low), (cx + 2, high), 1),
        # A tilde over two rows: the smooth three-row wave of the tilde
        # character has no room to sit this close to a cap line.
        "tilde": {(cx - 1, high), (cx, high), (cx + 2, high)}
        | {(cx - 2, low), (cx + 1, low), (cx + 2, low)},
        "diaeresis": box(cx - 2, cx - 3 + w, low - w + 1, low)
        | box(cx + 2 - w + 1, cx + 2, low - w + 1, low),
        "macron": box(cx - 2, cx + 2, low - w + 1, low),
        "dot": dot,
        # Three rows if the face has them; on the tallest face the ring keeps
        # its counter by standing on two, open at the bottom.
        "ring": ring(cx - 1, cx + 1, low - 2, low, 1)
        if low - 2 >= SAFE_Y[0]
        else box(cx - 1, cx + 1, high, high) | {(cx - 1, low), (cx + 1, low)},
        "double acute": line((cx - 3, low), (cx - 1, high), w)
        | line((cx, low), (cx + 2, high), w),
        "breve": box(cx - 1, cx + 1, low, low) | {(cx - 2, high), (cx + 2, high)},
        "cedilla": _below(g, base, "cedilla"),
        "comma": _below(g, base, "comma"),
        "ogonek": _below(g, base, "ogonek"),
    }


DEEP = 2  # rows a mark below the baseline wants
HIGH = {"ring": 3}  # marks that want more than two rows above the cap
DEFAULT_HIGH = 2


def _drop(base: Core, mark: str) -> int:
    """How far to lower a letter so its mark above fits over it.

    Only the ring wants a third row, and only the two tallest faces are short
    of one; lowering the letter keeps the ring a ring instead of a bar.
    """
    want = HIGH.get(mark, DEFAULT_HIGH)
    room_above = min(y for _, y in base) - SAFE_Y[0]
    room_below = SAFE_Y[1] - max(y for _, y in base)
    return max(0, min(want - room_above, room_below))


def _lift(g: Geometry, base: Core) -> int:
    """How far to raise a letter so its mark below fits under it.

    The tall faces fill the cell to the baseline, so something has to give.
    Raising the letter is what the Cyrillic already does for the spur on
    the letters that need it, and it keeps the mark whole.
    """
    room_below = SAFE_Y[1] - max(y for _, y in base)
    room_above = min(y for _, y in base) - SAFE_Y[0]
    return max(0, min(DEEP - room_below, room_above))


def _below(g: Geometry, base: Core, kind: str) -> Core:
    """Marks hanging under the baseline: cedilla, ogonek, comma below."""
    bottom = max(y for _, y in base)
    row = [x for x, y in base if y >= bottom - 1]
    deep = min(DEEP, SAFE_Y[1] - bottom)
    left, right = min(row), max(row)
    centre = (left + right) // 2
    w = min(g.weight, 2)
    if kind == "ogonek":
        # Under the right of the letter, where an ogonek hangs.
        tail = box(right - w, right - 1, bottom + 1, bottom + deep)
        return tail | {(right, bottom + deep)} if deep > 1 else tail
    if kind == "comma":
        return box(centre, centre + w - 1, bottom + 1, bottom + deep)
    hook = box(centre - w + 1, centre, bottom + 1, bottom + deep)
    return hook | ({(centre - w, bottom + deep)} if deep > 1 else set())


def _struck(g: Geometry, latin: dict[str, Pixels]) -> dict[int, Core]:
    """Letters with a stroke through them: Ø, Ł, Ð/Đ, Þ."""
    w = g.weight
    top, bottom = g.top, g.bottom
    out: dict[int, Core] = {}

    o = core_of(latin["O"])
    ox0, ox1, oy0, oy1 = bounds(o)
    # The slash overhangs the bowl, but only as far as the cell allows.
    out[0x00D8] = o | line(
        (max(SAFE_X[0], ox0 - 1), min(SAFE_Y[1], oy1 + 1)),
        (min(SAFE_X[1] - w + 1, ox1 + 1), max(SAFE_Y[0], oy0 - 1)),
        w,
    )

    d = core_of(latin["D"])
    dx0, _, _, _ = bounds(d)
    middle = (top + bottom) // 2
    out[0x00D0] = d | box(
        max(SAFE_X[0], dx0 - w), dx0 + w, middle - w // 2, middle - w // 2 + w - 1
    )
    out[0x0110] = out[0x00D0]

    ell = core_of(latin["L"])
    lx0, _, _, _ = bounds(ell)
    waist = (top + bottom) // 2
    out[0x0141] = ell | line(
        (max(SAFE_X[0], lx0 - 1), waist + 2), (lx0 + w + 1, waist - 2), 1
    )

    # A thorn is P's bowl slid down the stem, which is what the letter is.
    p = core_of(latin["P"])
    stem = g.stem(g.left)
    bowl = {cell for cell in p if cell not in stem}
    drop = max(1, (bottom - top) // 5)
    out[0x00DE] = stem | {(x, y + drop) for x, y in bowl if y + drop <= bottom}
    return out


def cores(latin: dict[str, Pixels]) -> dict[int, Core]:
    """Codepoint -> white core."""
    g = Geometry(latin)
    out: dict[int, Core] = {}
    for codepoint, (letter, mark) in COMPOSED.items():
        base = core_of(latin[letter])
        if mark in ("cedilla", "ogonek", "comma"):
            base = shift(base, 0, -_lift(g, base))
        else:
            base = shift(base, 0, _drop(base, mark))
        out[codepoint] = base | fit_x(_marks(g, base)[mark])
    out.update(_struck(g, latin))
    return {cp: clip(core) for cp, core in out.items()}


def glyphs(latin: dict[str, Pixels]) -> dict[int, Pixels]:
    """Codepoint -> pixels, ready to hand to the font builder."""
    return {cp: render(core) for cp, core in cores(latin).items()}


# Letters that are two letters in an all-capitals face. The font builder folds
# them through GSUB rather than drawing a ligature that would not fit.
FOLDS = {
    0x00C6: "AE",
    0x00E6: "AE",
    0x0152: "OE",
    0x0153: "OE",
    0x00DF: "SS",
    0x1E9E: "SS",
    0x0132: "IJ",
    0x0133: "IJ",
}
