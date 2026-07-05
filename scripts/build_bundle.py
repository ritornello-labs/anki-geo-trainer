"""Pack Natural Earth layers into compact, pre-projected scope bundles.

The interaction engine runs *inside* an Anki card and does its own hit-testing and
rendering, so it needs geometry client-side. We pre-project here into a clean pixel
space (equirectangular, mean-latitude standard parallel) and simplify there
(sub-pixel tolerance => shared borders stay visually seamless). The engine only
scales a viewBox.

Scopes (one bundle each):
  * us-states        — 50 states, AK/HI as inset frames at their own scale
  * europe-countries — sovereign Europe (+ Cyprus), viewport clipped at the Urals,
                       territories kept as tappable context (tier 2, no notes),
                       microstates as magnified tap-circles, land-border adjacency
                       for the tap-all-neighbors family, and a neutral context
                       landmass (Africa/Anatolia) for orientation

Bundle shape (JSON):
    {
      "scope": "...", "title": "...", "noun": "state|country",
      "view": {"w", "h"},
      "tray": [x, y],                      # optional: F5 piece start position
      "frames": [{"id", "rect", "kmPerUnit", "label"}],
      "context": [[[x,y],...], ...],       # optional: neutral background land
      "regions": [{
        "id", "name", "abbr", "frame", "tier",     # tier 2 = no notes, map-only
        "small": true?,                            # magnified tap-circle region
        "c": [x,y], "s": sqrt_area_px,
        "pts": [[x,y] * 16],                       # F4 interior sample points
        "nb": ["id", ...],                         # land-border neighbors (F7)
        "rings": [[[x,y],...], ...]
      }]
    }
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import urllib.request
from pathlib import Path

from shapely.geometry import MultiPolygon, Point, Polygon, box, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "bundles"

NE_BASE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
SOURCES = {
    "admin1": "ne_50m_admin_1_states_provinces.geojson",
    "admin0": "ne_50m_admin_0_countries.geojson",
    "land110": "ne_110m_land.geojson",
}

EARTH_KM_PER_DEG = 111.32
U32 = 0xFFFFFFFF
N_SAMPLE_POINTS = 16
PAD = 8.0
SMALL_S_PX = 8.0  # below this sqrt-area, a region becomes a magnified tap-circle
SMALL_CIRCLE_R = 7.0


def ensure_source(key: str) -> Path:
    path = RAW_DIR / SOURCES[key]
    if not path.exists():
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        url = NE_BASE + SOURCES[key]
        print(f"downloading {url} -> {path}")
        with urllib.request.urlopen(url) as resp, path.open("wb") as fh:
            shutil.copyfileobj(resp, fh)
    return path


def load_features(key: str) -> list[dict]:
    return json.loads(ensure_source(key).read_text(encoding="utf-8"))["features"]


def prop(props: dict, *names: str):
    for n in names:
        for cand in (n, n.lower(), n.upper()):
            if cand in props:
                return props[cand]
    return None


# --- deterministic PRNG (mirrors engine's mulberry32/strHash JS port) -----------


def str_hash(s: str) -> int:
    h = 2166136261
    for ch in s:
        h ^= ord(ch)
        h = (h * 16777619) & U32
    return h & U32


def mulberry32(seed: int):
    state = seed & U32

    def rnd() -> float:
        nonlocal state
        state = (state + 0x6D2B79F5) & U32
        t = state
        t = ((t ^ (t >> 15)) * (t | 1)) & U32
        t ^= (t + (((t ^ (t >> 7)) * (t | 61)) & U32)) & U32
        t &= U32
        return ((t ^ (t >> 14)) & U32) / 4294967296.0

    return rnd


# --- projection ------------------------------------------------------------------


def fit_projector(geoms: list, rect: tuple[float, float, float, float]):
    """Equirectangular projector (mean-lat standard parallel) fitted inside rect,
    preserving aspect. Returns (project, km_per_unit)."""
    rx, ry, rw, rh = rect
    lon_min = lat_min = math.inf
    lon_max = lat_max = -math.inf
    for g in geoms:
        x0, y0, x1, y1 = g.bounds
        lon_min, lat_min = min(lon_min, x0), min(lat_min, y0)
        lon_max, lat_max = max(lon_max, x1), max(lat_max, y1)

    lat0 = math.radians((lat_min + lat_max) / 2.0)
    cos0 = math.cos(lat0)
    x_span = (lon_max - lon_min) * cos0
    y_span = lat_max - lat_min

    inner_w, inner_h = rw - 2 * PAD, rh - 2 * PAD
    scale = min(inner_w / x_span, inner_h / y_span)
    used_w, used_h = x_span * scale, y_span * scale
    ox = rx + PAD + (inner_w - used_w) / 2.0
    oy = ry + PAD + (inner_h - used_h) / 2.0
    km_per_unit = (1.0 / scale) * EARTH_KM_PER_DEG

    def project(lon: float, lat: float) -> tuple[float, float]:
        return ox + (lon - lon_min) * cos0 * scale, oy + (lat_max - lat) * scale

    return project, km_per_unit


def project_geom(geom, project) -> BaseGeometry:
    polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    out = []
    for poly in polys:
        ext = [project(lon, lat) for lon, lat in poly.exterior.coords]
        p = Polygon(ext)
        if p.is_valid and p.area > 0:
            out.append(p)
    if not out:
        return Polygon()
    return unary_union(out) if len(out) > 1 else out[0]


def rings_of(geom, min_area: float = 3.0) -> list[list[list[float]]]:
    """Exterior rings, dropping micro-islands below min_area px² (invisible at
    card size but heavy — the Aleutians/Norwegian skerries are hundreds)."""
    if geom.is_empty:
        return []
    polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    rings = []
    for poly in sorted(polys, key=lambda p: p.area, reverse=True):
        if poly.area < min_area and rings:
            continue
        coords = [[round(x, 1), round(y, 1)] for x, y in poly.exterior.coords]
        if len(coords) >= 4:
            rings.append(coords)
    return rings


# --- F4 sample points --------------------------------------------------------------


def erosion_distance(geom: BaseGeometry) -> float:
    return 0.12 * math.sqrt(geom.area)


def eroded(geom: BaseGeometry) -> BaseGeometry:
    for frac in (1.0, 0.5, 0.25):
        inset = geom.buffer(-erosion_distance(geom) * frac)
        if not inset.is_empty and inset.area > 0:
            return inset
    return geom


def sample_points(geom: BaseGeometry, region_id: str, n: int = N_SAMPLE_POINTS):
    inset = eroded(geom)
    rnd = mulberry32(str_hash("pts:" + region_id))
    minx, miny, maxx, maxy = inset.bounds
    pts: list[list[float]] = []
    tries = 0
    while len(pts) < n and tries < n * 300:
        tries += 1
        x = minx + (maxx - minx) * rnd()
        y = miny + (maxy - miny) * rnd()
        if inset.contains(Point(x, y)):
            pts.append([round(x, 1), round(y, 1)])
    while len(pts) < n:  # degenerate sliver fallback
        rp = inset.representative_point()
        pts.append([round(rp.x, 1), round(rp.y, 1)])
    return pts


def circle_ring(cx: float, cy: float, r: float, n: int = 20) -> list[list[float]]:
    return [
        [round(cx + r * math.cos(2 * math.pi * i / n), 1),
         round(cy + r * math.sin(2 * math.pi * i / n), 1)]
        for i in range(n + 1)
    ]


def make_region(
    rid: str, name: str, abbr: str, frame: str, projected: BaseGeometry, tier: int = 1
) -> dict | None:
    """Common per-region packaging: simplify, microstate circle upgrade, samples."""
    if projected.is_empty:
        return None
    simplified = projected.simplify(0.6, preserve_topology=True)
    c = projected.representative_point()
    s = math.sqrt(projected.area)
    region = {
        "id": rid,
        "name": name,
        "abbr": abbr,
        "frame": frame,
        "tier": tier,
        "c": [round(c.x, 1), round(c.y, 1)],
        "s": round(s, 1),
    }
    if s < SMALL_S_PX:
        # Magnified tap-circle (Ultimate-Geography style): keep it findable and
        # tappable on a continental map.
        region["small"] = True
        region["rings"] = [circle_ring(c.x, c.y, SMALL_CIRCLE_R)]
        region["s"] = SMALL_CIRCLE_R
        region["pts"] = [[round(c.x, 1), round(c.y, 1)]] * N_SAMPLE_POINTS
        return region
    rings = rings_of(simplified)
    if not rings:
        return None
    region["rings"] = rings
    region["pts"] = sample_points(projected, rid)
    return region


def add_adjacency(regions: list[dict], full_geoms: dict[str, BaseGeometry]) -> None:
    """Land-border neighbor lists computed on the UNCLIPPED lon/lat geometries.
    A neighbor pair must share a real boundary line (> ~5 km), not a point touch
    (Four Corners: Arizona–Colorado is a corner, not a border)."""
    ids = [r["id"] for r in regions if r["id"] in full_geoms]
    nb: dict[str, set[str]] = {i: set() for i in ids}
    for i, a in enumerate(ids):
        ga = full_geoms[a]
        for b in ids[i + 1:]:
            gb = full_geoms[b]
            if not ga.envelope.intersects(gb.envelope):
                continue
            shared = ga.intersection(gb)
            if shared.is_empty:
                continue
            if getattr(shared, "length", 0.0) > 0.05:
                nb[a].add(b)
                nb[b].add(a)
    for r in regions:
        r["nb"] = sorted(nb.get(r["id"], set()))


# =========================== scope: us-states =====================================

US_HI_MIN_LON = -161.0  # keep Hawaii's eight main islands, drop the NW chain
US_MAIN_WIDTH = 1000.0
US_INSET_BAND_H = 190.0


def _us_geom(feat: dict, unwrap_lon: bool = False, min_lon: float | None = None):
    geom = shape(feat["geometry"])
    if min_lon is not None:
        polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
        kept = [p for p in polys if p.centroid.x >= min_lon]
        geom = unary_union(kept) if kept else geom
    if not unwrap_lon:
        return geom
    polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    shifted = []
    for poly in polys:
        ext = [(lon - 360.0 if lon > 0 else lon, lat) for lon, lat in poly.exterior.coords]
        shifted.append(Polygon(ext))
    return unary_union(shifted)


def build_us_states() -> dict:
    feats = [
        f
        for f in load_features("admin1")
        if prop(f["properties"], "adm0_a3") == "USA"
        and prop(f["properties"], "type_en") == "State"
    ]
    lower48 = [f for f in feats if prop(f["properties"], "name") not in ("Alaska", "Hawaii")]
    ak = [f for f in feats if prop(f["properties"], "name") == "Alaska"]
    hi = [f for f in feats if prop(f["properties"], "name") == "Hawaii"]

    l48_geoms = [_us_geom(f) for f in lower48]
    lon_min = min(g.bounds[0] for g in l48_geoms)
    lon_max = max(g.bounds[2] for g in l48_geoms)
    lat_min = min(g.bounds[1] for g in l48_geoms)
    lat_max = max(g.bounds[3] for g in l48_geoms)
    cos0 = math.cos(math.radians((lat_min + lat_max) / 2.0))
    main_h = (lat_max - lat_min) / ((lon_max - lon_min) * cos0) * US_MAIN_WIDTH + 2 * PAD
    main_rect = (0.0, 0.0, US_MAIN_WIDTH + 2 * PAD, main_h)

    view_w = US_MAIN_WIDTH + 2 * PAD
    view_h = main_h + US_INSET_BAND_H
    band_y = main_h
    ak_rect = (8.0, band_y + 4.0, 300.0, US_INSET_BAND_H - 12.0)
    hi_rect = (324.0, band_y + 4.0, 250.0, US_INSET_BAND_H - 12.0)

    frame_specs = [
        ("main", main_rect, l48_geoms, lower48, False, None, ""),
        ("ak", ak_rect, [_us_geom(ak[0], unwrap_lon=True)], ak, True, None, "Alaska (own scale)"),
        ("hi", hi_rect, [_us_geom(hi[0], min_lon=US_HI_MIN_LON)], hi, False, US_HI_MIN_LON,
         "Hawaii (own scale)"),
    ]

    frames, regions = [], []
    full_geoms: dict[str, BaseGeometry] = {}
    for fid, rect, geoms, feat_list, unwrap, min_lon, label in frame_specs:
        project, km = fit_projector(geoms, rect)
        frames.append(
            {"id": fid, "rect": [round(v, 1) for v in rect], "kmPerUnit": round(km, 3),
             "label": label}
        )
        for feat in feat_list:
            props = feat["properties"]
            rid = prop(props, "iso_3166_2") or f"US-{prop(props, 'postal')}"
            projected = project_geom(_us_geom(feat, unwrap_lon=unwrap, min_lon=min_lon), project)
            region = make_region(rid, prop(props, "name"), prop(props, "postal") or "", fid, projected)
            if region:
                regions.append(region)
                full_geoms[rid] = shape(feat["geometry"])

    add_adjacency(regions, full_geoms)
    regions.sort(key=lambda r: r["name"])
    return {
        "scope": "us-states",
        "title": "United States — States",
        "noun": "state",
        "view": {"w": round(view_w, 1), "h": round(view_h, 1)},
        "frames": frames,
        "regions": regions,
    }


# ======================== scope: europe-countries =================================

# Viewport: Iceland to the Urals, Malta to Nordkapp. Russia is clipped at the box
# edge (standard political-quiz cartography); Svalbard falls above the lat cap.
EU_BOX = (-25.0, 34.0, 62.0, 72.0)  # lon_min, lat_min, lon_max, lat_max
EU_WIDTH = 1000.0

# NE marks these as Asia; European political quizzes conventionally include Cyprus
# (EU member). The Caucasus trio and Turkey wait for the Asia scope.
EU_EXTRA_ADMINS = {"Cyprus"}
EU_EXCLUDE_ADMINS = {"Northern Cyprus"}  # disputed; not a tier-1 quiz entity

# Quiz-friendly display names where NE's ADMIN is formal/odd.
EU_NAME_OVERRIDES = {
    "Republic of Serbia": "Serbia",
    "Vatican": "Vatican City",
}


def build_europe() -> dict:
    feats = []
    for f in load_features("admin0"):
        props = f["properties"]
        admin = prop(props, "ADMIN")
        continent = prop(props, "CONTINENT")
        if admin in EU_EXCLUDE_ADMINS:
            continue
        if continent == "Europe" or admin in EU_EXTRA_ADMINS:
            feats.append(f)

    clip = box(*[EU_BOX[i] for i in (0, 1, 2, 3)])
    entries = []  # (rid, name, abbr, tier, clipped_geom, full_geom)
    for f in feats:
        props = f["properties"]
        admin = prop(props, "ADMIN")
        full = shape(f["geometry"])
        clipped = full.intersection(clip)
        if clipped.is_empty or clipped.area == 0:
            continue  # entirely outside the viewport
        iso2 = prop(props, "ISO_A2", "ISO_A2_EH")
        a3 = prop(props, "ADM0_A3")
        rid = iso2 if iso2 and iso2 != "-99" else a3
        # Tier 1 = self-sovereign (catches Denmark/France/UK "Country" rows and
        # Kosovo "Disputed"); tier 2 = dependencies (Faroes, Aland, Crown deps).
        tier = 1 if prop(props, "SOVEREIGNT") == admin else 2
        name = EU_NAME_OVERRIDES.get(admin, admin)
        entries.append((rid, name, iso2 or a3, tier, clipped, full))

    # Projection fitted to the viewport box itself (stable framing, not data-driven).
    lat0 = math.radians((EU_BOX[1] + EU_BOX[3]) / 2.0)
    cos0 = math.cos(lat0)
    x_span = (EU_BOX[2] - EU_BOX[0]) * cos0
    y_span = EU_BOX[3] - EU_BOX[1]
    scale = EU_WIDTH / x_span
    view_w = EU_WIDTH + 2 * PAD
    view_h = y_span * scale + 2 * PAD
    km_per_unit = (1.0 / scale) * EARTH_KM_PER_DEG

    def project(lon: float, lat: float) -> tuple[float, float]:
        return (lon - EU_BOX[0]) * cos0 * scale + PAD, (EU_BOX[3] - lat) * scale + PAD

    regions = []
    geoms_by_id: dict[str, BaseGeometry] = {}
    for rid, name, abbr, tier, clipped, full in entries:
        projected = project_geom(clipped, project)
        region = make_region(rid, name, abbr, "main", projected, tier=tier)
        if region:
            regions.append(region)
            geoms_by_id[rid] = full

    # Land-border adjacency on the UNCLIPPED geometries (Russia–Norway etc. count
    # even where the border sits near the viewport edge).
    add_adjacency(regions, geoms_by_id)

    # Neutral context land (Africa/Anatolia/greater Russia) for orientation.
    context: list[list[list[float]]] = []
    land = unary_union([shape(f["geometry"]) for f in load_features("land110")])
    ctx = land.intersection(clip)
    context = rings_of(project_geom(ctx, project).simplify(0.8, preserve_topology=True))

    regions.sort(key=lambda r: r["name"])
    return {
        "scope": "europe-countries",
        "title": "Europe — Countries",
        "noun": "country",
        "view": {"w": round(view_w, 1), "h": round(view_h, 1)},
        "tray": [90.0, round(view_h - 90.0, 1)],  # open Atlantic, bottom-left
        "frames": [
            {"id": "main", "rect": [0.0, 0.0, round(view_w, 1), round(view_h, 1)],
             "kmPerUnit": round(km_per_unit, 3), "label": ""}
        ],
        "context": context,
        "regions": regions,
    }


# ---------------------------------------------------------------------------------

SCOPES = {
    "us-states": build_us_states,
    "europe-countries": build_europe,
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", default="all", choices=["all", *SCOPES.keys()])
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    names = list(SCOPES) if args.scope == "all" else [args.scope]
    for name in names:
        bundle = SCOPES[name]()
        out_path = OUT_DIR / f"{name}.json"
        out_path.write_text(json.dumps(bundle, separators=(",", ":")), encoding="utf-8")
        n = len(bundle["regions"])
        tier1 = sum(1 for r in bundle["regions"] if r.get("tier", 1) == 1)
        small = sum(1 for r in bundle["regions"] if r.get("small"))
        size_kb = out_path.stat().st_size / 1024
        print(f"wrote {out_path}")
        print(
            f"  regions: {n} (tier1: {tier1}, small: {small}) | "
            f"view: {bundle['view']['w']}x{bundle['view']['h']} | {size_kb:.1f} KB"
        )


if __name__ == "__main__":
    main()
