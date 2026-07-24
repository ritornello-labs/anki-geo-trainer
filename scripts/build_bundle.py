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
import re
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
    # 10m admin-1 (≈40 MB) covers every country's provinces; the 50m file only
    # has nine large ones. Used for scopes outside that set (Argentina, Mexico…).
    "admin1_10m": "ne_10m_admin_1_states_provinces.geojson",
    "admin0": "ne_50m_admin_0_countries.geojson",
    "land110": "ne_110m_land.geojson",
    # 10m places (≈19 MB) carries 2,259 province capitals vs the 50m file's 482 —
    # needed for near-complete state/province capital coverage in F8.
    "places": "ne_10m_populated_places.geojson",
    # Physical features: river centrelines (50m) and areal regions (10m — its
    # FEATURECLA/NAME_EN are populated; the 50m regions file's are empty).
    "rivers": "ne_50m_rivers_lake_centerlines.geojson",
    "regions10": "ne_10m_geography_regions_polys.geojson",
    "lakes10": "ne_10m_lakes.geojson",
    "marine50": "ne_50m_geography_marine_polys.geojson",
}
EXTERNAL_SOURCES = {
    "plates": (
        "PB2002_plates.json",
        "https://raw.githubusercontent.com/fraxen/tectonicplates/master/GeoJSON/"
        "PB2002_plates.json",
    ),
}

EARTH_KM_PER_DEG = 111.32
U32 = 0xFFFFFFFF
N_SAMPLE_POINTS = 16
PAD = 8.0
SMALL_S_PX = 8.0  # below this sqrt-area, a region becomes a magnified tap-circle
SMALL_CIRCLE_R = 7.0


def ensure_source(key: str) -> Path:
    if key in EXTERNAL_SOURCES:
        filename, url = EXTERNAL_SOURCES[key]
    else:
        filename, url = SOURCES[key], NE_BASE + SOURCES[key]
    path = RAW_DIR / filename
    if not path.exists():
        RAW_DIR.mkdir(parents=True, exist_ok=True)
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
        if not p.is_valid:
            # Repair self-intersecting rings (NE state polygons that wrap around
            # an enclave — e.g. Goiás around Brazil's Federal District — are
            # invalid and would otherwise be silently dropped).
            p = p.buffer(0)
        if not p.is_empty and p.area > 0:
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
    rid: str,
    name: str,
    abbr: str,
    frame: str,
    projected: BaseGeometry,
    tier: int = 1,
    magnify_small: bool = True,
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
    if magnify_small and s < SMALL_S_PX:
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


def shape_payload(geom: BaseGeometry, box_px: float = 400.0, mainland_only: bool = False) -> dict:
    """Standalone outline for F6 draw-the-shape: the region re-fitted into its
    own box at drawing resolution (the continental-bundle rings are simplified
    for map scale and look chunky blown up). Keeps islands >= 3% of the largest
    polygon (Corsica-sized specks drop; Michigan's peninsulas and Northern
    Ireland stay). Unwraps antimeridian crossers (Alaska, Russia) so Chukotka
    doesn't smear the fit across the globe. With `mainland_only`, keep ONLY the
    single largest contiguous landmass — for continent silhouettes and the USA,
    where a detached-but-near part (Greenland off Canada, Alaska off the lower-48)
    would otherwise chain in and isn't what you picture drawing. Central America
    stays either way: it is one connected polygon with the North American mainland."""
    polys = list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]
    lon_span = max(p.bounds[2] for p in polys) - min(p.bounds[0] for p in polys)
    if lon_span > 180:
        shifted = []
        for p in polys:
            if p.centroid.x < 0:
                p = Polygon([(lon + 360.0, lat) for lon, lat in p.exterior.coords])
            shifted.append(p)
        polys = shifted
    biggest = max(polys, key=lambda p: p.area)
    if mainland_only:
        polys = [biggest]
    else:
        pool = [p for p in polys if p.area >= 0.03 * biggest.area and p is not biggest]
        # Keep only parts near the main landmass: NE admin-0 includes far-flung
        # territory in the same geometry (French Guiana is 15% of "France",
        # Svalbard 19% of "Norway") which would shrink the iconic mainland into a
        # corner of the drawing box. Greedy chain growth on edge-to-edge distance
        # so island chains stay whole (Hawaii's Maui/Oahu), while Sicily/Sardinia,
        # Northern Ireland, and Michigan's UP stay and overseas parts drop.
        bx0, by0, bx1, by1 = biggest.bounds
        reach = max(0.25 * math.hypot(bx1 - bx0, by1 - by0), 0.8)  # degrees
        kept = [biggest]
        grew = True
        while grew and pool:
            grew = False
            for p in list(pool):
                if any(p.distance(k) <= reach for k in kept):
                    kept.append(p)
                    pool.remove(p)
                    grew = True
        polys = kept

    lon_min = min(p.bounds[0] for p in polys)
    lat_min = min(p.bounds[1] for p in polys)
    lon_max = max(p.bounds[2] for p in polys)
    lat_max = max(p.bounds[3] for p in polys)
    cos0 = math.cos(math.radians((lat_min + lat_max) / 2.0))
    x_span = max((lon_max - lon_min) * cos0, 1e-9)
    y_span = max(lat_max - lat_min, 1e-9)
    pad = 6.0
    scale = min((box_px - 2 * pad) / x_span, (box_px - 2 * pad) / y_span)
    w = x_span * scale + 2 * pad
    h = y_span * scale + 2 * pad

    rings = []
    for p in sorted(polys, key=lambda p: p.area, reverse=True)[:6]:
        simplified = Polygon(
            [((lon - lon_min) * cos0 * scale + pad, (lat_max - lat) * scale + pad)
             for lon, lat in p.exterior.coords]
        ).simplify(1.0, preserve_topology=True)
        if simplified.is_empty:
            continue
        coords = [[round(x, 1), round(y, 1)] for x, y in simplified.exterior.coords]
        if len(coords) >= 4:
            rings.append(coords)
    return {"w": round(w, 1), "h": round(h, 1), "rings": rings}


