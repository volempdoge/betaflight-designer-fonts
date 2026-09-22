// Renders assets/og-card.html to assets/og-card.jpg, the 1200x630 image every
// social preview of the site shows.
//
// Not part of `npm run build`: the card only changes when someone edits it, and
// it is an input to the build rather than an output. Run `npm run og-card` after
// touching og-card.html, and commit the result.
//
// JPEG rather than WebP -- some social scrapers still refuse a WebP og:image.

import { writeFile } from "node:fs/promises";
import { join } from "node:path";
import puppeteer from "puppeteer";

import { HERE, ROOT } from "./config.mjs";
import { serve } from "./server.mjs";

const PORT = 4174;
const QUALITY = 90;
const OUT = join(HERE, "assets", "og-card.jpg");

// Served from the repository root so the card can reach output/ for the fonts.
const server = await serve(PORT, ROOT);
const browser = await puppeteer.launch({ args: ["--no-sandbox", "--disable-dev-shm-usage"] });

try {
  const page = await browser.newPage();
  await page.setViewport({ width: 1200, height: 630 });
  await page.goto(`http://127.0.0.1:${PORT}/site/assets/og-card.html`, {
    waitUntil: "networkidle0",
    timeout: 60_000,
  });
  // The OSD faces are font-display: block, so nothing is drawn until they land.
  await page.evaluate(() => document.fonts.ready.then(() => true));

  const card = await page.$("#card");
  if (!card) throw new Error("no #card in og-card.html");
  const box = await card.boundingBox();
  if (Math.round(box.width) !== 1200 || Math.round(box.height) !== 630) {
    throw new Error(`card is ${box.width}x${box.height}, expected 1200x630`);
  }

  await writeFile(OUT, await card.screenshot({ type: "jpeg", quality: QUALITY }));
  console.log(`wrote ${OUT}`);
} finally {
  await browser.close();
  server.close();
}
