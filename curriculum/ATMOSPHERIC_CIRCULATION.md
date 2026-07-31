# Atmospheric circulation curriculum design

Status: design proposal; no atmospheric cards or note types are built yet.

## Curriculum brief

The useful target is not a flat list of “air currents.” Atmospheric circulation
contains several different spatial retrieval problems: overturning cells in a
vertical cross-section, pressure and convergence belts by latitude, horizontal
prevailing winds, and high-altitude jet corridors. GeoTrainer should teach those
with separate note types so every front makes the expected representation clear.

The first release should cover the stable idealized global model. Seasonal and
weather-dependent systems belong in later stages because an exact permanent route
would teach false precision.

## Concept map

```text
unequal solar heating + Earth rotation
  ├─ three-cell circulation in each hemisphere
  │    ├─ Hadley cell
  │    ├─ Ferrel cell
  │    └─ Polar cell
  ├─ rising/sinking and pressure belts
  │    ├─ ITCZ / equatorial low
  │    ├─ subtropical highs
  │    ├─ subpolar lows / polar front
  │    └─ polar highs
  ├─ prevailing surface winds
  │    ├─ northeast and southeast trade winds
  │    ├─ northern and southern westerlies
  │    └─ northern and southern polar easterlies
  └─ upper-level jets near cell boundaries
       ├─ subtropical jets
       └─ polar-front jets

stable idealized model
  └─ prerequisites for variable circulation
       ├─ seasonal ITCZ migration and monsoons
       ├─ Walker circulation and ENSO phases
       └─ regional/local circulations
```

## Proposed note types and first batch

### 1. `GeoTrainer Trace Cell — Atmospheric Circulation` (6 cards)

Front: a blank latitude-versus-altitude cross-section for one hemisphere and a
cell name. Trace the overturning loop in the correct direction.

Cards: Hadley, Ferrel, and Polar cells in each hemisphere. The back shows the
accepted broad loop, rising and sinking limbs, and direction arrows. Grading is
direction-aware, like ocean currents, but uses a closed-loop scorer rather than a
single origin-to-destination route.

Why separate it: a circulation cell is vertical motion plus horizontal return
flow. A flat world map cannot show that honestly.

### 2. `GeoTrainer Place Belt — Atmospheric Circulation` (4 cards)

Front: a blank pole-to-pole latitude strip. Place the named belt at its idealized
latitude or latitudes.

Cards: ITCZ/equatorial low, subtropical highs, subpolar lows/polar fronts, and
polar highs. Symmetric northern/southern targets are one retrieval unit when the
belt occurs in both hemispheres. The accepted target is a latitude band, not a
thin line.

### 3. `GeoTrainer Trace Wind — Prevailing Winds` (6 cards)

Front: a borderless world map with faint latitude guides and the wind-belt name.
Trace the generalized near-surface direction across a representative ocean basin.

Cards: northeast trades, southeast trades, northern westerlies, southern
westerlies, northern polar easterlies, and southern polar easterlies. The scorer
checks both corridor and direction while tolerating zonal variation.

### 4. `GeoTrainer Trace Jet — Jet Streams` (4 cards)

Front: a world map with broad latitude guides. Trace the named jet's generalized
west-to-east corridor.

Cards: northern/southern subtropical jets and northern/southern polar-front jets.
The answer must be shown as a wide, explicitly variable belt with a schematic
meander. It must not imply that the jet occupies a fixed daily path.

The first batch is therefore **20 cards across four purpose-built note types**.
It gives prerequisite closure: cell motion first, then pressure belts, surface
winds, and finally upper-level jets.

## Selection ledger

| Decision | Include/defer | Reason |
|---|---|---|
| Three-cell model, both hemispheres | Include | Stable organizing model and prerequisite for the other families |
| Global pressure/convergence belts | Include | Explains ascent, descent, deserts, and storm belts |
| Prevailing surface wind belts | Include | Strong map-direction retrieval and direct link to surface ocean gyres |
| Subtropical and polar-front jets | Include | Major upper-air circulation, but grade a broad variable corridor |
| Seasonal ITCZ migration | Defer to phase 2 | Needs month/season on the front and two target states |
| South Asian and other monsoons | Defer to phase 2 | Direction reverses seasonally; requires paired seasonal cards |
| Walker circulation / ENSO | Defer to phase 2 | Needs equatorial Pacific cross-sections for neutral, El Niño, and La Niña states |
| Sea/land and mountain/valley breezes | Defer outside GeoTrainer | Local diagram retrieval, not geographic placement on a world map |
| Cyclone/anticyclone flow | Defer outside GeoTrainer | Best learned as hemisphere-specific pressure-system diagrams |
| Daily weather maps | Exclude from a fixed deck | Routes are transient observations, not stable geographic facts |

## Phase-2 candidates

- **Season-paired monsoon trace**: the front always names region and season;
  summer and winter are separate cards with opposite low-level flow.
- **ITCZ migration compare**: place the mean January and July convergence zones
  on a world map, then reveal both together.
- **Walker circulation state**: direction-aware loop tracing in a Pacific
  longitude-versus-altitude cross-section for neutral conditions, El Niño, and
  La Niña.
- **Ocean–atmosphere bridge cards**: given one of the five subtropical gyres,
  identify the prevailing wind belts that drive its equatorward and poleward
  limbs. These are relationship cards, not additional line-tracing notes.

## Rollout plan

1. Prototype one Northern Hemisphere Hadley-cell card and one northeast-trades
   card to validate the cross-section and zonal-corridor scorers.
2. Calibrate faithful, wobbly, reversed, and wrong-belt attempts in Chromium,
   WebKit, disposable Desktop Anki, and AnkiDroid.
3. Build the 20-card stable global batch and study it before adding seasonal
   circulation.
4. Add phase 2 only after telemetry or study feedback shows which seasonal
   distinctions are worth their extra prompt complexity.

## Sources for the model

- [Met Office: Global circulation patterns](https://weather.metoffice.gov.uk/learn-about/weather/atmosphere/global-circulation-patterns)
- [Met Office: What is the jet stream?](https://weather.metoffice.gov.uk/learn-about/weather/types-of-weather/wind/what-is-the-jet-stream)
- [NOAA Ocean Service: Surface ocean currents](https://oceanservice.noaa.gov/education/tutorial_currents/04currents2.html)
