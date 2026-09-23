import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..");
const D3_ARRAY = readFileSync(join(ROOT, "node_modules", "d3-array", "dist", "d3-array.min.js"), "utf-8");
const D3_GEO = readFileSync(join(ROOT, "node_modules", "d3-geo", "dist", "d3-geo.min.js"), "utf-8");
const ENGINE = readFileSync(join(ROOT, "engine", "globe-placement.js"), "utf-8");
const CSS = readFileSync(join(ROOT, "anki", "globe-placement", "card.css"), "utf-8");
const BUNDLE = JSON.parse(readFileSync(join(ROOT, "data", "bundles", "world-islands.json"), "utf-8"));

async function canvasBox(page) {
  return page.locator(".ig-canvas").boundingBox();
}

test.beforeEach(async ({ page }) => {
  await page.setContent(`<!doctype html><html><head><style>${CSS}</style></head><body class="card"><main id="card"></main><button id="reveal" type="button">Reveal answer</button></body></html>`);
  await page.addScriptTag({ content: D3_ARRAY });
  await page.addScriptTag({ content: D3_GEO });
  await page.addScriptTag({ content: ENGINE });
  await page.evaluate((bundle) => {
    window.__ISLAND_GLOBE_BUNDLE__ = bundle;
    window.__renderGlobe = function (side) {
      const item = bundle.targets.features.find((candidate) => candidate.properties.key === "cok");
      const controls = side === "front"
        ? '<div class="ig-toolbar" role="group"><button class="ig-button" type="button" data-mode="rotate" aria-pressed="true">Rotate</button><button class="ig-button" type="button" data-mode="mark" aria-pressed="false">Draw ellipse</button><button class="ig-button" type="button" data-action="clear">Clear</button></div>'
        : '<div class="ig-toolbar" role="group"><button class="ig-button" type="button" data-mode="rotate" aria-pressed="true">Rotate</button><button class="ig-button" type="button" data-action="focus">Focus answer</button></div>';
      const result = side === "back" ? '<div class="ig-result" data-result></div>' : "";
      document.getElementById("card").innerHTML =
        '<div class="ig-card" data-island-globe data-side="' + side + '" data-family="place" data-key="cok">' +
          '<div class="ig-mast"><span>GeoTrainer</span><span class="ig-chip">Globe placement</span></div>' +
          '<h1 class="ig-prompt">' + item.properties.name + '</h1>' +
          '<div class="ig-stage"><canvas class="ig-canvas"></canvas>' + controls + '</div>' +
          result +
        '</div>';
      window.IslandGlobe.mount(document.querySelector("[data-island-globe]"), bundle);
    };
    document.getElementById("reveal").addEventListener("click", function () {
      window.__renderGlobe("back");
    });
    window.__renderGlobe("front");
  }, BUNDLE);
  await expect(page.locator(".ig-prompt")).toHaveText("Cook Islands");
});

test("starts at a randomly tilted globe orientation", async ({ page }) => {
  await expect(page.locator("[data-island-globe]")).toHaveAttribute("data-graticule-step", "15");
  await expect(page.locator("[data-island-globe]")).toHaveAttribute("data-reference-guides", "equator,tropics");
  const rotation = await page.evaluate(() => window.__islandGlobeState.getState().rotation);
  expect(rotation[0]).toBeGreaterThanOrEqual(-180);
  expect(rotation[0]).toBeLessThan(180);
  expect(rotation[1]).toBeGreaterThanOrEqual(-22);
  expect(rotation[1]).toBeLessThanOrEqual(22);
});

