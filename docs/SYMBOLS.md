[← README](../README.md) · [Developer docs](DEVELOPERS.md) · [Українською](SYMBOLS_UA.md)

# OSD symbols

The Betaflight fonts spend two thirds of their 256 characters on icons rather
than letters. Every one of them is reachable three ways: type its name between
colons, use its private use codepoint, or -- where the icon is also a standard
character -- type that character.

Images below are cut from `clarity`; every font draws the same set in its
own weight.

## Battery and power

| | Type | Also at | Private use |
| --- | --- | --- | --- |
| <img src="../output/clarity/png/006.png" width="24"> | `:volt:` | — | `U+E006` |
| <img src="../output/clarity/png/007.png" width="24"> | `:mah:` | — | `U+E007` |
| <img src="../output/clarity/png/144.png" width="24"> | `:batt_full:` | — | `U+E090` |
| <img src="../output/clarity/png/145.png" width="24"> | `:batt_5:` | — | `U+E091` |
| <img src="../output/clarity/png/146.png" width="24"> | `:batt_4:` | — | `U+E092` |
| <img src="../output/clarity/png/147.png" width="24"> | `:batt_3:` | — | `U+E093` |
| <img src="../output/clarity/png/148.png" width="24"> | `:batt_2:` | — | `U+E094` |
| <img src="../output/clarity/png/149.png" width="24"> | `:batt_1:` | — | `U+E095` |
| <img src="../output/clarity/png/150.png" width="24"> | `:batt_empty:` | — | `U+E096` |
| <img src="../output/clarity/png/151.png" width="24"> | `:battery:` | U+1F50B | `U+E097` |
| <img src="../output/clarity/png/154.png" width="24"> | `:amp:` | — | `U+E09A` |

## Telemetry

| | Type | Also at | Private use |
| --- | --- | --- | --- |
| <img src="../output/clarity/png/001.png" width="24"> | `:rssi:` | U+1F4F6 | `U+E001` |
| <img src="../output/clarity/png/004.png" width="24"> | `:throttle:` | — | `U+E004` |
| <img src="../output/clarity/png/018.png" width="24"> | `:rpm:` | — | `U+E012` |
| <img src="../output/clarity/png/020.png" width="24"> | `:roll:` | — | `U+E014` |
| <img src="../output/clarity/png/021.png" width="24"> | `:pitch:` | — | `U+E015` |
| <img src="../output/clarity/png/122.png" width="24"> | `:temperature:` | U+1F321 | `U+E07A` |
| <img src="../output/clarity/png/127.png" width="24"> | `:altitude:` | — | `U+E07F` |

## GPS and navigation

| | Type | Also at | Private use |
| --- | --- | --- | --- |
| <img src="../output/clarity/png/005.png" width="24"> | `:over_home:` | — | `U+E005` |
| <img src="../output/clarity/png/017.png" width="24"> | `:home:` | `⌂` U+2302 | `U+E011` |
| <img src="../output/clarity/png/024.png" width="24"> | `:heading_n:` | — | `U+E018` |
| <img src="../output/clarity/png/025.png" width="24"> | `:heading_s:` | — | `U+E019` |
| <img src="../output/clarity/png/026.png" width="24"> | `:heading_e:` | — | `U+E01A` |
| <img src="../output/clarity/png/027.png" width="24"> | `:heading_w:` | — | `U+E01B` |
| <img src="../output/clarity/png/028.png" width="24"> | `:heading_divider:` | — | `U+E01C` |
| <img src="../output/clarity/png/029.png" width="24"> | `:heading_line:` | — | `U+E01D` |
| <img src="../output/clarity/png/030.png" width="24"> | `:sat_left:` | — | `U+E01E` |
| <img src="../output/clarity/png/031.png" width="24"> | `:sat_right:` | — | `U+E01F` |
| <img src="../output/clarity/png/137.png" width="24"> | `:latitude:` | — | `U+E089` |
| <img src="../output/clarity/png/152.png" width="24"> | `:longitude:` | — | `U+E098` |

## Arrows

