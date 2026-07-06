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
  .filter((f) => f.endsWith(".json") && !f.endsWith("-shapes.json") && !f.endsWith("-capitals.json"))
  .map((f) => f.replace(".json", ""));

function load(scope) {
  return {
    bundle: JSON.parse(readFileSync(join(BUNDLE_DIR, `${scope}.json`), "utf-8")),
    shapes: JSON.parse(readFileSync(join(BUNDLE_DIR, `${scope}-shapes.json`), "utf-8")),
    capitals: JSON.parse(readFileSync(join(BUNDLE_DIR, `${scope}-capitals.json`), "utf-8")),
  };
}

async function mount(page, scope, data, { target, mode, side }) {
  const cap = data.capitals[target];
  await page.setContent("<!doctype html><html><head></head><body></body></html>");
  await page.evaluate(
    ({ scope, bundle, shapes, capitals }) => {
      window.GT_BUNDLES = { [scope]: bundle };
      window.GT_SHAPES = {};
      for (const id of Object.keys(shapes)) window.GT_SHAPES[scope + ":" + id] = shapes[id];
      window.GT_CAPS = { [scope]: capitals };
    },
    { scope, bundle: data.bundle, shapes: data.shapes, capitals: data.capitals }
  );
  await page.evaluate(
    ({ scope, target, mode, side, name, cap }) => {
      const app = document.createElement("div");
      app.className = "gt-app";
      app.setAttribute("data-scope", scope);
      app.setAttribute("data-target", target);
      app.setAttribute("data-name", name);
      app.setAttribute("data-side", side);
      app.setAttribute("data-mode", mode);
      if (cap) {
        app.setAttribute("data-capname", cap.name);
        app.setAttribute("data-cappt", cap.x + "," + cap.y);
      }
      document.body.appendChild(app);
    },
    { scope, target, mode, side, name: "X", cap }
  );
  await page.addScriptTag({ content: ENGINE });
}

const POLYGON_SCOPES = SCOPES.filter((s) => {
  const b = JSON.parse(readFileSync(join(BUNDLE_DIR, `${s}.json`), "utf-8"));
  return b.kind !== "rivers"; // river scopes have no regions; tested separately
});

for (const scope of POLYGON_SCOPES) {
  const data = load(scope);
  const { bundle, shapes, capitals } = data;
  const tier1 = bundle.regions.filter((r) => r.tier !== 2);
  const target = tier1[Math.min(3, tier1.length - 1)]; // a mid-list region

  test(`${scope}: locate renders all regions and hit-tests a real tap`, async ({ page }) => {
    await mount(page, scope, data, { target: target.id, mode: "locate", side: "front" });
    await page.waitForSelector("svg.gt-map");
    await expect(page.locator(".gt-region")).toHaveCount(bundle.regions.length);
    // Dispatch the click in SVG space: some scopes (Argentina) are taller than
    // any viewport, so a real page.mouse click would land off-screen. The engine
    // reads clientX/clientY and inverts via getScreenCTM regardless of viewport.
    await page.evaluate(
      ({ scope, id }) => {
        const r = window.GT_BUNDLES[scope].regions.find((x) => x.id === id);
        const svg = document.querySelector("svg.gt-map");
        const pt = svg.createSVGPoint();
        pt.x = r.c[0];
        pt.y = r.c[1];
        const s = pt.matrixTransform(svg.getScreenCTM());
        svg.dispatchEvent(new MouseEvent("click", { clientX: s.x, clientY: s.y, bubbles: true }));
      },
      { scope, id: target.id }
    );
    const attempt = await readState(page, "locate", scope, target.id);
    // Tapping a region's representative point should hit that region (or, for
    // slivers, at least register *some* hit — never null).
    expect(attempt).not.toBeNull();
    expect(attempt.hitId).toBeTruthy();
  });

  test(`${scope}: point front↔back agree on the same dot`, async ({ page }) => {
    await mount(page, scope, data, { target: target.id, mode: "point", side: "front" });
    await page.waitForSelector(".gt-point");
    const front = await page.evaluate(() => {
      const d = document.querySelector(".gt-point");
      return [d.getAttribute("cx"), d.getAttribute("cy")];
    });
    await mount(page, scope, data, { target: target.id, mode: "point", side: "back" });
    await page.waitForSelector(".gt-point");
    const back = await page.evaluate(() => {
      const d = document.querySelector(".gt-point");
      return [d.getAttribute("cx"), d.getAttribute("cy")];
    });
    expect(back).toEqual(front);
    await expect(page.locator(".gt-answer")).toHaveAttribute("data-id", target.id);
  });

  // Trace-scoring is only meaningful on a substantial shape; a microstate's
  // magnified tap-circle traces imperfectly. Pick the largest tier-1 region.
  const drawTarget = tier1.filter((r) => !r.small).sort((a, b) => b.s - a.s)[0] || target;
  test(`${scope}: every tier-1 region has a drawable shape and a perfect trace scores Good`, async ({ page }) => {
    // shape coverage
    for (const r of tier1) expect(shapes[r.id], `${scope} missing shape for ${r.id}`).toBeTruthy();
    await mount(page, scope, data, { target: drawTarget.id, mode: "draw", side: "front" });
    await page.waitForSelector("svg.gt-canvas");
    const quality = await page.evaluate(
      ({ scope, id }) => {
        const shape = window.GT_SHAPES[scope + ":" + id];
        // Trace EVERY ring (densified), matching what _drawScore compares
        // against — otherwise a multi-part shape (islands) scores as "missed
        // chunks". Densify so it clears the "too few points" floor.
        const strokes = shape.rings.map((ring) => {
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
          return stroke;
        });
        return window.GeoTrainer._drawScore(strokes, shape).quality;
      },
      { scope, id: drawTarget.id }
    );
    expect(quality).toBe(2);
  });

  // F8: exercise the capital family on a region that has a capital. Physical
  // scopes (seas) have no capitals — skip the capital test there.
  const capTarget = tier1.find((r) => capitals[r.id] && capitals[r.id].name);
  const capIt = Object.keys(capitals).length ? test : test.skip;
  capIt(`${scope}: capital — prompt names the capital, exact tap grades Good`, async ({ page }) => {
    expect(capTarget, `${scope} has no capital-bearing region`).toBeTruthy();
    await mount(page, scope, data, { target: capTarget.id, mode: "capital", side: "front" });
    await page.waitForSelector("svg.gt-map");
    await expect(page.locator(".gt-prompt")).toHaveText(capitals[capTarget.id].name);
    await page.evaluate(
      ({ scope, id }) => {
        const c = window.GT_CAPS[scope][id];
        const svg = document.querySelector("svg.gt-map");
        const pt = svg.createSVGPoint();
        pt.x = c.x;
        pt.y = c.y;
        const s = pt.matrixTransform(svg.getScreenCTM());
        svg.dispatchEvent(new MouseEvent("click", { clientX: s.x, clientY: s.y, bubbles: true }));
      },
      { scope, id: capTarget.id }
    );
    // flip: re-render back mode in the same page (state survives in window/localStorage)
    await page.evaluate(
      ({ scope, id, cap }) => {
        document.body.innerHTML = "";
        const app = document.createElement("div");
        app.className = "gt-app";
        app.setAttribute("data-scope", scope);
        app.setAttribute("data-target", id);
        app.setAttribute("data-name", "X");
        app.setAttribute("data-side", "back");
        app.setAttribute("data-mode", "capital");
        app.setAttribute("data-capname", cap.name);
        app.setAttribute("data-cappt", cap.x + "," + cap.y);
        document.body.appendChild(app);
        window.GeoTrainer.mountAll();
      },
      { scope, id: capTarget.id, cap: capitals[capTarget.id] }
    );
    await expect(page.locator(".gt-capital")).toHaveCount(1); // true-capital star
    await expect(page.locator(".gt-bar.gt-ok")).toContainText(capitals[capTarget.id].name);
    await expect(page.locator(".gt-suggest")).toContainText("Good");
  });
}

