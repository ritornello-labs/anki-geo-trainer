from __future__ import annotations

import json
import zipfile
from pathlib import Path

from shapely.geometry import MultiPolygon, shape

ROOT = Path(__file__).resolve().parent.parent


def test_generated_bundle_has_sparse_front_and_complete_back() -> None:
    bundle = json.loads((ROOT / "data/bundles/world-islands.json").read_text())
    targets = bundle["targets"]["features"]
    assert len(targets) == 67
    assert sum(item["properties"]["pilot"] for item in targets) == 21
    assert {item["properties"]["key"] for item in targets} >= {"cok", "fji", "ton", "pyf"}
    assert len(bundle["land"]["features"]) > len(bundle["anchors"]["features"])
    assert "exercises" not in bundle


def test_cook_islands_has_reference_point_and_geometry() -> None:
    bundle = json.loads((ROOT / "data/bundles/world-islands.json").read_text())
    cook = next(
        item for item in bundle["targets"]["features"] if item["properties"]["key"] == "cok"
    )
    assert cook["properties"]["name"] == "Cook Islands"
    assert -161 < cook["properties"]["lon"] < -158
    assert -23 < cook["properties"]["lat"] < -20
    assert cook["geometry"]["type"] == "MultiPolygon"
    assert len(cook["properties"]["components"]) == 13


def test_dispersed_archipelagos_keep_their_fine_components() -> None:
    bundle = json.loads((ROOT / "data/bundles/world-islands.json").read_text())
    counts = {
        item["properties"]["key"]: len(item["properties"]["components"])
        for item in bundle["targets"]["features"]
    }
    assert counts["kir"] == 35
    assert counts["pyf"] == 88
    assert counts["fsm"] == 20


def test_curated_focus_points_and_extents_cover_archipelagos() -> None:
    bundle = json.loads((ROOT / "data/bundles/world-islands.json").read_text())
    properties = {item["properties"]["key"]: item["properties"] for item in bundle["targets"]["features"]}
    assert properties["kir"]["extent_km"] > 3000
    assert properties["pyf"]["extent_km"] > 1000
    assert -180 <= properties["kir"]["focus"][0] <= 180
    assert -90 <= properties["kir"]["focus"][1] <= 90


def test_all_exterior_rings_are_clockwise_for_d3_spherical_fill() -> None:
    bundle = json.loads((ROOT / "data/bundles/world-islands.json").read_text())
    for layer in ("anchors", "land", "targets"):
        for item in bundle[layer]["features"]:
            geometry = shape(item["geometry"])
            polygons = geometry.geoms if isinstance(geometry, MultiPolygon) else [geometry]
            assert all(not polygon.exterior.is_ccw for polygon in polygons)


def test_apkg_contains_collection_and_media_manifest() -> None:
    output = ROOT / "dist/geo-trainer-world-islands-globe.apkg"
    assert output.exists()
    with zipfile.ZipFile(output) as archive:
        assert "collection.anki2" in archive.namelist()
        assert "media" in archive.namelist()
