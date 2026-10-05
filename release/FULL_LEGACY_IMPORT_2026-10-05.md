# Full-edition legacy update gate — October 5, 2026

**Do not submit the current full candidate.** Fresh component/full/component
imports pass, but importing over the actual July AnkiWeb release does not update
its existing notes correctly. This is a different compatibility boundary.

The original share/source name for listing `908455862` is exactly `GeoTrainer`.
The actual current download contains 1,716 notes/cards and 52 models. The current
unpublished full candidate contains 3,007 notes / 4,232 cards / 106 models. It
combines all accepted concept families and the fifteen shipped components;
physical-system QA/foundations/retired flow content remain excluded.

Native Anki 25.09, disposable collections, no personal collection access:

| Import path | Result | Failure |
|---|---|---|
| Merge note types enabled | 3,099 notes / 7,014 cards | Old and new family templates merge and create extra cards; only 180 old notes retain their model IDs. |
| Standard import, merge disabled | 3,099 notes / 4,324 cards | All 1,624 accepted legacy notes keep stale fields/templates; none receives the current fields or templates. All old card IDs remain, but this is not a successful update. |

1,536 overlapping GUIDs now point at different source model IDs. Legacy family
slots and current family slots collide (e.g. old Which/Place/Draw versus current
Point/Place/Draw/Sketch). An unchanged GUID alone does not guarantee a native
update when the note-type identity/schema changes. Ninety-two legacy cards in
retired range/desert task families are absent from the candidate; a public import
does not delete those cards automatically. Do not claim retirement happened in
an installed collection.

## Required next work

Design and verify a GUID-aware upgrade that preserves existing note/card identity
and study state, reconciles legacy/current model schemas without extra templates,
and also passes current delivered component → full → component tests. Do not
silently remap the full edition into a different identity space from the shipped
components. Use native Anki APIs in disposable QA and isolated Publisher only.
Record exact old/new family mappings and explicit treatment of retired tasks.

Reproduce against an actual download from `908455862`, not the live personal
collection or a fresh generated pack. Raw disposable test scripts/results are
in the publication workspace's `full-edition-qa` directory; summary counts and
artifact digest are in [the JSON receipt](FULL_LEGACY_IMPORT_2026-10-05.json).
A successful test must check semantic field values, templates/CSS, note/card IDs,
scheduling, expected new-card count, and zero duplicate GUIDs in both import
orders. Then prepare one complete native-GIF listing batch for review, preserve
the source name `GeoTrainer`, publish through the release tool, and archive the
actual delivered bytes. No full-edition image approval or submission is recorded.

## GUID-aware prototype verified — October 5

A native-API transition now passes in disposable Anki 25.09 against the actual
July public download. This is **QA proof only**, not a supported upgrader for an
installed collection; the full-edition update is still held.

- All 1,624 accepted legacy notes receive the current semantic fields, templates
  and CSS; all 3,007 current notes have the correct canonical model IDs and fields.
- All 1,716 old note/card identities, native deck assignments and study state
  remain unchanged. Seven real native test reviews and their exact revlog records
  survive the upgrade and all fifteen delivered-component imports.
- Result: 3,099 notes / 4,324 cards = 4,232 current cards + 92 retained retired
  cards. Zero duplicate GUIDs, zero extra merged templates. The public update
  does not delete the older range/desert task cards.
- A second migration does no work. Every delivered component can subsequently
  import without adding duplicate cards or changing existing study state.
- A separate mixed-install test also passes: July download → delivered World
  Countries component (ordinary non-merge import) → GUID-aware transition → full
  → all fifteen delivered components. This verifies a realistic partially
  upgraded installation as well as a July-only installation.

The necessary exception is **legacy note-type identity**: legacy slots were
renumbered for different games by an earlier redesign. The prototype preserves
note/card GUIDs/IDs and history, but migrates legacy notes to the already-shipped
canonical model IDs. It temporarily preserves conflicting old types, clears only
empty conflicting slots through native APIs, imports the canonical package,
then changes the matching legacy notes by GUID with explicit field/template maps.
Never remap the current components or silently force legacy model merging.

Elvis was asked to choose whether to prepare a one-time desktop upgrade for
older users while retaining `908455862`, or keep the full edition held and
continue the other publication queue. This decision is required because the
original instruction explicitly required unchanged model IDs. It does not
request or authorize any change to the personal collection.

The ten-GIF full-edition batch now uses previously approved native component
captures: nine GIFs are byte-identical; the static concept GIF changes delay
metadata only to the approved 2-second front / 3-second answer pattern, with every
native frame pixel and all other bytes preserved. `release/FULL_EDITION_REVIEW_2026-10-05.json` pins their
hashes; the complete held draft is in `release/ankiweb.md`. It includes membership,
reference-line globe placement and UTC/date conversion, excludes retired flows,
and links all fifteen submitted components. This new complete listing batch
was approved by Elvis on October 5 (Looks fine to me; GIFs confirmed). The
contact sheet is review-only; the public listing uses all ten animated GIFs.
Legacy model-ID decision and supported upgrade remain pending. No full submission
or Publisher staging has occurred.

Reproduction with Anki 25.09's Python interpreter:

```sh
python scripts/test_legacy_guid_upgrade.py \
  --legacy-apkg /path/to/actual-july-download.apkg \
  --current-apkg /path/to/geo-trainer-all.apkg \
  --components-dir /path/to/fifteen-delivered-apkgs \
  --receipt /tmp/geotrainer-guid-upgrade.json
```

Add `--preimport-component /path/to/fifteen-delivered-apkgs/geo-trainer-world-countries.apkg`
to reproduce the mixed-install case. The script accepts APKG inputs and creates
only temporary collections; it cannot open an existing personal/Publisher
collection. The exact fixture digest is enforced. Summary receipts:
`FULL_GUID_UPGRADE_PROTOTYPE_2026-10-05.json` and
`FULL_GUID_UPGRADE_PARTIAL_2026-10-05.json`.

Before submission, turn the prototype into a reviewed user-facing upgrade with
backup, preflight, clear treatment of legacy cards, recovery and full-sync guidance;
verify it in disposable Anki and prepare final instructions. It must never choose
a user's sync direction automatically. Complete the listing review, stage only
isolated Publisher, and archive the actual delivered full-edition bytes.
