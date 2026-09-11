"""The OSD icons the .mcm fonts carry, named.

Two thirds of a Betaflight font is not text: battery states, satellite dishes,
compass arrows, the attitude ladder, unit labels and, in the last 96 slots, the
Betaflight logo cut into tiles. In the source font they are reachable only by
character index, which is why they are addressed here by name instead.

Every icon gets three ways in:

* a ligature, so typing `:battery:` produces the icon,
* a private use codepoint at U+E000 plus the index, which never changes,
* for the icons that have an obvious standard character -- arrows, the home
  symbol, the degree Celsius sign -- that character too.

Names follow `osd_symbols.h` in the Betaflight firmware where the drawing
matches it. Where it does not (the bundled fonts predate some of the moves in
that header, and 0x70 still holds the on-time icon) the name follows what the
glyph actually draws.
"""

from __future__ import annotations

from dataclasses import dataclass, field

LOGO_START = 0xA0
LOGO_COLUMNS = 24  # the logo is 24 tiles wide and 4 tall


@dataclass(frozen=True)
class Symbol:
    """One icon in the source font."""

    index: int
    name: str
    group: str
    label: str
    unicode: tuple[int, ...] = field(default=())


def _logo() -> list[Symbol]:
    return [
        Symbol(
            index=LOGO_START + i,
            name=f"logo_{i:02d}",
            group="logo",
            label=f"Betaflight logo tile, row {i // LOGO_COLUMNS + 1} "
            f"column {i % LOGO_COLUMNS + 1}",
        )
        for i in range(0x100 - LOGO_START)
    ]