def extract_capitals(
    full_geoms: dict[str, BaseGeometry], project_point, feature_class: str, pt_shift=None
) -> dict[str, dict]:
    """F8 data: match each Natural Earth capital of `feature_class` to the region
    whose (unclipped) geometry contains it, then project the point into scope
    coords. `feature_class` is "Admin-0 capital" for country scopes, "Admin-1
    capital" for subdivision scopes. `project_point(rid, lon, lat) -> (x, y)`
    lets us-states route each capital through its own inset frame's projector.
    One capital per region (first containing match wins)."""
    items = list(full_geoms.items())
    caps: dict[str, dict] = {}
    for f in load_features("places"):
        props = f["properties"]
        if props.get("FEATURECLA") != feature_class:
            continue
        coords = f["geometry"]["coordinates"]
        lon, lat = coords[0], coords[1]
        # Match containment against the (possibly antimeridian-shifted) geoms.
        pt = Point(pt_shift(lon) if pt_shift else lon, lat)
        for rid, g in items:
            if rid in caps:
                continue
            if g.contains(pt):
                x, y = project_point(rid, lon, lat)
                caps[rid] = {"name": props.get("NAME"), "x": round(x, 1), "y": round(y, 1)}
                break
    return caps


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
    frame_projectors: dict[str, object] = {}
    for fid, rect, geoms, feat_list, unwrap, min_lon, label in frame_specs:
        project, km = fit_projector(geoms, rect)
        frame_projectors[fid] = project
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
    shapes = {r["id"]: shape_payload(full_geoms[r["id"]]) for r in regions}
    # F8: state capitals, each routed through its region's inset frame projector
    # (Juneau/Honolulu land in the AK/HI panels, not the lower-48 frame).
    region_frame = {r["id"]: r["frame"] for r in regions}
    capitals = extract_capitals(
        full_geoms,
        lambda rid, lon, lat: frame_projectors[region_frame[rid]](lon, lat),
        "Admin-1 capital",
    )
    return {
        "scope": "us-states",
        "title": "United States — States",
        "noun": "state",
        "view": {"w": round(view_w, 1), "h": round(view_h, 1)},
        "frames": frames,
        "regions": regions,
    }, shapes, capitals


# ================= generic continent builder (admin0 → viewport) ==================
# Europe was the first instance; every continent scope is now the same machine
# driven by CONTINENT_SCOPES config: a hand-picked lon/lat viewport box, a
# CONTINENT filter (+ per-scope extras/excludes), sovereign/dependency tiering,
# magnified microstate circles, and neutral 110m context land for orientation.

TRAY_CORNERS = {
    "bottom-left": lambda w, h: [90.0, round(h - 90.0, 1)],
    "bottom-right": lambda w, h: [round(w - 90.0, 1), round(h - 90.0, 1)],
    "top-left": lambda w, h: [90.0, 90.0],
    "top-right": lambda w, h: [round(w - 90.0, 1), 90.0],
}

CONTINENT_SCOPES = {
    "europe-countries": {
        "title": "Europe — Countries",
        # Iceland to the Urals, Malta to Nordkapp. Russia clips at the box edge.
        "box": (-25.0, 34.0, 62.0, 72.0),
        "continent": "Europe",
        "extra_admins": {"Cyprus"},          # NE files it under Asia
        "exclude_admins": {"Northern Cyprus"},
        "name_overrides": {"Republic of Serbia": "Serbia", "Vatican": "Vatican City"},
        "tray": "bottom-left",               # open Atlantic
    },
    "south-america-countries": {
        "title": "South America — Countries",
        "box": (-82.0, -56.0, -34.0, 13.0),  # Galápagos (−91°) intentionally out
        "continent": "South America",
        "name_overrides": {},
        "tray": "bottom-left",               # SE Pacific
    },
    "africa-countries": {
        "title": "Africa — Countries",
        "box": (-18.0, -35.0, 52.0, 38.0),
        "continent": "Africa",
        "name_overrides": {
            "Democratic Republic of the Congo": "DR Congo",
            "Republic of the Congo": "Congo",
            "United Republic of Tanzania": "Tanzania",
            "eSwatini": "Eswatini",
        },
        "tray": "bottom-left",               # South Atlantic
    },
    "oceania-countries": {
        "title": "Oceania — Countries",
        # Pacific-centred: box is in unwrapped 0..360 lon. Australia (113°) through
        # Samoa (~188° = −172°+360); Micronesia/Palau in the north.
        "box": (110.0, -50.0, 200.0, 22.0),
        "continent": "Oceania",
        "unwrap_antimeridian": True,
        "name_overrides": {
            "Federated States of Micronesia": "Micronesia",
            "Papua New Guinea": "Papua New Guinea",
        },
        "tray": "top-left",  # empty NW ocean
    },
    "north-america-countries": {
        "title": "North America — Countries",
        # Lower-48 + Canada mainland + Mexico + Central America + Caribbean.
        # Alaska (west of −140) clips at the frame; Greenland excluded (it dwarfs
        # the map and the USA/Canada/Mexico shapes people actually study).
        "box": (-140.0, 5.0, -52.0, 72.0),
        "continent": "North America",
        "exclude_admins": {"Greenland"},
        "draw_mainland_only": {"US"},        # lower-48; Alaska/Hawaii off the draw shape
        "name_overrides": {"United States of America": "United States", "The Bahamas": "Bahamas"},
        "tray": "bottom-left",               # open E Pacific
    },
    "asia-countries": {
        "title": "Asia — Countries",
        # Turkey to Japan, Timor to the Kazakh steppe; Russia clips at the top.
        "box": (25.0, -11.0, 147.0, 56.0),
        "continent": "Asia",
        # Drop NE's non-country oddities that would otherwise float as labelled
        # tap-circles: a disputed glacier and an uninhabited island territory.
        "exclude_admins": {
            "Northern Cyprus", "Siachen Glacier", "Indian Ocean Territories",
        },
        "name_overrides": {},
        "tray": "bottom-left",               # Indian Ocean
    },
}


