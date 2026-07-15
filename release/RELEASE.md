# Release plan (M5)

Status: **submitted to AnkiWeb on 2026-07-15; awaiting its standard 24-hour
public-visibility review.** [Open the fresh listing](https://ankiweb.net/shared/info/908455862?cb=1784084661007).

Verification status (2026-07-07, post borderless-recall redesign + study-feedback
pass 2 + continents/North-America scopes): all 22 scopes pass the cross-engine suite
(Chromium + WebKit, 224 passed / 6 skipped). Region scopes carry Which/Place/Draw;
rivers are Trace-the-course; mountain ranges and deserts are Place-only; the
Continents scope is Draw-only (all six inhabited continent silhouettes).
Combined `geo-trainer-all.apkg` = 52 decks, 1,699 notes, 26.9 MB.

## Decisions

1. **Packaging: one shared deck.** Decided (Elvis, 2026-07-06) — ship a single
   `GeoTrainer` deck with every scope as a subdeck, so there's one listing and one set
   of screenshots to maintain. Built: `make apkg-all` → `dist/geo-trainer-all.apkg`
   (**52 decks, 1,699 notes, 26.9 MB** — well under AnkiWeb's per-deck limit).
2. **Ship everything.** All 22 scopes are import-verified; the single deck includes them
   all. (Thin spots like Oceania capitals are just fewer cards in a subdeck, not a
   problem for a combined deck.)

## Release record

1. The repo was history/tree audited and made public on 2026-07-13.
2. The listing description was previewed and approved before submission. Its three
   screenshots were captured from reviewer cards in a disposable real-Anki
   `anki-addon-workbench` profile, not a browser mock.

## Ready artifacts

- `release/ankiweb.md` — listing copy (title, tags, support URL front-matter; body has
  the clickable full-URL GitHub link per workspace convention).
- `dist/geo-trainer-all.apkg` — the single shareable deck (`make apkg-all`).
- `release/screenshots/` — three public listing images captured from real Anki reviewer
  cards in a disposable `anki-addon-workbench` profile.
- Per-scope APKGs in `dist/` (18 packs) remain for anyone who wants just one region.

## Before publishing (checklist)

- [x] MIT `LICENSE` added (2026-07-06); tracked-tree secret/absolute-path scan clean.
- [x] Full history/tree secret and absolute-path scan passed; GitHub repo made public (2026-07-13).
- [x] Actual Anki reviewer screenshots captured to `release/screenshots/` (2026-07-15).
- [x] Single-deck decision made; `dist/geo-trainer-all.apkg` built via `make apkg-all`.
- [x] Configure `anki-addon-release` with a git-ignored source-deck reference and
      process-boundary 1Password credentials.
- [x] Preview the rendered listing and pass the visible-clickable-GitHub-URL check.
- [x] Submit the first version; record shared id `908455862` and link it from the README.

## Not blocking release

- Two orphan "GeoTrainer Neighbors" note types remain in Elvis's collection from the
  F7 retirement (Tools → Manage Note Types to drop).
- Deferred content: mountain ranges (needs 10m regions with `featurecla`), lakes,
  more country subdivisions from the 10m admin-1 file.
