import { test, expect } from "@playwright/test";
import { readState } from "./state-helper.mjs";
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

// Verifies the SHIPPED inlined card form (base64 bundle + brace-guarded engine,
// exactly as Anki renders it) boots and behaves in real engines. Fixtures are
// produced by scripts/emit_card_fixture.py.
const HERE = dirname(fileURLToPath(import.meta.url));
const FIX = (name) => join(HERE, "fixtures", name);

const CASES = [
  { scope: "us-states", regions: 50, modes: ["point", "place", "sketch", "draw"] },
  { scope: "europe-countries", regions: 51, modes: ["point", "place", "sketch", "draw"] },
];

const PHYSICAL_CASES = [
  { scope: "atmospheric-cells", mode: "cell", chip: "Trace circulation cell" },
  { scope: "atmospheric-pressure-belts", mode: "belt", chip: "Place pressure belt" },
  { scope: "world-prevailing-winds", mode: "wind", chip: "Trace prevailing wind" },
  { scope: "world-jet-streams", mode: "jet", chip: "Trace jet stream" },
  { scope: "south-asia-monsoon-winds", mode: "seasonalwind", chip: "Trace seasonal wind" },
  { scope: "indian-ocean-seasonal-currents", mode: "seasonalcurrent", chip: "Trace seasonal current" },
  { scope: "atlantic-overturning", mode: "amoc", chip: "Order Atlantic overturning" },
  { scope: "equatorial-pacific-enso", mode: "enso", chip: "Recall ENSO pattern" },
];

test.describe("shipped inlined cards", () => {
  test.skip(!existsSync(FIX("card-us-states-point-front.html")), "run make apkg first");

  for (const { scope, regions, modes } of CASES) {
    for (const mode of modes) {
      test(`${scope}/${mode} front fixture boots from its inlined data`, async ({ page }) => {
        await page.setContent(readFileSync(FIX(`card-${scope}-${mode}-front.html`), "utf-8"));
        await expect(page.locator("svg.gt-map")).toBeVisible({ timeout: 5000 });
        if (mode === "draw") {
          // draw ships per-note ShapeData instead of the basemap bundle
          await expect(page.locator("svg.gt-canvas")).toBeVisible();
        } else {
          const expected = mode === "sketch"
            ? await page.evaluate((s) => window.GT_BUNDLES[s].regions.filter((r) => !r.small).length, scope)
            : regions;
          await expect(page.locator(".gt-region")).toHaveCount(expected);
        }
      });
    }
  }

  test("point fixture front->back agreement in shipped form", async ({ page }) => {
    await page.setContent(readFileSync(FIX("card-us-states-point-front.html"), "utf-8"));
    await page.waitForSelector(".gt-point");
    const frontDot = await page.evaluate(() => {
      const d = document.querySelector(".gt-point");
      return [d.getAttribute("cx"), d.getAttribute("cy")];
    });
    await page.setContent(readFileSync(FIX("card-us-states-point-back.html"), "utf-8"));
    await page.waitForSelector(".gt-point");
    const backDot = await page.evaluate(() => {
      const d = document.querySelector(".gt-point");
      return [d.getAttribute("cx"), d.getAttribute("cy")];
    });
    expect(backDot).toEqual(frontDot);
    await expect(page.locator(".gt-answer")).toHaveAttribute("data-id", "US-CA");
  });

  test("direction-aware current fixture boots with per-note data", async ({ page }) => {
    await page.setContent(
      readFileSync(FIX("card-world-ocean-currents-current-front.html"), "utf-8")
    );
    await expect(page.locator("svg.gt-map")).toBeVisible({ timeout: 5000 });
    await expect(page.locator(".gt-chip")).toHaveText("Trace current");
    const route = await page.evaluate(
      () => window.GT_SHAPES["world-ocean-currents:gulf-stream"]
    );
    expect(route.name).toBe("Gulf Stream");
    expect(route.paths[0].length).toBeGreaterThan(4);
  });

  for (const { scope, mode, chip } of PHYSICAL_CASES) {
    test(`${scope}/${mode} shipped fixture boots with per-note data`, async ({ page }) => {
      await page.setContent(readFileSync(FIX(`card-${scope}-${mode}-front.html`), "utf-8"));
      await expect(page.locator("svg.gt-map")).toBeVisible({ timeout: 5000 });
      await expect(page.locator(".gt-chip")).toHaveText(chip);
      const payload = await page.evaluate(([s, m]) => window.GT_SHAPES[`${s}:${m}`], [scope,
        scope === "atmospheric-cells" ? "01-hadley-pair" :
        scope === "atmospheric-pressure-belts" ? "subtropical-highs" :
        scope === "world-prevailing-winds" ? "northeast-trades" :
        scope === "world-jet-streams" ? "polar-front-jet-north" :
        scope === "south-asia-monsoon-winds" ? "south-asia-summer" :
        scope === "indian-ocean-seasonal-currents" ? "somali-current-summer" :
        scope === "atlantic-overturning" ? "02-pathway-order" :
        "02-el-nino"]);
      expect(payload.name).toBeTruthy();
      if (mode.startsWith("seasonal")) {
        await expect(page.locator(".gt-season")).toHaveText(payload.season);
      }
    });
  }

});
