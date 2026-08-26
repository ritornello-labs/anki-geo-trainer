#!/usr/bin/env python3
"""Fail when live Anki collection snapshots are tracked by Git."""

from __future__ import annotations

import subprocess
import sys


FORBIDDEN_PREFIXES = (
    "backups/live-imports/",
    "backups/live-moves/",
)
FORBIDDEN_BASENAMES = {
    "cards-info.json",
    "cards-scheduling.json",
    "identity.json",
    "notes-info.json",
    "original-cards-info.json",
    "original-notes-info.json",
}


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        stdout=subprocess.PIPE,
    )
    return [
        entry.decode("utf-8", errors="surrogateescape")
        for entry in result.stdout.split(b"\0")
        if entry
    ]


def main() -> int:
    violations = sorted(
        path
        for path in tracked_files()
        if path.startswith(FORBIDDEN_PREFIXES)
        or path.rsplit("/", 1)[-1] in FORBIDDEN_BASENAMES
    )
    if not violations:
        print("privacy-check: no tracked live-collection backup artifacts")
        return 0

    print("privacy-check: tracked private Anki artifacts found:", file=sys.stderr)
    for path in violations:
        print(f"  {path}", file=sys.stderr)
    print(
        "Keep live snapshots outside Git; backups/live-imports and "
        "backups/live-moves are ignored.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
