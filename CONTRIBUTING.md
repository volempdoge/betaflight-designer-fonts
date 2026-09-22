[← README](README.md) · [Developer docs](docs/DEVELOPERS.md) · [Українською](README_UA.md)

# Contributing

Thanks for looking. `docs/DEVELOPERS.md` explains how the conversion works;
this file is only about the mechanics of getting a change in.

## Setting up

The project uses [uv](https://docs.astral.sh/uv/). The minimum Python version
is whatever `requires-python` in `pyproject.toml` says.

```bash
uv sync --group dev
```

## Before opening a pull request

Run what CI runs:

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run pytest
```

## If you change anything that affects the fonts

`output/` is committed, because it is what people download. CI rebuilds it
from `original_fonts/*.mcm` and compares byte for byte, so a change to the
glyph code, the metrics or the character sets means you also have to
regenerate it:

```bash
uv run bf2font.py original_fonts/*.mcm
```

The build is deterministic: the same sources give the same bytes on any
supported Python, with or without the optional `uharfbuzz` extra. If a rebuild
produces a diff you did not expect, that is a bug worth reporting.

## If you change the symbol catalogue or the character sets

Two documentation files and two images are generated. Regenerate them in the
same commit, or CI will disagree with you:

```bash
uv run tools/symbol_index.py   # docs/SYMBOLS.md, docs/SYMBOLS_UA.md, docs/logo.png
uv run tools/specimen.py       # docs/sets.png
```

## Documentation

The English and Ukrainian docs are kept in step: `README.md` / `README_UA.md`,
`docs/DEVELOPERS.md` / `docs/DEVELOPERS_UA.md`. If you change one, change the
other. `docs/SYMBOLS*.md` are generated — edit `tools/symbol_index.py`, not the
Markdown.

## Licence

The original font data comes from
[betaflight/betaflight-configurator](https://github.com/betaflight/betaflight-configurator)
under the GNU General Public License v3.0, and everything here is under the
same licence. By contributing you agree your work is licensed that way too.
