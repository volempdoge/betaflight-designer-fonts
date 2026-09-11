"""PNG slicing and the command line end to end."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import FONT_DIR
from PIL import Image

from bf2font import CHAR_H, CHAR_W, CHARS, Glyph, glyph_image, main, sheet_image

SOURCE = FONT_DIR / "default.mcm"


def test_glyph_image_colours(default_glyphs: list[Glyph]) -> None:
    glyph = default_glyphs[0x41]
    image = glyph_image(glyph, 1)
    assert image.size == (CHAR_W, CHAR_H)
    for y, row in enumerate(glyph.pixels):
        for x, value in enumerate(row):
            expected = {0: (0, 0, 0, 255), 2: (255, 255, 255, 255)}.get(
                value, (0, 0, 0, 0)
            )
            assert image.getpixel((x, y)) == expected, (x, y)


def test_glyph_image_scales_without_blurring(default_glyphs: list[Glyph]) -> None:
    image = glyph_image(default_glyphs[0x41], 4)
    assert image.size == (CHAR_W * 4, CHAR_H * 4)
    assert set(image.getchannel("A").tobytes()) <= {0, 255}, "no blending"


def test_sheet_is_a_16_by_16_grid(default_glyphs: list[Glyph]) -> None:
    sheet = sheet_image(default_glyphs, 2)
    assert sheet.size == (16 * CHAR_W * 2, 16 * CHAR_H * 2)


def run(*args: str) -> int:
    return main([str(SOURCE), *args])


def test_end_to_end(tmp_path: Path) -> None:
    assert run("-o", str(tmp_path), "--scale", "2") == 0
    out = tmp_path / "default"

    assert len(list((out / "png").glob("*.png"))) == CHARS
    assert Image.open(out / "png" / "065.png").size == (CHAR_W * 2, CHAR_H * 2)
    assert (out / "default_sheet.png").exists()

    for fmt in ("otf", "ttf", "woff", "woff2"):
        files = sorted(p.name for p in (out / "fonts" / fmt).iterdir())
        assert files == [
            f"BetaflightOSDDefault.{fmt}",
            f"BetaflightOSDDefaultFill.{fmt}",
            f"BetaflightOSDDefaultShadow.{fmt}",
        ], fmt


def test_json_index(tmp_path: Path) -> None:
    assert run("-o", str(tmp_path), "--formats", "woff2") == 0
    data = json.loads((tmp_path / "default" / "default.json").read_text())
    assert data["families"] == [
        "Betaflight OSD Default",
        "Betaflight OSD Default Shadow",
        "Betaflight OSD Default Fill",
    ]
    assert len(data["characters"]) == CHARS
    entry = data["characters"][0x41]
    assert entry == {
        "index": 0x41,
        "png": "png/065.png",
        "codepoint": "U+E041",
        "ascii": "A",
        "blank": False,
    }


def test_selecting_formats_and_skipping_layer_fonts(tmp_path: Path) -> None:
    assert run("-o", str(tmp_path), "--formats", "woff2", "--no-layer-fonts") == 0
    fonts = tmp_path / "default" / "fonts"
    assert [d.name for d in fonts.iterdir()] == ["woff2"]
    assert [p.name for p in (fonts / "woff2").iterdir()] == [
        "BetaflightOSDDefault.woff2"
    ]


def test_custom_family_name(tmp_path: Path) -> None:
    assert run("-o", str(tmp_path), "--formats", "otf", "--family", "My OSD") == 0
    assert (tmp_path / "default" / "fonts" / "otf" / "MyOSD.otf").exists()


@pytest.mark.parametrize(
    "args",
    [
        ("--formats", "eot"),
        ("--scale", "0"),
    ],
)
def test_argument_validation(tmp_path: Path, args: tuple[str, ...]) -> None:
    with pytest.raises(SystemExit):
        run("-o", str(tmp_path), *args)


def test_family_needs_a_single_source(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        main([str(SOURCE), str(SOURCE), "-o", str(tmp_path), "--family", "X"])


def test_builds_are_reproducible(tmp_path: Path) -> None:
    """Pinning SOURCE_DATE_EPOCH keeps repeated runs byte for byte identical."""
    first, second = tmp_path / "a", tmp_path / "b"
    for out in (first, second):
        assert main([str(SOURCE), "-o", str(out), "--formats", "otf,woff2"]) == 0
    built = sorted(p.relative_to(first) for p in first.rglob("*") if p.is_file())
    assert built, "nothing was produced"
    for rel in built:
        assert (first / rel).read_bytes() == (second / rel).read_bytes(), rel
