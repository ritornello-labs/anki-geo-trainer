"""Snapshot, import, relocate, and verify a GeoTrainer live update via AnkiConnect.

The default is read-only. Pass ``--apply`` only after building and testing
``dist/geo-trainer-all.apkg``.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
BACKUPS = ROOT / "backups" / "live-imports"
PACKAGE = ROOT / "dist" / "geo-trainer-all.apkg"
LIVE_ROOT = "Decks::Geography::GeoTrainer"
IMPORT_ROOT = "GeoTrainer"
EXPECTED_BEFORE = 2_338
EXPECTED_ADDED = 38

SCHEDULING_FIELDS = (
    "cardId",
    "note",
    "deckName",
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
    with urlopen(request, timeout=120) as response:  # noqa: S310 - intentional localhost API
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
    return rows


def notes_info(note_ids: list[int]) -> list[dict]:
    rows = []
    for batch in chunks(note_ids):
        rows.extend(invoke("notesInfo", notes=batch))
    return rows


def collect(deck_root: str) -> dict:
    card_ids = sorted(invoke("findCards", query=f'deck:"{deck_root}"'))
    cards = cards_info(card_ids)
    note_ids = sorted({card["note"] for card in cards})
    notes = notes_info(note_ids)
    return {
        "deckRoot": deck_root,
        "cardIds": card_ids,
        "noteIds": note_ids,
        "cards": cards,
        "notes": notes,
    }


def normalized_scheduling(card: dict) -> dict:
    return {field: card.get(field) for field in SCHEDULING_FIELDS}


def normalized_note(note: dict) -> dict:
    return {
        "noteId": note["noteId"],
        "modelName": note["modelName"],
        "tags": sorted(note["tags"]),
        "fields": {
            key: value["value"] for key, value in sorted(note["fields"].items())
        },
    }


def write_snapshot(directory: Path, state: dict) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    identity = {
        "deckRoot": state["deckRoot"],
        "noteCount": len(state["noteIds"]),
        "cardCount": len(state["cardIds"]),
        "noteIds": state["noteIds"],
        "cardIds": state["cardIds"],
    }
    (directory / "identity.json").write_text(
        json.dumps(identity, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (directory / "notes-info.json").write_text(
        json.dumps(state["notes"], indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (directory / "cards-scheduling.json").write_text(
        json.dumps(
            [normalized_scheduling(card) for card in state["cards"]],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def read_snapshot(directory: Path) -> dict:
    identity = json.loads((directory / "identity.json").read_text(encoding="utf-8"))
    return {
        "deckRoot": identity["deckRoot"],
        "cardIds": identity["cardIds"],
        "noteIds": identity["noteIds"],
        "cards": json.loads(
            (directory / "cards-scheduling.json").read_text(encoding="utf-8")
        ),
        "notes": json.loads((directory / "notes-info.json").read_text(encoding="utf-8")),
    }


def verify(before: dict, after: dict) -> dict:
    before_cards = {card["cardId"]: card for card in before["cards"]}
    after_cards = {card["cardId"]: card for card in after["cards"]}
    before_notes = {note["noteId"]: note for note in before["notes"]}
    after_notes = {note["noteId"]: note for note in after["notes"]}

    missing_cards = sorted(set(before_cards) - set(after_cards))
    missing_notes = sorted(set(before_notes) - set(after_notes))
    if missing_cards or missing_notes:
        raise RuntimeError(
            f"identity loss: {len(missing_notes)} notes, {len(missing_cards)} cards"
        )

    scheduling_changes = []
    for card_id, old in before_cards.items():
        if normalized_scheduling(old) != normalized_scheduling(after_cards[card_id]):
            scheduling_changes.append(card_id)
    if scheduling_changes:
        raise RuntimeError(f"original scheduling changed on {len(scheduling_changes)} cards")

    current_note_ids = {
        note_id
        for note_id, note in before_notes.items()
        if "geotrainer::skill::current" in note["tags"]
    }
    note_changes = {
        note_id
        for note_id, old in before_notes.items()
        if normalized_note(old) != normalized_note(after_notes[note_id])
    }
    unexpected_note_changes = note_changes - current_note_ids
    if unexpected_note_changes:
        raise RuntimeError(
            f"unexpected original note changes: {sorted(unexpected_note_changes)}"
        )

    added_cards = sorted(set(after_cards) - set(before_cards))
    added_notes = sorted(set(after_notes) - set(before_notes))
    if len(added_cards) != EXPECTED_ADDED or len(added_notes) != EXPECTED_ADDED:
        raise RuntimeError(
            f"expected {EXPECTED_ADDED} additions, got "
            f"{len(added_notes)} notes/{len(added_cards)} cards"
        )

    added_by_deck: dict[str, int] = defaultdict(int)
    for card_id in added_cards:
        added_by_deck[after_cards[card_id]["deckName"]] += 1
    expected_by_deck = {
        f"{LIVE_ROOT}::Physical::Tectonic Plates::2 Place": 16,
        f"{LIVE_ROOT}::Physical::Ocean Currents::1 Trace": 22,
    }
    if dict(added_by_deck) != expected_by_deck:
        raise RuntimeError(f"unexpected additions by deck: {dict(added_by_deck)}")

    key_to_note = {
        note["fields"]["Key"]["value"]: note for note in after["notes"]
    }
    atlantic = key_to_note["world-ocean-currents:north-equatorial-current"]
    if atlantic["fields"]["RegionName"]["value"] != "North Equatorial Current — Atlantic":
        raise RuntimeError("the existing Atlantic current note was not updated in place")

    return {
        "beforeNotes": len(before_notes),
        "beforeCards": len(before_cards),
        "afterNotes": len(after_notes),
        "afterCards": len(after_cards),
        "addedNotes": len(added_notes),
        "addedCards": len(added_cards),
        "addedByDeck": dict(added_by_deck),
        "changedOriginalCurrentNotes": len(note_changes),
        "changedOriginalScheduling": len(scheduling_changes),
        "missingOriginalNotes": len(missing_notes),
        "missingOriginalCards": len(missing_cards),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--resume-before",
        type=Path,
        help="finish cleanup/verification after an interrupted import using this snapshot",
    )
    args = parser.parse_args()

    stamp = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    before_dir = BACKUPS / f"{stamp}-before"
    after_dir = BACKUPS / f"{stamp}-after"

    if invoke("version") < 6:
        raise RuntimeError("AnkiConnect version 6 is required")

    if args.resume_before:
        before = read_snapshot(args.resume_before.resolve())
        strays = invoke("findCards", query=f'deck:"{IMPORT_ROOT}"')
        if strays:
            raise RuntimeError(f"cannot resume: {len(strays)} cards remain under import root")
        if any(
            deck == IMPORT_ROOT or deck.startswith(IMPORT_ROOT + "::")
            for deck in invoke("deckNames")
        ):
            # Anki 2.1.28+ requires cardsToo=True. The zero-card assertion above
            # makes this an empty-shell deletion, not a card deletion.
            invoke("deleteDecks", decks=[IMPORT_ROOT], cardsToo=True)
        after = collect(LIVE_ROOT)
        write_snapshot(after_dir, after)
        report = verify(before, after)
        (after_dir / "verification.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        print(f"before: {args.resume_before.resolve()}")
        print(f"after:  {after_dir}")
        return

    before = collect(LIVE_ROOT)
    write_snapshot(before_dir, before)
    if len(before["cardIds"]) != EXPECTED_BEFORE:
        raise RuntimeError(
            f"expected {EXPECTED_BEFORE} live cards before import, got {len(before['cardIds'])}"
        )
    rollback = before_dir / "geotrainer-before.apkg"
    invoke("exportPackage", deck=LIVE_ROOT, path=str(rollback), includeSched=True)

    if not args.apply:
        print(f"audit only: {len(before['noteIds'])} notes/{len(before['cardIds'])} cards")
        print(f"snapshot: {before_dir}")
        return

    if not PACKAGE.exists():
        raise RuntimeError(f"missing package: {PACKAGE}")
    invoke("importPackage", path=str(PACKAGE))

    imported_ids = sorted(invoke("findCards", query=f'deck:"{IMPORT_ROOT}"'))
    imported = cards_info(imported_ids)
    by_source_deck: dict[str, list[int]] = defaultdict(list)
    for card in imported:
        source = card["deckName"]
        if not source.startswith(IMPORT_ROOT + "::"):
            raise RuntimeError(f"unexpected imported deck: {source}")
        by_source_deck[source].append(card["cardId"])
    for source, card_ids in sorted(by_source_deck.items()):
        destination = "Decks::Geography::" + source
        invoke("changeDeck", cards=card_ids, deck=destination)

    strays = invoke("findCards", query=f'deck:"{IMPORT_ROOT}"')
    if strays:
        raise RuntimeError(f"{len(strays)} cards remain under the temporary import root")
    # Anki 2.1.28+ requires cardsToo=True. The zero-card assertion above makes
    # this an empty-shell deletion, not a card deletion.
    invoke("deleteDecks", decks=[IMPORT_ROOT], cardsToo=True)

    after = collect(LIVE_ROOT)
    write_snapshot(after_dir, after)
    report = verify(before, after)
    (after_dir / "verification.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"before: {before_dir}")
    print(f"after:  {after_dir}")


if __name__ == "__main__":
    main()
