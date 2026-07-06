import { test, expect } from "@playwright/test";
import { readState } from "./state-helper.mjs";
import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

// Data-driven smoke across EVERY scope bundle: each new scope (continent or
// country subdivision) is verified to load, render its regions, hit-test a real
// tap, keep front↔back agreement, and carry a drawable shape — without a
// hand-written spec per scope. Guards the config-driven factories.
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..");
const ENGINE = readFileSync(join(ROOT, "engine", "geo-engine.js"), "utf-8");
const BUNDLE_DIR = join(ROOT, "data", "bundles");

const SCOPES = readdirSync(BUNDLE_DIR)
  .filter((f) => f.endsWith(".json") && !f.endsWith("-shapes.json"))
  .map((f) => f.replace(".json", ""));

function load(scope) {
  return {
    bundle: JSON.parse(readFileSync(join(BUNDLE_DIR, `${scope}.json`), "utf-8")),
    shapes: JSON.parse(readFileSync(join(BUNDLE_DIR, `${scope}-shapes.json`), "utf-8")),
  };
}

async function mount(page, scope, { bundle, shapes }, { target, mode, side }) {
  await page.setContent("<!doctype html><html><head></head><body></body></html>");
  await page.evaluate(
    ({ scope, bundle, shapes }) => {
      window.GT_BUNDLES = { [scope]: bundle };
      window.GT_SHAPES = {};
      for (const id of Object.keys(shapes)) window.GT_SHAPES[scope + ":" + id] = shapes[id];
    },
    { scope, bundle, shapes }
  );
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
    { scope, target, mode, side, name: "X" }
  );
  await page.addScriptTag({ content: ENGINE });
}

for (const scope of SCOPES) {
  const { bundle, shapes } = load(scope);
  const tier1 = bundle.regions.filter((r) => r.tier !== 2);
  const target = tier1[Math.min(3, tier1.length - 1)]; // a mid-list region

  test(`${scope}: locate renders all regions and hit-tests a real tap`, async ({ page }) => {
    await mount(page, scope, { bundle, shapes }, { target: target.id, mode: "locate", side: "front" });
    await page.waitForSelector("svg.gt-map");
    await expect(page.locator(".gt-region")).toHaveCount(bundle.regions.length);
    const p = await page.evaluate(
      ({ scope, id }) => {
        const r = window.GT_BUNDLES[scope].regions.find((x) => x.id === id);
        const svg = document.querySelector("svg.gt-map");
        const pt = svg.createSVGPoint();
        pt.x = r.c[0];
        pt.y = r.c[1];
        const s = pt.matrixTransform(svg.getScreenCTM());
        return { x: s.x, y: s.y };
      },
      { scope, id: target.id }
    );
    await page.mouse.click(p.x, p.y);
    const attempt = await readState(page, "locate", scope, target.id);
    // Tapping a region's representative point should hit that region (or, for
    // slivers, at least register *some* hit — never null).
    expect(attempt).not.toBeNull();
    expect(attempt.hitId).toBeTruthy();
  });

  test(`${scope}: point front↔back agree on the same dot`, async ({ page }) => {
    await mount(page, scope, { bundle, shapes }, { target: target.id, mode: "point", side: "front" });
    await page.waitForSelector(".gt-point");
    const front = await page.evaluate(() => {
      const d = document.querySelector(".gt-point");
      return [d.getAttribute("cx"), d.getAttribute("cy")];
    });
    await mount(page, scope, { bundle, shapes }, { target: target.id, mode: "point", side: "back" });
    await page.waitForSelector(".gt-point");
    const back = await page.evaluate(() => {
      const d = document.querySelector(".gt-point");
      return [d.getAttribute("cx"), d.getAttribute("cy")];
    });
    expect(back).toEqual(front);
    await expect(page.locator(".gt-answer")).toHaveAttribute("data-id", target.id);
  });

  test(`${scope}: every tier-1 region has a drawable shape and a perfect trace scores Good`, async ({ page }) => {
    // shape coverage
    for (const r of tier1) expect(shapes[r.id], `${scope} missing shape for ${r.id}`).toBeTruthy();
    await mount(page, scope, { bundle, shapes }, { target: target.id, mode: "draw", side: "front" });
    await page.waitForSelector("svg.gt-canvas");
    const quality = await page.evaluate(
      ({ scope, id }) => {
        const shape = window.GT_SHAPES[scope + ":" + id];
        // Densify the true ring the way a finger would (many points), so the
        // trace clears the engine's "too few points isn't a drawing" floor.
        const ring = shape.rings[0];
        const stroke = [];
        for (let i = 1; i < ring.length; i++) {
          for (let t = 0; t < 4; t++) {
            const f = t / 4;
            stroke.push([
              ring[i - 1][0] + (ring[i][0] - ring[i - 1][0]) * f,
              ring[i - 1][1] + (ring[i][1] - ring[i - 1][1]) * f,
            ]);
          }
        }
        return window.GeoTrainer._drawScore([stroke], shape).quality;
      },
      { scope, id: target.id }
    );
    expect(quality).toBe(2);
  });
}

test("all expected scopes are present", () => {
  expect(SCOPES.sort()).toEqual(
    [
      "africa-countries",
      "asia-countries",
      "brazil-states",
      "europe-countries",
      "india-states",
      "south-america-countries",
      "us-states",
    ].sort()
  );
});
