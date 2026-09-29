# Betaflight OSD Fonts

Betaflight OSD fonts, out of the goggles: all ten fonts that come with
Betaflight Configurator, converted for use outside the drone. Installable OTF
and TTF, web WOFF and WOFF2, and every one of the 256 characters as a
transparent PNG. For FPV
thumbnails, stream overlays, video titles and anything that should look like a
real drone OSD. Free under GPL 3.0.

- Website: {{SITE}}/
- Download everything (.zip): {{REPO}}/archive/refs/heads/main.zip
- Source: {{REPO}}

## The fonts

Cap height is in OSD pixels, out of an 18 pixel character cell. Each font is
also available as WOFF; swap the extension in any link below.

| Font | Family name | Cap height | Look | Download |
| --- | --- | --- | --- | --- |
| `extra_large` | Betaflight OSD Extra Large | 16 | The biggest one, fills the whole cell | [OTF]({{RAW}}/output/extra_large/fonts/otf/BetaflightOSDExtraLarge.otf) · [TTF]({{RAW}}/output/extra_large/fonts/ttf/BetaflightOSDExtraLarge.ttf) · [WOFF2]({{RAW}}/output/extra_large/fonts/woff2/BetaflightOSDExtraLarge.woff2) |
| `clarity` | Betaflight OSD Clarity | 15 | Large and clean with high contrast | [OTF]({{RAW}}/output/clarity/fonts/otf/BetaflightOSDClarity.otf) · [TTF]({{RAW}}/output/clarity/fonts/ttf/BetaflightOSDClarity.ttf) · [WOFF2]({{RAW}}/output/clarity/fonts/woff2/BetaflightOSDClarity.woff2) |
| `bold` | Betaflight OSD Bold | 12 | Heavy and narrow | [OTF]({{RAW}}/output/bold/fonts/otf/BetaflightOSDBold.otf) · [TTF]({{RAW}}/output/bold/fonts/ttf/BetaflightOSDBold.ttf) · [WOFF2]({{RAW}}/output/bold/fonts/woff2/BetaflightOSDBold.woff2) |
| `impact` | Betaflight OSD Impact | 12 | Heavy and a bit wider | [OTF]({{RAW}}/output/impact/fonts/otf/BetaflightOSDImpact.otf) · [TTF]({{RAW}}/output/impact/fonts/ttf/BetaflightOSDImpact.ttf) · [WOFF2]({{RAW}}/output/impact/fonts/woff2/BetaflightOSDImpact.woff2) |
| `vision` | Betaflight OSD Vision | 12 | The size of impact with its own letterforms | [OTF]({{RAW}}/output/vision/fonts/otf/BetaflightOSDVision.otf) · [TTF]({{RAW}}/output/vision/fonts/ttf/BetaflightOSDVision.ttf) · [WOFF2]({{RAW}}/output/vision/fonts/woff2/BetaflightOSDVision.woff2) |
| `betaflight` | Betaflight OSD Betaflight | 10 | Slanted, the branded look | [OTF]({{RAW}}/output/betaflight/fonts/otf/BetaflightOSDBetaflight.otf) · [TTF]({{RAW}}/output/betaflight/fonts/ttf/BetaflightOSDBetaflight.ttf) · [WOFF2]({{RAW}}/output/betaflight/fonts/woff2/BetaflightOSDBetaflight.woff2) |
| `impact_mini` | Betaflight OSD Impact Mini | 10 | A compact take on impact | [OTF]({{RAW}}/output/impact_mini/fonts/otf/BetaflightOSDImpactMini.otf) · [TTF]({{RAW}}/output/impact_mini/fonts/ttf/BetaflightOSDImpactMini.ttf) · [WOFF2]({{RAW}}/output/impact_mini/fonts/woff2/BetaflightOSDImpactMini.woff2) |
| `default` | Betaflight OSD Default | 10 | The thin stock font, smallest of all | [OTF]({{RAW}}/output/default/fonts/otf/BetaflightOSDDefault.otf) · [TTF]({{RAW}}/output/default/fonts/ttf/BetaflightOSDDefault.ttf) · [WOFF2]({{RAW}}/output/default/fonts/woff2/BetaflightOSDDefault.woff2) |
| `large` | Betaflight OSD Large | 10 | Small letters with tall 15 pixel digits | [OTF]({{RAW}}/output/large/fonts/otf/BetaflightOSDLarge.otf) · [TTF]({{RAW}}/output/large/fonts/ttf/BetaflightOSDLarge.ttf) · [WOFF2]({{RAW}}/output/large/fonts/woff2/BetaflightOSDLarge.woff2) |
| `digital` | Betaflight OSD Digital | 9 | Wide blocks like a segment display | [OTF]({{RAW}}/output/digital/fonts/otf/BetaflightOSDDigital.otf) · [TTF]({{RAW}}/output/digital/fonts/ttf/BetaflightOSDDigital.ttf) · [WOFF2]({{RAW}}/output/digital/fonts/woff2/BetaflightOSDDigital.woff2) |

## What is in each font's folder

Everything lives in the repository under `output/<font>/`, no build step:

