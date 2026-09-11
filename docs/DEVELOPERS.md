[← README](../README.md) · [Українською](DEVELOPERS_UA.md)

# Developer notes

How [`bf2font.py`](../bf2font.py) turns a Betaflight `.mcm` file into PNGs and
font files, and how to run it on your own fonts.

## Running it

Dependencies are managed with [uv](https://docs.astral.sh/uv/). The script also
carries inline PEP 723 metadata, so it runs standalone from anywhere.

```bash
uv run bf2font.py original_fonts/default.mcm
```

```bash
uv run bf2font.py original_fonts/*.mcm -o output --scale 16
```

| Option | Meaning |
| --- | --- |
| `-o, --output` | output directory (default `output`) |
| `-s, --scale` | PNG pixel scale; 1 OSD pixel = N image pixels (default `8`, so 96×144 per character) |
| `--formats` | any subset of `otf,ttf,woff,woff2` |
| `--family` | exact family name, single source file only |
| `--family-prefix` | prefix for the derived name (default `Betaflight OSD`) |
| `--literal-ascii` | keep `a-z` on their own symbol slots instead of folding onto uppercase |
| `--no-ascii-cmap` | map characters only at `U+E000 + index` |
| `--no-layer-fonts` | skip the flat `Shadow` and `Fill` families |

Output per source file:

```
output/<name>/
├── png/000.png … 255.png    one PNG per character, transparent background
├── <name>_sheet.png         16×16 atlas of the whole set
├── <name>.json              index → PNG path, codepoint, ASCII, blank flag
└── fonts/
    ├── otf/                 <Family>.otf, <Family>Shadow.otf, <Family>Fill.otf
    ├── ttf/                 same three families
    ├── woff/
    └── woff2/
```

## The `.mcm` format

A MAX7456 character-memory dump: the line `MAX7456`, then 16384 lines of eight
binary digits, which is 256 characters × 64 bytes. Each character uses the
first 54 bytes as 12×18 pixels at two bits each, row by row. The remaining 10
bytes are padding (`0x55`).

| Value | Pixel |
| --- | --- |
| `0b00` | black |
| `0b10` | white |
| `0b01`, `0b11` | transparent |

That two-bit encoding is why a Betaflight glyph is white with a black outline,
and why a single-colour font cannot represent it faithfully.

## Pixels → outlines

Each character produces two pixel sets: the **silhouette** (black + white) and
the **white pixels** alone.

Both are vectorised by boundary tracing. Every cell contributes the unit edges
that face a cell outside the set, oriented so the filled area is on the left.
Chaining those edges yields counter-clockwise outer contours and clockwise
holes, which is correct under the non-zero fill rule. Where two cells meet only
at a corner, several edges leave the same vertex, so the traversal takes the
sharpest right turn and loops never cross. Collinear points are dropped
afterwards.

TrueType's contour direction is the opposite of PostScript's, so contours are
reversed when building `glyf`.

## Cyrillic

`cyrillic.py` adds 37 capitals that Betaflight does not ship. They are not
drawn from scratch: each one is assembled from that font's own Latin shapes, so
the weight and proportions come along for free.

- 14 letters are a Latin glyph as it stands (А В Е І К М Н О Р С Т Х У, and З
  from the digit three), 2 are one flipped left to right (И from N, Я from R).
- The rest are built from parts the font already has: Г is the top bar plus a
  stem, П adds the second stem, Ш the third, Щ and Ц a spur, Ф is О with a
  stem through it, Ж is Х with the same.
- Only the white core is composed; `outline()` derives the black outline.

Three things the fonts force:

- **Width.** Three stems and two gaps do not fit the Latin box in several
  faces, so Ж Ш Щ Ю Ы get a wider one. Without it the stems merge into a blob.
- **Slant.** betaflight is italic. Composition happens on a straightened copy
  and the result is leant back, because parts taken from different letters
  meet at the wrong offsets otherwise, and a mirrored letter would tip the
  wrong way.
- **Fallbacks.** Where a shape cannot work, a letter takes a second form: Ж
  becomes three stems joined at the waist when the arms would swallow the
  centre stem, and З is drawn rather than borrowed where digits are taller
  than capitals.

None of this reaches the `.mcm` files: 222 of the 256 slots are taken, so the
alphabet does not fit, and the OSD cannot display it either.

## Colour glyphs

Colour comes from `COLR` v0 / `CPAL`, with a two-entry palette: black and white.
Each character is three glyphs:

| Glyph | Contents |
| --- | --- |
| `bfXX` | silhouette, the base glyph drawn by renderers that ignore `COLR` |
| `bfXX.black` | silhouette, painted with palette index 0 |
| `bfXX.white` | white pixels only, palette index 1, drawn on top |

The white layer sits on top of a **full** black silhouette rather than next to
black-only shapes. Abutting fills of different colours leave anti-aliasing
hairlines along the seam; overlapping them does not.

Apps that cannot read `COLR` draw the base glyph instead, which is why Figma
shows flat single-colour letters. For those, `--layer-fonts` is on by default
and each font also ships as two flat families: `Shadow` carries the silhouette
in every glyph, `Fill` carries only the white pixels. They are built from the
same outlines and metrics as the colour font, so stacking them as two text
layers reproduces it exactly.

`COLR`/`CPAL` are independent of the outline format, so the same construction is
used for both the CFF `.otf` and the `glyf` `.ttf`. The web files are that TTF
wrapped as WOFF and WOFF2, since `glyf` outlines have the broader colour-font
support of the two.

## Metrics

| | |
| --- | --- |
| Units per em | 1800 (100 units per OSD pixel) |
| Advance width | 1200 (12 pixels), monospaced |
| Ascender / descender | 1400 and -400, with the 18-pixel cell between them |

`hmtx` left side bearings are set from each glyph's real `xMin`. TrueType
positions glyphs using the left side bearing, so a flat `lsb` of 0 shifts every
glyph sideways.

## Character map

- `U+E000 + index` reaches all 256 characters, always.
- `0x20-0x7E` are additionally mapped to their ASCII codepoints, plus `U+00A0`
  to the blank.
- `a-z` are folded onto the uppercase glyphs, because Betaflight has no
  lowercase and those slots hold arrows and symbols. `--literal-ascii` keeps
  them on the raw slots. Either way the symbols stay reachable through their
  `U+E0xx` codepoints.

## Working on the script

```bash
uv sync --group dev
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run mypy
```

CI runs the same three on every push: lint (ruff and mypy), tests on Python 3.10
and 3.14, and a build job that regenerates every bundled font and compares the
result against the committed `output/` with `tools/compare_output.py`.

Fonts and the JSON index are compared byte for byte, which works because
`SOURCE_DATE_EPOCH` is pinned in the script and fontTools would otherwise stamp
`head.created` from the clock. PNGs are compared as decoded pixels instead:
Pillow's platform wheels bundle different zlib-ng builds, so the deflate stream
differs between macOS and Linux even when every pixel is identical.

## Verifying a change

The outlines are exactly invertible, so round-tripping is the core test:
`tests/conftest.py` rasterises the traced contours with the non-zero winding
rule at pixel centres and compares against the source bitmap. The suite does
that for both layers of all 256 characters across the ten bundled fonts, which
is 5120 outline sets.

The rest of the suite covers parsing, the character map, the metrics, and one
regression that outline comparison alone would miss: `hmtx` left side bearings
have to match `xMin`, otherwise TrueType shifts every glyph sideways.

Rendering is the one thing tests do not cover. Pillow's `ImageFont` with
`embedded_color=True` rasterises `COLR`/`CPAL` through FreeType, which is a
quick way to eyeball layer and palette mistakes.
