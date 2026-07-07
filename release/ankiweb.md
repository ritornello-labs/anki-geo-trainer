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
- **Draw** — sketch the outline from memory; scored on whether you captured the real
  shape (a rough enclosing blob fails; an honest freehand attempt passes).
- **Trace** (rivers) — trace a major river's course over a world map; graded by how
  closely your line follows the real one. Starts on the *full* world map (no hint
  where it is) — pinch or tap **＋** to zoom in and trace precisely.

Drawing surfaces support **zoom & pan** (pinch / two-finger on mobile, +/− buttons
and mouse-wheel on desktop), so fine work is easy even on a phone.

## What's covered

Continents (countries): **Europe, Africa, Asia, South America, Oceania**.
Country subdivisions: **US states, Brazil, India, Russia, China, Canada, Australia,
Argentina, Mexico, Indonesia**. Physical: **mountain ranges** and **deserts** (name /
place / draw them over the continents), and **major rivers** (trace the course).

Cards are **tagged by skill and scope** (`geotrainer::skill::…`,
`geotrainer::scope::…`) so you can build your own study path with saved searches and
filtered decks — see the GitHub README for ready-made recipes.

## Source & issues

GitHub: [https://github.com/elvis-sik/anki-geo-trainer](https://github.com/elvis-sik/anki-geo-trainer)

Maps are rendered from [Natural Earth](https://www.naturalearthdata.com/) public-domain
data. Built with the open-source generator in the repository above.
