# Release plan (M5)

Status (2026-09-24): the initial version is on AnkiWeb at listing `908455862`.
No follow-up has been uploaded. The 29 older physical-system cards and seven
foundations-pilot cards are QA-only in `Process`; do not restore them to the
daily GeoTrainer tree or include them in a Publisher export without acceptance.
AMOC is out of the general-geography core, and the old four-card ENSO deck is
superseded by a smaller candidate still awaiting Elvis's QA.

The current `qa/physical-systems-redesign-pilot` branch builds an accepted-scope
combined candidate with **77 leaf decks / 2,376 notes**. All nine unaccepted
physical QA scopes are excluded. The full Chromium/WebKit suite passes
**374 tests / 12 intentional skips**, and package inspection confirms no QA
note type or `Process` deck in the combined APKG. This is a branch-local
candidate, not a publication approval; reconcile other pending source branches,
the live collection, Publisher rendering, and the listing before any upload.

## Decisions

1. **Packaging: one shared deck.** Decided (Elvis, 2026-07-06) — ship a single
   `GeoTrainer` deck with accepted scopes as subdecks, so there's one listing and one
   set of screenshots to maintain. Current branch candidate: `make apkg-all` →
   `dist/geo-trainer-all.apkg` (**77 leaf decks, 2,376 notes**).
2. **Release gate.** Source generation is not acceptance. Keep every QA-only scope
   out of the combined deck until its content and interaction have been approved;
   the former “ship everything” decision is superseded.

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
5. The 2,402-card atmospheric/seasonal follow-up was installed through AnkiConnect
   on 2026-07-31. It added exactly 26 cards across six new note types, preserved
   all 2,376 original note/card IDs, content, and scheduling, and left no temporary
   import tree. The AnkiWeb queue now targets this artifact.
6. The 2,406-card Atlantic-overturning follow-up added four prerequisite-ordered
   latitude–depth traces directly to the manual-QA tree. It preserved all 2,402
   existing notes, cards, deck assignments, and scheduling.
7. The 2026-08-06 redesign replaced the six unreviewed cell cards with three paired
   hemisphere cards, replaced the four unreviewed AMOC traces with two direction/
   sequence cards, added four ENSO state cards, and updated pressure/wind/monsoon
   interactions. The final collection has 2,405 GeoTrainer cards, 29 of them in the
   QA tree. Scheduling on all 2,396 retained cards was unchanged; no sync ran.

## Ready artifacts

- `release/ankiweb.md` — listing copy (title, tags, support URL front-matter; body has
  the clickable full-URL GitHub link per workspace convention).
- `dist/geo-trainer-all.apkg` — branch-local accepted-scope candidate
  (`make apkg-all`); rebuild after branch reconciliation, not a ready upload.
- `release/screenshots/` — three public listing images captured from real Anki reviewer
  cards in a disposable `anki-addon-workbench` profile.
- Per-scope APKGs in `dist/` include QA-only packs for testing; do not publish
  those packs as accepted geography content.

## Before publishing (checklist)

- [x] MIT `LICENSE` added (2026-07-06); tracked-tree secret/absolute-path scan clean.
- [x] Full history/tree secret and absolute-path scan passed; GitHub repo made public (2026-07-13).
- [x] Actual Anki reviewer screenshots captured to `release/screenshots/` (2026-07-15).
- [x] Single-deck decision made; `dist/geo-trainer-all.apkg` built via `make apkg-all`.
- [x] Configure `anki-addon-release` with a git-ignored source-deck reference and
      process-boundary 1Password credentials.
- [x] Preview the rendered listing and pass the visible-clickable-GitHub-URL check.
- [x] Submit the first version; record shared id `908455862` and link it from the README.
- [x] Install and verify the historical 2,405-card source expansion in the local
      collection; later QA decisions supersede that package for publication.
- [x] Add the historical update to the workspace's AnkiWeb publication queue;
      its old 2,405-note artifact is superseded and must be replaced before upload.
- [x] Delete the two orphan `GeoTrainer Neighbors` note types left by the F7
      retirement. Verified absent from the live collection on 2026-08-05; a
      fresh backup preceded the successful full sync, and the pending-change
      counts were zero afterward.
- [ ] Reconcile source branches and build the exact accepted-scope release artifact.
- [ ] Import that artifact into the isolated Publisher collection, render the proposed
      updated listing for review, and upload only after explicit approval.

## Not blocking release

- Additional country subdivisions are intentionally outside the core release. Build
  them as optional expansion packs only if demand appears.
