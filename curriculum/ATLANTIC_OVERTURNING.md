# Atlantic overturning curriculum design

Status: redesigned, cross-engine verified, and staged for manual QA 2026-08-06.

## Curriculum brief

The goal is to understand Atlantic Meridional Overturning Circulation (AMOC) as
an ordered relationship between latitude, depth, and direction—not to reproduce
one precise model line. The latitude–depth cross-section is still the right
representation; the original freehand interaction was the problem.

The cards teach the broad zonally integrated model:

```text
northward upper-ocean flow
  -> high-latitude cooling/densification and sinking
  -> southward deep-ocean return toward the Southern Ocean
```

The section does not invent a local South Atlantic upwelling limb. Transformation
back toward the upper ocean is distributed through Southern Ocean and Indo-Pacific
mixing/upwelling outside this Atlantic-only exercise.

## Implemented cards

| Order | Stable item ID | Retrieval |
|---:|---|---|
| 1 | `01-limb-directions` | Choose northward for the upper limb and southward for the deep limb |
| 2 | `02-pathway-order` | Tap upper south → upper north → deep north → deep south |

Both cards use the same labelled Atlantic latitude–depth section. The first uses
two explicit direction choices; the second uses four selectable waypoints with
Undo/Clear. The front does not reveal a required stage count. The back overlays
the warm upper limb, sinking transition, cool deep return, arrows, and ordered
waypoints.

This replaces four unreviewed freehand notes:

- `01-upper-limb`
- `02-sinking-limb`
- `03-deep-return-limb`
- `04-complete-pathway`

The replacement is deliberately smaller because those four traces decomposed one
simple causal pathway into awkward motor tasks. Direction choice plus sequence
tests the intended model directly.

## Fairness boundary

- broad zonally integrated teaching paths, not exact local currents;
- no forecasts, transport measurements, tipping thresholds, or climate projection;
- no assertion that one parcel follows a single global conveyor loop;
- no water-mass-name or exact-depth memorization;
- no global Indo-Pacific return pathway.

## Rollout record

The guarded 2026-08-06 update deleted only the four exact old AMOC notes, all of
which still had zero reviews, and installed the two new notes under
`Process::GeoTrainer QA::Physical::Ocean Currents::3 Learn Atlantic Overturning`.
All retained GeoTrainer scheduling was unchanged; no sync was performed. Rollback
exports and the verification report were captured locally under the timestamped
`20260806T181704-0700-physical-redesign` recovery directory. Live snapshots are
private local artifacts and are no longer stored in Git.

## Sources

- [NOAA 2024 AMOC state-of-the-science fact sheet](https://doi.org/10.25923/pav0-be22)
- [NOAA GFDL: AMOC decadal variability and predictability](https://www.gfdl.noaa.gov/amoc-decadal-predictability/)
- [NOAA Ocean Service: What is the AMOC?](https://oceanservice.noaa.gov/facts/amoc.html)
- [NOAA Ocean Service: Global conveyor belt](https://oceanservice.noaa.gov/facts/conveyor.html)
