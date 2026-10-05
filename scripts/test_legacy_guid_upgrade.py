#!/usr/bin/env python3
"""Reproduce the October 2026 GUID-aware transition using disposable Anki only.

This is a compatibility proof, NOT an upgrader for an installed collection.
It accepts APKG inputs and creates only temporary source/destination collections.
Run with Anki 25.09's Python interpreter. Never pass a live collection file.
"""

import argparse
import collections
import hashlib
import json
import tempfile
from pathlib import Path

from anki.collection import Collection, ImportAnkiPackageOptions, ImportAnkiPackageRequest
from anki.import_export_pb2 import IMPORT_ANKI_PACKAGE_UPDATE_CONDITION_ALWAYS as ALWAYS
from anki.notetypes_pb2 import ChangeNotetypeRequest
from anki.scheduler.v3 import CardAnswer

parser = argparse.ArgumentParser(
    description="Disposable QA proof only; never opens an existing collection."
)
parser.add_argument("--legacy-apkg", type=Path, required=True)
parser.add_argument("--current-apkg", type=Path, required=True)
parser.add_argument("--components-dir", type=Path, required=True)
parser.add_argument("--receipt", type=Path, required=True)
parser.add_argument("--preimport-component", type=Path)
args = parser.parse_args()
PACK = args.current_apkg
components = sorted(args.components_dir.glob("*.apkg"))
assert len(components) == 15, "Expected all fifteen delivered component APKGs"
assert (
    hashlib.sha256(args.legacy_apkg.read_bytes()).hexdigest()
    == "3769f7c0d84c59858e0a3880e7cce204c54ac41c9559df889a7503751027edcc"
), "Wrong July legacy fixture"


def load(c, p, always=False):
    opts = ImportAnkiPackageOptions(
        merge_notetypes=False, with_scheduling=False, with_deck_configs=False
    )
    if always:
        opts.update_notes = ALWAYS
        opts.update_notetypes = ALWAYS
    return c.import_anki_package(ImportAnkiPackageRequest(package_path=str(p), options=opts))


def snap(c):
    return {
        g: {
            "nid": nid,
            "mid": mid,
            "fields": dict(c.get_note(nid).items()),
            "cards": c.db.all(
                "select id,nid,ord,type,queue,due,ivl,factor,reps,lapses,left,odue,odid,flags,data from cards where nid=? order by ord",
                nid,
            ),
            "deck_ids": c.db.list("select did from cards where nid=? order by ord", nid),
        }
        for nid, g, mid in c.db.all("select id,guid,mid from notes")
    }


def move(c, old, new, nids):
    before = c.models.get(old)
    after = c.models.get(new)
    fmap = {f["name"]: i for i, f in enumerate(before["flds"])}
    assert len(before["tmpls"]) == len(after["tmpls"]) == 1
    c.models.change_notetype_of_notes(
        ChangeNotetypeRequest(
            note_ids=nids,
            old_notetype_id=old,
            new_notetype_id=new,
            old_notetype_name=before["name"],
            current_schema=c.db.scalar("select scm from col"),
            new_fields=[fmap.get(f["name"], -1) for f in after["flds"]],
            new_templates=[0],
        )
    )


def upgrade(c, source, models):
    before = snap(c)
    accepted = set(source) & set(before)
    need = {
        g
        for g in accepted
        if before[g]["mid"] != source[g]["mid"]
        or set(before[g]["fields"]) != set(source[g]["fields"])
    }
    print("Migration candidates:", len(need), flush=True)
    if not need:
        return {"migrated_accepted_notes": 0}
    targets = {source[g]["mid"] for g in need}
    evac = set()
    tempmap = {}
    for mid, canonical in models.items():
        existing = c.models.get(mid)
        if existing and (
            [f["name"] for f in existing["flds"]] != [f["name"] for f in canonical["flds"]]
            or [t["name"] for t in existing["tmpls"]] != [t["name"] for t in canonical["tmpls"]]
        ):
            targets.add(mid)
    for mid in targets:
        m = c.models.get(mid)
        if m and c.db.scalar("select count(*) from notes where mid=?", mid):
            evac.add(mid)
    evac |= {before[g]["mid"] for g in need}
    for mid in sorted(evac):
        m = c.models.get(mid)
        ids = c.db.list("select id from notes where mid=?", mid)
        clone = c.models.copy(m, add=False)
        clone["name"] = "GeoTrainer July transition — " + m["name"]
        newid = c.models.add_dict(clone).id
        tempmap[mid] = newid
        move(c, mid, newid, ids)
    # Native APKG import installs the fixed canonical IDs; add_dict assigns new IDs.
    # Remove only empty conflicting slots after preserving their notes in clones.
    for mid in sorted(targets):
        if c.models.get(mid):
            assert c.db.scalar("select count(*) from notes where mid=?", mid) == 0
            c.models.remove(mid)
    load(c, PACK, always=True)
    assert all(c.models.get(mid) for mid in targets)
    groups = collections.defaultdict(list)
    for g in need:
        groups[(tempmap[before[g]["mid"]], source[g]["mid"])].append(before[g]["nid"])
    for (old, new), ids in groups.items():
        move(c, old, new, ids)
    notes = []
    for g in need:
        n = c.get_note(before[g]["nid"])
        if "Key" in n:
            n["Key"] = source[g]["fields"]["Key"]
        notes.append(n)
    if notes:
        c.update_notes(notes)
    interim = snap(c)
    assert all(
        interim[g]["nid"] == n["nid"] and interim[g]["cards"] == n["cards"]
        for g, n in before.items()
    )
    return {
        "migrated_accepted_notes": len(need),
        "evacuated_model_count": len(evac),
        "preserved_all_old_note_card_ids_and_study_state": True,
        "retired_cards_retained": len(set(before) - set(source)),
    }


