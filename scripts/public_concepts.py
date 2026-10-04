"""Accepted concept families shared by public components and their full union.

Deck identities are frozen from the existing family APKGs, including the four
families whose display grouping changed. Public names never derive new IDs.
"""
from __future__ import annotations

import base64
from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import re
import sys

import genanki

ROOT = Path(__file__).resolve().parent.parent
CONCEPTS = ROOT / "concepts"
sys.path.insert(0, str(CONCEPTS))
spec = importlib.util.spec_from_file_location("accepted_concept_builder", CONCEPTS / "scripts/build_family_apkgs.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

PACK_FAMILIES = {
    "physical-geography": ("peninsulas", "chokepoints", "capes", "mountain-ranges", "deserts", "plateaus-basins", "plains-grasslands", "biomes", "koppen", "koppen-letters"),
    "plate-tectonics": ("tectonic-plates", "minor-plates", "plate-boundaries", "named-boundaries"),
    "islands-archipelagos": ("islands-archipelagos",),
    "world-countries": ("regions-groupings", "country-blocs", "bloc-drill"),
}
PACK_ROOTS = {
    "physical-geography": "GeoTrainer::Physical Geography",
    "plate-tectonics": "GeoTrainer::Plate Tectonics",
    "islands-archipelagos": "GeoTrainer::Islands & Archipelagos",
    "world-countries": "GeoTrainer::World Countries",
}

def membership_deck():
    identities = json.loads((CONCEPTS / "deck-identities.json").read_text())
    data = json.loads((CONCEPTS / "families/data/country-blocs.json").read_text())
    research = json.loads((CONCEPTS / "families/research/country-blocs.json").read_text())
    bundle = (CONCEPTS / "families/data/world-countries-bundle.json").read_bytes()
    ids = {r["id"] for r in json.loads(bundle)["regions"]}
    engine = (ROOT / "engine/geo-engine.js").read_text()
    assert "</script>" not in engine
    engine = engine.replace("{{", "{ {").replace("}}", "} }")
    boot = '<script>window.GT_BUNDLES=window.GT_BUNDLES||{ };window.GT_BUNDLES["world-countries"]=JSON.parse(atob("' + base64.b64encode(bundle).decode() + '"));</script>'
    sets = '<script>window.GT_SETS=window.GT_SETS||{ };window.GT_SETS["world-countries:"+"{{slug}}"] = JSON.parse(atob("{{members_b64}}"));</script>'
    app = '<div class="gt-app" data-scope="world-countries" data-target="{{slug}}" data-side="%s" data-mode="members"></div>'
    tail = sets + boot + '<script>' + engine + '</script>'
    css = (ROOT / "anki/shared/card.css").read_text() + '''
.card { font-family: Arial, sans-serif; background: #f7f4ea; color: #1d1d1d; }
.drill-head { max-width: 960px; margin: 0 auto; padding: 16px 20px 0; font-size: 13px; letter-spacing: 0.08em; text-transform: uppercase; color: #3b5f8a; font-weight: 700; }
.gt-app { max-width: 960px; margin: 0 auto; padding: 8px 20px 24px; }
.card.nightMode, .nightMode .card { background: #1f2023; color: #e6e3dc; }
.nightMode .drill-head { color: #d8c48a; }
'''
    model = genanki.Model(builder.stable_id("model-v2", "Geo Bloc Drill"), "Geo Bloc Drill", fields=[{"name": n} for n in ("slug", "name", "members_b64", "member_count")], templates=[{"name": "2 Tap Members", "qfmt": '<div class="drill-head">Tap the members</div>' + app % "front" + tail, "afmt": '<div class="drill-head">{{name}}</div>' + app % "back" + tail}], css=css)
    deck = genanki.Deck(identities["bloc-drill"]["id"], PACK_ROOTS["world-countries"] + "::Concepts::Bloc Membership Drill")
    for concept in data["concepts"]:
        slug = concept["slug"]
        members = [c for c in research[slug]["member_codes"] if c in ids]
        if len(members) < 4:
            continue
        payload = {"name": concept["name"], "ids": members, "instruction": f"Tap every {concept['name']} member"}
        deck.add_note(genanki.Note(model=model, fields=[slug, concept["name"], base64.b64encode(json.dumps(payload).encode()).decode(), str(len(members))], guid=genanki.guid_for("v2", "Geo Bloc Drill", slug), tags=["geo::bloc-drill"]))
    assert len(deck.notes) == 59
    return deck

@lru_cache(maxsize=None)
def concept_pack(name: str):
    identities = json.loads((CONCEPTS / "deck-identities.json").read_text())
    wanted = set(PACK_FAMILIES.get(name, ()))
    decks, media = [], set()
    for family in builder.FAMILIES:
        if family.key not in wanted:
            continue
        deck, _ = builder.build_family(family, media)
        deck.deck_id = identities[family.key]["id"]
        deck.name = PACK_ROOTS[name] + "::Concepts::" + family.deck_path
        decks.append(deck)
    if "koppen" in wanted:
        for deck, _, files in builder.build_koppen():
            key = "koppen-letters" if "Letter" in deck.name else "koppen"
            suffix = deck.name.removeprefix(builder.DECK_ROOT + "::")
            deck.deck_id = identities[key]["id"]
            deck.name = PACK_ROOTS[name] + "::Concepts::" + suffix
            decks.append(deck)
            media.update(files)
    if "bloc-drill" in wanted:
        decks.append(membership_deck())
    # Every explicit local image reference must be included. Derived fields
    # intentionally left empty by the accepted builder stay empty.
    filenames = {Path(p).name for p in media}
    for deck in decks:
        for note in deck.notes:
            refs = {ref for field in note.fields for ref in re.findall(r'<img\b[^>]*\bsrc=["\']([^"\']+)', field, re.I)}
            missing = refs - filenames
            if missing:
                raise ValueError(f"Missing media in {deck.name}: {sorted(missing)}")
    return decks, sorted(media)
