#!/usr/bin/env python3
"""Cut the site icons out of a built character PNG.

The character PNGs are 12x18 OSD cells, so handing one to a browser as a
favicon gets it squeezed into a square slot and the glyph comes out stretched.
The `#` this uses happens to be square once the blank margin is gone, so this
is a crop around the ink. The larger and smaller sizes are whole-number
multiples of the OSD pixel, so nothing is ever blurred: every icon is the same
pixels the font draws.

Writes three files into site/assets/:

- favicon.png, 96x96 and transparent, the one the page links. Google Search
  wants a multiple of 48px.
- favicon.ico, 16, 32 and 48, for anything that asks for /favicon.ico.
- apple-touch-icon.png, 180x180 on black. iOS fills transparency with black
  anyway, and a home screen tile wants some room around the mark.

    uv run tools/favicon.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent

# The OSD hash, from the face the page shows first.
SOURCE = ROOT / "output" / "clarity" / "png" / "035.png"
TARGET = ROOT / "site" / "assets"

# The character PNGs are drawn at this many image pixels per OSD pixel.
PNG_SCALE = 8
ICO_SIZES = (16, 32, 48)
TOUCH_SIZE = 180


def square(image: Image.Image) -> Image.Image:
    """The ink, centred on a transparent square, keeping its own margin."""
    box = image.getbbox()
    if box is None:
        raise SystemExit(f"{SOURCE} is blank, there is no glyph to cut out")
    left, top, right, bottom = box
    width, height = right - left, bottom - top
    if width != height:
        raise SystemExit(
            f"the ink is {width}x{height}, not square; pick a character whose "
            "drawing is, or this would have to scale and blur it"
        )
    # The horizontal margin the cell already leaves is the one to keep.
    margin = min(left, image.width - right)
    side = width + 2 * margin
    out = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    out.paste(image.crop(box), (margin, margin))
    return out


def tile(
    glyph: Image.Image, size: int, clear: float, background: tuple[int, ...]
) -> Image.Image:
    """The glyph centred on a `size` square, at the largest whole-number scale
    that still leaves `clear` of the side free on every edge.

    `glyph` is the bare ink at one image pixel per OSD pixel. Scaling it by a
    whole number with nearest-neighbour is the only resize that adds no blur.
    """
    factor = int(size * (1 - 2 * clear)) // glyph.width
    if factor < 1:
        raise SystemExit(f"a {glyph.width}px glyph does not fit a {size}px icon")
    side = glyph.width * factor
    scaled = glyph.resize((side, side), Image.Resampling.NEAREST)
    out = Image.new("RGBA", (size, size), background)
    offset = (size - side) // 2
    out.alpha_composite(scaled, (offset, offset))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=TARGET,
        help=f"where to write the icons (default: {TARGET.relative_to(ROOT)})",
    )
    args = parser.parse_args(argv)

    if not SOURCE.exists():
        raise SystemExit(
            f"{SOURCE} is missing -- build the fonts first:\n"
            "  uv run bf2font.py original_fonts/*.mcm"
        )

    with Image.open(SOURCE) as source:
        icon = square(source.convert("RGBA"))
    # The bare ink at one image pixel per OSD pixel, for the other sizes.
    box = icon.getbbox()
    assert box is not None
    ink = icon.crop(box)
    ink = ink.resize(
        (ink.width // PNG_SCALE, ink.height // PNG_SCALE), Image.Resampling.NEAREST
    )

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    icon.save(out / "favicon.png", optimize=True)
    print(f"{out / 'favicon.png'} ({icon.width}x{icon.height})")

    # Pillow downsamples a single image into every requested size, which would
    # blur them; hand it each size already drawn instead.
    frames = [tile(ink, size, 1 / 12, (0, 0, 0, 0)) for size in ICO_SIZES]
    frames[-1].save(
        out / "favicon.ico",
        sizes=[(s, s) for s in ICO_SIZES],
        append_images=frames[:-1],
    )
    print(f"{out / 'favicon.ico'} ({', '.join(map(str, ICO_SIZES))})")

    touch = tile(ink, TOUCH_SIZE, 1 / 9, (0, 0, 0, 255)).convert("RGB")
    touch.save(out / "apple-touch-icon.png", optimize=True)
    print(f"{out / 'apple-touch-icon.png'} ({touch.width}x{touch.height})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
