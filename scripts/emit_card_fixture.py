"""Emit the exact rendered card HTML (as Anki would produce it) to fixtures.

This lets the Playwright suite verify the *shipped* inlined form — base64 bundle
(or per-note ShapeData/RiverData/CurrentData field) + brace-guarded engine + {{fields}}
substituted — actually boots in real browser engines, not just the raw engine
source. One front/back pair per (scope, family). Mirrors the "verify rendered
output, not just state" lesson.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

from build_apkg import (
    DEFAULT_FAMILIES,
    FAMILY_DEFS,
    build_templates,
    load_bundle,
    load_capitals,
    load_shapes,
)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tests" / "fixtures"

# One representative target per fixture scope (must have all the data its
# families need — a capital, a drawable shape, etc.).
FIXTURE_TARGETS = {
    "us-states": "US-CA",
    "europe-countries": "FRA",
    "world-rivers": "amazon",
    "world-ocean-currents": "gulf-stream",
}


def _b64(obj) -> str:
    return base64.b64encode(json.dumps(obj, separators=(",", ":")).encode("ascii")).decode("ascii")


def render(side_html: str, css: str, scope: str, target: str, mode: str) -> str:
    bundle = load_bundle(scope)
    if mode in ("river", "current"):
        name = load_shapes(scope)[target]["name"]
    else:
        name = next(r["name"] for r in bundle["regions"] if r["id"] == target)
    body = side_html.replace("{{RegionId}}", target).replace("{{RegionName}}", name)
    if "{{ShapeData}}" in body:
        body = body.replace("{{ShapeData}}", _b64(load_shapes(scope)[target]))
    if "{{RiverData}}" in body:
        body = body.replace("{{RiverData}}", _b64(load_shapes(scope)[target]))
    if "{{CurrentData}}" in body:
        body = body.replace("{{CurrentData}}", _b64(load_shapes(scope)[target]))
    if "{{CapitalName}}" in body:
        cap = load_capitals(scope)[target]
        body = body.replace("{{CapitalName}}", cap["name"]).replace(
            "{{CapitalPt}}", f"{cap['x']},{cap['y']}"
        )
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<style>{css}</style></head><body>{body}</body></html>"
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for scope, target in FIXTURE_TARGETS.items():
        bundle = load_bundle(scope)
        allowed = bundle.get("families") or DEFAULT_FAMILIES
        for mode, *_ in FAMILY_DEFS:
            if mode not in allowed:
                continue
            front, back, css = build_templates(scope, mode)
            (OUT / f"card-{scope}-{mode}-front.html").write_text(
                render(front, css, scope, target, mode), encoding="utf-8"
            )
            (OUT / f"card-{scope}-{mode}-back.html").write_text(
                render(back, css, scope, target, mode), encoding="utf-8"
            )
        print(f"wrote fixtures for {scope}")


if __name__ == "__main__":
    main()
