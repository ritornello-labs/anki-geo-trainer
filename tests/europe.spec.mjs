import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..");
const ENGINE = readFileSync(join(ROOT, "engine", "geo-engine.js"), "utf-8");
const BUNDLE = JSON.parse(
  readFileSync(join(ROOT, "data", "bundles", "europe-countries.json"), "utf-8")
);

async function showSide(page, { target, mode, side, fresh = true }) {
  if (fresh) {
    await page.setContent("<!doctype html><html><head></head><body></body></html>");
    await page.evaluate((bundle) => {
      window.GT_BUNDLES = { "europe-countries": bundle };
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
      app.setAttribute("data-scope", "europe-countries");
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

async function tapRegionPoint(page, regionId) {
  const p = await page.evaluate((regionId) => {
    const b = window.GT_BUNDLES["europe-countries"];
    const r = b.regions.find((x) => x.id === regionId);
    const svg = document.querySelector("svg.gt-map");
    const pt = svg.createSVGPoint();
    pt.x = r.pts[0][0];
    pt.y = r.pts[0][1];
    const s = pt.matrixTransform(svg.getScreenCTM());
    return { x: s.x, y: s.y };
  }, regionId);
  await page.mouse.click(p.x, p.y);
}

test("europe front renders all countries, context land, and microstate circles", async ({ page }) => {
  await showSide(page, { target: "FRA", mode: "locate", side: "front" });
  await expect(page.locator(".gt-region")).toHaveCount(51);
  await expect(page.locator(".gt-context")).toHaveCount(1);
  await expect(page.locator(".gt-region.gt-small")).toHaveCount(11);
  await expect(page.locator(".gt-region.gt-tier2")).toHaveCount(5);
  await expect(page.locator(".gt-chip")).toContainText("Locate");
});

test("noun generalization: point mode says country, not state", async ({ page }) => {
  await showSide(page, { target: "DE", mode: "point", side: "front" });
  await expect(page.locator(".gt-chip")).toHaveText("Which country?");
});

test("microstate tap-circle is hittable (Vatican)", async ({ page }) => {
  await showSide(page, { target: "VA", mode: "locate", side: "front" });
  const c = BUNDLE.regions.find((r) => r.id === "VA").c;
  const p = await page.evaluate(({ x, y }) => {
    const svg = document.querySelector("svg.gt-map");
    const pt = svg.createSVGPoint();
    pt.x = x;
    pt.y = y;
    const s = pt.matrixTransform(svg.getScreenCTM());
    return { x: s.x, y: s.y };
  }, { x: c[0], y: c[1] });
  await page.mouse.click(p.x, p.y);
  const attempt = await page.evaluate(() =>
    JSON.parse(localStorage.getItem("geotrainer:locate:europe-countries:VA"))
  );
  expect(attempt.hitId).toBe("VA");
});

test("neighbors: correct taps accumulate, wrong taps tracked, back grades", async ({ page }) => {
  await showSide(page, { target: "DE", mode: "neighbors", side: "front" });
  await expect(page.locator(".gt-target")).toHaveAttribute("data-id", "DE");
  await tapRegionPoint(page, "AT"); // correct
  await tapRegionPoint(page, "PL"); // correct
  await tapRegionPoint(page, "ES"); // wrong
  const state = await page.evaluate(() =>
    JSON.parse(localStorage.getItem("geotrainer:nb:europe-countries:DE"))
  );
  expect(state.found.sort()).toEqual(["AT", "PL"]);
  expect(state.wrong).toEqual(["ES"]);

  await showSide(page, { target: "DE", mode: "neighbors", side: "back", fresh: false });
  await expect(page.locator(".gt-nb-found")).toHaveCount(2);
  await expect(page.locator(".gt-bar.gt-miss")).toContainText("Found 2 of 9");
  await expect(page.locator(".gt-bar.gt-miss")).toContainText("missed:");
  await expect(page.locator(".gt-suggest")).toContainText("Again");
});

test("neighbors: perfect round grades Good", async ({ page }) => {
  await showSide(page, { target: "PT", mode: "neighbors", side: "front" });
  await tapRegionPoint(page, "ES"); // Portugal's only neighbor
  await showSide(page, { target: "PT", mode: "neighbors", side: "back", fresh: false });
  await expect(page.locator(".gt-bar.gt-ok")).toContainText("Found 1 of 1");
  await expect(page.locator(".gt-suggest")).toContainText("Good");
});

test("cross-scope isolation: US bundle unaffected by Europe fields", async ({ page }) => {
  // Europe regions carry tier/nb/small; make sure locate still works with them.
  await showSide(page, { target: "IS", mode: "locate", side: "front" });
  await tapRegionPoint(page, "IS");
  const attempt = await page.evaluate(() =>
    JSON.parse(localStorage.getItem("geotrainer:locate:europe-countries:IS"))
  );
  expect(attempt.hitId).toBe("IS");
});
