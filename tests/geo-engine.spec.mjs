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
async function showFront(page, target) {
  await page.setContent("<!doctype html><html><head></head><body></body></html>");
  await page.evaluate(
    ({ bundle, target }) => {
      window.GT_BUNDLES = { "us-states": bundle };
      const app = document.createElement("div");
      app.className = "gt-app";
      app.setAttribute("data-scope", "us-states");
      app.setAttribute("data-target", target);
      app.setAttribute("data-side", "front");
      document.body.appendChild(app);
    },
    { bundle: BUNDLE, target }
  );
  await page.addScriptTag({ content: ENGINE });
  await page.waitForSelector("svg.gt-map");
}

async function showBack(page, target) {
  await page.evaluate((target) => {
    document.body.innerHTML = "";
    const app = document.createElement("div");
    app.className = "gt-app";
    app.setAttribute("data-scope", "us-states");
    app.setAttribute("data-target", target);
    app.setAttribute("data-side", "back");
    document.body.appendChild(app);
    window.GeoTrainer.mountAll();
  }, target);
  await page.waitForSelector(".gt-bar");
}

// A real mouse click at the projected centroid of a region (exercises the
// engine's own click listener + SVG coordinate mapping).
async function tapRegion(page, regionId) {
  const p = await page.evaluate((regionId) => {
    const b = window.GT_BUNDLES["us-states"];
    const r = b.regions.find((x) => x.id === regionId);
    const svg = document.querySelector("svg.gt-map");
    const pt = svg.createSVGPoint();
    pt.x = r.c[0];
    pt.y = r.c[1];
    const s = pt.matrixTransform(svg.getScreenCTM());
    return { x: s.x, y: s.y };
  }, regionId);
  await page.mouse.click(p.x, p.y);
}

test("front renders a full blank map with the prompt", async ({ page }) => {
  await showFront(page, "US-CA");
  await expect(page.locator(".gt-region")).toHaveCount(48);
  await expect(page.locator(".gt-prompt")).toHaveText("California");
  await expect(page.locator(".gt-chip")).toHaveText("Locate");
  // Nothing placed yet.
  await expect(page.locator(".gt-attempt")).toHaveCount(0);
});

test("tapping inside the target is graded correct", async ({ page }) => {
  await showFront(page, "US-CA");
  await tapRegion(page, "US-CA");
  const attempt = await page.evaluate(() =>
    JSON.parse(localStorage.getItem("geotrainer:attempt:us-states:US-CA"))
  );
  expect(attempt.hitId).toBe("US-CA");

  await showBack(page, "US-CA");
  await expect(page.locator(".gt-answer")).toHaveAttribute("data-id", "US-CA");
  await expect(page.locator(".gt-bar.gt-ok")).toContainText("Correct");
  await expect(page.locator(".gt-attempt.gt-good")).toHaveCount(1);
});

test("tapping the wrong state reports distance and what was tapped", async ({ page }) => {
  await showFront(page, "US-CA");
  await tapRegion(page, "US-TX");
  await showBack(page, "US-CA");
  const verdict = page.locator(".gt-bar.gt-miss");
  await expect(verdict).toContainText("Missed by");
  await expect(verdict).toContainText("Texas");
  await expect(page.locator(".gt-attempt.gt-bad")).toHaveCount(1);
  await expect(page.locator(".gt-link")).toHaveCount(1);
});

test("no tap yields an Again suggestion, not a crash", async ({ page }) => {
  await showFront(page, "US-CA");
  // deliberately no tap
  await showBack(page, "US-CA");
  await expect(page.locator(".gt-bar.gt-miss")).toContainText("No tap recorded");
  await expect(page.locator(".gt-answer")).toHaveCount(1);
});

test("survives out-of-order load: engine before DOM + bundle", async ({ page }) => {
  await page.setContent("<!doctype html><html><head></head><body></body></html>");
  // Engine evaluates first, when there is no .gt-app and no bundle yet.
  await page.addScriptTag({ content: ENGINE });
  // Only afterwards do the bundle and the card container appear.
  await page.evaluate(
    ({ bundle }) => {
      window.GT_BUNDLES = { "us-states": bundle };
      const app = document.createElement("div");
      app.className = "gt-app";
      app.setAttribute("data-scope", "us-states");
      app.setAttribute("data-target", "US-FL");
      app.setAttribute("data-side", "front");
      document.body.appendChild(app);
    },
    { bundle: BUNDLE }
  );
  // boot()'s retry loop should still mount it.
  await expect(page.locator("svg.gt-map")).toBeVisible({ timeout: 5000 });
  await expect(page.locator(".gt-prompt")).toHaveText("Florida");
});
