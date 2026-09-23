# Enclave visibility repair — 2026-09-22

Status: installed in the personal collection; rebuilt for shared deck `908455862`
and queued for its next update. No AnkiWeb upload, release artifact publication,
Publisher import, or collection sync was performed.

## Cause and correction

The Adygey Place answer existed and had the orange answer class, but the later
Krasnodar path painted over it. The builder also discarded interior polygon rings.
Magnified enclave markers can extend beyond a true hole, so preserving holes alone
is insufficient.

- Preserve interior rings through map projection, antimeridian unwrapping, and
  simplified bundle export. Seventeen map bundles changed; note selection and
  standalone Draw shapes are unchanged.
- Use even-odd SVG fill and matching region hit testing.
- Layer small markers above neutral host regions, and raise each answer above all
  neutral regions for Place, Which, Sketch, Locate, and capital-location answers.
- Keep legacy live templates' unrelated code, CSS, fields, and family metadata.
  No note type schema changes, imports, card additions, deletions, or moves.

## Verification

- Python topology regressions: **2 passed** (projection/export and dateline holes).
- Current public suite: Chromium **173 passed, 13 skipped**; WebKit
  **173 passed, 13 skipped** (346 passed total). The 26 skips comprise 14 optional
  bloc-fixture tests without their external fixture and 12 inapplicable scope/family
  tests. Tests check actual SVG hit targets
  and answer colors for Adygey, Vatican City, and Lesotho, transparent holes,
  location grading inside a hole, and legacy assets without holes.
- All **130 sides across 65 planned live templates** rendered without JavaScript
  errors. The Adygey Place marker was topmost at its intended location.
- The combined package imported successfully into a disposable Anki 25.09.4
  collection: **2,405 notes / 2,405 cards**. Its Adygey Place question and answer
  rendered through Anki's backend with the repaired template.
- The additional offscreen Qt GUI workbench run exited with signal 11 before
  producing a smoke result. No desktop visual-smoke pass is claimed. Docker had
  no prepared Anki image, and no Android emulator was connected. Remote QA was
  not run: automatic approval review rejected the cloud deck upload.
- Live AnkiConnect update completed: **65 models / 1,766 cards**. Every template
  read back exactly as planned; CSS and field schemas were unchanged. Exact
  note/card memberships, card scheduling, deck assignments, and note-field hashes
  matched before/after. Collection-wide note/card counts were unchanged.
- A later optional extra card read found AnkiConnect unavailable, after the full
  live readback and scheduling verification had already completed successfully.

## Local evidence and recovery

The timestamped `backups/live-imports/20260922T220834-0700-enclave-repair/`
contains the exact before/after template plan, CSS/field schemas and identities,
compact before/after card state, and verification. These are private local recovery
files, excluded from Git. To undo, restore only each planned model's `before`
templates through AnkiConnect and verify readback; do not reimport the deck.
Earlier import/migration checkpoints remain protected recovery records.

The repair script defaults to a read-only plan. Its `--apply` path checks for stale
state before writing and refuses unknown source bundles/functions.

## Source history

Publish only this change on top of the sanitized public history (`d780e76`).
The original local checkout still has pre-sanitization ancestry and unrelated
working-tree changes; do not push or merge that ancestry back to GitHub. The
public repair script uses the equivalent sanitized source baseline `a9aa540`.
The public engine, generator, and all bundle bytes match the validated local build.

## Upload queue

`dist/geo-trainer-all.apkg`: **85 leaf decks / 2,405 notes/cards**.
SHA-256: `c2b3add80661af13100297a615ca244eec7ee7eae599ae1eb5ea51b86b06ddd0`.

Keep this fix in the existing publication queue. The 29-card physical-systems
manual-QA/restoration prerequisite remains unchanged. When publication is approved,
rebuild the Publisher export, retain this fix, and attach the identical submitted
artifact to the corresponding GitHub release. **Do not upload this package yet.**
