"""Import the plateaus and grasslands scopes into the live collection.

Imports ``dist/geo-trainer-world-plateaus.apkg`` and
``dist/geo-trainer-world-grasslands.apkg`` (new note types and decks only,
nothing existing is touched), then moves the imported cards from the package
root ``GeoTrainer::Physical::…`` to the live tree
``Decks::Geography::GeoTrainer::Physical::…`` and deletes the emptied import
decks. New note types sync normally; no schema change to an existing model.

Read-only by default; ``--apply`` imports and relocates. A snapshot of the
live GeoTrainer tree (card -> deck, scheduling) is written before and after.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
BACKUPS = ROOT / "backups" / "live-imports"
LIVE_ROOT = "Decks::Geography::GeoTrainer"
IMPORT_ROOT = "GeoTrainer"
SCOPES = {
    "world-plateaus": ("Physical::Plateaus & Basins", 22),
    "world-grasslands": ("Physical::Plains & Grasslands", 18),
}
FAMILY_DECKS = ("2 Place", "3 Sketch")
SCHEDULING = ("cardId", "note", "deckName", "ord", "type", "queue", "due",
              "interval", "factor", "reps", "lapses", "left", "flags")


def invoke(action: str, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params}).encode()
    request = Request("http://127.0.0.1:8765", data=payload,
                      headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=600) as response:  # noqa: S310 - localhost API
        result = json.load(response)
    if result.get("error") is not None:
        raise RuntimeError(f"AnkiConnect {action}: {result['error']}")
    return result.get("result")


def tree(root: str) -> dict[int, dict]:
    ids = invoke("findCards", query=f'"deck:{root}"')
    out = {}
    for start in range(0, len(ids), 500):
        for card in invoke("cardsInfo", cards=ids[start:start + 500]):
            out[card["cardId"]] = {k: card[k] for k in SCHEDULING}
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    BACKUPS.mkdir(parents=True, exist_ok=True)
    before = tree(LIVE_ROOT)
    (BACKUPS / f"{stamp}-geo-concepts-scopes-before.json").write_text(
        json.dumps(before, indent=1), encoding="utf-8")
    print(f"live tree before: {len(before)} cards")
    models = set(invoke("modelNames"))
    for scope, (leaf, expected) in SCOPES.items():
        path = ROOT / "dist" / f"geo-trainer-{scope}.apkg"
        if not path.exists():
            sys.exit(f"missing {path}; build it first")
        for fam in ("Place", "Sketch"):
            name = f"GeoTrainer {fam} — {leaf.split('::')[-1]}"
            if name in models:
                sys.exit(f"model {name!r} already exists; refusing to import over it")
        for deck in (f"{IMPORT_ROOT}::{leaf}", f"{LIVE_ROOT}::{leaf}"):
            if invoke("findCards", query=f'"deck:{deck}"'):
                sys.exit(f"{deck} already has cards; refusing")
        print(f"{scope}: {path.name} -> {LIVE_ROOT}::{leaf} (expect {expected} cards)")
    if not args.apply:
        print("dry run; pass --apply to import")
        return 0

    for scope, (leaf, expected) in SCOPES.items():
        path = ROOT / "dist" / f"geo-trainer-{scope}.apkg"
        invoke("importPackage", path=str(path))
        moved_total = 0
        for fam_deck in FAMILY_DECKS:
            src = f"{IMPORT_ROOT}::{leaf}::{fam_deck}"
            dst = f"{LIVE_ROOT}::{leaf}::{fam_deck}"
            cards = invoke("findCards", query=f'"deck:{src}"')
            if not cards:
                sys.exit(f"nothing imported into {src}")
            invoke("createDeck", deck=dst)
            invoke("changeDeck", cards=cards, deck=dst)
            if len(invoke("findCards", query=f'"deck:{dst}"')) != len(cards):
                sys.exit(f"{dst}: move incomplete")
            if invoke("findCards", query=f'"deck:{src}"'):
                sys.exit(f"{src}: cards left behind")
            invoke("deleteDecks", decks=[src], cardsToo=True)
            moved_total += len(cards)
            print(f"  {src} -> {dst}: {len(cards)} cards")
        parent = f"{IMPORT_ROOT}::{leaf}"
        if invoke("findCards", query=f'"deck:{parent}"'):
            sys.exit(f"{parent} still has cards")
        invoke("deleteDecks", decks=[parent], cardsToo=True)
        if moved_total != expected:
            sys.exit(f"{scope}: moved {moved_total}, expected {expected}")

    after = tree(LIVE_ROOT)
    (BACKUPS / f"{stamp}-geo-concepts-scopes-after.json").write_text(
        json.dumps(after, indent=1), encoding="utf-8")
    added = set(after) - set(before)
    changed = [cid for cid in before if cid in after and after[cid] != before[cid]]
    missing = set(before) - set(after)
    print(f"live tree after: {len(after)} cards; added {len(added)}, "
          f"pre-existing changed {len(changed)}, missing {len(missing)}")
    if missing or changed or len(added) != sum(n for _, n in SCOPES.values()):
        sys.exit("verification failed; see snapshots")
    print("verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
