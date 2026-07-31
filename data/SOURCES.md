# GeoTrainer data sources

Generated bundles in `data/bundles/` are derived from the following sources.
Raw downloads in `data/raw/` are build inputs and are not committed.

## Natural Earth

Country, subdivision, land, river, mountain-range, desert, and lake geometry:

- [Natural Earth vector data](https://github.com/nvkelso/natural-earth-vector)
- License: public domain

GeoTrainer uses the 1:10m, 1:50m, and 1:110m GeoJSON layers named in
`scripts/build_bundle.py`.

## Tectonic plates

Major plate polygons:

- [fraxen/tectonicplates](https://github.com/fraxen/tectonicplates), a GeoJSON
  conversion by Hugo Ahlenius / Nordpil of Peter Bird's PB2002 plate model
- Original model: Peter Bird, “An updated digital model of plate boundaries,”
  *Geochemistry, Geophysics, Geosystems* 4(3), 2003
- Source database license: Open Database License (ODbL)

The curated `world-tectonic-plates` bundle is a derived database and retains the
source attribution and ODbL terms. GeoTrainer's generator code remains MIT-licensed.

## Ocean currents

The 34 ordered current centrelines are deliberately schematic study routes. The
curriculum closes the four named limbs of each of the five major subtropical
gyres, then adds major subpolar, equatorial, regional-throughflow, and
circumpolar branches. Route names and directions were checked against:

- [NOAA Ocean Service: Boundary Currents](https://oceanservice.noaa.gov/education/tutorial_currents/04currents3.html)
- [NOAA Tides & Currents glossary](https://tidesandcurrents.noaa.gov/glossary.html)
- [NOAA/AOML: Antarctic Circumpolar Current](https://www.aoml.noaa.gov/phod/altimetry/cvar/acc/index.php)
- [Australian Bureau of Meteorology: Ocean currents](https://www.bom.gov.au/resources/learn-and-explore/marine-knowledge-centre/ocean-currents)

They encode a memorable route and direction, not an instantaneous ocean-velocity
field and not navigational data. Season-reversing Somali/monsoon currents and
deep thermohaline circulation are intentionally deferred because they require
season-specific or depth-aware prompts. NOAA material produced by the United
States government is public domain.
