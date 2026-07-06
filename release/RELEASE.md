# Release plan (M5)

Status: **prepared, not published.** The artifacts below are ready; actually
submitting to AnkiWeb needs Elvis's go-ahead, credentials, and awareness of the
20-shares-per-7-days quota. Nothing here has been uploaded.

## Open decisions (need Elvis)

1. **Public GitHub repo?** The repo is currently private (`elvis-sik/anki-geo-trainer`).
   AnkiWeb listings link back to it, so it should be public first. Run the
   history/secret-leak scan (as the other deck projects did) before flipping it.
2. **Packaging on AnkiWeb.** Two options:
   - **One shared deck** `GeoTrainer` with every scope as a subdeck (~2,500 notes,
     ~40 MB). Simplest for users; one listing to maintain.
   - **Several shared decks** (e.g. one per continent + one "Physical"). Lets users
     grab only what they want; more listings, more quota use.
   Recommendation: start with **one** `GeoTrainer` deck; split later if users ask.
3. **Which scopes ship first.** All 18 are import-verified. Could hold back the
   thinnest (Oceania capitals 8/14) or ship everything.

## Ready artifacts

- `release/ankiweb.md` — listing copy (title, tags, support URL front-matter; body has
  the clickable full-URL GitHub link per workspace convention).
- Built APKGs in `dist/` for every scope (18 packs).
- A combined `dist/geo-trainer-all.apkg` is **not** built yet; add a `make apkg-all`
  target (import-merge the per-scope packs, or a `build_apkg.py --combined` mode) if we
  go with the single-deck option.

## Before publishing (checklist)

- [ ] Make the GitHub repo public; run a tree+history secret/absolute-path scan first.
- [ ] Add MIT `LICENSE`, README badges, and a workbench-generated screenshot
      (`anki-workbench screenshot`) as the listing image — mirror `brazil-ddd-codes`.
- [ ] Decide single-deck vs per-continent; build the combined pack if needed.
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
