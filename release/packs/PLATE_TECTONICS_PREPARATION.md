# Plate Tectonics publication preparation — October 4

Status: complete listing and five real-Anki GIFs await Elvis's image approval.
No images uploaded, no Publisher staging, and no AnkiWeb submission. Personal
Anki has not been accessed or changed.

Accepted scope: 204 notes / 492 cards, ten models and ten canonical leaf decks.
Geometry has 132 game notes/cards: 16 mapped plates × identify/place/sketch;
35 minor-plate placement and 32 minor-plate sketches; 17 named-boundary traces.
Concepts have 72 notes / 360 cards: 17 plate concepts, 35 minor plates, three
boundary types and 17 named boundaries. All 70 media files survive a native
Anki 25.09 import/export byte-identically; none are missing. Public source
rebuild exactly matches GUIDs/fields/models/templates/CSS/deck IDs/names/media.
Native component → full candidate → component imports preserve all note/model/
card/leaf IDs and create zero duplicates (full candidate 2,987 notes / 4,212 cards).
QA/foundations and retired current flows remain excluded.

Five GIFs show distinct experiences: African Plate identification; Arabian Plate
placement; Arabian Plate sketch; San Andreas Fault zoom/pan/trace; named-boundary
type recall with its complete locator map. They came from anki-addon-workbench
in a disposable Docker/Xvfb Anki 25.09 profile with native pointer input, real
answer reveals and ffmpeg X11 capture. No Anki grades were recorded. Noto Emoji
was installed only in that capture environment. The trace is deliberately an
imperfect recall attempt, followed by the native roughly-right/Hard suggestion.

Source/copyright check: PB2002 by Peter Bird, converted by Hugo Ahlenius/Nordpil,
Open Data Commons Attribution 1.0 (primary fraxen/tectonicplates repository).
Locator base map is **TUBS**, CC BY-SA 3.0, not the inherited catalog's Tentotwo
attribution; corrected source catalog, README and listing, without changing card
fields/templates/media. Basemap: World_location_map_(equirectangular_180).svg on
Wikimedia Commons. Selected plate/boundary overlays are credited and derivatives
retain CC BY-SA 3.0. Natural Earth context data are public domain. Wikipedia-derived
prose retains its original attribution/license in source credits. The stable
support page, banner, gallery, full-edition link and visible GitHub URL are present.

## Resume after image approval

1. Verify `PLATE_TECTONICS_REVIEW.json` hashes against the locally shown files in
   `www/.tmp/publish-batch-plate-tectonics/media/`. Deploy those exact GIFs/posters
   to the immutable versioned media path and verify their live hashes.
2. Close only task-owned isolated Publisher, make a complete collection/media
   backup, read exact existing pack membership/model/deck IDs, and add the precise
   Publisher schema-change row to `PENDING_FULL_SYNCS.md` before mutations.
3. Reconcile only this pack's exclusive scope with native Anki APIs. Preserve all
   outside notes/cards/models/deck names/IDs/media, including held flows. Verify
   204 notes / 492 cards, ten model/leaf IDs, exact source content and all 70 media.
   Register the source parent only in ignored `.env`, under
   `ANKIWEB_SOURCE_DECK_ID_PLATE_TECTONICS`. Parent: `GeoTrainer::Plate Tectonics`.
4. Complete the already explicitly authorized isolated-Publisher **Upload** if
   required; verify normal/final sync required 0, native integrity and unchanged
   source/all outside content. Close the full-sync row only then. No new direction
   approval is needed. Never operate the personal profile.
5. Commit -S and push clean release source. Run anki-release wrapper preflight,
   then publish with config `release/packs/plate-tectonics.toml`, `--submit
   --confirm-copyright`, resolving secrets only through `op run --env-file=.env`.
   Stop and wait for Elvis if 1Password needs his authorization.
6. Owner-verify listing/image URLs/support/counts, download the actual AnkiWeb-
   delivered APKG and compare native identity/content/media against the verified
   export. Archive that exact byte stream on the current date-tagged GitHub release;
   digest-verify and retain previous assets/tags. Add shared_id in the AnkiWeb config
   and update COMPONENT_LINKS.json; preserve the exact original share name.
7. Update ritornello.dev homepage/gallery/release/downloads and verify in a browser;
   update PROJECT_STATUS.md and PUBLISH_QUEUE.md with observed quota and next order.
   Stop cleanly on an actual quota rejection. No reminder is authorized.

Physical Geography is already shipped at 1832856685; don't resubmit it. Five prior
components are archived. Current quota is 8/20 deck shares; no limit has been hit
and reset date is unknown. After Plate: Islands & Archipelagos, World Countries,
remaining seven country components, then full edition at 908455862 (exact original
share name). Each new image batch requires its own approval.
