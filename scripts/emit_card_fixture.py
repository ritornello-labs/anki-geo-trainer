"""Emit the exact rendered card HTML (as Anki would produce it) to fixtures.

This lets the Playwright suite verify the *shipped* inlined form — base64 bundle
(or per-note ShapeData field for draw) + brace-guarded engine + {{fields}}
substituted — actually boots in real browser engines, not just the raw engine
source. One front/back pair per (scope, family). Mirrors the "verify rendered
output, not just state" lesson.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

from build_apkg import FAMILY_DEFS, build_templates, load_bundle, load_shapes

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tests" / "fixtures"

FIXTURE_TARGETS = {
    "us-states": "US-CA",
    "europe-countries": "FRA",
}


def render(side_html: str, css: str, scope: str, target: str) -> str:
    name = next(r["name"] for r in load_bundle(scope)["regions"] if r["id"] == target)
    body = side_html.replace("{{RegionId}}", target).replace("{{RegionName}}", name)
    if "{{ShapeData}}" in body:
        payload = load_shapes(scope)[target]
        b64 = base64.b64encode(
            json.dumps(payload, separators=(",", ":")).encode("ascii")
        ).decode("ascii")
        body = body.replace("{{ShapeData}}", b64)
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<style>{css}</style></head><body>{body}</body></html>"
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for scope, target in FIXTURE_TARGETS.items():
        for mode, *_ in FAMILY_DEFS:
            front, back, css = build_templates(scope, mode)
            (OUT / f"card-{scope}-{mode}-front.html").write_text(
                render(front, css, scope, target), encoding="utf-8"
            )
            (OUT / f"card-{scope}-{mode}-back.html").write_text(
                render(back, css, scope, target), encoding="utf-8"
            )
        print(f"wrote fixtures for {scope}")


if __name__ == "__main__":
    main()
