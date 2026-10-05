# Publication process

Public repositories contain curated deck source and deliberately public release
records. Personal Anki snapshots, scheduling, raw AnkiConnect responses, recovery
packages and detailed audit findings live outside every Git checkout. A public
CI failure is an alarm after exposure, not prevention.

## Bootstrap each publishing machine

Use sanitized public ancestry. Never push the divergent legacy development
checkout, even if its final tree looks clean.

```
python3 scripts/install_publication_hooks.py --private-dir /absolute/private/recovery-directory
make publication-test
```

The private directory is saved in local Git configuration, never committed.
`GEOTRAINER_PRIVATE_DIR` overrides it when a different recovery location is needed.
The installer refuses to overwrite existing hooks. Its absolute hook path is
shared by linked worktrees, so keep that checkout available until the hooks are
reinstalled from another sanitized checkout. Hooks are not installed by cloning:
repeat bootstrap on every publishing machine. GUI clients or tooling that bypass
hooks must run the checker explicitly. Agents must not bypass these gates.

Live scripts validate the output directory before their live operations; missing
configuration or a path inside Git stops the script. Existing recovery files are
not moved or deleted automatically. Resume paths must also be outside Git.
Retain routine recovery snapshots for 30 days; preserve incident/migration/only
recovery copies. Do not include this private directory in build contexts or uploads.

## Before commit and push

```
python3 scripts/check_private_artifacts.py --staged --details
```

This reads the staged Git objects, not potentially different working files.
The pre-push hook checks the actual destination's advertised refs and every
outgoing commit/tag target. Intermediate commits count: adding a snapshot and
then deleting it before pushing still fails. Unavailable boundary objects cause
more ancestry to be checked. A failed scan or unavailable remote blocks the push.

The checker detects forbidden recovery paths and filenames, recognizable renamed
Anki JSON snapshots, several credential formats, personal home paths, uninspected
LFS pointers, symlinks/submodules, and unsupported binaries. It recursively checks
ZIP attachments without extracting them. It is not a universal PII classifier:
review prose, screenshots and personal-derived content before staging. Synthetic
fixtures and disposable Anki profiles are the default for tests and public demos.

Do not copy raw live receipts into `release/`. Export public facts through a
fixed schema, preserving any existing release record's meaningful public checks.
`prepare_public_release.py` emits only a schema version, SHA-256, byte count,
check result, and visual-review status. It never imports fields from a live receipt.
Local diagnostics list locations and rule names; they never print matched values.

## Before every artifact upload

```
python3 scripts/prepare_public_release.py dist/deck.apkg --receipt dist/deck.publication.json
```

Package builders run the same check automatically and write adjacent receipts.
Re-run preparation immediately before uploading to GitHub or AnkiWeb. Upload
exactly the checked bytes; confirm the uploaded GitHub asset digest matches the
receipt. A rebuild or Publisher export needs a new check, even if source is clean.
This command checks files; it never publishes, imports, or syncs anything.

For approved listing images, pass `--reviewed-media-sha256 SHA256` from the exact
image that Elvis approved. This attestation does not perform visual review.
Archive-contained deck media are checked for known signatures, but their visual
and content review belongs to the deck's QA process.

Legacy SQLite `collection.anki2` and `collection.anki21` packages are inspected,
including both databases when present. Review logs and non-new scheduling cause
rejection. Compressed `collection.anki21b`, unknown schemas/formats, corrupt or
oversized archives, and encrypted entries are blocked until inspection support
exists. Do not bypass a format failure or treat it as a clean result.

## Public CI and GitHub protection

Public Actions runs use generic pass/fail output with no paths, snippets, values,
tracebacks, reports, or diagnostic artifacts. Incoming commit ranges are checked
as well as the final tree. Branch protection should require the publication job
before merge/release; this prevents further distribution but cannot retract an
already public branch. GitHub credential push protection adds a server-side gate
for supported credentials; it does not recognize arbitrary personal Anki data.

## If a real exposure is found

Stop publication and preserve the detailed finding privately. Determine whether
it exists only locally or reached any public commit, log, attachment, release,
listing image or deck. Rotate exposed credentials immediately. Personal content
needs a scoped cleanup plan covering refs/history, logs, artifacts, cached views,
forks and clones. Removing the current file is insufficient. History rewriting,
public deletion and coordination with other people require their own concrete
review; do not automatically force-push or erase evidence. Keep the incident
record privately and verify affected publication surfaces after cleanup.

## Verification for this rollout

Security tests use invented data and disposable repositories. They cover staged
versus working-file differences; renamed snapshots; add/delete histories and tags;
quiet findings/errors; private directory and symlink rejection; ZIP traversal;
credential signatures; APKG scheduling/review history; exact artifact hashes and
public receipt fields; and listing-image review attestations.

Existing public history and exact release bytes were audited privately during
rollout. Detailed findings and inventories are deliberately outside this repo;
a passing known-signature scan is not a claim that arbitrary personal content
has been independently reviewed.
