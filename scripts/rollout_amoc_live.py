"""Import the four AMOC cards directly into the live manual-QA tree.

The default is a read-only preflight. ``--apply`` imports only the dedicated
four-card APKG, moves the exact tag-resolved cards to ``Process::GeoTrainer QA``,
and verifies that all 2,402 existing GeoTrainer cards remained unchanged.
No sync is performed.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "dist" / "geo-trainer-atlantic-overturning.apkg"
SNAPSHOTS = ROOT / "backups" / "live-imports"
DAILY_ROOT = "Decks::Geography::GeoTrainer"
QA_ROOT = "Process::GeoTrainer QA"
IMPORT_ROOT = "GeoTrainer"
DESTINATION = f"{QA_ROOT}::Physical::Ocean Currents::3 Trace Atlantic Overturning"
SCOPE_TAG = "geotrainer::scope::physical::ocean-currents::amoc"
EXPECTED_EXISTING = 2_402
EXPECTED_KEYS = [
    "atlantic-overturning:01-upper-limb",
    "atlantic-overturning:02-sinking-limb",
    "atlantic-overturning:03-deep-return-limb",
    "atlantic-overturning:04-complete-pathway",
]

SCHEDULING_FIELDS = (
    "cardId",
    "note",
    "deckName",
    "originalDeckName",
    "ord",
    "type",
    "queue",
    "due",
    "interval",
    "factor",
    "reps",
    "lapses",
    "left",
    "flags",
)


def invoke(action: str, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params}).encode()
    request = Request(
        "http://127.0.0.1:8765",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=120) as response:  # noqa: S310 - localhost API
        result = json.load(response)
    if result.get("error") is not None:
        raise RuntimeError(f"AnkiConnect {action}: {result['error']}")
    return result.get("result")


def chunks(values: list[int], size: int = 500):
    for start in range(0, len(values), size):
        yield values[start : start + size]


def cards_info(card_ids: list[int]) -> list[dict]:
    rows = []
    for batch in chunks(card_ids):
        rows.extend(invoke("cardsInfo", cards=batch))
    return sorted(rows, key=lambda row: row["cardId"])


def notes_info(note_ids: list[int]) -> list[dict]:
    rows = []
    for batch in chunks(note_ids):
        rows.extend(invoke("notesInfo", notes=batch))
    return sorted(rows, key=lambda row: row["noteId"])


def collect_all() -> dict:
    card_ids = sorted(invoke("findCards", query="tag:geotrainer::*"))
    cards = cards_info(card_ids)
    note_ids = sorted({card["note"] for card in cards})
    return {
        "cardIds": card_ids,
        "noteIds": note_ids,
        "cards": cards,
        "notes": notes_info(note_ids),
    }


def fingerprint(state: dict) -> str:
    return json.dumps(
        {"cards": state["cards"], "notes": state["notes"]},
        sort_keys=True,
        separators=(",", ":"),
    )


def scheduling(card: dict) -> dict:
    return {field: card.get(field) for field in SCHEDULING_FIELDS}


def normalized_note(note: dict) -> dict:
    return {
        "noteId": note["noteId"],
        "modelName": note["modelName"],
        "tags": sorted(note["tags"]),
        "fields": {
            name: value["value"] for name, value in sorted(note["fields"].items())
        },
    }


def write_snapshot(directory: Path, state: dict) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "state.json").write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def preflight() -> dict:
    if invoke("version") < 6:
        raise RuntimeError("AnkiConnect version 6 is required")
    if not PACKAGE.exists():
        raise RuntimeError(f"missing package: {PACKAGE}")

    state = collect_all()
    if len(state["cardIds"]) != EXPECTED_EXISTING:
        raise RuntimeError(
            f"expected {EXPECTED_EXISTING} existing GeoTrainer cards, "
            f"found {len(state['cardIds'])}"
        )
    if len(state["noteIds"]) != EXPECTED_EXISTING:
        raise RuntimeError("existing GeoTrainer notes are not one-card-per-note")
    existing_amoc = invoke("findCards", query=f"tag:{SCOPE_TAG}")
    if existing_amoc:
        raise RuntimeError(f"AMOC scope already has cards: {sorted(existing_amoc)}")
    import_cards = invoke("findCards", query=f'deck:"{IMPORT_ROOT}"')
    import_decks = [
        deck for deck in invoke("deckNames")
        if deck == IMPORT_ROOT or deck.startswith(IMPORT_ROOT + "::")
    ]
    if import_cards or import_decks:
        raise RuntimeError(
            f"temporary import root is not clean: {len(import_cards)} cards, "
            f"{len(import_decks)} decks"
        )
    return state


def verify(before: dict, after: dict, new_card_ids: list[int]) -> dict:
    before_cards = {card["cardId"]: card for card in before["cards"]}
    after_cards = {card["cardId"]: card for card in after["cards"]}
    before_notes = {note["noteId"]: note for note in before["notes"]}
    after_notes = {note["noteId"]: note for note in after["notes"]}

    if set(before_cards) - set(after_cards) or set(before_notes) - set(after_notes):
        raise RuntimeError("existing GeoTrainer identity was lost")
    scheduling_changes = [
        card_id
        for card_id, old in before_cards.items()
        if scheduling(old) != scheduling(after_cards[card_id])
    ]
    if scheduling_changes:
        raise RuntimeError(f"existing scheduling changed: {scheduling_changes}")
    note_changes = [
        note_id
        for note_id, old in before_notes.items()
        if normalized_note(old) != normalized_note(after_notes[note_id])
    ]
    if note_changes:
        raise RuntimeError(f"existing note content changed: {note_changes}")

    added_cards = sorted(set(after_cards) - set(before_cards))
    added_notes = sorted(set(after_notes) - set(before_notes))
    if added_cards != sorted(new_card_ids) or len(added_notes) != 4:
        raise RuntimeError(
            f"expected four exact additions, got {len(added_notes)} notes/"
            f"{len(added_cards)} cards"
        )

    new_cards = [after_cards[card_id] for card_id in added_cards]
    if any(card["deckName"] != DESTINATION for card in new_cards):
        raise RuntimeError("new AMOC cards are not all in the manual-QA deck")
    if any(card.get("originalDeckName") for card in new_cards):
        raise RuntimeError("a new AMOC card is captured by a filtered deck")
    if any(card["type"] != 0 or card["queue"] not in {0, -2, -3} for card in new_cards):
        raise RuntimeError("a new AMOC card is not in an eligible new-card state")

    note_by_id = {note["noteId"]: note for note in after["notes"]}
    ordered_cards = sorted(new_cards, key=lambda card: (card["due"], card["cardId"]))
    ordered_keys = [
        note_by_id[card["note"]]["fields"]["Key"]["value"]
        for card in ordered_cards
    ]
    if ordered_keys != EXPECTED_KEYS:
        raise RuntimeError(f"unexpected prerequisite order: {ordered_keys}")
    for note_id in added_notes:
        note = note_by_id[note_id]
        required = {"ai-created", SCOPE_TAG, "geotrainer::skill::amoc"}
        if not required.issubset(note["tags"]):
            raise RuntimeError(f"new note {note_id} is missing required tags")

    return {
        "beforeNotes": len(before_notes),
        "beforeCards": len(before_cards),
        "afterNotes": len(after_notes),
        "afterCards": len(after_cards),
        "addedNoteIds": added_notes,
        "addedCardIds": added_cards,
        "destination": DESTINATION,
        "orderedKeys": ordered_keys,
        "changedExistingNotes": len(note_changes),
        "changedExistingScheduling": len(scheduling_changes),
        "filteredDeckCollisions": 0,
        "syncPerformed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    before = preflight()
    if not args.apply:
        print(json.dumps({
            "audit": "ready",
            "existingNotes": len(before["noteIds"]),
            "existingCards": len(before["cardIds"]),
            "package": str(PACKAGE),
            "destination": DESTINATION,
        }, indent=2))
        return

    fresh = preflight()
    if fingerprint(before) != fingerprint(fresh):
        raise RuntimeError("live GeoTrainer state changed after preflight; aborting")

    stamp = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    snapshot_root = SNAPSHOTS / f"{stamp}-amoc"
    write_snapshot(snapshot_root / "before", before)
    invoke(
        "exportPackage",
        deck=DAILY_ROOT,
        path=str(snapshot_root / "before" / "daily-geotrainer.apkg"),
        includeSched=True,
    )
    invoke(
        "exportPackage",
        deck=QA_ROOT,
        path=str(snapshot_root / "before" / "qa-geotrainer.apkg"),
        includeSched=True,
    )

    invoke("importPackage", path=str(PACKAGE))
    new_card_ids = sorted(
        invoke("findCards", query=f"tag:{SCOPE_TAG} tag:ai-created")
    )
    if len(new_card_ids) != 4:
        raise RuntimeError(f"expected four imported AMOC cards, got {new_card_ids}")
    imported_cards = cards_info(new_card_ids)
    if any(
        not card["deckName"].startswith(IMPORT_ROOT + "::")
        for card in imported_cards
    ):
        raise RuntimeError("AMOC import did not land under the isolated import root")
    if any(card.get("originalDeckName") for card in imported_cards):
        raise RuntimeError("an imported AMOC card was captured by a filtered deck")

    invoke("changeDeck", cards=new_card_ids, deck=DESTINATION)
    strays = invoke("findCards", query=f'deck:"{IMPORT_ROOT}"')
    if strays:
        raise RuntimeError(f"temporary import root retains cards: {sorted(strays)}")
    invoke("deleteDecks", decks=[IMPORT_ROOT], cardsToo=True)

    after = collect_all()
    write_snapshot(snapshot_root / "after", after)
    report = verify(before, after, new_card_ids)
    (snapshot_root / "verification.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"snapshot: {snapshot_root}")


if __name__ == "__main__":
    main()
