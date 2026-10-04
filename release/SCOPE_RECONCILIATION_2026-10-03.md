# GeoTrainer publication scope reconciliation

Status: publication hold; previous full-edition image batch withdrawn. No personal collection operations are part of this audit.

## Decision records recovered

- September 30: Claude proposed World countries; country subdivisions; Physical geography; Plate tectonics; Reference lines & time; Globe placement; full edition. Elvis accepted it, renamed Globe placement to Islands & archipelagos and chose one subdivision pack per country.
- September 23–29: `world-geography-concepts/QA_VERDICTS.md` records the accepted concept families, the membership drill and its zoom, corrected Name prompts, retained Name/Locate cards, and the five geometry scopes integrated into GeoTrainer. The September 29 graduation verified 1,573 Geo Concepts cards plus 152 added GeoTrainer geometry cards, all accepted.
- September 29: `anki-geo-trainer/curriculum/REFERENCE_LINES_TIME_QA.md` records acceptance of 24 reference/time cards plus 54 atlas cards. Parallels and meridians use a rotatable orthographic globe; UTC conversion uses hour and relative-day inputs.
- October 3: Elvis withdrew the old flow exercise, requested components first and the full edition last, and asked that comparative quiz-site branding be removed.

The September 30 pack proposal did not resolve whether the separately maintained Geo Concepts families were part of the public full edition. That boundary must be settled explicitly; it cannot be inferred from the word “everything” in the generator.

## What the previous candidate missed

| Content | Source of accepted decision | Previous candidate | Required correction |
|---|---|---|---|
| Country-group membership taps (EU and other blocs) | Geo Concepts QA verdicts | Missing from package and preview | Include accepted drill with its existing identity; record selected component |
| Rotatable-globe placement of tropics, polar circles and meridians | Reference Lines & Time acceptance | In package, absent from preview | Capture current real-Anki interaction |
| UTC conversion and time-zone atlas | Reference Lines & Time acceptance | In package, absent from preview | Show distinct conversion experience and a representative atlas card |
| Plateaus, grasslands, peninsulas, minor plates, named boundaries | Geo Concepts QA verdicts | Geometry scopes in package; preview not representative | Use component-specific demos; do not imply seven legacy demos cover the full edition |
| Accepted Geo Concepts semantic families | Geo Concepts QA verdicts | Missing from package | Await scope choice below; preserve existing models/GUIDs and useful Name/Locate cards if included |
| Flow/current demo | October 3 user correction | Included in preview and Physical Geography candidate | Withdraw demo; withhold surface-current scope pending exact retirement reconciliation |
| Physical-systems QA and foundations prototype | Existing explicit exclusion | Excluded | Keep excluded; do not substitute the private replacement curriculum |

## Proposed routing if all accepted Geo Concepts families are included

| Component | Existing GeoTrainer content | Additional accepted Geo Concepts content |
|---|---|---|
| World countries | Country scopes; continent silhouettes | Bloc Membership Drill; Regions & Groupings; Country Blocs & Organizations |
| Physical geography | Rivers; lakes; ranges; deserts; plateaus; grasslands; peninsulas | Corresponding concept cards; capes; straits/canals/isthmuses; biomes; Köppen classes and letter system |
| Plate tectonics | Major/minor plates; named-boundary Trace | Major/minor plate facts; named-boundary facts; repaired boundary-type maps |
| Reference lines & time | Accepted globe placement, reference facts, UTC conversion and atlas | None needed from Geo Concepts |
| Islands & archipelagos | 67 globe-placement cards | Accepted island/archipelago concept cards |
| Each country’s subdivisions | That country’s accepted scope | None |
| Full edition | Exact union of the final components | No extra or retired families |

If only the membership drill is chosen, add that drill to World countries and retain the other Geo Concepts families outside this release. This choice is pending Elvis’s reply.

## Publication order and verification

1. Settle the source boundary and exact obsolete flow family before rebuilding affected packs.
2. Build components without changing their existing model/deck/GUID identities. Moving public deck paths must not derive new identities from the new names.
3. Verify each pack and the exact full union, then import overlaps in disposable Anki to prove no duplicates and media completeness. September 30 checks are historical evidence, not verification of the corrected release.
4. Preview one component batch at a time in real Anki. Default to a representative GIF per distinct learning experience, not per static template.
5. Publish components in value order, each linking to existing full listing 908455862 with an update-pending note. Record the resulting component listing IDs.
6. Publish the full edition last, retaining the original share name exactly and linking to every shipped component. Use a tagged GitHub release with byte-identical artifacts and update ritornello.dev.

All comparative quiz-site mentions were removed from current public GitHub copy on October 3. Retain actual Natural Earth, PB2002, NOAA and library attribution; this copy change makes no legal determination and does not erase historical Git commits.
