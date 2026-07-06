// Render representative GeoTrainer cards to PNGs for the AnkiWeb listing.
// Uses the shipped fixtures (full inlined engine + data), does the interaction
// in-page where the *result* is the compelling image (draw overlay, river line,
// capital star), and screenshots the card. Run: node scripts/capture_screenshots.mjs
import { chromium } from "@playwright/test";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { readFileSync, mkdirSync } from "node:fs";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..");
const FIX = (n) => "file://" + join(ROOT, "tests", "fixtures", n);
const OUT = join(ROOT, "release", "screenshots");
mkdirSync(OUT, { recursive: true });

// Re-mount the same card in "back" mode after an interaction (state survives in
// window/localStorage), the way Anki re-renders the back.
async function flipToBack(page, scope, target, mode) {
  await page.evaluate(
    ({ scope, target, mode }) => {
      const app = document.querySelector(".gt-app");
      const attrs = {};
      for (const a of app.attributes) {
        if (a.name === "data-gt-mounted") continue; // else mountAll skips the new div
        attrs[a.name] = a.value;
      }
      document.body.innerHTML = "";
      const back = document.createElement("div");
      for (const [k, v] of Object.entries(attrs)) back.setAttribute(k, v);
      back.setAttribute("data-side", "back");
      document.body.appendChild(back);
      window.GeoTrainer.mountAll();
    },
    { scope, target, mode }
  );
}

async function tapAt(page, sx, sy) {
  await page.evaluate(
    ({ x, y }) => {
      const svg = document.querySelector("svg.gt-map");
      const pt = svg.createSVGPoint();
      pt.x = x;
      pt.y = y;
      const s = pt.matrixTransform(svg.getScreenCTM());
      svg.dispatchEvent(new MouseEvent("click", { clientX: s.x, clientY: s.y, bubbles: true }));
    },
    { x: sx, y: sy }
  );
}

const SHOTS = [
  // Clean fronts: the map + the prompt sell "interactive map quiz" on their own.
  { file: "card-europe-countries-locate-front.html", out: "01-europe-locate.png" },
  { file: "card-world-seas-point-front.html", out: "02-world-seas.png" },
  { file: "card-us-states-locate-front.html", out: "03-us-states.png" },
  // Interaction backs: the graded result is the compelling image.
  {
    file: "card-us-states-draw-front.html", out: "04-draw-overlay.png",
    async act(page) {
      // trace California's true outline, then flip
      await page.evaluate(() => {
        const shape = window.GT_SHAPES["us-states:US-CA"];
        const svg = document.querySelector("svg.gt-canvas");
        const toClient = (p) => {
          const pt = svg.createSVGPoint();
          pt.x = p[0];
          pt.y = p[1];
          const s = pt.matrixTransform(svg.getScreenCTM());
          return { x: s.x, y: s.y };
        };
        const pev = (t, c) =>
          svg.dispatchEvent(new PointerEvent(t, { clientX: c.x, clientY: c.y, bubbles: true, pointerId: 1 }));
        const ring = shape.rings[0]; // trace every vertex for a clean overlay
        pev("pointerdown", toClient(ring[0]));
        for (let i = 1; i < ring.length; i++) pev("pointermove", toClient(ring[i]));
        pev("pointerup", toClient(ring[ring.length - 1]));
      });
      await flipToBack(page, "us-states", "US-CA", "draw");
      await page.waitForSelector(".gt-outline");
    },
  },
  {
    file: "card-world-rivers-river-front.html", out: "05-river-locate.png",
    async act(page) {
      const p = await page.evaluate(() => window.GT_SHAPES["world-rivers:amazon"].paths[0][3]);
      await tapAt(page, p[0] + 5, p[1] + 3); // close: grades "On it"
      await flipToBack(page, "world-rivers", "amazon", "river");
      await page.waitForSelector(".gt-river");
    },
  },
  {
    file: "card-europe-countries-capital-front.html", out: "06-capital.png",
    async act(page) {
      const c = await page.evaluate(() => {
        const a = document.querySelector(".gt-app").getAttribute("data-cappt").split(",").map(Number);
        return a;
      });
      await tapAt(page, c[0] + 18, c[1] + 10);
      await flipToBack(page, "europe-countries", "FRA", "capital");
      await page.waitForSelector(".gt-capital");
    },
  },
];

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1120, height: 900 }, deviceScaleFactor: 2 });
for (const shot of SHOTS) {
  await page.setContent(readFileSync(join(ROOT, "tests", "fixtures", shot.file), "utf-8"));
  await page.waitForSelector("svg.gt-map, svg.gt-canvas");
  if (shot.act) await shot.act(page);
  await page.waitForTimeout(150);
  const card = page.locator("body");
  await card.screenshot({ path: join(OUT, shot.out) });
  console.log("wrote", join("release/screenshots", shot.out));
}
await browser.close();
