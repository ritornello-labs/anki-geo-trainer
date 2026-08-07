# Atmospheric circulation curriculum design

Status: redesigned batch built, cross-engine verified, and staged for manual QA
on 2026-08-06.

## Curriculum brief

Atmospheric circulation contains distinct spatial retrieval problems: overturning
cells in a vertical cross-section, pressure belts by latitude, horizontal prevailing
winds, high-altitude jet corridors, season-reversing monsoons, and coupled Pacific
ocean–atmosphere states. GeoTrainer gives each representation its own interaction.
Daily weather remains out of scope because a fixed route would teach false precision.

## Concept map

```text
unequal solar heating + Earth rotation
  ├─ paired Hadley, Ferrel, and Polar cells
  ├─ equatorial, subtropical, subpolar, and polar pressure belts
  ├─ trade winds, westerlies, and polar easterlies
  └─ subtropical and polar-front jet corridors

seasonal heating contrast
  └─ summer/winter South Asian monsoon winds
       └─ reversing northern Indian Ocean currents

equatorial Pacific ocean–atmosphere coupling
  ├─ neutral state
  ├─ El Niño
  └─ La Niña
```

## Implemented note types

### 1. `GeoTrainer Trace Cell — Atmospheric Circulation` (3 cards)

Hadley, Ferrel, and Polar cells are each retrieved as a **paired hemispheric
system** on one curved pole-to-pole latitude–altitude cross-section. The learner
starts at both marked surface points and traces two directed loops. This makes the
global symmetry visible and removes the repetitive six-card hemisphere split.

### 2. `GeoTrainer Place Belt — Atmospheric Circulation` (4 cards)

The learner taps every idealized latitude band occupied by the ITCZ/equatorial
low, subtropical highs, subpolar lows/polar fronts, or polar highs. The front does
not reveal how many bands are required. Undo and Clear make accidental taps
recoverable; the back reveals broad accepted bands rather than thin lines.

### 3. `GeoTrainer Trace Wind — Prevailing Winds` (6 cards)

Northeast/southeast trades, northern/southern westerlies, and northern/southern
polar easterlies use a full world map. Grading checks the correct broad latitude
belt and flow direction, not distance to one arbitrary exemplar polyline. The back
shows the accepted belt, so a scientifically reasonable stroke is not marked Hard
merely for differing by hundreds of kilometres from a schematic route.

### 4. `GeoTrainer Trace Jet — Jet Streams` (4 cards)

Northern/southern subtropical and polar-front jets use broad latitude corridors
and schematic meanders. The cards explicitly avoid implying a fixed daily path.

### 5. `GeoTrainer Trace Seasonal Wind — South Asian Monsoon` (2 cards)

Summer and winter low-level monsoon flow is traced on a **full world map**, so the
regional system is learned in global context. Each prompt names the boreal season
and month range; route and direction remain forgiving but meaningful.

### 6. `GeoTrainer Trace Seasonal Current — Indian Ocean Monsoon Currents` (4 cards)

Summer/winter Somali Current and Southwest/Northeast Monsoon Current cards use a
northern Indian Ocean map. Season and month range are explicit, and the reversed
seasonal route fails.

### 7. `GeoTrainer Compare ENSO States — Equatorial Pacific ENSO` (4 cards)

Neutral, El Niño, and La Niña each have a labelled equatorial-Pacific plan view
paired with a depth section. A fourth comparison card places all three states
together. The diagrams jointly retrieve trade-wind strength, warm-pool position,
rainfall focus, thermocline tilt, and eastern-Pacific upwelling. These are state
comparison cards rather than misleading fixed line traces.

The atmospheric/seasonal core contains **23 cards** (3 cells + 4 belts + 6 winds +
4 jets + 2 monsoon winds + 4 monsoon currents). ENSO adds **4 coupled-system
cards** in its own scope.

## Selection ledger

| Decision | Status | Reason |
|---|---|---|
| Paired three-cell model | Included | Shows global symmetry with less repetitive retrieval |
| Global pressure belts | Included | Explains ascent, descent, deserts, and storm belts without leaking target count |
| Prevailing wind belts | Included | Strong map-direction retrieval; grades the belt, not one arbitrary line |
| Subtropical and polar-front jets | Included | Major upper-air circulation, represented as variable corridors |
| South Asian monsoon winds | Included | Paired seasonal routes on a world map |
| Northern Indian Ocean monsoon currents | Included | Four explicit season-specific surface routes |
| Neutral / El Niño / La Niña | Included | A paired plan/depth schematic captures coupled state differences honestly |
| Atlantic overturning | Included separately | Direction-choice and pathway-order drills use a latitude–depth section |
| Seasonal ITCZ migration | Deferred | Worth adding only with a clear January-versus-July comparison exercise |
| Sea/land and mountain/valley breezes | Outside GeoTrainer | Local diagram retrieval, not geographic placement |
| Cyclone/anticyclone flow | Outside GeoTrainer | Better as hemisphere-specific weather-system diagrams |
| Daily weather maps | Excluded | Transient observations are not stable geographic facts |

## Rollout record

1. The original 26-card atmospheric/seasonal batch was installed on 2026-07-31
   and moved to `Process::GeoTrainer QA` on 2026-08-05.
2. The 2026-08-06 redesign replaced six unreviewed hemisphere-specific cell cards
   with three paired cards, improved pressure/wind/monsoon interactions, and added
   four ENSO cards.
3. The guarded live update left **29 physical-system cards** in the QA tree when
   combined with the two-card AMOC redesign. It preserved scheduling on every
   retained card, found no filtered-deck collision, and performed no sync.

## Sources for the model

- [Met Office: Global circulation patterns](https://weather.metoffice.gov.uk/learn-about/weather/atmosphere/global-circulation-patterns)
- [Met Office: What is the jet stream?](https://weather.metoffice.gov.uk/learn-about/weather/types-of-weather/wind/what-is-the-jet-stream)
- [NOAA NESDIS: What is a monsoon?](https://www.nesdis.noaa.gov/about/k-12-education/severe-weather/what-monsoon)
- [NOAA PMEL: What is El Niño?](https://www.pmel.noaa.gov/elnino/what-is-el-nino)
- [NOAA CPC: ENSO cycle schematic](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensocycle/enso_schem.shtml)
- [NOAA CPC: ENSO winds](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensocycle/cycle_winds_body.html)
- [NOAA repository: *Observations of the Somali Current during 1970*](https://repository.library.noaa.gov/view/noaa/59095)
- [NOAA repository: *Circulation in the northern Indian Ocean during the northeast monsoon*](https://repository.library.noaa.gov/view/noaa/45610)
