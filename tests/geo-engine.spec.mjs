import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..");
const ENGINE = readFileSync(join(ROOT, "engine", "geo-engine.js"), "utf-8");
const BUNDLE = JSON.parse(
  readFileSync(join(ROOT, "data", "bundles", "us-states.json"), "utf-8")
);

// Render the card the way Anki does: bundle + engine inlined, no network.
async function showSide(page, { target, mode, side, fresh = true }) {
  if (fresh) {
    await page.setContent("<!doctype html><html><head></head><body></body></html>");
    await page.evaluate((bundle) => {
      window.GT_BUNDLES = { "us-states": bundle };
    }, BUNDLE);
  } else {
    await page.evaluate(() => {
      document.body.innerHTML = "";
    });
  }
  await page.evaluate(
    ({ target, mode, side }) => {
      const app = document.createElement("div");
      app.className = "gt-app";
      app.setAttribute("data-scope", "us-states");
      app.setAttribute("data-target", target);
      app.setAttribute("data-side", side);
      app.setAttribute("data-mode", mode);
      document.body.appendChild(app);
      if (window.GeoTrainer) window.GeoTrainer.mountAll();
    },
    { target, mode, side }
  );
  if (fresh) await page.addScriptTag({ content: ENGINE });
  await page.waitForSelector("svg.gt-map");
}

// Screen coords of a bundle-space point (exercises real event->SVG mapping).
async function screenPoint(page, x, y) {
  return page.evaluate(
    ({ x, y }) => {
      const svg = document.querySelector("svg.gt-map");
      const pt = svg.createSVGPoint();
      pt.x = x;
      pt.y = y;
      const s = pt.matrixTransform(svg.getScreenCTM());
      return { x: s.x, y: s.y };
    },
    { x, y }
  );
}

function region(id) {
  return BUNDLE.regions.find((r) => r.id === id);
}

// ============================== F3: LOCATE ====================================

test("locate front renders all 50 states plus inset frames", async ({ page }) => {
  await showSide(page, { target: "US-CA", mode: "locate", side: "front" });
  await expect(page.locator(".gt-region")).toHaveCount(50);
  await expect(page.locator(".gt-frame")).toHaveCount(2); // AK + HI boxes
  await expect(page.locator(".gt-prompt")).toHaveText("California");
});

test("locate: tapping inside the target is graded correct", async ({ page }) => {
  await showSide(page, { target: "US-CA", mode: "locate", side: "front" });
  const c = region("US-CA").c;
  const p = await screenPoint(page, c[0], c[1]);
  await page.mouse.click(p.x, p.y);
  const attempt = await page.evaluate(() =>
    JSON.parse(localStorage.getItem("geotrainer:locate:us-states:US-CA"))
  );
  expect(attempt.hitId).toBe("US-CA");

  await showSide(page, { target: "US-CA", mode: "locate", side: "back", fresh: false });
  await expect(page.locator(".gt-answer")).toHaveAttribute("data-id", "US-CA");
  await expect(page.locator(".gt-bar.gt-ok")).toContainText("Correct");
});

test("locate: wrong state reports distance and what was tapped", async ({ page }) => {
  await showSide(page, { target: "US-CA", mode: "locate", side: "front" });
  const c = region("US-TX").c;
  const p = await screenPoint(page, c[0], c[1]);
  await page.mouse.click(p.x, p.y);
  await showSide(page, { target: "US-CA", mode: "locate", side: "back", fresh: false });
  const verdict = page.locator(".gt-bar.gt-miss");
  await expect(verdict).toContainText("Missed by");
  await expect(verdict).toContainText("Texas");
});

test("locate: Alaska target tapped on the mainland gives inset hint, no bogus km", async ({ page }) => {
  await showSide(page, { target: "US-AK", mode: "locate", side: "front" });
  const c = region("US-NV").c; // mainland tap
  const p = await screenPoint(page, c[0], c[1]);
  await page.mouse.click(p.x, p.y);
  await showSide(page, { target: "US-AK", mode: "locate", side: "back", fresh: false });
  const verdict = page.locator(".gt-bar.gt-miss");
  await expect(verdict).toContainText("inset");
  await expect(verdict).not.toContainText("km");
});

test("locate: no tap yields Again, not a crash", async ({ page }) => {
  await showSide(page, { target: "US-CA", mode: "locate", side: "front" });
  await showSide(page, { target: "US-CA", mode: "locate", side: "back", fresh: false });
  await expect(page.locator(".gt-bar.gt-miss")).toContainText("No tap recorded");
});

// =========================== F4: POINT-IN-REGION ==============================

test("point front shows a dot inside the target region, no name leak", async ({ page }) => {
  await showSide(page, { target: "US-TN", mode: "point", side: "front" });
  await expect(page.locator(".gt-point")).toHaveCount(1);
  // The dot must be one of the precomputed interior samples.
  const ok = await page.evaluate(() => {
    const dot = document.querySelector(".gt-point");
    const x = parseFloat(dot.getAttribute("cx"));
    const y = parseFloat(dot.getAttribute("cy"));
    const r = window.GT_BUNDLES["us-states"].regions.find((q) => q.id === "US-TN");
    return r.pts.some((p) => Math.abs(p[0] - x) < 0.01 && Math.abs(p[1] - y) < 0.01);
  });
  expect(ok).toBe(true);
  // Lean front: the state name must not appear anywhere.
  const text = await page.evaluate(() => document.body.textContent);
  expect(text).not.toContain("Tennessee");
});

