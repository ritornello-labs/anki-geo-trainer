"""Build the compact world-islands bundle used by GeoTrainer globe placement."""

from __future__ import annotations

import json
import math
import shutil
import urllib.request
from pathlib import Path

from shapely.geometry import MultiPolygon, mapping, shape
from shapely.geometry.polygon import orient

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
BUNDLE_DIR = ROOT / "data" / "bundles"
NE_BASE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"

SOURCES = {
    "anchors": "ne_110m_land.geojson",
    "land": "ne_50m_land.geojson",
    "admin0": "ne_10m_admin_0_countries.geojson",
}

PACIFIC_CODES = [
    "FJI",
    "VUT",
    "SLB",
    "NCL",
    "WSM",
    "ASM",
    "TON",
    "WLF",
    "TUV",
    "NIU",
    "COK",
    "PYF",
    "PCN",
    "NRU",
    "KIR",
    "MHL",
    "FSM",
    "PLW",
    "GUM",
    "MNP",
    "NFK",
]

# Global expansion stays restricted to island countries and territories. Continental
# countries with offshore islands are intentionally excluded because their administrative
# geometry would turn this into another general country-location deck.
GLOBAL_ISLAND_CODES = [
    "ABW",
    "AIA",
    "ATG",
    "BHS",
    "BMU",
    "BRB",
    "COM",
    "CPV",
    "CUB",
    "CUW",
    "CYM",
    "CYP",
    "DMA",
    "DOM",
    "FLK",
    "FRO",
    "GRD",
    "HTI",
    "IDN",
    "IMN",
    "IRL",
    "ISL",
    "JAM",
    "JPN",
    "KNA",
    "LCA",
    "LKA",
    "MDG",
    "MDV",
    "MLT",
    "MSR",
    "MUS",
    "PHL",
    "PRI",
    "SGP",
    "SHN",
    "SPM",
    "STP",
    "SYC",
    "TCA",
    "TLS",
    "TTO",
    "TWN",
    "VCT",
    "VGB",
    "VIR",
]

ISLAND_CODES = PACIFIC_CODES + GLOBAL_ISLAND_CODES

FRONT_MIN_POLYGON_AREA_DEG2 = 1.5


def ensure_source(key: str) -> Path:
    filename = SOURCES[key]
    path = RAW_DIR / filename
    if path.exists():
        return path
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    url = NE_BASE + filename
    print(f"downloading {url} -> {path}")
    with urllib.request.urlopen(url) as response, path.open("wb") as output:
        shutil.copyfileobj(response, output)
    return path


def read_feature_collection(key: str) -> dict:
    return json.loads(ensure_source(key).read_text(encoding="utf-8"))


def rounded(value):
    if isinstance(value, float):
        # Five decimals (~1 m latitude) keeps tiny atoll triangles from changing winding
        # when serialized for D3's spherical polygon rules.
        return round(value, 5)
    if isinstance(value, tuple | list):
        return [rounded(item) for item in value]
    if isinstance(value, dict):
        return {key: rounded(item) for key, item in value.items()}
    return value


def feature(geometry, properties: dict | None = None) -> dict:
    return {
        "type": "Feature",
        "properties": properties or {},
        "geometry": rounded(mapping(geometry)),
    }


def orient_for_d3(geometry):
    """D3 spherical GeoJSON expects clockwise exterior rings for small polygons."""
    if isinstance(geometry, MultiPolygon):
        return MultiPolygon([orient(polygon, sign=-1.0) for polygon in geometry.geoms])
    return orient(geometry, sign=-1.0)


def build_anchor_layer(collection: dict) -> dict:
    """Keep continents and large island landmasses while omitting small islands."""
    out = []
    for source_feature in collection["features"]:
        geometry = shape(source_feature["geometry"])
        polygons = geometry.geoms if isinstance(geometry, MultiPolygon) else [geometry]
        for polygon in polygons:
            if polygon.area < FRONT_MIN_POLYGON_AREA_DEG2:
                continue
            simplified = orient_for_d3(polygon.simplify(0.18, preserve_topology=True))
            if not simplified.is_empty:
                out.append(feature(simplified))
    return {"type": "FeatureCollection", "features": out}


