import { test, expect } from "@playwright/test";
import { readState } from "./state-helper.mjs";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..");
const ENGINE = readFileSync(join(ROOT, "engine", "geo-engine.js"), "utf-8");
const SHAPES = JSON.parse(
  readFileSync(join(ROOT, "data", "bundles", "europe-countries-shapes.json"), "utf-8")
);

async function showDraw(page, { target, side, keepState = false }) {
  if (!keepState) {
    await page.setContent("<!doctype html><html><head></head><body></body></html>");
    await page.evaluate(
      ({ shapes, target }) => {
        window.GT_SHAPES = {};
        window.GT_SHAPES["europe-countries:" + target] = shapes[target];
      },
      { shapes: SHAPES, target }
    );
  } else {
    await page.evaluate(() => {
      document.body.innerHTML = "";
    });
  }
  await page.evaluate(
    ({ target, side }) => {
      const app = document.createElement("div");
      app.className = "gt-app";
      app.setAttribute("data-scope", "europe-countries");
      app.setAttribute("data-target", target);
      app.setAttribute("data-name", "France");
      app.setAttribute("data-side", side);
      app.setAttribute("data-mode", "draw");
      document.body.appendChild(app);
      if (window.GeoTrainer) window.GeoTrainer.mountAll();
    },
    { target, side }
  );
  if (!keepState) await page.addScriptTag({ content: ENGINE });
  await page.waitForSelector("svg.gt-canvas");
}

function densify(pts, per) {
  const out = [];
  for (let i = 1; i < pts.length; i++) {
    for (let t = 0; t < per; t++) {
      const f = t / per;
      out.push([
        pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f,
        pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f,
      ]);
    }
  }
  out.push(pts[pts.length - 1]);
  return out;
}

async function traceStroke(page, shapePts) {
  // Real pointer events through the canvas, client coords via fresh CTM.
  await page.evaluate((pts) => {
    const svg = document.querySelector("svg.gt-canvas");
    const toClient = (p) => {
      const pt = svg.createSVGPoint();
      pt.x = p[0];
      pt.y = p[1];
      const s = pt.matrixTransform(svg.getScreenCTM());
      return { x: s.x, y: s.y };
    };
    const pev = (type, c) =>
      svg.dispatchEvent(
        new PointerEvent(type, { clientX: c.x, clientY: c.y, bubbles: true, pointerId: 1 })
      );
    pev("pointerdown", toClient(pts[0]));
    for (let i = 1; i < pts.length; i++) pev("pointermove", toClient(pts[i]));
    pev("pointerup", toClient(pts[pts.length - 1]));
  }, shapePts);
}

test("drawing strokes register, undo and clear work", async ({ page }) => {
  await showDraw(page, { target: "FRA", side: "front" });
  await traceStroke(page, densify([[50, 50], [200, 60], [350, 200]], 8));
  await traceStroke(page, densify([[60, 300], [200, 320]], 8));
  await expect(page.locator(".gt-stroke")).toHaveCount(2);
  let state = await readState(page, "draw", "europe-countries", "FRA");
  expect(state.strokes.length).toBe(2);

  await page.locator(".gt-btn", { hasText: "Undo" }).click();
  await expect(page.locator(".gt-stroke")).toHaveCount(1);
  state = await readState(page, "draw", "europe-countries", "FRA");
  expect(state.strokes.length).toBe(1);

  await page.locator(".gt-btn", { hasText: "Clear" }).click();
  await expect(page.locator(".gt-stroke")).toHaveCount(0);
  state = await readState(page, "draw", "europe-countries", "FRA");
  expect(state.strokes.length).toBe(0);
});

test("tracing the true outline grades Good on the back", async ({ page }) => {
  await showDraw(page, { target: "FRA", side: "front" });
  const ring = SHAPES.FRA.rings[0];
  const step = Math.max(1, Math.floor(ring.length / 60));
  const pts = [];
  for (let i = 0; i < ring.length; i += step) pts.push(ring[i]);
  await traceStroke(page, pts);

  await showDraw(page, { target: "FRA", side: "back", keepState: true });
  await expect(page.locator(".gt-outline")).toHaveCount(1);
  await expect(page.locator(".gt-drawn")).toHaveCount(1);
  await expect(page.locator(".gt-bar.gt-ok")).toContainText("Solid outline");
  await expect(page.locator(".gt-suggest")).toContainText("Good");
});

test("scoring is translation/scale invariant but rejects scribble", async ({ page }) => {
  await showDraw(page, { target: "FRA", side: "front" });
  const scores = await page.evaluate((shapes) => {
    const shape = shapes.FRA;
    const ring = shape.rings[0];
    // exact trace, then the same trace shifted+shrunk, then a zigzag scribble
    const traced = [ring.filter((_, i) => i % 3 === 0)];
    const shrunk = [traced[0].map((p) => [p[0] * 0.4 + 30, p[1] * 0.4 + 55])];
    const dense = (pts, per) => {
      const out = [];
      for (let i = 1; i < pts.length; i++)
        for (let t = 0; t < per; t++) {
          const f = t / per;
          out.push([
            pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f,
            pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f,
          ]);
        }
      return out;
    };
    const zigzag = [dense([[20, 20], [380, 40], [30, 80], [370, 120], [40, 160], [360, 200]], 10)];
    const s = window.GeoTrainer._drawScore;
    return {
      traced: s(traced, shape),
      shrunk: s(shrunk, shape),
      zigzag: s(zigzag, shape),
    };
  }, SHAPES);
  expect(scores.traced.quality).toBe(2);
  expect(scores.shrunk.quality).toBe(2); // same form elsewhere/smaller: equal score
  expect(Math.abs(scores.shrunk.pct - scores.traced.pct)).toBeLessThan(0.5);
  expect(scores.zigzag.quality).toBe(0);
});

