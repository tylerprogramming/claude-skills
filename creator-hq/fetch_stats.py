#!/usr/bin/env python3
"""
Creator HQ - stats puller.

Pulls channel meta + recent uploads for each creator in config.json via yt-dlp
(no API key needed), downloads thumbnails, and writes a compact snapshot to
~/creator-hq/data/youtube.json. Pure data layer - no rendering here.

Usage:
    python3 fetch_stats.py [config.json]

Reads:  ~/creator-hq/config.json      (or the path passed as argv[1])
Writes: ~/creator-hq/data/youtube.json
        ~/creator-hq/data/thumbs/<id>.jpg
        ~/creator-hq/data/avatar-<n>.jpg
"""
import json
import subprocess
import sys
import datetime
import urllib.request
from pathlib import Path

HOME = Path.home()
BASE = HOME / "creator-hq"
DATA_DIR = BASE / "data"
THUMB_DIR = DATA_DIR / "thumbs"

DEFAULT_RECENT = 15


def run_yt(args, timeout=300):
    """Run yt-dlp and return stdout (empty string on failure)."""
    try:
        r = subprocess.run(
            ["yt-dlp", *args],
            capture_output=True, text=True, timeout=timeout,
        )
        return r.stdout or ""
    except FileNotFoundError:
        sys.exit("yt-dlp is not installed. Install it: pip install -U yt-dlp")
    except subprocess.TimeoutExpired:
        print(f"  ! yt-dlp timed out on {args[-1]}", file=sys.stderr)
        return ""


def channel_url(handle_or_url):
    h = handle_or_url.strip()
    if h.startswith("http"):
        return h.rstrip("/")
    if not h.startswith("@"):
        h = "@" + h
    return f"https://www.youtube.com/{h}"


def download(url, dest):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            dest.write_bytes(r.read())
        return True
    except Exception:
        return False


def fetch_channel_meta(url):
    out = run_yt(["--playlist-items", "0", "-J", url], timeout=60)
    d = json.loads(out) if out.strip() else {}
    thumbs = d.get("thumbnails") or []
    avatar = thumbs[-1]["url"] if thumbs else None
    return {
        "name": d.get("channel") or d.get("uploader"),
        "subs": d.get("channel_follower_count"),
        "avatar": avatar,
    }


def fetch_total_count(videos_url):
    out = run_yt(["--flat-playlist", "-J", videos_url], timeout=120)
    d = json.loads(out) if out.strip() else {}
    return len(d.get("entries") or [])


def fetch_recent(videos_url, n):
    out = run_yt(["--dump-json", "--playlist-end", str(n), videos_url], timeout=360)
    vids = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        vid = d.get("id")
        vids.append({
            "id": vid,
            "title": d.get("title", ""),
            "upload_date": d.get("upload_date"),      # YYYYMMDD
            "views": d.get("view_count"),
            "likes": d.get("like_count"),
            "comments": d.get("comment_count"),
            "duration": d.get("duration"),            # seconds
            "url": d.get("webpage_url") or (f"https://youtu.be/{vid}" if vid else None),
        })
        # subs sometimes only reliable from the video-level json
        vids[-1]["_subs"] = d.get("channel_follower_count")
    return vids


def main():
    cfg_path = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "config.json"
    if not cfg_path.exists():
        sys.exit(f"No config at {cfg_path}. Copy config.example.json to {BASE}/config.json and edit it.")
    cfg = json.loads(cfg_path.read_text())

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    THUMB_DIR.mkdir(parents=True, exist_ok=True)

    recent_n = int(cfg.get("recent_count", DEFAULT_RECENT))
    out_creators = []

    for i, c in enumerate(cfg.get("creators", [])):
        handle = c.get("handle") or c.get("channel_url")
        if not handle:
            print(f"  ! creator #{i} has no handle/channel_url, skipping", file=sys.stderr)
            continue
        url = channel_url(handle)
        videos_url = url + "/videos"
        print(f"Fetching {c.get('name') or handle} ...")

        meta = fetch_channel_meta(url)
        total = fetch_total_count(videos_url)
        vids = fetch_recent(videos_url, recent_n)

        # subs fallback from video-level data
        subs = meta.get("subs")
        if not subs:
            for v in vids:
                if v.get("_subs"):
                    subs = v["_subs"]
                    break
        for v in vids:
            v.pop("_subs", None)

        # avatar
        avatar_file = None
        if meta.get("avatar"):
            af = DATA_DIR / f"avatar-{i}.jpg"
            if download(meta["avatar"], af):
                avatar_file = af.name

        # thumbnails (mqdefault = small, fast, plenty sharp for a card)
        got = 0
        for v in vids:
            if not v.get("id"):
                continue
            tf = THUMB_DIR / f"{v['id']}.jpg"
            if not tf.exists():
                turl = f"https://i.ytimg.com/vi/{v['id']}/mqdefault.jpg"
                if download(turl, tf):
                    got += 1
            v["thumb"] = f"thumbs/{v['id']}.jpg" if tf.exists() else None

        out_creators.append({
            "name": meta.get("name") or c.get("name") or handle,
            "handle": handle,
            "url": url,
            "subs": subs,
            "total_videos": total,
            "avatar": avatar_file,
            "videos": vids,
        })
        print(f"  {len(vids)} recent videos, {got} new thumbs, {subs} subs, {total} total videos")

    snapshot = {
        "fetched_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "creators": out_creators,
    }
    out_path = DATA_DIR / "youtube.json"
    out_path.write_text(json.dumps(snapshot, indent=2))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
