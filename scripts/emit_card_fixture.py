"""Emit the exact rendered card HTML (as Anki would produce it) to fixtures.

This lets the Playwright suite verify the *shipped* inlined form — base64 bundle
+ brace-guarded engine + {{RegionId}} substituted — actually boots in real
browser engines, not just the raw engine source. One front/back pair per
(scope, family). Mirrors the "verify rendered output, not just state" lesson.
"""

from __future__ import annotations

from pathlib import Path

from build_apkg import SCOPE_PACKS, FAMILY_DEFS, build_templates

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tests" / "fixtures"

FIXTURE_TARGETS = {
    "us-states": "US-CA",
    "europe-countries": "FRA",
}


def render(side_html: str, css: str, target: str) -> str:
    body = side_html.replace("{{RegionId}}", target)
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
                render(front, css, target), encoding="utf-8"
            )
            (OUT / f"card-{scope}-{mode}-back.html").write_text(
                render(back, css, target), encoding="utf-8"
            )
        print(f"wrote fixtures for {scope}")


if __name__ == "__main__":
    main()
