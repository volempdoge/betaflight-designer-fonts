[← README](../README.md) · [Symbol reference](SYMBOLS.md) · [Українською](DEVELOPERS_UA.md)

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
| `--sets` | which composed sets to build: any subset of `cyrillic,accents,greek,punctuation,blocks`, empty for none |

Output per source file:

```
output/<name>/
├── png/000.png … 255.png    one PNG per character, transparent background
├── png/<set>/0410.png …     one PNG per composed character, named by codepoint
├── <name>_sheet.png         16×16 atlas of the whole set
├── <name>_<set>.png         one atlas per composed set
├── <name>.json              characters, composed sets, spelled-out characters, symbols
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

## Composed character sets

The source font is 256 characters: ASCII and OSD icons. Everything else is
drawn from the shapes that font already has, never from constants, so a heavy
face gets heavy punctuation and a slanted face gets slanted accents. It all
lives in `scripts/`; `bf2font.py` at the root is the only entry point.

| Module | What it adds |
| --- | --- |
| `scripts/shapes.py` | the primitives: `Geometry`, `render`, `box`, `ring`, `line`, `chevron`, `triangle`, `wave` |
| `scripts/cyrillic.py` | 37 Cyrillic capitals |
| `scripts/accents.py` | 67 accented Latin capitals, plus Ð Đ Ø Ł Þ |
| `scripts/greek.py` | 24 Greek capitals |
| `scripts/punctuation.py` | dashes, quotes, angle quotes, maths, currency, and the five ASCII slots the source font leaves to icons or blanks |
| `scripts/blocks.py` | box drawing, half blocks, shades, markers |

Each module exposes the same two entry points, which is all `bf2font.py` knows
about it:

```python
cores(latin)  -> {codepoint: set of white cells}
glyphs(latin) -> {codepoint: 12×18 pixels, outline included}
```

`Geometry` measures one font off its own Latin capitals: stroke weight, the
columns its stems sit in, the rows its bars sit on, and the staircase of its
slant. A glyph built from those numbers belongs to the face.

### What the cell forces

The cell is 12×18 with a one pixel border reserved for the outline, so a
composed glyph has 10×16 to work in. Three rules fall out of that:

- **Marks go above the cap line.** Every one of the ten faces leaves at least
  three rows there, so a mark is never squeezed. The ring on Å wants a third
  row: where the face has one to spare the letter drops a row to make room,
  and on the tallest face the ring stands on two rows instead, open at the
  bottom so it keeps a counter.
- **Marks below the baseline raise the letter.** `extra_large` reaches the
  bottom of the cell, so Ç Ę Ș lift by a row or two rather than lose the mark.
  It is the same trick the Cyrillic uses for the spur on Ц and Щ.
- **Blocks run to the wall on purpose.** Box drawing has to join up with the
  cell next to it, so `scripts/blocks.py` is the one set that ignores the
  border.

### Characters that are spelled out

Æ, ß, ©, ™, № and the vulgar fractions do not fit one 12 pixel cell and would
be unreadable if they did. Each has a `FOLDS` entry giving the characters it
stands for, and GSUB expands it: `Æ` becomes A E, `№` becomes N °. The
codepoint still carries a copy of the first character's outline, so a renderer
that ignores GSUB shows an A rather than a hole.

## Cyrillic

`scripts/cyrillic.py` adds 37 capitals that Betaflight does not ship. They are
not drawn from scratch: each one is assembled from that font's own Latin
shapes, so the weight and proportions come along for free.

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
shows flat single-colour letters. For those, the flat families are built by
default (`--no-layer-fonts` skips them) and each font also ships as two flat
families: `Shadow` carries the silhouette
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
- Lowercase folds onto the capitals in every script, from each set's
  `LOWERCASE` table.
- Icons that are also a standard character get that character too, from
  `symbols.ALIASES`: the compass arrows at `U+2190`-`U+2199`, home at `U+2302`,
  ℃ and ℉, the GPS minute and second marks as the prime and double prime. A
  drawn glyph always wins over an alias.
- `$`, `~` and `` ` `` hold a checkered flag, a crosshair and an arrow in the
  source font. `scripts/punctuation.py` draws the characters those codepoints
  are named after; the icons keep their names and `U+E0xx` codepoints.

## Symbols and OpenType features

`scripts/symbols.py` is the catalogue: every non-letter character of the source
font, with a name, a group and any standard codepoint it deserves. Names follow
`osd_symbols.h` in the Betaflight firmware where the drawing matches it, and
what the glyph actually draws where it does not -- the bundled fonts predate
some of the moves in that header, so `0x70` is still the on-time icon rather
than the speed one.

Two features are built with `feaLib`:

| Feature | What it does |
| --- | --- |
| `liga` | `:battery:` and the other 189 names become their icon |
| `ccmp` | the spelled-out characters expand |

Ligature components come from the cmap of the characters actually typed, so
`:sat_left:` works whether `a-z` are folded or literal, and the rules never fire on
text like `12:30:45` because every one of them starts and ends with a colon.
`--no-ascii-cmap` builds no features at all: without ASCII there is no colon
to type.

`docs/SYMBOLS.md` is generated from the catalogue:

```bash
uv run tools/symbol_index.py   # docs/SYMBOLS.md, docs/SYMBOLS_UA.md, docs/logo.png
uv run tools/specimen.py       # docs/sets.png
```

`docs/social-preview.png` is not generated. It is the image uploaded by hand
under Settings -> General -> Social preview, kept here so the repository keeps
a copy of what it shows.

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

`tests/test_sets.py` holds the rules every composed set has to keep on all ten
fonts: nothing blank, nothing on the cell wall, no two codepoints drawing the
same shape, an accented letter containing the whole letter it is built from,
and every `NAMES` entry matching what Unicode calls that codepoint -- which is
what catches a mistyped codepoint before anyone types it.

`tests/test_symbols.py` shapes text with HarfBuzz, so the ligatures and the
spelled-out characters are tested the way a renderer will actually run them.

Rendering is the one thing tests do not cover. Pillow's `ImageFont` with
`embedded_color=True` rasterises `COLR`/`CPAL` through FreeType, which is a
quick way to eyeball layer and palette mistakes.
