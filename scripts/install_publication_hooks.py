"""Install shared hooks for this repository and verify they are executable."""

import argparse
import subprocess
from pathlib import Path

from private_artifacts import validate_private_path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--private-dir", type=Path)
args = parser.parse_args()
if args.private_dir:
    directory = validate_private_path(args.private_dir)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    directory.chmod(0o700)
    subprocess.run(
        ["git", "config", "--local", "geotrainer.privateDirectory", str(directory)], check=True
    )
root = Path(__file__).resolve().parent.parent
hooks = root / ".githooks"
old = subprocess.run(["git", "config", "--get", "core.hooksPath"], capture_output=True, text=True)
if old.returncode == 0 and Path(old.stdout.strip()).resolve() != hooks:
    raise SystemExit(
        "Existing hooksPath is configured; integrate the publication hooks before replacing it."
    )
for name in ("pre-commit", "pre-push"):
    path = hooks / name
    if not path.exists() or not path.stat().st_mode & 0o111:
        raise SystemExit("Publication hooks are missing or not executable.")
subprocess.run(["git", "config", "--local", "core.hooksPath", str(hooks)], check=True)
print("Publication hooks installed for all linked worktrees; keep this checkout available.")
