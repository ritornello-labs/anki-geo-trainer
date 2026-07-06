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
| 3 | Locate | `1 Locate` | Name shown → tap where it is on a blank map |
| 4 | Point-in-region | `2 Which State/Country` | Random dot on a blank map → name the region under it |
| 5 | Place | `3 Place` | Drag the region's silhouette to its exact position |
| 6 | Draw | `4 Draw` | Sketch the region's outline from memory; scored against the true shape (translation/scale-invariant) |

A tap-all-neighbors family (F7) shipped briefly in M2 and was retired the same day:
it duplicates the passive border decks already in the user's collection. The engine
mode still exists (dormant) if a scope ever wants it back.

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

- `geotrainer::skill::locate | point | place | draw | neighbors | feature`
- `geotrainer::scope::<where>` — e.g. `geotrainer::scope::country::usa::states`,
  `geotrainer::scope::continent::europe` (planned)
- `geotrainer::level::3..6` — the rung on the ladder above

## Building a study track (filtered decks)

Anki cannot ship filtered decks inside an `.apkg`, so tracks are copy-paste
searches. Create a Filtered Deck (Tools → Create Filtered Deck) and paste one of
these, adjusting as you like:

- **US mastery, in ladder order** (study Locate before Which State before Place —
  make one filtered deck per level, or study subdecks in order, which is the
  default deck ordering anyway):
  - `deck:GeoTrainer::* tag:geotrainer::level::3 is:due`
  - `deck:GeoTrainer::* tag:geotrainer::level::4 is:due`
  - `deck:GeoTrainer::* tag:geotrainer::level::5 is:due`
- **All map-tapping skills across scopes**:
  `deck:GeoTrainer::* (tag:geotrainer::skill::locate OR tag:geotrainer::skill::place) is:due`

The subdeck names are numbered (`1 Locate`, `2 Which State`, `3 Place`) so plain
deck-order study already follows the ladder.

## Suggested pacing

- Unlock level N+1 for a scope when level N feels comfortable (say, >90% correct
  over a week) — Anki's own scheduling handles the rest.
- The three families are complementary, not redundant: Locate builds name→place,
  Which State builds place→name (and interior geography — the dot is rarely at
  the centroid), Place builds precise borders-and-neighbors intuition.

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
  the top) — and two country subdivisions, **Brazil** (27 states) and **India** (36
  states & union territories). Continents reuse Europe's machinery (viewport box +
  `CONTINENT` filter, sovereign/dependency tiering, microstate tap-circles). All
  four families on every scope: 2,420 notes total.
- **M4 follow-ups**: Argentina, Mexico, and other subdivisions need Natural Earth's
  10m admin-1 file (the 50m file only carries provinces for nine large countries —
  AUS, BRA, CAN, CHN, IDN, IND, RUS, USA, ZAF). Russia (85 subjects, antimeridian)
  and China/Indonesia subdivisions are available in 50m and are the next easy adds.
- **Later**: physical features (rivers, ranges, seas) and capitals-on-map (F8);
  Oceania once a sensible multi-viewport framing is settled.

### Adding a scope (for future me)

Continent: add an entry to `CONTINENT_SCOPES` in `scripts/build_bundle.py` (title,
lon/lat `box`, `CONTINENT` value, optional `extra_admins`/`exclude_admins`/
`name_overrides`/`tray` corner) and a `SCOPE_PACKS` entry in `build_apkg.py` (deck
root, model root, tag, fresh id bases). Country subdivision: add to
`SUBDIVISION_SCOPES` (title, ISO-3 `a3`, `noun`) + a `SCOPE_PACKS` entry. Then
`build_bundle.py && build_apkg.py`; the `scopes.spec.mjs` smoke picks it up
automatically. Never reuse a retired family id (ord 3 = neighbors).
