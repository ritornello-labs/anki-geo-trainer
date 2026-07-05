"""Pack a Natural Earth admin-1 layer into a compact, pre-projected scope bundle.

The interaction engine runs *inside* an Anki card and does its own hit-testing and
rendering, so it needs geometry client-side. Rather than ship raw lon/lat and project
in JS, we pre-project here into a clean regional pixel space (equirectangular with the
region's mean latitude as standard parallel, so the map isn't horizontally stretched),
simplify in that pixel space (sub-pixel tolerance => shared borders stay visually seamless),
and emit integer-ish coordinates. The engine then only has to scale the viewBox.

Output bundle shape (JSON):
    {
      "scope": "us-states",
      "title": "United States — States",
      "view": {"w": 1000, "h": 618, "kmPerUnit": 2.13},
      "regions": [
        {"id": "US-CA", "name": "California", "abbr": "CA",
         "c": [cx, cy],                 # projected centroid (for distance feedback)
         "rings": [[[x,y],...], ...]}   # exterior rings, projected px, y-down
      ]
    }

Distances reported by the engine are in projected units * kmPerUnit ~= great-circle km
near the region (good enough for "you were ~120 km off" feedback).
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import urllib.request
from pathlib import Path

from shapely.geometry import MultiPolygon, Polygon, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "ne_50m_admin_1_states_provinces.geojson"
RAW_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
    "geojson/ne_50m_admin_1_states_provinces.geojson"
)
OUT_DIR = ROOT / "data" / "bundles"

EARTH_KM_PER_DEG = 111.32


def ensure_raw() -> None:
    if RAW.exists():
        return
    RAW.parent.mkdir(parents=True, exist_ok=True)
    print(f"downloading {RAW_URL} -> {RAW}")
    with urllib.request.urlopen(RAW_URL) as resp, RAW.open("wb") as fh:
        shutil.copyfileobj(resp, fh)

# For the M0 spike: the contiguous lower 48 (+ nothing). Alaska and Hawaii need
# inset panels (own projection boxes) — deferred to M1.
EXCLUDE_NAMES = {"Alaska", "Hawaii"}


def load_us_states() -> list[dict]:
    ensure_raw()
    data = json.loads(RAW.read_text(encoding="utf-8"))
    out = []
    for feat in data["features"]:
        props = feat["properties"]
        if props.get("adm0_a3") != "USA":
            continue
        if props.get("type_en") != "State":  # drop DC (Federal District)
            continue
        if props.get("name") in EXCLUDE_NAMES:
            continue
        out.append(feat)
    return out


def make_projector(features: list[dict]):
    """Equirectangular projector fit to the features' bbox, standard parallel at
    the mean latitude. Returns (project, view) where project(lon,lat)->(x,y)."""
    lon_min = lat_min = math.inf
    lon_max = lat_max = -math.inf
    for feat in features:
        geom = shape(feat["geometry"])
        x0, y0, x1, y1 = geom.bounds
        lon_min, lat_min = min(lon_min, x0), min(lat_min, y0)
        lon_max, lat_max = max(lon_max, x1), max(lat_max, y1)

    lat0 = math.radians((lat_min + lat_max) / 2.0)
    cos0 = math.cos(lat0)

    # Scaled-degree space, y-down; then scale so width == target_w.
    x_span = (lon_max - lon_min) * cos0
    y_span = lat_max - lat_min
    target_w = 1000.0
    scale = target_w / x_span
    view_w = target_w
    view_h = y_span * scale
    km_per_unit = (1.0 / scale) * EARTH_KM_PER_DEG

    pad = 8.0  # px breathing room inside the viewBox

    def project(lon: float, lat: float) -> tuple[float, float]:
        x = (lon - lon_min) * cos0 * scale + pad
        y = (lat_max - lat) * scale + pad
        return x, y

    view = {
        "w": round(view_w + 2 * pad, 1),
        "h": round(view_h + 2 * pad, 1),
        "kmPerUnit": round(km_per_unit, 3),
    }
    return project, view


def project_geom(geom, project) -> MultiPolygon:
    polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    out = []
    for poly in polys:
        ext = [project(lon, lat) for lon, lat in poly.exterior.coords]
        out.append(Polygon(ext))  # holes dropped: irrelevant for locate/point tasks
    return unary_union(out) if len(out) > 1 else out[0]


def rings_of(geom) -> list[list[list[float]]]:
    polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    rings = []
    for poly in polys:
        coords = [[round(x, 1), round(y, 1)] for x, y in poly.exterior.coords]
        if len(coords) >= 4:
            rings.append(coords)
    return rings


def region_id(props: dict) -> str:
    iso = props.get("iso_3166_2") or ""
    return iso if iso else f"US-{props.get('postal', '??')}"


def build() -> dict:
    feats = load_us_states()
    project, view = make_projector(feats)

    regions = []
    for feat in feats:
        props = feat["properties"]
        projected = project_geom(shape(feat["geometry"]), project)
        # Simplify in pixel space; ~0.6px keeps shared borders visually seamless.
        simplified = projected.simplify(0.6, preserve_topology=True)
        rings = rings_of(simplified)
        if not rings:
            continue
        # Largest ring's representative point is a safe interior centroid label anchor.
        c = projected.representative_point()
        regions.append(
            {
                "id": region_id(props),
                "name": props["name"],
                "abbr": props.get("postal", ""),
                "c": [round(c.x, 1), round(c.y, 1)],
                "rings": rings,
            }
        )

    regions.sort(key=lambda r: r["name"])
    return {
        "scope": "us-states",
        "title": "United States — States",
        "view": view,
        "regions": regions,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_DIR / "us-states.json"))
    args = ap.parse_args()

    bundle = build()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out)
    out_path.write_text(json.dumps(bundle, separators=(",", ":")), encoding="utf-8")

    n = len(bundle["regions"])
    size_kb = out_path.stat().st_size / 1024
    total_pts = sum(len(r) for reg in bundle["regions"] for r in reg["rings"])
    print(f"wrote {out_path}")
    print(f"  regions: {n}")
    print(f"  view:    {bundle['view']}")
    print(f"  points:  {total_pts}")
    print(f"  size:    {size_kb:.1f} KB")


if __name__ == "__main__":
    main()
