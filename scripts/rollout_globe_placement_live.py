"""Merge the accepted globe-placement family into the live GeoTrainer tree.

The default mode is read-only preflight. Pass ``--apply`` only after reviewing the
snapshot. This script deliberately does not sync; sync direction remains an operator
decision when a collection has queued full-sync work.
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import datetime
from pathlib import Path

from globe_placement import live_template_payload

ROOT = Path(__file__).resolve().parent.parent
ANKI_CONNECT = "http://127.0.0.1:8765"
MODEL_NAME = "Island Globe — Place"
DESTINATION = "Decks::Geography::GeoTrainer::World::Islands::1 Globe Placement"
OLD_DECKS = [
    "Process::Island Globe Experiments::1 Placement",
    "Process::Island Globe Experiments::2 Antipodes",
    "Process::Island Globe Experiments",
]

PLACE_NOTES = [
    1785542131866, 1785542131868, 1785542131870, 1785542131872, 1785542131874,
    1785542131876, 1785542131878, 1785542131880, 1785542131882, 1785542131884,
    1785542131886, 1785542131888, 1785542131890, 1785542131892, 1785542131894,
    1785542131896, 1785542131898, 1785542131900, 1785542131902, 1785542131904,
    1785542131906, 1785633491543, 1785633491545, 1785633491547, 1785633491549,
    1785633491551, 1785633491553, 1785633491555, 1785633491557, 1785633491559,
    1785633491561, 1785633491563, 1785633491565, 1785633491567, 1785633491569,
    1785633491571, 1785633491573, 1785633491575, 1785633491577, 1785633491579,
    1785633491581, 1785633491583, 1785633491585, 1785633491587, 1785633491589,
    1785633491591, 1785633491593, 1785633491595, 1785633491597, 1785633491599,
    1785633491601, 1785633491603, 1785633491605, 1785633491607, 1785633491609,
    1785633491611, 1785633491613, 1785633491615, 1785633491617, 1785633491619,
    1785633491621, 1785633491623, 1785633491625, 1785633491627, 1785633491629,
    1785633491631, 1785633491633,
]
PLACE_CARDS = [
    1785542131867, 1785542131869, 1785542131871, 1785542131873, 1785542131875,
    1785542131877, 1785542131879, 1785542131881, 1785542131883, 1785542131885,
    1785542131887, 1785542131889, 1785542131891, 1785542131893, 1785542131895,
    1785542131897, 1785542131899, 1785542131901, 1785542131903, 1785542131905,
    1785542131907, 1785633491544, 1785633491546, 1785633491548, 1785633491550,
    1785633491552, 1785633491554, 1785633491556, 1785633491558, 1785633491560,
    1785633491562, 1785633491564, 1785633491566, 1785633491568, 1785633491570,
    1785633491572, 1785633491574, 1785633491576, 1785633491578, 1785633491580,
    1785633491582, 1785633491584, 1785633491586, 1785633491588, 1785633491590,
    1785633491592, 1785633491594, 1785633491596, 1785633491598, 1785633491600,
    1785633491602, 1785633491604, 1785633491606, 1785633491608, 1785633491610,
    1785633491612, 1785633491614, 1785633491616, 1785633491618, 1785633491620,
    1785633491622, 1785633491624, 1785633491626, 1785633491628, 1785633491630,
    1785633491632, 1785633491634,
]
ANTIPODE_NOTES = [
    1785633491661, 1785633491663, 1785633491665, 1785633491667,
    1785633491669, 1785633491671, 1785633491673, 1785633491675,
]
ANTIPODE_CARDS = [
    1785633491662, 1785633491664, 1785633491666, 1785633491668,
    1785633491670, 1785633491672, 1785633491674, 1785633491676,
]


def invoke(action: str, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params}).encode()
    request = urllib.request.Request(
        ANKI_CONNECT, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.loads(response.read())
    if result["error"] is not None:
        raise RuntimeError(f"{action}: {result['error']}")
    return result["result"]


def compact_card(card: dict) -> dict:
    keys = (
        "cardId", "note", "deckName", "originalDeckName", "type", "queue", "due",
        "interval", "factor", "reps", "lapses", "left", "flags",
    )
    return {key: card.get(key) for key in keys}


def scheduling_signature(card: dict) -> dict:
    value = compact_card(card)
    value.pop("deckName")
    return value


def snapshot() -> dict:
    place_cards = [compact_card(card) for card in invoke("cardsInfo", cards=PLACE_CARDS)]
    antipode_cards = [compact_card(card) for card in invoke("cardsInfo", cards=ANTIPODE_CARDS)]
    place_notes = invoke("notesInfo", notes=PLACE_NOTES)
    antipode_notes = invoke("notesInfo", notes=ANTIPODE_NOTES)
    return {
        "placeCards": place_cards,
        "antipodeCards": antipode_cards,
        "placeNotes": place_notes,
        "antipodeNotes": antipode_notes,
        "modelTemplates": invoke("modelTemplates", modelName=MODEL_NAME),
        "modelStyling": invoke("modelStyling", modelName=MODEL_NAME),
    }


def validate_before(state: dict) -> None:
    if sorted(card["cardId"] for card in state["placeCards"]) != sorted(PLACE_CARDS):
        raise RuntimeError("placement card identity changed")
    if sorted(note["noteId"] for note in state["placeNotes"]) != sorted(PLACE_NOTES):
        raise RuntimeError("placement note identity changed")
    if sorted(card["cardId"] for card in state["antipodeCards"]) != sorted(ANTIPODE_CARDS):
        raise RuntimeError("antipode card identity changed")
    if sorted(note["noteId"] for note in state["antipodeNotes"]) != sorted(ANTIPODE_NOTES):
        raise RuntimeError("antipode note identity changed")
    if any(card["originalDeckName"] for card in state["placeCards"] + state["antipodeCards"]):
        raise RuntimeError("a target card is captured by a filtered deck")
    if any(
        card["type"] != 0 or card["queue"] != 0 or card["reps"] != 0
        or card["lapses"] != 0 or card["flags"] != 0
        for card in state["antipodeCards"]
    ):
        raise RuntimeError("an Antipodes card is no longer untouched; stop before deletion")
    if any(note["modelName"] != MODEL_NAME for note in state["placeNotes"]):
        raise RuntimeError("placement model identity changed")


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def apply(before: dict) -> dict:
    front, back, css = live_template_payload()
    invoke(
        "updateModelTemplates",
        model={"name": MODEL_NAME, "templates": {"Place": {"Front": front, "Back": back}}},
    )
    invoke("updateModelStyling", model={"name": MODEL_NAME, "css": css})
    invoke(
        "addTags",
        notes=PLACE_NOTES,
        tags=(
            "geotrainer::skill::globe-placement geotrainer::scope::world::islands "
            "geotrainer::level::5"
        ),
    )
    invoke(
        "removeTags",
        notes=PLACE_NOTES,
        tags=(
            "island-globe::skill::place island-globe::stage::1-pacific-placement "
            "island-globe::stage::3-global-placement"
        ),
    )
    invoke("changeDeck", cards=PLACE_CARDS, deck=DESTINATION)

    moved = [compact_card(card) for card in invoke("cardsInfo", cards=PLACE_CARDS)]
    if any(card["deckName"] != DESTINATION for card in moved):
        raise RuntimeError("placement move did not complete exactly")
    before_schedule = {
        card["cardId"]: scheduling_signature(card) for card in before["placeCards"]
    }
    after_schedule = {card["cardId"]: scheduling_signature(card) for card in moved}
    if before_schedule != after_schedule:
        raise RuntimeError("placement scheduling changed during the move")

    invoke("deleteNotes", notes=ANTIPODE_NOTES)
    for deck in OLD_DECKS:
        if invoke("findCards", query=f'deck:"{deck}"'):
            raise RuntimeError(f"obsolete deck is not empty: {deck}")
    invoke("deleteDecks", decks=OLD_DECKS, cardsToo=True)

    final_cards = [compact_card(card) for card in invoke("cardsInfo", cards=PLACE_CARDS)]
    final_notes = invoke("notesInfo", notes=PLACE_NOTES)
    if invoke("findNotes", query='note:"Island Globe — Antipode"'):
        raise RuntimeError("Antipodes notes remain after deletion")
    if any(card["deckName"] != DESTINATION for card in final_cards):
        raise RuntimeError("final placement deck membership is wrong")
    if {card["cardId"]: scheduling_signature(card) for card in final_cards} != before_schedule:
        raise RuntimeError("final placement scheduling differs from preflight")
    required = {
        "geotrainer::skill::globe-placement",
        "geotrainer::scope::world::islands",
        "geotrainer::level::5",
    }
    forbidden = {
        "island-globe::skill::place",
        "island-globe::stage::1-pacific-placement",
        "island-globe::stage::3-global-placement",
    }
    if any(not required.issubset(note["tags"]) or forbidden.intersection(note["tags"])
           for note in final_notes):
        raise RuntimeError("final placement tags are wrong")
    return {"placeCards": final_cards, "placeNotes": final_notes}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    stamp = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    output = ROOT / "backups" / "live-imports" / f"{stamp}-globe-placement-merge"
    output.mkdir(parents=True, exist_ok=False)

    before = snapshot()
    validate_before(before)
    write_json(output / "before.json", before)
    summary = {
        "placementCards": len(before["placeCards"]),
        "placementReviewed": sum(card["reps"] > 0 for card in before["placeCards"]),
        "antipodeCards": len(before["antipodeCards"]),
        "antipodesUntouched": True,
        "destination": DESTINATION,
        "applied": args.apply,
    }
    if not args.apply:
        write_json(output / "preflight.json", summary)
        print(json.dumps(summary, indent=2))
        return

    freshness = snapshot()
    validate_before(freshness)
    if freshness != before:
        raise RuntimeError("live Island Globe state changed after preflight; aborting")
    after = apply(before)
    write_json(output / "after.json", after)
    summary["finalPlacementCards"] = len(after["placeCards"])
    summary["finalAntipodeCards"] = 0
    write_json(output / "receipt.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
