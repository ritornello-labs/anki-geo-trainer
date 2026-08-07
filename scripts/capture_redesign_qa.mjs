// Capture representative renders for the 2026-08 atmospheric/ENSO redesign.
// These are local QA artifacts, not AnkiWeb listing images.
import { chromium } from "@playwright/test";
import { readFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..");
const ENGINE = readFileSync(join(ROOT, "engine", "geo-engine.js"), "utf8");
const CSS = readFileSync(join(ROOT, "anki", "shared", "card.css"), "utf8");
const BUNDLES = join(ROOT, "data", "bundles");
const OUT = join(ROOT, "test-results", "redesign");
mkdirSync(OUT, { recursive: true });

function load(scope) {
  return {
    bundle: JSON.parse(readFileSync(join(BUNDLES, `${scope}.json`), "utf8")),
    shapes: JSON.parse(readFileSync(join(BUNDLES, `${scope}-shapes.json`), "utf8")),
  };
}

async function render(page, scope, target, mode, side, state) {
  const data = load(scope);
  await page.setContent(`<!doctype html><html><head><style>${CSS}</style></head><body></body></html>`);
  await page.evaluate(({ scope, target, mode, side, data, state }) => {
    window.GT_BUNDLES = { [scope]: data.bundle };
    window.GT_SHAPES = {};
    for (const [id, shape] of Object.entries(data.shapes)) {
      window.GT_SHAPES[`${scope}:${id}`] = shape;
    }
    if (state) window[`__gt_${mode}_${scope}_${target}`] = state;
    const app = document.createElement("div");
    app.className = "gt-app";
    app.dataset.scope = scope;
    app.dataset.target = target;
    app.dataset.mode = mode;
    app.dataset.side = side;
    document.body.appendChild(app);
  }, { scope, target, mode, side, data, state });
  await page.addScriptTag({ content: ENGINE });
  await page.waitForSelector("svg.gt-map");
}

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1180, height: 900 }, deviceScaleFactor: 2 });
const shots = [
  ["01-pressure-front.png", "atmospheric-pressure-belts", "subtropical-highs", "belt", "front"],
  ["02-cells-front.png", "atmospheric-cells", "01-hadley-pair", "cell", "front"],
  ["03-monsoon-world-front.png", "south-asia-monsoon-winds", "south-asia-summer", "seasonalwind", "front"],
  ["04-wind-back.png", "world-prevailing-winds", "northern-westerlies", "wind", "back", {
    strokes: [[[440, 220], [525, 205], [610, 186], [700, 166]]],
  }],
  ["05-amoc-directions-front.png", "atlantic-overturning", "01-limb-directions", "amoc", "front"],
  ["06-amoc-sequence-back.png", "atlantic-overturning", "02-pathway-order", "amoc", "back", {
    order: [0, 1, 2, 3],
  }],
  ["07-el-nino-back.png", "equatorial-pacific-enso", "02-el-nino", "enso", "back"],
  ["08-enso-comparison-back.png", "equatorial-pacific-enso", "04-comparison", "enso", "back"],
];

for (const [filename, scope, target, mode, side, state] of shots) {
  await render(page, scope, target, mode, side, state);
  await page.locator(".gt-app").screenshot({ path: join(OUT, filename) });
  console.log(join(OUT, filename));
}

await browser.close();
