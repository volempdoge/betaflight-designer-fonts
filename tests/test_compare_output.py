"""The output comparison used by CI."""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

from tools.compare_output import compare, main


def tree(root: Path) -> Path:
    (root / "fonts" / "otf").mkdir(parents=True)
    (root / "png").mkdir()
    (root / "fonts" / "otf" / "Font.otf").write_bytes(b"font bytes")
    (root / "index.json").write_text('{"a": 1}')
    Image.new("RGBA", (4, 6), (0, 0, 0, 0)).save(root / "png" / "000.png")
    return root


def test_identical_trees(tmp_path: Path) -> None:
    a = tree(tmp_path / "a")
    shutil.copytree(a, tmp_path / "b")
    assert compare(a, tmp_path / "b") == []


def test_png_recompression_is_not_a_difference(tmp_path: Path) -> None:
    """Different deflate settings, same pixels: that is what CI must tolerate."""
    a, b = tree(tmp_path / "a"), tree(tmp_path / "b")
    image = Image.open(a / "png" / "000.png")
    image.save(b / "png" / "000.png", compress_level=1)
    assert (a / "png" / "000.png").read_bytes() != (b / "png" / "000.png").read_bytes()
    assert compare(a, b) == []


def test_changed_pixels_are_caught(tmp_path: Path) -> None:
    a, b = tree(tmp_path / "a"), tree(tmp_path / "b")
    Image.new("RGBA", (4, 6), (255, 0, 0, 255)).save(b / "png" / "000.png")
    assert compare(a, b) == ["pixels differ: png/000.png"]


def test_changed_font_bytes_are_caught(tmp_path: Path) -> None:
    a, b = tree(tmp_path / "a"), tree(tmp_path / "b")
    (b / "fonts" / "otf" / "Font.otf").write_bytes(b"other bytes")
    assert compare(a, b) == ["bytes differ: fonts/otf/Font.otf"]


def test_missing_and_extra_files_are_caught(tmp_path: Path) -> None:
    a, b = tree(tmp_path / "a"), tree(tmp_path / "b")
    (b / "fonts" / "otf" / "Font.otf").unlink()
    (b / "extra.txt").write_text("x")
    assert compare(a, b) == [
        f"only in {a}: fonts/otf/Font.otf",
        f"only in {b}: extra.txt",
    ]


def test_exit_codes(tmp_path: Path) -> None:
    a = tree(tmp_path / "a")
    shutil.copytree(a, tmp_path / "b")
    assert main([str(a), str(tmp_path / "b")]) == 0
    (tmp_path / "b" / "index.json").write_text("{}")
    assert main([str(a), str(tmp_path / "b")]) == 1
