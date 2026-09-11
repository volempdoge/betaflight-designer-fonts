"""Typographic punctuation, maths and currency in the Betaflight OSD idiom.

The .mcm fonts carry ASCII and little else: a straight hyphen, straight quotes,
no dashes, no ellipsis, no currency beyond what the OSD needed. Everything here
is drawn from the same measurements the Cyrillic uses -- the font's own stroke
weight, stem columns and bar rows -- so punctuation matches the letters it sits
between.

Three ASCII slots in the source fonts hold OSD icons rather than the character
they are addressed by: `$` is a checkered flag, `~` a crosshair, `` ` `` an
arrow. Those are redrawn here and the icons stay reachable through
`symbols.py`.
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
    centre_x,
    chevron,
    clip,
    core_of,
    line,
    mirror,
    place,
    render,
    ring,
    rotate,
    shift,
    wave,
)

# Codepoint -> name, for the character index and the docs.
NAMES = {
    0x0024: "dollar sign",
    0x0060: "grave accent",
    0x007B: "left curly bracket",
    0x007D: "right curly bracket",
    0x007E: "tilde",
    0x00A1: "inverted exclamation mark",
    0x00A2: "cent sign",
    0x00A3: "pound sign",
    0x00A5: "yen sign",
    0x00B0: "degree sign",
    0x00B1: "plus-minus sign",
    0x00B5: "micro sign",
    0x00B7: "middle dot",
    0x00BF: "inverted question mark",
    0x00D7: "multiplication sign",
    0x00F7: "division sign",
    0x00AB: "left-pointing double angle quotation mark",
    0x00BB: "right-pointing double angle quotation mark",
    0x2018: "left single quotation mark",
    0x2019: "right single quotation mark",
    0x201C: "left double quotation mark",
    0x201D: "right double quotation mark",
    0x201A: "single low-9 quotation mark",
    0x201E: "double low-9 quotation mark",
    0x2013: "en dash",
    0x2014: "em dash",
    0x2022: "bullet",
    0x2026: "horizontal ellipsis",
    0x2039: "single left-pointing angle quotation mark",
    0x203A: "single right-pointing angle quotation mark",
    0x20A0: "euro-currency sign",
    0x20AC: "euro sign",
    0x20B4: "hryvnia sign",
    0x20BD: "ruble sign",
    0x2212: "minus sign",
    0x2248: "almost equal to",
    0x2260: "not equal to",
    0x2264: "less-than or equal to",
    0x2265: "greater-than or equal to",
    0x221E: "infinity",
}


def _widest_rows(core: Core) -> Core:
    """The rows a shape is widest on -- the bar inside + or =."""
    width = {y: sum(1 for _, yy in core if yy == y) for _, y in core}
    most = max(width.values())
    return {(x, y) for x, y in core if width[y] == most}


def cores(latin: dict[str, Pixels]) -> dict[int, Core]:
    """Codepoint -> white core, drawn to this font's own measurements."""
    g = Geometry(latin)
    w = g.weight
    top, bottom = g.top, g.bottom
    middle = (top + bottom) // 2
    dot = core_of(latin["."])
    dx0, dx1, dy0, dy1 = bounds(dot)
    dot_w, dot_h = dx1 - dx0 + 1, dy1 - dy0 + 1
    plus = core_of(latin["+"])
    px0, px1, py0, py1 = bounds(plus)
    equals = core_of(latin["="])
    ex0, ex1, ey0, ey1 = bounds(equals)
    comma = core_of(latin[","])
    cx0, cx1, _, _ = bounds(comma)
    hyphen = core_of(latin["-"])
    hx0, hx1, hy0, hy1 = bounds(hyphen)

    out: dict[int, Core] = {}

    # --- dashes: three widths of the font's own hyphen ------------------------
    out[0x2013] = box(max(SAFE_X[0], hx0 - 1), min(SAFE_X[1], hx1 + 1), hy0, hy1)
    out[0x2014] = box(SAFE_X[0], SAFE_X[1], hy0, hy1)
    # The minus sits on the maths axis, so it lines up with + and =.
    out[0x2212] = _widest_rows(plus)

    # --- dots -----------------------------------------------------------------
    gap = 1 if 3 * dot_w + 2 <= SAFE_X[1] - SAFE_X[0] + 1 else 0
    small = dot_w if gap else max(1, (SAFE_X[1] - SAFE_X[0] + 1 - 2) // 3)
    ellipsis: Core = set()
    for i in range(3):
        x = SAFE_X[0] + i * (small + gap)
        ellipsis |= box(x, x + small - 1, dy0, dy1)
    out[0x2026] = centre_x(ellipsis)
    out[0x00B7] = shift(dot, 0, middle - (dy0 + dy1) // 2)
    blob = box(dx0 - 1, dx1 + 1, dy0 - 1, dy1 + 1)
    out[0x2022] = centre_x(shift(blob, 0, middle - (dy0 + dy1) // 2))

    # --- quotes: the font's own comma, lifted and turned ----------------------
    raised = place(comma, y=top)
    pair_gap = 1 if 2 * (cx1 - cx0 + 1) + 1 <= SAFE_X[1] - SAFE_X[0] + 1 else 0
    step = cx1 - cx0 + 1 + pair_gap

    def pair(mark: Core) -> Core:
        return centre_x(mark | shift(mark, step))

    out[0x2019] = centre_x(raised)
    out[0x2018] = centre_x(rotate(raised))
    out[0x201D] = pair(raised)
    out[0x201C] = pair(rotate(raised))
    out[0x201A] = centre_x(comma)
    out[0x201E] = pair(comma)

    # --- angle quotes ---------------------------------------------------------
    tall = max(4, (bottom - top) // 2)
    while 2 * (tall // 2 + w) + 1 > SAFE_X[1] - SAFE_X[0] + 1:
        tall -= 2
    y0 = middle - tall // 2
    y1 = y0 + tall
    wide = tall // 2 + w

    def angle(point: str, count: int) -> Core:
        one = chevron(0, wide - 1, y0, y1, w, point)
        both = one | shift(one, wide + 1) if count == 2 else one
        return centre_x(both)

    out[0x203A] = angle("right", 1)
    out[0x2039] = angle("left", 1)
    out[0x00BB] = angle("right", 2)
    out[0x00AB] = angle("left", 2)

    # --- braces ---------------------------------------------------------------
    def brace(point: str) -> Core:
        stem_x = SAFE_X[0] + w + 1
        arm = box(stem_x + w, stem_x + 2 * w - 1, top, top + w - 1)
        foot = box(stem_x + w, stem_x + 2 * w - 1, bottom - w + 1, bottom)
        waist = box(stem_x - w, stem_x - 1, middle, middle + w - 1)
        spine = box(stem_x, stem_x + w - 1, top, bottom) - box(
            stem_x, stem_x + w - 1, middle, middle + w - 1
        )
        left = spine | arm | foot | waist
        return centre_x(left if point == "left" else mirror(left))

    out[0x007B] = brace("left")
    out[0x007D] = brace("right")

    # --- maths ----------------------------------------------------------------
    under = min(py1 + 2, SAFE_Y[1] - w + 1)
    out[0x00B1] = plus | box(px0, px1, under, under + w - 1)
    out[0x00D7] = line((px0, py0), (px1, py1), w) | line((px0, py1), (px1, py0), w)
    bar = _widest_rows(plus)
    bx0, bx1, by0, by1 = bounds(bar)
    out[0x00F7] = (
        bar
        | box(
            (bx0 + bx1 - dot_w) // 2 + 1,
            (bx0 + bx1 + dot_w) // 2,
            by0 - 1 - dot_h,
            by0 - 2,
        )
        | box(
            (bx0 + bx1 - dot_w) // 2 + 1,
            (bx0 + bx1 + dot_w) // 2,
            by1 + 2,
            by1 + 1 + dot_h,
        )
    )
    # The slash is steep: at 45 degrees it lies along the bars and disappears.
    mid_x = (ex0 + ex1) // 2
    out[0x2260] = equals | line((mid_x + w, ey0 - 3), (mid_x - w, ey1 + 3), 1)
    lower = min(ey1 + 2, SAFE_Y[1] - w)
    out[0x2248] = wave(ex0, ex1, ey0, w) | wave(ex0, ex1, lower, w)

    def ordered(point: str) -> Core:
        # A short face has no room for a gap: the bar thins before the chevron
        # flattens into a second bar.
        thick = min(w, 2)
        high = bottom - thick - 2 - top
        stroke = max(1, min(w, high // 3))
        return chevron(ex0, ex1, top, bottom - thick - 2, stroke, point) | box(
            ex0, ex1, bottom - thick + 1, bottom
        )

    out[0x2264] = ordered("left")
    out[0x2265] = ordered("right")
    # Two loops sharing a column. The corners come off so they read as rings
    # rather than boxes, which is all the room a 12 pixel cell leaves.
    loop = min(2 * w + 3, (SAFE_X[1] - SAFE_X[0] + 2) // 2)
    high = min(loop, bottom - middle)
    # A heavy face would close the counters, so the loops keep a thinner wall.
    wall = max(1, min(w, (min(loop, high) - 1) // 2))
    rings = _rounded(0, loop - 1, middle - high // 2, middle + high // 2, wall)
    out[0x221E] = centre_x(rings | shift(rings, loop - 1))

    # --- ASCII the source fonts spend on OSD icons ----------------------------
    out[0x0024] = core_of(latin["S"]) | _through(g)
    out[0x007E] = wave(SAFE_X[0] + 1, SAFE_X[1] - 1, middle, w)
    out[0x0060] = line((g.left[0], top), (g.left[0] + 2, top + 2), w)

    # --- inverted Spanish punctuation ----------------------------------------
    out[0x00A1] = rotate(core_of(latin["!"]))
    out[0x00BF] = rotate(core_of(latin["?"]))

    # --- degree and micro -----------------------------------------------------
    size = 2 * w + 2
    out[0x00B0] = centre_x(ring(0, size - 1, top, top + size - 1, w))
    u = core_of(latin["U"])
    ux0, _, _, uy1 = bounds(u)
    out[0x00B5] = u | box(ux0, ux0 + w - 1, uy1, min(SAFE_Y[1], uy1 + 3))

    # --- currency -------------------------------------------------------------
    c = core_of(latin["C"])
    strokes = box(g.left[0] - 1, g.centre[-1] + 1, middle - w, middle - 1) | box(
        g.left[0] - 1, g.centre[-1] + 1, middle + 1, middle + w
    )
    out[0x20AC] = c | {cell for cell in strokes if cell[0] >= SAFE_X[0]}
    out[0x20A0] = out[0x20AC]
    out[0x00A2] = c | _through(g)
    out[0x00A5] = (
        core_of(latin["Y"])
        | box(g.left[0], g.right[-1], middle + 1, middle + w)
        | box(g.left[0], g.right[-1], middle + w + 2, middle + 2 * w + 1)
    )
    # The stroke crosses below the waist of the S: level with it, the letter's
    # own middle swallows it and the sign reads as a plain S.
    strike = min(middle + 2, bottom - 2 * w)
    out[0x20B4] = core_of(latin["S"]) | box(
        max(SAFE_X[0], g.left[0] - 1),
        min(SAFE_X[1], g.right[-1] + 1),
        strike,
        strike + w - 1,
    )
    p = core_of(latin["P"])
    px, _, _, _ = bounds(p)
    out[0x20BD] = p | box(
        max(SAFE_X[0], px - w), g.right[-1], bottom - 2 * w, bottom - w - 1
    )
    out[0x00A3] = _pound(g, latin)
    return {cp: clip(core) for cp, core in out.items()}


def _rounded(x0: int, x1: int, y0: int, y1: int, weight: int) -> Core:
    """A ring with its corners taken off, so it reads round at this size."""
    corners = {(x, y) for x in (x0, x1) for y in (y0, y1)}
    return ring(x0, x1, y0, y1, weight) - corners


def _through(g: Geometry) -> Core:
    """The upright stroke that turns S into $ and C into a cent sign."""
    return box(
        g.centre[0],
        g.centre[0] + g.weight - 1,
        max(SAFE_Y[0], g.top - 1),
        min(SAFE_Y[1], g.bottom + 1),
    )


def _pound(g: Geometry, latin: dict[str, Pixels]) -> Core:
    """A pound sign: the top half of C, a stem, a foot and a crossbar."""
    w = g.weight
    c = core_of(latin["C"])
    middle = (g.top + g.bottom) // 2
    curl = {cell for cell in c if cell[1] < middle}
    stem = g.stem(g.left, min(y for _, y in curl), g.bottom - w)
    edge = max(SAFE_X[0], g.left[0] - 1)
    foot = box(edge, g.right[-1], g.bottom - w + 1, g.bottom)
    cross = box(edge, g.right[-1] - w, middle, middle + w - 1)
    return curl | stem | foot | cross


def glyphs(latin: dict[str, Pixels]) -> dict[int, Pixels]:
    """Codepoint -> pixels, ready to hand to the font builder."""
    return {cp: render(core) for cp, core in cores(latin).items()}


# Signs that read better spelled out at 12 pixels than drawn into one cell.
# The font builder folds them through GSUB; the codepoint still carries the
# first character's shape, so a renderer that ignores GSUB shows something.
FOLDS = {
    0x00A9: "(C)",
    0x00AE: "(R)",
    0x2122: "TM",
    0x2116: "N°",
    0x00BC: "1/4",
    0x00BD: "1/2",
    0x00BE: "3/4",
    0x2153: "1/3",
    0x2154: "2/3",
}
