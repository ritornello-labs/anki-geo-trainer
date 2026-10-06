"""User-invoked Tools menu; never runs at import/profile-open or syncs."""

from pathlib import Path

from aqt import mw
from aqt.operations import QueryOp
from aqt.qt import QAction
from aqt.utils import askUser, getFile, showInfo, showWarning

from .core import run


def launch():
    if not mw.col:
        return
    pack = getFile(
        mw,
        "Select the supported GeoTrainer Full Edition APKG",
        None,
        key="geotrainer-july-upgrade",
        filter="Anki deck package (*.apkg)",
    )
    if not pack:
        return
    if not askUser(
        "Upgrade the July GeoTrainer installation?\n\nThis creates a collection backup and saves affected media, then updates GeoTrainer content. Existing note/card identities, decks and review history are preserved; old retired exercises remain. Custom content or templates cause preflight to stop.\n\nThis changes note types and may require a full sync. The helper never syncs or chooses a direction. Finish syncing all devices before starting, and keep them closed during the upgrade.\n\nProceed?",
        parent=mw,
        defaultno=True,
    ):
        return
    recovery = Path(mw.pm.profileFolder()) / "geotrainer-upgrade-recovery"

    def success(result):
        mw.reset()
        showInfo(
            "GeoTrainer upgrade verified. Migrated "
            + str(result["migrated"])
            + " notes.\n\nBackup and saved media: "
            + result["recovery"]
            + "\n\nRead JULY_UPGRADE.md before syncing. Check this desktop collection first; the helper has not synced. You can remove the helper after verifying the upgrade.",
            parent=mw,
        )

    def failure(exc):
        mw.reset()
        showWarning(str(exc), parent=mw)

    QueryOp(parent=mw, op=lambda col: run(col, Path(pack), recovery), success=success).failure(
        failure
    ).with_progress("Backing up and upgrading GeoTrainer…").run_in_background()


action = QAction("GeoTrainer: upgrade July edition…", mw)
action.triggered.connect(launch)
mw.form.menuTools.addAction(action)