with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    s = Collection(str(td / "source.anki2"))
    load(s, PACK)
    source = snap(s)
    models = {m["id"]: m for m in s.models.all()}
    s.close()
    c = Collection(str(td / "destination.anki2"))
    load(c, args.legacy_apkg)
    legacy_guids = set(snap(c))
    if args.preimport_component:
        assert args.preimport_component in components
        load(c, args.preimport_component)
    before = snap(c)
    # Native scheduler reviews provide non-trivial learning state and revision history.
    c.decks.select(c.decks.id_for_name("GeoTrainer"))
    for _ in range(7):
        queued = c.sched.get_queued_cards().cards[0]
        card = c.get_card(queued.card.id)
        card.start_timer()
        answer = c.sched.build_answer(card=card, states=queued.states, rating=CardAnswer.GOOD)
        c.sched.answer_card(answer)
    before = snap(c)
    reviews = c.db.all("select * from revlog order by id")
    retired = {
        g: (n["fields"], c.models.get(n["mid"])) for g, n in before.items() if g not in source
    }
    r = upgrade(c, source, models)
    load(c, PACK, always=True)
    after = snap(c)
    overlap = set(before) & set(source)
    matches = sum(
        after[g]["mid"] == source[g]["mid"] and after[g]["fields"] == source[g]["fields"]
        for g in overlap
    )
    exact_templates = sum(
        c.models.get(after[g]["mid"])["css"] == models[source[g]["mid"]]["css"]
        and [(t["qfmt"], t["afmt"]) for t in c.models.get(after[g]["mid"])["tmpls"]]
        == [(t["qfmt"], t["afmt"]) for t in models[source[g]["mid"]]["tmpls"]]
        for g in overlap
    )
    assert matches == exact_templates == len(overlap)
    assert len(legacy_guids & set(source)) == 1624
    assert all(
        after[g]["mid"] == n["mid"] and after[g]["fields"] == n["fields"] for g, n in source.items()
    )
    assert all(
        after[g]["nid"] == n["nid"] and after[g]["cards"] == n["cards"] for g, n in before.items()
    )
    assert c.db.all("select * from revlog order by id") == reviews
    assert len(reviews) == 7
    assert all(after[g]["deck_ids"] == n["deck_ids"] for g, n in before.items())
    for g, (fields, old_model) in retired.items():
        new_model = c.models.get(after[g]["mid"])
        assert after[g]["fields"] == fields
        assert new_model["css"] == old_model["css"]
        assert [(t["qfmt"], t["afmt"]) for t in new_model["tmpls"]] == [
            (t["qfmt"], t["afmt"]) for t in old_model["tmpls"]
        ]
    assert c.note_count() == len(set(before) | set(source)) == 3099
    assert c.card_count() == 4232 + 92 == 4324
    assert c.db.scalar("select count(*)-count(distinct guid) from notes") == 0
    r.update(
        {
            "status": "passed-prototype",
            "all_accepted_old_fields_and_current_model_ids_exact": matches,
            "all_accepted_old_templates_css_exact": exact_templates,
            "after_notes": c.note_count(),
            "after_cards": c.card_count(),
            "new_expected_full_cards": 4232,
            "retained_retired_cards": 92,
            "review_history_preserved": True,
            "model_ids_changed_for_legacy_upgrade": True,
            "no_live_collection_access": True,
            "no_submission": True,
            "retired_fields_templates_css_preserved": True,
            "preimport_component": args.preimport_component.name
            if args.preimport_component
            else None,
        }
    )
    second = upgrade(c, source, models)
    assert second["migrated_accepted_notes"] == 0
    r["idempotent_second_upgrade_no_migration"] = True
    # Current delivered components must remain compatible with this upgraded state.
    for p in components:
        load(c, p, always=True)
    assert c.note_count() == 3099 and c.card_count() == 4324
    final = snap(c)
    assert all(
        final[g]["nid"] == n["nid"] and final[g]["cards"] == n["cards"] for g, n in before.items()
    )
    assert all(
        final[g]["mid"] == n["mid"] and final[g]["fields"] == n["fields"] for g, n in source.items()
    )
    assert all(
        c.models.get(mid)["css"] == m["css"]
        and [(t["qfmt"], t["afmt"]) for t in c.models.get(mid)["tmpls"]]
        == [(t["qfmt"], t["afmt"]) for t in m["tmpls"]]
        for mid, m in models.items()
        if any(n["mid"] == mid for n in source.values())
    )
    r["all_3007_current_notes_semantic_fields_and_model_ids_exact"] = True
    r["all_106_current_templates_css_exact_after_components"] = True
    r["seven_native_review_records_preserved"] = True
    r["legacy_native_deck_assignments_preserved"] = True
    r["all_fifteen_delivered_components_no_duplicates_or_study_state_changes"] = True
    r["legacy_sha256"] = hashlib.sha256(args.legacy_apkg.read_bytes()).hexdigest()
    r["current_sha256"] = hashlib.sha256(PACK.read_bytes()).hexdigest()
    r["components_sha256"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in components
    }
    args.receipt.write_text(json.dumps(r, indent=2) + "\n")
    print(json.dumps(r, indent=2))
    c.close()
