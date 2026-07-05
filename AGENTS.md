# AGENTS.md

## Scope

These instructions apply to the `anki-geo-trainer` repository.

## What this project is

Interactive, Sheppard-Software-style geography task decks for Anki, driven by a shared
JS engine inlined into note templates. `PLAN.md` is the plan of record; keep it current
when scope, task families, or milestones change.

## Hard constraints (do not relearn these)

- All card JS must be inlined into note templates (AnkiDroid media serving is unreliable
  for small fresh files). Guard inlined bundles against `</script>` and `{{` sequences.
- No script load-order assumptions; poll for dependencies and self-trigger per card side
  (AnkiMobile loads scripts async and out of order).
- Maps are rendered with our own plate-carrée projection over Natural Earth polygons.
  Never embed a base image with an unknown projection and do linear math on it.
- Cards are self-graded: the engine shows a verdict and suggested grade; it never
  auto-answers. Platform JS answer APIs may become an opt-in extra, never a dependency.
- Dynamic cards (random point in region) must be stable within a single review
  (front and back agree) and vary across reviews.
- Drag interactions need non-passive touch handlers that preventDefault on the dragged
  element, and `pointercancel` must NOT end the drag: AnkiDroid's WebView intercepts
  gestures mid-drag and cancels the pointer stream while touches keep flowing. Verify
  drags with real input (`adb shell input swipe`), never only synthetic events.
- Verify rendered output, not just JS state. Test lanes: Playwright Chromium + WebKit
  with Anki-style script injection, `anki-addon-workbench` Docker/Xvfb deck smoke, and
  the AnkiDroid emulator/CDP lane. Do not open a visible Anki GUI on the host.
- Night mode CSS from day one; lean fronts with a card-family chip.

## Workspace conventions that apply here

- Python tooling via `uv`; JS deps installed with `sfw` prefix; 7-day minimum release
  age configured for both toolchains when dependencies are first added.
- Sign commits with GPG (`git commit -S`); commit and push regularly.
- AnkiWeb listing copy, when it exists, lives in `release/ankiweb.md`.
