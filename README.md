[China Provinces & Regions on AnkiWeb](https://ankiweb.net/shared/info/315064803) — **31 mainland province-level divisions, 124 cards**: 22 provinces, five autonomous regions and four municipalities. Hong Kong, Macao and Taiwan are excluded. Submitted October 4; public review pending. [Download the canonical APKG](https://github.com/ritornello-labs/anki-geo-trainer/releases/download/v2026.10.04/geo-trainer-china-subdivisions.apkg) or [see all four Sichuan demos](https://ritornello.dev/#geo-trainer-china-subdivisions).

[Brazilian States on AnkiWeb](https://ankiweb.net/shared/info/834723592) — **26 states plus the Federal District, 108 cards**, with the same four spatial recall games. Submitted October 3; public review pending. [Download the canonical APKG](https://github.com/ritornello-labs/anki-geo-trainer/releases/download/v2026.10.03/geo-trainer-brazil-subdivisions.apkg) or [see all four Bahia demos](https://ritornello.dev/#geo-trainer-brazil-states).

# GeoTrainer

[![License: MIT](https://img.shields.io/badge/license-MIT-16A34A)](LICENSE)
[![AnkiWeb](https://img.shields.io/badge/AnkiWeb-shared%20deck-15A5EF)](https://ankiweb.net/shared/info/908455862?cb=1784084661007)
![Anki platforms](https://img.shields.io/badge/Anki-Desktop%20%7C%20Mobile%20%7C%20Droid-0EA5E9)

Interactive geography practice for Anki: a curriculum-ordered set of map tasks that
asks you to locate, place, sketch, draw, trace, and place archipelagos on a globe from
memory. It runs
offline on Anki Desktop, AnkiMobile, and AnkiDroid.

![GeoTrainer place-the-shape review in Anki](https://ritornello.dev/media/ankiweb/2026-08-06-v4/geo-trainer/preview.gif)

The animation is captured from real Anki. [Browse all GeoTrainer samples](https://ritornello.dev/#geo-trainer).

**Available on AnkiWeb:** [https://ankiweb.net/shared/info/908455862?cb=1784084661007](https://ankiweb.net/shared/info/908455862?cb=1784084661007)

**Release status:** components will ship first, followed by the full edition. The previous full-edition preview and package counts are superseded pending [scope reconciliation](release/SCOPE_RECONCILIATION_2026-10-03.md). The U.S. States component was submitted on October 3; AnkiWeb public review is pending. See [pack records](release/PACKS.md).

Accepted content includes countries and continent silhouettes; subdivisions of ten countries; rivers, lakes, ranges, deserts, plateaus, grasslands and peninsulas; major/minor tectonic plates and boundaries; islands and archipelagos; and reference lines and time zones. The physical-systems QA scopes and foundations prototype remain outside the public packages.

Each scope retains its existing model IDs, leaf deck IDs, and note GUIDs in every pack and the full edition. An overlapping import updates the same notes.

## Component downloads

| Component | Cards | AnkiWeb | GitHub archive |
|---|---|---|---|
| U.S. States | 200 (50 states × four tasks) | [909756180](https://ankiweb.net/shared/info/909756180) — public review pending | [v2026.10.03 APKG](https://github.com/ritornello-labs/anki-geo-trainer/releases/download/v2026.10.03/geo-trainer-united-states-subdivisions.apkg) |

[See the four U.S. games](https://ritornello.dev/#geo-trainer-us-states). Components share their source identities with the forthcoming full edition.

[Reference Lines & Time on AnkiWeb](https://ankiweb.net/shared/info/1962312135) — **56 notes, 78 cards**: globe reference-line placement, illustrated explanations, randomized UTC conversion and a 32-place time-zone atlas. All 32 maps are bundled for offline study. Submitted October 4; public review pending. [Download the canonical APKG](https://github.com/ritornello-labs/anki-geo-trainer/releases/download/v2026.10.04/geo-trainer-reference-lines-time.apkg) or [see the four demonstrations](https://ritornello.dev/#geo-trainer-reference-lines-time).

## Task families

| Deck | Skill | Interaction |
|------|-------|-------------|
| `…::1 Which State/Country` | position → name | A dot appears *inside* a region (different spot each review) on a **borderless** map; recall which one it is |
| `…::2 Place` | precise position | Drag the region's silhouette onto the **borderless** map to where it belongs — no labelled slot to snap into |
| `…::3 Sketch` | scaffolded shape + position recall | Draw the named country on its blank continent, a state/province on its blank country, or a continent on the blank world. The map has no internal borders; the back reveals the target and grades shape, position, and scale. Map-magnified microstates are omitted because their circles are interaction aids, not drawable geography |
| `…::4 Draw` | unscaffolded shape recall | Sketch the outline from memory on a blank **fixed-square** canvas (uniform for every card, so the frame never hints the answer's aspect ratio; multi-stroke, undo/clear); the back overlays the true shape and grades the match. Scoring gates on **both** boundary faithfulness and area overlap (IoU), so a right-size wrong-shape blob — a lazy circle over Algeria — fails to *Again*, while an honest freehand attempt (even wobbly) passes. Position and size don't matter, form does |
| `…::1 Trace` (rivers) | river course | Trace a major river's course over a world map; the back overlays the true line and grades by distance (km) to it. Start on the *full* world map (no positional hint), then zoom in to trace precisely |
| `World::Islands::1 Globe Placement` | spherical location + extent | Rotate a random globe and draw an editable ellipse covering the named island or archipelago; the back grades coverage, center, and footprint |

Drawing surfaces (Sketch, Draw, Trace) have **zoom + pan** via floating map-style controls
in the canvas corner (Google-Maps-like): a stacked **＋/−** zoom pill and a **✋**
toggle that turns a drag into a pan (so you can reposition a zoomed-in view onto, say,
South America to trace the Amazon). Mouse-wheel also zooms; on touch you can pinch-zoom
and two-finger pan; on desktop a right-drag pans without the toggle. Only the SVG
viewBox changes, so strokes stay in map coordinates and grading is exact at any zoom.

Cards are self-graded: the card shows a verdict and a suggested grade; you still
press Anki's answer buttons. Region maps hide internal borders on the front so the
task is genuine spatial recall, not shape-matching. Alaska and Hawaii render in
classic inset panels at their own scale; microstates are magnified tap-circles on
the *back*; Physical polygon scopes hide the feature on the front and show only the
continents.

**Design note (2026-07):** Locate (redundant), Capital (duplicated a Cities deck),
and Seas (trivial at world scale) were cut after studying the deck for real; the
survivors were made non-trivial by hiding the borders. Sketch was later added as
the scaffolded bridge from Place to blank-canvas Draw. Lakes and plates use only
the families that produce honest world-scale practice; chokepoints and island lists
remain deliberately excluded. Quality of each card type over breadth.

## Why

Anki's geography ecosystem covers *passive* recall well: highlighted region → name,
silhouette → name. Active practice adds further skills: find a region on a blank map,
judge a random point, place a silhouette, and draw an outline from memory. This project builds that ladder as Anki
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

Support continued development: [ritornello.dev/support](https://ritornello.dev/support).

Plate Tectonics: [AnkiWeb](https://ankiweb.net/shared/info/22154578) (public review pending) · [GitHub release](https://github.com/ritornello-labs/anki-geo-trainer/releases/tag/v2026.10.04) · [Exact delivered APKG](https://github.com/ritornello-labs/anki-geo-trainer/releases/download/v2026.10.04/geo-trainer-plate-tectonics.apkg). 204 notes / 492 cards; 70 bundled media files.

Islands & Archipelagos component preparation: `python scripts/build_islands_archipelagos_pack.py` builds the accepted 76-note / 112-card pack, with 67 globe games and nine concept notes (45 cards). Exact stable model/leaf IDs and GUIDs overlap the full edition. Ten concept maps bundled; full D3 ISC notices included. Published listing and release links below.

Islands & Archipelagos: [AnkiWeb](https://ankiweb.net/shared/info/1449321738) (public review pending) · [GitHub release](https://github.com/ritornello-labs/anki-geo-trainer/releases/tag/v2026.10.04) · [Exact delivered APKG](https://github.com/ritornello-labs/anki-geo-trainer/releases/download/v2026.10.04/geo-trainer-islands-archipelagos.apkg). 76 notes / 112 cards; ten bundled maps.

World Countries component preparation: `python scripts/build_world_countries_pack.py` builds all accepted geometry, membership drills and concepts: 900 notes / 1,220 cards, 77 bundled maps. Six actual-Anki GIFs and complete listing approved; native export, reproducibility and overlap checks passed. Published links below.

World Countries: [AnkiWeb](https://ankiweb.net/shared/info/452389265) (public review pending) · [GitHub release](https://github.com/ritornello-labs/anki-geo-trainer/releases/tag/v2026.10.04) · [Exact delivered APKG](https://github.com/ritornello-labs/anki-geo-trainer/releases/download/v2026.10.04/geo-trainer-world-countries.apkg). 900 notes / 1,220 cards; all 77 maps. Identify uses 2 seconds front + 3 seconds answer, the default for similar static reveal drills.

India component preparation: `python scripts/build_india_subdivisions_pack.py` builds 140 cards across 36 states/union territories, four task models and stable leaves. Native export, reproducibility and component/full overlap passed. Four actual-Anki Maharashtra GIFs and complete listing approved and submitted.

Indian States & Union Territories: [AnkiWeb](https://ankiweb.net/shared/info/346168633) (public review pending) · [GitHub release](https://github.com/ritornello-labs/anki-geo-trainer/releases/tag/v2026.10.04) · [Exact delivered APKG](https://github.com/ritornello-labs/anki-geo-trainer/releases/download/v2026.10.04/geo-trainer-india-subdivisions.apkg). 36 units / 140 cards, four offline spatial games; 32 contextual sketches.

Russian Regions: [AnkiWeb](https://ankiweb.net/shared/info/2018363684) (public review pending) · [GitHub release](https://github.com/ritornello-labs/anki-geo-trainer/releases/tag/v2026.10.04) · [Exact delivered APKG](https://github.com/ritornello-labs/anki-geo-trainer/releases/download/v2026.10.04/geo-trainer-russia-subdivisions.apkg). 85 source map units / 333 cards, four approved native Sakha game GIFs. Corrected English labels and territory/source caveats; stable geometry and identity spaces. Rebuild: `python scripts/build_russia_subdivisions_pack.py`.

Canadian Provinces & Territories: [AnkiWeb](https://ankiweb.net/shared/info/1166705214) (public review pending) · [GitHub release](https://github.com/ritornello-labs/anki-geo-trainer/releases/tag/v2026.10.04) · [Exact delivered APKG](https://github.com/ritornello-labs/anki-geo-trainer/releases/download/v2026.10.04/geo-trainer-canada-subdivisions.apkg). All 13 provinces/territories / 52 cards, four approved native Ontario GIFs. Rebuild: `python scripts/build_canada_subdivisions_pack.py`; native export and zero-duplicate full overlap passed.

Australian States & Territories: [AnkiWeb](https://ankiweb.net/shared/info/1585515572) (public review pending) · [GitHub release](https://github.com/ritornello-labs/anki-geo-trainer/releases/tag/v2026.10.05) · [Exact delivered APKG](https://github.com/ritornello-labs/anki-geo-trainer/releases/download/v2026.10.05/geo-trainer-australia-subdivisions.apkg). 9 source units / 35 cards, four approved native Queensland GIFs. Six states, ACT, NT and Jervis Bay; Jervis Bay omits contextual sketch only. Rebuild: `python scripts/build_australia_subdivisions_pack.py`; native export and zero-duplicate full overlap passed.

Mexican States & Mexico City: [AnkiWeb](https://ankiweb.net/shared/info/875505875) (public review pending) · [GitHub release](https://github.com/ritornello-labs/anki-geo-trainer/releases/tag/v2026.10.05) · [Exact delivered APKG](https://github.com/ritornello-labs/anki-geo-trainer/releases/download/v2026.10.05/geo-trainer-mexico-subdivisions.apkg). 31 states plus Mexico City / 32 entities / 128 cards, four approved native Jalisco GIFs. Public-only labels distinguish Mexico City and State of Mexico; geometry and identities retained. Native export/public rebuild/zero-duplicate full overlap passed. Rebuild: `python scripts/build_mexico_subdivisions_pack.py`.

Argentina component preparation: `python scripts/build_argentina_subdivisions_pack.py` builds 23 provinces plus Buenos Aires city / 24 jurisdictions / 96 cards, all four tasks per entity. Source labels/geometry/identities retained; native export/public rebuild/full-overlap pass, zero duplicates. Complete listing/four native Córdoba GIFs await approval; no public image upload/Publisher staging. See `release/packs/ARGENTINA_SUBDIVISIONS_PREPARATION.md`.
