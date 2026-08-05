# Atmospheric-circulation manual-QA staging — 2026-08-05

The exact 26-card atmospheric and season-aware batch was moved through
AnkiConnect from `Decks::Geography::GeoTrainer` to
`Process::GeoTrainer QA`. No cloud sync was run.

## Membership

- Atmospheric Circulation `1 Trace Cells`: 6
- Atmospheric Circulation `2 Place Pressure Belts`: 4
- Atmospheric Circulation `3 Trace Prevailing Winds`: 6
- Atmospheric Circulation `4 Trace Jet Streams`: 4
- Atmospheric Circulation `5 Trace Seasonal Monsoon Winds`: 2
- Ocean Currents `2 Trace Seasonal Monsoon Currents`: 4

Membership was resolved from the six durable `geotrainer::scope::…` tags plus
`ai-created`, not from a broad deck query. The audit found 26 unique notes and
26 unique cards, with no duplicate membership or filtered-deck capture.

## Verification

- Note/card identities preserved: 26 / 26
- Note fields, tags, and note types changed: 0
- Scheduling fields changed: 0
- Filtered-deck collisions: 0
- Full local before/after state:
  `20260805T134025-0700-stage/` (state JSON is intentionally Git-ignored)
- Concise machine-readable result:
  `20260805T134025-0700-stage/verification.json`

## Restore after manual QA

With local Anki and AnkiConnect running:

```bash
.venv/bin/python scripts/stage_live_qa.py --audit-restore
.venv/bin/python scripts/stage_live_qa.py --restore
```

The first command is read-only. The restore command takes a fresh snapshot,
moves the same tag-defined 26 cards back to their original six leaf decks, and
requires exact identity/content/scheduling preservation before reporting success.