// F9: river scopes are line data — the base bundle has no regions; each river's
// polyline lives in the shapes file. Verify one boots, renders its line on the
// back, and grades a tap by distance to the line.
const RIVER_SCOPES = SCOPES.filter((s) => {
  const b = JSON.parse(readFileSync(join(BUNDLE_DIR, `${s}.json`), "utf-8"));
  return b.kind === "rivers";
});

for (const scope of RIVER_SCOPES) {
  const data = load(scope);
  const rid = Object.keys(data.shapes)[0];

  test(`${scope}: river tap-to-locate grades by distance, line on back`, async ({ page }) => {
    await mount(page, scope, data, { target: rid, mode: "river", side: "front" });
    await page.waitForSelector("svg.gt-map");
    await expect(page.locator(".gt-chip")).toHaveText("River");
    await expect(page.locator(".gt-prompt")).toHaveText(data.shapes[rid].name);
    // tap a point ON the river (its first vertex)
    await page.evaluate(
      ({ scope, id }) => {
        const r = window.GT_SHAPES[scope + ":" + id];
        const p = r.paths[0][0];
        const svg = document.querySelector("svg.gt-map");
        const pt = svg.createSVGPoint();
        pt.x = p[0];
        pt.y = p[1];
        const s = pt.matrixTransform(svg.getScreenCTM());
        svg.dispatchEvent(new MouseEvent("click", { clientX: s.x, clientY: s.y, bubbles: true }));
      },
      { scope, id: rid }
    );
    // flip in-page (state + GT_SHAPES survive), like Anki re-rendering the back
    await page.evaluate(
      ({ scope, id, name, riverB64 }) => {
        document.body.innerHTML = "";
        window.GT_SHAPES[scope + ":" + id] = JSON.parse(atob(riverB64));
        const app = document.createElement("div");
        app.className = "gt-app";
        app.setAttribute("data-scope", scope);
        app.setAttribute("data-target", id);
        app.setAttribute("data-name", name);
        app.setAttribute("data-side", "back");
        app.setAttribute("data-mode", "river");
        document.body.appendChild(app);
        window.GeoTrainer.mountAll();
      },
      {
        scope, id: rid, name: data.shapes[rid].name,
        riverB64: Buffer.from(JSON.stringify(data.shapes[rid])).toString("base64"),
      }
    );
    await expect(page.locator(".gt-river")).not.toHaveCount(0); // highlighted line
    await expect(page.locator(".gt-bar.gt-ok")).toContainText(data.shapes[rid].name);
    await expect(page.locator(".gt-suggest")).toContainText("Good"); // exact tap
  });
}

test("all expected scopes are present", () => {
  expect(SCOPES.sort()).toEqual(
    [
      "africa-countries", "argentina-provinces", "asia-countries", "australia-states",
      "brazil-states", "canada-provinces", "china-provinces", "europe-countries",
      "india-states", "indonesia-provinces", "mexico-states", "oceania-countries",
      "russia-subjects", "south-america-countries", "us-states", "world-rivers",
      "world-seas",
    ].sort()
  );
});
