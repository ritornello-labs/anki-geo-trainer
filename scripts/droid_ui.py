"""Tiny AnkiDroid emulator UI driver: dump the accessibility tree over adb and
tap elements by visible text or content-desc. Used by the AnkiDroid smoke lane
(no Playwright dependency; plain adb + uiautomator)."""

from __future__ import annotations

import re
import subprocess
import sys
import time


def sh(*args: str, check: bool = True) -> str:
    r = subprocess.run(["adb", *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"adb {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout


def dump() -> str:
    sh("shell", "uiautomator", "dump", "/sdcard/ui.xml", check=False)
    return sh("shell", "cat", "/sdcard/ui.xml", check=False)


NODE_RE = re.compile(r"<node[^>]*/>|<node[^>]*>")


def find_bounds(xml: str, needle: str) -> tuple[int, int] | None:
    """Center of the first node whose text or content-desc contains needle."""
    for node in NODE_RE.findall(xml):
        if f'text="{needle}' in node or f'content-desc="{needle}' in node or (
            needle.lower() in node.lower() and ("text=" in node or "content-desc=" in node)
        ):
            m = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', node)
            if m:
                x0, y0, x1, y1 = map(int, m.groups())
                if x1 > x0 and y1 > y0:
                    return (x0 + x1) // 2, (y0 + y1) // 2
    return None


def tap_text(needle: str, tries: int = 6, wait: float = 1.2) -> bool:
    for _ in range(tries):
        xml = dump()
        pt = find_bounds(xml, needle)
        if pt:
            sh("shell", "input", "tap", str(pt[0]), str(pt[1]))
            time.sleep(wait)
            return True
        time.sleep(wait)
    return False


def visible_texts() -> list[str]:
    xml = dump()
    texts = re.findall(r'(?:text|content-desc)="([^"]{1,90})"', xml)
    return [t for t in texts if t.strip()]


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "tap":
        ok = tap_text(sys.argv[2])
        print("tapped" if ok else "NOT FOUND")
        sys.exit(0 if ok else 1)
    elif cmd == "texts":
        print(visible_texts())