test("a lazy right-size wrong-shape circle grades Again, not Hard", async ({ page }) => {
  // Regression: an irregular enclosing circle over a country used to score a
  // "decent" grade. It has the right footprint (boundary is nearby) but a poor
  // area overlap, so the IoU gate must reject it. An honest freehand trace with
  // the same jitter must still pass.
  await showDraw(page, { target: "FRA", side: "front" });
  const scores = await page.evaluate((shapes) => {
    const shape = shapes.FRA;
    const rings = shape.rings;
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const ring of rings) for (const [x, y] of ring) {
      if (x < minX) minX = x; if (x > maxX) maxX = x;
      if (y < minY) minY = y; if (y > maxY) maxY = y;
    }
    const cx = (minX + maxX) / 2, cy = (minY + maxY) / 2;
    const rx = (maxX - minX) / 2, ry = (maxY - minY) / 2;
    const amp = Math.max(maxX - minX, maxY - minY) * 0.05;
    let r = 7;
    const rnd = () => { r = (r * 9301 + 49297) % 233280; return r / 233280; };
    // lazy irregular circle: right size, wrong shape
    const circle = [];
    for (let i = 0; i <= 40; i++) {
      const a = (i / 40) * Math.PI * 2;
      const wob = 0.82 + rnd() * 0.4;
      circle.push([cx + Math.cos(a) * rx * wob, cy + Math.sin(a) * ry * wob]);
    }
    // honest freehand: the real boundary, jittered the same ~5%
    const honest = [];
    for (const ring of rings) {
      const stroke = [];
      for (let i = 1; i < ring.length; i++)
        for (let t = 0; t < 4; t++) {
          const f = t / 4;
          stroke.push([
            ring[i - 1][0] + (ring[i][0] - ring[i - 1][0]) * f + (rnd() - 0.5) * amp,
            ring[i - 1][1] + (ring[i][1] - ring[i - 1][1]) * f + (rnd() - 0.5) * amp,
          ]);
        }
      honest.push(stroke);
    }
    const s = window.GeoTrainer._drawScore;
    return { circle: s([circle], shape), honest: s(honest, shape) };
  }, SHAPES);
  expect(scores.circle.quality).toBe(0); // didn't try → Again
  expect(scores.circle.iou).toBeLessThan(0.78);
  expect(scores.honest.quality).toBe(2); // real attempt → Good
});

test("empty drawing grades Again with a clear message", async ({ page }) => {
  await showDraw(page, { target: "FRA", side: "front" });
  await showDraw(page, { target: "FRA", side: "back", keepState: true });
  await expect(page.locator(".gt-bar.gt-miss")).toContainText("No drawing recorded");
  await expect(page.locator(".gt-suggest")).toContainText("Again");
});

test("shipped draw fixture boots from the per-note ShapeData field", async ({ page }) => {
  const fix = join(HERE, "fixtures", "card-europe-countries-draw-front.html");
  await page.setContent(readFileSync(fix, "utf-8"));
  await page.waitForSelector("svg.gt-canvas");
  await traceStroke(page, densify([[80, 80], [300, 90], [320, 280], [90, 260], [80, 80]], 6));
  const state = await readState(page, "draw", "europe-countries", "FRA");
  expect(state.strokes.length).toBe(1);
  expect(state.strokes[0].length).toBeGreaterThan(10);
});

test("shipped draw back fixture renders outline and verdict", async ({ page }) => {
  const front = join(HERE, "fixtures", "card-europe-countries-draw-front.html");
  const back = join(HERE, "fixtures", "card-europe-countries-draw-back.html");
  await page.setContent(readFileSync(front, "utf-8"));
  await page.waitForSelector("svg.gt-canvas");
  const ring = SHAPES.FRA.rings[0];
  const pts = [];
  const step = Math.max(1, Math.floor(ring.length / 50));
  for (let i = 0; i < ring.length; i += step) pts.push(ring[i]);
  await traceStroke(page, pts);
  // same-page swap emulates Anki flipping without navigation
  const backBody = readFileSync(back, "utf-8").match(/<body>([\s\S]*)<\/body>/)[1];
  await page.evaluate((html) => {
    document.body.innerHTML = html;
    // Anki re-executes scripts on flip; emulate by re-running mountAll
    window.GeoTrainer.mountAll();
  }, backBody.replace(/<script>[\s\S]*?<\/script>/g, ""));
  await expect(page.locator(".gt-outline")).toHaveCount(1);
  await expect(page.locator(".gt-suggest")).toContainText("Good");
});
