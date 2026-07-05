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
- **M3 — Draw-the-shape (F6).** Sketch canvas, shape normalization, IoU + landmark
  scoring, overlay feedback. Its own milestone because scoring quality decides whether
  the family is fun or frustrating.
- **M4 — Breadth + physical geography.** Remaining subdivision scopes (reuse
  country-subdivision-map-decks coverage), F8 features, capitals-on-map.
- **M5 — Release.** AnkiWeb-shaped packaging per workspace conventions (`release/ankiweb.md`,
  `anki-addon-release`), public repo decision, screenshots via workbench.

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
