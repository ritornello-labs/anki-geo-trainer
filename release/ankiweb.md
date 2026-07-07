---
title: "GeoTrainer — Interactive Geography (borderless recall)"
tags: geography maps interactive world countries rivers deserts mountains
support_url: https://github.com/elvis-sik/anki-geo-trainer
---

# GeoTrainer — Interactive Geography

Sheppard-Software-style **interactive** geography practice, right inside Anki — but
with the internal borders hidden, so it's genuine spatial recall, not matching a
labelled shape. Name the region under a dot, drag a silhouette to where it belongs,
sketch a country's outline from memory, or trace a river's course. The card grades
your answer and suggests a button — you still press Anki's own answer keys, so
scheduling stays 100% Anki.

Works on **Desktop, AnkiMobile (iOS) and AnkiDroid** — all the map code is inlined
into the note templates, so there are no media downloads and nothing to configure.
Light and dark mode included.

## Task families

- **Which one?** — a dot lands inside a region (a different spot each review) on a
  **borderless** map; recall which region it is.
- **Place** — drag the region's silhouette onto the borderless map to where it
  belongs — there's no labelled slot to snap into.
- **Draw** — sketch the outline from memory; scored on both boundary faithfulness
  and area overlap, so a right-size wrong-shape blob (a lazy circle) fails while an
  honest freehand attempt passes.
- **Trace** (rivers) — trace a major river's course over a world map; graded by how
  closely your line follows the real one. Starts on the *full* world map (no hint
  where it is) — tap **＋** to zoom in and trace precisely.

Drawing surfaces support **zoom & pan**: +/− buttons and mouse-wheel to zoom, and a
**✋ Move** toggle that turns a drag into a pan so you can reposition a zoomed-in view
onto the right part of the world. On a phone you can also pinch-zoom and two-finger
pan — fine work is easy even on a small screen.

## What's covered

Continents (countries): **Europe, Africa, Asia, South America, North America,
Oceania**. Country subdivisions: **US states, Brazil, India, Russia, China, Canada,
Australia, Argentina, Mexico, Indonesia**. Physical: **mountain ranges** and
**deserts** (place them over the continents), and **major rivers** (trace the
course). And a **Continents** deck: draw the whole silhouette of South America,
North America, or Africa from memory.

Cards are **tagged by skill and scope** (`geotrainer::skill::…`,
`geotrainer::scope::…`) so you can build your own study path with saved searches and
filtered decks — see the GitHub README for ready-made recipes.

## Source & issues

GitHub: [https://github.com/elvis-sik/anki-geo-trainer](https://github.com/elvis-sik/anki-geo-trainer)

Maps are rendered from [Natural Earth](https://www.naturalearthdata.com/) public-domain
data. Built with the open-source generator in the repository above.
