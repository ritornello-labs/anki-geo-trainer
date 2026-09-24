# Physical geography foundations

Status: six-card QA prototype built on 2026-09-23. It is not an accepted
curriculum, not in the live collection, and not included in the combined
release APKG. The previous 29-card physical-systems batch remains untouched in
`Process::GeoTrainer QA`.

## Learning contract

Help a general-geography learner explain and apply broad air, ocean, seasonal,
and Pacific-coupling patterns. The learner will inspect cards for QA now, not
study them. Only after acceptance will a prerequisite-first deck be merged into
GeoTrainer and introduced slowly for actual learning.

The live collection contains extensive place-map exposure but does not establish
mastery of physical mechanisms. The 29 staged physical-system cards have no
reviews. Searches for dedicated Coriolis, ITCZ, upwelling, and thermocline
definitions found no reliable acquired substrate. Treat these as new material;
do not use a raw text-search hit as evidence that a prerequisite is learned.

## Prerequisite route

```text
latitude and ocean/land orientation
  -> uneven heating -> rising/sinking air -> broad rain tendency
  -> equatorward air + rotational deflection -> trade-wind direction
  -> wind-driven surface movement -> coastal upwelling
  -> seasonal land/ocean heating -> South Asian monsoon flow
  -> usual Pacific trades -> western warm pool / cooler eastern surface
  -> weaker trades -> eastern warming and reduced cold-water upwelling
```

This is a teaching route, not a claim that every mechanism can be reduced to
the preceding arrow. In particular, the monsoon and ENSO have more than one
feedback; the first pass teaches only the robust broad pattern.

## QA prototype

Each note has one response, a compact purpose-built schematic, and the same
diagram and choices on the back. Choice labels distinguish `You ✓`, `You ✕`,
and `✓ Correct` in addition to color. No diagram claims a fixed daily jet,
pressure line, or current path. Each back carries a source link.

| Order / ID | Retrieval target | Prior support | Source |
|---|---|---|---|
| `01-equatorial-ascent` | Choose the broad latitude where rising air and frequent rain are likelier than near 30° N | Plain latitude orientation on diagram | [Met Office](https://weather.metoffice.gov.uk/learn-about/weather/atmosphere/global-circulation-patterns) |
| `02-northern-trades` | Predict the westward bend of equatorward northern-hemisphere air | `01` and shown north/equator orientation | [Met Office](https://weather.metoffice.gov.uk/learn-about/weather/atmosphere/global-circulation-patterns) |
| `03-coastal-upwelling` | Infer replacement water when surface water moves offshore | Surface/depth and coast shown on diagram | [NOAA](https://oceanservice.noaa.gov/facts/upwelling.html) |
| `04-south-asian-summer` | Predict broad summer ocean-to-land moist flow | Land/ocean orientation shown on diagram | [NOAA NESDIS](https://www.nesdis.noaa.gov/about/k-12-education/severe-weather/what-monsoon) |
| `05-neutral-pacific` | Predict where usual trades accumulate warm surface water | `02` plus west/east orientation shown on diagram | [NOAA PMEL](https://www.pmel.noaa.gov/elnino/what-is-el-nino) |
| `06-weak-trades` | Predict eastern-Pacific surface warming relative to the neutral baseline | `05` | [NOAA PMEL](https://www.pmel.noaa.gov/elnino/what-is-el-nino) |

The pilot intentionally samples six *inference types* but currently uses one
choice-grid input family. Elvis's QA should test whether the diagrams make the
inferences quick and fair, and whether the answer layout supports a fast audit.
It should not be treated as a successful study trial merely because a prompt is
answerable when inspected once.

## Full-module design still to build

- Add explicit orientation and vocabulary retrievals where the pilot exposes a
  gap. Avoid a hidden assumption that a term mentioned in an old card is known.
- Add a small number of distinct wind, rainfall, gyre, boundary-current, and
  seasonal-transfer problems. Use the existing named-current trace deck for
  route practice instead of duplicating it.
- Teach the neutral Pacific before El Niño and La Niña. Test each change with a
  small prediction and finish with one integrated state diagnosis. Do not make
  mirrored five-variable worksheets.
- Represent jet streams as variable high-altitude corridors rather than fixed
  up/down arrows. Keep AMOC as upper/deep direction interpretation; retire
  memorized waypoint order. Consider the Somali Current seasonal pair as an
  optional application only after the monsoon mechanism is established.
- Use geographic transfer cases and explicit limits: climate averages are not
  daily forecasts, and an idealized diagram is not an exact route or boundary.

No target card count is fixed. A rough design envelope is 30–40 core
retrievals, with optional applications only when each earns its review cost.

## Rollout gate

1. Review the six local front/back renders and their factual claims. Fix any
   unfair cue, visual ambiguity, or incorrect causal wording.
2. Stage the prototype in a distinct `Process` QA subdeck only after the
   workspace's open full-sync/schema items are reconciled. Import must be
   snapshot-backed, exact-ID verified, and must not touch the existing 29 QA
   cards. Do not sync or grade for Elvis.
3. Elvis may inspect a sample or all cards as **QA**, not as scheduled study.
   Record his verdicts as design evidence. Expand only after the prototype
   interaction and content earn approval.
4. Complete independent content/prerequisite and cross-client verification
   before eventual study delivery. Merge into GeoTrainer and publish only after
   the full module, not merely the prototype, is accepted.
