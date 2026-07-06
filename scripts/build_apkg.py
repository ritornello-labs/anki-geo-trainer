"""Build GeoTrainer APKGs: one per scope, one note type per task family.

Anki-embedding strategy (the hard part):
  * The scope bundle is base64-encoded and decoded at runtime with
    atob()+JSON.parse(). base64's alphabet has no '{', '}', or '<', so the data
    can never collide with Anki's `{{field}}` templating or close a <script>.
    The bundle JSON is ASCII (ensure_ascii), so atob's Latin-1 output parses
    back cleanly.
  * The engine is inlined as readable JS, but every "{{" / "}}" is split with a
    space ("{ {" / "} }") — whitespace between tokens, a no-op in JS — so Anki
    never sees a field marker inside the engine. We also assert the engine
    contains no literal "</script>".

Everything is inlined into the note-type templates (no media), so AnkiDroid's
media server is never in the loop. The bundle lives in the template, i.e. once
per note type, not once per note.

Note selection:
  * tier-2 regions (dependencies) render on the map but get NO notes
  * the neighbors family only gets notes for regions with at least one land border
"""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

import genanki

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "engine" / "geo-engine.js"
CSS = ROOT / "anki" / "shared" / "card.css"
BUNDLE_DIR = ROOT / "data" / "bundles"
DIST = ROOT / "dist"

# Deterministic IDs so rebuilds update in place instead of duplicating.
# (us-states locate/point/place keep their M0/M1 ids so re-imports upgrade.)
# ord 3 is RETIRED: it was the tap-all-neighbors family, dropped 2026-07-05
# because the user's collection already drills borders (Country Borders deck).
# Never reuse ord 3 — those model/deck ids exist in live collections.
FAMILY_DEFS = [
    ("locate", 0, "Locate", "1 Locate", "geotrainer::skill::locate", "geotrainer::level::3"),
    ("point", 1, "Which {Noun}", "2 Which {Noun}", "geotrainer::skill::point", "geotrainer::level::4"),
    ("place", 2, "Place", "3 Place", "geotrainer::skill::place", "geotrainer::level::5"),
    ("draw", 4, "Draw", "4 Draw", "geotrainer::skill::draw", "geotrainer::level::6"),
]

SCOPE_PACKS = {
    "us-states": {
        "deck_root": "GeoTrainer::United States::States",
        "model_root": "GeoTrainer {family} — US States",
        "scope_tag": "geotrainer::scope::country::usa::states",
        "model_base": 1_607_392_001,   # locate=+0, point=+1, place=+2, neighbors=+3
        "deck_base": 1_607_392_050,
        "apkg": "geo-trainer-us-states.apkg",
    },
    "europe-countries": {
        "deck_root": "GeoTrainer::World::Europe",
        "model_root": "GeoTrainer {family} — Europe",
        "scope_tag": "geotrainer::scope::continent::europe",
        "model_base": 1_607_393_001,
        "deck_base": 1_607_393_050,
        "apkg": "geo-trainer-europe.apkg",
    },
    "south-america-countries": {
        "deck_root": "GeoTrainer::World::South America",
        "model_root": "GeoTrainer {family} — South America",
        "scope_tag": "geotrainer::scope::continent::south-america",
        "model_base": 1_607_394_001,
        "deck_base": 1_607_394_050,
        "apkg": "geo-trainer-south-america.apkg",
    },
    "africa-countries": {
        "deck_root": "GeoTrainer::World::Africa",
        "model_root": "GeoTrainer {family} — Africa",
        "scope_tag": "geotrainer::scope::continent::africa",
        "model_base": 1_607_395_001,
        "deck_base": 1_607_395_050,
        "apkg": "geo-trainer-africa.apkg",
    },
    "asia-countries": {
        "deck_root": "GeoTrainer::World::Asia",
        "model_root": "GeoTrainer {family} — Asia",
        "scope_tag": "geotrainer::scope::continent::asia",
        "model_base": 1_607_396_001,
        "deck_base": 1_607_396_050,
        "apkg": "geo-trainer-asia.apkg",
    },
    "brazil-states": {
        "deck_root": "GeoTrainer::World::South America::Brazil",
        "model_root": "GeoTrainer {family} — Brazil States",
        "scope_tag": "geotrainer::scope::country::brazil::states",
        "model_base": 1_607_397_001,
        "deck_base": 1_607_397_050,
        "apkg": "geo-trainer-brazil-states.apkg",
    },
    "india-states": {
        "deck_root": "GeoTrainer::World::Asia::India",
        "model_root": "GeoTrainer {family} — India States",
        "scope_tag": "geotrainer::scope::country::india::states",
        "model_base": 1_607_398_001,
        "deck_base": 1_607_398_050,
        "apkg": "geo-trainer-india-states.apkg",
    },
}


def load_bundle(scope: str) -> dict:
    return json.loads((BUNDLE_DIR / f"{scope}.json").read_text(encoding="utf-8"))


def guard_js(src: str) -> str:
    if "</script>" in src:
        raise SystemExit("engine contains literal </script>; handle before inlining")
    src = src.replace("{{", "{ {").replace("}}", "} }")
    if "{{" in src or "}}" in src:
        raise SystemExit("brace guard failed")
    return src