| | Type | Also at | Private use |
| --- | --- | --- | --- |
| <img src="../output/clarity/png/096.png" width="24"> | `:arrow_s:` | `↓` U+2193 | `U+E060` |
| <img src="../output/clarity/png/097.png" width="24"> | `:arrow_sse:` | — | `U+E061` |
| <img src="../output/clarity/png/098.png" width="24"> | `:arrow_se:` | `↘` U+2198 | `U+E062` |
| <img src="../output/clarity/png/099.png" width="24"> | `:arrow_ese:` | — | `U+E063` |
| <img src="../output/clarity/png/100.png" width="24"> | `:arrow_e:` | `→` U+2192 | `U+E064` |
| <img src="../output/clarity/png/101.png" width="24"> | `:arrow_ene:` | — | `U+E065` |
| <img src="../output/clarity/png/102.png" width="24"> | `:arrow_ne:` | `↗` U+2197 | `U+E066` |
| <img src="../output/clarity/png/103.png" width="24"> | `:arrow_nne:` | — | `U+E067` |
| <img src="../output/clarity/png/104.png" width="24"> | `:arrow_n:` | `↑` U+2191 | `U+E068` |
| <img src="../output/clarity/png/105.png" width="24"> | `:arrow_nnw:` | — | `U+E069` |
| <img src="../output/clarity/png/106.png" width="24"> | `:arrow_nw:` | `↖` U+2196 | `U+E06A` |
| <img src="../output/clarity/png/107.png" width="24"> | `:arrow_wnw:` | — | `U+E06B` |
| <img src="../output/clarity/png/108.png" width="24"> | `:arrow_w:` | `←` U+2190 | `U+E06C` |
| <img src="../output/clarity/png/109.png" width="24"> | `:arrow_wsw:` | — | `U+E06D` |
| <img src="../output/clarity/png/110.png" width="24"> | `:arrow_sw:` | `↙` U+2199 | `U+E06E` |
| <img src="../output/clarity/png/111.png" width="24"> | `:arrow_ssw:` | — | `U+E06F` |
| <img src="../output/clarity/png/117.png" width="24"> | `:arrow_small_up:` | `▴` U+25B4 | `U+E075` |
| <img src="../output/clarity/png/118.png" width="24"> | `:arrow_small_down:` | `▾` U+25BE | `U+E076` |
| <img src="../output/clarity/png/119.png" width="24"> | `:arrow_small_right:` | `▸` U+25B8 | `U+E077` |
| <img src="../output/clarity/png/120.png" width="24"> | `:arrow_small_left:` | `◂` U+25C2 | `U+E078` |

## Artificial horizon

| | Type | Also at | Private use |
| --- | --- | --- | --- |
| <img src="../output/clarity/png/002.png" width="24"> | `:ah_right:` | — | `U+E002` |
| <img src="../output/clarity/png/003.png" width="24"> | `:ah_left:` | — | `U+E003` |
| <img src="../output/clarity/png/019.png" width="24"> | `:ah_decoration:` | — | `U+E013` |
| <img src="../output/clarity/png/114.png" width="24"> | `:ah_corner_left:` | — | `U+E072` |
| <img src="../output/clarity/png/115.png" width="24"> | `:ah_corner_right:` | — | `U+E073` |
| <img src="../output/clarity/png/116.png" width="24"> | `:ah_corner_low:` | — | `U+E074` |
| <img src="../output/clarity/png/124.png" width="24"> | `:ladder:` | — | `U+E07C` |
| <img src="../output/clarity/png/126.png" width="24"> | `:crosshair:` | `⌖` U+2316 | `U+E07E` |
| <img src="../output/clarity/png/128.png" width="24"> | `:ah_bar_0:` | — | `U+E080` |
| <img src="../output/clarity/png/129.png" width="24"> | `:ah_bar_1:` | — | `U+E081` |
| <img src="../output/clarity/png/130.png" width="24"> | `:ah_bar_2:` | — | `U+E082` |
| <img src="../output/clarity/png/131.png" width="24"> | `:ah_bar_3:` | — | `U+E083` |
| <img src="../output/clarity/png/132.png" width="24"> | `:ah_bar_4:` | — | `U+E084` |
| <img src="../output/clarity/png/133.png" width="24"> | `:ah_bar_5:` | — | `U+E085` |
| <img src="../output/clarity/png/134.png" width="24"> | `:ah_bar_6:` | — | `U+E086` |
| <img src="../output/clarity/png/135.png" width="24"> | `:ah_bar_7:` | — | `U+E087` |
| <img src="../output/clarity/png/136.png" width="24"> | `:ah_bar_8:` | — | `U+E088` |

