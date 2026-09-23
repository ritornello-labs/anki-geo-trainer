# Physical-systems QA redesign

Status: revised again 2026-09-23 and refreshed in Elvis's live
`Process::GeoTrainer QA` tree. All 29 cards remain QA-only; none is approved
for release or moved into the daily GeoTrainer tree. No sync was performed.

## Brief and boundary

The learner should be able to locate the major *idealized* circulation zones,
explain the dominant direction of broad flows, and distinguish seasonal or
coupled states. A card must test one intelligible retrieval with enough context
to attempt it before revealing the answer. The immediate deliverable is one
reviewable front/back prototype for each proposed family, followed by an accepted
release set. Card count is not a target.

This route does not ask for a daily weather forecast, a precise jet or monsoon
track, an invariant position for the ITCZ, or a single parcel's global ocean
conveyor route. A world map is useful for *geographic* placement; a labelled
section is useful for vertical structure. Neither is automatically the right
interaction simply because the engine can draw on it. Do not assume prior
knowledge of ITCZ or thermocline; define those terms before using them.

## Concept route

```text
unequal heating + rotation
  -> idealized rising/sinking zones and pressure pattern
  -> broad surface wind belts and directions
  -> upper-air jets: west-to-east flow, variable latitude/meanders

seasonal land/ocean heating contrast
  -> South Asian summer/winter low-level wind regimes
  -> Somali coastal-current reversal and cross-basin monsoon-current reversal

Atlantic upper/deep distinction
  -> upper northward transport, northern sinking/transformation,
     deep southward return (AMOC)

equatorial Pacific trade-wind strength
  -> warm-water position + thermocline slope + eastern upwelling
  -> neutral / El Niño / La Niña comparison
```

Define any term used in a prompt before expecting its mechanism. In particular,
the three-cell diagram is a zonal-mean teaching model, not a literal pair of
closed air-parcel paths; the Ferrel cell is an indirect circulation influenced
by midlatitude eddies. The tropical rain belt and jets move with season and
weather. These caveats belong on the relevant answer sides, not hidden only in
project documentation.

## Selection ledger for the live QA batch

The stable keys below identify the scoped cards without publishing private
collection note/card IDs. `Retire design` means keep the live cards quarantined
while a replacement is evaluated; it does not authorize deletion. `Repair`
means reuse a live identity only if the revised retrieval genuinely fits it.

| Family | Live keys / count | Decision | Why and proposed retrieval |
|---|---:|---|---|
| Circulation cells | `atmospheric-cells` / 3 | Retire design | Two hand-drawn closed loops per card turn an idealized average into an exact tracing task. Start with labelled rising/sinking and surface-flow relationships; omit a drawing exercise unless it proves a distinct skill. |
| Pressure belts | `atmospheric-pressure-belts` / 4 | Repair or narrow | Full-width fixed stripes imply geographically uniform, stationary pressure; `subpolar lows / polar fronts` also conflates related but different phenomena. Use an explicitly idealized latitude section; ask for one named broad zone, state whether one or both hemispheres are wanted, and reveal the approximate/seasonal nature of the result. |
| Prevailing winds | `world-prevailing-winds` / 6 | Repair; polar pair blocked | Broad latitude and direction are worth retrieving. The current map ends at 80°N/70°S although the polar accepted belts extend to 90°, and the southern exemplar begins outside the visible SVG. Fix or remove that pair before piloting. Show the learner's arrow against an idealized flow *band*, not one invented polyline. Recheck whether the wind name gives away the intended direction. |
| Jet streams | `world-jet-streams` / 4 | Retire design | The answer currently shows arbitrary world-spanning zigzags although grading ignores those bends. Teach high-altitude, mainly west-to-east flow and variable jet latitude; use a broad-band or interpretation task only if it adds value beyond the wind cards. |
| South Asian monsoon winds | `south-asia-monsoon-winds` / 2 | Repair | The current regional arrow occupies a small part of a world map, and one fixed line overspecifies a seasonal wind regime. Use a South Asia/northern Indian Ocean view with a broad ocean-to-land versus land-to-ocean direction task. Reconcile the month labels with the chosen regional definition before release. |
| Indian Ocean seasonal currents | `indian-ocean-seasonal-currents` / 4 | Repair and pilot first | The Somali coastal reversal and east/west cross-basin reversal are source-backed, distinct geographic retrievals. Keep summer/winter explicit; explain that Southwest/Northeast in the current names denotes the *monsoon season*, not the current's compass direction. Show a broad accepted corridor and learner arrow, not one exact line. |
| Atlantic overturning | `atlantic-overturning` / 2 | Retire design | The front shows a sparse section; the sequence card asks for four invisible waypoints. Make every selectable stage visible and named. Test upper/deep direction and order separately, or defer AMOC if a clear interaction cannot be built. |
| ENSO | `equatorial-pacific-enso` / 4 | Retire design | The front asks for five coupled variables from a blank panel and records no response. First teach west/east and surface/depth orientation; then ask one state comparison at a time with explicit, specific feedback. |

This ledger records the defects that drove the redesign, not the current card
behavior. None of the 29 cards is approved for publication.

## Current implementation and manual QA

