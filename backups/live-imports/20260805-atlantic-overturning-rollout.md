# Atlantic-overturning live rollout — 2026-08-05

The four-card AMOC cross-section package was imported into the local Anki
collection through AnkiConnect and staged directly under `Process::GeoTrainer
QA`. No AnkiWeb/cloud sync was run.

## Before

- Existing GeoTrainer notes/cards: 2,402 / 2,402
- Daily and QA deck trees were exported with scheduling before import.
- Exact note IDs, card IDs, fields, tags, models, decks, and scheduling were
  captured under `20260805T143037-0700-amoc/before/`.

## Migration

- Added four prerequisite-ordered cards to `Physical::Ocean Currents::3 Trace
  Atlantic Overturning`:

  | Order | Stable item ID | Note ID | Card ID |
  |---:|---|---:|---:|
  | 1 | `01-upper-limb` | `1785965360866` | `1785965360867` |
  | 2 | `02-sinking-limb` | `1785965360868` | `1785965360869` |
  | 3 | `03-deep-return-limb` | `1785965360870` | `1785965360871` |
  | 4 | `04-complete-pathway` | `1785965360872` | `1785965360873` |

- The temporary generated `GeoTrainer` root was verified empty before its deck
  shells were removed.
- The destination is `Process::GeoTrainer QA::Physical::Ocean Currents::3 Trace
  Atlantic Overturning` until manual QA is complete.

## Verification

- Final GeoTrainer notes/cards: 2,406 / 2,406
- New notes/cards: 4 / 4 in the intended QA leaf deck
- Changed existing notes: 0
- Changed existing scheduling records: 0
- Filtered-deck collisions: 0
- Browser QA: 334 passed / 12 intentional skips across Chromium and WebKit.
- The local disposable-Anki environment failed while installing Anki inside its
  container, before import or rendering; hosted disposable Desktop run
  `9296308a3369` remained queued. Manual review in the installed Anki client is
  therefore the final rendering gate.
- Exact machine-readable verification:
  `20260805T143037-0700-amoc/verification.json`
- No sync was run.
