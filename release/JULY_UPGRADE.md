# Upgrading GeoTrainer's July 2026 edition

New users and users of the current focused components can import the full APKG normally, with **Merge note types disabled**. This one-time helper is for installations of the July deck from AnkiWeb listing 908455862. It is distributed in the [October 5 GitHub release](https://github.com/ritornello-labs/anki-geo-trainer/releases/tag/v2026.10.05) as `geo-trainer-july-upgrade.ankiaddon`.

The helper requires Anki Desktop 25.09 or newer; native integration testing uses 25.09. It uses native package import, note-type changes and synchronous backup APIs, including import options that preserve existing deck settings. Mobile users should perform this upgrade on desktop and then sync deliberately. The add-on is a release-file install and does not auto-update.

## Before starting

1. Sync all devices so this desktop has your latest cards and reviews. Close Anki on other devices until the upgrade is checked. If you already have an unresolved full-sync conflict, resolve the source of truth first; do not guess a direction.
2. Export a complete collection backup with scheduling and media through **File → Export** and keep it safe. This extra backup protects against interruptions outside the helper, including disk failure.
3. Download the full-edition APKG and `geo-trainer-july-upgrade.ankiaddon` from the same October 5 release. **Do not first import the APKG over the July edition.** Install the helper through Tools → Add-ons → Install from file, then restart Anki.
4. Choose **Tools → GeoTrainer: upgrade July edition…**, select that APKG, read the confirmation and proceed.

The helper first validates the package and checks your existing GeoTrainer fields and templates. Customized/unrecognized content, unrelated notes using a required note type, duplicate GUIDs or unsupported schemas stop the upgrade before collection changes. Keep your edits and request a manual migration instead of deleting the conflicting notes.

Before changing anything, it creates a fresh native collection backup and saves existing media that the package might replace. It refuses to continue if backup creation fails. Recovery files stay in your profile's `geotrainer-upgrade-recovery` directory and contain private collection data; do not post them in a public issue.

## What changes

Existing accepted July notes move to the current note-type IDs and receive the current fields, game templates and CSS. Their note/card identities, GUIDs, review history, scheduling, tags and existing card deck assignments are preserved. New content is imported into the GeoTrainer tree. Existing focused components share these canonical IDs, so subsequent component/full imports update the same notes.

The original July download had 1,716 cards, including 92 exercises excluded from today's edition. Those old exercises are retained with their content and rendering intact. A July-only installation therefore has 4,324 GeoTrainer cards after upgrading: 4,232 current cards plus the 92 retained old cards. You may archive or remove those old exercises yourself after review; the helper does not delete them. New users receive only the 4,232 current cards.

## Verify, then sync

The completion dialog appears only after native checks confirm current content and templates, all existing card identities/deck assignments/study state, unchanged review history, and collection integrity. Check several old and new cards and review counts yourself. Keep the recovery files and complete backup for at least 30 days. You can then remove the one-time helper.

Note-type changes may require a one-way full sync. The helper **never syncs or chooses Upload/Download**. If this upgraded, verified desktop holds your complete current collection, use **Upload to AnkiWeb** on this desktop and then **Download from AnkiWeb** on the other devices. If another device has unsynced edits or reviews, stop and reconcile them before choosing a direction. Do not download over the upgraded desktop unless you deliberately want to discard its changes.

## If interrupted or verification fails

Do not sync or retry. The helper records the failed/incomplete run and blocks another attempt. Its warning identifies the recovery directory.

1. Close Anki on every device. Keep the interrupted collection and recovery directory as recovery evidence.
2. On desktop, restore your complete pre-upgrade collection export through Anki's collection-package import/restore flow. Alternatively, restore the helper's `.colpkg` backup, then, with Anki closed, copy the contents of that run's `media` directory back into the profile's `collection.media` directory, allowing replacement of those files. The helper backup contains notes, cards, reviews and deck settings; the saved media restores affected original files. Extra newly imported media can remain harmlessly until a later Check Media pass.
3. Verify that your original cards and reviews are present. Only after verifying the restore, move `geotrainer-upgrade-recovery` out of the profile to a safe archive location. This clears the retry block without deleting recovery evidence.
4. Resolve the reported cause before attempting a new upgrade. Restore does not itself authorize a full-sync direction; keep other devices closed until the source of truth is verified.

GitHub: [https://github.com/ritornello-labs/anki-geo-trainer](https://github.com/ritornello-labs/anki-geo-trainer)

Support Ritornello: [https://ritornello.dev/support](https://ritornello.dev/support).