test("draws an ellipse from opposite bounding-box corners and reveals every deck island", async ({ page }) => {
  const box = await canvasBox(page);
  await page.getByRole("button", { name: "Draw ellipse" }).click();
  await page.mouse.move(box.x + box.width * 0.42, box.y + box.height * 0.44);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width * 0.70, box.y + box.height * 0.62, { steps: 5 });
  await page.mouse.up();

  const frontState = await page.evaluate(() => window.__islandGlobeState.getState());
  expect(frontState.guess.geometry.type).toBe("Polygon");
  expect(frontState.guess.geometry.coordinates[0].length).toBeGreaterThan(40);
  expect(Math.abs(frontState.guess.screen.center[0] - box.width * 0.56)).toBeLessThan(1.5);
  expect(Math.abs(frontState.guess.screen.center[1] - box.height * 0.53)).toBeLessThan(1.5);
  expect(Math.abs(frontState.guess.screen.radii[0] - box.width * 0.14)).toBeLessThan(1.5);
  expect(Math.abs(frontState.guess.screen.radii[1] - box.height * 0.09)).toBeLessThan(1.5);

  await page.getByRole("button", { name: "Reveal answer" }).click();
  const answer = page.locator("[data-island-globe]");
  await expect(answer).toHaveAttribute("data-side", "back");
  await expect(answer).toHaveAttribute("data-islands-shown", "67");
  await expect(page.locator("[data-result]")).toContainText("Suggested grade");
  await expect(page.locator("[data-result]")).toContainText("island components covered");
  await expect(page.locator("[data-result]")).toContainText("center offset");
  await expect(page.locator("[data-result]")).toContainText("target footprint");

  const backState = await page.evaluate(() => window.__islandGlobeState.getState());
  expect(backState.rotation).toEqual(frontState.rotation);
  expect(backState.guess.geometry).toEqual(frontState.guess.geometry);

  await page.getByRole("button", { name: "Focus answer" }).click();
  const focusedState = await page.evaluate(() => window.__islandGlobeState.getState());
  expect(focusedState.rotation[0]).toBeCloseTo(159.41474, 3);
  expect(focusedState.rotation[1]).toBeCloseTo(17.02642, 3);
});

test("clear removes the recorded prediction", async ({ page }) => {
  const box = await canvasBox(page);
  await page.getByRole("button", { name: "Draw ellipse" }).click();
  await page.mouse.move(box.x + box.width * 0.5, box.y + box.height * 0.5);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width * 0.62, box.y + box.height * 0.58);
  await page.mouse.up();
  await page.getByRole("button", { name: "Clear" }).click();
  expect(await page.evaluate(() => window.__islandGlobeState.getState().guess)).toBeNull();
});

test("moves and resizes an existing ellipse", async ({ page }) => {
  const box = await canvasBox(page);
  await page.getByRole("button", { name: "Draw ellipse" }).click();
  await page.mouse.move(box.x + box.width * 0.40, box.y + box.height * 0.42);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width * 0.62, box.y + box.height * 0.58);
  await page.mouse.up();
  const initial = await page.evaluate(() => window.__islandGlobeState.getState().guess.screen);

  await page.mouse.move(box.x + initial.center[0], box.y + initial.center[1]);
  await page.mouse.down();
  await page.mouse.move(box.x + initial.center[0] + 24, box.y + initial.center[1] - 16);
  await page.mouse.up();
  const moved = await page.evaluate(() => window.__islandGlobeState.getState().guess.screen);
  expect(moved.center[0] - initial.center[0]).toBeCloseTo(24, 0);
  expect(moved.center[1] - initial.center[1]).toBeCloseTo(-16, 0);

  await page.mouse.move(box.x + moved.center[0] + moved.radii[0], box.y + moved.center[1] + moved.radii[1]);
  await page.mouse.down();
  await page.mouse.move(box.x + moved.center[0] + moved.radii[0] + 30, box.y + moved.center[1] + moved.radii[1] + 20);
  await page.mouse.up();
  const resized = await page.evaluate(() => window.__islandGlobeState.getState().guess.screen);
  expect(resized.radii[0]).toBeGreaterThan(moved.radii[0] + 12);
  expect(resized.radii[1]).toBeGreaterThan(moved.radii[1] + 7);
});

test("rejects both pinprick and continent-sized placement ellipses", async ({ page }) => {
  const grades = await page.evaluate(() => {
    const target = window.__ISLAND_GLOBE_BUNDLE__.targets.features.find((item) => item.properties.key === "fji");
    const focus = target.properties.focus;
    const component = target.properties.components[0];
    function score(center, radius) {
      return window.IslandGlobe.scorePlacement(target, {
        center,
        geometry: window.d3.geoCircle().center(center).radius(radius)(),
      }).grade;
    }
    return {
      pinprick: score(component, 0.5),
      useful: score(focus, 8),
      enormous: score(focus, 40),
    };
  });
  expect(grades).toEqual({ pinprick: "Again", useful: "Good", enormous: "Again" });
});
