"""Greek capitals.

Most of the alphabet is already in the font under another name: half the
capitals are Latin letters, and Gamma, Pi and Phi are the Cyrillic ones this
project already composes. Only Delta, Theta, Lambda, Xi, Sigma, Psi and Omega
have to be drawn, out of the same stems and bars as everything else.
"""

from __future__ import annotations

import cyrillic
from shapes import (
    SAFE_X,
    Core,
    Geometry,
    Pixels,
    box,
    clip,
    core_of,
    line,
    render,
)

# Capitals the font already draws, under a Latin name.
AS_LATIN = {
    0x0391: "A",
    0x0392: "B",
    0x0395: "E",
    0x0396: "Z",
    0x0397: "H",
    0x0399: "I",
    0x039A: "K",
    0x039C: "M",
    0x039D: "N",
    0x039F: "O",
    0x03A1: "P",
    0x03A4: "T",
    0x03A5: "Y",
    0x03A7: "X",
}
# Capitals the Cyrillic already composes, under a Cyrillic name.
AS_CYRILLIC = {
    0x0393: "Г",
    0x03A0: "П",
    0x03A6: "Ф",
}
DRAWN = {
    0x0394: "delta",
    0x0398: "theta",
    0x039B: "lambda",
    0x039E: "xi",
    0x03A3: "sigma",
    0x03A8: "psi",
    0x03A9: "omega",
}
# Lowercase folds onto the capitals, as it does everywhere else in these fonts.
LOWERCASE = {cp + 0x20: cp for cp in list(AS_LATIN) + list(AS_CYRILLIC) + list(DRAWN)}
LOWERCASE[0x03C2] = 0x03A3  # final sigma
LOWERCASE[0x03D5] = 0x03A6  # phi symbol


def cores(latin: dict[str, Pixels]) -> dict[int, Core]:
    """Codepoint -> white core."""
    g = Geometry(latin)
    cyr = cyrillic.compose(latin)
    w = g.weight
    top, bottom = g.top, g.bottom
    left, right = g.left[0], g.right[-1]
    middle = (top + bottom) // 2

    out: dict[int, Core] = {cp: core_of(latin[ch]) for cp, ch in AS_LATIN.items()}
    out.update({cp: cyr[ch] for cp, ch in AS_CYRILLIC.items()})

    # Delta and Lambda: one stroke and its reflection, so the apex is centred
    # whichever way the rounding falls.
    apex = (left + right) // 2
    rise = line((left, bottom), (apex, top), w)
    tent = rise | {(left + right - x, y) for x, y in rise}
    out[0x0394] = tent | g.bar("bottom", left, right)
    out[0x039B] = tent
    out[0x0398] = core_of(latin["O"]) | g.bar("mid", left + w, right - w)
    out[0x039E] = (
        g.bar("top", left + 1, right - 1)
        | g.bar("mid", left + 1, right - 1)
        | g.bar("bottom", left, right)
    )
    out[0x03A3] = (
        g.bar("top", left, right)
        | g.bar("bottom", left, right)
        | line((left, top), (apex, middle), w)
        | line((apex, middle), (left, bottom), w)
    )
    # Psi uses the wide stem box the three-stem Cyrillic letters use, or its
    # arms would touch the stem on a narrow face.
    out[0x03A8] = (
        g.stem(g.centre)
        | g.stem(g.wide_left, top, middle)
        | g.stem(g.wide_right, top, middle)
        | g.bar("mid", g.wide_left[0], g.wide_right[-1])
    )
    # Omega: the bowl lifted off the baseline, standing on two feet. The feet
    # are drawn rather than borrowed from E, which would close the gap.
    sole = min(w, 2)
    bowl = {cell for cell in core_of(latin["O"]) if cell[1] <= bottom - sole}
    out[0x03A9] = (
        bowl
        | box(max(SAFE_X[0], left - w), left + w - 1, bottom - sole + 1, bottom)
        | box(right - w + 1, min(SAFE_X[1], right + w), bottom - sole + 1, bottom)
    )
    return {cp: clip(core) for cp, core in out.items()}


def glyphs(latin: dict[str, Pixels]) -> dict[int, Pixels]:
    """Codepoint -> pixels, ready to hand to the font builder."""
    return {cp: render(core) for cp, core in cores(latin).items()}
