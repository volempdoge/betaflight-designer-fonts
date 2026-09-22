// Renders every page in site/dist with a real browser and writes the result back
// over the same index.html.
//
// The landing page is a client-rendered component: support.js pulls React and
// Babel off a CDN, compiles the inline script, and only then is there any text on
// the page. Google can do that, slowly and unreliably; Bing and DuckDuckGo
// largely cannot. So the markup is baked in here instead.
//
// The scripts stay where they are. Each page ends up with three things in the
// body: the rendered markup under #dc-prerender, the component's template parked
// in an inert script tag, and a small shim that hands the template back to
// support.js as an <x-dc> element so the page hydrates exactly as before. Once
// React has mounted its own #dc-root the shim drops the prerendered copy. If
// React never arrives -- CDN blocked, JS off -- the static copy simply stays.

import { readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import puppeteer from "puppeteer";

import { DIST, LOCALES, SITE } from "./config.mjs";
import { serve } from "./server.mjs";

const PORT = 4173;
const ORIGIN = `http://127.0.0.1:${PORT}`;
// Wide enough that the page renders its desktop header: the nav links sit behind
// a burger menu below 760px, and a collapsed menu is markup a crawler cannot see.
const VIEWPORT = { width: 1280, height: 1000 };

// The template the runtime renders from. <helmet> is dropped: its tags are
// already in the prerendered <head>, and the helmet manager only ever appends,
// so keeping it would give the hydrated page a second title and description.
function extractTemplate(html) {
  const open = html.indexOf("<x-dc>");
  const close = html.lastIndexOf("</x-dc>");
  if (open === -1 || close <= open) throw new Error("no <x-dc> template in the source page");
  const template = html.slice(open + "<x-dc>".length, close);

  const hOpen = template.indexOf("<helmet>");
  const hClose = template.indexOf("</helmet>");
  if (hOpen === -1 || hClose <= hOpen) throw new Error("no <helmet> block in the template");
  const stripped = template.slice(0, hOpen) + template.slice(hClose + "</helmet>".length);

  // The template is parked in a script tag, which ends at the first "</script".
  if (/<\/script/i.test(stripped)) throw new Error("template contains </script, cannot be parked");
  return stripped;
}

const SHIM = `<script>
/* Prerender shim. Hands the template back to support.js as an <x-dc> element --
   which it hides on sight -- and removes the prerendered copy once React has
   mounted its own #dc-root. Runs while the document is still parsing, well
   before support.js finishes loading React off the CDN and boots. */
(function () {
  var tpl = document.getElementById("dc-template");
  if (!tpl || document.querySelector("x-dc")) return;
  var el = document.createElement("x-dc");
  el.innerHTML = tpl.textContent;
  tpl.parentNode.insertBefore(el, tpl);

  var stale = document.getElementById("dc-prerender");
  if (!stale) return;
  var deadline = Date.now() + 30000;
  (function poll() {
    var live = document.getElementById("dc-root");
    if (live && live.firstElementChild) { stale.remove(); return; }
    /* React never turned up. Leave the prerendered page standing. */
    if (Date.now() > deadline) return;
    requestAnimationFrame(poll);
  })();
})();
</script>`;

function bake(rendered, template) {
  // applySeo resolves the canonical, og:url, og:image and the hero background
  // against wherever the page is loaded from, and the capture freezes that in.
  // Here that is the prerender server, so put the real base back.
  let html = rendered.replaceAll(ORIGIN, SITE);
  if (SITE !== ORIGIN && html.includes(ORIGIN)) {
    throw new Error("prerender origin left in the markup");
  }

  if ((html.match(/id="dc-root"/g) ?? []).length !== 1) {
    throw new Error("expected exactly one #dc-root in the rendered page");
  }
  html = html.replace('id="dc-root"', 'id="dc-prerender"');

  // support.js prepends its own stylesheet to <head> as soon as it loads, which
  // in the captured markup leaves the charset declaration several kilobytes in.
  // It has to be inside the first 1024 bytes to count.
  const charset = '<meta charset="utf-8">';
  if ((html.match(/<meta charset=/g) ?? []).length !== 1) {
    throw new Error("expected exactly one charset declaration");
  }
  html = html.replace(charset, "").replace("<head>", `<head>${charset}`);

  // support.js sizes #dc-root; the prerendered copy stands in for it until the
  // hydrated one exists.
  html = html.replace(
    "</head>",
    '<style>#dc-prerender,#dc-prerender>.sc-host{height:100%}</style>\n</head>',
  );

  const marker = '<script type="text/x-dc"';
  if (!html.includes(marker)) throw new Error("component script missing from the rendered page");
  const parked = `<script id="dc-template" type="text/x-dc-template">${template}</script>\n${SHIM}\n`;
  html = html.replace(marker, parked + marker);

  return `<!DOCTYPE html>\n${html}\n`;
}

async function render(browser, locale) {
  const file = join(DIST, locale.dir, "index.html");
  const template = extractTemplate(await readFile(file, "utf8"));

  const page = await browser.newPage();
  await page.setViewport(VIEWPORT);

  const failures = [];
  page.on("pageerror", (err) => failures.push(`page error: ${err.message}`));
  page.on("requestfailed", (req) => failures.push(`request failed: ${req.url()}`));

  const url = `${ORIGIN}/${locale.dir ? locale.dir + "/" : ""}`;
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 90_000 });

  // The whole page sits at opacity 0 until the component's boot state flips,
  // which it does once document.fonts.ready settles. Waiting for the wrapper to
  // finish its fade covers React mounting, the fonts, and the fade in one go.
  await page.waitForFunction(
    () => {
      const el = document.querySelector('#dc-root [style*="transition: opacity 420ms"]');
      return !!el && getComputedStyle(el).opacity === "1";
    },
    { timeout: 90_000, polling: 200 },
  );
  await page.evaluate(() => document.fonts.ready.then(() => true));
  // The font swap animation and the OSD ticker settle.
  await new Promise((r) => setTimeout(r, 1500));

  const { title, lang, textLength } = await page.evaluate(() => ({
    title: document.title,
    lang: document.documentElement.lang,
    textLength: (document.getElementById("dc-root")?.innerText ?? "").trim().length,
  }));
  if (lang !== locale.htmlLang) {
    throw new Error(`${locale.hreflang}: rendered as lang="${lang}", expected "${locale.htmlLang}"`);
  }
  if (textLength < 1500) {
    throw new Error(`${locale.hreflang}: only ${textLength} characters rendered`);
  }

  const rendered = await page.evaluate(() => document.documentElement.outerHTML);
  await page.close();

  const baked = bake(rendered, template);
  await writeFile(file, baked);
  return { title, textLength, bytes: Buffer.byteLength(baked), failures };
}

async function main() {
  const server = await serve(PORT);
  const browser = await puppeteer.launch({
    args: ["--no-sandbox", "--disable-dev-shm-usage"],
  });

  const broken = [];

  try {
    for (const locale of LOCALES) {
      const { title, textLength, bytes, failures } = await render(browser, locale);
      const name = locale.dir || "(root)";
      console.log(`${name.padEnd(8)} ${textLength} chars, ${Math.round(bytes / 1024)} KB  ${title}`);
      for (const f of new Set(failures)) {
        console.error(`  ! ${f}`);
        broken.push(`${name}: ${f}`);
      }
    }
  } finally {
    await browser.close();
    server.close();
  }

  // A 404 on a font or a throw during hydration used to print and still ship.
  // Anything the browser reported is a build failure.
  if (broken.length) {
    throw new Error(`prerender hit ${broken.length} browser failure(s):\n  ${broken.join("\n  ")}`);
  }
}

await main();
