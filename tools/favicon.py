#!/usr/bin/env python3
"""Cut the site favicon out of a built character PNG.

The character PNGs are 12x18 OSD cells, so handing one to a browser as a
favicon gets it squeezed into a square slot and the glyph comes out stretched.
The `#` this uses happens to be square once the blank margin is gone, so this
is a crop around the ink and nothing is resampled: the favicon is the same
pixels the font draws.

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
TARGET = ROOT / "site" / "assets" / "favicon.png"


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=TARGET,
        help=f"where to write the favicon (default: {TARGET.relative_to(ROOT)})",
    )
    args = parser.parse_args(argv)

    if not SOURCE.exists():
        raise SystemExit(
            f"{SOURCE} is missing -- build the fonts first:\n"
            "  uv run bf2font.py original_fonts/*.mcm"
        )

    with Image.open(SOURCE) as source:
        icon = square(source.convert("RGBA"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    icon.save(args.output, optimize=True)
    print(f"{args.output} ({icon.width}x{icon.height})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
