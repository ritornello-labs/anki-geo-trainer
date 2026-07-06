# anki-geo-trainer

Sheppard-Software-style interactive geography practice for Anki: a comprehensive,
curriculum-ordered set of map-interaction task types rendered by a shared JS engine
that works on Anki Desktop, AnkiMobile, and AnkiDroid.

Status: M4c — **eighteen scopes** across six task families (Locate, Which
State/Country, Place, Draw, Capital, River). Continents: **Europe** (46),
**South America** (12), **Africa** (53), **Asia** (47), **Oceania** (14). Country
subdivisions: **United States** (50 states), **Brazil** (27), **India** (36),
**Russia** (85 subjects), **China** (31), **Canada** (13), **Australia** (9),
**Argentina** (24), **Mexico** (32), **Indonesia** (33). Physical: **world seas &
oceans** (97) and **major rivers** (84). All rendered by one shared engine and
verified on Desktop/WebKit/AnkiDroid. See [`PLAN.md`](./PLAN.md) for the roadmap,
[`curriculum/CURRICULUM.md`](./curriculum/CURRICULUM.md) for the skill ladder and
filtered-deck recipes, and [`release/RELEASE.md`](./release/RELEASE.md) for the
publishing plan.

New scopes are pure config: a continent is a viewport box + a Natural Earth
`CONTINENT` filter; a country subdivision is an ISO country code. Both feed the
same builder, so adding a scope is a few lines in `scripts/build_bundle.py`.

## Task families (shipped so far)

| Deck | Skill | Interaction |
|------|-------|-------------|
| `…::1 Locate` | name → position | Tap the named region on a blank map; the back grades your tap (inside / missed-by-km / what you hit) |
| `…::2 Which State/Country` | position → name | A dot appears somewhere *inside* a region (never hugging a border, different spot each review); name it |
| `…::3 Place` | precise position | Drag the region's silhouette from a tray to its exact spot; graded by how far off you were |
| `…::4 Draw` | shape recall | Sketch the region's outline from memory (multi-stroke, undo/clear); the back overlays the true shape on your drawing and grades the match — position and size don't matter, form does |
| `…::5 Capital` | capital location | Tap where the named capital city is on the blank map; the back stars the true spot, draws your tap, and grades by distance in km |
| `…::6 River` | river location | Tap where a major river runs on a world map; the back highlights the river line and grades by distance to it (physical scopes) |

All four are self-graded: the card shows a verdict and a suggested grade; you still
press Anki's answer buttons. Alaska and Hawaii render in classic inset panels at
their own scale (cross-panel distances are never reported — they'd be meaningless).
On the Europe map, microstates are magnified tap-circles, dependencies are muted
map-context without cards, and Africa/Anatolia appear as neutral land for orientation.

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
