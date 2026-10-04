# GeoTrainer publication scope reconciliation

Status: publication hold; previous full-edition image batch withdrawn. No personal collection operations are part of this audit.

## Decision records recovered

- September 30: Claude proposed World countries; country subdivisions; Physical geography; Plate tectonics; Reference lines & time; Globe placement; full edition. Elvis accepted it, renamed Globe placement to Islands & archipelagos and chose one subdivision pack per country.
- September 23–29: `world-geography-concepts/QA_VERDICTS.md` records the accepted concept families, the membership drill and its zoom, corrected Name prompts, retained Name/Locate cards, and the five geometry scopes integrated into GeoTrainer. The September 29 graduation verified 1,573 Geo Concepts cards plus 152 added GeoTrainer geometry cards, all accepted.
- September 29: `anki-geo-trainer/curriculum/REFERENCE_LINES_TIME_QA.md` records acceptance of 24 reference/time cards plus 54 atlas cards. Parallels and meridians use a rotatable orthographic globe; UTC conversion uses hour and relative-day inputs.
- October 3: Elvis withdrew the old flow exercise, requested components first and the full edition last, and asked that comparative quiz-site branding be removed.

**Confirmed October 3 by Elvis: all accepted Geo Concepts families belong in these releases.** The earlier drill-only alternative was introduced by Codex from the source-repository separation, not from a user decision, and is withdrawn. Repository boundaries do not define product scope. Most of the old flow deck has been discarded; use the retirement record and surviving accepted content, never an old everything-build, to choose release content.

## Discarded flow content

The September 29 retirement receipt (`anki-collection-audit-study/audits/2026-09-29-geotrainer-qa-retirement/`) records 36 discarded interactive QA notes/cards and nine emptied note types. These cover circulation cells, pressure belts, winds, jets, seasonal monsoons/currents, Atlantic overturning, ENSO states and pattern prediction. Empty models and older source builders are historical implementation, not accepted release content. Surface-current content remains withheld while survivors are matched to the accepted inventory. No deletion or schema cleanup is authorized as part of publishing.

## What the previous candidate missed

| Content | Source of accepted decision | Previous candidate | Required correction |
|---|---|---|---|
| Country-group membership taps (EU and other blocs) | Geo Concepts QA verdicts | Missing from package and preview | Include accepted drill with its existing identity; record selected component |
| Rotatable-globe placement of tropics, polar circles and meridians | Reference Lines & Time acceptance | In package, absent from preview | Capture current real-Anki interaction |
| UTC conversion and time-zone atlas | Reference Lines & Time acceptance | In package, absent from preview | Show distinct conversion experience and a representative atlas card |
| Plateaus, grasslands, peninsulas, minor plates, named boundaries | Geo Concepts QA verdicts | Geometry scopes in package; preview not representative | Use component-specific demos; do not imply seven legacy demos cover the full edition |
| Accepted Geo Concepts semantic families | Geo Concepts QA verdicts | Missing from package | Include all accepted families; preserve existing models/GUIDs and useful Name/Locate cards |
| Flow/current demo | October 3 user correction | Included in preview and Physical Geography candidate | Withdraw demo; withhold surface-current scope pending exact retirement reconciliation |
| Physical-systems QA and foundations prototype | Existing explicit exclusion | Excluded | Keep excluded; do not substitute the private replacement curriculum |

## Routing of all accepted Geo Concepts families

| Component | Existing GeoTrainer content | Additional accepted Geo Concepts content |
|---|---|---|
| World countries | Country scopes; continent silhouettes | Bloc Membership Drill; Regions & Groupings; Country Blocs & Organizations |
| Physical geography | Rivers; lakes; ranges; deserts; plateaus; grasslands; peninsulas | Corresponding concept cards; capes; straits/canals/isthmuses; biomes; Köppen classes and letter system |
| Plate tectonics | Major/minor plates; named-boundary Trace | Major/minor plate facts; named-boundary facts; repaired boundary-type maps |
| Reference lines & time | Accepted globe placement, reference facts, UTC conversion and atlas | None needed from Geo Concepts |
| Islands & archipelagos | 67 globe-placement cards | Accepted island/archipelago concept cards |
| Each country’s subdivisions | That country’s accepted scope | None |
| Full edition | Exact union of the final components | No extra or retired families |

All rows above are in scope. The rejected drill-only alternative must not reappear in release planning. Exact counts, source/media licensing and cross-edition identities still need verification against rebuilt artifacts.

## Offline rebuild

The current concept sources rebuilt successfully on October 3: 17 semantic family decks, 311 notes / 1,514 cards, plus 59 membership notes/cards. Total: **370 notes / 1,573 cards**, matching the accepted graduation total. Outputs are isolated temporary artifacts. This confirms source coverage, not final pack readiness: identity, media/license audit and component union/import checks remain. See CONCEPT_REBUILD_2026-10-03.json.

## Publication order and verification

1. Reconcile discarded flow families against the retirement receipt, then rebuild affected packs with all accepted Geo Concepts families.
2. Build components without changing their existing model/deck/GUID identities. Moving public deck paths must not derive new identities from the new names.
3. Verify each pack and the exact full union, then import overlaps in disposable Anki to prove no duplicates and media completeness. September 30 checks are historical evidence, not verification of the corrected release.
4. Preview one component batch at a time in real Anki. Default to a representative GIF per distinct learning experience, not per static template.
5. Publish components in value order, each linking to existing full listing 908455862 with an update-pending note. Record the resulting component listing IDs.
6. Publish the full edition last, retaining the original share name exactly and linking to every shipped component. Use a tagged GitHub release with byte-identical artifacts and update ritornello.dev.

All comparative quiz-site mentions were removed from current public GitHub copy on October 3. Retain actual Natural Earth, PB2002, NOAA and library attribution; this copy change makes no legal determination and does not erase historical Git commits.