## Units

| | Type | Also at | Private use |
| --- | --- | --- | --- |
| <img src="../output/clarity/png/012.png" width="24"> | `:metres:` | — | `U+E00C` |
| <img src="../output/clarity/png/013.png" width="24"> | `:fahrenheit:` | `℉` U+2109 | `U+E00D` |
| <img src="../output/clarity/png/014.png" width="24"> | `:celsius:` | `℃` U+2103 | `U+E00E` |
| <img src="../output/clarity/png/015.png" width="24"> | `:feet:` | — | `U+E00F` |
| <img src="../output/clarity/png/153.png" width="24"> | `:ft_per_s:` | — | `U+E099` |
| <img src="../output/clarity/png/157.png" width="24"> | `:mph:` | — | `U+E09D` |
| <img src="../output/clarity/png/158.png" width="24"> | `:kph:` | — | `U+E09E` |
| <img src="../output/clarity/png/159.png" width="24"> | `:m_per_s:` | — | `U+E09F` |

## Time

| | Type | Also at | Private use |
| --- | --- | --- | --- |
| <img src="../output/clarity/png/112.png" width="24"> | `:on_hours:` | — | `U+E070` |
| <img src="../output/clarity/png/113.png" width="24"> | `:fly_hours:` | — | `U+E071` |
| <img src="../output/clarity/png/121.png" width="24"> | `:prev_lap:` | — | `U+E079` |
| <img src="../output/clarity/png/155.png" width="24"> | `:on_minutes:` | — | `U+E09B` |
| <img src="../output/clarity/png/156.png" width="24"> | `:fly_minutes:` | — | `U+E09C` |

## Progress bar

| | Type | Also at | Private use |
| --- | --- | --- | --- |
| <img src="../output/clarity/png/138.png" width="24"> | `:progress_start:` | — | `U+E08A` |
| <img src="../output/clarity/png/139.png" width="24"> | `:progress_full:` | — | `U+E08B` |
| <img src="../output/clarity/png/140.png" width="24"> | `:progress_half:` | — | `U+E08C` |
| <img src="../output/clarity/png/141.png" width="24"> | `:progress_empty:` | — | `U+E08D` |
| <img src="../output/clarity/png/142.png" width="24"> | `:progress_end:` | — | `U+E08E` |
| <img src="../output/clarity/png/143.png" width="24"> | `:progress_close:` | — | `U+E08F` |

## Stick overlay

| | Type | Also at | Private use |
| --- | --- | --- | --- |
| <img src="../output/clarity/png/008.png" width="24"> | `:stick_high:` | — | `U+E008` |
| <img src="../output/clarity/png/009.png" width="24"> | `:stick_mid:` | — | `U+E009` |
| <img src="../output/clarity/png/010.png" width="24"> | `:stick_low:` | — | `U+E00A` |
| <img src="../output/clarity/png/011.png" width="24"> | `:stick_centre:` | — | `U+E00B` |
| <img src="../output/clarity/png/022.png" width="24"> | `:stick_vertical:` | — | `U+E016` |
| <img src="../output/clarity/png/023.png" width="24"> | `:stick_horizontal:` | — | `U+E017` |

## Status

| | Type | Also at | Private use |
| --- | --- | --- | --- |
| <img src="../output/clarity/png/016.png" width="24"> | `:blackbox:` | — | `U+E010` |
| <img src="../output/clarity/png/036.png" width="24"> | `:flag:` | U+1F3C1 | `U+E024` |

## The logo

The last 96 characters are the Betaflight logo, cut into tiles 24 wide and 4 tall, in reading order: `:logo_00:` is the top left tile, `:logo_95:` the bottom right. Set them on consecutive lines with no line spacing and the picture comes back.

![The Betaflight logo, assembled from its 96 tiles](logo.png)
