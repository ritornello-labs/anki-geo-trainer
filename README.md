# anki-geo-trainer

Sheppard-Software-style interactive geography practice for Anki: a comprehensive,
curriculum-ordered set of map-interaction task types rendered by a shared JS engine
that works on Anki Desktop, AnkiMobile, and AnkiDroid.

Status: redesigned to a lean, **borderless-recall** set after real-world study.
**Twenty-two scopes**, ~1,700 cards. Region scopes carry three families — **Which**,
**Place**, **Draw** — on a *borderless* map (no internal borders, so you recall
where things are instead of matching a labelled shape). Continents (countries):
**Europe** (46), **South America** (12), **Africa** (53), **Asia** (47),
**North America** (23), **Oceania** (14). Country subdivisions: **United States**
(50), **Brazil** (27), **India** (36), **Russia** (85), **China** (31), **Canada**
(13), **Australia** (9), **Argentina** (24), **Mexico** (32), **Indonesia** (33).
Physical: **mountain ranges** (29) and **deserts** (17) — **Place** only, dragged
onto the continents — and **major rivers** (42) as trace-the-course. Plus a
**Continents** scope — **Draw** the whole silhouette of South America, North America,
or Africa from memory. All rendered by one shared engine and verified on
Desktop/WebKit/AnkiDroid. See [`PLAN.md`](./PLAN.md), the skill ladder in
[`curriculum/CURRICULUM.md`](./curriculum/CURRICULUM.md), and the publishing plan in
[`release/RELEASE.md`](./release/RELEASE.md).

New scopes are pure config: a continent is a viewport box + a Natural Earth
`CONTINENT` filter; a country subdivision is an ISO country code. Both feed the
same builder, so adding a scope is a few lines in `scripts/build_bundle.py`.

## Task families

| Deck | Skill | Interaction |
|------|-------|-------------|
| `…::1 Which State/Country` | position → name | A dot appears *inside* a region (different spot each review) on a **borderless** map; recall which one it is |
| `…::2 Place` | precise position | Drag the region's silhouette onto the **borderless** map to where it belongs — no labelled slot to snap into |
| `…::3 Draw` | shape recall | Sketch the outline from memory on a blank **fixed-square** canvas (uniform for every card, so the frame never hints the answer's aspect ratio; multi-stroke, undo/clear); the back overlays the true shape and grades the match. Scoring gates on **both** boundary faithfulness and area overlap (IoU), so a right-size wrong-shape blob — a lazy circle over Algeria — fails to *Again*, while an honest freehand attempt (even wobbly) passes. Position and size don't matter, form does |
| `…::1 Trace` (rivers) | river course | Trace a major river's course over a world map; the back overlays the true line and grades by distance (km) to it. Start on the *full* world map (no positional hint), then zoom in to trace precisely |

Drawing surfaces (Draw, Trace) have **zoom + pan** via floating map-style controls
in the canvas corner (Google-Maps-like): a stacked **＋/−** zoom pill and a **✋**
toggle that turns a drag into a pan (so you can reposition a zoomed-in view onto, say,
South America to trace the Amazon). Mouse-wheel also zooms; on touch you can pinch-zoom
and two-finger pan; on desktop a right-drag pans without the toggle. Only the SVG
viewBox changes, so strokes stay in map coordinates and grading is exact at any zoom.

Cards are self-graded: the card shows a verdict and a suggested grade; you still
press Anki's answer buttons. Region maps hide internal borders on the front so the
task is genuine spatial recall, not shape-matching. Alaska and Hawaii render in
classic inset panels at their own scale; microstates are magnified tap-circles on
the *back*; Physical scopes (ranges/deserts) hide the feature on the front and show
only the continents — you drag the feature's silhouette to where it belongs.

**Design note (2026-07):** Locate (redundant), Capital (duplicated a Cities deck),
and Seas (trivial at world scale) were cut after studying the deck for real; the
survivors were made non-trivial by hiding the borders. Quality of each card type
over breadth.

## Why

Anki's geography ecosystem covers *passive* recall well: highlighted region → name,
silhouette → name. Sites like [Sheppard Software](https://www.sheppardsoftware.com/)
show that the higher rungs are *active*: find it on a blank map, judge a random
point, place the piece, draw the outline. This project builds that ladder as Anki
decks — beautiful, cross-platform, and tagged so students can assemble curricula
(see the curriculum doc for ready-made filtered-deck searches).

## Build & test

```
make bundle           # Natural Earth -> pre-projected scope bundle (data/bundles/)
make apkg             # bundle + engine -> dist/geo-trainer-us-states.apkg (+ test fixtures)
make test             # Playwright card tests on Chromium (~Desktop) and WebKit (~AnkiMobile)
make workbench-smoke  # imports the APKG into disposable real Anki (Docker/Xvfb)
```

Python via `uv` (deps: shapely, genanki); JS test deps via `npm` (Playwright only —
nothing ships to cards from npm). The AnkiDroid lane (emulator + adb + CDP) is driven
by `scripts/droid_ui.py` / `scripts/droid_cdp.py`.

## Engineering notes

- **Everything is inlined in the note templates** — the engine as brace-guarded JS,
  the geometry as a base64 JSON bundle. No media files, no script load-order
  assumptions, no network. This is what makes AnkiDroid and AnkiMobile reliable.
- Geometry is pre-projected in Python (equirectangular, mean-latitude standard
  parallel, sub-pixel simplification) so the card engine only scales a viewBox.
- Front→back interaction handoff goes through localStorage, with a deterministic
  day-seeded fallback for the random-dot family.
- Drags use pointer events *plus* a non-passive touch fallback because AnkiDroid's
  WebView fires `pointercancel` mid-gesture.
