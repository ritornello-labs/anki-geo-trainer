#!/usr/bin/env python3
"""Supported-helper integration tests. APKG inputs only, temporary collections only."""

import argparse
import importlib.util
import json
import tempfile
from pathlib import Path

from anki.collection import Collection
from anki.scheduler.v3 import CardAnswer

p = argparse.ArgumentParser()
p.add_argument("--legacy-apkg", type=Path, required=True)
p.add_argument("--current-apkg", type=Path, required=True)
p.add_argument("--components-dir", type=Path, required=True)
p.add_argument("--receipt", type=Path, required=True)
a = p.parse_args()
spec = importlib.util.spec_from_file_location(
    "upgrade_core", Path(__file__).resolve().parents[1] / "upgrade/geo_trainer_july_upgrade/core.py"
)
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
components = sorted(a.components_dir.glob("*.apkg"))
assert len(components) == 15
results = {}


def reviewed(c):
    c.decks.select(c.decks.id_for_name("GeoTrainer"))
    for _ in range(7):
        q = c.sched.get_queued_cards().cards[0]
        card = c.get_card(q.card.id)
        card.start_timer()
        c.sched.answer_card(
            c.sched.build_answer(card=card, states=q.states, rating=CardAnswer.GOOD)
        )


with tempfile.TemporaryDirectory(prefix="geotrainer-helper-test-") as td:
    td = Path(td)
    for mode in (
        "july",
        "partial",
        "custom-field",
        "unrelated-collision",
        "interruption",
        "backup-failure",
    ):
        c = Collection(str(td / (mode + ".anki2")))
        core.load(c, a.legacy_apkg)
        if mode == "partial":
            core.load(c, a.components_dir / "geo-trainer-world-countries.apkg")
        reviewed(c)
        basic = c.models.new("Unrelated QA")
        c.models.add_field(basic, c.models.new_field("Question"))
        c.models.add_field(basic, c.models.new_field("Answer"))
        t = c.models.new_template("Recall")
        t["qfmt"] = "{{Question}}"
        t["afmt"] = "{{FrontSide}}<hr>{{Answer}}"
        c.models.add_template(basic, t)
        basic = c.models.get(c.models.add_dict(basic).id)
        n = c.new_note(basic)
        n["Question"] = "Synthetic control"
        n["Answer"] = "Preserve me"
        c.add_note(n, c.decks.id("Unrelated control"))
        unrelated_id = n.id
        before = core.snapshot(c)
        media = Path(c.media.dir())
        (media / "untouched.txt").write_text("synthetic control")
        if mode == "custom-field":
            nid = c.db.scalar("select id from notes where id!=? limit 1", unrelated_id)
            n = c.get_note(nid)
            n.fields[0] += " custom edit"
            c.update_note(n)
            before = core.snapshot(c)
        if mode == "unrelated-collision":
            mid = c.db.scalar("select mid from notes where id!=? limit 1", unrelated_id)
            n = c.new_note(c.models.get(mid))
            n.fields[0] = "Unrelated collision"
            c.add_note(n, c.decks.id("Unrelated control"))
            before = core.snapshot(c)
        if mode == "backup-failure":
            c.create_backup = lambda **kwargs: (_ for _ in ()).throw(
                OSError("synthetic backup failure")
            )
        if mode in ("custom-field", "unrelated-collision", "backup-failure"):
            try:
                core.run(c, a.current_apkg, td / (mode + "-recovery"))
            except (core.UpgradeError, OSError):
                pass
            else:
                raise AssertionError("must reject")
            assert core.snapshot(c) == before
            results[mode] = "rejected before mutation"
        elif mode == "interruption":

            def interrupt(step):
                if step == "evacuated":
                    raise RuntimeError("synthetic interruption")

            try:
                core.run(c, a.current_apkg, td / (mode + "-recovery"), checkpoint=interrupt)
            except core.UpgradeError:
                pass
            else:
                raise AssertionError("must interrupt")
            marker = next((td / (mode + "-recovery")).glob("*/status.json"))
            assert json.loads(marker.read_text())["state"] == "failed"
            try:
                core.run(c, a.current_apkg, td / (mode + "-recovery"))
            except core.UpgradeError as exc:
                assert "interrupted" in str(exc)
            else:
                raise AssertionError("must block retry")
            backup = next(marker.parent.glob("*.colpkg"))
            assert backup.stat().st_size
            from anki._backend import RustBackend

            restore_path = td / "restored.anki2"
            RustBackend().import_collection_package(
                col_path=str(restore_path),
                backup_path=str(backup),
                media_folder=str(td / "restored.media"),
                media_db=str(td / "restored.media.db2"),
            )
            restored = Collection(str(restore_path))
            assert core.snapshot(restored) == before
            restored.close()
            results[mode] = (
                "native backup restored exact notes, cards and reviews; failed marker blocks retry"
            )
        else:
            r = core.run(c, a.current_apkg, td / (mode + "-recovery"))
            assert c.note_count() == 3100 and c.card_count() == 4325
            assert core.snapshot(c)[2] == before[2]
            assert c.get_note(unrelated_id)["Answer"] == "Preserve me"
            assert (media / "untouched.txt").read_text() == "synthetic control"
            after = core.snapshot(c)
            for pack in components:
                core.load(c, pack)
            assert core.snapshot(c) == after
            try:
                core.inspect(c, a.current_apkg)
            except core.UpgradeError as exc:
                assert "No supported July" in str(exc)
            else:
                raise AssertionError("must recognize current install")
            results[mode] = {
                "migrated": r["migrated"],
                "all_fifteen_components_safe": True,
                "unrelated_content_preserved": True,
                "seven_reviews_preserved": True,
                "backup_created": True,
                "idempotent_preflight": True,
            }
        c.close()
a.receipt.write_text(
    json.dumps(
        {
            "status": "passed",
            "native_anki": "25.09",
            "personal_collection_accessed": False,
            "tests": results,
        },
        indent=2,
    )
    + "\n"
)
print("Supported upgrade integration checks passed.")
