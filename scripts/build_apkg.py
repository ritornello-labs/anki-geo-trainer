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
# Redesign 2026-07 (Elvis's study feedback): Locate and Capital dropped (locate
# was trivial/redundant with all borders shown; capital duplicated his Cities
# deck). Point + Place survive but now render a BORDERLESS front, and Draw's
# scoring was made honest. River is now trace-the-course (draw), not tap-locate.
# A full delete+reimport of the GeoTrainer tree accompanies the renumbering, so
# ords need not preserve old ids.
FAMILY_DEFS = [
    ("point", 0, "Which {Noun}", "1 Which {Noun}", "geotrainer::skill::point", "geotrainer::level::4"),
    ("place", 1, "Place", "2 Place", "geotrainer::skill::place", "geotrainer::level::5"),
    ("draw", 2, "Draw", "3 Draw", "geotrainer::skill::draw", "geotrainer::level::6"),
    ("river", 3, "Trace", "1 Trace", "geotrainer::skill::river", "geotrainer::level::5"),
]

# Families a scope gets when it doesn't declare its own. River is opt-in (river
# scopes only, via the bundle's `families`).
DEFAULT_FAMILIES = ["point", "place", "draw"]

SCOPE_PACKS = {
    "us-states": {
        "deck_root": "GeoTrainer::World::North America::United States",
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
    "north-america-countries": {
        "deck_root": "GeoTrainer::World::North America",
        "model_root": "GeoTrainer {family} — North America",
        "scope_tag": "geotrainer::scope::continent::north-america",
        "model_base": 1_607_411_001,
        "deck_base": 1_607_411_050,
        "apkg": "geo-trainer-north-america.apkg",
    },
    "continents": {
        # Draw-only single silhouettes (South America, North America, Africa).
        # Top-level (peer of World/Physical) so the continent Draw deck is easy
        # to find rather than buried under World.
        "deck_root": "GeoTrainer::Continents",
        "model_root": "GeoTrainer {family} — Continents",
        "scope_tag": "geotrainer::scope::world::continents",
        "model_base": 1_607_412_001,
        "deck_base": 1_607_412_050,
        "apkg": "geo-trainer-continents.apkg",
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
    "russia-subjects": {
        "deck_root": "GeoTrainer::World::Europe::Russia",
        "model_root": "GeoTrainer {family} — Russia Subjects",
        "scope_tag": "geotrainer::scope::country::russia::subjects",
        "model_base": 1_607_399_001,
        "deck_base": 1_607_399_050,
        "apkg": "geo-trainer-russia-subjects.apkg",
    },
    "china-provinces": {
        "deck_root": "GeoTrainer::World::Asia::China",
        "model_root": "GeoTrainer {family} — China Provinces",
        "scope_tag": "geotrainer::scope::country::china::provinces",
        "model_base": 1_607_400_001,
        "deck_base": 1_607_400_050,
        "apkg": "geo-trainer-china-provinces.apkg",
    },
    "canada-provinces": {
        "deck_root": "GeoTrainer::World::North America::Canada",
        "model_root": "GeoTrainer {family} — Canada Provinces",
        "scope_tag": "geotrainer::scope::country::canada::provinces",
        "model_base": 1_607_401_001,
        "deck_base": 1_607_401_050,
        "apkg": "geo-trainer-canada-provinces.apkg",
    },
    "australia-states": {
        "deck_root": "GeoTrainer::World::Oceania::Australia",
        "model_root": "GeoTrainer {family} — Australia States",
        "scope_tag": "geotrainer::scope::country::australia::states",
        "model_base": 1_607_402_001,
        "deck_base": 1_607_402_050,
        "apkg": "geo-trainer-australia-states.apkg",
    },
    "argentina-provinces": {
        "deck_root": "GeoTrainer::World::South America::Argentina",
        "model_root": "GeoTrainer {family} — Argentina Provinces",
        "scope_tag": "geotrainer::scope::country::argentina::provinces",
        "model_base": 1_607_403_001,
        "deck_base": 1_607_403_050,
        "apkg": "geo-trainer-argentina-provinces.apkg",
    },
    "mexico-states": {
        "deck_root": "GeoTrainer::World::North America::Mexico",
        "model_root": "GeoTrainer {family} — Mexico States",
        "scope_tag": "geotrainer::scope::country::mexico::states",
        "model_base": 1_607_404_001,
        "deck_base": 1_607_404_050,
        "apkg": "geo-trainer-mexico-states.apkg",
    },
    "indonesia-provinces": {
        "deck_root": "GeoTrainer::World::Asia::Indonesia",
        "model_root": "GeoTrainer {family} — Indonesia Provinces",
        "scope_tag": "geotrainer::scope::country::indonesia::provinces",
        "model_base": 1_607_405_001,
        "deck_base": 1_607_405_050,
        "apkg": "geo-trainer-indonesia-provinces.apkg",
    },
    "oceania-countries": {
        "deck_root": "GeoTrainer::World::Oceania",
        "model_root": "GeoTrainer {family} — Oceania",
        "scope_tag": "geotrainer::scope::continent::oceania",
        "model_base": 1_607_406_001,
        "deck_base": 1_607_406_050,
        "apkg": "geo-trainer-oceania.apkg",
    },
    "world-rivers": {
        "deck_root": "GeoTrainer::Physical::Rivers",
        "model_root": "GeoTrainer {family} — Rivers",
        "scope_tag": "geotrainer::scope::physical::rivers",
        "model_base": 1_607_408_001,
        "deck_base": 1_607_408_050,
        "apkg": "geo-trainer-world-rivers.apkg",
    },
    "world-ranges": {
        "deck_root": "GeoTrainer::Physical::Mountain Ranges",
        "model_root": "GeoTrainer {family} — Mountain Ranges",
        "scope_tag": "geotrainer::scope::physical::ranges",
        "model_base": 1_607_409_001,
        "deck_base": 1_607_409_050,
        "apkg": "geo-trainer-world-ranges.apkg",
    },
    "world-deserts": {
        "deck_root": "GeoTrainer::Physical::Deserts",
        "model_root": "GeoTrainer {family} — Deserts",
        "scope_tag": "geotrainer::scope::physical::deserts",
        "model_base": 1_607_410_001,
        "deck_base": 1_607_410_050,
        "apkg": "geo-trainer-world-deserts.apkg",
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

    bundle_boot = ""
    if mode != "draw":
        b64 = base64.b64encode((BUNDLE_DIR / f"{scope}.json").read_bytes()).decode("ascii")
        bundle_boot = (
            '<script>window.GT_BUNDLES=window.GT_BUNDLES||{};'
            f'window.GT_BUNDLES["{scope}"]=JSON.parse(atob("{b64}"));</script>'
        )

    if mode in ("draw", "river"):
        # Per-note geometry (draw outline / river polyline) in a base64 field, so
        # the substitution can't collide with markup. Draw needs no basemap;
        # rivers still inline the world-land bundle above.
        field = "ShapeData" if mode == "draw" else "RiverData"
        shape_boot = (
            "<script>window.GT_SHAPES=window.GT_SHAPES||{ };"
            f'window.GT_SHAPES["{scope}:" + "{{{{RegionId}}}}"]='
            f'JSON.parse(atob("{{{{{field}}}}}"));</script>'
        )
        boot = bundle_boot + shape_boot
    else:
        boot = bundle_boot

    # F8 capital cards carry the capital's name + projected point per note.
    cap_attrs = ' data-capname="{{CapitalName}}" data-cappt="{{CapitalPt}}"' if mode == "capital" else ""

    def side(which: str) -> str:
        return (
            f'<div class="gt-app" data-scope="{scope}" data-mode="{mode}" '
            'data-target="{{RegionId}}" data-name="{{RegionName}}"' + cap_attrs + " "
            'data-side="' + which + '"></div>\n'
            f"{boot}\n{engine_tag}"
        )

    # Independent renders (no {{FrontSide}}): the back re-mounts in back mode
    # and reads front state from localStorage (window-global fallback inside).
    return side("front"), side("back"), css


def families_for(scope: str, pack: dict, test_ids: bool = False) -> list[dict]:
    bundle = load_bundle(scope)
    noun = bundle.get("noun", "region").capitalize()
    # A scope may declare which families make sense for it (physical scopes skip
    # place/capital; river scopes are river-only); default is the standard set.
    allowed = bundle.get("families") or DEFAULT_FAMILIES
    fams = []
    for mode, ord_, fam_label, deck_label, skill_tag, level_tag in FAMILY_DEFS:
        if mode not in allowed:
            continue
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


def load_capitals(scope: str) -> dict:
    return json.loads((BUNDLE_DIR / f"{scope}-capitals.json").read_text(encoding="utf-8"))


def _b64(obj) -> str:
    return base64.b64encode(json.dumps(obj, separators=(",", ":")).encode("ascii")).decode("ascii")


def notes_for(scope: str, model: genanki.Model, fam: dict, pack: dict) -> list[genanki.Note]:
    bundle = load_bundle(scope)
    shapes = load_shapes(scope) if fam["mode"] in ("draw", "river") else {}
    capitals = load_capitals(scope) if fam["mode"] == "capital" else {}

    # Rivers have no regions; each river is a shapes-file entry {name, paths}.
    if fam["mode"] == "river":
        notes = []
        for rid, river in sorted(shapes.items()):
            notes.append(
                genanki.Note(
                    model=model,
                    fields=[f"{scope}:{rid}", scope, rid, river["name"], _b64(river)],
                    guid=genanki.guid_for("geotrainer", scope, fam["guid_ns"], rid),
                    tags=[fam["skill_tag"], pack["scope_tag"], fam["level_tag"]],
                )
            )
        return notes

    notes = []
    for reg in bundle["regions"]:
        if reg.get("tier", 1) != 1:
            continue  # dependencies are map context, not quiz entities
        fields = [f"{scope}:{reg['id']}", scope, reg["id"], reg["name"]]
        if fam["mode"] == "draw":
            payload = shapes.get(reg["id"])
            if not payload:
                continue
            fields.append(
                base64.b64encode(
                    json.dumps(payload, separators=(",", ":")).encode("ascii")
                ).decode("ascii")
            )
        elif fam["mode"] == "capital":
            cap = capitals.get(reg["id"])
            if not cap or not cap.get("name"):
                continue  # no capital in the data for this region
            fields.append(cap["name"])
            fields.append(f"{cap['x']},{cap['y']}")
        notes.append(
            genanki.Note(
                model=model,
                fields=fields,
                guid=genanki.guid_for("geotrainer", scope, fam["guid_ns"], reg["id"]),
                tags=[fam["skill_tag"], pack["scope_tag"], fam["level_tag"]],
            )
        )
    return notes


def scope_decks(scope: str, test_ids: bool = False) -> tuple[list, int]:
    """Build (but do not write) the genanki decks for one scope."""
    pack = SCOPE_PACKS[scope]
    decks = []
    total = 0
    for fam in families_for(scope, pack, test_ids=test_ids):
        front, back, css = build_templates(scope, fam["mode"])
        # Field 0 "Key" (`scope:region_id`) is a unique natural key: Anki uses the
        # first field for duplicate detection and (here) as the sort field, so it
        # must be unique — the old first field "Scope" was constant per note type.
        fields = [{"name": "Key"}, {"name": "Scope"}, {"name": "RegionId"}, {"name": "RegionName"}]
        if fam["mode"] == "draw":
            fields.append({"name": "ShapeData"})
        elif fam["mode"] == "capital":
            fields.append({"name": "CapitalName"})
            fields.append({"name": "CapitalPt"})
        elif fam["mode"] == "river":
            fields.append({"name": "RiverData"})
        model = genanki.Model(
            fam["model_id"],
            fam["model_name"],
            fields=fields,
            templates=[{"name": fam["mode"].capitalize(), "qfmt": front, "afmt": back}],
            css=css,
            sort_field_index=0,  # the unique Key
        )
        deck = genanki.Deck(fam["deck_id"], fam["deck"])
        for note in notes_for(scope, model, fam, pack):
            deck.add_note(note)
        if not deck.notes:
            continue
        total += len(deck.notes)
        decks.append(deck)
    return decks, total


def build_scope(scope: str, test_ids: bool = False) -> Path:
    pack = SCOPE_PACKS[scope]
    decks, total = scope_decks(scope, test_ids=test_ids)
    DIST.mkdir(parents=True, exist_ok=True)
    out = DIST / (pack["apkg"] if not test_ids else pack["apkg"].replace(".apkg", "-test.apkg"))
    genanki.Package(decks).write_to_file(str(out))
    size_kb = out.stat().st_size / 1024
    print(f"wrote {out}  ({len(decks)} decks, {total} notes, {size_kb:.0f} KB)")
    return out


def build_combined() -> Path:
    """One shareable APKG holding the whole GeoTrainer tree — the single deck we
    publish on AnkiWeb so the listing and screenshots cover everything at once."""
    all_decks, total = [], 0
    for scope in SCOPE_PACKS:
        decks, n = scope_decks(scope)
        all_decks.extend(decks)
        total += n
    DIST.mkdir(parents=True, exist_ok=True)
    out = DIST / "geo-trainer-all.apkg"
    genanki.Package(all_decks).write_to_file(str(out))
    size_kb = out.stat().st_size / 1024
    print(f"wrote {out}  ({len(all_decks)} decks, {total} notes, {size_kb / 1024:.1f} MB)")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", default="all", choices=["all", *SCOPE_PACKS.keys()])
    ap.add_argument("--combined", action="store_true",
                    help="also write one geo-trainer-all.apkg with the whole tree")
    ap.add_argument("--test-ids", action="store_true",
                    help="offset ids and rename (emulator re-import testing only)")
    args = ap.parse_args()
    scopes = list(SCOPE_PACKS) if args.scope == "all" else [args.scope]
    for scope in scopes:
        build_scope(scope, test_ids=args.test_ids)
    if args.combined:
        build_combined()


if __name__ == "__main__":
    main()
