// Builds the static site into site/dist: one directory per language, the fonts
// and images the page loads, plus robots.txt and sitemap.xml.
//
// The pages this writes are still client-rendered. prerender.mjs runs next and
// replaces each index.html with the fully rendered markup.

import { cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";

import { DIST, HERE, LOCALES, ROOT, SITE, localeUrl } from "./config.mjs";

// Font families the page declares in @font-face, by output directory and the
// CamelCase stem bf2font.py gives the files.
const FONTS = [
  ["extra_large", "ExtraLarge"],
  ["clarity", "Clarity"],
  ["bold", "Bold"],
  ["impact", "Impact"],
  ["vision", "Vision"],
  ["betaflight", "Betaflight"],
  ["impact_mini", "ImpactMini"],
  ["default", "Default"],
  ["large", "Large"],
  ["digital", "Digital"],
];

// Everything a language directory loads sits one level up. Only rewrite paths at
// the start of a URL -- `RAW + "/output/..."` and the GitHub blob links are
// absolute and must stay untouched, and those always have a slash in front.
function retargetToSubdirectory(html) {
  const out = html
    .replace(/(["'(])(assets\/|output\/)/g, "$1../$2")
    .replace(/(["'(])\.\/support\.js/g, "$1../support.js");
  if (out === html) throw new Error("subdirectory rewrite matched nothing");
  return out;
}

function setLangProp(html, key) {
  // The props are an HTML-escaped JSON blob on the runtime's script tag; the page
  // reads `lang` from it, so patching the default is what picks a language.
  const from =
    "&quot;lang&quot;:{&quot;editor&quot;:&quot;enum&quot;,&quot;default&quot;:&quot;en&quot;";
  const to = from.replace("&quot;en&quot;", `&quot;${key}&quot;`);
  if (!html.includes(from)) throw new Error("lang prop default not found");
  return html.replace(from, to);
}

// Static head tags per language. applySeo writes the canonical and the og:url
// again at runtime, from the same values; these are here for everything that
// never runs the script.
function headTags(locale) {
  const alternates = LOCALES.map(
    (l) => `<link rel="alternate" hreflang="${l.hreflang}" href="${localeUrl(l)}">`,
  );
  alternates.push(`<link rel="alternate" hreflang="x-default" href="${localeUrl(LOCALES[0])}">`);
  return [
    `<link rel="canonical" href="${localeUrl(locale)}">`,
    `<meta property="og:url" content="${localeUrl(locale)}">`,
    ...alternates,
  ].join("\n");
}

function page(source, locale) {
  let html = setLangProp(source, locale.key);
  if (locale.dir) html = retargetToSubdirectory(html);
  if (!html.includes("<html>")) throw new Error("no bare <html> tag to give a lang");
  html = html.replace("<html>", `<html lang="${locale.htmlLang}">`);
  return html.replace("</head>", `${headTags(locale)}\n</head>`);
}

function sitemap() {
  const entries = LOCALES.map((locale) => {
    const alts = LOCALES.map(
      (l) => `    <xhtml:link rel="alternate" hreflang="${l.hreflang}" href="${localeUrl(l)}"/>`,
    );
    alts.push(
      `    <xhtml:link rel="alternate" hreflang="x-default" href="${localeUrl(LOCALES[0])}"/>`,
    );
    return [
      "  <url>",
      `    <loc>${localeUrl(locale)}</loc>`,
      ...alts,
      "    <changefreq>monthly</changefreq>",
      `    <priority>${locale.dir ? "0.8" : "1.0"}</priority>`,
      "  </url>",
    ].join("\n");
  });
  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
    '        xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ...entries,
    "</urlset>",
    "",
  ].join("\n");
}

const robots = () => `User-agent: *\nAllow: /\n\nSitemap: ${SITE}/sitemap.xml\n`;

async function copyRuntimeAssets() {
  await cp(join(HERE, "support.js"), join(DIST, "support.js"));
  // og-card.html is an input -- `npm run og-card` renders it -- not something
  // the site serves.
  await cp(join(HERE, "assets"), join(DIST, "assets"), {
    recursive: true,
    filter: (src) => !src.endsWith("og-card.html"),
  });

  // Only the woff2 the page actually loads. The installable formats are large and
  // the download buttons point at raw.githubusercontent.com anyway.
  for (const [dir, stem] of FONTS) {
    for (const suffix of ["", "Shadow", "Fill"]) {
      const rel = join("output", dir, "fonts", "woff2", `BetaflightOSD${stem}${suffix}.woff2`);
      await mkdir(join(DIST, dirname(rel)), { recursive: true });
      await cp(join(ROOT, rel), join(DIST, rel));
    }
  }

  // The favicon.
  const icon = join("output", "clarity", "png", "035.png");
  await mkdir(join(DIST, dirname(icon)), { recursive: true });
  await cp(join(ROOT, icon), join(DIST, icon));
}

async function main() {
  const source = await readFile(join(HERE, "index.dc.html"), "utf8");

  for (const name of ["fpv-frame.webp", "og-card.jpg"]) {
    try {
      await readFile(join(HERE, "assets", name));
    } catch {
      throw new Error(
        `site/assets/${name} is missing. The hero background and the social card are ` +
          `binary assets that live with the design source; export them into ` +
          `site/assets/ before building.`,
      );
    }
  }

  await rm(DIST, { recursive: true, force: true });
  await mkdir(DIST, { recursive: true });
  await copyRuntimeAssets();

  for (const locale of LOCALES) {
    const dir = join(DIST, locale.dir);
    await mkdir(dir, { recursive: true });
    await writeFile(join(dir, "index.html"), page(source, locale));
  }

  await writeFile(join(DIST, "sitemap.xml"), sitemap());
  await writeFile(join(DIST, "robots.txt"), robots());
  // Keeps Pages from putting the content through Jekyll if the site is ever
  // served from a branch. upload-pages-artifact v4+ strips dotfiles, so the
  // Actions deployment below never sees this file -- and never needs to.
  await writeFile(join(DIST, ".nojekyll"), "");

  console.log(`built ${LOCALES.length} pages into ${DIST}`);
}

await main();
