# The landing page

Source and build for <https://volempdoge.github.io/betaflight-designer-fonts/>.

`index.dc.html` is the page, imported from the Claude design project. It is a
single client-rendered component: `support.js` pulls React and Babel off a CDN,
compiles the inline script, and only then is there any text on the page. Google
manages that, slowly and unreliably. Bing and DuckDuckGo largely do not.

So the build runs a real browser over the page and writes the rendered markup
back into `index.html`, leaving every script where it was. A crawler gets
finished text; a browser gets the same interactivity on top.

## Files

| File | What it is |
| --- | --- |
| `index.dc.html` | the page itself: template, styles and component, all six languages |
| `support.js` | the design runtime that boots the component. Generated; do not edit |
| `config.mjs` | the site URL and the language table, shared by the build steps |
| `build.mjs` | writes the six language pages, the fonts, `robots.txt` and `sitemap.xml` into `dist/` |
| `prerender.mjs` | renders each page in Chrome and bakes the markup back in |
| `server.mjs` | static server over a directory, used by the prerender, the card and `npm run serve` |
| `og-card.mjs` | renders `assets/og-card.html` to `assets/og-card.jpg` |
| `assets/og-card.html` | the 1200x630 social card. An input to the build, not something the site serves |
| `public/` | copied to the root of `dist/` verbatim, under the same names |
| `assets/favicon.png` | the tab icon, cut square from `#` by `tools/favicon.py` |

The page loads two images. `assets/fpv-frame.webp` is the hero frame: it came
from the design project as a 883 KB PNG, fully opaque and blurred 7px in CSS, so
it is a 58 KB WebP here. `assets/og-card.jpg` is the social card, rendered from
`og-card.html` by `npm run og-card` -- JPEG rather than WebP, because some social
scrapers still refuse a WebP `og:image`. Run that after editing the card and
commit the result; it is not part of `npm run build`, which stops with a clear
message if either image is missing.

## Building

```bash
npm ci
npx puppeteer browsers install chrome
npm run build
```

`npm run build` is `build.mjs` then `prerender.mjs`. To look at the result:

```bash
SITE_URL=http://127.0.0.1:4173 npm run build && npm run serve
```

The `SITE_URL` override matters for a local look: the prerender bakes absolute
URLs for the canonical, the social card and the hero background, and without it
those point at the live site.

CI does the same three commands in `.github/workflows/pages.yml` and publishes
`dist/` to Pages on every push to `main` that touches `site/` or `output/`.

## The six languages

| URL | Language | `lang` |
| --- | --- | --- |
| `/` | English | `en` |
| `/uk/` | Ukrainian | `uk` |
| `/es/` | Spanish | `es` |
| `/fr/` | French | `fr` |
| `/zh/` | Chinese | `zh-Hans` |
| `/ja/` | Japanese | `ja` |

All six come off the same `index.dc.html`. `build.mjs` patches the `lang` prop
default in the runtime's `data-props`, retargets the relative paths one directory
up, and adds the canonical and the mutual `hreflang` links. Everything else --
title, description, `og:locale`, the JSON-LD -- the page writes itself from its
own dictionary while the prerender is watching, so there is one copy of each
string and it lives in the page.

The page calls Ukrainian `ua` and Japanese `jp` internally. The URLs and the
`hreflang` tags use the BCP 47 codes, `uk` and `ja`.

The language buttons still swap in place, animation and all, and rewrite the
address with `history.replaceState` so the URL always matches what is on screen.
Both `FRAME_SRC` and `OG_SRC` are resolved to absolute URLs once at boot for that
reason: after the address moves, a bare relative path would be measured from the
new directory.

## robots.txt

`robots.txt` only counts at the root of a host. On a project Pages site the root
is `volempdoge.github.io`, which belongs to a different repository, so the
`robots.txt` this build writes is never read and the `Sitemap:` line in it does
nothing. Submit `sitemap.xml` in Search Console instead, or move the site to a
custom domain, where both start working on their own.
