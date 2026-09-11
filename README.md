[Українська](README_UA.md) · [Symbol reference](docs/SYMBOLS.md) · [Developer docs](docs/DEVELOPERS.md)

# Betaflight OSD fonts for designers

The ten stock Betaflight OSD fonts, converted for use outside the goggles:
installable **OTF** and **TTF**, web **WOFF** and **WOFF2**, and all 256
characters as transparent **PNG** files.

Colour fonts, so the white glyph keeps its black outline over any footage.
Full Cyrillic, accented Latin, Greek, typographic punctuation, maths, currency
and box drawing -- all composed from each font's own shapes. For FPV
thumbnails, stream overlays, video titles and anything that should look like a
real drone OSD.

Source files are the MAX7456 `.mcm` fonts from betaflight-configurator.
[`bf2font.py`](bf2font.py) converts any other `.mcm` the same way.

![Betaflight OSD fonts betaflight, bold, clarity, default, digital, extra large, impact, impact mini, large and vision, rendered as text](docs/preview.png)

## The fonts

Cap height is in OSD pixels, out of an 18 pixel character cell.

| Font | Cap height | Notes |
| --- | --- | --- |
| `extra_large` | 16 | the biggest, fills the cell |
| `clarity` | 15 | large and clean, high contrast |
| `bold` | 12 | heavy, narrow |
| `impact` | 12 | heavy, wider |
| `vision` | 12 | same size as `impact`, its own letterforms |
| `betaflight` | 10 | slanted, the branded look |
| `impact_mini` | 10 | compact version of `impact` |
| `default` | 10 | thin stock font, smallest footprint |
| `large` | 10 | small letters with tall 15 pixel digits |
| `digital` | 9 | short, full width blocks, like a segmented display |

## Cyrillic

Full Cyrillic, in every font, at the usual codepoints.
Lowercase types as capitals, the same as Latin.

Each font's Cyrillic matches that font: `clarity` keeps clarity's weight,
`betaflight` keeps its slant.

![Cyrillic in four of the fonts](docs/cyrillic.png)

Font files only. The OSD itself cannot display Cyrillic.

## Everything else the OSD never had

The source fonts are ASCII and icons. These add the rest, drawn to each face's
own stroke weight, stem positions and slant:

| Set | What it covers |
| --- | --- |
| Accented Latin | `Latin-1` and the common `Latin Extended-A`: ÄÖÜ ÁÉÍÓÚ ÀÈÊ ÅØ ÑÇ ŁĄĆĘŃŚŹŻ ČŠŽŘĎŤŇĚŮ ĂÎȘȚ ĞİŞ ÐÞ |
| Greek | the full run of capitals, ΑΒΓΔ through ΧΨΩ |
| Punctuation | – — … « » ‹ › “ ” ‘ ’ „ • · ¿ ¡ ° ′ ″ § -- and `{ } $ ~` \`, which the source fonts spend on icons |
| Maths and currency | ± × ÷ − ≠ ≈ ≤ ≥ ∞ µ · € £ ¥ ¢ ₴ ₽ |
| Blocks | ─ │ ┼ ═ ║ ╬ and the rest of box drawing, █ ▓ ▒ ░, ▲ ▼ ◀ ▶ ● ○ ◆ ■ ★ ✓ ✗ |

![Accented Latin, punctuation, maths, box drawing and Greek in five of the fonts](docs/sets.png)

A few characters are spelled out rather than squeezed into one 12 pixel cell,
which is what an all-capitals face would do anyway: Æ types as AE, ß as SS,
™ as TM, № as N°, ½ as 1/2, © as (C).

## Symbols by name

Two thirds of a Betaflight font is icons. Type the name between colons and the
icon appears -- `:battery:`, `:home:`, `:arrow_n:`, `:rssi:`, `:flag:` -- in any
app with OpenType ligatures, which is browsers, macOS and Windows text, Adobe
and Affinity.

Arrows, the home symbol and degrees Celsius are also on their own standard
characters: ↑ ↓ ← → ↖ ↗ ↘ ↙ ⌂ ℃ ℉. Every icon keeps its `U+E000 + index`
codepoint as well.

**[The full symbol reference →](docs/SYMBOLS.md)**

## Download

Everything is in the repo, no build step. Grab
[the whole thing as a zip](https://github.com/volempdoge/betaflight-designer-fonts/archive/refs/heads/main.zip)
or open `output/<font>/`:

| | |
| --- | --- |
| `fonts/otf/`, `fonts/ttf/` | to install |
| `fonts/woff/`, `fonts/woff2/` | for the web |
| `png/` | all 256 characters, one transparent PNG each |
| `png/<set>/` | the composed characters, one PNG each, named by codepoint |
| `<font>_sheet.png` | the whole character set as a single 16×16 sheet |
| `<font>_<set>.png` | one sheet per composed set |
| `<font>.json` | the index: every character, set and symbol, with its codepoints |

Each format folder holds three families: the colour font, plus the flat
`Shadow` and `Fill` pair for apps that cannot read colour fonts.

## The black outline is part of the font

Type over video and the outline is already there, no layer styles.

Colour renders in every modern browser and in macOS and Windows text.
**Figma does not support colour fonts**, and Adobe support varies by app and
version. Without colour you get flat white letters, the right shape with no
outline.

### Figma and other apps without colour fonts

Stack two text layers: `Shadow` in black below, `Fill` in white above, same
text, size and position. All three families share their metrics, so they line
up exactly and the text stays editable.

## Typing

- Latin, Cyrillic, Greek, digits and punctuation work as usual. Lowercase
  types as capitals, in every script -- the fonts have no lowercase at all.
- `$`, `~` and `` ` `` are drawn characters here. In the source font those
  slots hold a checkered flag, a crosshair and an arrow; they are still there
  as `:flag:`, `:crosshair:` and `:arrow_s:`.
- Every character also sits at `U+E000 + index`, so `0x01` is `U+E001`. That is
  where the arrows, battery and signal icons, GPS and flight mode symbols and
  the logo tiles live. The sheet image and `output/<font>/<font>.json` show
  what is where.

Prefer bitmaps? Drop the PNGs onto the timeline or the canvas.

## Stand with Ukraine

Currently, you are either in the army or working for the army, thank you.
A reminder to donate to support Ukraine:
- https://savelife.in.ua/donate/
- https://prytulafoundation.org

## Legal Information

The original font files are taken directly from the [betaflight/betaflight-configurator](https://github.com/betaflight/betaflight-configurator) repository, which is distributed under the GNU General Public License v3.0.

In accordance with the terms of the original license, this repository and all its materials are also licensed under **GNU General Public License v3.0**.

The full text of the license is available in the `LICENSE` file in this repository.