- Cells ask for approximate rising and sinking latitudes in both hemispheres;
  the answer identifies the zonal-mean/indirect-Ferrel caveat. Pressure belts
  use an abstract latitude section, and subpolar low is no longer conflated
  with the polar-front concept.
- Wind/jet maps include both poles; answers show broad bands and a schematic
  arrow, not prescribed zigzags. South Asian monsoon winds use a regional
  frame and a broad seasonal corridor. Seasonal currents accept alternative
  ocean-only arrows but reject reversed, misplaced, and on-land responses.
- AMOC uses explicit upper/deep direction choices and shuffled, named stage
  buttons. The cell and AMOC backs now repeat the front's choice arrangement,
  marking both the learner's selection and the correct selection in place.
- ENSO now begins with a normal west/east baseline, then asks what weaker and
  stronger westward trades do to warm surface water and cool water rising in
  the east. The first answer defines eastern upwelling instead of assuming it
  is known; the final card asks for an unaided El Niño/La Niña comparison.
  Choice backs retain the same grid and visibly mark wrong/right answers.
- The eight revised packages were imported over the 29 already-staged cards.
  Live verification preserved all 2,341 GeoTrainer card identities and
  scheduling values, changed no unrelated note content, and matched all eight
  generated note templates/CSS. Recovery export and verification are outside
  the source repository in
  `.tmp-anki-geo-extra/private-qa-recovery/20260923T142444-0700-physical-qa-refresh`.
  No Anki sync was performed.
- A second, scoped refresh imported only cells, Atlantic overturning, and ENSO
  into those same live QA cards. It again preserved all 2,341 GeoTrainer card
  IDs and scheduling values and changed no unrelated notes. The recovery export
  and verification are in
  `.tmp-anki-geo-extra/private-qa-recovery/20260923T150040-0700-physical-qa-refresh`.
  The obsolete, empty, childless `3 Trace Atlantic Overturning` QA deck shell
  was removed after confirming zero card deletion; `3 Learn Atlantic
  Overturning` retains its two cards. No sync was performed.

For Elvis's QA, browse `Process::GeoTrainer QA` in Anki and try each family
front-to-back, including a deliberately wrong direction or choice. Check the
cell rise/sink distinction, pressure latitudes, polar winds, jet bands,
summer/winter monsoon reversals, AMOC order, and whether the ENSO cards teach
rather than merely cue their answers. Record any confusing prompt or
misleading diagram before release selection. The current local browser suite
passed 338 tests across Chromium and WebKit with 26 expected skips; focused
post-wording tests passed in both engines. Learner judgment and other-client
interaction QA remain open.

## Prototype and release gates

1. **Science and task brief.** For each family, write the single thing a learner
   must retrieve, the cues visible on the front, the acceptable answer range,
   and the caveat shown on the back. Cite the source used for each claim.
2. **Prerequisite closure.** Introduce the latitude/hemisphere and surface/depth
   frames before asking for a flow. Explain ITCZ, jet, monsoon, thermocline,
   upwelling, and AMOC on a prior card or within the first relevant answer.
3. **One prototype per family.** Review front, attempted response, and back
   in Elvis's own QA collection. Check that the learner can discover the
   action and interpret the answer without developer documentation.
4. **Acceptance tests.** Check meaningful correct, reversed, incomplete, and
   reasonable-alternative responses. Technical mount/count tests do not count
   as pedagogical approval. Run cross-client checks for interaction changes.
5. **Guarded live update.** The QA-only refresh is complete with exact
   membership, snapshot, and content/scheduling checks. Preserve those
   identities; leave rejected cards in QA until a deliberate retirement
   decision. Do not restore the 29-card batch wholesale.
6. **Publication choice.** Recompute a clean release artifact from accepted
   families only. A core GeoTrainer update that excludes the QA batch may be
   considered separately, but its exact contents, count, listing, Publisher
   import, and preview need their own verification. AnkiWeb upload and the
   matching GitHub release remain on hold until those gates pass.

## Source checks

- [Met Office: global circulation patterns](https://weather.metoffice.gov.uk/learn-about/weather/atmosphere/global-circulation-patterns) and [UCAR: global circulation](https://www.meted.ucar.edu/tropical/textbook_2nd_edition/print_3.htm) for the idealized three-cell model and indirect Ferrel circulation.
- [NOAA: ITCZ/doldrums](https://oceanservice.noaa.gov/facts/doldrums.html) for its seasonal movement.
- [NOAA: jet streams](https://www.nesdis.noaa.gov/about/k-12-education/atmosphere/what-the-jet-stream) for upper-air west-to-east flow and north/south meanders.
- [Met Office: South Asian monsoon](https://www.metoffice.gov.uk/binaries/content/assets/metofficegovuk/pdf/business/international/scipsa_review_seasonal_forecasting_south_asia_final.pdf) for regional wind regimes and season labels.
- [NOAA-hosted Somali Current study](https://repository.library.noaa.gov/view/noaa/59095) and [NOAA-hosted Indian Ocean circulation review](https://repository.library.noaa.gov/view/noaa/44660/noaa_44660_DS1.pdf) for the seasonal current reversals.
- [NOAA: AMOC](https://oceanservice.noaa.gov/facts/amoc.html) and [NOAA PMEL: ENSO schematics](https://www.pmel.noaa.gov/elnino/schematic-diagrams) for the two coupled ocean-system models.
