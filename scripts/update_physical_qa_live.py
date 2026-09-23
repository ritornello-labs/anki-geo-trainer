"""Refresh the 29 already-staged physical-systems cards, in place.

Read-only by default. ``--apply`` imports only the eight revised scope APKGs,
then verifies every GeoTrainer card identity and scheduling value. No sync.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime

import build_apkg
import rollout_physical_redesign_live as rollout


def expected_notes(scope: str) -> tuple[dict[str, dict], dict[str, tuple[str, str, str]]]:
    decks, _ = build_apkg.scope_decks(scope)
    notes = {}
    models = {}
    for deck in decks:
        for note in deck.notes:
            model = note.model
            names = [field["name"] for field in model.fields]
            notes[note.fields[0]] = {
                "modelName": model.name,
                "fields": dict(zip(names, note.fields, strict=True)),
            }
            mode = model.templates[0]["name"].lower()
            models[model.name] = build_apkg.build_templates(scope, mode)
    return notes, models


def audit() -> tuple[dict, dict, dict]:
    if rollout.invoke("version") < 6:
        raise RuntimeError("AnkiConnect version 6 is required")
    before = rollout.collect_all()
    notes_by_id = {note["noteId"]: note for note in before["notes"]}
    cards_by_id = {card["cardId"]: card for card in before["cards"]}
    qa_ids = sorted(rollout.invoke("findCards", query=f'deck:"{rollout.QA_ROOT}"'))
    if len(qa_ids) != 29:
        raise RuntimeError(f"expected 29 existing QA cards; found {len(qa_ids)}")
    rollout.assert_ordinary([cards_by_id[card_id] for card_id in qa_ids], "QA")
    target_ids = []
    expected = {}
    models = {}
    for tag, suffix, count, package in rollout.TARGETS:
        package_path = rollout.ROOT / "dist" / package
        if not package_path.is_file():
            raise RuntimeError(f"missing package: {package}")
        scope = package.removeprefix("geo-trainer-").removesuffix(".apkg")
        scope_notes, scope_models = expected_notes(scope)
        ids = rollout.target_cards(tag)
        if len(ids) != count or len(scope_notes) != count:
            raise RuntimeError(f"{tag}: expected {count} live and packaged cards")
        rows = [cards_by_id[card_id] for card_id in ids]
        rollout.assert_ordinary(rows, tag)
        deck_name = f"{rollout.QA_ROOT}::{suffix}"
        if any(card["deckName"] != deck_name for card in rows):
            raise RuntimeError(f"{tag}: card outside {deck_name}")
        if any(card["reps"] or card["type"] != 0 or card["queue"] not in {0, -2, -3} for card in rows):
            raise RuntimeError(f"{tag}: QA card has been reviewed or is in an unsafe queue")
        actual_keys = {rollout.note_key(notes_by_id[card["note"]]) for card in rows}
        if actual_keys != set(scope_notes):
            raise RuntimeError(f"{tag}: live keys differ from the revised package")
        target_ids.extend(ids)
        expected.update(scope_notes)
        models.update(scope_models)
    if sorted(target_ids) != qa_ids:
        raise RuntimeError("Process QA contains an unexpected card")
    if rollout.invoke("findCards", query=f'deck:"{rollout.IMPORT_ROOT}"'):
        raise RuntimeError("temporary import root contains cards")
    for model_name in models:
        model_count = Counter(note["modelName"] for note in before["notes"])[model_name]
        target_count = sum(notes_by_id[cards_by_id[cid]["note"]]["modelName"] == model_name for cid in qa_ids)
        if model_count != target_count:
            raise RuntimeError(f"{model_name}: note type is shared outside QA")
    return before, expected, models


def verify(before: dict, after: dict, expected: dict, models: dict) -> dict:
    if before["cardIds"] != after["cardIds"] or before["noteIds"] != after["noteIds"]:
        raise RuntimeError("import changed a GeoTrainer card or note identity")
    old_cards = {card["cardId"]: card for card in before["cards"]}
    new_cards = {card["cardId"]: card for card in after["cards"]}
    for card_id, old in old_cards.items():
        new = new_cards[card_id]
        if rollout.scheduling(old) != rollout.scheduling(new):
            raise RuntimeError(f"card {card_id}: scheduling changed")
        if old["deckName"] != new["deckName"]:
            raise RuntimeError(f"card {card_id}: deck changed")
    old_notes = {note["noteId"]: note for note in before["notes"]}
    for note in after["notes"]:
        old = old_notes[note["noteId"]]
        key = rollout.note_key(note)
        if key in expected:
            fields = {name: value["value"] for name, value in note["fields"].items()}
            if note["modelName"] != expected[key]["modelName"] or fields != expected[key]["fields"]:
                raise RuntimeError(f"{key}: imported fields/model differ from package")
        elif rollout.normalized_note(old) != rollout.normalized_note(note):
            raise RuntimeError(f"note {note['noteId']}: unrelated content changed")
    for model_name, (front, back, css) in models.items():
        templates = rollout.invoke("modelTemplates", modelName=model_name)
        styling = rollout.invoke("modelStyling", modelName=model_name)
        if len(templates) != 1:
            raise RuntimeError(f"{model_name}: unexpected template count")
        template = next(iter(templates.values()))
        if (template["Front"], template["Back"], styling["css"]) != (front, back, css):
            raise RuntimeError(f"{model_name}: template/CSS did not update exactly")
    qa_ids = sorted(rollout.invoke("findCards", query=f'deck:"{rollout.QA_ROOT}"'))
    if len(qa_ids) != 29:
        raise RuntimeError("final Process QA membership is not 29")
    if rollout.invoke("findCards", query=f'deck:"{rollout.IMPORT_ROOT}"'):
        raise RuntimeError("import left cards outside Process QA")
    return {
        "qaCards": len(qa_ids),
        "updatedNoteTypes": len(models),
        "preservedCardIds": len(old_cards),
        "schedulingChanges": 0,
        "unrelatedContentChanges": 0,
        "syncPerformed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    before, expected, models = audit()
    if not args.apply:
        print(json.dumps({"audit": "ready", "qaCards": 29, "noteTypes": len(models), "totalGeoTrainerCards": len(before["cardIds"])}, indent=2))
        return
    fresh, _, _ = audit()
    if rollout.fingerprint(before) != rollout.fingerprint(fresh):
        raise RuntimeError("GeoTrainer changed since preflight")
    stamp = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    snapshot = rollout.SNAPSHOTS / f"{stamp}-physical-qa-refresh"
    rollout.SNAPSHOTS.mkdir(parents=True, mode=0o700, exist_ok=True)
    rollout.SNAPSHOTS.chmod(0o700)
    rollout.write_snapshot(snapshot / "before", before)
    rollout.invoke("exportPackage", deck=rollout.QA_ROOT, path=str(snapshot / "before" / "qa-geotrainer.apkg"), includeSched=True)
    for _, _, _, package in rollout.TARGETS:
        rollout.invoke("importPackage", path=str(rollout.ROOT / "dist" / package))
    after = rollout.collect_all()
    rollout.write_snapshot(snapshot / "after", after)
    report = verify(before, after, expected, models)
    (snapshot / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"recovery: {snapshot}")


if __name__ == "__main__":
    main()
