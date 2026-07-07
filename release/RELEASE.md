# Release plan (M5)

Status: **prepared, not published.** The artifacts below are ready; actually
submitting to AnkiWeb needs Elvis's go-ahead, credentials, and awareness of the
20-shares-per-7-days quota. Nothing here has been uploaded.

Verification status (2026-07-06): all 18 scopes × 6 families pass the cross-engine
suite (Chromium + WebKit, 198 passed / 2 skipped), Docker/Xvfb deck smoke, and live
AnkiConnect import (2,880 notes, 80 leaf decks). The newest engine mode (F9
river-locate) is also confirmed on the AnkiDroid emulator end to end: physical tap on
the Abay, polyline highlighted, graded "On it".

## Decisions

1. **Packaging: one shared deck.** Decided (Elvis, 2026-07-06) — ship a single
   `GeoTrainer` deck with every scope as a subdeck, so there's one listing and one set
   of screenshots to maintain. Built: `make apkg-all` → `dist/geo-trainer-all.apkg`
   (**52 decks, ~1,716 notes, 24.1 MB** — well under AnkiWeb's per-deck limit).
2. **Ship everything.** All 18 scopes are import-verified; the single deck includes them
   all. (Thin spots like Oceania capitals are just fewer cards in a subdeck, not a
   problem for a combined deck.)

## Open decisions (need Elvis)

1. **Public GitHub repo?** The repo is currently private (`elvis-sik/anki-geo-trainer`).
   AnkiWeb listings link back to it, so it should be public first. Run the
   history/secret-leak scan (as the other deck projects did) before flipping it.

## Ready artifacts

- `release/ankiweb.md` — listing copy (title, tags, support URL front-matter; body has
  the clickable full-URL GitHub link per workspace convention).
- `dist/geo-trainer-all.apkg` — the single shareable deck (`make apkg-all`).
- `release/screenshots/` — listing images (`make apkg-all` cards captured in the browser
  preview); pick the best 1–3 for the AnkiWeb listing.
- Per-scope APKGs in `dist/` (18 packs) remain for anyone who wants just one region.

## Before publishing (checklist)

- [x] MIT `LICENSE` added (2026-07-06); tracked-tree secret/absolute-path scan clean.
- [ ] Make the GitHub repo public; run a full history (not just tree) secret scan first.
- [x] Listing screenshots captured to `release/screenshots/` (2026-07-06).
- [x] Single-deck decision made; `dist/geo-trainer-all.apkg` built via `make apkg-all`.
- [ ] Configure `anki-addon-release` (`pyproject.toml` target + git-ignored `.env`
      with `ANKIWEB_*` 1Password refs and the source deck id).
- [ ] `anki-addon-release publish --dry-run` / `--preview-description` to verify the
      rendered Markdown and the visible-clickable-GitHub-URL check pass.
- [ ] Submit (respecting the 20/7-day quota), then add the AnkiWeb download badge/link
      to the README.

## Not blocking release

- Two orphan "GeoTrainer Neighbors" note types remain in Elvis's collection from the
  F7 retirement (Tools → Manage Note Types to drop).
- Deferred content: mountain ranges (needs 10m regions with `featurecla`), lakes,
  more country subdivisions from the 10m admin-1 file.
