// Exercises the engine's `members` mode against a real-world bundle: the
// world-countries map and bloc answer sets built by the sibling
// world-geography-concepts repo (`make drill-fixtures` there). Skipped when
// those fixtures are absent, so this repo still tests standalone.
//
// Served over HTTP rather than file://, because the engine carries the
// front's taps to the back through localStorage, which browsers refuse on a
// file:// origin.
import { test, expect } from "@playwright/test";
import { createServer } from "node:http";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const DIR = "/Users/elvis/Code/anki-studying/world-geography-concepts/out/qa/drill";

test.skip(!existsSync(resolve(DIR, "asean-front.html")),
  "bloc drill fixtures not built (run `make drill-fixtures` in world-geography-concepts)");

let server, base;
test.beforeAll(async () => {
  server = createServer((req, res) => {
    const name = decodeURIComponent(req.url.slice(1)) || "index.html";
    try {
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      res.end(readFileSync(resolve(DIR, name)));
    } catch {
      res.writeHead(404);
      res.end("no");
    }
  });
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  base = `http://127.0.0.1:${server.address().port}/`;
});
test.afterAll(async () => {
  await new Promise((r) => server.close(r));
});

// Tap the region's own label point, not the centre of its bounding box:
// Indonesia's bbox centre is open sea, so a bbox tap misses the country
// entirely -- a fact about archipelagos, not about the engine.
async function tap(page, id) {
  const ok = await page.evaluate((rid) => {
    const bundle = window.GT_BUNDLES["world-countries"];
    const region = bundle.regions.find((r) => r.id === rid);
    if (!region) return "missing region " + rid;
    const svg = document.querySelector("svg.gt-map");
    const pt = svg.createSVGPoint();
    pt.x = region.c[0];
    pt.y = region.c[1];
    const screen = pt.matrixTransform(svg.getScreenCTM());
    svg.dispatchEvent(new MouseEvent("click", {
      clientX: screen.x, clientY: screen.y, bubbles: true,
    }));
    return true;
  }, id);
  expect(ok, `tap ${id}`).toBe(true);
}

test("front mounts a world map with every country clickable", async ({ page }) => {
  await page.goto(base + "asean-front.html");
  await page.waitForSelector("svg.gt-map");
  expect(await page.locator("svg.gt-map path[data-id]").count()).toBeGreaterThan(200);
  await expect(page.locator(".gt-hint")).toContainText("0 / 11");
  await expect(page.locator(".gt-app")).toContainText("ASEAN");
});

test("tapping a member counts it; tapping a non-member is wrong", async ({ page }) => {
  await page.goto(base + "asean-front.html");
  await page.waitForSelector("svg.gt-map");
  await tap(page, "IDN");
  await expect(page.locator(".gt-hint")).toContainText("1 / 11");
  await tap(page, "IND"); // India is not in ASEAN
  await expect(page.locator(".gt-hint")).toContainText("1 wrong");
});

test("microstate members are tappable at world scale", async ({ page }) => {
  await page.goto(base + "caricom-front.html");
  await page.waitForSelector("svg.gt-map");
  for (const id of ["BRB", "ATG", "DMA"]) await tap(page, id);
  await expect(page.locator(".gt-hint")).toContainText("3 / 15");
});

test("back scores hits, misses and false positives", async ({ page }) => {
  await page.goto(base + "asean-front.html");
  await page.waitForSelector("svg.gt-map");
  await tap(page, "IDN");
  await tap(page, "IND");
  await page.goto(base + "asean-back.html");
  await page.waitForSelector("svg.gt-map");
  const text = await page.locator(".gt-app").innerText();
  expect(text).toContain("Found 1 of 11");
  expect(text).toMatch(/missed:/);
  expect(text).toMatch(/wrong:/);
});

test("a perfect run with no false positives scores full marks", async ({ page }) => {
  await page.goto(base + "asean-front.html");
  await page.waitForSelector("svg.gt-map");
  const ids = await page.evaluate(() => window.GT_SETS["world-countries:asean"].ids);
  for (const id of ids) await tap(page, id);
  await expect(page.locator(".gt-hint")).toContainText("11 / 11");
  await page.goto(base + "asean-back.html");
  await page.waitForSelector("svg.gt-map");
  await expect(page.locator(".gt-ok")).toContainText("Found 11 of 11");
  await expect(page.locator(".gt-app")).not.toContainText("wrong:");
});