| Path | What it is |
| --- | --- |
| `fonts/otf/`, `fonts/ttf/` | to install |
| `fonts/woff/`, `fonts/woff2/` | for the web |
| `png/000.png` … `png/255.png` | all 256 characters, one transparent PNG each, 8× the OSD pixel |
| `png/<set>/<codepoint>.png` | the composed characters (`cyrillic`, `greek`, `accents`, `punctuation`, `blocks`), named by codepoint |
| `<font>_sheet.png` | the whole character set as one 16×16 sheet |
| `<font>_<set>.png` | one sheet per composed set |
| `<font>.json` | the index: every character, set and symbol, with its codepoints |

Each format folder holds three families:

- `BetaflightOSD<Name>`: the colour font, white glyph with its black outline
- `BetaflightOSD<Name>Shadow`: the outline only, flat
- `BetaflightOSD<Name>Fill`: the white glyph only, flat

A direct file URL is
`{{RAW}}/output/<font>/fonts/<format>/BetaflightOSD<Name>[Shadow|Fill].<format>`.

## The black outline is part of the font

Betaflight characters come in two colours, a white glyph with a black outline,
so text over video already has its outline and needs no extra effects. These
are colour (COLR) fonts that keep it.

- Works: every modern browser, and ordinary text on macOS and Windows.
- Depends on the app: Figma has no colour font support at all, and in Adobe it
  changes from app to app and from version to version. Without colour support
  you get flat white letters, the right shape with no outline.
- Workaround: stack two text layers, `Shadow` in black below and `Fill` in
  white above, same text, size and position. All three families share their
  metrics, so the layers land together and the text stays editable.

## Everything else the OSD never had

The source fonts are only ASCII and icons, so this is not a port: Cyrillic,
Greek, accented Latin, punctuation and maths were drawn as new characters, each
one from the shapes the font already has, so a heavy face gets heavy
punctuation and a slanted face gets slanted accents.

| Set | What it covers |
| --- | --- |
| Cyrillic | the full alphabet, including Ukrainian, at the usual codepoints |
| Accented Latin | Latin-1 and the common Latin Extended-A: ÄÖÜ ÁÉÍÓÚ ÀÈÊ ÅØ ÑÇ ŁĄĆĘŃŚŹŻ ČŠŽŘĎŤŇĚŮ ĂÎȘȚ ĞİŞ ÐÞ |
| Greek | the full run of capitals, ΑΒΓΔ through ΧΨΩ |
| Punctuation | – — … « » ‹ › “ ” ‘ ’ „ • · ¿ ¡ ° ′ ″ § and `$ ~` \`, which the source fonts spend on icons, plus `{ }` |
| Maths and currency | ± × ÷ − ≠ ≈ ≤ ≥ ∞ µ · € £ ¥ ¢ ₴ ₽ |
| Blocks | ─ │ ┼ ═ ║ ╬ and the rest of box drawing, █ ▓ ▒ ░, ▲ ▼ ◀ ▶ ● ○ ◆ ■ ★ ✓ ✗ |

A few characters are spelled out rather than squeezed into one 12 pixel cell:
Æ types as AE, ß as SS, ™ as TM, № as N°, ½ as 1/2, © as (C).

The OSD itself cannot show any of this, but the font files can.

## Typing

- Latin, Cyrillic, Greek, digits and punctuation work as usual. Lowercase types
  as capitals, in every script: the fonts have no lowercase at all.
- `$`, `~` and `` ` `` are drawn characters here. In the source font those slots
  hold a checkered flag, a crosshair and an arrow; they are still there as
  `:flag:`, `:crosshair:` and `:arrow_s:`.
- Every character also sits at `U+E000` plus its index, so index `0x01` is
  `U+E001`. That is where the arrows, the battery and signal icons, the GPS and
  flight mode marks and the logo tiles are.

## Symbols by name

Two thirds of a Betaflight font is icons. Type the name between colons and the
icon appears, for example `:battery:`, `:home:`, `:arrow_n:`, `:rssi:`,
`:flag:`, in any app with OpenType ligatures: browsers, macOS and Windows
text, Adobe and Affinity.

Arrows, the home symbol and degrees are also on their own standard characters:
↑ ↓ ← → ↖ ↗ ↘ ↙ ⌂ ℃ ℉.

Every name, index and codepoint: [the full symbol reference]({{RAW}}/docs/SYMBOLS.md).

## On a web page

```css
@font-face {
  font-family: "Betaflight OSD Clarity";
  src: url("BetaflightOSDClarity.woff2") format("woff2");
  font-display: swap;
}

.osd {
  font-family: "Betaflight OSD Clarity", monospace;
  /* The ligatures are on by default; this only makes it explicit. */
  font-variant-ligatures: common-ligatures;
}
```

## Converting your own

The source files are the MAX7456 `.mcm` fonts from
[betaflight-configurator](https://github.com/betaflight/betaflight-configurator).
`bf2font.py` in the repository converts any other `.mcm` font the same way; see
the [developer docs]({{RAW}}/docs/DEVELOPERS.md).

## Licence

The original `.mcm` fonts come from betaflight-configurator, distributed under
the GNU General Public License v3.0. Following that licence, this repository
and everything in it is GPL 3.0 as well.

Created by Volodymyr Myronenko, [@volempdoge](https://github.com/volempdoge).

## Stand with Ukraine

A reminder to donate and support Ukraine: <https://savelife.in.ua/donate/>,
<https://prytulafoundation.org>.

## Other languages

[English]({{SITE}}/) · [Українська]({{SITE}}/uk/) · [Español]({{SITE}}/es/) ·
[Français]({{SITE}}/fr/) · [中文]({{SITE}}/zh/) · [日本語]({{SITE}}/ja/)