def _build_continent(scope_name: str, cfg: dict) -> tuple[dict, dict]:
    box_t = cfg["box"]
    width = cfg.get("width", 1000.0)
    extra = cfg.get("extra_admins", set())
    exclude = cfg.get("exclude_admins", set())
    overrides = cfg.get("name_overrides", {})
    unwrap = cfg.get("unwrap_antimeridian", False)  # Pacific-centred (Oceania)

    feats = []
    for f in load_features("admin0"):
        props = f["properties"]
        admin = prop(props, "ADMIN")
        if admin in exclude:
            continue
        if prop(props, "CONTINENT") == cfg["continent"] or admin in extra:
            feats.append(f)

    clip = box(*box_t)  # box_t is already in unwrapped (0..360) coords when unwrap
    entries = []  # (rid, name, abbr, tier, clipped, full)
    for f in feats:
        props = f["properties"]
        admin = prop(props, "ADMIN")
        full = shape(f["geometry"])
        if unwrap:
            full = _unwrap_antimeridian(full)
        clipped = full.intersection(clip)
        if clipped.is_empty or clipped.area == 0:
            continue  # entirely outside the viewport
        iso2 = prop(props, "ISO_A2", "ISO_A2_EH")
        a3 = prop(props, "ADM0_A3")
        rid = iso2 if iso2 and iso2 != "-99" else a3
        # Tier 1 = self-sovereign (catches "Country" rows and disputed states);
        # tier 2 = dependencies, shown muted and card-less.
        tier = 1 if prop(props, "SOVEREIGNT") == admin else 2
        name = overrides.get(admin, admin)
        entries.append((rid, name, iso2 or a3, tier, clipped, full))

    # Projection fitted to the viewport box itself (stable framing, not data-driven).
    lat0 = math.radians((box_t[1] + box_t[3]) / 2.0)
    cos0 = math.cos(lat0)
    x_span = (box_t[2] - box_t[0]) * cos0
    y_span = box_t[3] - box_t[1]
    scale = width / x_span
    view_w = width + 2 * PAD
    view_h = y_span * scale + 2 * PAD
    km_per_unit = (1.0 / scale) * EARTH_KM_PER_DEG

    def project(lon: float, lat: float) -> tuple[float, float]:
        return (lon - box_t[0]) * cos0 * scale + PAD, (box_t[3] - lat) * scale + PAD

    regions = []
    geoms_by_id: dict[str, BaseGeometry] = {}
    for rid, name, abbr, tier, clipped, full in entries:
        projected = project_geom(clipped, project)
        region = make_region(rid, name, abbr, "main", projected, tier=tier)
        if region:
            regions.append(region)
            geoms_by_id[rid] = full

    add_adjacency(regions, geoms_by_id)
    tier1_geoms = {r["id"]: geoms_by_id[r["id"]] for r in regions if r.get("tier", 1) == 1}
    # Some countries draw as mainland-only (USA: drop the detached Alaska/Hawaii
    # so the graded shape is the lower-48 you actually picture).
    mainland_ids = cfg.get("draw_mainland_only", set())
    shapes = {rid: shape_payload(g, mainland_only=(rid in mainland_ids))
              for rid, g in tier1_geoms.items()}

    # F8: national capitals, tier-1 countries only. Under unwrap, shift the
    # capital's western-hemisphere lon east by 360 to match the shifted geoms.
    def cap_project(rid, lon, lat):
        return project((lon + 360.0 if unwrap and lon < 0 else lon), lat)
    capitals = extract_capitals(tier1_geoms, cap_project, "Admin-0 capital",
                                pt_shift=(lambda lon: lon + 360.0 if lon < 0 else lon) if unwrap else None)

    # Neutral context land (neighbouring continents) for orientation. Skipped for
    # antimeridian-unwrapped scopes: unwrapping the whole-world land mangles the
    # dateline seam, and an isolated Pacific view has no neighbours to show anyway.
    if unwrap:
        context = []
    else:
        land = unary_union([shape(f["geometry"]) for f in load_features("land110")])
        context = rings_of(
            project_geom(land.intersection(clip), project).simplify(0.8, preserve_topology=True)
        )

    regions.sort(key=lambda r: r["name"])
    tray = TRAY_CORNERS[cfg.get("tray", "bottom-left")](view_w, view_h)
    return {
        "scope": scope_name,
        "title": cfg["title"],
        "noun": "country",
        "view": {"w": round(view_w, 1), "h": round(view_h, 1)},
        "tray": tray,
        "frames": [
            {"id": "main", "rect": [0.0, 0.0, round(view_w, 1), round(view_h, 1)],
             "kmPerUnit": round(km_per_unit, 3), "label": ""}
        ],
        "context": context,
        "regions": regions,
    }, shapes, capitals


# ==================== continents: single dissolved silhouettes ====================
# Each "region" is a whole continent — every country of that continent dissolved
# into one polygon — so the Draw family asks you to sketch the continent outline
# from memory. Draw-only: naming/placing a continent is trivial. Each continent
# draws as its main landmass (`mainland_only`): far islands drop, but contiguous
# parts like Central America stay. Eurasia is split messily by country membership
# (Natural Earth files Russia under Europe), so Europe is clipped at the Urals to
# cut Siberia off; Asia then dissolves without Russia (no Siberia, but a clean,
# recognizable Turkey-to-Japan mass). Antarctica is omitted — in plate-carrée it
# smears into an unrecognizable band across the bottom and nobody sketches it.
CONTINENTS_SCOPES = {
    "continents": {
        "title": "World — Continents",
        "families": ["sketch", "draw"],
        "members": [
            {"name": "Africa", "continents": ["Africa"]},
            {"name": "Asia", "continents": ["Asia"]},
            {"name": "Europe", "continents": ["Europe"], "box": (-25.0, 34.0, 62.0, 72.0)},
            {"name": "North America", "continents": ["North America"], "exclude": {"Greenland"}},
            {"name": "Oceania", "continents": ["Oceania"]},
            {"name": "South America", "continents": ["South America"]},
        ],
    },
}


def _largest_poly(geom: BaseGeometry) -> BaseGeometry:
    if isinstance(geom, MultiPolygon):
        return max(geom.geoms, key=lambda p: p.area)
    return geom


