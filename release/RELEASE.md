# Release plan (M5)

## Current publication pass — October 5, 2026

**All fifteen components submitted; full edition awaits legacy-upgrade decision and batch review.**
The latest Indonesian Provinces pack is 38 provinces / 151 cards at `1473740061`;
its four approved native GIFs and exact delivered APKG are archived with the other
October 5 components on `v2026.10.05`. Owner metadata/source name and delivered
content/identities are verified; public review is pending. Observed deck quota
18/20, no rejection; reset unknown. The website gallery/release links are committed
and locally verified; deployment awaits GitHub Actions runner recovery. The listing
uses byte-identical approved GIFs at immutable GitHub URLs during that incident.

Fresh component/full overlap checks pass, but the actual July public full release
fails both standard and merge-note-types imports. Do not publish the current full
candidate. See [legacy import gate](FULL_LEGACY_IMPORT_2026-10-05.md). Exact original
share/source name `GeoTrainer` verified for `908455862`. No personal collection
mutation/import/sync is authorized. Continue scope, source/map correctness, and
semantic update checks for every subsequent item, as Elvis requested.

The eight physical-systems QA scopes and foundations remain excluded. Surface ocean currents are also withheld pending retirement reconciliation. The September 29 Geo Concepts approval record includes 1,573 cards in a separate source project; Elvis confirmed all accepted families are included; source repository separation is not a release exclusion. Most of the old flow deck was discarded. See SCOPE_RECONCILIATION_2026-10-03.md.

Elvis approved 908455862 as the eventual full edition, retaining its exact original share name `GeoTrainer` (verified October 5). Each component will link to that listing with an update-pending note; the final full listing will link back to every shipped component. Real-Anki demos are selected by distinct learning experience, including membership taps, reference-line globe placement and UTC conversion where relevant.

## Historical release records (superseded scope)

Status: the initial version was submitted to AnkiWeb on 2026-07-15. The contextual
**Sketch** family and the physical-geography expansion are installed in the live
personal collection. The combined update is queued for existing shared deck
`908455862` but has not yet been uploaded. The 29-card atmospheric, seasonal, ENSO,
and Atlantic-overturning batch is temporarily staged under `Process::GeoTrainer QA`
for manual review in that historical build. Exclude these QA scopes from every
current public component and the full edition.

Verification status (2026-09-22, combined update): all 32 scopes are covered by
the cross-engine suite (Chromium + WebKit): **362 passed / 26 intentional skips**.
Every one of the 34 current routes is tested in both directions.
Region scopes carry Which/Place/Sketch/Draw; rivers are Trace-the-course; mountain
ranges and deserts carry Place + Sketch; lakes carry Which + Place; tectonic plates
carry Which + Place + Sketch; ocean currents use direction-aware Trace; atmospheric
circulation has dedicated paired-cell, pressure-belt, prevailing-wind, jet, and seasonal
monsoon interactions; Atlantic overturning uses latitude–depth direction and sequence
drills; ENSO uses coupled plan/depth state comparisons. The Continents
scope carries Sketch + Draw for all six inhabited continent silhouettes. Combined
`geo-trainer-all.apkg` = 86 leaf decks, 2,472 notes, 63.6 MB. The guarded live
AnkiConnect rollout installed the redesign successfully; manual visual
review in the installed client remains pending.

## Decisions

