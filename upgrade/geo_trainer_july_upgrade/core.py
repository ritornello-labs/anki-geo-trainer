"""Native-API July transition. Never syncs and never deletes existing notes/cards."""

from __future__ import annotations

import collections
import hashlib
import json
import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path

from anki.collection import Collection, ImportAnkiPackageOptions, ImportAnkiPackageRequest
from anki.import_export_pb2 import IMPORT_ANKI_PACKAGE_UPDATE_CONDITION_ALWAYS as ALWAYS
from anki.notetypes_pb2 import ChangeNotetypeRequest

CATALOG = Path(__file__).with_name("catalog.json")


class UpgradeError(Exception):
    pass


def require(ok, message):
    if not ok:
        raise UpgradeError(message)


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def schema(model):
    return [f["name"] for f in model["flds"]], [t["name"] for t in model["tmpls"]]


def render_signature(model):
    return [schema(model), model["css"], [[t["qfmt"], t["afmt"]] for t in model["tmpls"]]]


def snapshot(col):
    notes = {}
    for nid, guid, mid, fields, tags in col.db.all("select id,guid,mid,flds,tags from notes"):
        require(guid not in notes, "Duplicate note GUIDs: stop and resolve these before upgrading.")
        model = col.models.get(mid)
        notes[guid] = {
            "nid": nid,
            "mid": mid,
            "fields": dict(
                zip([f["name"] for f in model["flds"]], fields.split("\x1f"), strict=True)
            ),
            "tags": tags,
        }
    cards = col.db.all(
        "select id,nid,did,ord,type,queue,due,ivl,factor,reps,lapses,left,odue,odid,flags,data from cards order by id"
    )
    reviews = digest(col.db.all("select * from revlog order by id"))
    return notes, cards, reviews


def load(col, pack):
    return col.import_anki_package(
        ImportAnkiPackageRequest(
            package_path=str(pack),
            options=ImportAnkiPackageOptions(
                merge_notetypes=False,
                with_scheduling=False,
                with_deck_configs=False,
                update_notes=ALWAYS,
                update_notetypes=ALWAYS,
            ),
        )
    )


def move(col, old, new, nids):
    a, b = col.models.get(old), col.models.get(new)
    require(
        len(a["tmpls"]) == len(b["tmpls"]) == 1,
        "Unsupported multi-template note type; no automatic mapping is allowed.",
    )
    indexes = {f["name"]: i for i, f in enumerate(a["flds"])}
    col.models.change_notetype_of_notes(
        ChangeNotetypeRequest(
            note_ids=nids,
            old_notetype_id=old,
            new_notetype_id=new,
            old_notetype_name=a["name"],
            current_schema=col.db.scalar("select scm from col"),
            new_fields=[indexes.get(f["name"], -1) for f in b["flds"]],
            new_templates=[0],
        )
    )


