# Plate Place and expanded-current live rollout — 2026-07-31

The verified combined `dist/geo-trainer-all.apkg` was imported into the daily
Anki collection through AnkiConnect. This was a local collection update; no
AnkiWeb/cloud sync was run.

## Before

- Root: `Decks::Geography::GeoTrainer`
- Notes/cards: 2,338 / 2,338
- Exact note IDs, card IDs, fields, tags, deck assignments, and scheduling were
  captured under `20260731T153402-0700-before/`.
- A scheduled rollback package was exported as
  `20260731T153402-0700-before/geotrainer-before.apkg`. APKG files are ignored
  by Git, so this remains a local backup.

## Migration

- Added 16 `Tectonic Plates::2 Place` notes/cards.
- Expanded `Ocean Currents::1 Trace` from 12 to 34 notes/cards, adding 22.
- Five existing current notes were updated in place to improve or disambiguate
  their study route: Gulf Stream, Canary, Agulhas, West Australian, and the
  now explicitly Atlantic North Equatorial Current.
- Existing current IDs were deliberately retained through stable route keys.
- The imported top-level `GeoTrainer` cards were moved into the existing nested
  tree. An initial empty-deck cleanup call used Anki's obsolete
  `cardsToo=false` form and was rejected without deleting anything; after a
  zero-card assertion, the empty shells were removed with the required flag.

## Verification

- Final notes/cards: 2,376 / 2,376
- New notes/cards: 38 / 38 in the two intended leaf decks
- Top-level stray `GeoTrainer` cards/decks: 0 / 0
- Missing original note/card IDs: 0 / 0
- Changed original scheduling records: 0
- Original content changes outside the five intended current notes: 0
- Verification snapshot/report:
  `20260731T153655-0700-after/verification.json`
- No cloud sync was run; the requested scope was the local collection.
