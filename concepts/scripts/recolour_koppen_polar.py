#!/usr/bin/env python3
"""Recolour the polar Koppen distribution maps so the class is actually visible.

The upstream Koppen-Geiger v2 rasters paint every class in its standard
palette colour. For the polar group those colours are greys -- ET is
(178,178,178), EF and E around (102,102,102) -- which on a grey basemap means
the ET map looks completely empty and the EF/E maps read as a shadow. A
rendered-card pass caught it: three of the 21 distribution cards showed a
prompt with nothing on it.

The class overlay is isolated without guessing: the per-pixel median across
all class maps is the basemap (each map differs from the others only where its
own class is painted), so anything differing from that median is overlay. The
overlay is then repainted in the deck's accent red, keeping its own lightness
so coastlines inside the class stay legible.

Inputs and outputs are the staged media files the deck already references.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "families" / "data" / "koppen.json"
#: Repaint these codes only; every other class already has a colour of its own.
POLAR = ("E", "ET", "EF")
ACCENT = (214, 45, 24)
#: Ignore near-identical pixels: JPEG-ish noise in the upstream rasters.
DIFF_THRESHOLD = 18


def median_basemap(paths: list[Path], size: tuple[int, int]) -> Image.Image:
    """Per-pixel median across every class map, which is the shared basemap."""
    stacks = [Image.open(p).convert("RGB").crop((0, 0, *size)).getdata() for p in paths]
    out = Image.new("RGB", size)
    out.putdata([
        (
            int(statistics.median(px[i][0] for px in row)),
            int(statistics.median(px[i][1] for px in row)),
            int(statistics.median(px[i][2] for px in row)),
        )
        for i, row in [(i, stacks) for i in range(size[0] * size[1])]
    ])
    return out


def recolour(path: Path, base: Image.Image, size: tuple[int, int]) -> tuple[Path, float]:
    im = Image.open(path).convert("RGB").crop((0, 0, *size))
    src, ref = list(im.getdata()), list(base.getdata())

    # Raw "differs from the basemap" also fires along every coastline and
    # border, because those hairlines antialias slightly differently in each
    # source raster. A class region is an AREA, so open the mask (erode then
    # dilate) to drop structures a couple of pixels wide and keep the regions.
    mask = Image.new("L", size)
    mask.putdata([255 if sum(abs(a - b) for a, b in zip(px, bp)) > DIFF_THRESHOLD else 0
                  for px, bp in zip(src, ref)])
    mask = mask.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5))

    out = []
    painted = 0
    for px, m in zip(src, mask.getdata()):
        if m:
            # Keep relative lightness so borders inside the class stay visible.
            k = (sum(px) / 3) / 255.0 * 0.45 + 0.55
            out.append(tuple(min(255, int(c * k)) for c in ACCENT))
            painted += 1
        else:
            out.append(px)
    im.putdata(out)
    im.save(path, "PNG", optimize=True)
    return path, painted / len(src) * 100


def main() -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    media = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if media is None or not media.is_dir():
        raise SystemExit("usage: recolour_koppen_polar.py <media-dir>")
    files = {c["code"]: media / c["distribution_map"]
             for c in data["concepts"] if c.get("distribution_map")}
    missing = [c for c, p in files.items() if not p.exists()]
    if missing:
        raise SystemExit(f"missing distribution maps for: {missing}")

    size = (1582, 770)
    base = median_basemap(list(files.values()), size)
    for code in POLAR:
        _, pct = recolour(files[code], base, size)
        print(f"  {code:3s} repainted {pct:5.2f}% of the map")
    return 0


if __name__ == "__main__":
    sys.exit(main())
