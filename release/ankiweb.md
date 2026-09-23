---
title: "GeoTrainer: Interactive Geography (Borderless Recall)"
tags: geography maps interactive world countries rivers deserts mountains
support_url: https://github.com/ritornello-labs/anki-geo-trainer
---

Sheppard-Software-style **interactive** geography practice, right inside Anki — but
with the internal borders hidden, so it's genuine spatial recall, not matching a
labelled shape. Name the region under a dot, drag a silhouette to where it belongs,
sketch it in place on a blank parent map, draw it without any map, trace a
river/current route, or place an island archipelago on a rotating globe. The card grades
your answer and suggests a button — you still press Anki's own answer keys, so
scheduling stays 100% Anki.

Works on **Desktop, AnkiMobile (iOS) and AnkiDroid** — all the map code is inlined
into the note templates, so there are no media downloads and nothing to configure.
Light and dark mode included.

## See it in Anki

Each animation is a short capture from Anki. Select it for the full-resolution MP4;
the still-image link works when animation is unavailable.

**Place a silhouette.** Drag the Libyan Desert onto a borderless map and see the
placement score. [![GeoTrainer Place card animation](https://ritornello.dev/media/ankiweb/2026-09-23-v5/geo-trainer/place.gif)](https://ritornello.dev/media/ankiweb/2026-09-23-v5/geo-trainer/place.mp4)
[Still: graded placement](https://ritornello.dev/media/ankiweb/2026-09-23-v5/geo-trainer/place-back.png)

**Sketch in context.** Draw Italy on the blank Europe map, then compare shape and
position. [![GeoTrainer Sketch card animation](https://ritornello.dev/media/ankiweb/2026-09-23-v5/geo-trainer/sketch.gif)](https://ritornello.dev/media/ankiweb/2026-09-23-v5/geo-trainer/sketch.mp4)
[Still: sketch feedback](https://ritornello.dev/media/ankiweb/2026-09-23-v5/geo-trainer/sketch-back.png)

**Draw from memory.** Use a blank canvas, then see your Italy outline overlaid on
the true one. [![GeoTrainer Draw card animation](https://ritornello.dev/media/ankiweb/2026-09-23-v5/geo-trainer/draw.gif)](https://ritornello.dev/media/ankiweb/2026-09-23-v5/geo-trainer/draw.mp4)
[Still: outline overlay](https://ritornello.dev/media/ankiweb/2026-09-23-v5/geo-trainer/draw-back.png)

**Trace a river.** Draw the Amazon's course and reveal the distance-based result.
[![GeoTrainer Amazon trace animation](https://ritornello.dev/media/ankiweb/2026-09-23-v5/geo-trainer/river.gif)](https://ritornello.dev/media/ankiweb/2026-09-23-v5/geo-trainer/river.mp4)
[Still: river feedback](https://ritornello.dev/media/ankiweb/2026-09-23-v5/geo-trainer/river-back.png)

**Trace a current and its direction.** The Gulf Stream attempt earns Good for
route and direction. [![GeoTrainer Gulf Stream trace animation](https://ritornello.dev/media/ankiweb/2026-09-23-v5/geo-trainer/current.gif)](https://ritornello.dev/media/ankiweb/2026-09-23-v5/geo-trainer/current.mp4)
[Still: current feedback](https://ritornello.dev/media/ankiweb/2026-09-23-v5/geo-trainer/current-back.png)

**Place an island on a globe.** Draw an ellipse around Iceland; the card grades
coverage, center, and footprint. [![GeoTrainer globe placement animation](https://ritornello.dev/media/ankiweb/2026-09-23-v5/geo-trainer/globe.gif)](https://ritornello.dev/media/ankiweb/2026-09-23-v5/geo-trainer/globe.mp4)
[Still: island placement feedback](https://ritornello.dev/media/ankiweb/2026-09-23-v5/geo-trainer/globe-back.png)

**Identify a map dot.** Recall the country before revealing Albania on the
borderless Europe map. [![GeoTrainer Which-country animation](https://ritornello.dev/media/ankiweb/2026-09-23-v5/geo-trainer/point.gif)](https://ritornello.dev/media/ankiweb/2026-09-23-v5/geo-trainer/point.mp4)
[Still: revealed country](https://ritornello.dev/media/ankiweb/2026-09-23-v5/geo-trainer/point-back.png)

## Task families

- **Which one?** — a dot lands inside a region (a different spot each review) on a
  **borderless** map; recall which region it is.
- **Place** — drag the region's silhouette onto the borderless map to where it
  belongs — there's no labelled slot to snap into.
- **Sketch** — draw a country on its blank continent, a state/province on its blank
  country, or a continent on the blank world. The map supplies geographic context but
  no internal borders; shape, position, and scale all count.
- **Draw** — sketch the outline from memory; scored on both boundary faithfulness
  and area overlap, so a right-size wrong-shape blob (a lazy circle) fails while an
  honest freehand attempt passes.
- **Trace** (rivers) — trace a major river's course over a world map; graded by how
  closely your line follows the real one. Starts on the *full* world map (no hint
  where it is) — tap **＋** to zoom in and trace precisely.
- **Trace** (ocean currents) — trace from origin to destination. Your stroke ends
  in an arrow; the back reveals a forgiving route corridor and direction. Drawing
  the right route backwards is still wrong.
- **Atmospheric circulation** — trace paired hemispheric Hadley, Ferrel, and Polar
  loops on a curved latitude–altitude cross-section, place global pressure belts
  without a count hint, and trace prevailing winds in forgiving broad belts plus
  broad jet-stream corridors.
- **Seasonal circulation** — paired summer/winter monsoon-wind and northern Indian
  Ocean current cards name the boreal season and month range explicitly; tracing the
  other season's direction is wrong.
- **Atlantic overturning** — choose upper/deep limb directions and order the AMOC
  pathway on a labelled Atlantic latitude–depth section.
- **ENSO** — compare neutral, El Niño, and La Niña through Pacific plan/depth
  schematics showing winds, warm pool, rainfall, thermocline, and upwelling.
- **Globe placement** — rotate a randomly oriented globe and draw a movable, resizable
  ellipse around a named island or archipelago; coverage, center, and footprint all count.

All drawing surfaces support **zoom & pan**: +/− buttons and mouse-wheel to zoom, and a
**✋ Move** toggle that turns a drag into a pan so you can reposition a zoomed-in view
onto the right part of the world. On a phone you can also pinch-zoom and two-finger
pan — fine work is easy even on a small screen.

## What's covered

Continents (countries): **Europe, Africa, Asia, South America, North America,
Oceania**. Country subdivisions: **US states, Brazil, India, Russia, China, Canada,
Australia, Argentina, Mexico, Indonesia**. Physical: **mountain ranges** and
**deserts** (place or sketch them over the continents), **major lakes** (identify
and place), **tectonic plates** (identify, place, and sketch), **major rivers** (trace the
course), **ocean currents** (trace route + direction), and **atmospheric circulation**
(paired cells, pressure belts, winds, jets, and season-aware monsoon flows). A
depth-aware Atlantic cross-section teaches the **Atlantic Meridional Overturning
Circulation**, and an equatorial-Pacific scope compares neutral, **El Niño**, and
**La Niña** states. A 67-card **Islands** scope adds globe placement for island countries
and dispersed archipelagos. And a **Continents**
deck: first sketch each one on a blank world map, then
draw its silhouette from memory without context.

Cards are **tagged by skill and scope** (`geotrainer::skill::…`,
`geotrainer::scope::…`) so you can build your own study path with saved searches and
filtered decks — see the GitHub README for ready-made recipes.

## Source & issues

GitHub: [https://github.com/ritornello-labs/anki-geo-trainer](https://github.com/ritornello-labs/anki-geo-trainer)

Maps are rendered primarily from [Natural Earth](https://www.naturalearthdata.com/)
public-domain data. Tectonic plates use the PB2002-derived GeoJSON credited in the
repository's data-source notes; current routes are schematic adaptations of NOAA
education maps. Built with the open-source generator in the repository above.
