#!/usr/bin/env python3
"""
render.py: turn snapshot.json into a self-contained index.html.

The template carries a <script id="ll-snapshot" type="application/json"> block.
This script replaces its contents with the snapshot, so the page works when
opened straight from a mounted filespace (file://) with no server and no fetch.

Usage:
    python3 scripts/render.py --snapshot out/snapshot.json --out out/index.html
    python3 scripts/render.py --snapshot out/snapshot.json --publish "/Volumes/<ws>/<fs>/Dashboards/<name>"

--publish copies index.html and snapshot.json into a directory (typically inside
the filespace) and, unless --no-history is given, appends a dated copy of the
snapshot under <publish>/history/ so trends can be built later.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = HERE.parent / "templates" / "dashboard.html"
REQUIRED = ["schema", "generated_at", "stats", "activity", "folders", "cold", "extensions", "recent", "notes"]
DEFAULTS = {
    "flags": [],
    "largest": [],
    "locks": None,
    "budget": "unknown",
    "window_days": 7,
    "title": "LucidLink filespace",
    "source": {"mode": "unknown"},
}


def validate(snap: dict) -> list[str]:
    problems = []
    for k in REQUIRED:
        if k not in snap:
            problems.append(f"missing top-level key: {k}")
    for k, v in DEFAULTS.items():
        snap.setdefault(k, v)
    act = snap.get("activity", {})
    for k in ("events", "by_day", "by_action", "by_actor"):
        if k not in act:
            problems.append(f"missing activity.{k}")
    return problems


def render(snap: dict, template: Path) -> str:
    html = template.read_text(encoding="utf-8")
    payload = json.dumps(snap, ensure_ascii=False).replace("</", "<\\/")
    pattern = re.compile(r'(<script id="ll-snapshot" type="application/json">)(.*?)(</script>)', re.S)
    if not pattern.search(html):
        sys.exit("template has no <script id=\"ll-snapshot\"> block")
    return pattern.sub(lambda m: m.group(1) + payload + m.group(3), html, count=1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    ap.add_argument("--out", help="output html path (default: <snapshot dir>/index.html)")
    ap.add_argument("--publish", help="directory to copy index.html and snapshot.json into, for example a folder inside the filespace")
    ap.add_argument("--no-history", action="store_true")
    args = ap.parse_args()

    snap_path = Path(args.snapshot)
    snap = json.loads(snap_path.read_text(encoding="utf-8"))
    problems = validate(snap)
    if problems:
        sys.exit("snapshot.json is not renderable:\n  " + "\n  ".join(problems) + "\nSee references/snapshot-schema.md")

    out = Path(args.out) if args.out else snap_path.parent / "index.html"
    out.write_text(render(snap, Path(args.template)), encoding="utf-8")
    print(f"wrote {out}")

    if args.publish:
        pub = Path(args.publish)
        pub.mkdir(parents=True, exist_ok=True)
        shutil.copy2(out, pub / "index.html")
        shutil.copy2(snap_path, pub / "snapshot.json")
        if not args.no_history:
            hist = pub / "history"
            hist.mkdir(exist_ok=True)
            stamp = snap.get("generated_at", dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")).replace(":", ".")
            shutil.copy2(snap_path, hist / f"snapshot-{stamp}.json")
        print(f"published to {pub}")


if __name__ == "__main__":
    main()
