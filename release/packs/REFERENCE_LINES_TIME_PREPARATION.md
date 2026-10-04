# Reference Lines & Time preparation — 2026-10-04

Status: awaiting Elvis's complete listing/image approval. Not staged in Publisher, not submitted to AnkiWeb, no shared ID assigned. The accepted component includes the complete 78-card reference/time curriculum; the two historical internal model names containing “QA” retain their identities. These are accepted families, distinct from the rejected physical-systems QA scopes and foundations prototype.

## Verification

- Fresh build: `build_apkg.build_public_pack('reference-lines-time', PUBLIC_PACKS['reference-lines-time'])` from the sanitized release worktree. Counts: 56 notes, 78 cards, ten leaves, 32 bundled SVG atlas maps.
- `REFERENCE_LINES_TIME_REVIEW.json` records source package digest, model/leaf identities, all map digests, four native GIF digests and visual checks.
- `REFERENCE_LINES_TIME_OVERLAP.json`: Anki 25.09 native import of component, held September 30 full candidate, then component again. All 56 note identities and 78 card identities unchanged; zero duplicates. Recheck against the final rebuilt full edition before shipping it.
- Actual workbench captures used disposable Anki 25.09 Docker/Xvfb with native pointer/keyboard input and `ffmpeg-x11grab`. Globe: rotate, place Tropic of Cancer, reveal 23.5° N. UTC: 22:00 UTC−3 → 01:00 UTC next day. Date line: illustrated self-graded east/west calendar recall. Atlas: Kathmandu offset, Nepal highlighted.
- Complete preview: `www/.tmp/publish-batch-reference-lines-time/reference-lines-time-listing.png`; local HTML retains the animated images. The static overview uses answer frames from those same real-Anki GIFs.

## Sources

- Natural Earth globe geometry is public domain: https://www.naturalearthdata.com/about/terms-of-use/
- Timezone Boundary Builder 2026d boundary data: https://github.com/evansiroky/timezone-boundary-builder/releases/tag/2026d
- Boundary output is ODbL, distinct from the generator's MIT code: https://github.com/evansiroky/timezone-boundary-builder/blob/master/DATA_LICENSE ; © OpenStreetMap contributors. Primary project license/source checked October 4. Card footers and listing retain the attribution.
- The atlas uses named civil-time areas; only the Brazil maps union areas sharing an offset at 2026-09-25 12:00 UTC. Local Xinjiang practice is approximate and dashed. Standard/daylight conditions are explicit on seasonal questions.
- Individual cards retain their original NOAA, USGS, NASA, USNO, NIST, BIPM, ITU, IANA and national source links. No personal collection content was changed.

## Resume after approval

1. Deploy exactly the reviewed GIFs and record immutable URLs from the listing's `2026-10-04-v1/geo-trainer-reference-lines-time` media directory.
2. Back up and verify the isolated Publisher. Determine its existing reference/atlas scope by the source GUIDs and model IDs; ensure scope models are exclusive before replacing obsolete Publisher content. Preserve canonical package model/leaf IDs and GUIDs; hash all outside-scope content before and after.
3. Record any full-sync obligation before schema changes. Close only the verified owned Publisher process before native collection staging. The isolated Publisher full Upload direction is already approved in this chat. Never operate on the personal profile.
4. Privately register the reference container in ignored `.env` as `ANKIWEB_SOURCE_DECK_ID_REFERENCE_LINES_TIME`. Native scoped export, readback, integrity and sync must pass before publishing.
5. Sign/push source, run `anki-release.sh` preflight/publish with `release/packs/reference-lines-time.toml`. Credentials resolve only at the `op run` process boundary; authenticated browser reuse requires no credential typing.
6. Verify owner listing/title/counts/exact original share name and current quota. Download the actual AnkiWeb-delivered APKG; compare note GUIDs/fields/card associations/models/templates/CSS/leaf IDs against the native export. Archive that exact file on a dated tagged GitHub release, verifying the asset digest. Add to the existing shipping-date release if appropriate; never overwrite another component's asset.
7. Update component links, public README, website/gallery, queue and workspace status. Retain the full-edition hold and recheck its final union identities.
