[Українська](README_UA.md) · [Developer docs](docs/DEVELOPERS.md)

# Betaflight OSD fonts for designers

The ten stock Betaflight OSD fonts, converted for use outside the goggles:
installable **OTF** and **TTF**, web **WOFF** and **WOFF2**, and all 256
characters as transparent **PNG** files.

They are colour fonts, so the white glyph keeps its black outline and stays
readable over any footage. Handy for FPV thumbnails, stream overlays, video
titles and anything that should look like a real drone OSD.

The sources are the MAX7456 `.mcm` fonts from betaflight-configurator.
[`bf2font.py`](bf2font.py) converts any other `.mcm` font the same way.

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

Betaflight characters are two-coloured, a white glyph with a black outline, so
they stay readable over any footage. That is preserved here, so typing over
video gives you the outline for free.

Colour works in every modern browser and in normal macOS / Windows text.
Design apps are uneven: **Figma does not support colour fonts at all**, and
Adobe support varies by app and version. An app that cannot read them draws the
character's silhouette in a single colour, so you get flat white letters with
the right shape and no outline.

### Figma, and other apps without colour fonts

Use the **Shadow** and **Fill** families next to each one. They are flat
single-colour fonts: `Shadow` is the whole character, `Fill` is only the white
part. Stack two text layers with the same text, size and position, `Shadow`
below in black and `Fill` above in white, and you get the OSD look with the
text still editable. The three families share their metrics, so the layers line
up exactly.

The PNGs work too, they just are not type any more.

## Typing

- `A-Z`, `0-9` and punctuation work as usual.
- Lowercase letters give you the same uppercase glyphs, since Betaflight has no
  lowercase.
- Every character also sits at `U+E000 + index`, so character `0x01` is
  `U+E001`. That is where the arrows, battery and signal icons, GPS and flight
  mode symbols and the Betaflight logo tiles are. The sheet image and
  `output/<font>/<font>.json` show what is where.

Prefer bitmaps? Drop the PNGs straight into the timeline or the canvas.

## Stand with Ukraine

Currently, you are either in the army or working for the army, thank you.
A reminder to donate to support Ukraine:
- https://savelife.in.ua/donate/
- https://prytulafoundation.org

## Legal Information

The original font files are taken directly from the [betaflight/betaflight-configurator](https://github.com/betaflight/betaflight-configurator) repository, which is distributed under the GNU General Public License v3.0.

In accordance with the terms of the original license, this repository and all its materials are also licensed under **GNU General Public License v3.0**.

The full text of the license is available in the `LICENSE` file in this repository.
