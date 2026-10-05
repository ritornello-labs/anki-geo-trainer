# anki-geo-trainer — Plan

Status: all fifteen public components submitted and exact delivered APKGs archived.
The full-edition update for `908455862` remains held: ordinary July imports fail,
but the GUID-aware disposable migration prototype now passes, including existing
World Countries installs and all fifteen delivered components. Older users need a
one-time model-ID transition; Elvis's decision and user-facing upgrade remain
pending. Elvis approved the ten-GIF full image batch on October 5; the review contact sheet
is not public listing media. Legacy model-ID decision and supported upgrade remain pending.
See `release/FULL_LEGACY_IMPORT_2026-10-05.md`. Personal collection changes are
outside this publication pass. Created 2026-07-05.

## Privacy boundary

Live Anki collection snapshots, rollback exports, and move-state captures are
private local recovery artifacts. The original GitHub repository was made private
on 2026-08-26 after such artifacts were found in Git history. The
`backups/live-imports/` and `backups/live-moves/` trees were then removed from every
reachable commit, and the sanitized signed history initially ended at
`ea1b973d00fb19c412c54c490f88f890935e4b92`.

On 2026-08-28, the original GitHub repository identity was permanently quarantined
as the private repository
`ritornello-labs/anki-geo-trainer-private-archive-2026-08-26`. A fresh private
repository was created at `elvis-sik/anki-geo-trainer`, received only the sanitized
`main` branch, passed a scan of every reachable object and the privacy workflow, and
was transferred without renaming to `ritornello-labs/anki-geo-trainer`. Only that
fresh repository was then made public; the legacy personal URL redirects to it.

Both live-backup paths remain ignored, and `make privacy-check` rejects tracked
live-collection artifacts. Never publish or reuse the quarantined repository
identity.

## Vision

Bring interactive geography practice into Anki: a comprehensive,
curriculum-ordered catalog of map-interaction task types, rendered by one shared JS engine,
working on all three platforms (Anki Desktop / QtWebEngine, AnkiMobile / WebKit,
AnkiDroid / Android WebView), and looking genuinely good.

The user's collection already covers the *passive* recall levels well (Ultimate Geography,
Country Shapes, borders, capitals, first-level subdivisions for ~15 countries, cities,
physical geography). This project adds an *active* interaction ladder: click the map,
judge a random point, place the piece, draw the shape.
This project builds that ladder.

## Task catalog

Each task family is defined once (schema + engine mode + grading rule), then instantiated
scope by scope (world, continent, country, subdivision set). Families are ordered roughly
by difficulty; together they form the level ladder for any given scope.

