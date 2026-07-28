# Physical-geography live rollout — 2026-07-28

The verified combined `dist/geo-trainer-all.apkg` was imported into the daily
Anki collection through AnkiConnect. This was a local collection update; no
AnkiWeb/cloud sync was run.

## Before

- Root: `Decks::Geography::GeoTrainer`
- Notes/cards: 2,200 / 2,200
- Exact note IDs, card IDs, fields, tags, model names, deck assignments, and
  scheduling were captured under `20260728T153543-0700-before/`.
- A scheduled rollback package was exported as
  `20260728T153543-0700-before/geotrainer-before.apkg`. APKG files are ignored
  by Git, so this remains a local backup.

## Migration

- Import added 138 new notes/cards without duplicating any prior notes.
- The new cards were moved from the temporary top-level `GeoTrainer` tree into
  the existing nested tree:

  - Mountain Ranges `3 Sketch`: 29
  - Deserts `3 Sketch`: 17
  - Lakes `1 Which Lake`: 24
  - Lakes `2 Place`: 24
  - Tectonic Plates `1 Which Tectonic Plate`: 16
  - Tectonic Plates `3 Sketch`: 16
  - Ocean Currents `1 Trace`: 12

- The temporary top-level tree was verified card-free before its deck shells
  were deleted.

## Verification

- Final notes/cards: 2,338 / 2,338
- New notes/cards: 138 / 138 in the seven intended leaf decks
- Top-level stray `GeoTrainer` cards/decks: 0 / 0
- All 2,200 original note IDs, card IDs, fields, tags, model names, and deck
  assignments are unchanged.
- All scheduling fields on the 2,200 original cards are byte-for-byte
  equivalent in the normalized before/after snapshots.
- The package deliberately refreshed rendered question/answer HTML and CSS on
  576 existing cards whose note types use the shared engine; their content,
  identity, deck assignment, and scheduling did not change.
- No cloud sync was run; the requested scope was the local collection.

The AnkiWeb update for existing shared deck `908455862` is now recorded in the
workspace publication queue. Uploading through the isolated Publisher profile
remains a separate release step.
