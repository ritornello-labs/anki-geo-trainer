"""Build the M0 GeoTrainer APKG: F3 Locate for the US states.

Anki-embedding strategy (the hard part):
  * The scope bundle is base64-encoded and decoded at runtime with
    atob()+JSON.parse(). base64's alphabet has no '{', '}', or '<', so the data
    can never collide with Anki's `{{field}}` templating or close a <script>.
    The bundle JSON is ASCII (ensure_ascii), so atob's Latin-1 output parses
    back cleanly (non-ASCII like the em dash rides along as \\uXXXX escapes).
  * The engine is inlined as readable JS, but every "{{" / "}}" is split with a
    space ("{ {" / "} }"). That is whitespace between tokens — always a no-op in
    JS code — so Anki never sees a field marker inside the engine. We also assert
    the engine contains no literal "</script>".

Everything is inlined into the note-type templates (no media), so AnkiDroid's
media server is never in the loop. The bundle lives in the template, i.e. once
per note type, not once per note.
"""

from __future__ import annotations

import base64
import re
from pathlib import Path

import genanki

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "engine" / "geo-engine.js"
CSS = ROOT / "anki" / "shared" / "card.css"
BUNDLE = ROOT / "data" / "bundles" / "us-states.json"
OUT = ROOT / "dist" / "geo-trainer-us-states.apkg"

SCOPE = "us-states"

# Deterministic IDs so rebuilds update in place instead of duplicating.
MODEL_ID = 1_607_392_001
DECK_ID = 1_607_392_050


def guard_js(src: str) -> str:
    if "</script>" in src:
        raise SystemExit("engine contains literal </script>; handle before inlining")
    # Split adjacent braces so Anki's {{ }} parser never triggers inside code.
    src = src.replace("{{", "{ {").replace("}}", "} }")
    if "{{" in src or "}}" in src:
        raise SystemExit("brace guard failed")
    return src


def build_templates() -> tuple[str, str, str]:
    engine = guard_js(ENGINE.read_text(encoding="utf-8"))
    b64 = base64.b64encode(BUNDLE.read_bytes()).decode("ascii")
    css = CSS.read_text(encoding="utf-8")

    boot = (
        '<script>window.GT_BUNDLES=window.GT_BUNDLES||{};'
        f'window.GT_BUNDLES["{SCOPE}"]=JSON.parse(atob("{b64}"));</script>'
    )
    engine_tag = f"<script>{engine}</script>"

    front = (
        f'<div class="gt-app" data-scope="{SCOPE}" '
        'data-target="{{RegionId}}" data-side="front"></div>\n'
        f"{boot}\n{engine_tag}"
    )
    # Independent render (no {{FrontSide}}): the back re-mounts in back mode and
    # reads the tap from localStorage.
    back = (
        f'<div class="gt-app" data-scope="{SCOPE}" '
        'data-target="{{RegionId}}" data-side="back"></div>\n'
        f"{boot}\n{engine_tag}"
    )
    return front, back, css


def us_state_notes(model: genanki.Model) -> list[genanki.Note]:
    import json

    bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
    notes = []
    for reg in bundle["regions"]:
        note = genanki.Note(
            model=model,
            fields=[SCOPE, reg["id"], reg["name"]],
            # Stable guid keyed on region id so re-import updates the same note.
            guid=genanki.guid_for("geotrainer", SCOPE, reg["id"]),
            tags=[
                "geotrainer::skill::locate",
                "geotrainer::scope::country::usa::states",
                "geotrainer::level::3",
            ],
        )
        notes.append(note)
    return notes


def main() -> None:
    front, back, css = build_templates()
    model = genanki.Model(
        MODEL_ID,
        "GeoTrainer Locate — US States",
        fields=[{"name": "Scope"}, {"name": "RegionId"}, {"name": "RegionName"}],
        templates=[{"name": "Locate", "qfmt": front, "afmt": back}],
        css=css,
        sort_field_index=2,
    )
    deck = genanki.Deck(DECK_ID, "GeoTrainer::United States::States::Locate")
    for note in us_state_notes(model):
        deck.add_note(note)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    genanki.Package(deck).write_to_file(str(OUT))

    size_kb = OUT.stat().st_size / 1024
    # Rough report of the per-template inlined payload.
    tpl_kb = (len(front) + len(back)) / 1024
    print(f"wrote {OUT}")
    print(f"  notes:          {len(deck.notes)}")
    print(f"  apkg size:      {size_kb:.1f} KB")
    print(f"  inlined/card:   {tpl_kb:.1f} KB (front+back templates, stored once)")


if __name__ == "__main__":
    main()
