"""Replace the staged physical-systems QA cards with the redesigned batch.

The default is a read-only preflight. ``--apply`` imports the eight affected
scope packages, replaces only the ten unreviewed legacy cell/AMOC notes, adds
the four ENSO notes, keeps all 29 resulting cards under ``Process::GeoTrainer
QA``, and verifies preserved identity/scheduling. No sync is performed.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOTS = ROOT / "backups" / "live-imports"
DAILY_ROOT = "Decks::Geography::GeoTrainer"
QA_ROOT = "Process::GeoTrainer QA"
IMPORT_ROOT = "GeoTrainer"
EXPECTED_BEFORE = 2_406
EXPECTED_AFTER = 2_405

TARGETS = (
    (
        "geotrainer::scope::physical::atmosphere::cells",
        "Physical::Atmospheric Circulation::1 Trace Cells",
        3,
        "geo-trainer-atmospheric-cells.apkg",
    ),
    (
        "geotrainer::scope::physical::atmosphere::pressure-belts",
        "Physical::Atmospheric Circulation::2 Place Pressure Belts",
        4,
        "geo-trainer-atmospheric-pressure-belts.apkg",
    ),
    (
        "geotrainer::scope::physical::atmosphere::prevailing-winds",
        "Physical::Atmospheric Circulation::3 Trace Prevailing Winds",
        6,
        "geo-trainer-world-prevailing-winds.apkg",
    ),
    (
        "geotrainer::scope::physical::atmosphere::jet-streams",
        "Physical::Atmospheric Circulation::4 Trace Jet Streams",
        4,
        "geo-trainer-world-jet-streams.apkg",
    ),
    (
        "geotrainer::scope::physical::atmosphere::monsoon",
        "Physical::Atmospheric Circulation::5 Trace Seasonal Monsoon Winds",
        2,
        "geo-trainer-south-asia-monsoon-winds.apkg",
    ),
    (
        "geotrainer::scope::physical::ocean-currents::monsoon",
        "Physical::Ocean Currents::2 Trace Seasonal Monsoon Currents",
        4,
        "geo-trainer-indian-ocean-seasonal-currents.apkg",
    ),
    (
        "geotrainer::scope::physical::ocean-currents::amoc",
        "Physical::Ocean Currents::3 Learn Atlantic Overturning",
        2,
        "geo-trainer-atlantic-overturning.apkg",
    ),
    (
        "geotrainer::scope::physical::ocean-atmosphere::enso",
        "Physical::Ocean–Atmosphere Coupling::1 Compare ENSO States",
        4,
        "geo-trainer-equatorial-pacific-enso.apkg",
    ),
)

OLD_REPLACEMENT_KEYS = {
    "atmospheric-cells:ferrel-north",
    "atmospheric-cells:ferrel-south",
    "atmospheric-cells:hadley-north",
    "atmospheric-cells:hadley-south",
    "atmospheric-cells:polar-north",
    "atmospheric-cells:polar-south",
    "atlantic-overturning:01-upper-limb",
    "atlantic-overturning:02-sinking-limb",
    "atlantic-overturning:03-deep-return-limb",
    "atlantic-overturning:04-complete-pathway",
}

EXPECTED_KEYS = {
    "geotrainer::scope::physical::atmosphere::cells": [
        "atmospheric-cells:01-hadley-pair",
        "atmospheric-cells:02-ferrel-pair",
        "atmospheric-cells:03-polar-pair",
    ],
    "geotrainer::scope::physical::ocean-currents::amoc": [
        "atlantic-overturning:01-limb-directions",
        "atlantic-overturning:02-pathway-order",
    ],
    "geotrainer::scope::physical::ocean-atmosphere::enso": [
        "equatorial-pacific-enso:01-neutral",
        "equatorial-pacific-enso:02-el-nino",
        "equatorial-pacific-enso:03-la-nina",
        "equatorial-pacific-enso:04-comparison",
    ],
}

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
    with urlopen(request, timeout=180) as response:  # noqa: S310 - localhost API
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
    return json.dumps(state, sort_keys=True, separators=(",", ":"))


def note_key(note: dict) -> str:
    return note["fields"]["Key"]["value"]


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
    compact = {
        "cardIds": state["cardIds"],
        "noteIds": state["noteIds"],
        "cards": [scheduling(card) for card in state["cards"]],
        "notes": [
            {
                "noteId": note["noteId"],
                "modelName": note["modelName"],
                "key": note_key(note),
                "tags": sorted(note["tags"]),
            }
            for note in state["notes"]
        ],
    }
    (directory / "state-compact.json").write_text(
        json.dumps(compact, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def read_legacy_before_cards(path: Path) -> list[dict]:
    """Read only the card prefix from the oversized legacy state snapshot."""
    prefix: list[str] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line == '  "noteIds": [\n':
                break
            prefix.append(line)
    if not prefix:
        raise RuntimeError(f"empty legacy snapshot: {path}")
    for index in range(len(prefix) - 1, -1, -1):
        if prefix[index].rstrip().endswith(","):
            prefix[index] = prefix[index].rstrip()[:-1] + "\n"
            break
    prefix.append("}\n")
    return json.loads("".join(prefix))["cards"]


def resume_verify(snapshot_root: Path) -> dict:
    legacy_path = snapshot_root / "before" / "state.json"
    compact_path = snapshot_root / "before" / "state-compact.json"
    if compact_path.exists():
        before_cards = json.loads(compact_path.read_text(encoding="utf-8"))["cards"]
    elif legacy_path.exists():
        before_cards = read_legacy_before_cards(legacy_path)
    else:
        raise RuntimeError(f"no before-state snapshot under {snapshot_root}")

    before_by_id = {card["cardId"]: card for card in before_cards}
    current_ids = sorted(invoke("findCards", query="tag:geotrainer::*"))
    current_cards = cards_info(current_ids)
    current_by_id = {card["cardId"]: card for card in current_cards}
    old_card_ids = {
        card_id
        for card_id, card in before_by_id.items()
        if card["note"]
        in {
            1785540781317,
            1785540781319,
            1785540781321,
            1785540781323,
            1785540781325,
            1785540781327,
            1785965360866,
            1785965360868,
            1785965360870,
            1785965360872,
        }
    }
    missing = set(before_by_id) - set(current_by_id)
    if missing != old_card_ids:
        raise RuntimeError(f"unexpected missing card identities: {sorted(missing)}")
    scheduling_changes = [
        card_id
        for card_id in set(before_by_id) - old_card_ids
        if scheduling(before_by_id[card_id]) != scheduling(current_by_id[card_id])
    ]
    if scheduling_changes:
        raise RuntimeError(f"preserved scheduling changed: {scheduling_changes}")
    if len(current_ids) != EXPECTED_AFTER:
        raise RuntimeError(f"expected {EXPECTED_AFTER} final cards, found {len(current_ids)}")

    all_target_ids: list[int] = []
    cards_by_deck: dict[str, int] = {}
    ordered_keys: dict[str, list[str]] = {}
    final_note_ids: set[int] = set()
    for tag, suffix, count, _ in TARGETS:
        ids = target_cards(tag)
        if len(ids) != count:
            raise RuntimeError(f"{tag}: expected {count} final cards, found {len(ids)}")
        rows = cards_info(ids)
        assert_ordinary(rows, tag)
        destination = f"{QA_ROOT}::{suffix}"
        if any(card["deckName"] != destination for card in rows):
            raise RuntimeError(f"{tag}: final deck membership is wrong")
        if any(card["type"] != 0 or card["queue"] not in {0, -2, -3} for card in rows):
            raise RuntimeError(f"{tag}: a final card is not in an eligible new state")
        cards_by_deck[destination] = count
        all_target_ids.extend(ids)
        target_note_ids = sorted({card["note"] for card in rows})
        final_note_ids.update(target_note_ids)
        notes = {note["noteId"]: note for note in notes_info(target_note_ids)}
        for note in notes.values():
            if not {"ai-created", tag}.issubset(note["tags"]):
                raise RuntimeError(f"note {note['noteId']} is missing required tags")
        if tag in EXPECTED_KEYS:
            keys = [
                note_key(notes[card["note"]])
                for card in sorted(rows, key=lambda row: (row["due"], row["cardId"]))
            ]
            if keys != EXPECTED_KEYS[tag]:
                raise RuntimeError(f"{tag}: unexpected learning order {keys}")
            ordered_keys[tag] = keys

    qa_ids = sorted(invoke("findCards", query=f'deck:"{QA_ROOT}"'))
    if sorted(all_target_ids) != qa_ids or len(qa_ids) != 29:
        raise RuntimeError("QA tree does not contain exactly the 29 redesigned cards")
    if invoke("findCards", query=f'deck:"{IMPORT_ROOT}"'):
        raise RuntimeError("temporary import root still contains cards")

    report = {
        "beforeCards": len(before_by_id),
        "afterCards": len(current_by_id),
        "deletedLegacyCardIds": sorted(old_card_ids),
        "deletedLegacyNoteIds": sorted(
            {before_by_id[card_id]["note"] for card_id in old_card_ids}
        ),
        "addedCardIds": sorted(set(current_by_id) - set(before_by_id)),
        "addedNoteIds": sorted(
            current_by_id[card_id]["note"]
            for card_id in set(current_by_id) - set(before_by_id)
        ),
        "preservedSchedulingChanges": 0,
        "qaCards": len(qa_ids),
        "qaNoteIds": sorted(final_note_ids),
        "cardsByDeck": dict(sorted(cards_by_deck.items())),
        "orderedKeys": ordered_keys,
        "filteredDeckCollisions": 0,
        "syncPerformed": False,
        "recoveryVerification": True,
    }
    (snapshot_root / "verification.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def target_cards(tag: str) -> list[int]:
    return sorted(invoke("findCards", query=f"tag:{tag} tag:ai-created"))


def assert_ordinary(cards: list[dict], label: str) -> None:
    filtered = [card["cardId"] for card in cards if card.get("originalDeckName")]
    if filtered:
        raise RuntimeError(f"{label} cards are captured by a filtered deck: {filtered}")


def preflight() -> tuple[dict, list[int], list[int]]:
    if invoke("version") < 6:
        raise RuntimeError("AnkiConnect version 6 is required")
    missing_packages = [
        package for *_, package in TARGETS if not (ROOT / "dist" / package).exists()
    ]
    if missing_packages:
        raise RuntimeError(f"missing packages: {missing_packages}")

    state = collect_all()
    if len(state["cardIds"]) != EXPECTED_BEFORE or len(state["noteIds"]) != EXPECTED_BEFORE:
        raise RuntimeError(
            f"expected {EXPECTED_BEFORE} one-card GeoTrainer notes, found "
            f"{len(state['noteIds'])} notes/{len(state['cardIds'])} cards"
        )
    notes_by_id = {note["noteId"]: note for note in state["notes"]}
    cards_by_id = {card["cardId"]: card for card in state["cards"]}

    qa_ids = sorted(invoke("findCards", query=f'deck:"{QA_ROOT}"'))
    if len(qa_ids) != 30:
        raise RuntimeError(f"expected 30 cards in the QA tree, found {len(qa_ids)}")
    assert_ordinary([cards_by_id[card_id] for card_id in qa_ids], "QA")

    old_note_ids = sorted(
        note_id for note_id, note in notes_by_id.items() if note_key(note) in OLD_REPLACEMENT_KEYS
    )
    if len(old_note_ids) != 10:
        found = sorted(note_key(notes_by_id[note_id]) for note_id in old_note_ids)
        raise RuntimeError(f"expected ten exact legacy replacement notes, found {found}")
    old_card_ids = sorted(
        card_id for card_id, card in cards_by_id.items() if card["note"] in old_note_ids
    )
    if not set(old_card_ids).issubset(qa_ids):
        raise RuntimeError("legacy replacement cards are no longer all in the QA tree")
    unsafe = [
        card["cardId"]
        for card in (cards_by_id[card_id] for card_id in old_card_ids)
        if card["reps"] != 0 or card["type"] != 0 or card["queue"] not in {0, -2, -3}
    ]
    if unsafe:
        raise RuntimeError(f"refusing to replace reviewed or non-new cards: {unsafe}")

    # The seven old scopes must still have their original staged membership; ENSO
    # must not exist yet.
    expected_old_counts = [6, 4, 6, 4, 2, 4, 4, 0]
    for (tag, suffix, _, _), count in zip(TARGETS, expected_old_counts, strict=True):
        ids = target_cards(tag)
        if len(ids) != count:
            raise RuntimeError(f"{tag}: expected {count} pre-rollout cards, found {len(ids)}")
        if tag == "geotrainer::scope::physical::ocean-currents::amoc":
            suffix = "Physical::Ocean Currents::3 Trace Atlantic Overturning"
        for card in cards_info(ids):
            if card["deckName"] != f"{QA_ROOT}::{suffix}":
                raise RuntimeError(f"{tag}: card {card['cardId']} is outside its QA deck")

    import_cards = invoke("findCards", query=f'deck:"{IMPORT_ROOT}"')
    if import_cards:
        raise RuntimeError(f"temporary import root contains cards: {sorted(import_cards)}")
    return state, old_note_ids, old_card_ids


def verify(before: dict, after: dict, old_note_ids: list[int], old_card_ids: list[int]) -> dict:
    before_cards = {card["cardId"]: card for card in before["cards"]}
    after_cards = {card["cardId"]: card for card in after["cards"]}
    before_notes = {note["noteId"]: note for note in before["notes"]}
    after_notes = {note["noteId"]: note for note in after["notes"]}
    old_note_set = set(old_note_ids)
    old_card_set = set(old_card_ids)

    if old_note_set & set(after_notes) or old_card_set & set(after_cards):
        raise RuntimeError("one or more obsolete cell/AMOC notes survived replacement")
    preserved_note_ids = set(before_notes) - old_note_set
    preserved_card_ids = set(before_cards) - old_card_set
    if preserved_note_ids - set(after_notes) or preserved_card_ids - set(after_cards):
        raise RuntimeError("identity loss outside the ten intentional replacements")

    scheduling_changes = [
        card_id
        for card_id in preserved_card_ids
        if scheduling(before_cards[card_id]) != scheduling(after_cards[card_id])
    ]
    if scheduling_changes:
        raise RuntimeError(f"preserved scheduling changed: {scheduling_changes}")

    target_tags = {tag for tag, *_ in TARGETS}
    unaffected_note_ids = {
        note_id
        for note_id in preserved_note_ids
        if not target_tags.intersection(before_notes[note_id]["tags"])
    }
    content_changes = [
        note_id
        for note_id in unaffected_note_ids
        if normalized_note(before_notes[note_id]) != normalized_note(after_notes[note_id])
    ]
    if content_changes:
        raise RuntimeError(f"unaffected note content changed: {content_changes}")

    if len(after_cards) != EXPECTED_AFTER or len(after_notes) != EXPECTED_AFTER:
        raise RuntimeError(
            f"expected {EXPECTED_AFTER} final notes/cards, got "
            f"{len(after_notes)}/{len(after_cards)}"
        )

    by_deck: dict[str, int] = defaultdict(int)
    ordered_keys: dict[str, list[str]] = {}
    for tag, suffix, count, _ in TARGETS:
        ids = target_cards(tag)
        if len(ids) != count:
            raise RuntimeError(f"{tag}: expected {count} final cards, found {len(ids)}")
        rows = cards_info(ids)
        assert_ordinary(rows, tag)
        destination = f"{QA_ROOT}::{suffix}"
        if any(card["deckName"] != destination for card in rows):
            raise RuntimeError(f"{tag}: final deck membership is wrong")
        if any(card["type"] != 0 or card["queue"] not in {0, -2, -3} for card in rows):
            raise RuntimeError(f"{tag}: a redesigned card is not in an eligible new state")
        by_deck[destination] = len(rows)
        if tag in EXPECTED_KEYS:
            keys = [
                note_key(after_notes[card["note"]])
                for card in sorted(rows, key=lambda row: (row["due"], row["cardId"]))
            ]
            if keys != EXPECTED_KEYS[tag]:
                raise RuntimeError(f"{tag}: unexpected learning order {keys}")
            ordered_keys[tag] = keys
        for card in rows:
            note = after_notes[card["note"]]
            if not {"ai-created", tag}.issubset(note["tags"]):
                raise RuntimeError(f"note {note['noteId']} is missing required tags")

    qa_ids = sorted(invoke("findCards", query=f'deck:"{QA_ROOT}"'))
    if len(qa_ids) != 29:
        raise RuntimeError(f"expected 29 final QA cards, found {len(qa_ids)}")
    strays = invoke("findCards", query=f'deck:"{IMPORT_ROOT}"')
    if strays:
        raise RuntimeError(f"temporary import root retains cards: {sorted(strays)}")

    return {
        "beforeNotes": len(before_notes),
        "afterNotes": len(after_notes),
        "deletedLegacyNoteIds": old_note_ids,
        "deletedLegacyCardIds": old_card_ids,
        "addedNoteIds": sorted(set(after_notes) - set(before_notes)),
        "addedCardIds": sorted(set(after_cards) - set(before_cards)),
        "preservedSchedulingChanges": len(scheduling_changes),
        "unaffectedContentChanges": len(content_changes),
        "qaCards": len(qa_ids),
        "cardsByDeck": dict(sorted(by_deck.items())),
        "orderedKeys": ordered_keys,
        "filteredDeckCollisions": 0,
        "syncPerformed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--resume-before", type=Path)
    args = parser.parse_args()

    if args.resume_before:
        report = resume_verify(args.resume_before.resolve())
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    before, old_note_ids, old_card_ids = preflight()
    if not args.apply:
        print(
            json.dumps(
                {
                    "audit": "ready",
                    "existingNotes": len(before["noteIds"]),
                    "qaCards": 30,
                    "legacyNotesToReplace": old_note_ids,
                    "resultingQaCards": 29,
                    "syncPerformed": False,
                },
                indent=2,
            )
        )
        return

    fresh, fresh_old_note_ids, fresh_old_card_ids = preflight()
    if fingerprint(before) != fingerprint(fresh):
        raise RuntimeError("live GeoTrainer state changed after preflight; aborting")
    if old_note_ids != fresh_old_note_ids or old_card_ids != fresh_old_card_ids:
        raise RuntimeError("replacement target identity changed after preflight; aborting")

    stamp = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    snapshot_root = SNAPSHOTS / f"{stamp}-physical-redesign"
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

    for _, _, _, package in TARGETS:
        invoke("importPackage", path=str(ROOT / "dist" / package))

    # Move every final-key card to its exact QA destination before deleting the
    # old zero-review notes. Existing matched cards generally remain in place;
    # newly imported cards arrive under the isolated package root.
    notes = notes_info(sorted(invoke("findNotes", query="tag:geotrainer::*")))
    note_by_key = {note_key(note): note for note in notes}
    for tag, suffix, _, _ in TARGETS:
        destination = f"{QA_ROOT}::{suffix}"
        wanted_keys = EXPECTED_KEYS.get(tag)
        if wanted_keys is None:
            ids = target_cards(tag)
        else:
            missing = [key for key in wanted_keys if key not in note_by_key]
            if missing:
                raise RuntimeError(f"missing imported notes: {missing}")
            wanted_note_ids = {note_by_key[key]["noteId"] for key in wanted_keys}
            ids = sorted(
                card["cardId"]
                for card in cards_info(sorted(invoke("findCards", query=f"tag:{tag}")))
                if card["note"] in wanted_note_ids
            )
        invoke("changeDeck", cards=ids, deck=destination)

    invoke("deleteNotes", notes=old_note_ids)
    strays = invoke("findCards", query=f'deck:"{IMPORT_ROOT}"')
    if strays:
        raise RuntimeError(f"temporary import root retains cards: {sorted(strays)}")
    import_decks = [
        deck
        for deck in invoke("deckNames")
        if deck == IMPORT_ROOT or deck.startswith(IMPORT_ROOT + "::")
    ]
    if import_decks:
        invoke("deleteDecks", decks=[IMPORT_ROOT], cardsToo=True)

    after = collect_all()
    write_snapshot(snapshot_root / "after", after)
    report = verify(before, after, old_note_ids, old_card_ids)
    (snapshot_root / "verification.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"snapshot: {snapshot_root}")


if __name__ == "__main__":
    main()
