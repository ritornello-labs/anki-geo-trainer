# anki-geo-trainer

Sheppard-Software-style interactive geography practice for Anki: a comprehensive,
curriculum-ordered set of map-interaction task types (click-to-locate, point-in-region,
place-the-piece, draw-the-shape, tap-all-neighbors, …) rendered by a shared JS engine
that works on Anki Desktop, AnkiMobile, and AnkiDroid.

Status: planning. See [`PLAN.md`](./PLAN.md) for the task catalog, architecture,
constraints, and milestones.

## Why

Anki's geography ecosystem (including this workspace's own shared decks) covers passive
recall well: highlighted region → name, silhouette → name, capital → country. Sites like
[Sheppard Software](https://www.sheppardsoftware.com/) show that the higher rungs of the
skill ladder are *active*: find the region on a blank map, judge which region contains a
random point, place a floating shape, draw the outline yourself. This project builds that
ladder as Anki decks — self-gradable, beautiful, cross-platform, and tagged so students
can assemble their own curricula.

## Layout (planned)

- `PLAN.md` — the plan of record
- `curriculum/` — ordering, tags, and track definitions
- `engine/` — TypeScript interaction engine (bundled and inlined into card templates)
- `data/` — Natural Earth sources and entity registries
- `scripts/` — Python build pipeline (geometry packing, note generation, APKG build)
- `anki/` — note types: templates and shared CSS
- `tests/` — Playwright (Chromium + WebKit) card tests and workbench smoke configs
