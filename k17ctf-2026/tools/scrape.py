#!/usr/bin/env python3
"""Grab all challenges (description + attachments) from the k17ctf scoreboard API."""
import hashlib
import json
import os
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

API = "https://api-k17ctf.secso.cc"
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "challenges"
RAW = ROOT / "raw"
TOKEN = (ROOT / "token.txt").read_text().strip()

HEADERS = {
    "authorization": f"Bearer {TOKEN}",
    "accept": "*/*",
    "origin": "https://scoreboard.k17ctf.secso.cc",
    "referer": "https://scoreboard.k17ctf.secso.cc/",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
}


def get(path):
    req = urllib.request.Request(f"{API}{path}", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def get_json(path):
    return json.loads(get(path))


def slugify(s):
    return re.sub(r"[^A-Za-z0-9._-]+", "-", s).strip("-").lower() or "unnamed"


def primary_category(tags):
    cats = [c.strip() for c in tags.get("categories", "").split(",") if c.strip()]
    for c in cats:
        if c != "beginner":
            return c
    return cats[0] if cats else "uncategorized"


def download(rel_url, dest, expected_hash=None):
    if dest.exists() and expected_hash:
        algo, _, want = expected_hash.partition(":")
        h = hashlib.new(algo)
        with open(dest, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        if h.hexdigest() == want:
            return f"skip (verified)  {dest.name}"
    data = get("/" + rel_url.lstrip("/"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    if expected_hash:
        algo, _, want = expected_hash.partition(":")
        got = hashlib.new(algo, data).hexdigest()
        if got != want:
            return f"!! HASH MISMATCH {dest.name}: got {got}, want {want}"
    return f"ok {len(data):>9,} B  {dest}"


def write_readme(c, d, cdir):
    meta = d.get("metadata") or {}
    files = meta.get("files") or []
    hints = meta.get("hints") or []
    tags = c.get("tags") or {}

    lines = [
        f"# {c['title']}",
        "",
        f"- **ID**: {c['id']}",
        f"- **Slug**: `{c['slug']}`",
        f"- **Category**: {tags.get('categories', '?')}",
        f"- **Difficulty**: {tags.get('difficulty', '?')}",
        f"- **Points**: {c.get('value', '?')}  ({c.get('solve_count', '?')} solves)",
    ]
    if tags.get("author"):
        lines.append(f"- **Author**: {tags['author']}")
    lines += ["", "## Description", "", (d.get("description") or "").strip() or "_(empty)_"]

    if files:
        lines += ["", "## Files", ""]
        for f in files:
            lines.append(f"- `{f['filename']}` ({f.get('size', 0):,} bytes) — {f.get('hash', '')}")

    if hints:
        lines += ["", "## Hints", ""]
        for h in hints:
            lines.append(f"- {h.get('content') or h}")

    if meta.get("solve"):
        lines += ["", "## Submission", "", f"`input_type: {meta['solve'].get('input_type')}`"]

    (cdir / "README.md").write_text("\n".join(lines) + "\n")


def main():
    OUT.mkdir(exist_ok=True)
    RAW.mkdir(exist_ok=True)

    listing = get_json("/challenges")["data"]["challenges"]
    listing.sort(key=lambda c: (primary_category(c.get("tags") or {}), c["id"]))
    print(f"[*] {len(listing)} challenges\n")

    jobs = []
    index = []
    for c in listing:
        try:
            d = get_json(f"/challenges/{c['id']}")["data"]
        except Exception as e:
            print(f"[!] challenge {c['id']} ({c['slug']}): {e}")
            continue

        (RAW / f"{c['id']:03d}-{c['slug']}.json").write_text(json.dumps(d, indent=2))

        cat = primary_category(c.get("tags") or {})
        cdir = OUT / slugify(cat) / slugify(c["slug"])
        cdir.mkdir(parents=True, exist_ok=True)
        write_readme(c, d, cdir)

        files = (d.get("metadata") or {}).get("files") or []
        index.append((cat, c, files))
        for f in files:
            jobs.append((f["url"], cdir / f["filename"], f.get("hash"), f["filename"]))

    print(f"[*] {len(jobs)} attachments, downloading...\n")
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(download, u, p, h) for u, p, h, _ in jobs]
        for (u, p, h, name), fut in zip(jobs, futs):
            try:
                print("   ", fut.result())
            except Exception as e:
                print(f"    !! FAILED {name}: {e}")

    print("\n=== summary ===")
    for cat, c, files in index:
        print(f"{cat:<12} {c['title']:<28} {len(files)} file(s)")
    print(f"\n[*] written to {OUT}")


if __name__ == "__main__":
    sys.exit(main())
