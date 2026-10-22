"""Fail if any file looks like it contains IPTV credentials or a playlist.

    python tools/check_secrets.py              # every tracked file (CI)
    python tools/check_secrets.py FILE...      # just these files (pre-commit hook)

Hard rule: IPTV usernames, passwords, server URLs and M3U files never enter this repo.
The patterns are assembled from pieces so this file doesn't flag itself.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

PATTERNS = {
    "Xtream stream URL": re.compile(r"/(live|movie|series)/[^/\s\"']+/[^/\s\"']+/\d+"),
    # short form some providers use: http://host:port/USER/PASS/<stream id>
    # (the id must end the address; x.com/<user>/status/<id> has the same shape and is allowed)
    "IPTV stream URL": re.compile(r"https?://(?!(www\.)?(x|twitter)\.com/)[^\s/\"']+"
                                  r"/[A-Za-z0-9_-]{4,}/[A-Za-z0-9_-]{4,}/\d{2,}(\.\w{2,4})?(?=$|[\s\"'<>)\]])"),
    "user name parameter": re.compile(r"\b" + "user" + r"name\s*=", re.I),
    "password parameter": re.compile(r"\b" + "pass" + r"word\s*=", re.I),
    "Xtream API endpoint": re.compile(r"(player_api|get|xmltv)\.php\?", re.I),
    "M3U playlist header": re.compile("#EXT" + "M3U"),
}


def scan_text(text: str) -> list[tuple[int, str]]:
    hits = []
    for n, line in enumerate(text.splitlines(), 1):
        for name, rx in PATTERNS.items():
            if rx.search(line):
                hits.append((n, name))
    return hits


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True).stdout
    return out.splitlines()


def main(argv: list[str]) -> int:
    files = argv or tracked_files()
    bad = 0
    for f in files:
        p = Path(f)
        if not p.is_file():
            continue
        if p.suffix.lower() in (".m3u", ".m3u8"):
            print(f"{f}: playlist files must never be committed")
            bad += 1
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for n, name in scan_text(text):
            print(f"{f}:{n}: looks like {name}")
            bad += 1
    if bad:
        print("\nRefusing: IPTV credentials, server URLs and playlists must stay on your devices.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
