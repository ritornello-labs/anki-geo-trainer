---
title: "GeoTrainer: Interactive Geography (Borderless Recall)"
tags: geography maps interactive world countries rivers deserts mountains
support_url: https://github.com/ritornello-labs/anki-geo-trainer
---

Sheppard-Software-style **interactive** geography practice, right inside Anki — but
with the internal borders hidden, so it's genuine spatial recall, not matching a
labelled shape. Name the region under a dot, drag a silhouette to where it belongs,
sketch it in place on a blank parent map, draw it without any map, or trace a
river/current route. The card grades
your answer and suggests a button — you still press Anki's own answer keys, so
scheduling stays 100% Anki.

Works on **Desktop, AnkiMobile (iOS) and AnkiDroid** — all the map code is inlined
into the note templates, so there are no media downloads and nothing to configure.
Light and dark mode included.

## See it in Anki

![GeoTrainer place-the-shape review](https://ritornello.dev/media/ankiweb/2026-08-05-v3/geo-trainer/preview.gif)

![Place Alabama on a borderless map](https://ritornello.dev/media/ankiweb/2026-08-05-v3/geo-trainer/gallery-01.png)

![Trace the Amazon from memory](https://ritornello.dev/media/ankiweb/2026-08-05-v3/geo-trainer/gallery-02.png)

[Full-resolution Place MP4](https://ritornello.dev/media/ankiweb/2026-08-05-v3/geo-trainer/place.mp4)

[Full-resolution Amazon Trace MP4](https://ritornello.dev/media/ankiweb/2026-08-05-v3/geo-trainer/river.mp4)

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
- **Atmospheric circulation** — trace the six overturning cells on a
  latitude–altitude cross-section, place global pressure belts, and trace prevailing
  winds and broad jet-stream corridors.
- **Seasonal circulation** — paired summer/winter monsoon-wind and northern Indian
  Ocean current cards name the boreal season and month range explicitly; tracing the
  other season's direction is wrong.

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
(cells, pressure belts, winds, jets, and season-aware monsoon flows). A depth-aware
Atlantic cross-section adds the upper, sinking, and deep-return limbs of the **Atlantic
Meridional Overturning Circulation**. And a **Continents**
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
