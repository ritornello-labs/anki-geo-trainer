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
into the note templates, with required map media bundled in the package.
Light and dark mode included.

## See it in Anki

![GeoTrainer place-the-shape review](https://ritornello.dev/media/ankiweb/2026-08-06-v4/geo-trainer/preview.gif)

![Place the Libyan Desert on a borderless map](https://ritornello.dev/media/ankiweb/2026-08-06-v4/geo-trainer/gallery-01.png)

![Trace the Amazon from memory](https://ritornello.dev/media/ankiweb/2026-08-06-v4/geo-trainer/gallery-02.png)

[3.75-second Place MP4](https://ritornello.dev/media/ankiweb/2026-08-06-v4/geo-trainer/place.mp4)

[3-second Amazon Trace MP4](https://ritornello.dev/media/ankiweb/2026-08-06-v4/geo-trainer/river.mp4)

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
- **Globe placement** — rotate a randomly oriented globe and draw a movable, resizable
  ellipse around a named island or archipelago; coverage, center, and footprint all count.

All drawing surfaces support **zoom & pan**: +/− buttons and mouse-wheel to zoom, and a
**✋ Move** toggle that turns a drag into a pan so you can reposition a zoomed-in view
onto the right part of the world. On a phone you can also pinch-zoom and two-finger
pan — fine work is easy even on a small screen.

## What's covered

The full edition contains **2,651 notes / 2,673 cards** across the accepted families. World countries covers the six continental country scopes and continent silhouettes. Subdivision packs cover the United States, Brazil, India, Russia, China, Canada, Australia, Argentina, Mexico, and Indonesia. Physical geography includes rivers, mountain ranges, deserts, lakes, surface ocean currents, plateaus, grasslands, and peninsulas. Plate tectonics covers major and minor plates and named boundaries. Islands & archipelagos contains 67 globe-placement cards. Reference lines & time covers parallels, meridians, the date line, and time-zone geography.

Choose a focused pack or the full edition. Shared scopes retain the same note GUIDs, note-type IDs, and leaf deck IDs, so importing an overlapping pack updates the same notes.

Cards are **tagged by skill and scope** (`geotrainer::skill::…`,
`geotrainer::scope::…`) so you can build your own study path with saved searches and
filtered decks — see the GitHub README for ready-made recipes.

## Source & issues

GitHub: [https://github.com/ritornello-labs/anki-geo-trainer](https://github.com/ritornello-labs/anki-geo-trainer)

Maps are rendered primarily from [Natural Earth](https://www.naturalearthdata.com/)
public-domain data. Tectonic plates use the PB2002-derived GeoJSON credited in the
repository's data-source notes; current routes are schematic adaptations of NOAA
education maps. Built with the open-source generator in the repository above.

Support continued development: [ritornello.dev/support](https://ritornello.dev/support).