def _build_continents(scope_name: str, cfg: dict) -> tuple[dict, dict, dict]:
    members = cfg["members"]
    # Smoke-test map only (Draw uses per-note shapes): a plain world equirect box.
    box_t = cfg.get("map_box", (-180.0, -60.0, 180.0, 84.0))
    width = cfg.get("width", 1400.0)
    lat0 = math.radians((box_t[1] + box_t[3]) / 2.0)
    cos0 = math.cos(lat0)
    scale = width / ((box_t[2] - box_t[0]) * cos0)
    view_w = width + 2 * PAD
    view_h = (box_t[3] - box_t[1]) * scale + 2 * PAD
    km_per_unit = (1.0 / scale) * EARTH_KM_PER_DEG

    def project(lon, lat):
        return (lon - box_t[0]) * cos0 * scale + PAD, (box_t[3] - lat) * scale + PAD

    regions = []
    shape_geoms: dict[str, BaseGeometry] = {}
    for m in members:
        conts = set(m["continents"])
        exclude = m.get("exclude", set())
        parts = [
            shape(f["geometry"])
            for f in load_features("admin0")
            if prop(f["properties"], "CONTINENT") in conts
            and prop(f["properties"], "ADMIN") not in exclude
        ]
        geom = unary_union(parts)
        if "box" in m:  # Europe: clip Eurasia at the Urals so Siberia drops
            geom = geom.intersection(box(*m["box"]))
        rid = _slug(m["name"])
        # Map region = the mainland projected into the world view (smoke tests).
        projected = project_geom(_largest_poly(geom), project)
        region = make_region(rid, m["name"], "", "main", projected)
        if region:
            regions.append(region)
            shape_geoms[rid] = geom

    regions.sort(key=lambda r: r["name"])
    shapes = {rid: shape_payload(g, mainland_only=True) for rid, g in shape_geoms.items()}

    return {
        "scope": scope_name,
        "title": cfg["title"],
        "noun": "continent",
        "families": cfg.get("families", ["draw"]),
        "view": {"w": round(view_w, 1), "h": round(view_h, 1)},
        "tray": [90.0, round(view_h - 90.0, 1)],
        "frames": [
            {"id": "main", "rect": [0.0, 0.0, round(view_w, 1), round(view_h, 1)],
             "kmPerUnit": round(km_per_unit, 3), "label": ""}
        ],
        "context": [],  # Draw uses a blank canvas; the map is only for the smoke tests
        "regions": regions,
    }, shapes, {}


# ============ generic first-level subdivision builder (admin1 → frame) ============
# NOTE: the Natural Earth *50m* admin1 file only carries provinces for nine large
# countries — AUS, BRA, CAN, CHN, IDN, IND, RUS, USA, ZAF. Everything else
# (Argentina, Mexico, …) needs the heavier 10m file, which we can add later.
# us-states stays its own function because AK/HI need inset frames; contiguous
# countries fit a single frame.

SUBDIVISION_SCOPES = {
    "brazil-states": {
        "title": "Brazil — States", "a3": "BRA", "noun": "state",
        "deck_root": "GeoTrainer::World::South America::Brazil",
    },
    "india-states": {
        "title": "India — States & Union Territories", "a3": "IND", "noun": "state",
        "deck_root": "GeoTrainer::World::Asia::India",
    },
    "russia-subjects": {
        "title": "Russia — Federal Subjects", "a3": "RUS", "noun": "region",
        "unwrap_antimeridian": True,  # Chukotka crosses the dateline
        "deck_root": "GeoTrainer::World::Europe::Russia",
    },
    "china-provinces": {
        "title": "China — Provinces", "a3": "CHN", "noun": "province",
        "deck_root": "GeoTrainer::World::Asia::China",
    },
    "canada-provinces": {
        "title": "Canada — Provinces & Territories", "a3": "CAN", "noun": "province",
        "deck_root": "GeoTrainer::World::North America::Canada",
    },
    "australia-states": {
        "title": "Australia — States & Territories", "a3": "AUS", "noun": "state",
        "deck_root": "GeoTrainer::World::Oceania::Australia",
    },
    "indonesia-provinces": {
        "title": "Indonesia — Provinces", "a3": "IDN", "noun": "province",
        "deck_root": "GeoTrainer::World::Asia::Indonesia",
    },
    "argentina-provinces": {
        "title": "Argentina — Provinces", "a3": "ARG", "noun": "province",
        "source": "admin1_10m",
        "deck_root": "GeoTrainer::World::South America::Argentina",
    },
    "mexico-states": {
        "title": "Mexico — States", "a3": "MEX", "noun": "state",
        "source": "admin1_10m",
        "deck_root": "GeoTrainer::World::North America::Mexico",
    },
}


def _unwrap_antimeridian(geom: BaseGeometry) -> BaseGeometry:
    """Shift the western (negative-lon) half of a dateline-crossing country east
    by 360° so it projects as one continuous landmass (Russia's Chukotka)."""
    polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    out = []
    for poly in polys:
        coords = [((lon + 360.0 if lon < 0 else lon), lat) for lon, lat in poly.exterior.coords]
        out.append(Polygon(coords))
    return unary_union(out) if len(out) > 1 else out[0]


