# GeoTrainer Curriculum

How the trainer decks are ordered, tagged, and combined into study tracks.
This file is the human-readable source of truth; the tags on every note make the
same structure machine-usable inside Anki.

## The skill ladder

Within any scope (a continent's countries, a country's states), skills stack in
this order. Each rung assumes comfort with the one before it.

| Level | Skill | Deck kind | What you do |
|-------|-------|-----------|-------------|
| 1 | Recognize | *external* (see below) | Highlighted region on a map → recall its name |
| 2 | Shape ID | *external* (see below) | Isolated silhouette → recall its name |
| 4 | Which one? | `1 Which State/Country` | Dot on a **borderless** map → name the region under it (pure spatial recall — no borders to read) |
| 5 | Place | `2 Place` | Drag the region's silhouette onto the **borderless** map to where it belongs — no labelled slot |
| 5.5 | Sketch | `3 Sketch` | Draw the region in place on its **borderless parent map**; the parent outline scaffolds recall, while shape, position, and scale are graded |
| 6 | Draw | `4 Draw` | Sketch the outline on a completely blank square; scored on capturing the real shape (a rough enclosing blob fails) |
| 5 | Trace | `1 Trace` (rivers) | Trace a river's course over a world map; graded by km distance to the true line |

**Redesign (2026-07), after studying the deck for real.** Cut families that were
trivial or redundant: **Locate** (tapping a labelled shape isn't recall), **Capital**
(duplicated the Cities/World-Capitals deck), and **Seas** (trivial at world scale).
The survivors — Which / Place / Draw — were the ones the borders made trivial, so
their fronts now hide all internal borders (the map is a blank silhouette; you recall
*where*, not *which shape*). Draw's scoring was rebuilt to reward capturing distinctive
features. **Sketch** was added later as a scaffolded bridge: draw the same shape in
place on the blank parent map before graduating to the context-free Draw card. Rivers
became **Trace-the-course** (drawing a river is interesting; tapping
where it is was not). New physical scopes: **mountain ranges** and **deserts** (name /
place / draw the feature over the continents). A tap-all-neighbors family (F7) was
retired even earlier (duplicated border decks). The engine keeps the dropped modes
dormant, so any could return.

Levels 1–2 are passive recognition, already well served by existing shared decks —
GeoTrainer does not duplicate them. Good on-ramps:

- [Ultimate Geography](https://ankiweb.net/shared/info/2109889812) — countries,
  capitals, flags, maps
- The per-country subdivision decks published from this workspace (e.g.
  [U.S. states](https://ankiweb.net/shared/info/1539478471),
  [Brazilian DDD regions](https://ankiweb.net/shared/info/1860702413),
  [China regions](https://ankiweb.net/shared/info/159990073))

## Tags

Every note carries three orthogonal tags:

- `geotrainer::skill::locate | point | place | sketch | draw | neighbors | feature`
- `geotrainer::scope::<where>` — e.g. `geotrainer::scope::country::usa::states`,
  `geotrainer::scope::continent::europe`
- `geotrainer::level::3..6` (including `5.5`) — the rung on the ladder above

## Building a study track (filtered decks)

Anki cannot ship filtered decks inside an `.apkg`, so tracks are copy-paste
searches. Create a Filtered Deck (Tools → Create Filtered Deck) and paste one of
these, adjusting as you like:

- **US mastery, in ladder order** (study Which before Place before Sketch before Draw —
  make one filtered deck per level, or study subdecks in order, which is the
  default deck ordering anyway):
  - `deck:GeoTrainer::* tag:geotrainer::level::3 is:due`
  - `deck:GeoTrainer::* tag:geotrainer::level::4 is:due`
  - `deck:GeoTrainer::* tag:geotrainer::level::5 is:due`
  - `deck:GeoTrainer::* tag:geotrainer::level::5.5 is:due`
  - `deck:GeoTrainer::* tag:geotrainer::level::6 is:due`
- **All map-tapping skills across scopes**:
  `deck:GeoTrainer::* (tag:geotrainer::skill::locate OR tag:geotrainer::skill::place) is:due`

The region subdeck names are numbered (`1 Which`, `2 Place`, `3 Sketch`, `4 Draw`) so plain
deck-order study already follows the ladder.

## Suggested pacing

- Unlock level N+1 for a scope when level N feels comfortable (say, >90% correct
  over a week) — Anki's own scheduling handles the rest.
- The four region families are complementary: Which builds place→name (and interior
  geography — the dot is rarely at the centroid); Place supplies the shape and tests
  location; Sketch removes the supplied shape but keeps the parent-map scaffold; Draw
  removes the scaffold as well.

## Scope roadmap

- **Shipped**: United States — 50 states, 4 families (Alaska and Hawaii in inset
  panels at their own scale; distance feedback is suppressed across panels
  because it would be meaningless). 198 notes.
- **Shipped**: Europe — 46 sovereign countries (incl. Cyprus and Kosovo), 4
  families, 180 notes. The viewport runs Iceland→Urals; Russia is clipped at the
  frame edge. Microstates (Vatican, Monaco, San Marino, Liechtenstein, Andorra,
  Malta, …) appear as magnified tap-circles, Ultimate-Geography style.
  Dependencies (Faroes, Åland, Crown dependencies) stay on the map as muted,
  tappable context but get no cards.
- **Shipped**: Draw-the-shape (level 6) on every scope. Each note carries its own
  hi-res outline; overseas territory is excluded from the drawing box (mainland
  France, Norway without Svalbard) while nearby parts stay (Sicily/Sardinia,
  Northern Ireland, Hawaii's island chain).
- **Shipped (M4)**: three more continents — **South America** (12 countries),
  **Africa** (53), **Asia** (47; Turkey→Japan, Timor→the steppe, Russia clipped at
  the top) — plus subdivisions. Continents reuse Europe's machinery (viewport box +
  `CONTINENT` filter, sovereign/dependency tiering, microstate tap-circles).
- **Shipped (M4b)**: six more subdivisions — **Russia** (85 federal subjects,
  antimeridian-unwrapped), **China** (31), **Canada** (13), **Australia** (9) from
  the 50m admin-1 file; **Argentina** (24) and **Mexico** (32) from the 10m file
  (the 50m file only carries provinces for nine large countries — AUS, BRA, CAN,
  CHN, IDN, IND, RUS, USA, ZAF). And the **F8 Capital** family on every scope
  (national capitals for continents, state/province capitals for subdivisions;
  capitals from 10m populated-places, matched by point-in-region). **13 scopes ×
  5 families = 2,286 notes.**
- **Shipped (M4c)**: **Indonesia** (33 provinces) and the **Oceania** continent (14
  sovereigns; the continent builder gained antimeridian unwrapping so Australia→NZ→the
  Pacific island nations render in one Pacific-centred view). Two physical-feature
  scopes: **world seas & oceans** (97 named water bodies as tappable polygons, locate
  + which + draw families) and **major rivers** (84, via a new line-locate "River"
  family — tap where the river runs, graded by distance to the polyline). Physical
  scopes declare a `families` list so they ship only the sensible tasks; a `kind`
  marker (physical/rivers) drives the test suite.
- **Later**: mountain ranges (needs the 10m geography-regions file — the 50m has no
  `featurecla`); lakes; more country subdivisions from 10m admin-1. Then AnkiWeb
  release — see [`release/RELEASE.md`](../release/RELEASE.md).

### Adding a scope (for future me)

Continent: add an entry to `CONTINENT_SCOPES` in `scripts/build_bundle.py` (title,
lon/lat `box`, `CONTINENT` value, optional `extra_admins`/`exclude_admins`/
`name_overrides`/`tray` corner) and a `SCOPE_PACKS` entry in `build_apkg.py` (deck
root, model root, tag, fresh id bases). Country subdivision: add to
`SUBDIVISION_SCOPES` (title, ISO-3 `a3`, `noun`) + a `SCOPE_PACKS` entry. Then
`build_bundle.py && build_apkg.py`; the `scopes.spec.mjs` smoke picks it up
automatically. Never reuse a retired family id (ord 3 = neighbors).