def build_land_layer(collection: dict) -> dict:
    """Keep every Natural Earth 1:50m land polygon for the answer reference globe."""
    out = []
    for source_feature in collection["features"]:
        geometry = orient_for_d3(
            shape(source_feature["geometry"]).simplify(0.06, preserve_topology=True)
        )
        if not geometry.is_empty:
            out.append(feature(geometry))
    return {"type": "FeatureCollection", "features": out}


def display_name(properties: dict) -> str:
    return (
        properties.get("NAME_EN")
        or properties.get("NAME_LONG")
        or properties.get("ADMIN")
        or properties["NAME"]
    )


def spherical_mean(points: list[list[float]]) -> list[float]:
    x = y = z = 0.0
    for lon, lat in points:
        lon_r = math.radians(lon)
        lat_r = math.radians(lat)
        x += math.cos(lat_r) * math.cos(lon_r)
        y += math.cos(lat_r) * math.sin(lon_r)
        z += math.sin(lat_r)
    lon = math.degrees(math.atan2(y, x))
    lat = math.degrees(math.atan2(z, math.hypot(x, y)))
    return [round(lon, 5), round(lat, 5)]


def angular_distance_km(first: list[float], second: list[float]) -> float:
    lon1, lat1 = map(math.radians, first)
    lon2, lat2 = map(math.radians, second)
    cosine = (
        math.sin(lat1) * math.sin(lat2)
        + math.cos(lat1) * math.cos(lat2) * math.cos(lon1 - lon2)
    )
    return 6371.0088 * math.acos(max(-1.0, min(1.0, cosine)))


def build_targets(collection: dict) -> dict:
    by_code = {item["properties"].get("ADM0_A3"): item for item in collection["features"]}
    missing = sorted(set(ISLAND_CODES) - set(by_code))
    if missing:
        raise RuntimeError(f"Natural Earth is missing configured target codes: {missing}")

    targets = []
    for code in ISLAND_CODES:
        source_feature = by_code[code]
        properties = source_feature["properties"]
        source_geometry = shape(source_feature["geometry"])
        polygons = (
            list(source_geometry.geoms)
            if isinstance(source_geometry, MultiPolygon)
            else [source_geometry]
        )
        components = []
        for polygon in polygons:
            point = polygon.representative_point()
            components.append([round(point.x, 5), round(point.y, 5)])
        focus = spherical_mean(components)
        extent_km = max(angular_distance_km(focus, point) for point in components)
        geometry = orient_for_d3(source_geometry.simplify(0.01, preserve_topology=True))
        label_lon = float(properties["LABEL_X"])
        label_lat = float(properties["LABEL_Y"])
        targets.append(
            feature(
                geometry,
                {
                    "key": code.lower(),
                    "code": code,
                    "name": display_name(properties),
                    "lon": round(label_lon, 5),
                    "lat": round(label_lat, 5),
                    "subregion": properties.get("SUBREGION") or "Oceania",
                    "components": components,
                    "focus": focus,
                    "extent_km": round(extent_km),
                    "pilot": code in PACIFIC_CODES,
                },
            )
        )
    return {"type": "FeatureCollection", "features": targets}


def main() -> None:
    anchors_source = read_feature_collection("anchors")
    land_source = read_feature_collection("land")
    admin0_source = read_feature_collection("admin0")

    targets = build_targets(admin0_source)
    bundle = {
        "version": 2,
        "source": "Natural Earth 1:110m, 1:50m, and 1:10m",
        "anchors": build_anchor_layer(anchors_source),
        "land": build_land_layer(land_source),
        "targets": targets,
    }

    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)
    output = BUNDLE_DIR / "world-islands.json"
    output.write_text(
        json.dumps(bundle, ensure_ascii=True, separators=(",", ":")),
        encoding="utf-8",
    )
    target_count = len(bundle["targets"]["features"])
    print(f"wrote {output} ({output.stat().st_size:,} bytes, {target_count} targets)")


if __name__ == "__main__":
    main()