def _build_admin1_country(scope_name: str, cfg: dict) -> tuple[dict, dict]:
    a3 = cfg["a3"]
    types = cfg.get("types")
    width = cfg.get("width", 1000.0)
    id_prefix = cfg.get("id_prefix", a3[:2])
    source = cfg.get("source", "admin1")
    unwrap = cfg.get("unwrap_antimeridian", False)

    feats = [
        f for f in load_features(source)
        if prop(f["properties"], "adm0_a3") == a3
        and prop(f["properties"], "name")  # skip NE's occasional nameless junk row
        and (types is None or prop(f["properties"], "type_en") in types)
    ]
    if not feats:
        raise SystemExit(f"{scope_name}: no admin1 for {a3} in {source}")

    def render_geom(f):
        g = shape(f["geometry"])
        return _unwrap_antimeridian(g) if unwrap else g

    geoms = [render_geom(f) for f in feats]
    lon_min = min(g.bounds[0] for g in geoms)
    lon_max = max(g.bounds[2] for g in geoms)
    lat_min = min(g.bounds[1] for g in geoms)
    lat_max = max(g.bounds[3] for g in geoms)
    cos0 = math.cos(math.radians((lat_min + lat_max) / 2.0))
    main_h = (lat_max - lat_min) / ((lon_max - lon_min) * cos0) * width + 2 * PAD
    rect = (0.0, 0.0, width + 2 * PAD, main_h)
    project, km_per_unit = fit_projector(geoms, rect)
    view_w, view_h = width + 2 * PAD, main_h

    regions = []
    full_geoms: dict[str, BaseGeometry] = {}
    for f in feats:
        props = f["properties"]
        rid = prop(props, "iso_3166_2") or f"{id_prefix}-{prop(props, 'postal')}"
        g = render_geom(f)  # antimeridian-unwrapped where needed
        projected = project_geom(g, project)
        region = make_region(rid, prop(props, "name"), prop(props, "postal") or "", "main", projected)
        if region:
            regions.append(region)
            full_geoms[rid] = g

    add_adjacency(regions, full_geoms)
    regions.sort(key=lambda r: r["name"])
    shapes = {r["id"]: shape_payload(full_geoms[r["id"]]) for r in regions}
    # F8: state/province capitals (Admin-1 capital), projected through the frame.
    capitals = extract_capitals(full_geoms, lambda rid, lon, lat: project(lon, lat),
                                "Admin-1 capital")
    return {
        "scope": scope_name,
        "title": cfg["title"],
        "noun": cfg.get("noun", "state"),
        "view": {"w": round(view_w, 1), "h": round(view_h, 1)},
        # Piece tray sits in the emptiest corner the aspect-fit letterbox leaves;
        # bottom-left is a safe default (the engine also has a corner fallback).
        "tray": [90.0, round(view_h - 90.0, 1)],
        "frames": [
            {"id": "main", "rect": [round(v, 1) for v in rect],
             "kmPerUnit": round(km_per_unit, 3), "label": ""}
        ],
        "regions": regions,
    }, shapes, capitals


# ================ generic physical-feature polygon builder (world map) ============
# Seas/oceans/gulfs (and, later, ranges) are named polygons on a world plate-
# carrée. They reuse the region machinery (locate + point + draw) but have no
# tiers, adjacency, or capitals. `families` limits which task decks are built.

def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


# Areal physical features as polygons on a world map. Seas were dropped (useless
# at world scale). Ranges/deserts come from 10m geography_regions_polys (FEATURECLA
# = "Range/mtn" / "Desert"), major ones only (scalerank ≤ 3). Point/place hide the
# feature and show only continents for reference (kind == "physical" → the engine
# renders context land, not the feature, on the borderless front).
PHYSICAL_SCOPES = {
    "world-ranges": {
        "title": "World — Mountain Ranges",
        "layer": "regions10",
        "featureclasses": {"Range/mtn"},
        "max_scalerank": 2,  # 31 iconic ranges (≤3 pulls in Andes sub-ranges)
        "noun": "range",
        "families": ["place", "sketch"],
        "box": (-165.0, -56.0, 180.0, 75.0),
        "width": 1500.0,
        "deck_root": "GeoTrainer::Physical::Mountain Ranges",
    },
    "world-deserts": {
        "title": "World — Deserts",
        "layer": "regions10",
        "featureclasses": {"Desert"},
        "max_scalerank": 3,  # 18 major deserts
        "exclude": {"Punjab"},  # not a desert
        "noun": "desert",
        "families": ["place", "sketch"],
        "box": (-120.0, -40.0, 150.0, 50.0),
        "width": 1500.0,
        "deck_root": "GeoTrainer::Physical::Deserts",
    },
}


# A deliberately finite world-lakes curriculum. It includes the largest/iconic
# lakes a learner can reasonably place on a world map, while avoiding a noisy
# "every named pond in Natural Earth" deck. Caspian is a marine polygon in
# Natural Earth; the Aral Sea is reconstructed from its north/south polygons.
LAKE_NAMES = {
    "Caspian Sea": ("marine50", {"Caspian Sea"}),
    "Aral Sea": ("lakes10", {"North Aral Sea", "South Aral Sea"}),
    "Lake Baikal": ("lakes10", {"Baikal"}),
    "Lake Balkhash": ("lakes10", {"Balkhash"}),
    "Lake Chad": ("lakes10", {"Chad"}),
    "Great Bear Lake": ("lakes10", {"Great Bear"}),
    "Great Slave Lake": ("lakes10", {"Great Slave"}),
    "Lake Winnipeg": ("lakes10", {"Winnipeg"}),
    "Lake Superior": ("lakes10", {"Superior"}),
    "Lake Michigan": ("lakes10", {"Michigan"}),
    "Lake Huron": ("lakes10", {"Huron"}),
    "Lake Erie": ("lakes10", {"Erie"}),
    "Lake Ontario": ("lakes10", {"Ontario"}),
    "Lake Ladoga": ("lakes10", {"Ladoga"}),
    "Lake Onega": ("lakes10", {"Onega"}),
    "Lake Victoria": ("lakes10", {"Nyanza"}),
    "Lake Tanganyika": ("lakes10", {"Tanganyika"}),
    "Lake Malawi": ("lakes10", {"Malawi"}),
    "Lake Turkana": ("lakes10", {"Turkana"}),
    "Lake Titicaca": ("lakes10", {"Titicaca"}),
    "Lake Nicaragua": ("lakes10", {"Nicaragua"}),
    "Great Salt Lake": ("lakes10", {"Great Salt"}),
    "Dead Sea": ("lakes10", {"Dead Sea"}),
    "Lake Tana": ("lakes10", {"Tana"}),
}

PLATE_NAMES = {
    "Africa": "African Plate",
    "Antarctica": "Antarctic Plate",
    "Arabia": "Arabian Plate",
    "Australia": "Australian Plate",
    "Caribbean": "Caribbean Plate",
    "Cocos": "Cocos Plate",
    "Eurasia": "Eurasian Plate",
    "India": "Indian Plate",
    "Juan de Fuca": "Juan de Fuca Plate",
    "Nazca": "Nazca Plate",
    "North America": "North American Plate",
    "Pacific": "Pacific Plate",
    "Philippine Sea": "Philippine Sea Plate",
    "South America": "South American Plate",
    "Scotia": "Scotia Plate",
    "Somalia": "Somali Plate",
}