test("point: front and back show the SAME dot; back names the state", async ({ page }) => {
  await showSide(page, { target: "US-TN", mode: "point", side: "front" });
  const frontDot = await page.evaluate(() => {
    const d = document.querySelector(".gt-point");
    return [d.getAttribute("cx"), d.getAttribute("cy")];
  });
  await showSide(page, { target: "US-TN", mode: "point", side: "back", fresh: false });
  const backDot = await page.evaluate(() => {
    const d = document.querySelector(".gt-point");
    return [d.getAttribute("cx"), d.getAttribute("cy")];
  });
  expect(backDot).toEqual(frontDot);
  await expect(page.locator(".gt-prompt")).toHaveText("Tennessee");
  await expect(page.locator(".gt-answer")).toHaveAttribute("data-id", "US-TN");
});

test("point: without storage, front and back still agree (deterministic day seed)", async ({ page }) => {
  await showSide(page, { target: "US-FL", mode: "point", side: "front" });
  const frontDot = await page.evaluate(() => {
    const d = document.querySelector(".gt-point");
    return [d.getAttribute("cx"), d.getAttribute("cy")];
  });
  // Simulate storage loss between sides (worst case).
  await page.evaluate(() => localStorage.clear());
  await showSide(page, { target: "US-FL", mode: "point", side: "back", fresh: false });
  const backDot = await page.evaluate(() => {
    const d = document.querySelector(".gt-point");
    return [d.getAttribute("cx"), d.getAttribute("cy")];
  });
  expect(backDot).toEqual(frontDot);
});

// =========================== F5: PLACE-THE-PIECE ==============================

test("place front shows the piece in the tray and a full basemap", async ({ page }) => {
  await showSide(page, { target: "US-CO", mode: "place", side: "front" });
  await expect(page.locator(".gt-piece")).toHaveCount(1);
  await expect(page.locator(".gt-tray")).toHaveCount(1);
  await expect(page.locator(".gt-region")).toHaveCount(50);
  await expect(page.locator(".gt-prompt")).toHaveText("Colorado");
});

test("place: dragging the piece near its true spot grades well", async ({ page }) => {
  await showSide(page, { target: "US-CO", mode: "place", side: "front" });
  const c = region("US-CO").c;
  // The piece starts with its centroid at the tray; grab there, drop 15px off true.
  const grab = await page.evaluate(() => {
    const piece = document.querySelector(".gt-piece");
    const m = piece.getAttribute("transform").match(/translate\(([-\d.]+),([-\d.]+)\)/);
    const r = window.GT_BUNDLES["us-states"].regions.find((q) => q.id === "US-CO");
    return { x: r.c[0] + parseFloat(m[1]), y: r.c[1] + parseFloat(m[2]) };
  });
  const from = await screenPoint(page, grab.x, grab.y);
  const to = await screenPoint(page, c[0] + 15, c[1]);
  await page.mouse.move(from.x, from.y);
  await page.mouse.down();
  await page.mouse.move(to.x, to.y, { steps: 10 });
  await page.mouse.up();

  const stored = await page.evaluate(() =>
    JSON.parse(localStorage.getItem("geotrainer:place:us-states:US-CO"))
  );
  expect(Math.abs(stored.dx - 15)).toBeLessThan(2);
  expect(Math.abs(stored.dy)).toBeLessThan(2);

  await showSide(page, { target: "US-CO", mode: "place", side: "back", fresh: false });
  await expect(page.locator(".gt-answer")).toHaveAttribute("data-id", "US-CO");
  await expect(page.locator(".gt-piece.gt-ghost")).toHaveCount(1);
  await expect(page.locator(".gt-bar.gt-ok")).toContainText("Great placement");
});

test("place: a wildly wrong drop grades Again", async ({ page }) => {
  await showSide(page, { target: "US-CO", mode: "place", side: "front" });
  const grab = await page.evaluate(() => {
    const piece = document.querySelector(".gt-piece");
    const m = piece.getAttribute("transform").match(/translate\(([-\d.]+),([-\d.]+)\)/);
    const r = window.GT_BUNDLES["us-states"].regions.find((q) => q.id === "US-CO");
    return { x: r.c[0] + parseFloat(m[1]), y: r.c[1] + parseFloat(m[2]) };
  });
  const fl = region("US-FL").c; // drop Colorado on Florida
  const from = await screenPoint(page, grab.x, grab.y);
  const to = await screenPoint(page, fl[0], fl[1]);
  await page.mouse.move(from.x, from.y);
  await page.mouse.down();
  await page.mouse.move(to.x, to.y, { steps: 10 });
  await page.mouse.up();
  await showSide(page, { target: "US-CO", mode: "place", side: "back", fresh: false });
  await expect(page.locator(".gt-bar.gt-miss")).toContainText("Off by");
  await expect(page.locator(".gt-suggest")).toContainText("Again");
});

// ============================ BOOT ROBUSTNESS =================================

test("survives out-of-order load: engine before DOM + bundle", async ({ page }) => {
  await page.setContent("<!doctype html><html><head></head><body></body></html>");
  await page.addScriptTag({ content: ENGINE });
  await page.evaluate((bundle) => {
    window.GT_BUNDLES = { "us-states": bundle };
    const app = document.createElement("div");
    app.className = "gt-app";
    app.setAttribute("data-scope", "us-states");
    app.setAttribute("data-target", "US-FL");
    app.setAttribute("data-side", "front");
    app.setAttribute("data-mode", "locate");
    document.body.appendChild(app);
  }, BUNDLE);
  await expect(page.locator("svg.gt-map")).toBeVisible({ timeout: 5000 });
  await expect(page.locator(".gt-prompt")).toHaveText("Florida");
});