1. **Packaging: one shared deck — superseded 2026-09-30.** Elvis: GeoTrainer
   "grew way too big"; split it into modular decks, and consider also shipping a
   full edition with everything. Not designed yet: the pack map, whether listing
   `908455862` becomes the full edition, and per-pack listings, screenshots and
   GitHub releases are open. Every scope already has its own deterministic model,
   deck and GUID space and builds its own APKG, so packs and the full edition can
   share note types and notes (installing both updates in place, no duplicates).
   Decided 2026-09-30 (Elvis): packs are World countries; one pack per country
   for Country subdivisions; Physical geography; Plate tectonics; Reference lines
   & time; **Islands & archipelagos** (not "Globe placement"); plus the full
   edition. Elvis ships it and updates ritornello.dev and AnkiWeb himself.
   The original decision, for the record: (Elvis, 2026-07-06) — ship a single
   `GeoTrainer` deck with every scope as a subdeck, so there's one listing and one set
   of screenshots to maintain. Built: `make apkg-all` → `dist/geo-trainer-all.apkg`
   (**86 leaf decks, 2,472 notes, 63.6 MB** — well under AnkiWeb's per-deck limit).
2. **Accepted families only (2026-09-30).** Exclude retired flows/currents, physical-systems QA and foundations from all current public packs and the full edition. Include all accepted Geo Concepts families. PACKS.md and the per-pack records describe the accepted scope.

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
8. On 2026-09-22, the learner-approved 67-card globe-placement family graduated from
   `anki-island-globe` into `GeoTrainer::World::Islands`. Its stable note/card identity
   and scheduling were preserved; the eight untouched Antipodes cards were retired.

## Queued enclave visibility fix (2026-09-22)

Include the enclave fix in the next update to shared deck `908455862`; **do not
upload yet**. The shared package has been rebuilt with all 2,405 notes and 85 leaf
decks. It preserves interior polygon holes through projection/export, uses matching
even-odd fill and hit testing, and keeps small-region markers and answer highlights
above surrounding regions. This fixes the invisible Adygey answer and the same
occlusion class elsewhere. The existing 29-card manual-QA/Publisher prerequisites
above remain in force. See `release/ENCLAVE_FIX_2026-09-22.md` for verification.

## Ready artifacts

- `release/ankiweb.md` — listing copy (title, tags, support URL front-matter; body has
  the clickable full-URL GitHub link per workspace convention).
- `dist/geo-trainer-all.apkg` — the single shareable deck (`make apkg-all`).
- `release/screenshots/` — three public listing images captured from real Anki reviewer
  cards in a disposable `anki-addon-workbench` profile.
- Per-scope APKGs in `dist/` (32 packs) remain for anyone who wants just one scope.

## Before publishing (checklist)

Every upload also requires the exact-byte gate in [PUBLICATION_PROCESS.md](PUBLICATION_PROCESS.md). Recheck any Publisher-exported package; a source-build receipt cannot attest to different bytes.

- [x] MIT `LICENSE` added (2026-07-06); tracked-tree secret/absolute-path scan clean.
- [x] Full history/tree secret and absolute-path scan passed; GitHub repo made public (2026-07-13).
- [x] Actual Anki reviewer screenshots captured to `release/screenshots/` (2026-07-15).
- [x] Single-deck decision made; `dist/geo-trainer-all.apkg` built via `make apkg-all`.
- [x] Configure `anki-addon-release` with a git-ignored source-deck reference and
      process-boundary 1Password credentials.
- [x] Preview the rendered listing and pass the visible-clickable-GitHub-URL check.
- [x] Submit the first version; record shared id `908455862` and link it from the README.
- [x] Install and verify the 2,405-card combined update in the local collection.
- [x] Add the update to the workspace's active AnkiWeb publication queue.
- [x] Delete the two orphan `GeoTrainer Neighbors` note types left by the F7
      retirement. Verified absent from the live collection on 2026-08-05; a
      fresh backup preceded the successful full sync, and the pending-change
      counts were zero afterward.
- [ ] Import the update into the isolated Publisher collection, render the proposed
      updated listing for review, and upload only after explicit approval.

## Not blocking release

- Additional country subdivisions are intentionally outside the core release. Build
  them as optional expansion packs only if demand appears.

### October 5: legacy transition prototype and full preview

Ordinary July-release imports still fail. The disposable GUID-aware transition
passes with old identities/history preserved, all 3,007 current notes exact, no
duplicates, 92 older retired cards retained, and all fifteen component reimports.
A partial World Countries installation also passes. Older users necessarily move
to current model IDs; decision and a supported user-facing upgrade are pending.
The held complete full-edition listing now has ten native GIFs and reciprocal
component links, ready for fresh batch review. No full submission/staging.
See `FULL_LEGACY_IMPORT_2026-10-05.md` and its pinned QA/review receipts.

October 5: Elvis approved the full-edition ten-GIF image batch. The static contact
sheet is review-only. Legacy model-ID exception and supported upgrade remain
pending; no full submission/staging. Preserve the approved GIF hashes.
