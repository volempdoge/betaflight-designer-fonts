#!/usr/bin/env python3
"""Compare two conversion output trees.

Fonts and the JSON index must match byte for byte, since builds are reproducible.
PNGs are compared as decoded pixels: Pillow's wheels deflate differently per
platform even when every pixel is identical.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image


def relative_files(root: Path) -> set[Path]:
    return {p.relative_to(root) for p in root.rglob("*") if p.is_file()}


def same_image(left: Path, right: Path) -> bool:
    with Image.open(left) as a, Image.open(right) as b:
        return (a.size, a.mode, a.tobytes()) == (b.size, b.mode, b.tobytes())


def compare(left: Path, right: Path) -> list[str]:
    problems = []
    here, there = relative_files(left), relative_files(right)
    problems += [f"only in {left}: {p}" for p in sorted(here - there)]
    problems += [f"only in {right}: {p}" for p in sorted(there - here)]

    for rel in sorted(here & there):
        a, b = left / rel, right / rel
        if rel.suffix == ".png":
            if not same_image(a, b):
                problems.append(f"pixels differ: {rel}")
        elif a.read_bytes() != b.read_bytes():
            problems.append(f"bytes differ: {rel}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    args = parser.parse_args(argv)

    problems = compare(args.left, args.right)
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        print(f"{len(problems)} difference(s)", file=sys.stderr)
        return 1
    print(f"{len(relative_files(args.left))} files match")
    return 0


if __name__ == "__main__":
    sys.exit(main())
