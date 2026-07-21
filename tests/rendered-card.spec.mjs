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
  { scope: "us-states", regions: 50, modes: ["locate", "point", "place", "sketch", "draw"] },
  { scope: "europe-countries", regions: 51, modes: ["locate", "point", "place", "sketch", "draw"] },
];

test.describe("shipped inlined cards", () => {
  test.skip(!existsSync(FIX("card-us-states-locate-front.html")), "run make apkg first");

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

  test("locate fixture registers a real tap (shipped form)", async ({ page }) => {
    await page.setContent(readFileSync(FIX("card-us-states-locate-front.html"), "utf-8"));
    await page.waitForSelector("svg.gt-map");
    const p = await page.evaluate(() => {
      const b = window.GT_BUNDLES["us-states"];
      const r = b.regions.find((x) => x.id === "US-CA");
      const svg = document.querySelector("svg.gt-map");
      const pt = svg.createSVGPoint();
      pt.x = r.c[0];
      pt.y = r.c[1];
      const s = pt.matrixTransform(svg.getScreenCTM());
      return { x: s.x, y: s.y };
    });
    await page.mouse.click(p.x, p.y);
    await expect(page.locator(".gt-attempt")).toBeVisible();
  });

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

});
