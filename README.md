# Sports TV guide

Four days of public TV listings for about 66 sports channels (UK: Virgin Media, Sky Sports F1;
Germany: MagentaTV, DAZN; Netherlands: Ziggo, Delta), grabbed once a day with
[iptv-org/epg](https://github.com/iptv-org/epg) and compacted into one JSON file:

    https://raw.githubusercontent.com/hannesnie-cmd/sports-tv-guide/epg/guide.json

The private sports calendar reads it to pick the TV channel for each game. This repo is public so
the daily grab runs on GitHub's free public minutes.

**Public data only.** `channels.xml` lists the guide channels (site ids from iptv-org). There are no
logins, no playlist, no channel numbers or stream ids from any provider, and none may be added:
`tools/check_secrets.py` blocks IPTV credentials, server URLs and playlists on every push, and as a
pre-commit hook (enable once per clone: `git config core.hooksPath .githooks`).

- `.github/workflows/tvguide.yml`: grab → `compact.py` → force-push `guide.json` to the `epg` branch.
  Started every morning by the sports calendar's Cloudflare Worker; a daily schedule is the backup.
- `compact.py`: keeps live programmes only (no replays, highlights or studio shows), with the
  same text normalization as the calendar's `src/epg.py`.
- To add a channel, add its line from iptv-org's `sites/<site>/<site>.channels.xml` to `channels.xml`.
