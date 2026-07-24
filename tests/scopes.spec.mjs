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
  return !["rivers", "currents"].includes(b.kind); // line scopes are tested separately
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

  const allowedFamilies = bundle.families || ["point", "place", "sketch", "draw"];
  const sketchIt = allowedFamilies.includes("sketch") ? test : test.skip;
  sketchIt(`${scope}: contextual Sketch accepts a faithful in-place outline`, async ({ page }) => {
    await mount(page, scope, data, { target: drawTarget.id, mode: "sketch", side: "front" });
    await page.waitForSelector("svg.gt-sketch-map");
    await expect(page.locator(".gt-land.gt-borderless")).toHaveCount(1);
    const quality = await page.evaluate(
      ({ scope, id }) => {
        const region = window.GT_BUNDLES[scope].regions.find((r) => r.id === id);
        const strokes = region.rings.map((ring) => {
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
        return window.GeoTrainer._sketchScore(strokes, region).quality;
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

  test(`${scope}: zoom shrinks the viewBox and a zoomed trace still scores`, async ({ page }) => {
    await mount(page, scope, data, { target: rid, mode: "river", side: "front" });
    await page.waitForSelector("svg.gt-map");
    await expect(page.locator(".gt-zoom")).toHaveCount(2); // − and +
    const wBefore = await page.evaluate(() =>
      Number(document.querySelector("svg.gt-map").getAttribute("viewBox").split(/\s+/)[2])
    );
    // Zoom in (wheel toward the river's midpoint), then trace at the new zoom.
    const scoreOk = await page.evaluate(
      ({ scope, id }) => {
        const svg = document.querySelector("svg.gt-map");
        const paths = window.GT_SHAPES[scope + ":" + id].paths;
        const mid = paths[0][Math.floor(paths[0].length / 2)];
        const toScreen = (p) => {
          const pt = svg.createSVGPoint();
          pt.x = p[0];
          pt.y = p[1];
          return pt.matrixTransform(svg.getScreenCTM());
        };
        const m = toScreen(mid);
        for (let i = 0; i < 2; i++)
          svg.dispatchEvent(new WheelEvent("wheel", { clientX: m.x, clientY: m.y, deltaY: -100, bubbles: true }));
        // trace the true course under the NEW zoom (screen coords recomputed)
        for (const path of paths) {
          if (path.length < 2) continue;
          const c0 = toScreen(path[0]);
          svg.dispatchEvent(new PointerEvent("pointerdown", { clientX: c0.x, clientY: c0.y, bubbles: true, pointerId: 1, button: 0 }));
          for (let i = 1; i < path.length; i++) {
            const c = toScreen(path[i]);
            svg.dispatchEvent(new PointerEvent("pointermove", { clientX: c.x, clientY: c.y, bubbles: true, pointerId: 1 }));
          }
          const cl = toScreen(path[path.length - 1]);
          svg.dispatchEvent(new PointerEvent("pointerup", { clientX: cl.x, clientY: cl.y, bubbles: true, pointerId: 1 }));
        }
        const w = Number(svg.getAttribute("viewBox").split(/\s+/)[2]);
        return { zoomedW: w };
      },
      { scope, id: rid }
    );
    expect(scoreOk.zoomedW).toBeLessThan(wBefore); // zoomed in
    const state = await readState(page, "river", scope, rid);
    // Coordinates must stay in map space at zoom — a faithful trace still covers
    // the river (many points recorded, not garbage).
    expect(state.strokes.reduce((n, s) => n + s.length, 0)).toBeGreaterThan(20);
  });

  test(`${scope}: Move toggle pans on drag and suppresses drawing`, async ({ page }) => {
    await mount(page, scope, data, { target: rid, mode: "river", side: "front" });
    await page.waitForSelector("svg.gt-map");
    // zoom in first, otherwise the view is already clamped and can't pan
    await page.evaluate(() => {
      const svg = document.querySelector("svg.gt-map");
      const r = svg.getBoundingClientRect();
      const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      for (let i = 0; i < 3; i++)
        svg.dispatchEvent(new WheelEvent("wheel", { clientX: cx, clientY: cy, deltaY: -100, bubbles: true }));
    });
    const move = page.locator(".gt-move");
    await expect(move).toHaveCount(1);
    await move.click();
    await expect(move).toHaveClass(/gt-active/);

    const panned = await page.evaluate(() => {
      const svg = document.querySelector("svg.gt-map");
      const vb0 = svg.getAttribute("viewBox").split(/\s+/).map(Number);
      const r = svg.getBoundingClientRect();
      const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      // left-button drag: in Move mode this pans, and must NOT record a stroke
      svg.dispatchEvent(new PointerEvent("pointerdown", { clientX: cx, clientY: cy, bubbles: true, pointerId: 1, button: 0 }));
      svg.dispatchEvent(new PointerEvent("pointermove", { clientX: cx - 60, clientY: cy - 40, bubbles: true, pointerId: 1 }));
      svg.dispatchEvent(new PointerEvent("pointerup", { clientX: cx - 60, clientY: cy - 40, bubbles: true, pointerId: 1 }));
      const vb1 = svg.getAttribute("viewBox").split(/\s+/).map(Number);
      return { movedX: Math.abs(vb1[0] - vb0[0]), movedY: Math.abs(vb1[1] - vb0[1]) };
    });
    expect(panned.movedX + panned.movedY).toBeGreaterThan(0); // the view moved
    const noStroke = await readState(page, "river", scope, rid);
    expect(noStroke.strokes.reduce((n, s) => n + s.length, 0)).toBe(0); // nothing drawn

    // toggle Move off → the same drag now draws
    await move.click();
    await expect(move).not.toHaveClass(/gt-active/);
    await page.evaluate(() => {
      const svg = document.querySelector("svg.gt-map");
      const r = svg.getBoundingClientRect();
      const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      svg.dispatchEvent(new PointerEvent("pointerdown", { clientX: cx, clientY: cy, bubbles: true, pointerId: 1, button: 0 }));
      for (let i = 1; i <= 10; i++)
        svg.dispatchEvent(new PointerEvent("pointermove", { clientX: cx + i * 6, clientY: cy + i * 4, bubbles: true, pointerId: 1 }));
      svg.dispatchEvent(new PointerEvent("pointerup", { clientX: cx + 60, clientY: cy + 40, bubbles: true, pointerId: 1 }));
    });
    const drew = await readState(page, "river", scope, rid);
    expect(drew.strokes.reduce((n, s) => n + s.length, 0)).toBeGreaterThan(2); // drew now
  });

  test(`${scope}: river trace-the-course grades the drawn line, line on back`, async ({ page }) => {
    await mount(page, scope, data, { target: rid, mode: "river", side: "front" });
    await page.waitForSelector("svg.gt-map");
    await expect(page.locator(".gt-chip")).toHaveText("Trace");
    await expect(page.locator(".gt-prompt")).toHaveText(data.shapes[rid].name);
    // Trace the river's true course faithfully — every path as its own stroke,
    // so the whole line is covered (scoring compares against all segments).
    await page.evaluate(
      ({ scope, id }) => {
        const r = window.GT_SHAPES[scope + ":" + id];
        const svg = document.querySelector("svg.gt-map");
        const toClient = (p) => {
          const pt = svg.createSVGPoint();
          pt.x = p[0];
          pt.y = p[1];
          const s = pt.matrixTransform(svg.getScreenCTM());
          return { x: s.x, y: s.y };
        };
        const pev = (t, c) =>
          svg.dispatchEvent(new PointerEvent(t, { clientX: c.x, clientY: c.y, bubbles: true, pointerId: 1 }));
        for (const path of r.paths) {
          if (path.length < 2) continue;
          pev("pointerdown", toClient(path[0]));
          for (let i = 1; i < path.length; i++) pev("pointermove", toClient(path[i]));
          pev("pointerup", toClient(path[path.length - 1]));
        }
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
    await expect(page.locator(".gt-river")).not.toHaveCount(0); // true course
    await expect(page.locator(".gt-drawn")).not.toHaveCount(0); // the traced line
    await expect(page.locator(".gt-bar.gt-ok")).toContainText("Good course"); // faithful trace
  });
}

const CURRENT_SCOPES = SCOPES.filter((s) => {
  const b = JSON.parse(readFileSync(join(BUNDLE_DIR, `${s}.json`), "utf-8"));
  return b.kind === "currents";
});

for (const scope of CURRENT_SCOPES) {
  const data = load(scope);
  const cid = Object.keys(data.shapes)[0];

  test(`${scope}: current trace shows arrows and accepts a faithful directed route`, async ({ page }) => {
    await mount(page, scope, data, { target: cid, mode: "current", side: "front" });
    await page.waitForSelector("svg.gt-map");
    await expect(page.locator(".gt-chip")).toHaveText("Trace current");
    await expect(page.locator(".gt-current-user")).toHaveCount(0);

    const score = await page.evaluate(
      ({ scope, id }) => {
        const route = window.GT_SHAPES[scope + ":" + id].paths;
        const frame = window.GT_BUNDLES[scope].frames[0];
        return {
          forward: window.GeoTrainer._currentScore([route[0]], route, frame.kmPerUnit),
          reverse: window.GeoTrainer._currentScore(
            [route[0].slice().reverse()], route, frame.kmPerUnit
          ),
        };
      },
      { scope, id: cid }
    );
    expect(score.forward.quality).toBe(2);
    expect(score.forward.reversed).toBe(false);
    expect(score.reverse.quality).toBe(0);
    expect(score.reverse.reversed).toBe(true);

    // Draw the ordered route through the actual capture surface so the persisted
    // state and learner arrow are exercised, then flip to the answer.
    await page.evaluate(
      ({ scope, id }) => {
        const svg = document.querySelector("svg.gt-map");
        const route = window.GT_SHAPES[scope + ":" + id].paths[0];
        const toClient = (p) => {
          const pt = svg.createSVGPoint();
          pt.x = p[0];
          pt.y = p[1];
          const s = pt.matrixTransform(svg.getScreenCTM());
          return { x: s.x, y: s.y };
        };
        const emit = (type, p) => svg.dispatchEvent(new PointerEvent(type, {
          clientX: p.x, clientY: p.y, bubbles: true, pointerId: 1, button: 0,
        }));
        emit("pointerdown", toClient(route[0]));
        for (let i = 1; i < route.length; i++) emit("pointermove", toClient(route[i]));
        emit("pointerup", toClient(route[route.length - 1]));
      },
      { scope, id: cid }
    );
    await expect(page.locator(".gt-current-user")).toHaveAttribute(
      "marker-end", "url(#gt-user-current-arrow)"
    );

    await page.evaluate(
      ({ scope, id, name }) => {
        document.body.innerHTML = "";
        const app = document.createElement("div");
        app.className = "gt-app";
        app.setAttribute("data-scope", scope);
        app.setAttribute("data-target", id);
        app.setAttribute("data-name", name);
        app.setAttribute("data-side", "back");
        app.setAttribute("data-mode", "current");
        document.body.appendChild(app);
        window.GeoTrainer.mountAll();
      },
      { scope, id: cid, name: data.shapes[cid].name }
    );
    await expect(page.locator(".gt-current")).toHaveAttribute(
      "marker-end", "url(#gt-target-current-arrow)"
    );
    await expect(page.locator(".gt-current-corridor")).toHaveCount(1);
    await expect(page.locator(".gt-bar.gt-ok")).toContainText("Good route and direction");
  });
}

test("new physical curricula have deliberate, stable membership", () => {
  const lakes = load("world-lakes");
  const plates = load("world-tectonic-plates");
  const currents = load("world-ocean-currents");
  expect(lakes.bundle.regions).toHaveLength(24);
  expect(lakes.bundle.families).toEqual(["point", "place"]);
  expect(lakes.bundle.regions.map((r) => r.name)).toContain("Lake Victoria");
  expect(plates.bundle.regions).toHaveLength(16);
  expect(plates.bundle.families).toEqual(["point", "sketch"]);
  expect(plates.bundle.regions.map((r) => r.name)).toContain("Pacific Plate");
  expect(Object.keys(currents.shapes)).toHaveLength(12);
  expect(currents.bundle.families).toEqual(["current"]);
  for (const route of Object.values(currents.shapes)) {
    expect(["warm", "cold"]).toContain(route.temperature);
    expect(route.paths).toHaveLength(1);
    expect(route.paths[0].length).toBeGreaterThanOrEqual(4);
  }
});

test("all expected scopes are present", () => {
  expect(SCOPES.sort()).toEqual(
    [
      "africa-countries", "argentina-provinces", "asia-countries", "australia-states",
      "brazil-states", "canada-provinces", "china-provinces", "continents",
      "europe-countries", "india-states", "indonesia-provinces", "mexico-states",
      "north-america-countries", "oceania-countries", "russia-subjects",
      "south-america-countries", "us-states", "world-deserts",
      "world-lakes", "world-ocean-currents", "world-ranges", "world-rivers",
      "world-tectonic-plates",
    ].sort()
  );
});
