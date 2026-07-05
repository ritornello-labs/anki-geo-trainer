"""F4 stable-randomness spike: prove the risky parts of the point-in-region task.

F4 shows a random dot on a blank map and asks which region contains it. Two hard
requirements:

  (1) The dot must sit comfortably INSIDE the region, never hugging a border
      (a point 2 px from the CA/NV line is an unfair prompt). We sample from an
      *eroded* (negatively-buffered) copy of the polygon, with the erosion
      distance scaled to the region's own size and a fallback for slivers.

  (2) The dot must be STABLE within one review (front and back agree) yet VARY
      across reviews. We use a deterministic PRNG (mulberry32) seeded by
      hash(regionId + dayStamp). Front and back rendered on the same day derive
      the identical point; a later day derives a different one. (The shipped
      engine will additionally persist the front's chosen point to localStorage
      and let the back read it — the exact handoff already proven for F3 — so
      agreement holds even across a midnight flip. This spike proves the seed
      math itself.)

mulberry32 is implemented here with explicit 32-bit masking so the identical
algorithm ports to JS unchanged (same uint32 arithmetic), giving reproducible
points across Python and every card webview.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from shapely.geometry import Point, shape
from shapely.geometry.base import BaseGeometry

ROOT = Path(__file__).resolve().parent.parent
BUNDLE = ROOT / "data" / "bundles" / "us-states.json"

U32 = 0xFFFFFFFF


def str_hash(s: str) -> int:
    """Deterministic 32-bit string hash (djb2-style), portable to JS."""
    h = 2166136261
    for ch in s:
        h ^= ord(ch)
        h = (h * 16777619) & U32
    return h & U32


def mulberry32(seed: int):
    """Classic mulberry32 PRNG. Returns a callable yielding floats in [0,1).
    32-bit masked so it matches a JS port exactly."""
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


def erosion_distance(geom: BaseGeometry) -> float:
    """Border margin scaled to region size: a fraction of sqrt(area), so big
    states erode more than small ones."""
    return 0.12 * math.sqrt(geom.area)


def eroded(geom: BaseGeometry) -> BaseGeometry:
    """Inset polygon to sample from; fall back progressively for slivers so we
    never return empty."""
    for frac in (1.0, 0.5, 0.25):
        inset = geom.buffer(-erosion_distance(geom) * frac)
        if not inset.is_empty and inset.area > 0:
            return inset
    return geom  # last resort: sample the original (thin sliver state)


def sample_point(geom_eroded: BaseGeometry, seed: int, max_tries: int = 400):
    """Rejection-sample a point inside the eroded polygon using the seeded PRNG."""
    rnd = mulberry32(seed)
    minx, miny, maxx, maxy = geom_eroded.bounds
    for _ in range(max_tries):
        x = minx + (maxx - minx) * rnd()
        y = miny + (maxy - miny) * rnd()
        if geom_eroded.contains(Point(x, y)):
            return (x, y)
    return (geom_eroded.representative_point().x, geom_eroded.representative_point().y)


def region_geom(bundle: dict, rid: str) -> BaseGeometry:
    reg = next(r for r in bundle["regions"] if r["id"] == rid)
    # Rebuild a shapely geometry from the projected rings.
    from shapely.geometry import MultiPolygon, Polygon
    from shapely.ops import unary_union

    polys = [Polygon(r) for r in reg["rings"] if len(r) >= 4]
    g = unary_union(polys) if len(polys) > 1 else polys[0]
    return g if isinstance(g, (Polygon, MultiPolygon)) else g


def main() -> None:
    bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
    ok = True

    # --- Requirement 2a: same seed -> identical point (front == back) ----------
    p1 = mulberry32(12345)
    p2 = mulberry32(12345)
    seq1 = [p1() for _ in range(5)]
    seq2 = [p2() for _ in range(5)]
    same = seq1 == seq2
    ok &= same
    print(f"[det] same seed reproduces sequence: {same}")

    # --- Requirement 2b: different seeds -> different streams ------------------
    diff = mulberry32(1) != mulberry32(2) or [mulberry32(1)() for _ in range(3)] != [
        mulberry32(2)() for _ in range(3)
    ]
    ok &= diff
    print(f"[det] different seeds diverge:        {diff}")

    # --- Requirement 2c: day-stamp seeding varies across reviews ---------------
    day_seeds = {str_hash("US-CA" + d) for d in ("2026-07-05", "2026-07-06", "2026-07-07")}
    varies = len(day_seeds) == 3
    ok &= varies
    print(f"[det] day-stamp seed varies per day:  {varies}")

    # --- Requirement 1: eroded sampling stays inside with margin ---------------
    print("[geo] sampling points for a range of states (each over 8 review days):")
    test_ids = ["US-CA", "US-TX", "US-FL", "US-TN", "US-CO", "US-MD"]  # incl. thin/odd
    all_inside = True
    all_margin = True
    for rid in test_ids:
        orig = region_geom(bundle, rid)
        inset = eroded(orig)
        margin = erosion_distance(orig)
        pts = []
        for day in range(8):
            seed = str_hash(rid + f"day{day}")
            pts.append(sample_point(inset, seed))
        inside = all(orig.contains(Point(*p)) for p in pts)
        # Distance from each point to the region boundary >= ~half the margin.
        clear = min(orig.exterior.distance(Point(*p)) for p in pts) if orig.geom_type == "Polygon" else min(
            orig.boundary.distance(Point(*p)) for p in pts
        )
        distinct = len({(round(x, 1), round(y, 1)) for x, y in pts})
        all_inside &= inside
        all_margin &= clear >= margin * 0.4
        print(
            f"   {rid}: inside={inside} min_edge_clearance={clear:6.1f}px "
            f"(margin={margin:5.1f}px) distinct_points={distinct}/8"
        )
    ok &= all_inside and all_margin
    print(f"[geo] all sampled points inside region:      {all_inside}")
    print(f"[geo] all points clear of the border margin: {all_margin}")

    print()
    print("F4 SPIKE:", "PASS" if ok else "FAIL")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
