# anki-geo-trainer — Plan

Status: planning. Created 2026-07-05.

## Vision

Bring Sheppard-Software-class interactive geography practice into Anki: a comprehensive,
curriculum-ordered catalog of map-interaction task types, rendered by one shared JS engine,
working on all three platforms (Anki Desktop / QtWebEngine, AnkiMobile / WebKit,
AnkiDroid / Android WebView), and looking genuinely good.

The user's collection already covers the *passive* recall levels well (Ultimate Geography,
Country Shapes, borders, capitals, first-level subdivisions for ~15 countries, cities,
physical geography). What is missing is the *active* interaction ladder that makes Sheppard
Software effective: click the map, judge a random point, place the piece, draw the shape.
This project builds that ladder.

## Task catalog

Each task family is defined once (schema + engine mode + grading rule), then instantiated
scope by scope (world, continent, country, subdivision set). Families are ordered roughly
by difficulty; together they form the level ladder for any given scope.

| # | Family | Interaction | Sheppard analogue | Notes |
|---|--------|-------------|-------------------|-------|
| F1 | Recognize | highlighted region on locator map → recall name | tutorial levels | **Not built here.** Passive recall; the README links a few good example AnkiWeb decks (Ultimate Geography, the workspace's shared subdivision decks) instead |
| F2 | Shape ID | isolated silhouette → recall name | shape quizzes | **Not built here.** The user already has shape→name recognition (Country Shapes); the README links examples. The *inverse* (draw the shape) is F6, not this |
| F3 | Locate | name shown → tap/click the region on a blank map | click-on-map games | Engine highlights what you hit, then reveals the answer region; self-grade with distance feedback. Scope = continental blank maps **and** country-internal blank maps for the user's target countries (USA, Russia, India, Brazil, Argentina, …) |
| F4 | Point-in-region | random dot on a blank map → name the region containing it | "which state is this point in" | Dynamic: point re-randomized per review, stable within one review (front and back must agree). One note per region; the dot varies across reviews but stays inside an **eroded (inset) polygon** so it never hugs a border. Same scope catalog as F3 (US states, Brazilian states, countries of South America, Indian states, …) |
| F5 | Place-the-piece | drag a floating **silhouette (shape supplied)** to its correct position on a faded/blank map | place-the-state (hard levels) | Tests *location* with the shape given. Score by centroid offset + rotation-free overlap. Distinct from F6 |
| F6 | Draw-the-shape | **name only** → sketch the outline of the region on a canvas; engine scores vs. truth | draw-the-state | Tests *shape recall*. This is the "draw the shape of country/state/continent X" task. Hardest to build well: normalization + IoU-style scoring + visual overlay feedback |
| F7 | Neighbors | given a region (highlighted or named) → tap **all** its bordering regions on the map | border quizzes | Interactive tap-all version of the user's passive Country Borders deck. Engine tracks correct/missed/wrong neighbors and shows the full adjacency on the back |
| F8 | Feature overlay | tap the named **non-region feature** (river, mountain range, sea, capital) on the map | rivers/landscapes games | Later phase; reuses F3/F4 machinery but the targets are lines (rivers/ranges) and points (capitals) laid over the basemap, not the fill regions |

Cross-cutting variants (per family, where meaningful): political vs. physical basemap,
labeled vs. unlabeled neighbors. (Timed modes are dropped — they fight Anki's review model.)

## Anki-specific design constraints

These are the hard-won rules from this workspace (especially `sight-singing-deck`):

- **All JS inlined into the note templates.** AnkiDroid's media server intermittently 404s
  small freshly-imported files; inline the engine, keep only large stable-named assets
  (if any) as media. Target: engine bundle small enough to inline comfortably.
- **No script load-order dependence.** Poll for deps; self-trigger per card side. AnkiMobile
  loads scripts async and out of order.
- **Geometry data per scope packed as inlined JSON** (simplified TopoJSON-style), budgeted
  per deck (~100–200 KB per scope target; measure). One shared blank-world/blank-country
  base per scope, not per card.
- **Own plate-carrée projection over Natural Earth polygons** (workspace memory: never
  embed a mystery-projection base image and do linear math on it).
- **Self-grading, not auto-answering.** Anki grading stays manual. The engine renders a
  verdict (hit/miss, distance in km, overlap %) and a suggested grade; the user grades.
  AnkiDroid/AnkiMobile JS answer APIs are a possible later opt-in, never a dependency.
- **Front→back state handoff.** Interaction happens on the front (or is at least previewed
  there); the back must show the user's attempt vs. truth. Persist attempt state across
  card sides (serialized state; platform-tested — sessionStorage is not reliable everywhere).
- **Stable randomness for F4.** The random point must be identical on front and back of one
  review and different across reviews. Reuse/absorb the `anki-dynamic-cards` prototype's
  approach; this project is its first serious consumer. The candidate point is sampled from
  an **eroded (negatively-buffered) copy of the region polygon** so it always sits comfortably
  inside with border margin — never so close to an edge that it's ambiguous. Erosion distance
  is a fraction of the region's own size (small states erode less than large ones) with a
  fallback for slivers too thin to erode.
- **Lean fronts, task type visible at a glance** (card-family chip), night-mode CSS from
  day one, verify rendered output not just state.
- **Test lanes:** browser harness (Chromium + WebKit Playwright, Anki-style script
  injection) for fast iteration; `anki-addon-workbench` Docker/Xvfb deck smoke; AnkiDroid
  emulator/CDP lane for suspicion; no visible host Anki GUI.

## Architecture

```
data/            Natural Earth sources (compressed), entity registries (CSV/JSON)
scripts/         Python (uv) build pipeline: simplify geometry, pack scope bundles,
                 generate notes, build APKGs (reuse _geo_base plate-carrée pattern
                 from world-geography-concepts)
engine/          TypeScript source for the interaction engine; bundled + minified,
                 then inlined into templates at build time (guard `{{`/`</script>`
                 like sight-singing-deck does)
anki/            Note type definitions: templates (front/back per family), shared CSS
                 (design tokens + night mode)
curriculum/      CURRICULUM.md + machine-readable ordering/tags manifest
tests/           Playwright (Chromium + WebKit) card tests, workbench smoke configs
```

One note type per task family (fields: entity id, name, scope id, difficulty metadata,
Wikipedia/extra); one scope bundle per deck inlined once per template — measure whether
per-note or per-template data embedding wins on APKG size and render speed (spike in M0).

## Curriculum & tagging

Tags are the curriculum's backbone, hierarchical:

- `geotrainer::skill::locate | point | place | draw | neighbors | …`
- `geotrainer::scope::world`, `geotrainer::scope::continent::europe`,
  `geotrainer::scope::country::usa::states`, …
- `geotrainer::level::1..6` (position on the ladder within a scope)
- `geotrainer::track::<named track>` for suggested course-like sequences

`CURRICULUM.md` defines the recommended progression: for each scope, unlock order
F3→F4→F5→F6 (with F7 folded in where borders matter), preceded by F1/F2 which the student
gets from existing public decks — the trainer decks themselves start at F3. Deck structure
mirrors scope (`GeoTrainer::World::Europe::Locate`, etc.) so students can subscribe to
exactly the slice they want; tags let power users rebuild any custom ordering.

**Curricula ship as documented saved searches, not filtered decks.** Anki excludes
filtered/dynamic decks from `.apkg` exports (they are emptied on export), so we cannot
bundle suggested course sequences as ready-made filtered decks. Instead the README/`CURRICULUM.md`
lists copy-paste search strings (e.g. `deck:GeoTrainer::* tag:geotrainer::level::1`,
`tag:geotrainer::track::south-america-mastery`) that a student pastes into their own
filtered deck. This is more flexible than shipped filtered decks and survives re-import.

## Milestones

- **M0 — Engine spike (prove the risky part first). ✅ Done 2026-07-05 (`91f490c`).**
  One F3 Locate card for the lower-48 US states, end-to-end: pre-projected data bundle
  (`scripts/build_bundle.py`, 34 KB), plain-JS engine (`engine/geo-engine.js`) with tap
  hit-testing against real polygons, front→back attempt handoff via localStorage,
  self-graded verdict, night mode, and no script-load-order/media dependence. Verified in
  browser preview, on Chromium + WebKit Playwright (incl. a fixture test of the shipped
  inlined form), and by the `anki-addon-workbench` Docker/Xvfb deck smoke (`ok: true`).
  F4 stable-randomness spike (`scripts/f4_spike.py`) passed: eroded-polygon sampling with
  border margin + portable mulberry32/day-stamp seeding. **Not yet done, carried to M1:**
  AK/HI insets, the AnkiDroid emulator/CDP lane run, and F4 wired as a live engine mode.
- **M1 — US states pack. ✅ Done 2026-07-05.** F3 + F4 + F5 for all 50 states (AK/HI as
  classic inset panels with own projections and per-frame kmPerUnit; cross-frame
  distances suppressed). F4 ships 16 precomputed eroded-interior sample points per
  state, chosen by a deterministic day seed with localStorage smoothing. F5 drags with
  pointer events plus a non-passive touch fallback — AnkiDroid's WebView fires
  `pointercancel` mid-drag (found via real `input swipe` on the emulator; synthetic
  events hide it). Verified: Chromium + WebKit Playwright suites, Docker/Xvfb real-Anki
  deck smoke, and a full AnkiDroid emulator lane (UI-scripted APKG import, real-touch
  tap/drag on all three families over CDP). Curriculum tags + `curriculum/CURRICULUM.md`
  with filtered-deck recipes. Dogfooded: imported into the live collection via
  AnkiConnect (150 notes, 3 subdecks).
- **M2 — World countries (Europe) + F7. ✅ Done 2026-07-05.** Multi-scope pipeline
  (scope registry in `build_bundle.py` / `SCOPE_PACKS` in `build_apkg.py`). Europe:
  46 sovereigns incl. Cyprus/Kosovo, viewport Iceland→Urals with Russia clipped at the
  frame, tier-2 dependencies as muted tappable context without notes, microstates as
  magnified tap-circles, neutral context land (110m) for orientation. F7
  tap-all-neighbors shipped for BOTH scopes from shapely land-border adjacency
  (point-touches excluded — Four Corners verified; islands get no F7 notes). Engine:
  scope nouns, context/tier-2/small rendering, tray override, neighbors mode with live
  found/wrong feedback. Verified per platform matrix; both packs imported into the
  live collection (confirmed that APKG re-import updates existing note-type templates,
  so engine upgrades propagate). Continents beyond Europe moved to M4.
- **M3 — Draw-the-shape (F6). ✅ Done 2026-07-05.** F7 retired first (user call:
  duplicates his existing borders decks; engine mode kept dormant, ord 3 ids never
  reused). Draw ships as `4 Draw` for both scopes (50 + 46 notes). Per-note base64
  `ShapeData` field carries a hi-res outline refitted to its own box (greedy
  edge-distance chain keeps Sicily/NI/Hawaii's islands, drops French Guiana and
  Svalbard — NE admin-0 bundles overseas territory into one geometry). Front:
  multi-stroke SVG sketch canvas (pointer + non-passive touch, pointercancel-immune,
  undo/clear, `touch-action: none`). Back: true outline overlaid with the drawing
  aligned translation/scale-invariantly (uniform bbox fit + centroid), scored by
  symmetric chamfer distance as % of shape diagonal — calibrated on France: trace
  1%, wobbly trace 2.2–2.5% (Good <3.5), ellipse 5.3 (Hard <6.5), square/scribble
  7.5–8.3 (Again). Verified: 68/68 Chromium+WebKit (incl. shipped-fixture boots and
  scoring-invariance tests), Docker smoke, live import, AnkiDroid physical-swipe
  strokes (3-stroke Albania → "Grade: Hard", state front→back on device).
- **M4 — Breadth. ✅ First batch done 2026-07-05.** The two hand-written builders
  became config-driven factories: `_build_continent(cfg)` (viewport box + NE
  `CONTINENT` filter, driving `CONTINENT_SCOPES`) and `_build_admin1_country(cfg)`
  (ISO-3 code → single frame, driving `SUBDIVISION_SCOPES`); us-states stays bespoke
  for its AK/HI insets. Added five scopes — South America (12), Africa (53), Asia
  (47; Turkey→Japan, Russia clipped, junk NE entities like "Siachen Glacier" and
  "Indian Ocean Territories" excluded), Brazil (27 states), India (36). All four
  families each → **2,420 notes across 7 scopes**. A `buffer(0)` repair in
  `project_geom` recovered self-intersecting NE polygons that were being silently
  dropped (Goiás wraps around Brazil's Federal District enclave → invalid ring).
  Data-driven `scopes.spec.mjs` smokes every scope (load, render, hit-test, F4
  front↔back, shape coverage) — 112/112 cross-engine. Docker smoke + live import of
  all 7 packs green.
- **M4b — 6 more subdivisions + F8. ✅ Done 2026-07-06 (commit `ec8b216`).** Added
  Russia (85 subjects, antimeridian-unwrapped), China (31), Canada (13), Australia
  (9) from 50m admin-1; Argentina (24) and Mexico (32) from a new 10m admin-1 source
  (subdivision builder gained `source` + `unwrap_antimeridian`; skips NE nameless
  junk rows). **F8 capital-locate family** (ord 5, `5 Capital`): tap where the named
  capital is, distance-graded like a locate miss; the back stars the true point and
  names the region. Capitals matched by point-in-region and projected into scope
  coords (us-states routes each through its inset frame); national capitals for
  continents, state/province capitals for subdivisions, from the 10m populated-places
  file (2,259 province capitals vs 482 in 50m → US 48/50, Mexico 31/32). **13 scopes
  × 5 families = 2,286 notes.** Suite 174/174 (scopes.spec now covers all 13 scopes +
  the capital family; locate/capital taps dispatch in SVG space so Argentina's
  2148px-tall map doesn't clip the synthetic click). Docker smoke + live import of
  all 13 packs; AnkiDroid verified the US capital family end to end (physical tap on
  Montgomery → "Spot on — Montgomery (Alabama)", star + region highlight).
- **M4c — Indonesia, Oceania, physical features. ✅ Done 2026-07-06.** Indonesia (33
  provinces, 50m). Oceania continent (14 sovereigns) — the continent builder gained
  `unwrap_antimeridian` (Pacific-centred, box in 0..360 lon; context land skipped
  because unwrapping whole-world land mangles the dateline seam). Physical features:
  **world seas & oceans** (97 named marine polygons, reuses the region machinery with
  a `families` = locate/point/draw restriction) and **world rivers** (84 majors,
  scalerank ≤ 3, multi-segment merged by name) via a brand-new **F9 river-locate
  engine mode** — rivers are lines, so the base bundle carries only world-land context
  and each river's polyline rides per-note; "tap where the river runs" grades by
  distance to the nearest point on the line. Added a `families` scope-config key
  (default = the 5 standard families; river is opt-in) and a `kind` bundle marker so
  `scopes.spec.mjs` routes polygon vs river scopes. **18 scopes.** Suite 198 passed /
  2 skipped (seas have no capitals) across Chromium + WebKit; Docker smoke green with
  all 18 packs; all import-verified (rivers preview: the Amazon highlighted, "~313 km
  off" graded Hard). **M5 release prepared but NOT published** — see
  `release/RELEASE.md` + `release/ankiweb.md`; publishing needs Elvis's go-ahead,
  public-repo flip, and the AnkiWeb quota.
  **Remaining:** mountain ranges (10m regions), lakes, more 10m subdivisions; then M5.
- **Redesign — borderless recall. ✅ Done 2026-07-07.** Elvis studied the deck for
  real and cut most of it as trivial or redundant. **Dropped:** Locate (tapping a
  labelled shape isn't recall), Capital (duplicated his Cities deck), Seas (trivial
  at world scale). **Kept & fixed:** Which + Place + Draw — but the fronts now hide
  all internal borders (`buildSvg({borderless})` → seamless silhouette), turning them
  from shape-matching into genuine spatial recall; Draw's score moved from mean-
  chamfer (rewarded a rough enclosing blob) to an 85th-percentile coverage metric
  (calibrated on China: faithful trace ~0.3% → Good, honest wobble → Good, a smooth
  blob that misses the bulges → 11% → Again). **Rivers → Trace-the-course** (a new
  draw-style mode; graded in km via a shared stroke-capture helper). **New physical
  scopes:** mountain ranges (29) + deserts (17) as areal polygons — initially
  point/place/draw, later pared to Place-only (see the next entry) — with the feature
  hidden and only the continents shown for reference (`kind:physical`).
  Families renumbered (1 Which / 2 Place / 3 Draw). Fixed: US now under
  `World::North America`. Static analysis (`ruff`) + a Node-version guard on `make
  test` added. **20 scopes, ~1,716 cards**; suite 204 passed / 4 skipped; the whole
  live GeoTrainer tree was deleted and re-imported clean. Lesson: verify each card
  type earns its place before mass-producing — quality over breadth.
- **Study-feedback pass 2 — sort key, honest Draw, pan, lean physical. ✅ Done
  2026-07-07.** Elvis studied the borderless redesign and reported four issues,
  all fixed: **(1) Unique sort field** — the first field was the constant "Scope",
  breaking Anki's duplicate detection and browser sort; every note type now leads
  with a natural `Key` (`scope:region_id`, `sort_field_index=0`). **(2) Draw still
  too lenient** — an irregular circle over Algeria still scored a decent grade;
  added a rasterised **area-IoU** gate (multi-ring aware, so archipelagos traced as
  separate strokes stay registered). Calibrated on real African shapes: honest
  freehand (even ~5% jitter) lands at IoU 0.87–0.99, a lazy circle tops out at
  ~0.75; the Hard gate at 0.78 drops every lazy circle to *Again* while honest
  attempts stay *Good*. **(3) Zoom couldn't reposition** — added a **✋ Move** toggle
  that turns a one-finger / left-button drag into a pan (plus existing pinch /
  two-finger / right-drag), so a zoomed-in view can be moved onto South America to
  trace the Amazon. **(4) Ranges/deserts → Place only** (`families:["place"]`),
  dropping the Which/Draw decks Elvis didn't want there. Suite 210 passed / 4
  skipped; bundles + per-scope + combined APKGs + fixtures rebuilt.
- **M5 — Release.** AnkiWeb-shaped packaging per workspace conventions (`release/ankiweb.md`,
  `anki-addon-release`), public repo decision, single-deck `geo-trainer-all.apkg`
  (`make apkg-all`) + `release/screenshots/`. Publishing still gated on Elvis's
  go-ahead + public-repo flip + the AnkiWeb quota.

## Relationship to existing projects

- `world-geography-concepts` — source of the `_geo_base.py` plate-carrée renderer and
  Natural Earth handling; we generalize, not fork-and-drift (extract if practical).
- `country-subdivision-map-decks` / `us-states` / `chinese-regions` / `us-regions` —
  define the scope catalog and provide F1/F2 coverage; the README links these (and
  Ultimate Geography) as the recommended passive-recall on-ramp rather than duplicating them.
- `anki-dynamic-cards` — its stable-randomness prototype becomes F4's foundation.
- `sight-singing-deck` — the cross-platform JS playbook (inline everything, dep polling,
  WebKit + AnkiDroid lanes) is adopted wholesale.
- `anki-addon-workbench` — all smoke/GUI verification.

## Decisions (settled 2026-07-05)

1. **Naming:** `anki-geo-trainer` / `GeoTrainer::…` confirmed.
2. **F1/F2:** not built. The README links a few good example AnkiWeb decks for passive
   recognition; the trainer starts at F3.
3. **Release:** AnkiWeb-shaped from day one, shared as soon as it's decent. (Designing for
   AnkiWeb vs. not makes little practical difference to the build; the constraints above
   already assume shareable, self-contained decks.)
4. **Languages:** English-only to start.
5. **Timed modes:** dropped — they fight Anki's review model.
6. **Curricula delivery:** documented saved searches + tags, not filtered decks (APKG can't
   carry filtered decks).
7. **F4 point placement:** sampled from an eroded polygon with border margin.

## Open questions (remaining)

- Geometry-embedding strategy (per-note vs. per-template scope bundle) — resolve empirically
  in the M0 spike by measuring APKG size and render speed both ways.
