import { test, expect } from "@playwright/test";
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { readState } from "./state-helper.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const FIX = (name) => join(HERE, "fixtures", name);
const SCOPE = "physical-foundations";
const CARDS = [
  ["01-equatorial-ascent", "Near 0°"],
  ["02-northern-trades", "Westward"],
  ["03-coastal-upwelling", "Cool water rises from below"],
  ["04-south-asian-summer", "Ocean toward land"],
  ["05-neutral-pacific", "Near Indonesia, west"],
  ["06-weak-trades", "Surface water tends to warm"],
];

test.describe("physical-foundations pilot", () => {
  test.skip(!existsSync(FIX(`card-${SCOPE}-reason-01-equatorial-ascent-front.html`)),
    "run python scripts/emit_card_fixture.py first");

  for (const [id, correct] of CARDS) {
    test(`${id}: answers in the same layout with a visible choice and explanation`, async ({ page }) => {
      const prefix = `card-${SCOPE}-reason-${id}`;
      await page.setContent(readFileSync(FIX(`${prefix}-front.html`), "utf-8"));
      await expect(page.locator(".gt-reason-scene")).toBeVisible();
      const frontQuestion = await page.locator(".gt-prompt").innerText();
      const frontChoices = await page.locator(".gt-reason-choices button").allInnerTexts();
      await page.locator(".gt-reason-choices button", { hasText: correct }).click();
      expect((await readState(page, "reason", SCOPE, id)).selected).toBe(correct);

      await page.setContent(readFileSync(FIX(`${prefix}-back.html`), "utf-8"));
      await expect(page.locator(".gt-reason-scene")).toBeVisible();
      await expect(page.locator(".gt-prompt")).toHaveText(frontQuestion);
      const backChoices = (await page.locator(".gt-reason-choices button").allInnerTexts())
        .map((text) => text.split("\n")[0]);
      expect(backChoices).toEqual(frontChoices);
      await expect(page.locator(".gt-answer-correct")).toContainText("You ✓");
      await expect(page.locator(".gt-bar.gt-ok")).toHaveText("Your choice matches");
      await expect(page.locator(".gt-reason-source")).toHaveAttribute("href", /^https:\/\//);
    });
  }

  test("wrong answer is labelled, not merely colored", async ({ page }) => {
    const prefix = `card-${SCOPE}-reason-03-coastal-upwelling`;
    await page.setContent(readFileSync(FIX(`${prefix}-front.html`), "utf-8"));
    await page.locator(".gt-reason-choices button", { hasText: "Surface water sinks near shore" }).click();
    await page.setContent(readFileSync(FIX(`${prefix}-back.html`), "utf-8"));
    await expect(page.locator(".gt-answer-wrong")).toContainText("You ✕");
    await expect(page.locator(".gt-answer-correct")).toContainText("✓ Correct");
    await expect(page.locator(".gt-bar.gt-miss")).toHaveText("Your choice differs");
  });

  test("QA reveal without a choice does not pretend a review was graded", async ({ page }) => {
    const prefix = `card-${SCOPE}-reason-06-weak-trades`;
    await page.setContent(readFileSync(FIX(`${prefix}-back.html`), "utf-8"));
    await expect(page.locator(".gt-bar.gt-hint").first())
      .toHaveText("No choice recorded; inspect the answer");
    await expect(page.locator(".gt-suggest")).toHaveCount(0);
  });

  test("choice grid fits a narrow phone viewport", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    const prefix = `card-${SCOPE}-reason-06-weak-trades`;
    await page.setContent(readFileSync(FIX(`${prefix}-front.html`), "utf-8"));
    await expect(page.locator(".gt-reason-choices button")).toHaveCount(3);
    const overflow = await page.evaluate(() =>
      document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });
});
