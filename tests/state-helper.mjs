// Read engine state the way the engine itself does: localStorage when the
// origin allows it, else the window-global fallback. setContent() pages have
// an opaque origin in current Chromium/WebKit, which DENIES localStorage —
// the engine survives that (cards still work); tests must read through the
// same fallback rather than assuming storage.
export function readState(page, mode, scope, target) {
  return page.evaluate(
    ({ mode, scope, target }) => {
      try {
        const raw = localStorage.getItem("geotrainer:" + mode + ":" + scope + ":" + target);
        if (raw) return JSON.parse(raw);
      } catch (e) {
        /* opaque origin: fall through */
      }
      return window["__gt_" + mode + "_" + scope + "_" + target] || null;
    },
    { mode, scope, target }
  );
}

export function clearState(page) {
  return page.evaluate(() => {
    try {
      localStorage.clear();
    } catch (e) {
      /* opaque origin */
    }
    for (const k of Object.keys(window)) {
      if (k.startsWith("__gt_")) delete window[k];
    }
  });
}
