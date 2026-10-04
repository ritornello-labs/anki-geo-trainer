"""Build the reference-lines/world-time QA subdecks."""

from __future__ import annotations

import argparse
import base64
import json
import re
from pathlib import Path

import genanki

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "reference-lines-time-qa.json"
GLOBE = ROOT / "data" / "bundles" / "world-islands.json"
ENGINE = ROOT / "engine" / "reference-lines-qa.js"
TEMPLATE_DIR = ROOT / "anki" / "reference-lines"
OUTPUT = ROOT / "dist" / "reference-lines-time-qa-v2.apkg"
MODEL_ID = 1_607_431_001
DECK_ROOT = "GeoTrainer::Reference Lines & Time"
DECK_IDS = {stage: 1_607_431_110 + stage for stage in range(1, 5)}
MODEL_NAME = "Reference Lines & Time — QA v2"
STAGES = {
    1: "01 Coordinates",
    2: "02 Solar lines",
    3: "03 Date Line",
    4: "04 UTC",
}
SUBDECKS = {
    1: "01 Coordinates",
    2: "02 Tropics and Polar Circles",
    3: "03 International Date Line",
    4: "04 UTC Foundations",
}


def guard_js(source: str) -> str:
    if re.search(r"</script", source, flags=re.IGNORECASE):
        raise ValueError("inlined JavaScript closes its own script element")
    return source.replace("{{", "{ {").replace("}}", "} }")


def runtime_script() -> str:
    d3_array = (ROOT / "node_modules" / "d3-array" / "dist" / "d3-array.min.js").read_text(
        encoding="utf-8"
    )
    d3_geo = (ROOT / "node_modules" / "d3-geo" / "dist" / "d3-geo.min.js").read_text(
        encoding="utf-8"
    )
    engine = ENGINE.read_text(encoding="utf-8")
    source_globe = json.loads(GLOBE.read_text(encoding="utf-8"))
    bundle = {"anchors": source_globe["anchors"]}
    bundle64 = base64.b64encode(json.dumps(bundle, separators=(",", ":")).encode()).decode()
    boot = (
        'window.__GEO_REFERENCE_QA_BUNDLE__=JSON.parse(atob("'
        + bundle64
        + '"));window.GeoReferenceQA.mount(document.querySelector("[data-reference-qa]"),'
        + "window.__GEO_REFERENCE_QA_BUNDLE__);"
    )
    return guard_js("\n".join((d3_array, d3_geo, engine, boot)))


def load_cards() -> list[dict]:
    cards = json.loads(DATA.read_text(encoding="utf-8"))
    keys = [card["key"] for card in cards]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate QA keys")
    if [card["stage"] for card in cards] != sorted(card["stage"] for card in cards):
        raise ValueError("QA stages are out of order")
    for card in cards:
        if card["mode"] == "line":
            if card["axis"] not in ("lat", "lon"):
                raise ValueError(card["key"])
            if not -180 <= card["target"] <= 180:
                raise ValueError(card["key"])
        elif card["mode"] == "recall":
            if not card.get("answer") or card.get("grading") not in ("short", "self"):
                raise ValueError(card["key"])
        elif card["mode"] == "clock":
            if card.get("randomized") is not True:
                raise ValueError(card["key"])
        else:
            raise ValueError(card["key"])
        if card.get("figure") not in (None, "tropical-belt", "polar-circles",
                                      "date-line-role", "date-line-crossing"):
            raise ValueError(f"unknown figure: {card['key']}")
        if not card["source"].startswith("https://"):
            raise ValueError(card["key"])
    return cards


def reference_decks(only_keys: set[str] | None = None) -> list:
    cards = load_cards()
    if only_keys is not None:
        unknown = only_keys - {card["key"] for card in cards}
        if unknown:
            raise ValueError(f"unknown QA keys: {sorted(unknown)}")
        cards = [card for card in cards if card["key"] in only_keys]
    runtime = runtime_script()
    front = (TEMPLATE_DIR / "front.html").read_text(encoding="utf-8")
    back = (TEMPLATE_DIR / "back.html").read_text(encoding="utf-8")
    model = genanki.Model(
        MODEL_ID,
        MODEL_NAME,
        fields=[{"name": name} for name in ("Key", "Prompt", "Stage", "Payload", "Explanation", "Source")],
        templates=[{
            "name": "Drill",
            "qfmt": front + "\n<script>\n" + runtime + "\n</script>",
            "afmt": back + "\n<script>\n" + runtime + "\n</script>",
        }],
        css=(TEMPLATE_DIR / "card.css").read_text(encoding="utf-8"),
        sort_field_index=0,
    )
    decks = {stage: genanki.Deck(DECK_IDS[stage], f"{DECK_ROOT}::{name}")
             for stage, name in SUBDECKS.items()}
    for card in cards:
        payload = base64.b64encode(json.dumps(card, ensure_ascii=False, separators=(",", ":")).encode()).decode()
        note = genanki.Note(
            model=model,
            fields=[card["key"], card["prompt"], STAGES[card["stage"]], payload,
                    "", card["source"]],
            tags=["ai-created", "geo-reference::qa",
                  f"geo-reference::stage::{card['stage']}", f"geo-reference::skill::{card['mode']}"],
            guid=genanki.guid_for("reference-lines-time-qa-v2", card["key"]),
        )
        decks[card["stage"]].add_note(note)
    return [deck for deck in decks.values() if deck.notes]


def build(output: Path = OUTPUT, only_keys: set[str] | None = None) -> Path:
    decks = reference_decks(only_keys)
    cards = [note for deck in decks for note in deck.notes]
    output.parent.mkdir(parents=True, exist_ok=True)
    genanki.Package(decks).write_to_file(output)
    print(f"wrote {output} ({len(cards)} notes/cards, {output.stat().st_size / 1024:.0f} KiB)")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--keys", nargs="+", help="Build only these exact card keys")
    args = parser.parse_args()
    build(args.output, set(args.keys) if args.keys else None)
