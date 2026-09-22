// Shared between build.mjs and prerender.mjs.

import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

// Where the site is served from. Everything absolute -- canonical, hreflang, the
// sitemap, and the URLs the prerender bakes in -- is built off this, so a move to
// a custom domain is a one-line change. SITE_URL overrides it, which is what a
// local preview wants: `SITE_URL=http://127.0.0.1:4173 npm run build`.
export const SITE = (process.env.SITE_URL ?? "https://volempdoge.github.io/betaflight-designer-fonts")
  .replace(/\/+$/, "");

// `key` is the language code inside the page, `dir` its directory under the site
// root, `hreflang` what goes in the link tags and the sitemap. The page calls
// Ukrainian "ua" and Japanese "jp"; the URLs and the tags use the BCP 47 codes.
export const LOCALES = [
  { key: "en", dir: "", hreflang: "en", htmlLang: "en" },
  { key: "ua", dir: "uk", hreflang: "uk", htmlLang: "uk" },
  { key: "es", dir: "es", hreflang: "es", htmlLang: "es" },
  { key: "fr", dir: "fr", hreflang: "fr", htmlLang: "fr" },
  { key: "zh", dir: "zh", hreflang: "zh-Hans", htmlLang: "zh-Hans" },
  { key: "jp", dir: "ja", hreflang: "ja", htmlLang: "ja" },
];

export const localeUrl = (locale) => `${SITE}/${locale.dir ? locale.dir + "/" : ""}`;

export const HERE = dirname(fileURLToPath(import.meta.url));
export const ROOT = join(HERE, "..");
export const DIST = join(HERE, "dist");
