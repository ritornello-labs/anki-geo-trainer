import { defineConfig, devices } from "@playwright/test";

// Cross-engine card tests. Chromium ~= Anki Desktop (QtWebEngine); WebKit ~=
// AnkiMobile (iOS). AnkiDroid's Android WebView is Chromium-family and is
// covered separately by the emulator/CDP lane, not here.
export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  reporter: [["list"]],
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "webkit", use: { ...devices["Desktop Safari"] } },
  ],
});
