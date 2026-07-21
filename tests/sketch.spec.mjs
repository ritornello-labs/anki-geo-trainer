import { test, expect } from "@playwright/test";
import { readState } from "./state-helper.mjs";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..");
const ENGINE = readFileSync(join(ROOT, "engine", "geo-engine.js"), "utf-8");
const BUNDLE = JSON.parse(
  readFileSync(join(ROOT, "data", "bundles", "europe-countries.json"), "utf-8")
);

async function showSketch(page, side, keepState = false) {
  if (!keepState) {
    await page.setContent("<!doctype html><html><head></head><body></body></html>");
    await page.evaluate((bundle) => { window.GT_BUNDLES = { [bundle.scope]: bundle }; }, BUNDLE);
  } else {
    await page.evaluate(() => { document.body.innerHTML = ""; });
  }
  await page.evaluate((side) => {
    const app = document.createElement("div");
    app.className = "gt-app";
    app.setAttribute("data-scope", "europe-countries");
    app.setAttribute("data-target", "FRA");
    app.setAttribute("data-name", "France");
    app.setAttribute("data-side", side);
    app.setAttribute("data-mode", "sketch");
    document.body.appendChild(app);
    if (window.GeoTrainer) window.GeoTrainer.mountAll();
  }, side);
  if (!keepState) await page.addScriptTag({ content: ENGINE });
  await page.waitForSelector("svg.gt-sketch-map");
}

function densify(ring, per = 3) {
  const out = [];
  for (let i = 1; i < ring.length; i++) {
    for (let t = 0; t < per; t++) {
      const f = t / per;
      out.push([
        ring[i - 1][0] + (ring[i][0] - ring[i - 1][0]) * f,
        ring[i - 1][1] + (ring[i][1] - ring[i - 1][1]) * f,
      ]);
    }
  }
  return out;
}

async function traceStroke(page, points) {
  await page.evaluate((pts) => {
    const svg = document.querySelector("svg.gt-sketch-map");
    const toClient = (p) => {
      const pt = svg.createSVGPoint();
      pt.x = p[0];
      pt.y = p[1];
      const screen = pt.matrixTransform(svg.getScreenCTM());
      return { x: screen.x, y: screen.y };
    };
    const send = (type, p) => svg.dispatchEvent(new PointerEvent(type, {
      clientX: p.x, clientY: p.y, bubbles: true, pointerId: 1,
    }));
    send("pointerdown", toClient(pts[0]));
    for (let i = 1; i < pts.length; i++) send("pointermove", toClient(pts[i]));
    send("pointerup", toClient(pts[pts.length - 1]));
  }, points);
}

test("Sketch supplies a borderless parent map and records freehand strokes", async ({ page }) => {
  await showSketch(page, "front");
  await expect(page.locator(".gt-chip")).toHaveText("Sketch");
  await expect(page.locator(".gt-land.gt-borderless")).toHaveCount(1);
  await expect(page.locator(".gt-region.gt-small")).toHaveCount(0);

  const france = BUNDLE.regions.find((r) => r.id === "FRA");
  await traceStroke(page, densify(france.rings[0]));
  const state = await readState(page, "sketch", "europe-countries", "FRA");
  expect(state.strokes.length).toBe(1);
  expect(state.strokes[0].length).toBeGreaterThan(8);
});

test("Sketch grades shape in map position, unlike translation-invariant Draw", async ({ page }) => {
  await showSketch(page, "front");
  const scores = await page.evaluate(() => {
    const region = window.GT_BUNDLES["europe-countries"].regions.find((r) => r.id === "FRA");
    const traced = region.rings.map((ring) => ring.flatMap((p, i) => {
      if (!i) return [];
      const a = ring[i - 1];
      return [0, 0.25, 0.5, 0.75].map((f) => [
        a[0] + (p[0] - a[0]) * f,
        a[1] + (p[1] - a[1]) * f,
      ]);
    }));
    const shifted = traced.map((stroke) => stroke.map(([x, y]) => [x + region.s * 1.5, y]));
    return {
      traced: window.GeoTrainer._sketchScore(traced, region),
      shifted: window.GeoTrainer._sketchScore(shifted, region),
    };
  });
  expect(scores.traced.quality).toBe(2);
  expect(scores.shifted.quality).toBe(0);
});

test("Sketch back reveals the target and overlays a faithful attempt", async ({ page }) => {
  await showSketch(page, "front");
  const france = BUNDLE.regions.find((r) => r.id === "FRA");
  for (const ring of france.rings) await traceStroke(page, densify(ring));

  await showSketch(page, "back", true);
  await expect(page.locator(".gt-answer")).toHaveAttribute("data-id", "FRA");
  await expect(page.locator(".gt-drawn")).not.toHaveCount(0);
  await expect(page.locator(".gt-bar.gt-ok")).toContainText("Solid map sketch");
  await expect(page.locator(".gt-suggest")).toContainText("Good");
});
