"""Compact the grabbed XMLTV guide into the small JSON file the sports-calendar build reads.

    python3 compact.py guide.xml channels.xml out/guide.json

Keeps every programme except replays, highlights and studio shows, as
{"c": channel, "s": grabber site, "a": start, "b": stop, "t": title, "x": normalized text}.
The text normalization and the not-live filter are copied from sports-calendar's src/epg.py
(norm, NOT_LIVE, LIVE, Programme.not_live, compact) and must stay identical to it.
Standard library only, so the workflow needs no installs.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

NOT_LIVE = re.compile(
    r"\b(highlights?|zusammenfassung|samenvatting|wiederholung|herhaling|replay|re-?air|reprise|"
    r"classics?|best of|magazin|countdown|vorbericht|voorbeschouwing|preview|review|reaction|"
    r"analyse|nabeschouwing|studio|news|nachrichten|journaal|goals|tore|doelpunten|"
    r"retro|rewind|uncut|in full)\b")
LIVE = re.compile(r"\b(live|direct|direkt)\b")


def norm(text: str | None) -> str:
    text = unicodedata.normalize("NFKD", (text or "").lower().replace("ß", "ss"))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return " " + re.sub(r"[^a-z0-9]+", " ", text).strip() + " "


def not_live(title: str, text: str) -> bool:
    # Sky Deutschland prefixes almost everything with "Live", so a highlights/replay word in the
    # title always wins; elsewhere in the description, "live" can override it.
    if NOT_LIVE.search(norm(title)):
        return True
    return bool(NOT_LIVE.search(text)) and not LIVE.search(text)


def _time(s: str) -> datetime:
    return datetime.strptime(s.strip(), "%Y%m%d%H%M%S %z")


def channel_sites(channels_xml: str) -> dict[str, str]:
    return {name.strip(): site for site, name in re.findall(r'site="([^"]+)"[^>]*>([^<]+)<', channels_xml)}


def compact(xml: bytes, sites: dict[str, str]) -> tuple[list[dict], dict[str, int]]:
    root = ET.fromstring(xml)
    names = {c.get("id"): (c.findtext("display-name") or c.get("id")) for c in root.iter("channel")}
    rows, per = [], {}
    for p in root.iter("programme"):
        name = names.get(p.get("channel"), p.get("channel"))
        parts = [p.findtext("title"), p.findtext("sub-title"), p.findtext("desc"),
                 " ".join(c.text or "" for c in p.findall("category"))]
        try:
            start = _time(p.get("start"))
            stop = _time(p.get("stop")) if p.get("stop") else None
        except (TypeError, ValueError):
            continue
        per[name] = per.get(name, 0) + 1
        title, text = p.findtext("title") or "", norm(" ".join(x for x in parts if x))
        if not not_live(title, text):
            rows.append({"c": name, "s": sites.get(name, ""), "a": start.isoformat(),
                         "b": stop.isoformat() if stop else None, "t": title, "x": text})
    return rows, per


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        sys.exit(__doc__)
    guide, chans, out = argv
    sites = channel_sites(Path(chans).read_text(encoding="utf-8"))
    rows, per = compact(Path(guide).read_bytes(), sites)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps({"programmes": rows, "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
                                     "channels_with_listings": len(per), "channels": len(sites)},
                                    ensure_ascii=False))
    empty = [n for n in sites if not per.get(n)]
    print(f"{len(rows)} of {sum(per.values())} programmes kept from {len(per)}/{len(sites)} channels")
    if empty:
        print("no listings: " + ", ".join(empty))
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
