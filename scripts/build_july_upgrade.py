#!/usr/bin/env python3
"""Deterministic helper package; explicit source allowlist, no profile/recovery data."""

import zipfile
from pathlib import Path

from check_private_artifacts import content_reasons

root = Path(__file__).resolve().parents[1]
out = root / "dist/geo-trainer-july-upgrade.ankiaddon"
out.parent.mkdir(exist_ok=True)
files = {
    name: (root / "upgrade/geo_trainer_july_upgrade" / name).read_bytes()
    for name in ("__init__.py", "core.py", "manifest.json", "catalog.json")
}
files["JULY_UPGRADE.md"] = (root / "release/JULY_UPGRADE.md").read_bytes()
with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for name, data in sorted(files.items()):
        info = zipfile.ZipInfo(name, date_time=(2026, 10, 5, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        z.writestr(info, data)
if content_reasons(out.name, out.read_bytes()):
    out.unlink()
    raise SystemExit("Helper package publication check failed.")
print("Helper packaged; exact artifact check passed.")
