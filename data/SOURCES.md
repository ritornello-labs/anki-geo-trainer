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
field and not navigational data. Four additional northern Indian Ocean cards are
explicitly season-specific: the summer/winter Somali Current and the Southwest/
Northeast Monsoon Currents. Their direction and month ranges were checked against:

- [NOAA Tides & Currents glossary](https://tidesandcurrents.noaa.gov/glossary.html)
- [NOAA repository: *Observations of the Somali Current during 1970*](https://repository.library.noaa.gov/view/noaa/59095)
- [NOAA repository: *Circulation in the northern Indian Ocean during the northeast monsoon*](https://repository.library.noaa.gov/view/noaa/45610)
- [NOAA/IndOOS observing-system report](https://www.pmel.noaa.gov/tao/drupal/disdel/doc/IndOOS_report_small.pdf)

The depth-aware follow-up represents the Atlantic Meridional Overturning
Circulation as a zonally integrated latitude–depth section rather than a flat
global conveyor route. Its upper, sinking, deep-return, and integrated pathways
were checked against:

- [NOAA 2024 AMOC state-of-the-science fact sheet](https://doi.org/10.25923/pav0-be22)
- [NOAA GFDL: AMOC decadal variability and predictability](https://www.gfdl.noaa.gov/amoc-decadal-predictability/)
- [NOAA Ocean Service: What is the AMOC?](https://oceanservice.noaa.gov/facts/amoc.html)

The Atlantic pathway ends at the deep South Atlantic boundary rather than
inventing a local upwelling limb. NOAA identifies mixing and upwelling in the
Southern Ocean and Indo-Pacific as part of the wider transformation back toward
upper-ocean waters. NOAA material produced by the United States government is
public domain.

## Atmospheric circulation

The cell, pressure-belt, prevailing-wind, and jet-stream cards are idealized
teaching models. Jet cards use broad schematic meanders rather than claiming a
fixed daily route. The South Asian monsoon-wind pair always names the boreal season
and month range.

- [Met Office: Global circulation patterns](https://weather.metoffice.gov.uk/learn-about/weather/atmosphere/global-circulation-patterns)
- [Met Office: What is the jet stream?](https://weather.metoffice.gov.uk/learn-about/weather/types-of-weather/wind/what-is-the-jet-stream)
- [NOAA JetStream: Global atmospheric circulations](https://prod-01-alb-www-noaa.woc.noaa.gov/jetstream/global/global-atmospheric-circulations)
- [NOAA NESDIS: What is the jet stream?](https://www.nesdis.noaa.gov/about/k-12-education/atmosphere/what-the-jet-stream)
- [NOAA NESDIS: What is a monsoon?](https://www.nesdis.noaa.gov/about/k-12-education/severe-weather/what-monsoon)
