[Українська](README_UA.md) · [Developer docs](docs/DEVELOPERS.md)

# Betaflight OSD fonts for designers

The ten stock Betaflight OSD fonts, converted for use outside the goggles:
installable **OTF** and **TTF**, web **WOFF** and **WOFF2**, and all 256
characters as transparent **PNG** files.

Colour fonts, so the white glyph keeps its black outline over any footage.
Full Cyrillic. For FPV thumbnails, stream overlays, video titles and anything
that should look like a real drone OSD.

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

## Download

Everything is in the repo, no build step. Grab
[the whole thing as a zip](https://github.com/volempdoge/betaflight-designer-fonts/archive/refs/heads/main.zip)
or open `output/<font>/`:

| | |
| --- | --- |
| `fonts/otf/`, `fonts/ttf/` | to install |
| `fonts/woff/`, `fonts/woff2/` | for the web |
| `png/` | all 256 characters, one transparent PNG each |
| `<font>_sheet.png` | the whole character set as a single 16×16 sheet |

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

- Latin, Cyrillic, digits and punctuation work as usual. Lowercase types as
  capitals.
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
