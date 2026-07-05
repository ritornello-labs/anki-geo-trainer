"""Emit the exact rendered card HTML (as Anki would produce it) to a fixture.

This lets the Playwright suite verify the *shipped* inlined form — base64 bundle
+ brace-guarded engine + {{RegionId}} substituted — actually boots in real
browser engines, not just the raw engine source. Mirrors the "verify rendered
output, not just state" workspace lesson.
"""

from __future__ import annotations

from pathlib import Path

from build_apkg import build_templates

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tests" / "fixtures"
TARGET = "US-CA"


def render(side_html: str, css: str) -> str:
    # Anki substitutes {{RegionId}}; reproduce that for the fixture.
    body = side_html.replace("{{RegionId}}", TARGET)
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<style>{css}</style></head><body>{body}</body></html>"
    )


def main() -> None:
    front, back, css = build_templates()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "card-front.html").write_text(render(front, css), encoding="utf-8")
    (OUT / "card-back.html").write_text(render(back, css), encoding="utf-8")
    print(f"wrote {OUT / 'card-front.html'}")
    print(f"wrote {OUT / 'card-back.html'}")


if __name__ == "__main__":
    main()