def _world_polygon_bundle(
    scope_name: str,
    title: str,
    noun: str,
    families: list[str],
    geoms_by_name: dict[str, BaseGeometry],
) -> tuple[dict, dict, dict]:
    """Build a physical polygon scope on one consistent whole-world frame."""
    box_t = (-180.0, -90.0, 180.0, 90.0)
    width = 1500.0
    scale = width / (box_t[2] - box_t[0])
    view_w = width + 2 * PAD
    view_h = (box_t[3] - box_t[1]) * scale + 2 * PAD

    def project(lon, lat):
        return (lon - box_t[0]) * scale + PAD, (box_t[3] - lat) * scale + PAD

    regions = []
    source_geoms = {}
    for name, geom in geoms_by_name.items():
        rid = _slug(name)
        region = make_region(
            rid, name, "", "main", project_geom(geom, project), magnify_small=False
        )
        if region:
            regions.append(region)
            source_geoms[rid] = geom
    regions.sort(key=lambda r: r["name"])
    shapes = {rid: shape_payload(geom) for rid, geom in source_geoms.items()}

    land = unary_union([shape(f["geometry"]) for f in load_features("land110")])
    context = rings_of(project_geom(land, project).simplify(0.8, preserve_topology=True))
    bundle = {
        "scope": scope_name,
        "title": title,
        "noun": noun,
        "kind": "physical",
        "families": families,
        "view": {"w": round(view_w, 1), "h": round(view_h, 1)},
        "tray": [90.0, round(view_h - 90.0, 1)],
        "frames": [
            {
                "id": "main",
                "rect": [0.0, 0.0, round(view_w, 1), round(view_h, 1)],
                "kmPerUnit": round(EARTH_KM_PER_DEG / scale, 3),
                "label": "",
            }
        ],
        "context": context,
        "regions": regions,
    }
    return bundle, shapes, {}


def _build_lakes() -> tuple[dict, dict, dict]:
    features = {key: load_features(key) for key in {src for src, _ in LAKE_NAMES.values()}}
    geoms = {}
    for display, (source, source_names) in LAKE_NAMES.items():
        matched_features = [
            f
            for f in features[source]
            if prop(f["properties"], "NAME_EN", "NAME") in source_names
        ]
        found_names = {
            prop(f["properties"], "NAME_EN", "NAME") for f in matched_features
        }
        if found_names != source_names:
            raise SystemExit(
                f"world-lakes: expected source names {sorted(source_names)} for {display}, "
                f"found {sorted(found_names)}"
            )
        geoms[display] = unary_union([shape(f["geometry"]) for f in matched_features])
    return _world_polygon_bundle(
        "world-lakes",
        "World — Major Lakes",
        "lake",
        ["point", "place"],
        geoms,
    )


def _build_plates() -> tuple[dict, dict, dict]:
    grouped: dict[str, list[BaseGeometry]] = {name: [] for name in PLATE_NAMES}
    for feature in load_features("plates"):
        source_name = prop(feature["properties"], "PlateName")
        if source_name in grouped:
            grouped[source_name].append(shape(feature["geometry"]))
    missing = [name for name, geoms in grouped.items() if not geoms]
    if missing:
        raise SystemExit(f"world-tectonic-plates: missing {', '.join(missing)}")
    geoms = {
        PLATE_NAMES[source_name]: unary_union(parts)
        for source_name, parts in grouped.items()
    }
    bundle, shapes, capitals = _world_polygon_bundle(
        "world-tectonic-plates",
        "World — Major Tectonic Plates",
        "tectonic plate",
        ["point", "sketch"],
        geoms,
    )
    # Keep the natural in-card noun ("Which tectonic plate?") while giving the
    # generated deck/model a properly title-cased multiword family label.
    bundle["family_noun"] = "Tectonic Plate"
    return bundle, shapes, capitals


def _build_world_polys(scope_name: str, cfg: dict) -> tuple[dict, dict, dict]:
    box_t = cfg["box"]
    width = cfg.get("width", 1200.0)
    fclasses = cfg.get("featureclasses")
    max_sr = cfg.get("max_scalerank")
    exclude = cfg.get("exclude", set())

    feats = []
    for f in load_features(cfg["layer"]):
        props = f["properties"]
        name = prop(props, "NAME_EN", "NAME")
        if not name or name in exclude:
            continue
        if fclasses is not None and prop(props, "FEATURECLA") not in fclasses:
            continue
        if max_sr is not None and (prop(props, "SCALERANK") or 99) > max_sr:
            continue
        feats.append(f)

    lat0 = math.radians((box_t[1] + box_t[3]) / 2.0)
    cos0 = math.cos(lat0)
    x_span = (box_t[2] - box_t[0]) * cos0
    y_span = box_t[3] - box_t[1]
    scale = width / x_span
    view_w = width + 2 * PAD
    view_h = y_span * scale + 2 * PAD
    km_per_unit = (1.0 / scale) * EARTH_KM_PER_DEG

    def project(lon, lat):
        return (lon - box_t[0]) * cos0 * scale + PAD, (box_t[3] - lat) * scale + PAD

    regions = []
    geoms_by_id: dict[str, BaseGeometry] = {}
    seen: set[str] = set()
    for f in feats:
        name = prop(f["properties"], "NAME_EN", "NAME")
        norm = name.title() if name.isupper() else name
        rid = _slug(norm)
        if rid in seen:
            continue
        seen.add(rid)
        projected = project_geom(shape(f["geometry"]), project)
        region = make_region(rid, norm, "", "main", projected)
        if region:
            regions.append(region)
            geoms_by_id[rid] = shape(f["geometry"])

    regions.sort(key=lambda r: r["name"])
    shapes = {r["id"]: shape_payload(geoms_by_id[r["id"]]) for r in regions}

    # Land as neutral context so the seas read as water between continents.
    land = unary_union([shape(f["geometry"]) for f in load_features("land110")])
    context = rings_of(
        project_geom(land.intersection(box(*box_t)), project).simplify(0.8, preserve_topology=True)
    )

    return {
        "scope": scope_name,
        "title": cfg["title"],
        "noun": cfg.get("noun", "sea"),
        "kind": "physical",
        "families": cfg.get("families", ["point", "place", "draw"]),
        "view": {"w": round(view_w, 1), "h": round(view_h, 1)},
        "tray": [90.0, round(view_h - 90.0, 1)],
        "frames": [
            {"id": "main", "rect": [0.0, 0.0, round(view_w, 1), round(view_h, 1)],
             "kmPerUnit": round(km_per_unit, 3), "label": ""}
        ],
        "context": context,
        "regions": regions,
    }, shapes, {}  # no capitals