| # | Family | Interaction | Notes |
|---|--------|-------------|-------|
| F1 | Recognize | highlighted region on locator map → recall name | **Not built here.** Passive recall; the README links a few good example AnkiWeb decks (Ultimate Geography, the workspace's shared subdivision decks) instead |
| F2 | Shape ID | isolated silhouette → recall name | **Not built here.** The user already has shape→name recognition (Country Shapes); the README links examples. The *inverse* (draw the shape) is F6, not this |
| F3 | Locate | name shown → tap/click the region on a blank map | Engine highlights what you hit, then reveals the answer region; self-grade with distance feedback. Scope = continental blank maps **and** country-internal blank maps for the user's target countries (USA, Russia, India, Brazil, Argentina, …) |
| F4 | Point-in-region | random dot on a blank map → name the region containing it | Dynamic: point re-randomized per review, stable within one review (front and back must agree). One note per region; the dot varies across reviews but stays inside an **eroded (inset) polygon** so it never hugs a border. Same scope catalog as F3 (US states, Brazilian states, countries of South America, Indian states, …) |
| F5 | Place-the-piece | drag a floating **silhouette (shape supplied)** to its correct position on a faded/blank map | Tests *location* with the shape given. Score by centroid offset + rotation-free overlap. Distinct from F6 |
| F5.5 | Contextual Sketch | **name + borderless parent map** → sketch the region in geographic position | Bridges Place and Draw: the parent outline helps orientation, but there are no internal borders to trace. Direct map-coordinate scoring tests shape, position, and scale |
| F6 | Draw-the-shape | **name only** → sketch the outline of the region on a canvas; engine scores vs. truth | Tests *shape recall*. This is the "draw the shape of country/state/continent X" task. Hardest to build well: normalization + IoU-style scoring + visual overlay feedback |
| F7 | Neighbors | given a region (highlighted or named) → tap **all** its bordering regions on the map | Interactive tap-all version of the user's passive Country Borders deck. Engine tracks correct/missed/wrong neighbors and shows the full adjacency on the back |
| F8 | Feature overlay | tap the named **non-region feature** (river, mountain range, sea, capital) on the map | Later phase; reuses F3/F4 machinery but the targets are lines (rivers/ranges) and points (capitals) laid over the basemap, not the fill regions |

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
- **Continents + North America scopes. ✅ Done 2026-07-07.** Elvis's Draw priorities
  exposed two coverage gaps: no continent-outline cards, and North America had no
  country scope at all (only US/Canada/Mexico *subdivisions*), so "Draw USA" as a
  country didn't exist. Added: **(1) `continents`** — a Draw-only scope whose regions
  are whole continents (all member countries dissolved via `unary_union` on the NE
  `CONTINENT` field). Ships all six inhabited continents (Elvis: "why not have all?").
  Eurasia is split wrong by country membership (NE files Russia under Europe), so
  **Europe** is clipped at the Urals (`box`) to cut Siberia and **Asia** dissolves
  without Russia (no Siberia, but a clean Turkey-to-Japan mass); the others dissolve
  cleanly. Antarctica is omitted (a plate-carrée smear nobody sketches). **(2)
  `north-america-countries`** — a standard continent
  scope (Which/Place/Draw) filling the missing continent: 23 tier-1 countries
  (USA/Canada/Mexico + Central America + Caribbean microstate circles), nested under
  `GeoTrainer::World::North America` beside the existing subdivision decks. New
  `shape_payload(mainland_only=…)` flag keeps just the main contiguous landmass for
  the continent silhouettes and the USA (drops Greenland off NA and the detached
  Alaska/Hawaii off the USA, so the graded shape is the lower-48 you actually picture;
  Central America stays because it's contiguous with the mainland polygon). **22 scopes;
  suite 224 passed / 6 skipped.** Combined `geo-trainer-all.apkg` = 52 decks / 1,699
  notes / 26.9 MB; both new scopes imported live. (Continents later expanded 3→6 to
  cover all inhabited continents at Elvis's request.)
- **Draw/Trace UI polish. ✅ Done 2026-07-07.** Three study-driven refinements:
  **(1) Uniform Draw canvas** — the front was sized to the shape's own box, so the
  canvas aspect leaked the answer; it's now a **fixed 400×400 square** for every card
  (`drawCanvas(shape, square)`; the back keeps the shape's real box for the overlay).
  Scoring is scale/translation-invariant so this costs nothing. **(2) Google-Maps-style
  controls** — the +/−/Move button row was replaced by floating controls in the canvas
  corner: a stacked ＋/− zoom pill and a round ✋ pan toggle, overlaid as siblings of
  the SVG (`drawSurface` wraps the canvas; the square Draw wrap hugs the canvas via
  `.gt-wrap-square` so the controls land on its corner, not the letterbox margin).
  Undo/Clear stay in a row below. Light + dark verified. **(3) Continents deck promoted**
  to top-level `GeoTrainer::Continents` (peer of World/Physical) for discoverability;
  live cards moved with AnkiConnect `changeDeck` + the old nested deck deleted. Suite
  224 passed / 6 skipped; templates re-imported live.
- **Contextual Sketch. ✅ Built 2026-07-20; installed in the live personal
  collection 2026-07-24; AnkiWeb rollout pending.**
  Added the missing bridge between Place and blank-canvas Draw: country on a
  borderless continent, subdivision on a borderless country, or continent on the
  blank world. The engine reuses freehand capture, zoom/pan, undo/clear, and the
  honest boundary+IoU grading, but scores directly in map coordinates so position
  and scale matter. Magnified microstates are omitted because their map circles are
  interaction affordances rather than real outlines. Deck order is now `1 Which / 2
  Place / 3 Sketch / 4 Draw`; existing Draw IDs remain stable, retired ord 3 remains
  untouched, and Sketch uses fresh ord 4. Combined build: 69 decks / 2,200 notes /
  38.1 MB; cross-engine suite 268 passed / 10 skipped; disposable desktop Anki QA
  imported 200 US cards and rendered all sampled cards successfully. The controlled
  live rollout preserved all 1,699 prior note/card IDs, fields, tags, and scheduling,
  added exactly 501 Sketch cards, nested them under
  `Decks::Geography::GeoTrainer`, and moved the 541 existing Draw cards from
  `3 Draw` to `4 Draw`. Timestamped before/after snapshots and a scheduled APKG
  rollback were captured locally under the timestamped `20260724T150455-0700-before`
  and `20260724T150959-0700-after` recovery directories; live snapshots are no
  longer stored in Git.
- **Physical-geography expansion. ✅ Built and browser-verified 2026-07-24;
  installed live 2026-07-28; AnkiWeb update queued.** Added contextual Sketch to the existing **29
  mountain ranges** and **17 deserts**. Added three curated scopes: **24 major
  lakes** (Which + Place; actual lake polygons, never magnified circles), **16
  major tectonic plates** (Which + Sketch; PB2002-derived polygons), and **12 major
  ocean currents** (new direction-aware Trace family). Current routes are ordered,
  schematic NOAA-derived learning corridors: the learner's stroke carries an
  arrowhead, the back reveals a wide accepted corridor plus the directed
  centreline, and a geometrically accurate reversed trace is forced to Again.
  Chokepoints and island/archipelago lists remain excluded by design because they
  do not fit GeoTrainer's interaction strengths. New scope/model/deck IDs use fresh
  deterministic bases `1607413xxx`–`1607415xxx`; no existing family IDs were
  reused. Combined target: **76 leaf decks / 2,338 notes**. Browser validation:
  **292 passed / 12 intentional skips** across Chromium + WebKit, including the
  exact inlined current template and forward/reverse grading. Disposable desktop
  Anki QA run `b4f905dfb463` passed: real Anki imported all 2,338 notes/cards,
  discovered the full new deck/note-type tree, and rendered all five sampled cards.
  The controlled live rollout added exactly 138 notes/cards in seven leaf decks,
  preserved all 2,200 prior note/card IDs, fields, tags, models, deck assignments,
  and scheduling, and left no temporary top-level `GeoTrainer` tree. Timestamped
  snapshots and the scheduled rollback package were captured locally under the
  timestamped `20260728T153543-0700-before` and `20260728T153543-0700-after`
  recovery directories; live snapshots are no longer stored in Git.
- **Plate Place + system-complete surface currents. ✅ Built, verified, and installed
  live 2026-07-31; AnkiWeb update remains queued.** Added a 16-card Place family
  for tectonic plates. Expanded ocean-current Trace from 12 to **34** cards: all
  four named limbs of each of the five major subtropical gyres plus important
  subpolar, equatorial, regional-throughflow, and Antarctic Circumpolar branches.
  Existing current IDs remain stable; five route/name payloads updated in place.
  Seasonal Somali/monsoon currents and deep thermohaline circulation remained
  deferred at this point because they required season- or depth-aware prompts. Combined build:
  **77 leaf decks / 2,376 notes / 44.9 MB**. Cross-engine tests exercise every
  current forward and reversed (**294 passed / 12 intentional skips**); disposable
  Anki 25.09 imported all 2,376 cards and rendered its samples. The live rollout
  added exactly 38 notes/cards,
  preserved all 2,338 original IDs and every original scheduling record, and
  left no temporary top-level deck. Snapshots and rollback were captured locally
  under the timestamped `20260731T153402-0700-before` and
  `20260731T153655-0700-after` recovery directories; live snapshots are no longer
  stored in Git. A 20-card, four-note-type
  atmospheric-circulation design was recorded in
  `curriculum/ATMOSPHERIC_CIRCULATION.md` for the next batch.
- **Atmospheric circulation + season-aware monsoon flow. ✅ Built, verified, and
  installed live 2026-07-31; AnkiWeb update remains queued.** Added a 20-card
  stable global core: six latitude–altitude circulation-cell loops, four
  pressure-belt placement cards, six prevailing-wind traces, and four broad
  jet-stream traces. Added six season-aware cards: South Asian monsoon winds for
  boreal summer/winter and summer/winter Somali plus Southwest/Northeast Monsoon
  Currents. Seasonal fronts show the named boreal season and explicit month
  range. Deep thermohaline circulation remains deferred pending a credible
  depth-aware exercise. The blocker is curriculum design and scientific
  representation, not line-tracing implementation: a flat global "conveyor belt"
  collapses surface and deep flows into a misleading route. Plausible future drills
  are a depth-sliced surface/deep trace or a latitude–depth AMOC cross-section.
  Combined build: **83 leaf decks / 2,402 notes / 51.2 MB**.
  Cross-engine validation: **318 passed / 12 intentional skips**, including exact
  inlined templates for every new note type and forward/reverse scoring for every
  directed route. Disposable Anki imported all 2,402 notes/cards. The guarded
  live rollout added exactly 26 notes/cards, preserved all 2,376 original IDs,
  note content, and scheduling, and left no temporary top-level deck. Snapshots
  and rollback were captured locally under the timestamped
  `20260731T163538-0700-before` and `20260731T163538-0700-after` recovery
  directories; live snapshots are no longer stored in Git.
  On 2026-08-05, the exact 26-card batch was moved without scheduling or content
  changes to `Process::GeoTrainer QA` for manual QA. Restore it with
  `scripts/stage_live_qa.py --restore` after review.
- **Atlantic overturning cross-section. ✅ Built, verified, and staged live
  2026-08-05; AnkiWeb update remains queued.** Added four prerequisite-ordered
  direction-aware traces: the northward upper-ocean limb, northern high-latitude
  sinking limb, southward deep-ocean return limb, and integrated Atlantic pathway.
  A latitude–depth cross-section replaces the misleading flat global conveyor map;
  the integrated route ends at the deep South Atlantic boundary rather than inventing
  a local upwelling limb. Combined build: **84 leaf decks / 2,406 notes / 53.3 MB**.
  Cross-engine validation: **334 passed / 12 intentional skips**. The four new cards
  were imported directly into `Process::GeoTrainer QA` with all 2,402 existing notes,
  card identities, deck assignments, and scheduling preserved.
- **Physical-systems QA redesign + ENSO. ✅ Built, cross-engine verified, and
  staged live 2026-08-06; manual QA remains.** Replaced six unreviewed
  hemisphere-specific cell cards with three paired-loop cards on a curved global
  cross-section; removed the pressure-belt count hint; changed prevailing-wind
  grading to broad latitude belts; moved monsoon winds to a world map; replaced
  four confusing AMOC traces with two direction/sequence cards; and added four
  neutral/El Niño/La Niña comparison cards. Cross-engine validation: **344 passed /
  12 intentional skips**. Combined build: **85 leaf decks / 2,405 notes / 60.0 MB**.
  The guarded live replacement deleted only the ten exact zero-review legacy notes,
  added nine redesigned notes, preserved scheduling on all 2,396 retained cards,
  found no filtered-deck collision, and performed no sync. Rollback packages and
  verification were captured locally under the timestamped
  `20260806T181704-0700-physical-redesign` recovery directory; live snapshots are
  no longer stored in Git.
- **Globe placement merge. ✅ Built and accepted 2026-09-22.** Graduated the one
  successful family from `anki-island-globe`: 67 island and archipelago cards on a
  randomly oriented orthographic globe, using editable extent ellipses and area-aware
  feedback. Stable note/card identities are preserved in
  `GeoTrainer::World::Islands::1 Globe Placement`. The eight untouched Antipodes cards
  and all other rejected globe experiments were retired. Combined build target:
  **86 leaf decks / 2,472 notes / 63.6 MB**. Full cross-engine validation:
  **362 passed / 26 intentional skips**.
- **Five scopes from world-geography-concepts. ✅ Built and browser-verified
  2026-09-23/24.** Peninsulas (15, Place + Sketch; Delmarva and Guajira are
  tap-circles, Place only), minor tectonic plates (35 PB2002 plates, Place +
  Sketch, three microplates Place only; nested under Tectonic Plates) and named
  plate boundaries (17, Trace via the river mode: a boundary is a line, so
  there is nothing to drag) followed the first two below. IDs
  `1607426xxx`–`1607428xxx`. **37 scopes, 2,624 cards.** QA'd by Elvis in `Process` and graduated 2026-09-29 into `Decks::Geography Drills::GeoTrainer::Physical` (leaf new limit 0).
- **Plateaus and grasslands from world-geography-concepts. ✅ Built and
  browser-verified 2026-09-23.** Two Place + Sketch scopes, **11 plateaus,
  highlands & basins** and **9 plains, grasslands & steppes**, whose polygons are
  the concept deck's own outlines (`data/sources/geo-concepts.geojson`,
  exported there and committed here) so both decks draw the same shape for the
  same name. Five members are hand outlines with no Natural Earth polygon; the
  Eurasian Steppe is excluded (no polygon, and its Pontic-Caspian and Kazakh parts
  are members). IDs `1607424xxx`–`1607425xxx`. The tap-the-members bloc drill in
  that project also gained the map's pan/zoom (`members-zoom`).
- **Demand-driven expansion policy.** Additional country subdivision scopes are not
  part of the core backlog: package them as optional expansion packs only if learner
  demand appears. Elvis would not use them now, so no speculative build is planned.
- **M5 — Release.** AnkiWeb-shaped packaging per workspace conventions (`release/ankiweb.md`,
  `anki-addon-release`), public repo decision, single-deck `geo-trainer-all.apkg`
  (`make apkg-all`) + `release/screenshots/`. The 2,405-card update is in the
  workspace's active AnkiWeb queue for existing shared deck `908455862`; uploading
  it remains a separate Publisher action subject to the AnkiWeb quota.

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

## Publication milestone — 2026-10-03

The first component, U.S. States, was submitted at AnkiWeb `909756180`: all
50 states × four games, 200 cards, with four approved actual-Anki GIFs.
The explicitly approved isolated-Publisher full Upload completed; personal Anki
was untouched. AnkiWeb's delivered package is the canonical GitHub
`v2026.10.03` artifact, SHA-256
`a4e942b5686a56b3ab501397e99d484e3ff224ede308e9bcb9f513a5f6441f8a`.
Native disposable import tests confirm the delivered component retains its
GUIDs/model/card/leaf-deck IDs across component → full candidate → component,
with zero duplicates. The candidate is only compatibility evidence; accepted
full-edition scope still needs reconciliation. Website component gallery and
download links are deployed and browser-verified.

Brazil is the next ready component using the U.S. four-game pattern: 26 states
plus the Federal District, 108 cards, with fresh actual-Anki Bahia recordings.
Native component/full/component imports preserve note/model/card/leaf-deck IDs
and create zero duplicates. Complete listing preview and GIF manifest are ready
for Elvis's approval. Publisher staging and submission remain pending.

### Brazil component shipped — 2026-10-03

Approved four-GIF listing submitted through `anki-addon-release` at `834723592`:
26 states plus the Federal District, 108 cards. Only the obsolete Publisher
Brazil copy was replaced; all other notes/cards/models are hash-identical.
Approved isolated-Publisher Upload and normal/final sync completed with clean
integrity. Canonical GitHub `v2026.10.03` now includes the exact AnkiWeb-delivered
Brazil APKG, SHA-256
`381da9926e435e0ce8a15804ecaaddd1b1fe497e9df064bc5a5149962d4beb48`; native
component/full/component import verification preserved all scoped identities
and created zero duplicate cards. AnkiWeb public review remains pending.
Fresh Bahia game gallery and canonical download links are deployed with the
standard support page. No personal Anki collection changes.

### China subdivision review checkpoint

Fresh China pack: 31 province-level divisions / 124 notes and cards across identification, placement, map sketch and outline drawing. Coverage includes 22 provinces, five autonomous regions and four municipalities; Hong Kong, Macao and Taiwan are excluded. All model/leaf IDs and note GUIDs survive native component → superseded full candidate → component imports with zero duplicates. Four Sichuan demonstrations were captured with native workbench input in disposable Anki 25.09 and visually verified, including positive placement/sketch/outline feedback. Complete listing preview and exact image manifest are prepared; Elvis’s image approval is pending. China has not been staged in Publisher or submitted. U.S. and Brazil remain shipped; broad concept reconciliation and final full union remain open. Root PUBLISH_QUEUE.md records the exact resume sequence.

### China approved and Publisher ready — 2026-10-04

Elvis approved the complete China listing and four actual-Anki GIFs. Immutable media URLs serve the exact approved bytes. Only the obsolete isolated Publisher China scope was replaced; 124 notes/cards match source GUIDs/fields/models/templates/CSS and leaf deck IDs. All other Publisher content is hash-identical. Previously approved full Upload completed, normal/final sync clear, native integrity/readback passed. No personal Anki changes. Submission and canonical archive verification follow.

### China component submitted — 2026-10-04

Approved 31-division / 124-card China listing submitted through anki-addon-release at `315064803`, exact source share name `GeoTrainer::World::Asia::China`, owner verified with public review pending. Six of 20 deck shares used. Actual AnkiWeb-delivered APKG SHA-256 `f95e481da79786e168a24e322e64c80f8dc9f28d6bfa4ee329486a9a427b1a01`; content/identities exactly match the Publisher export and native component/full-candidate/component imports preserve identities with zero duplicates. The full candidate remains compatibility evidence only. Canonical archive/tag: `v2026.10.04`, `geo-trainer-china-subdivisions.apkg`. Personal Anki unchanged.

### Reference Lines & Time review checkpoint — 2026-10-04

Accepted component rebuilt: 56 notes / 78 cards in ten leaves, comprising 24 reference-line/time drills and 54 atlas cards from 32 place notes (including 12 selected abbreviation cards). All 32 SVG maps are bundled and verified. Native disposable Anki 25.09 component → superseded full candidate → component imports preserve all note/model/card/leaf identities with zero duplicates; the full candidate is compatibility evidence only. Four distinct real-Anki workbench GIFs show globe placement, a UTC conversion crossing midnight, illustrated date-line recall and Kathmandu atlas recall. All answer renders visually checked. Complete listing copy/preview, source/license notes and image hashes are recorded in `release/packs/REFERENCE_LINES_TIME_*`. Image approval is pending; this scope has not been staged or submitted. Reference/time moves ahead of physical/tectonic packs because those still need accepted Geo Concepts source/media reconciliation. Personal collection untouched; China archive/storefront verification is complete.

### Reference/time approved, native export and Publisher verified — 2026-10-04

Elvis approved the complete listing and four GIFs. Native export exposed that scalar atlas filenames were not recognized as media references. The atlas builder now stores native HTML image references and renders the Map field directly, preserving the same output and identities. Corrected fresh Anki render and export verify all 32 maps, 56 notes / 78 cards. Outside-scope Publisher unchanged; approved Upload and normal/final sync clear. Submission follows.

### Reference Lines & Time submitted — 2026-10-04

Approved component submitted through anki-addon-release at `1962312135`, exact source name `GeoTrainer::Reference Lines & Time`; owner title/counts/five image URLs verified, public review pending. Seven of 20 deck shares used. Actual delivered APKG: 2,218,240 bytes, SHA-256 `ec4d7a40b7beb144f8b70786485d557bf64cbd1f6b30dc99a35da648453c7a70`. All 56 note and 78 card IDs/GUIDs/fields/model/template/CSS/leaf identities and all 32 media bytes match native export. Canonical archive and website verification follow. Personal Anki untouched.

### Reference/time archive and storefront verified — 2026-10-04

Exact delivered `geo-trainer-reference-lines-time.apkg` attached to `v2026.10.04`; GitHub digest/size verified. Combined release notes retain China and link Reference source commit `84f549d`. Website homepage, four approved GIFs and canonical download/release links deployed and Chrome-verified. No resubmission needed. Next broad packs require the recorded Geo Concepts reconciliation and fresh image review.


## Physical Geography preparation — 2026-10-04

The accepted component is rebuilt: 404 notes / 963 cards (250 map games and 713 concept cards), with all ten routed semantic families and all 223 media files. Missing Köppen rasters are restored with provenance and existing filenames retained. Native component/full/component overlap, native media export, public-source reproduction and all four shipped-component overlap checks pass. Corrected full-union candidate: 2,987 notes / 4,212 cards; no publication of that candidate. Five actual-Anki GIFs and complete listing await image approval. No Physical Geography Publisher staging or submission; personal collection untouched. See `release/packs/PHYSICAL_GEOGRAPHY_PREPARATION.md` for verification and exact resume steps.

Physical Geography shipped October 4 at `1832856685` (404 notes / 963 cards / 223 media). Five approved native GIFs deployed; exact delivered APKG verified against native export and archived on `v2026.10.04`. Publisher outside scope/media unchanged; approved Upload and normal/final sync clear. Next: Plate Tectonics preview.

Plate Tectonics preview prepared October 4: 204 notes / 492 cards, all four accepted concept families, ten model/leaf IDs and 70 media. Native export, public-source rebuild and component/full overlap pass. Five real-Anki GIFs and complete listing await image approval; no Publisher staging or image upload. Next resume: `release/packs/PLATE_TECTONICS_PREPARATION.md`.

Plate Tectonics image batch approved October 4. Exact approved GIFs deployed; native Publisher import and normal sync pass for 204 notes / 492 cards / 70 media, outside content/deck names/IDs/media unchanged. No full Upload required; normal/final required 0. Listing submission next.

Plate Tectonics shipped at 22154578, exact share name GeoTrainer::Plate Tectonics. Delivered APKG (204 notes / 492 cards, 70 media) identity/media exact and GitHub digest verified on existing v2026.10.04; prior assets/tag preserved. Owner listing and approved images verified; public review pending. Observed quota 9/20. Next: Islands & Archipelagos review.

Islands & Archipelagos preparation October 4: 76 notes / 112 cards (67 globe games + 45 concept cards), two models/leaves, ten SVG maps; native export/media, public rebuild and component/full overlap pass. Full ISC notices retained in bundled D3 code. Complete listing and two real-Anki GIFs awaiting image approval; no images uploaded or Publisher staging. See release/packs/ISLANDS_ARCHIPELAGOS_PREPARATION.md.

Islands image batch approved October 4. Two reviewed GIFs deployed with exact hashes. Native Publisher import/sync verifies 76 notes / 112 cards, two models/leaves, ten media; all outside content/deck names/IDs/media unchanged, normal/final required 0. No full Upload needed. Listing submission next.

Islands & Archipelagos shipped at 1449321738 on October 4, exact source/share name GeoTrainer::Islands & Archipelagos. Owner title/counts/banner/two GIF URLs verified; delivered 76 notes / 112 cards / ten media match native export. Exact delivered bytes digest verified on existing v2026.10.04; prior tag/assets preserved. Observed quota 10/20. Next: World Countries image review.

World Countries shipped October 4 at 452389265, exact share name GeoTrainer::World Countries. 900 notes / 1,220 cards / 77 maps include all accepted geometry, 59 membership drills and 396 concept cards. Approved six GIFs, Identify 2+3 seconds. Native export vs delivered identities/content/media exact; outside Publisher content unchanged, approved Upload and normal/final sync clear. Canonical date-tag artifact digest and live six-image gallery verified; Publisher closed, observed quota 11/20. Next: India subdivision image batch.

India subdivisions: 36 units / 140 cards; four real-Anki Maharashtra GIFs and complete listing ready for approval. Identify applies the 2+3-second pattern. Native export/reproducibility/zero-duplicate component-full checks passed; no Publisher staging or public media upload. See release/packs/INDIA_SUBDIVISIONS_PREPARATION.md.

India subdivisions shipped October 4 at 346168633, exact share name GeoTrainer::World::Asia::India. 36 units / 140 cards, four approved native Maharashtra GIFs (Identify 2+3 seconds). Actual delivered content and identities exact against native export; canonical archive digest verified. Outside Publisher content/media unchanged; approved Upload completed and normal/final required 0 after native metadata reconciliation. Website/gallery/release links updated. Quota 12/20; next Russia image batch.

Russia publication preparation: 85 source map units / 333 cards, four native Sakha game GIFs and complete listing await image approval. Name-only upstream English-label corrections plus Moscow/Altai disambiguation preserve all geometry/identity spaces. Territory/source note explicitly explains Crimea/Sevastopol scope. Public rebuild/native export/component-full overlap pass; all other full-union content unchanged, full remains 2,987 notes / 4,212 cards unpublished. No Publisher staging or public Russia media upload.

Russia component shipped October 4 at 2018363684, exact source/share name GeoTrainer::World::Europe::Russia. Approved 333-card pack and four native GIFs. Delivered content/identities match native export; exact bytes archived on existing v2026.10.04, prior seven assets/tag unchanged. Outside Publisher content/deck names/IDs/media unchanged; approved full Upload and normal/final sync clear. Quota 13/20; next Canada image batch. Personal Anki untouched.

Canada image review: 13 units / 52 cards, all four tasks per unit, no omissions. Public rebuild/native export/component-full-component pass with zero duplicates. Complete listing and four real-Anki Ontario GIFs ready for approval; Identify 2+3 seconds, full map/canvas and feedback visible. No Publisher staging/public media upload. See release/packs/CANADA_SUBDIVISIONS_PREPARATION.md.

Canada shipped October 4 at 1166705214, exact source/share name GeoTrainer::World::North America::Canada. All 13 provinces/territories / 52 cards, four approved native Ontario GIFs (Identify 2+3 seconds). Delivered content/identities exact against native export; canonical existing v2026.10.04 asset digest verified, prior eight assets/tag retained. All outside Publisher content/deck names/IDs/media unchanged; approved Upload and normal/final required 0. Quota 14/20; next Australia image batch. Personal Anki untouched.

Australia image review: 9 units / 35 cards, four tasks with Jervis Bay contextual-sketch omission. Exact source scope includes six states, ACT, NT and Jervis Bay; external territories excluded. Public rebuild/native export/zero-duplicate full overlap pass. Complete listing/four native Queensland GIFs await approval, Identify 2+3 seconds, full maps/canvas/feedback. No public media upload or Publisher staging. See release/packs/AUSTRALIA_SUBDIVISIONS_PREPARATION.md.

Australia shipped October 5 at 1585515572, exact source/share name GeoTrainer::World::Oceania::Australia. Approved 35-card pack/four native Queensland GIFs, Identify 2+3 seconds. Delivered content/identities match native export; exact archive digest verified on v2026.10.05. All outside Publisher content/deck names/IDs/media unchanged; approved Upload and normal/final required 0, integrity ok. Quota 15/20; next Mexico image batch with corrected public-only display labels, all identities/geometry preserved. Personal Anki untouched.

Mexico image review: 32 units / 128 cards, no omissions. Public-only Mexico City/State of Mexico display-label corrections preserve all geometry/source keys/GUIDs/model/leaf identity spaces; public rebuild and every non-Mexico full note/model unchanged. Native export/full-overlap pass with zero duplicates. Complete listing/four native Jalisco GIFs await approval; Identify 2+3 seconds, full maps/canvas/feedback. No public media upload or Publisher staging. See release/packs/MEXICO_SUBDIVISIONS_PREPARATION.md.

Mexico shipped October 5 at 875505875, exact source/share name GeoTrainer::World::North America::Mexico. Approved 128-card pack/four native Jalisco GIFs, Identify 2+3 seconds. Source/export/delivered content and identities match; exact v2026.10.05 archive digest verified, Australia asset/tag preserved. All outside Publisher content/deck names/IDs/media unchanged; approved Upload and normal/final required 0, integrity ok. Quota 16/20; next Argentina image batch, Indonesia, full edition last. Personal Anki untouched.

Argentina image review: 24 jurisdictions / 96 cards, no omissions; existing source labels/geometry/model/deck/GUIDs retained. Native export/public rebuild/zero-duplicate full-overlap pass. Complete listing/four native Córdoba GIFs await approval; actual Identify scenes 2+3 seconds, full maps/canvas/feedback. No public image upload or Publisher staging. See release/packs/ARGENTINA_SUBDIVISIONS_PREPARATION.md.

Argentina shipped October 5 at 1530523005, exact source/share name GeoTrainer::World::South America::Argentina. Approved 96-card pack/four native Córdoba GIFs, Identify 2+3 seconds. Source/export/delivered identities/content exact; v2026.10.05 digest verified, prior assets/tag retained. All outside Publisher content/deck names/IDs/media unchanged; approved Upload and normal/final required 0, integrity ok. Quota 17/20. Next Indonesia: existing map has 33 provinces, current BPS catalog has 38; current-map vs historical-edition decision requested, no Indonesia publication/staging. Full edition last; legacy public-full import compatibility still to verify. Personal Anki untouched.


Indonesia public update authorized October 5: 38 provinces / 151 cards (38 Identify, 38 Place, 37 Sketch, 38 Draw). All 33 legacy region keys and 131 note/card identities retained, with 20 new notes. Current MIT Peta Nusa/Laravel Nusa boundaries replace the 33-province Natural Earth map; native old→new→full→component test creates zero duplicates. Corrected full candidate is 3,007 notes / 4,232 cards; all non-Indonesia content unchanged. Four native North Kalimantan GIFs and complete listing need explicit review before public media or Publisher staging. Personal collection audit is read-only; no live import or rollout authorized.

## Indonesia shipped and full legacy gate — October 5

Indonesia `1473740061`, exact share/source name `GeoTrainer::World::Asia::Indonesia`:
38 provinces / 151 cards, four approved native GIFs. Owner counts/images verified;
public review pending. Actual delivered APKG 1,625,379 bytes, SHA-256
`7c5a14e693509350045a62e5982068fb793c5453a150e31c22732599dfba0c8b`,
digest-verified on `v2026.10.05`; previous assets/tag retained. All outside Publisher
content/names/IDs/media unchanged; approved Upload and normal/final required 0,
ledger closed, task-owned Publisher closed. Website commit `79c5cd6` locally
verified; deployment queued during GitHub Actions runner delays. Approved listing
GIFs use exact bytes from immutable GitHub hosting during that incident. Quota
18/20; no limit rejection, reset unknown. Do not resubmit.

Delivered components contain all 1,573 accepted Geo Concepts cards under subject
packs; recognition/fact cards complement games. Actual July full import receives
stale old templates with merge disabled and extra cards with merge enabled. Hold
full publication until GUID/model/schema/card identity and scheduling are verified
across legacy and delivered-component import paths. Continue map/content/source
checks as requested. No personal collection mutation/import/sync.


### October 5: described public tree and varied GIF revision

AnkiWeb owner catalog reports 35 downloads for listing 908455862, modified
July 15. Downloads are not unique users, include our QA download and have no
version breakdown. Treat July users as potentially present; the model-ID
exception remains pending. See FULL_LEGACY_DOWNLOAD_COUNT_2026-10-05.json.

All 159 accepted public decks now carry native Markdown descriptions and
Wikipedia background links (114 leaves and 45 explicit containers), including
a Köppen climate-code guide. The source retains every existing leaf deck ID,
model ID, GUID, field and card-template/CSS value. Anki 25.09 imports and
rendered links pass; all descriptions survive reimport of the fifteen delivered
components. Their already archived bytes remain unchanged; description-only
component refreshes are queued separately. The described full package still has
3,007 notes / 4,232 cards. See FULL_DECK_DESCRIPTIONS_2026-10-05.json and
DECK_DESCRIPTIONS_2026-10-05.md. Native legacy migration proof passes again with
this exact package; FULL_DESCRIBED_LEGACY_UPGRADE_2026-10-05.json. This proof
remains a disposable test, not a supported upgrader for users.

Elvis requested subject variety after the earlier image approval. Revised batch:
Italy Identify; California Place (new native pointer recording); France Sketch;
Maharashtra, India Draw; EU membership; Amazon trace; Japan archipelago; Tropic
of Cancer; UTC/date conversion; tropical moist forest concept. Ten animated GIFs
remain the listing format. The complete revised batch needs fresh approval;
FULL_EDITION_REVIEW_2026-10-05.json pins current media hashes. No new public
media upload, Publisher staging, full submission or personal collection access.
Build accepted full only with `python scripts/build_apkg.py --public-full`.

## Publication safety — October 5, 2026

Local staged-object and outgoing-history gates, generic public CI, external live recovery directories, and exact-artifact checks are implemented. See [the publication process](release/PUBLICATION_PROCESS.md). Private audit details are outside Git; the existing release/upgrade holds remain in force.
