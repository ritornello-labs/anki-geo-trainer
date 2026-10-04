# Accepted geography concepts

These are the accepted September 2026 concept sources, imported from the
world-geography-concepts source revision `a3f9055`. They supplement the interactive
map tasks in the public GeoTrainer components. The 17 semantic families produce
311 notes / 1,514 cards; the membership drill adds 59 notes/cards. The full edition
uses exactly the same objects as the components.

`deck-identities.json` freezes the original family APKG deck IDs. Public deck names
are assigned after those identities are selected. Model IDs and note GUIDs retain
the existing family generator's stable definitions. These files contain no live
collection export or private scheduling data.

## Source material and licensing

- Natural Earth base and physical-region data are public domain:
  <https://www.naturalearthdata.com/about/terms-of-use/>. Maps use the project's
  own plate-carrée projection, with locally generated highlights and locators.
- Biome distribution geometry comes from RESOLVE Ecoregions 2017, CC BY 4.0:
  <https://ecoregions.world/>. Biome maps combine the accepted ecoregion classes.
- Köppen distribution maps use Beck and colleagues' Köppen–Geiger v2 1991–2020
  maps, CC BY 4.0, via Wikimedia Commons. See `koppen-provenance.json` for each
  source page, direct source URL, author list and hashes. The published PNGs crop
  away titles, legends and source bands; the E/ET/EF overlays use the accepted
  accent-red treatment so the polar classes remain visible. Source publication:
  <https://doi.org/10.1038/s41597-023-02549-6>.
- The biome photos retain individual Wikimedia Commons author, source and license
  links in the card's gallery. Their manifest is
  `families/research/biome-photos.json`; the original license of each image applies,
  including CC BY-SA where stated. Media are not relicensed as project code.
- Concept research and definitions reference Wikipedia pages in each note and
  research file. Wikipedia-derived prose remains under CC BY-SA 4.0 where
  applicable: <https://creativecommons.org/licenses/by-sa/4.0/>.
- Tectonic concepts and maps use Peter Bird’s PB2002 plate/boundary model via
  Hugo Ahlenius / Nordpil’s conversion, under the Open Data Commons Attribution
  License 1.0: <https://github.com/fraxen/tectonicplates>. Any TUBS base map
  identified in `source-media.csv` retains CC BY-SA 3.0. Retain those sources and
  licenses when distributing the tectonic pack.

`source-media.csv` preserves the source catalog; it includes historical assets
that are not all used by these families. The package builder includes only media
referenced by the selected accepted cards and fails if an explicit image is missing.

The 21 Köppen PNGs are committed here so rebuilding does not depend on a temporary
v1 raster staging directory. `koppen-provenance.json` documents the October 4
restoration from the recorded upstream SVGs. No personal collection was accessed.

Support continued development: [ritornello.dev/support](https://ritornello.dev/support).
