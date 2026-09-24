"""Import the scopes built from world-geography-concepts into the live collection.

Imports the per-scope packages in ``dist/`` (new note types and decks only,
nothing existing is touched), moves the imported cards from the package root
``GeoTrainer::Physical::…`` to the live tree ``Decks::Geography::GeoTrainer::
Physical::…``, and deletes the emptied import decks (never ``GeoTrainer::
Physical`` or ``GeoTrainer`` themselves, which hold live QA decks). New note
types sync normally; no existing model changes.

Read-only by default; ``--apply`` imports and relocates. A snapshot of the
live GeoTrainer tree (card -> deck, scheduling) is written before and after,
and every pre-existing card must come out unchanged.
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
# scope -> (deck leaf under the roots, expected cards, family decks, model label)
SCOPES = {
    "world-plateaus": ("Physical::Plateaus & Basins", 22, ("2 Place", "3 Sketch"),
                       "Plateaus & Basins"),
    "world-grasslands": ("Physical::Plains & Grasslands", 18, ("2 Place", "3 Sketch"),
                         "Plains & Grasslands"),
    "world-peninsulas": ("Physical::Peninsulas", 28, ("2 Place", "3 Sketch"), "Peninsulas"),
    "world-minor-plates": ("Physical::Tectonic Plates::Minor Plates", 67,
                           ("2 Place", "3 Sketch"), "Minor Tectonic Plates"),
    "world-plate-boundaries": ("Physical::Plate Boundaries", 17, ("1 Trace",),
                               "Plate Boundaries"),
}
FAMILY_LABEL = {"1 Trace": "Trace", "2 Place": "Place", "3 Sketch": "Sketch"}
KEEP = {IMPORT_ROOT, f"{IMPORT_ROOT}::Physical"}
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


def cards_in(deck: str) -> list[int]:
    return invoke("findCards", query=f'"deck:{deck}"')


def tree(root: str) -> dict[int, dict]:
    ids = cards_in(root)
    out = {}
    for start in range(0, len(ids), 500):
        for card in invoke("cardsInfo", cards=ids[start:start + 500]):
            out[card["cardId"]] = {k: card[k] for k in SCHEDULING}
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--scope", action="append", choices=sorted(SCOPES),
                        help="limit to these scopes (default: all)")
    args = parser.parse_args()
    scopes = {k: SCOPES[k] for k in (args.scope or SCOPES)}

    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    before = tree(LIVE_ROOT)
    print(f"live tree before: {len(before)} cards")
    models = set(invoke("modelNames"))
    for scope, (leaf, expected, fam_decks, label) in scopes.items():
        path = ROOT / "dist" / f"geo-trainer-{scope}.apkg"
        if not path.exists():
            sys.exit(f"missing {path}; build it first")
        for fam_deck in fam_decks:
            name = f"GeoTrainer {FAMILY_LABEL[fam_deck]} — {label}"
            if name in models:
                sys.exit(f"model {name!r} already exists; refusing to import over it")
            for root in (IMPORT_ROOT, LIVE_ROOT):
                if cards_in(f"{root}::{leaf}::{fam_deck}"):
                    sys.exit(f"{root}::{leaf}::{fam_deck} already has cards; refusing")
        print(f"{scope}: {path.name} -> {LIVE_ROOT}::{leaf} (expect {expected} cards)")
    if not args.apply:
        print("dry run; pass --apply to import")
        return 0

    BACKUPS.mkdir(parents=True, exist_ok=True)
    (BACKUPS / f"{stamp}-geo-concepts-scopes-before.json").write_text(
        json.dumps(before, indent=1), encoding="utf-8")
    for scope, (leaf, expected, fam_decks, _) in scopes.items():
        invoke("importPackage", path=str(ROOT / "dist" / f"geo-trainer-{scope}.apkg"))
        moved = 0
        for fam_deck in fam_decks:
            src, dst = f"{IMPORT_ROOT}::{leaf}::{fam_deck}", f"{LIVE_ROOT}::{leaf}::{fam_deck}"
            cards = cards_in(src)
            if not cards:
                sys.exit(f"nothing imported into {src}")
            invoke("createDeck", deck=dst)
            invoke("changeDeck", cards=cards, deck=dst)
            if len(cards_in(dst)) != len(cards) or cards_in(src):
                sys.exit(f"{src} -> {dst}: move incomplete")
            invoke("deleteDecks", decks=[src], cardsToo=True)  # verified empty
            moved += len(cards)
            print(f"  {src} -> {dst}: {len(cards)} cards")
        # Remove the now-empty import parents, deepest first.
        parts = leaf.split("::")
        for depth in range(len(parts), 0, -1):
            deck = "::".join([IMPORT_ROOT, *parts[:depth]])
            if deck in KEEP or deck not in invoke("deckNames"):
                continue
            if cards_in(deck):
                break
            invoke("deleteDecks", decks=[deck], cardsToo=True)  # verified empty
        if moved != expected:
            sys.exit(f"{scope}: moved {moved}, expected {expected}")

    after = tree(LIVE_ROOT)
    (BACKUPS / f"{stamp}-geo-concepts-scopes-after.json").write_text(
        json.dumps(after, indent=1), encoding="utf-8")
    added = set(after) - set(before)
    changed = [cid for cid in before if cid in after and after[cid] != before[cid]]
    missing = set(before) - set(after)
    want = sum(expected for _, expected, _, _ in scopes.values())
    print(f"live tree after: {len(after)} cards; added {len(added)} (want {want}), "
          f"pre-existing changed {len(changed)}, missing {len(missing)}")
    if missing or changed or len(added) != want:
        sys.exit("verification failed; see snapshots")
    print("verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
