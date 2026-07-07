// Render representative GeoTrainer cards to PNGs for the AnkiWeb listing.
// Loads bundles/shapes directly and mounts cards (works for any scope, incl.
// physical), does the interaction where the graded result is the compelling
// image, and screenshots the card. Run: node scripts/capture_screenshots.mjs
import { chromium } from "@playwright/test";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { readFileSync, mkdirSync } from "node:fs";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..");
const ENGINE = readFileSync(join(ROOT, "engine", "geo-engine.js"), "utf-8");
const CSS = readFileSync(join(ROOT, "anki", "shared", "card.css"), "utf-8");
const BUNDLE_DIR = join(ROOT, "data", "bundles");
const OUT = join(ROOT, "release", "screenshots");
mkdirSync(OUT, { recursive: true });

function load(scope) {
  return {
    bundle: JSON.parse(readFileSync(join(BUNDLE_DIR, `${scope}.json`), "utf-8")),
    shapes: JSON.parse(readFileSync(join(BUNDLE_DIR, `${scope}-shapes.json`), "utf-8")),
  };
}

async function mountCard(page, scope, target, mode, side) {
  const { bundle, shapes } = load(scope);
  await page.setContent(`<!doctype html><html><head><style>${CSS}</style></head><body></body></html>`);
  await page.evaluate(
    ({ scope, bundle, shapes }) => {
      window.GT_BUNDLES = { [scope]: bundle };
      window.GT_SHAPES = {};
      for (const id of Object.keys(shapes)) window.GT_SHAPES[scope + ":" + id] = shapes[id];
    },
    { scope, bundle, shapes }
  );
  const name =
    mode === "river" ? shapes[target].name
    : (bundle.regions.find((r) => r.id === target) || {}).name || target;
  await page.evaluate(
    ({ scope, target, mode, side, name }) => {
      const app = document.createElement("div");
      app.className = "gt-app";
      app.setAttribute("data-scope", scope);
      app.setAttribute("data-target", target);
      app.setAttribute("data-name", name);
      app.setAttribute("data-side", side);
      app.setAttribute("data-mode", mode);
      document.body.appendChild(app);
    },
    { scope, target, mode, side, name }
  );
  await page.addScriptTag({ content: ENGINE });
  await page.waitForSelector("svg.gt-map, svg.gt-canvas");
}

async function flipToBack(page) {
  await page.evaluate(() => {
    const app = document.querySelector(".gt-app");
    const attrs = {};
    for (const a of app.attributes) if (a.name !== "data-gt-mounted") attrs[a.name] = a.value;
    document.body.innerHTML = "";
    const back = document.createElement("div");
    for (const [k, v] of Object.entries(attrs)) back.setAttribute(k, v);
    back.setAttribute("data-side", "back");
    document.body.appendChild(back);
    window.GeoTrainer.mountAll();
  });
}

async function tracePolyline(page, pointsFn) {
  await page.evaluate((pointsFn) => {
    const svg = document.querySelector("svg.gt-map, svg.gt-canvas");
    const toClient = (p) => {
      const pt = svg.createSVGPoint();
      pt.x = p[0];
      pt.y = p[1];
      const s = pt.matrixTransform(svg.getScreenCTM());
      return { x: s.x, y: s.y };
    };
    const pev = (t, c) =>
      svg.dispatchEvent(new PointerEvent(t, { clientX: c.x, clientY: c.y, bubbles: true, pointerId: 1 }));
    const strokes = new Function("w", "return (" + pointsFn + ")(w)")(window);
    for (const pts of strokes) {
      if (pts.length < 2) continue;
      pev("pointerdown", toClient(pts[0]));
      for (let i = 1; i < pts.length; i++) pev("pointermove", toClient(pts[i]));
      pev("pointerup", toClient(pts[pts.length - 1]));
    }
  }, pointsFn.toString());
}

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1120, height: 820 }, deviceScaleFactor: 2 });

// 1. Borderless "Which country?" — the hero: blank Europe + a dot to recall.
await mountCard(page, "europe-countries", "DE", "point", "front");
await page.locator("body").screenshot({ path: join(OUT, "01-which-borderless.png") });
console.log("01-which-borderless");

// 2. Deserts — name the feature at the dot (back reveals the Sahara).
await mountCard(page, "world-deserts", "sahara", "point", "front");
await tracePolyline(page, (w) => []); // no draw; just flip
await flipToBack(page);
await page.locator("body").screenshot({ path: join(OUT, "02-deserts.png") });
console.log("02-deserts");

// 3. Draw overlay with the honest scoring (trace California).
await mountCard(page, "us-states", "US-CA", "draw", "front");
await tracePolyline(page, (w) => [w.GT_SHAPES["us-states:US-CA"].rings[0]]);
await flipToBack(page);
await page.waitForSelector(".gt-outline");
await page.locator("body").screenshot({ path: join(OUT, "03-draw-overlay.png") });
console.log("03-draw-overlay");

// 4. River trace — draw the Nile's course over the world map.
await mountCard(page, "world-rivers", "nile", "river", "front");
await tracePolyline(page, (w) => w.GT_SHAPES["world-rivers:nile"].paths);
await flipToBack(page);
await page.waitForSelector(".gt-river");
await page.locator("body").screenshot({ path: join(OUT, "04-river-trace.png") });
console.log("04-river-trace");

// 5. Mountain ranges — name the range at the dot (back reveals the Andes).
await mountCard(page, "world-ranges", "andes", "point", "front");
await flipToBack(page);
await page.locator("body").screenshot({ path: join(OUT, "05-ranges.png") });
console.log("05-ranges");

await browser.close();
