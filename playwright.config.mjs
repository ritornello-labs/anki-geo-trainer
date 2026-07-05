import { defineConfig, devices } from "@playwright/test";

// Cross-engine card tests. Chromium ~= Anki Desktop (QtWebEngine); WebKit ~=
// AnkiMobile (iOS). AnkiDroid's Android WebView is Chromium-family and is
// covered separately by the emulator/CDP lane, not here.
export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  reporter: [["list"]],
  // Tall viewport: the full map must be inside the window — mouse clicks on
  // southern regions (Vatican, Spain, the F5 tray) land at viewport coords,
  // and the default 720px window clips the map's lower third.
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 1700 } } },
    { name: "webkit", use: { ...devices["Desktop Safari"], viewport: { width: 1280, height: 1700 } } },
  ],
});
