"""Stage the physical-systems GeoTrainer batch under Process for manual QA.

The default is a read-only forward audit. ``--apply`` moves the exact 30-card
batch from the daily GeoTrainer tree to ``Process::GeoTrainer QA``. ``--restore``
moves that same tag-defined batch back after manual QA. All operations use
AnkiConnect and verify that only deck assignment changed.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOTS = ROOT / "backups" / "live-moves"
DAILY_ROOT = "Decks::Geography::GeoTrainer"
QA_ROOT = "Process::GeoTrainer QA"

TARGETS = (
    (
        "geotrainer::scope::physical::atmosphere::cells",
        "Physical::Atmospheric Circulation::1 Trace Cells",
        6,
    ),
    (
        "geotrainer::scope::physical::atmosphere::pressure-belts",
        "Physical::Atmospheric Circulation::2 Place Pressure Belts",
        4,
    ),
    (
        "geotrainer::scope::physical::atmosphere::prevailing-winds",
        "Physical::Atmospheric Circulation::3 Trace Prevailing Winds",
        6,
    ),
    (
        "geotrainer::scope::physical::atmosphere::jet-streams",
        "Physical::Atmospheric Circulation::4 Trace Jet Streams",
        4,
    ),
    (
        "geotrainer::scope::physical::atmosphere::monsoon",
        "Physical::Atmospheric Circulation::5 Trace Seasonal Monsoon Winds",
        2,
    ),
    (
        "geotrainer::scope::physical::ocean-currents::monsoon",
        "Physical::Ocean Currents::2 Trace Seasonal Monsoon Currents",
        4,
    ),
    (
        "geotrainer::scope::physical::ocean-currents::amoc",
        "Physical::Ocean Currents::3 Trace Atlantic Overturning",
        4,
    ),
)

EXPECTED_TOTAL = sum(count for _, _, count in TARGETS)

SCHEDULING_FIELDS = (
    "cardId",
    "note",
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
    return rows


def notes_info(note_ids: list[int]) -> list[dict]:
    rows = []
    for batch in chunks(note_ids):
        rows.extend(invoke("notesInfo", notes=batch))
    return rows


def expected_deck(root: str, suffix: str) -> str:
    return f"{root}::{suffix}"


def collect(expected_root: str) -> dict:
    card_ids: list[int] = []
    expected_by_card: dict[int, str] = {}
    counts: dict[str, int] = {}
    for tag, suffix, count in TARGETS:
        ids = sorted(invoke("findCards", query=f"tag:{tag} tag:ai-created"))
        if len(ids) != count:
            raise RuntimeError(f"{tag}: expected {count} cards, found {len(ids)}")
        deck = expected_deck(expected_root, suffix)
        counts[deck] = len(ids)
        for card_id in ids:
            if card_id in expected_by_card:
                raise RuntimeError(f"card {card_id} belongs to multiple target scopes")
            expected_by_card[card_id] = deck
        card_ids.extend(ids)

    if len(card_ids) != EXPECTED_TOTAL:
        raise RuntimeError(
            f"expected {EXPECTED_TOTAL} unique cards, found {len(card_ids)}"
        )
    cards = cards_info(sorted(card_ids))
    note_ids = sorted({card["note"] for card in cards})
    if len(note_ids) != EXPECTED_TOTAL:
        raise RuntimeError(
            f"expected {EXPECTED_TOTAL} unique notes, found {len(note_ids)}"
        )
    notes = notes_info(note_ids)

    filtered = []
    misplaced = []
    for card in cards:
        wanted = expected_by_card[card["cardId"]]
        if card["deckName"] == wanted:
            continue
        if card.get("originalDeckName") == wanted:
            filtered.append(card["cardId"])
        else:
            misplaced.append(
                {
                    "cardId": card["cardId"],
                    "expected": wanted,
                    "actual": card["deckName"],
                    "original": card.get("originalDeckName", ""),
                }
            )
    if filtered:
        raise RuntimeError(f"target cards are captured by a filtered deck: {filtered}")
    if misplaced:
        raise RuntimeError(f"target cards are in unexpected decks: {misplaced}")

    return {
        "root": expected_root,
        "cardIds": sorted(card_ids),
        "noteIds": note_ids,
        "cards": sorted(cards, key=lambda row: row["cardId"]),
        "notes": sorted(notes, key=lambda row: row["noteId"]),
        "expectedByCard": expected_by_card,
        "counts": counts,
    }


def write_snapshot(directory: Path, state: dict) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    serializable = {key: value for key, value in state.items() if key != "expectedByCard"}
    (directory / "state.json").write_text(
        json.dumps(serializable, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def state_fingerprint(state: dict) -> str:
    return json.dumps(
        {"cards": state["cards"], "notes": state["notes"]},
        sort_keys=True,
        separators=(",", ":"),
    )


def scheduling(card: dict) -> dict:
    return {field: card.get(field) for field in SCHEDULING_FIELDS}


def verify(before: dict, after: dict, destination_root: str) -> dict:
    if before["cardIds"] != after["cardIds"] or before["noteIds"] != after["noteIds"]:
        raise RuntimeError("target note/card identity changed during move")

    before_cards = {card["cardId"]: card for card in before["cards"]}
    after_cards = {card["cardId"]: card for card in after["cards"]}
    scheduling_changes = [
        card_id
        for card_id, old in before_cards.items()
        if scheduling(old) != scheduling(after_cards[card_id])
    ]
    if scheduling_changes:
        raise RuntimeError(f"scheduling changed on cards: {scheduling_changes}")
    if before["notes"] != after["notes"]:
        raise RuntimeError("note fields, tags, or note types changed during move")

    by_deck: dict[str, list[int]] = defaultdict(list)
    for card in after["cards"]:
        by_deck[card["deckName"]].append(card["cardId"])
    if {deck: len(ids) for deck, ids in by_deck.items()} != after["counts"]:
        raise RuntimeError(
            f"post-move deck membership does not match the {len(TARGETS)} target decks"
        )

    return {
        "destinationRoot": destination_root,
        "notes": len(after["noteIds"]),
        "cards": len(after["cardIds"]),
        "cardIds": after["cardIds"],
        "cardsByDeck": {deck: sorted(ids) for deck, ids in sorted(by_deck.items())},
        "schedulingChanges": scheduling_changes,
        "noteChanges": 0,
        "filteredDeckCollisions": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--apply", action="store_true", help="move daily → Process QA")
    action.add_argument(
        "--audit-restore",
        action="store_true",
        help="read-only audit of the Process QA batch before restoration",
    )
    action.add_argument("--restore", action="store_true", help="move Process QA → daily")
    args = parser.parse_args()

    if invoke("version") < 6:
        raise RuntimeError("AnkiConnect version 6 is required")

    source_root = QA_ROOT if args.restore or args.audit_restore else DAILY_ROOT
    destination_root = DAILY_ROOT if args.restore or args.audit_restore else QA_ROOT
    before = collect(source_root)
    mode = "restore" if args.restore or args.audit_restore else "stage"
    if not args.apply and not args.restore:
        print(json.dumps({"audit": mode, "root": source_root, "counts": before["counts"]}, indent=2))
        return

    # Freshness check immediately before the first write.
    fresh = collect(source_root)
    if state_fingerprint(before) != state_fingerprint(fresh):
        raise RuntimeError("target live state changed after snapshot; aborting")

    stamp = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    snapshot_root = SNAPSHOTS / f"{stamp}-{mode}"
    write_snapshot(snapshot_root / "before", before)

    by_destination: dict[str, list[int]] = defaultdict(list)
    for card_id, source_deck in before["expectedByCard"].items():
        suffix = source_deck.removeprefix(source_root + "::")
        by_destination[expected_deck(destination_root, suffix)].append(card_id)
    for deck, card_ids in sorted(by_destination.items()):
        invoke("changeDeck", cards=sorted(card_ids), deck=deck)

    after = collect(destination_root)
    write_snapshot(snapshot_root / "after", after)
    report = verify(before, after, destination_root)
    (snapshot_root / "verification.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"snapshot: {snapshot_root}")


if __name__ == "__main__":
    main()
