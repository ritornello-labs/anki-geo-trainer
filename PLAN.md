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
| F1 | Recognize | highlighted region on locator map → recall name | tutorial levels | Already covered by existing decks; we tag/reference, not rebuild |
| F2 | Shape ID | isolated silhouette → recall name | shape quizzes | Covered for countries (Country Shapes); build only for missing scopes |
| F3 | Locate | name shown → tap/click the region on a blank map | click-on-map games | Engine highlights what you hit, then reveals the answer region; self-grade with distance feedback |
| F4 | Point-in-region | random dot on a blank map → name the region containing it | "which state is this point in" | Dynamic: point re-randomized per review, stable within one review (front and back must agree) |
| F5 | Place-the-piece | drag a floating silhouette to its correct position on a faded or blank map | place-the-state (hard levels) | Score by centroid offset + rotation-free overlap |
| F6 | Draw-the-shape | sketch the outline of a named region on a canvas; engine scores vs. truth | draw-the-state | Hardest to build well: normalization + IoU-style scoring + visual overlay feedback |
| F7 | Neighbors | name/blank map → enumerate or tap all bordering regions | border quizzes | Passive variant exists (Country Borders); interactive tap-all variant is new |
| F8 | Feature overlay | rivers, mountain ranges, seas, capitals as tap targets on the map | rivers/landscapes games | Later phase; reuses F3/F4 machinery with line/point features |

Cross-cutting variants (per family, where meaningful): political vs. physical basemap,
labeled vs. unlabeled neighbors, timed vs. untimed presentation.

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
  approach; this project is its first serious consumer.
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
F1→F2→F3→F4→F5→F6, with F1/F2 satisfiable by existing public decks (Ultimate Geography,
the user's shared subdivision decks) — the trainer decks start at F3. Deck structure
mirrors scope (`GeoTrainer::World::Europe::Locate`, etc.) so students can subscribe to
exactly the slice they want; tags let power users rebuild any custom ordering.

## Milestones

- **M0 — Engine spike (prove the risky part first).** One F3 Locate card (US states)
  end-to-end: inlined engine, tap detection against real polygons, front→back attempt
  handoff, verdict UI, night mode. Verified on Chromium + WebKit harnesses, workbench
  Docker smoke, and the AnkiDroid emulator lane. Also spike F4's stable randomness.
- **M1 — US states pack.** F3 + F4 + F5 for the 50 states; curriculum tags; APKG built
  and imported; first real dogfood.
- **M2 — World countries.** Same families by continent (Europe first), entity tiering
  (UN members vs. territories), F7 tap-all-neighbors.
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
  define the scope catalog and provide F1/F2 coverage; trainer decks reference them
  in the curriculum rather than duplicating.
- `anki-dynamic-cards` — its stable-randomness prototype becomes F4's foundation.
- `sight-singing-deck` — the cross-platform JS playbook (inline everything, dep polling,
  WebKit + AnkiDroid lanes) is adopted wholesale.
- `anki-addon-workbench` — all smoke/GUI verification.

## Open questions (for Elvis)

1. Repo/deck naming: is `anki-geo-trainer` / `GeoTrainer::…` good, or prefer another name?
2. F1/F2: reference existing decks only (personal curriculum), or also generate
   self-contained versions so the published product stands alone?
3. Release intent: personal-first then AnkiWeb, or design for AnkiWeb from day one?
4. Languages: English-only to start? (`anki-multilingual-concepts` could matter later.)
5. Timed modes: worth it inside Anki, or does it fight the review model? (Lean: skip.)
