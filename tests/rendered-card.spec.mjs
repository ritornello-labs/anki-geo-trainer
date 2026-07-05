import { test, expect } from "@playwright/test";
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

// Verifies the SHIPPED inlined card form (base64 bundle + brace-guarded engine,
// exactly as Anki renders it) boots and hit-tests in real engines. The fixture
// is produced by scripts/emit_card_fixture.py.
const HERE = dirname(fileURLToPath(import.meta.url));
const FRONT = join(HERE, "fixtures", "card-front.html");

test.describe("shipped inlined card", () => {
  test.skip(!existsSync(FRONT), "run scripts/emit_card_fixture.py first (make apkg)");

  test("front fixture boots the map from the base64 bundle", async ({ page }) => {
    await page.setContent(readFileSync(FRONT, "utf-8"));
    // If atob/JSON.parse of the bundle or the guarded engine were broken, no
    // map would appear.
    await expect(page.locator("svg.gt-map")).toBeVisible({ timeout: 5000 });
    await expect(page.locator(".gt-region")).toHaveCount(48);
    await expect(page.locator(".gt-prompt")).toHaveText("California");
  });

  test("tapping the inlined map registers an attempt", async ({ page }) => {
    await page.setContent(readFileSync(FRONT, "utf-8"));
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
    // The attempt marker becomes visible on a successful hit-test.
    await expect(page.locator(".gt-attempt")).toBeVisible();
  });
});