def inspect(col, pack):
    """Read-only for destination. Import only into a new temporary source collection."""
    catalog = json.loads(CATALOG.read_text())
    require(
        hashlib.sha256(pack.read_bytes()).hexdigest() in catalog["package_sha256"],
        "Select the supported October full-edition APKG from the matching GitHub release.",
    )
    with tempfile.TemporaryDirectory(prefix="geotrainer-source-") as td:
        source_col = Collection(str(Path(td) / "source.anki2"))
        try:
            load(source_col, pack)
            source, source_cards, _ = snapshot(source_col)
            source_counts = collections.Counter(row[1] for row in source_cards)
            used = {n["mid"] for n in source.values()}
            models = {m["id"]: m for m in source_col.models.all() if m["id"] in used}
        finally:
            source_col.close()
    before, cards, reviews = snapshot(col)
    accepted = set(before) & set(source)
    need = {
        g
        for g in accepted
        if before[g]["mid"] != source[g]["mid"]
        or set(before[g]["fields"]) != set(source[g]["fields"])
    }
    require(
        need,
        "No supported July note types need migration. For a current installation, use ordinary APKG import with note-type merging disabled.",
    )
    legacy = catalog["legacy"]
    for g in accepted:
        old = before[g]
        allowed = [digest(source[g]["fields"])]
        if g in legacy:
            allowed.append(legacy[g]["fields_sha256"])
        require(
            digest(old["fields"]) in allowed,
            "A GeoTrainer note has custom or unrecognized content. Upgrade stopped before changes; preserve your edits and request a manual migration.",
        )
    targets = {source[g]["mid"] for g in need}
    for mid, canonical in models.items():
        existing = col.models.get(mid)
        if existing and schema(existing) != schema(canonical):
            targets.add(mid)
    evac = {before[g]["mid"] for g in need}
    evac |= {
        mid
        for mid in targets
        if col.models.get(mid) and col.db.scalar("select count(*) from notes where mid=?", mid)
    }
    affected = evac | set(models)
    for g, old in before.items():
        if old["mid"] not in affected:
            continue
        if g not in source:
            require(
                g in legacy and digest(old["fields"]) == legacy[g]["fields_sha256"],
                "An unrelated or customized note uses a required GeoTrainer note type. Upgrade stopped before changes.",
            )
        m = col.models.get(old["mid"])
        signatures = [digest(render_signature(models[source[g]["mid"]]))] if g in source else []
        if g in legacy:
            signatures.append(legacy[g]["render_sha256"])
        require(
            digest(render_signature(m)) in signatures,
            "A required note type has customized or unrecognized templates. Upgrade stopped before changes.",
        )
        if old["mid"] in evac:
            require(len(m["tmpls"]) == 1, "Unsupported note-type migration schema.")
    require(
        all(
            schema(models[source[g]["mid"]])[1] and len(models[source[g]["mid"]]["tmpls"]) == 1
            for g in need
        ),
        "Unsupported target templates.",
    )
    outside_models = {m["id"]: digest(m) for m in col.models.all() if m["id"] not in affected}
    retired_render = {
        g: digest(render_signature(col.models.get(n["mid"])))
        for g, n in before.items()
        if g not in source
    }
    return {
        "before": before,
        "cards": cards,
        "reviews": reviews,
        "source": source,
        "models": models,
        "need": need,
        "targets": targets,
        "evac": evac,
        "outside_models": outside_models,
        "retired_render": retired_render,
        "source_counts": source_counts,
    }


def verify(col, plan):
    after, cards, reviews = snapshot(col)
    before, source = plan["before"], plan["source"]
    original_card_ids = {row[0] for row in plan["cards"]}
    require(
        [r for r in cards if r[0] in original_card_ids] == plan["cards"],
        "Card identity, deck assignment or study-state verification failed.",
    )
    require(reviews == plan["reviews"], "Review-history verification failed.")
    require(set(after) == set(before) | set(source), "Unexpected note count or GUID after upgrade.")
    for g, old in before.items():
        require(
            after[g]["nid"] == old["nid"] and after[g]["tags"] == old["tags"],
            "Existing note identity or tags changed.",
        )
        if g not in source:
            require(
                after[g]["fields"] == old["fields"]
                and digest(render_signature(col.models.get(after[g]["mid"])))
                == plan["retired_render"][g],
                "Unrelated or retired content changed.",
            )
            if old["mid"] not in plan["evac"]:
                require(after[g]["mid"] == old["mid"], "An unrelated note type changed.")
    for g, expected in source.items():
        require(
            after[g]["mid"] == expected["mid"] and after[g]["fields"] == expected["fields"],
            "Current GeoTrainer content verification failed.",
        )
    for mid, model in plan["models"].items():
        require(
            render_signature(col.models.get(mid)) == render_signature(model),
            "Canonical template verification failed.",
        )
    for mid, sig in plan["outside_models"].items():
        require(digest(col.models.get(mid)) == sig, "Unrelated note type changed.")
    expected_new = sum(plan["source_counts"][source[g]["nid"]] for g in set(source) - set(before))
    require(len(cards) == len(plan["cards"]) + expected_new, "Unexpected card count.")
    require(
        col.db.all("pragma integrity_check") == [["ok"]],
        "Collection integrity verification failed.",
    )


