# Atlantic overturning curriculum design

Status: implemented and staged for manual QA 2026-08-05.

## Curriculum brief

- **Goal:** recall the Atlantic Meridional Overturning Circulation as motion
  through both latitude and depth.
- **Immediate deliverable:** four direction-aware GeoTrainer traces in one
  Atlantic latitude–depth cross-section.
- **Baseline:** the collection already contains surface-current, atmospheric-cell,
  and season-aware flow drills, but the live duplicate audit found no actual AMOC,
  thermohaline-circulation, or global-conveyor notes.
- **Fairness boundary:** routes are broad zonally integrated teaching paths, not
  exact local currents, forecasts, transport measurements, or a claim that one
  parcel follows a single global conveyor loop.
- **Excluded:** AMOC climate projections, tipping thresholds, water-mass names,
  exact depths/transport values, and the global Indo-Pacific return pathway.

## Concept map

```text
northward upper-ocean limb
  -> high-latitude cooling and densification
  -> northern sinking / water-mass transformation
  -> southward deep-ocean return limb
  -> connection to Southern Ocean and wider global overturning

three component traces
  -> complete Atlantic overturning pathway
```

The final pathway deliberately ends at the deep South Atlantic boundary. It does
not draw a vertical “upwelling” limb there: much of the transformation back toward
the upper ocean occurs through mixing and upwelling in the Southern Ocean and
Indo-Pacific, outside the Atlantic section.

## Selection ledger

| Order | Stable item ID | Decision | Retrieval |
|---:|---|---|---|
| 1 | `01-upper-limb` | Add | Trace the northward upper-ocean limb |
| 2 | `02-sinking-limb` | Add | Trace the northern high-latitude descent |
| 3 | `03-deep-return-limb` | Add | Trace the southward deep-ocean return limb |
| 4 | `04-complete-pathway` | Add | Integrate the three components into the complete Atlantic pathway |
| — | Flat global conveyor-belt loop | Defer | Collapses depth and implies a falsely singular parcel route |
| — | Global upwelling locations | Defer | Diffuse, distributed transformation is a poor fixed-point drill |

The live audit searched `thermohaline`, `AMOC`, the expanded AMOC name, and
`global conveyor belt`. The apparent `AMOC` hits were incidental substrings in
unrelated vocabulary and city notes; there were no reusable or repairable notes.

The live rollout created the four selected items in prerequisite order:

| Stable item ID | Note ID | Card ID |
|---|---:|---:|
| `01-upper-limb` | `1785965360866` | `1785965360867` |
| `02-sinking-limb` | `1785965360868` | `1785965360869` |
| `03-deep-return-limb` | `1785965360870` | `1785965360871` |
| `04-complete-pathway` | `1785965360872` | `1785965360873` |

## Card and note-type design

One purpose-built note type, `GeoTrainer Trace Atlantic Overturning — AMOC
Cross-section`, carries all four cards. The front shows:

- Atlantic latitude from 30°S through 60°N;
- ocean depth from the surface to 5 km;
- a start dot and the named component;
- no answer flow.

The learner traces one directed open pathway. Grading checks latitude, depth,
coverage, stray distance, and direction. The back reveals a broad accepted
corridor and arrow. The integration card is an open Atlantic pathway rather than
a closed global loop.

## Rollout plan

1. Build and test the four cards with a fresh deterministic model/deck ID pair.
2. Run exact-template Chromium/WebKit tests and request disposable real-Anki
   Desktop QA. The cross-engine suite passed; the hosted Desktop job was still
   queued when the local QA staging pass completed.
3. Add the four cards to `Process::GeoTrainer QA::Physical::Ocean Currents::3
   Trace Atlantic Overturning`, preserving the existing 2,402 notes and every
   scheduling record.
4. After manual QA, restore these four cards alongside the staged atmospheric
   batch to the normal GeoTrainer tree before Publisher export.

The guarded live rollout completed with 2,402 existing notes, card identities,
deck assignments, fields, tags, and scheduling records unchanged. It added only
the four IDs above, found no filtered-deck collision, and performed no sync. The
rollback snapshot and exact verification record live under
`backups/live-imports/20260805T143037-0700-amoc/`.

## Sources

- [NOAA 2024 AMOC state-of-the-science fact sheet](https://doi.org/10.25923/pav0-be22)
- [NOAA GFDL: AMOC decadal variability and predictability](https://www.gfdl.noaa.gov/amoc-decadal-predictability/)
- [NOAA Ocean Service: What is the AMOC?](https://oceanservice.noaa.gov/facts/amoc.html)
- [NOAA Ocean Service: Global conveyor belt](https://oceanservice.noaa.gov/facts/conveyor.html)
