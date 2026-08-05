// The `members` mode is the tap-a-set interaction with an injected answer
// list: same machinery as tap-all-neighbors, but the set comes from the note
// (which countries are in this bloc?) rather than from the target's borders.
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

const SET_ID = "test-set";

async function showSide(page, { side, ids, mounted = true }) {
  await page.setContent("<!doctype html><html><head></head><body></body></html>");
  await page.evaluate(
    ({ bundle, ids, setId }) => {
      window.GT_BUNDLES = { "us-states": bundle };
      if (ids) {
        window.GT_SETS = {
          ["us-states:" + setId]: { name: "Test Bloc", ids: ids, chip: "Members" },
        };
      }
    },
    { bundle: BUNDLE, ids, setId: SET_ID }
  );
  await page.evaluate((setId) => {
    const app = document.createElement("div");
    app.className = "gt-app";
    app.setAttribute("data-scope", "us-states");
    app.setAttribute("data-target", setId);
    app.setAttribute("data-side", document.title || "front");
    app.setAttribute("data-mode", "members");
    document.body.appendChild(app);
  }, SET_ID);
  await page.evaluate((s) => { document.querySelector(".gt-app").setAttribute("data-side", s); }, side);
  await page.addScriptTag({ content: ENGINE });
  if (mounted) await page.waitForSelector("svg.gt-map");
}

async function tapRegion(page, id) {
  await page.evaluate((regionId) => {
    const path = document.querySelector(`path[data-id="${regionId}"]`);
    const box = path.getBoundingClientRect();
    const svg = document.querySelector("svg.gt-map");
    svg.dispatchEvent(
      new MouseEvent("click", {
        clientX: box.x + box.width / 2,
        clientY: box.y + box.height / 2,
        bubbles: true,
      })
    );
  }, id);
}

function firstIds(n) {
  return BUNDLE.regions.slice(0, n).map((r) => r.id);
}

test("members front prompts with the set name and counts taps against the set", async ({ page }) => {
  const ids = firstIds(3);
  await showSide(page, { side: "front", ids });

  await expect(page.locator(".gt-app")).toContainText("Test Bloc");
  await expect(page.locator(".gt-hint")).toContainText("0 / 3");

  await tapRegion(page, ids[0]);
  await expect(page.locator(".gt-hint")).toContainText("1 / 3");
  await expect(page.locator(`path[data-id="${ids[0]}"]`)).toHaveClass(/gt-nb-found/);
});

test("tapping a found member again un-picks it, so a misfire is recoverable", async ({ page }) => {
  const ids = firstIds(3);
  await showSide(page, { side: "front", ids });

  await tapRegion(page, ids[0]);
  await expect(page.locator(".gt-hint")).toContainText("1 / 3");
  await tapRegion(page, ids[0]);
  await expect(page.locator(".gt-hint")).toContainText("0 / 3");
  await expect(page.locator(`path[data-id="${ids[0]}"]`)).not.toHaveClass(/gt-nb-found/);
});

test("a non-member tap is recorded as wrong", async ({ page }) => {
  const ids = firstIds(2);
  const outsider = BUNDLE.regions[5].id;
  await showSide(page, { side: "front", ids });

  await tapRegion(page, outsider);
  await expect(page.locator(".gt-hint")).toContainText("1 wrong");
});

test("back names every missed member and every false positive", async ({ page }) => {
  const ids = firstIds(3);
  const outsider = BUNDLE.regions[7];
  await showSide(page, { side: "front", ids });
  await tapRegion(page, ids[0]);
  await tapRegion(page, outsider.id);

  await page.evaluate(() => {
    document.body.innerHTML = "";
    const app = document.createElement("div");
    app.className = "gt-app";
    app.setAttribute("data-scope", "us-states");
    app.setAttribute("data-target", "test-set");
    app.setAttribute("data-side", "back");
    app.setAttribute("data-mode", "members");
    document.body.appendChild(app);
    window.GeoTrainer.mountAll();
  });
  await page.waitForSelector("svg.gt-map");

  const missedNames = BUNDLE.regions.slice(1, 3).map((r) => r.name);
  const text = await page.locator(".gt-app").innerText();
  expect(text).toContain("Found 1 of 3");
  for (const name of missedNames) expect(text).toContain(name);
  expect(text).toContain(outsider.name);
});

test("full marks require every member and zero false positives", async ({ page }) => {
  const ids = firstIds(3);
  await showSide(page, { side: "front", ids });
  for (const id of ids) await tapRegion(page, id);

  await page.evaluate(() => {
    document.body.innerHTML = "";
    const app = document.createElement("div");
    app.className = "gt-app";
    app.setAttribute("data-scope", "us-states");
    app.setAttribute("data-target", "test-set");
    app.setAttribute("data-side", "back");
    app.setAttribute("data-mode", "members");
    document.body.appendChild(app);
    window.GeoTrainer.mountAll();
  });
  await page.waitForSelector("svg.gt-map");

  await expect(page.locator(".gt-ok")).toContainText("Found 3 of 3");
  await expect(page.locator(".gt-app")).not.toContainText("wrong:");
});

test("mounting waits for the answer-set script, which may arrive after the engine", async ({ page }) => {
  await showSide(page, { side: "front", ids: null, mounted: false });
  await expect(page.locator("svg.gt-map")).toHaveCount(0);

  await page.evaluate((ids) => {
    window.GT_SETS = { "us-states:test-set": { name: "Late Bloc", ids: ids } };
  }, firstIds(2));
  await page.waitForSelector("svg.gt-map");
  await expect(page.locator(".gt-app")).toContainText("Late Bloc");
});
