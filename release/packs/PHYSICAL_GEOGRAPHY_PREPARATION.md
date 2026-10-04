# Physical Geography release preparation — October 4

Status: **complete listing and five real-Anki GIFs await Elvis's image approval**.
No Physical Geography image has been uploaded; no Publisher staging or submission
has occurred. Personal Anki has not been accessed or changed.

## Accepted content and verification

- 404 notes / 963 cards: 250 map-game notes/cards across rivers, ranges, deserts,
  lakes, plateaus/basins, plains/grasslands and peninsulas; 154 concept notes / 713
  cards across ten accepted semantic families. 23 models and 23 leaf decks.
- Public export root: `GeoTrainer::Physical Geography`. Geometry leaf IDs retain
  the scope definitions; concept IDs are frozen from the original family APKGs.
  Public names are assigned without deriving new IDs. Model IDs and GUIDs retain
  their established generator definitions.
- 223 media files present. Native Anki 25.09 import and native export retain every
  file byte-for-byte; no missing media. The 21 missing Köppen rasters were restored
  from the recorded CC BY 4.0 upstream SVGs, with the accepted crop/polar treatment.
  Filenames and card fields did not change. Provenance and credits are committed.
- Native component → corrected full candidate → component imports preserve
  note/model/card/leaf IDs and create zero duplicates. The candidate is the exact
  source union: 2,987 notes / 4,212 cards, with retired currents/QA scopes excluded.
- The four actual delivered components (U.S., Brazil, China, Reference Lines &
  Time) also retain all 488 notes / 510 cards, fields and identities through the
  corrected full candidate and repeated delivered-package imports.
- The public source rebuild matches the reviewed component's GUIDs, models,
  fields, templates, CSS, deck IDs/names and all media bytes.

## Reviewed image batch

`PHYSICAL_GEOGRAPHY_REVIEW.json` records the immutable image hashes, frame counts
and native capture origin. Five examples: zoom/pan/trace the Amazon; place Sahara;
zoom/pan/sketch the Tibetan Plateau; recall tropical moist forest vegetation with
credited photographs; identify the Af climate distribution. Pointer input and
Anki's ordinary answer reveal generated the captures; no Anki grades were recorded.
Noto Emoji (OFL 1.1) was installed only in the disposable capture environment so
the original pan control rendered correctly. Templates were not altered for capture.

Preview is generated locally in the website worktree's ignored review directory.
Source listing: `physical-geography.md`; release configuration:
`physical-geography.toml`. The original brand banner, gallery link, visible GitHub
URL, full-edition update-pending link and stable support page are included.

## Resume after image approval

1. Confirm the approved hashes, then deploy those exact GIFs and reduced-motion
   posters to the versioned website media path. Keep listing copy and Git commits
   signed/pushed before submission.
2. Back up the complete isolated Publisher collection and media. Record a full-sync
   ledger row before any Publisher schema change. Read existing scope membership;
   reconcile only this pack's exclusive models/notes/leaves against its source.
   Preserve and hash-verify all outside-scope content, including held current/QA
   content. Do not operate the personal profile.
3. Import the component with native Anki APIs, verify exact GUIDs/fields/models/cards/
   leaf IDs and all 223 media bytes. Register only its Publisher parent ID in the
   ignored `.env`, under `ANKIWEB_SOURCE_DECK_ID_PHYSICAL_GEOGRAPHY`.
4. Complete the already authorized isolated-Publisher **Upload** direction if
   required; then require normal/final sync `required: 0` and native integrity/content
   checks before closing the ledger row. No new Upload approval is needed.
5. Use the anki-release skill wrapper with `--config release/packs/physical-geography.toml`
   and `op run --env-file=.env` at the process boundary. Preflight first; publish with
   `--submit --confirm-copyright` only after this image batch is approved.
6. Owner-verify the listing title/counts/images/support. Download the actual delivered
   APKG through the authenticated publishing workflow; compare native content and
   media against the export. Attach that exact delivered byte stream to the tagged
   GitHub release and verify its digest/size. Preserve existing component assets.
7. Add the listing, latest release/download links and approved five-demo gallery to
   ritornello.dev; deploy and verify. Update component links, project status and the
   root publish queue. Record observed quota; stop cleanly only on an actual limit.

Do not resubmit the four shipped components. Remaining broad components need their
own source/license checks and fresh approved visual batches. The full edition ships
last and must retain listing 908455862's exact original share name.