def build_templates(scope: str, mode: str) -> tuple[str, str, str]:
    engine = guard_js(ENGINE.read_text(encoding="utf-8"))
    css = CSS.read_text(encoding="utf-8")
    engine_tag = f"<script>{engine}</script>"

    if mode == "draw":
        # Draw needs no basemap — each NOTE carries its own outline in the
        # ShapeData field (base64, so field substitution can't collide with
        # markup). Template stays small; data lives per note.
        boot = (
            "<script>window.GT_SHAPES=window.GT_SHAPES||{ };"
            f'window.GT_SHAPES["{scope}:" + "{{{{RegionId}}}}"]='
            'JSON.parse(atob("{{ShapeData}}"));</script>'
        )
    else:
        b64 = base64.b64encode((BUNDLE_DIR / f"{scope}.json").read_bytes()).decode("ascii")
        boot = (
            '<script>window.GT_BUNDLES=window.GT_BUNDLES||{};'
            f'window.GT_BUNDLES["{scope}"]=JSON.parse(atob("{b64}"));</script>'
        )

    def side(which: str) -> str:
        return (
            f'<div class="gt-app" data-scope="{scope}" data-mode="{mode}" '
            'data-target="{{RegionId}}" data-name="{{RegionName}}" '
            'data-side="' + which + '"></div>\n'
            f"{boot}\n{engine_tag}"
        )

    # Independent renders (no {{FrontSide}}): the back re-mounts in back mode
    # and reads front state from localStorage (window-global fallback inside).
    return side("front"), side("back"), css


def families_for(scope: str, pack: dict, test_ids: bool = False) -> list[dict]:
    bundle = load_bundle(scope)
    noun = bundle.get("noun", "region").capitalize()
    fams = []
    for mode, ord_, fam_label, deck_label, skill_tag, level_tag in FAMILY_DEFS:
        fam_name = fam_label.replace("{Noun}", noun)
        fam = {
            "mode": mode,
            "model_id": pack["model_base"] + ord_,
            "deck_id": pack["deck_base"] + ord_,
            "model_name": pack["model_root"].replace("{family}", fam_name),
            "deck": f"{pack['deck_root']}::{deck_label.replace('{Noun}', noun)}",
            "skill_tag": skill_tag,
            "level_tag": level_tag,
            "guid_ns": mode,
        }
        if test_ids:
            fam["model_id"] += 7000
            fam["deck_id"] += 7000
            fam["model_name"] += " (test)"
            fam["deck"] = fam["deck"].replace("GeoTrainer", "GeoTrainerTest", 1)
            fam["guid_ns"] = mode + "-test"
        fams.append(fam)
    return fams


def load_shapes(scope: str) -> dict:
    return json.loads((BUNDLE_DIR / f"{scope}-shapes.json").read_text(encoding="utf-8"))


def notes_for(scope: str, model: genanki.Model, fam: dict, pack: dict) -> list[genanki.Note]:
    bundle = load_bundle(scope)
    shapes = load_shapes(scope) if fam["mode"] == "draw" else {}
    notes = []
    for reg in bundle["regions"]:
        if reg.get("tier", 1) != 1:
            continue  # dependencies are map context, not quiz entities
        fields = [scope, reg["id"], reg["name"]]
        if fam["mode"] == "draw":
            payload = shapes.get(reg["id"])
            if not payload:
                continue
            fields.append(
                base64.b64encode(
                    json.dumps(payload, separators=(",", ":")).encode("ascii")
                ).decode("ascii")
            )
        notes.append(
            genanki.Note(
                model=model,
                fields=fields,
                guid=genanki.guid_for("geotrainer", scope, fam["guid_ns"], reg["id"]),
                tags=[fam["skill_tag"], pack["scope_tag"], fam["level_tag"]],
            )
        )
    return notes


def build_scope(scope: str, test_ids: bool = False) -> Path:
    pack = SCOPE_PACKS[scope]
    decks = []
    total = 0
    for fam in families_for(scope, pack, test_ids=test_ids):
        front, back, css = build_templates(scope, fam["mode"])
        fields = [{"name": "Scope"}, {"name": "RegionId"}, {"name": "RegionName"}]
        if fam["mode"] == "draw":
            fields.append({"name": "ShapeData"})
        model = genanki.Model(
            fam["model_id"],
            fam["model_name"],
            fields=fields,
            templates=[{"name": fam["mode"].capitalize(), "qfmt": front, "afmt": back}],
            css=css,
            sort_field_index=2,
        )
        deck = genanki.Deck(fam["deck_id"], fam["deck"])
        for note in notes_for(scope, model, fam, pack):
            deck.add_note(note)
        if not deck.notes:
            continue
        total += len(deck.notes)
        decks.append(deck)

    DIST.mkdir(parents=True, exist_ok=True)
    out = DIST / (pack["apkg"] if not test_ids else pack["apkg"].replace(".apkg", "-test.apkg"))
    genanki.Package(decks).write_to_file(str(out))
    size_kb = out.stat().st_size / 1024
    print(f"wrote {out}  ({len(decks)} decks, {total} notes, {size_kb:.0f} KB)")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", default="all", choices=["all", *SCOPE_PACKS.keys()])
    ap.add_argument("--test-ids", action="store_true",
                    help="offset ids and rename (emulator re-import testing only)")
    args = ap.parse_args()
    scopes = list(SCOPE_PACKS) if args.scope == "all" else [args.scope]
    for scope in scopes:
        build_scope(scope, test_ids=args.test_ids)


if __name__ == "__main__":
    main()
