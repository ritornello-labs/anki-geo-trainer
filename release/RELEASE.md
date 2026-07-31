# Release plan (M5)

Status: the initial version was submitted to AnkiWeb on 2026-07-15. The contextual
**Sketch** family and the physical-geography expansion are installed in the live
personal collection. The combined update is queued for existing shared deck
`908455862` but has not yet been uploaded.

Verification status (2026-07-31, combined update): all 23 scopes are covered by
the cross-engine suite (Chromium + WebKit): **294 passed / 12 intentional skips**.
Every one of the 34 current routes is tested in both directions.
Region scopes carry Which/Place/Sketch/Draw; rivers are Trace-the-course; mountain
ranges and deserts carry Place + Sketch; lakes carry Which + Place; tectonic plates
carry Which + Place + Sketch; ocean currents use direction-aware Trace. The Continents
scope carries Sketch + Draw for all six inhabited continent silhouettes. Combined
`geo-trainer-all.apkg` = 77 leaf decks, 2,376 notes, 44.9 MB. A disposable
Desktop Anki 25.09 run imported all 2,376 notes/cards and rendered its samples.

## Decisions

1. **Packaging: one shared deck.** Decided (Elvis, 2026-07-06) — ship a single
   `GeoTrainer` deck with every scope as a subdeck, so there's one listing and one set
   of screenshots to maintain. Built: `make apkg-all` → `dist/geo-trainer-all.apkg`
   (**77 leaf decks, 2,376 notes, 44.9 MB** — well under AnkiWeb's per-deck limit).
2. **Ship everything.** All 23 scopes are import-verified; the single deck includes them
   all. (Thin spots like Oceania capitals are just fewer cards in a subdeck, not a
   problem for a combined deck.)

## Release record

1. The repo was history/tree audited and made public on 2026-07-13.
2. The listing description was previewed and approved before the initial submission. Its three
   screenshots were captured from reviewer cards in a disposable real-Anki
   `anki-addon-workbench` profile, not a browser mock.
3. The combined 2,338-card update was installed in the daily collection through
   AnkiConnect on 2026-07-28. It added exactly 138 cards while preserving all 2,200
   prior note/card IDs, content, deck assignments, and scheduling. The active
   AnkiWeb queue now targets the existing listing `908455862`.
4. The 2,376-card follow-up was installed through AnkiConnect on 2026-07-31. It
   added 16 tectonic-plate Place cards and 22 current cards, preserved all 2,338
   original note/card IDs and scheduling, and left no temporary import tree.

## Ready artifacts

- `release/ankiweb.md` — listing copy (title, tags, support URL front-matter; body has
  the clickable full-URL GitHub link per workspace convention).
- `dist/geo-trainer-all.apkg` — the single shareable deck (`make apkg-all`).
- `release/screenshots/` — three public listing images captured from real Anki reviewer
  cards in a disposable `anki-addon-workbench` profile.
- Per-scope APKGs in `dist/` (23 packs) remain for anyone who wants just one scope.

## Before publishing (checklist)

- [x] MIT `LICENSE` added (2026-07-06); tracked-tree secret/absolute-path scan clean.
- [x] Full history/tree secret and absolute-path scan passed; GitHub repo made public (2026-07-13).
- [x] Actual Anki reviewer screenshots captured to `release/screenshots/` (2026-07-15).
- [x] Single-deck decision made; `dist/geo-trainer-all.apkg` built via `make apkg-all`.
- [x] Configure `anki-addon-release` with a git-ignored source-deck reference and
      process-boundary 1Password credentials.
- [x] Preview the rendered listing and pass the visible-clickable-GitHub-URL check.
- [x] Submit the first version; record shared id `908455862` and link it from the README.
- [x] Install and verify the 2,376-card combined update in the daily collection.
- [x] Add the update to the workspace's active AnkiWeb publication queue.
- [ ] Import the update into the isolated Publisher collection, render the proposed
      updated listing for review, and upload only after explicit approval.

## Not blocking release

- Two orphan "GeoTrainer Neighbors" note types remain in Elvis's collection from the
  F7 retirement (Tools → Manage Note Types to drop).
- Deferred content: more country subdivisions from the 10m admin-1 file.
