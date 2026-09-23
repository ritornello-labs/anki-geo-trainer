"""Build the stable-identity GeoTrainer globe-placement deck."""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path

import genanki

ROOT = Path(__file__).resolve().parent.parent
BUNDLE = ROOT / "data" / "bundles" / "world-islands.json"
ENGINE = ROOT / "engine" / "globe-placement.js"
CSS = ROOT / "anki" / "globe-placement" / "card.css"
FRONT = ROOT / "anki" / "globe-placement" / "front.html"
BACK = ROOT / "anki" / "globe-placement" / "back.html"
DIST = ROOT / "dist"

# These IDs and GUIDs deliberately retain the accepted Island Globe deployment's
# identity, so importing the merged GeoTrainer package updates instead of duplicating it.
MODEL_ID = 1_607_420_001
DECK_ID = 1_607_420_100
MODEL_NAME = "Island Globe — Place"
DECK_NAME = "GeoTrainer::World::Islands::1 Globe Placement"
APKG_NAME = "geo-trainer-world-islands-globe.apkg"


def guard_js(source: str) -> str:
    if re.search(r"</script", source, flags=re.IGNORECASE):
        raise ValueError("inlined JavaScript contains a script-closing sequence")
    while "{{" in source or "}}" in source:
        source = source.replace("{{", "{ {").replace("}}", "} }")
    if "{{" in source or "}}" in source:
        raise ValueError("brace guard failed")
    return source


def runtime_script() -> str:
    d3_array = (ROOT / "node_modules/d3-array/dist/d3-array.min.js").read_text(
        encoding="utf-8"
    )
    d3_geo = (ROOT / "node_modules/d3-geo/dist/d3-geo.min.js").read_text(encoding="utf-8")
    engine = ENGINE.read_text(encoding="utf-8")
    bundle64 = base64.b64encode(BUNDLE.read_bytes()).decode("ascii")
    boot = (
        'window.__ISLAND_GLOBE_BUNDLE__=JSON.parse(atob("'
        + bundle64
        + '"));'
        + "window.IslandGlobe.mount(document.querySelector('[data-island-globe]'),"
        + "window.__ISLAND_GLOBE_BUNDLE__);"
    )
    return guard_js("\n".join((d3_array, d3_geo, engine, boot)))


def card_template(path: Path, runtime: str) -> str:
    return path.read_text(encoding="utf-8") + "\n<script>\n" + runtime + "\n</script>"


def live_template_payload() -> tuple[str, str, str]:
    runtime = runtime_script()
    return (
        card_template(FRONT, runtime),
        card_template(BACK, runtime),
        CSS.read_text(encoding="utf-8"),
    )


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def globe_deck(*, test_ids: bool = False) -> tuple[genanki.Deck, int]:
    front, back, css = live_template_payload()
    model_id = MODEL_ID + (7000 if test_ids else 0)
    deck_id = DECK_ID + (7000 if test_ids else 0)
    model_name = MODEL_NAME + (" (test)" if test_ids else "")
    deck_name = DECK_NAME.replace("GeoTrainer", "GeoTrainerTest", 1) if test_ids else DECK_NAME
    model = genanki.Model(
        model_id,
        model_name,
        fields=[{"name": name} for name in ("Key", "Territory", "Region")],
        templates=[
            {
                # Preserve the live card-template identity from the former standalone deck.
                "name": "Place",
                "qfmt": front,
                "afmt": back,
            }
        ],
        css=css,
        sort_field_index=0,
    )
    deck = genanki.Deck(deck_id, deck_name)
    bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
    for item in bundle["targets"]["features"]:
        properties = item["properties"]
        note = genanki.Note(
            model=model,
            fields=[properties["key"], properties["name"], properties["subregion"]],
            tags=[
                "geotrainer::skill::globe-placement",
                "geotrainer::scope::world::islands",
                "geotrainer::level::5",
                "geotrainer::region::" + slug(properties["subregion"]),
            ],
            guid=genanki.guid_for("island-globe", properties["key"]),
        )
        deck.add_note(note)
    return deck, len(deck.notes)


def build_globe_scope(*, test_ids: bool = False) -> Path:
    deck, total = globe_deck(test_ids=test_ids)
    DIST.mkdir(parents=True, exist_ok=True)
    filename = APKG_NAME.replace(".apkg", "-test.apkg") if test_ids else APKG_NAME
    output = DIST / filename
    genanki.Package(deck).write_to_file(output)
    print(f"wrote {output}  (1 deck, {total} notes, {output.stat().st_size / 1024:.0f} KB)")
    return output