# ==================== rivers: named polylines on a world map ======================
# Rivers are LINES, not regions. The base bundle carries only the world land
# context + view; each river's polyline lives per-note (in the shapes slot, keyed
# by id, as {name, paths}). The engine's F9 "river" mode taps-to-locate and grades
# by distance to the nearest point on the line.

RIVER_SCOPES = {
    "world-rivers": {
        "title": "World — Major Rivers",
        "box": (-180.0, -55.0, 180.0, 78.0),
        "max_scalerank": 3,      # 1 = biggest; ≤3 keeps the iconic rivers
        "deck_root": "GeoTrainer::Physical::Rivers",
    },
}

# NE labels river segments by local name and includes delta distributaries. Map
# local/alt names onto one canonical English name (segments then MERGE into a
# more complete line), and drop delta arms / connectors that aren't a river a
# student would quiz.
RIVER_CANONICAL = {
    "Amazonas": "Amazon",
    "Huang": "Yellow", "Shiquan": "Yellow",
    "Ayeyarwady": "Irrawaddy",
    "Al Furat": "Euphrates", "Firat": "Euphrates",
    "Abay": "Blue Nile",
    "Ertis": "Irtysh",
    "Tongtian": "Yangtze", "Tuotuo": "Yangtze", "Za": "Yangtze",
    "Dihang": "Brahmaputra", "Nmai": "Brahmaputra", "Damqogkanbab": "Brahmaputra",
    "Lualaba": "Congo",
    "Ergun": "Amur", "Hailar": "Amur",
    "Ideriyn": "Selenge", "Selenge (Selenga)": "Selenge",
    "Mountain Nile": "White Nile", "Albert Nile": "White Nile", "Victoria Nile": "White Nile",
    "Grande": "Rio Grande",
    "Madison": "Missouri",
    "Uele": "Ubangi", "Kibali": "Ubangi",
    "Mamoré": "Madeira", "Guaporé": "Madeira",
    "Allegheny": "Ohio",
    "Shire": "Zambezi",
    "Slave": "Mackenzie",
}
RIVER_EXCLUDE = {
    "Bratul Chillia", "Bratul Sfintu Gheorghe", "Bratul Sulina",  # Danube delta arms
    "Bykovskaya Protoka", "Olenekskaya Protoka",                  # Lena delta arms
    "Damietta Branch", "Rosetta Branch",                          # Nile delta arms
    "Borcea",                                                     # Danube side-channel
    "St. Clair",                                                  # Great Lakes connector
    "Irrawaddy Delta",                                            # the delta, keep the river
    "Niagara",                                                    # short lake connector
    "Shatt al Arab",                                              # Tigris–Euphrates confluence
    "Weir", "Barwon",                                            # minor (keep Murray/Darling)
    "Teslin",                                                     # minor Yukon tributary
}


def _line_coords(geom):
    """All coordinate sequences of a (Multi)LineString geometry."""
    if geom["type"] == "LineString":
        return [geom["coordinates"]]
    if geom["type"] == "MultiLineString":
        return list(geom["coordinates"])
    return []


def _build_rivers(scope_name: str, cfg: dict) -> tuple[dict, dict, dict]:
    box_t = cfg["box"]
    width = cfg.get("width", 1400.0)
    max_sr = cfg.get("max_scalerank", 3)

    lat0 = math.radians((box_t[1] + box_t[3]) / 2.0)
    cos0 = math.cos(lat0)
    x_span = (box_t[2] - box_t[0]) * cos0
    y_span = box_t[3] - box_t[1]
    scale = width / x_span
    view_w = width + 2 * PAD
    view_h = y_span * scale + 2 * PAD
    km_per_unit = (1.0 / scale) * EARTH_KM_PER_DEG

    def project(lon, lat):
        return round((lon - box_t[0]) * cos0 * scale + PAD, 1), round((box_t[3] - lat) * scale + PAD, 1)

    # Group multi-segment rivers by canonical English display name.
    grouped: dict[str, dict] = {}
    for f in load_features("rivers"):
        props = f["properties"]
        if props.get("featurecla") != "River":
            continue
        if (props.get("scalerank") or 99) > max_sr:
            continue
        raw = props.get("name_en") or props.get("name")
        if not raw or raw in RIVER_EXCLUDE:
            continue
        name = RIVER_CANONICAL.get(raw, raw)  # merge local/alt names
        entry = grouped.setdefault(name, {"name": name, "paths": []})
        for seq in _line_coords(f["geometry"]):
            path = [project(lon, lat) for lon, lat in seq]
            if len(path) >= 2:
                entry["paths"].append(path)

    rivers = {}
    for name, entry in grouped.items():
        if not entry["paths"]:
            continue
        rivers[_slug(name)] = entry

    # Base map: world land as context (rivers read against the continents).
    land = unary_union([shape(f["geometry"]) for f in load_features("land110")])
    context = rings_of(
        project_geom(land.intersection(box(*box_t)), project).simplify(0.8, preserve_topology=True)
    )

    bundle = {
        "scope": scope_name,
        "title": cfg["title"],
        "noun": "river",
        "kind": "rivers",
        "families": ["river"],
        "view": {"w": round(view_w, 1), "h": round(view_h, 1)},
        "frames": [
            {"id": "main", "rect": [0.0, 0.0, round(view_w, 1), round(view_h, 1)],
             "kmPerUnit": round(km_per_unit, 3), "label": ""}
        ],
        "context": context,
        "regions": [],  # rivers are lines, carried per-note in the shapes slot
    }
    return bundle, rivers, {}