SYMBOLS: list[Symbol] = [
    Symbol(0x01, "rssi", "telemetry", "RSSI bars", (0x1F4F6,)),
    Symbol(0x02, "ah_right", "horizon", "artificial horizon, right marker"),
    Symbol(0x03, "ah_left", "horizon", "artificial horizon, left marker"),
    Symbol(0x04, "throttle", "telemetry", "throttle"),
    Symbol(0x05, "over_home", "navigation", "directly over home"),
    Symbol(0x06, "volt", "power", "volts"),
    Symbol(0x07, "mah", "power", "milliamp hours"),
    Symbol(0x08, "stick_high", "sticks", "stick overlay, high"),
    Symbol(0x09, "stick_mid", "sticks", "stick overlay, middle"),
    Symbol(0x0A, "stick_low", "sticks", "stick overlay, low"),
    Symbol(0x0B, "stick_centre", "sticks", "stick overlay, centre"),
    Symbol(0x0C, "metres", "units", "metres"),
    Symbol(0x0D, "fahrenheit", "units", "degrees Fahrenheit", (0x2109,)),
    Symbol(0x0E, "celsius", "units", "degrees Celsius", (0x2103,)),
    Symbol(0x0F, "feet", "units", "feet"),
    Symbol(0x10, "blackbox", "status", "blackbox logging"),
    Symbol(0x11, "home", "navigation", "home", (0x2302,)),
    Symbol(0x12, "rpm", "telemetry", "rotations per minute"),
    Symbol(0x13, "ah_decoration", "horizon", "attitude ladder tick"),
    Symbol(0x14, "roll", "telemetry", "roll"),
    Symbol(0x15, "pitch", "telemetry", "pitch"),
    Symbol(0x16, "stick_vertical", "sticks", "stick overlay, vertical rule"),
    Symbol(0x17, "stick_horizontal", "sticks", "stick overlay, horizontal rule"),
    Symbol(0x18, "heading_n", "navigation", "heading north"),
    Symbol(0x19, "heading_s", "navigation", "heading south"),
    Symbol(0x1A, "heading_e", "navigation", "heading east"),
    Symbol(0x1B, "heading_w", "navigation", "heading west"),
    Symbol(0x1C, "heading_divider", "navigation", "heading tape divider"),
    Symbol(0x1D, "heading_line", "navigation", "heading tape line"),
    Symbol(0x1E, "sat_left", "navigation", "satellite dish, left half"),
    Symbol(0x1F, "sat_right", "navigation", "satellite dish, right half"),
    Symbol(0x24, "flag", "status", "checkered flag", (0x1F3C1,)),
    Symbol(0x60, "arrow_s", "arrows", "arrow, south", (0x2193,)),
    Symbol(0x61, "arrow_sse", "arrows", "arrow, south south east"),
    Symbol(0x62, "arrow_se", "arrows", "arrow, south east", (0x2198,)),
    Symbol(0x63, "arrow_ese", "arrows", "arrow, east south east"),
    Symbol(0x64, "arrow_e", "arrows", "arrow, east", (0x2192,)),
    Symbol(0x65, "arrow_ene", "arrows", "arrow, east north east"),
    Symbol(0x66, "arrow_ne", "arrows", "arrow, north east", (0x2197,)),
    Symbol(0x67, "arrow_nne", "arrows", "arrow, north north east"),
    Symbol(0x68, "arrow_n", "arrows", "arrow, north", (0x2191,)),
    Symbol(0x69, "arrow_nnw", "arrows", "arrow, north north west"),
    Symbol(0x6A, "arrow_nw", "arrows", "arrow, north west", (0x2196,)),
    Symbol(0x6B, "arrow_wnw", "arrows", "arrow, west north west"),
    Symbol(0x6C, "arrow_w", "arrows", "arrow, west", (0x2190,)),
    Symbol(0x6D, "arrow_wsw", "arrows", "arrow, west south west"),
    Symbol(0x6E, "arrow_sw", "arrows", "arrow, south west", (0x2199,)),
    Symbol(0x6F, "arrow_ssw", "arrows", "arrow, south south west"),
    Symbol(0x70, "on_hours", "time", "time since power on, hours"),
    Symbol(0x71, "fly_hours", "time", "time since arming, hours"),
    Symbol(0x72, "ah_corner_left", "horizon", "horizon centre, left"),
    Symbol(0x73, "ah_corner_right", "horizon", "horizon centre, right"),
    Symbol(0x74, "ah_corner_low", "horizon", "horizon centre, lower"),
    Symbol(0x75, "arrow_small_up", "arrows", "small arrow, up", (0x25B4,)),
    Symbol(0x76, "arrow_small_down", "arrows", "small arrow, down", (0x25BE,)),
    Symbol(0x77, "arrow_small_right", "arrows", "small arrow, right", (0x25B8,)),
    Symbol(0x78, "arrow_small_left", "arrows", "small arrow, left", (0x25C2,)),
    Symbol(0x79, "prev_lap", "time", "previous lap"),
    Symbol(0x7A, "temperature", "telemetry", "temperature", (0x1F321,)),
    Symbol(0x7C, "ladder", "horizon", "altitude ladder rule"),
    Symbol(0x7E, "crosshair", "horizon", "crosshair", (0x2316,)),
    Symbol(0x7F, "altitude", "telemetry", "altitude"),
    *[
        Symbol(0x80 + i, f"ah_bar_{i}", "horizon", f"attitude ladder rung {i}")
        for i in range(9)
    ],
    Symbol(0x89, "latitude", "navigation", "latitude"),
    Symbol(0x8A, "progress_start", "progress", "progress bar, left cap"),
    Symbol(0x8B, "progress_full", "progress", "progress bar, filled"),
    Symbol(0x8C, "progress_half", "progress", "progress bar, half filled"),
    Symbol(0x8D, "progress_empty", "progress", "progress bar, empty"),
    Symbol(0x8E, "progress_end", "progress", "progress bar, right cap"),
    Symbol(0x8F, "progress_close", "progress", "progress bar, closed end"),
    Symbol(0x90, "batt_full", "power", "battery, full"),
    *[
        Symbol(0x91 + i, f"batt_{5 - i}", "power", f"battery, {5 - i} of 6")
        for i in range(5)
    ],
    Symbol(0x96, "batt_empty", "power", "battery, empty"),
    Symbol(0x97, "battery", "power", "battery", (0x1F50B,)),
    Symbol(0x98, "longitude", "navigation", "longitude"),
    Symbol(0x99, "ft_per_s", "units", "feet per second"),
    Symbol(0x9A, "amp", "power", "amps"),
    Symbol(0x9B, "on_minutes", "time", "time since power on, minutes"),
    Symbol(0x9C, "fly_minutes", "time", "time since arming, minutes"),
    Symbol(0x9D, "mph", "units", "miles per hour"),
    Symbol(0x9E, "kph", "units", "kilometres per hour"),
    Symbol(0x9F, "m_per_s", "units", "metres per second"),
    *_logo(),
]

BY_INDEX: dict[int, Symbol] = {symbol.index: symbol for symbol in SYMBOLS}
BY_NAME: dict[str, Symbol] = {symbol.name: symbol for symbol in SYMBOLS}

# Codepoints that should reach a character the font already has. The primes are
# the OSD's own GPS minute and second marks, which are exactly that shape.
ALIASES: dict[int, int] = {
    **{cp: symbol.index for symbol in SYMBOLS for cp in symbol.unicode},
    0x2032: 0x27,
    0x2033: 0x22,
}


def ligatures() -> dict[str, int]:
    """`:name:` -> character index, for the font's ligature table."""
    return {f":{symbol.name}:": symbol.index for symbol in SYMBOLS}
