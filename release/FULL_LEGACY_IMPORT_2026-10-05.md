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