def run(col, pack, recovery_root, checkpoint=lambda step: None):
    """User-confirmed operation. Local recovery files must never be published."""
    pack, recovery_root = Path(pack), Path(recovery_root)
    recovery_root.mkdir(parents=True, exist_ok=True)
    for marker in recovery_root.glob("*/status.json"):
        require(
            json.loads(marker.read_text())["state"] in ("verified", "restored"),
            "An interrupted upgrade exists. Restore its backup before retrying; see JULY_UPGRADE.md.",
        )
    plan = inspect(col, pack)
    recovery = recovery_root / uuid.uuid4().hex
    recovery.mkdir()
    # Native notes/reviews/decks backup, plus every existing media file that this
    # package might replace. New media can safely remain after rollback.
    require(
        col.create_backup(backup_folder=str(recovery), force=True, wait_for_completion=True),
        "Anki did not create a fresh backup. Nothing was changed. Restart Anki and retry.",
    )
    backups = list(recovery.glob("*.colpkg"))
    require(
        len(backups) == 1 and backups[0].stat().st_size > 0,
        "Backup verification failed; nothing was changed.",
    )
    media_dir = Path(col.media.dir())
    saved_media = recovery / "media"
    saved_media.mkdir()
    with zipfile.ZipFile(pack) as archive:
        for name in json.loads(archive.read("media")).values():
            require(Path(name).name == name and name not in (".", ".."), "Unsafe media name.")
            existing = media_dir / name
            if existing.is_file():
                shutil.copy2(existing, saved_media / name)
    marker = recovery / "status.json"
    marker.write_text(json.dumps({"state": "started", "backup": backups[0].name}) + "\n")
    try:
        checkpoint("backed-up")
        tempmap = {}
        for mid in sorted(plan["evac"]):
            model = col.models.get(mid)
            ids = col.db.list("select id from notes where mid=?", mid)
            clone = col.models.copy(model, add=False)
            clone["name"] = "GeoTrainer July preserved — " + model["name"]
            new = col.models.add_dict(clone).id
            tempmap[mid] = new
            move(col, mid, new, ids)
        checkpoint("evacuated")
        for mid in sorted(plan["targets"]):
            if col.models.get(mid):
                require(
                    col.db.scalar("select count(*) from notes where mid=?", mid) == 0,
                    "A conflicting note type is not empty.",
                )
                col.models.remove(mid)
        load(col, pack)
        groups = collections.defaultdict(list)
        for g in plan["need"]:
            groups[(tempmap[plan["before"][g]["mid"]], plan["source"][g]["mid"])].append(
                plan["before"][g]["nid"]
            )
        for (old, new), ids in groups.items():
            move(col, old, new, ids)
        updates = []
        for g in plan["need"]:
            note = col.get_note(plan["before"][g]["nid"])
            for name, value in plan["source"][g]["fields"].items():
                note[name] = value
            updates.append(note)
        col.update_notes(updates)
        load(col, pack)
        verify(col, plan)
        checkpoint("verified")
        marker.write_text(json.dumps({"state": "verified", "backup": backups[0].name}) + "\n")
        return {
            "migrated": len(plan["need"]),
            "recovery": str(recovery),
            "backup": str(backups[0]),
            "retained": len(set(plan["before"]) - set(plan["source"])),
        }
    except BaseException as exc:
        marker.write_text(json.dumps({"state": "failed", "backup": backups[0].name}) + "\n")
        raise UpgradeError(
            "Upgrade stopped. Do not sync or retry. Restore the collection backup and saved media from "
            + str(recovery)
            + "; follow JULY_UPGRADE.md. Reason: "
            + str(exc)
        ) from exc
