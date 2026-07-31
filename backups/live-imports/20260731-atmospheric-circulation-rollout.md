# Atmospheric-circulation live rollout — 2026-07-31

The verified combined `dist/geo-trainer-all.apkg` was imported into the daily
Anki collection through AnkiConnect. This was a local collection update; no
AnkiWeb/cloud sync was run.

## Before

- Root: `Decks::Geography::GeoTrainer`
- Notes/cards: 2,376 / 2,376
- Exact note IDs, card IDs, fields, tags, model names, deck assignments, and
  scheduling were captured under `20260731T163538-0700-before/`.
- A scheduled rollback package was exported as
  `20260731T163538-0700-before/geotrainer-before.apkg`. APKG files are ignored
  by Git, so this remains a local backup.

## Migration

- Import added 26 new notes/cards without duplicating any prior notes.
- Every new note carries the `ai-created` tag.
- The new cards were moved from the temporary top-level `GeoTrainer` tree into
  the existing nested tree:

  - Atmospheric Circulation `1 Trace Cells`: 6
  - Atmospheric Circulation `2 Place Pressure Belts`: 4
  - Atmospheric Circulation `3 Trace Prevailing Winds`: 6
  - Atmospheric Circulation `4 Trace Jet Streams`: 4
  - Atmospheric Circulation `5 Trace Seasonal Monsoon Winds`: 2
  - Ocean Currents `2 Trace Seasonal Monsoon Currents`: 4

- The temporary top-level tree was verified card-free before its deck shells
  were deleted.

## Verification

- Final notes/cards: 2,402 / 2,402
- New notes/cards: 26 / 26 in the six intended leaf decks
- Top-level stray `GeoTrainer` cards/decks: 0 / 0
- All 2,376 original note IDs, card IDs, fields, tags, model names, and deck
  assignments are unchanged.
- All scheduling fields on the 2,376 original cards are equivalent in the
  normalized before/after snapshots.
- Browser QA: 318 passed / 12 intentional skips across Chromium and WebKit,
  including exact inlined-template tests for all six new note types.
- Disposable Desktop Anki imported all 2,402 notes/cards and rendered its samples.
- No cloud sync was run; the requested scope was the local collection.

The AnkiWeb update for existing shared deck `908455862` now points at the
2,402-card artifact in the workspace publication queue. Importing it into the
isolated Publisher profile, rendering the revised listing for review, and upload
remain separate release steps.