# ================= direction-aware schematic ocean-current routes =================
# These ordered centrelines are a study abstraction based on NOAA's global-current
# teaching diagrams. They encode the major route and direction a learner should
# remember; they are intentionally not a live velocity field or navigational data.
CURRENT_ROUTES = {
    "Gulf Stream": {
        "temperature": "warm",
        "coordinates": [
            (-82, 24), (-79, 29), (-75, 35), (-68, 40),
            (-55, 44), (-40, 48), (-25, 52), (-12, 55),
        ],
    },
    "Labrador Current": {
        "temperature": "cold",
        "coordinates": [(-58, 62), (-55, 55), (-53, 50), (-49, 45), (-45, 41)],
    },
    "Canary Current": {
        "temperature": "cold",
        "coordinates": [(-15, 40), (-18, 33), (-20, 25), (-22, 18), (-25, 12)],
    },
    "Brazil Current": {
        "temperature": "warm",
        "coordinates": [(-35, -8), (-38, -15), (-43, -23), (-48, -31), (-52, -38)],
    },
    "Benguela Current": {
        "temperature": "cold",
        "coordinates": [(15, -37), (12, -30), (10, -23), (10, -15), (8, -7)],
    },
    "Kuroshio Current": {
        "temperature": "warm",
        "coordinates": [(122, 18), (126, 23), (132, 28), (138, 33), (145, 37), (155, 40)],
    },
    "California Current": {
        "temperature": "cold",
        "coordinates": [(-135, 44), (-130, 38), (-125, 32), (-120, 25)],
    },
    "Humboldt Current": {
        "temperature": "cold",
        "coordinates": [(-77, -45), (-75, -35), (-73, -25), (-72, -15), (-77, -5)],
    },
    "East Australian Current": {
        "temperature": "warm",
        "coordinates": [(153, -15), (154, -23), (153, -30), (149, -36), (144, -41)],
    },
    "West Australian Current": {
        "temperature": "cold",
        "coordinates": [(108, -35), (110, -28), (112, -20), (115, -13)],
    },
    "Agulhas Current": {
        "temperature": "warm",
        "coordinates": [(47, -16), (43, -22), (38, -28), (32, -34), (27, -39)],
    },
    "North Equatorial Current": {
        "temperature": "warm",
        "coordinates": [(-18, 15), (-35, 14), (-55, 13), (-75, 12)],
    },
}


def _build_currents() -> tuple[dict, dict, dict]:
    box_t = (-180.0, -60.0, 180.0, 80.0)
    width = 1400.0
    scale = width / (box_t[2] - box_t[0])
    view_w = width + 2 * PAD
    view_h = (box_t[3] - box_t[1]) * scale + 2 * PAD

    def project(lon, lat):
        return [
            round((lon - box_t[0]) * scale + PAD, 1),
            round((box_t[3] - lat) * scale + PAD, 1),
        ]

    currents = {}
    for name, route in CURRENT_ROUTES.items():
        currents[_slug(name)] = {
            "name": name,
            "temperature": route["temperature"],
            # A route is ordered from origin toward destination. The engine uses
            # those endpoints to detect a reversed (otherwise accurate) trace.
            "paths": [[project(lon, lat) for lon, lat in route["coordinates"]]],
        }

    land = unary_union([shape(f["geometry"]) for f in load_features("land110")])
    context = rings_of(
        project_geom(land.intersection(box(*box_t)), lambda lon, lat: project(lon, lat))
        .simplify(0.8, preserve_topology=True)
    )
    bundle = {
        "scope": "world-ocean-currents",
        "title": "World — Major Ocean Currents",
        "noun": "ocean current",
        "kind": "currents",
        "families": ["current"],
        "view": {"w": round(view_w, 1), "h": round(view_h, 1)},
        "frames": [
            {
                "id": "main",
                "rect": [0.0, 0.0, round(view_w, 1), round(view_h, 1)],
                "kmPerUnit": round(EARTH_KM_PER_DEG / scale, 3),
                "label": "",
            }
        ],
        "context": context,
        "regions": [],
    }
    return bundle, currents, {}


# ---------------------------------------------------------------------------------

SCOPES = {"us-states": build_us_states}
for _name, _cfg in PHYSICAL_SCOPES.items():
    SCOPES[_name] = (lambda n, c: (lambda: _build_world_polys(n, c)))(_name, _cfg)
for _name, _cfg in RIVER_SCOPES.items():
    SCOPES[_name] = (lambda n, c: (lambda: _build_rivers(n, c)))(_name, _cfg)
SCOPES["world-lakes"] = _build_lakes
SCOPES["world-tectonic-plates"] = _build_plates
SCOPES["world-ocean-currents"] = _build_currents
for _name, _cfg in CONTINENT_SCOPES.items():
    SCOPES[_name] = (lambda n, c: (lambda: _build_continent(n, c)))(_name, _cfg)
for _name, _cfg in CONTINENTS_SCOPES.items():
    SCOPES[_name] = (lambda n, c: (lambda: _build_continents(n, c)))(_name, _cfg)
for _name, _cfg in SUBDIVISION_SCOPES.items():
    SCOPES[_name] = (lambda n, c: (lambda: _build_admin1_country(n, c)))(_name, _cfg)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", default="all", choices=["all", *SCOPES.keys()])
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    names = list(SCOPES) if args.scope == "all" else [args.scope]
    for name in names:
        bundle, shapes, capitals = SCOPES[name]()
        out_path = OUT_DIR / f"{name}.json"
        out_path.write_text(json.dumps(bundle, separators=(",", ":")), encoding="utf-8")
        shapes_path = OUT_DIR / f"{name}-shapes.json"
        shapes_path.write_text(json.dumps(shapes, separators=(",", ":")), encoding="utf-8")
        caps_path = OUT_DIR / f"{name}-capitals.json"
        caps_path.write_text(json.dumps(capitals, separators=(",", ":")), encoding="utf-8")
        n = len(bundle["regions"])
        tier1 = sum(1 for r in bundle["regions"] if r.get("tier", 1) == 1)
        small = sum(1 for r in bundle["regions"] if r.get("small"))
        size_kb = out_path.stat().st_size / 1024
        print(f"wrote {out_path}")
        print(
            f"  regions: {n} (tier1: {tier1}, small: {small}) | capitals: {len(capitals)} | "
            f"view: {bundle['view']['w']}x{bundle['view']['h']} | {size_kb:.1f} KB"
        )


if __name__ == "__main__":
    main()
