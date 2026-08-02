#!/usr/bin/env python3
"""
Creator HQ — daily snapshot job (runs on the Mac; needs the YT Analytics token).

For every video currently tracked in the `youtube_daily` Supabase table, fetch
today's LIFETIME stats and upsert one row for today:
  - views / likes / comments  → YouTube Data API (videos.list statistics)
  - subscribers gained (lifetime) → YouTube Analytics API (subscribersGained)

Writes to Supabase via the REST API using the anon key (SUPABASE_URL/SUPABASE_KEY
from ~/home-dashboard/.env). Idempotent: replaces today's rows if re-run.

Schedule daily, e.g. crontab:
  30 6 * * * /path/to/python3 ~/.claude/skills/creator-hq/snapshot.py >> ~/creator-hq/snapshot.log 2>&1
"""

# --- skills venv bootstrap: run under .venv, not whatever python3 resolves to.
# Looks for .venv beside this script and up a few levels, then ~/.claude/skills,
# so a skill works wherever you copied it. Compares realpaths, and re-execs at
# most once, because a symlinked path that never compares equal would otherwise
# loop forever. Rationale: "Why there is a venv" in README.md
import os as _os, sys as _sys
if not _os.environ.get("SKILLS_VENV"):
    _base = _os.path.dirname(_os.path.abspath(__file__))
    for _v in [_os.path.realpath(_os.path.join(_base, *([".."] * _i), ".venv")) for _i in range(4)
               ] + [_os.path.realpath(_os.path.expanduser("~/.claude/skills/.venv"))]:
        if _os.path.exists(_os.path.join(_v, "bin", "python3")):
            if _os.path.realpath(_sys.prefix) != _v:
                _os.environ["SKILLS_VENV"] = _v
                _os.execv(_os.path.join(_v, "bin", "python3"),
                          [_os.path.join(_v, "bin", "python3"), *_sys.argv])
            break
# --- end bootstrap ---------------------------------------------------------


import datetime
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude" / "skills" / "yt-analytics"))
import yt_analytics as ya  # noqa: E402
from googleapiclient.discovery import build  # noqa: E402


def load_env():
    for p in (Path.home() / "home-dashboard" / ".env", Path.home() / "creator-hq" / ".env"):
        if p.exists():
            env = {}
            for line in p.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
            if env.get("SUPABASE_URL") and env.get("SUPABASE_KEY"):
                return env["SUPABASE_URL"].rstrip("/"), env["SUPABASE_KEY"]
    sys.exit("SUPABASE_URL / SUPABASE_KEY not found in ~/home-dashboard/.env")


SUPA_URL, SUPA_KEY = load_env()
REST = SUPA_URL + "/rest/v1"


def sb(method, path, body=None, prefer="return=minimal"):
    req = urllib.request.Request(
        REST + path, method=method,
        headers={"apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}",
                 "Content-Type": "application/json", "Prefer": prefer},
    )
    data = json.dumps(body).encode() if body is not None else None
    with urllib.request.urlopen(req, data=data, timeout=45) as r:
        t = r.read().decode()
        return json.loads(t) if t else []


def main():
    today = datetime.date.today().isoformat()
    creds = ya.authenticate()
    youtube = build("youtube", "v3", credentials=creds)
    yta = build("youtubeAnalytics", "v2", credentials=creds)

    # cohort = the videos already tracked in youtube_daily
    tracked = sb("GET", "/youtube_daily?select=video_id,published_date", prefer="return=representation")
    pub_by = {}
    for r in tracked:
        pub_by.setdefault(r["video_id"], r.get("published_date"))
    ids = list(pub_by)
    if not ids:
        sys.exit("No tracked videos in youtube_daily yet.")
    print(f"[{today}] tracking {len(ids)} videos")

    # lifetime views/likes/comments + title (Data API)
    stats = {}
    for i in range(0, len(ids), 50):
        resp = youtube.videos().list(part="statistics,snippet", id=",".join(ids[i:i+50])).execute()
        for it in resp.get("items", []):
            s = it["statistics"]
            stats[it["id"]] = {
                "title": it["snippet"]["title"],
                "views": int(s.get("viewCount", 0)),
                "likes": int(s.get("likeCount")) if "likeCount" in s else None,
                "comments": int(s.get("commentCount")) if "commentCount" in s else None,
                "published": it["snippet"].get("publishedAt", "")[:10] or None,
            }

    # lifetime subscribers gained per video (Analytics API, one query)
    subs = {}
    try:
        rep = yta.reports().query(
            ids="channel==MINE", startDate="2025-01-01", endDate=today,
            metrics="subscribersGained", dimensions="video",
            sort="-subscribersGained", maxResults=200,
        ).execute()
        for row in rep.get("rows", []):
            subs[row[0]] = int(row[1])
    except Exception as e:
        print(f"  ! subscribersGained query failed ({e}); leaving subs null")

    # explicit ids (youtube_daily id sequence is out of sync)
    mx = sb("GET", "/youtube_daily?select=id&order=id.desc&limit=1", prefer="return=representation")
    next_id = (mx[0]["id"] if mx else 0)

    payload = []
    for n, vid in enumerate(ids, 1):
        st = stats.get(vid, {})
        payload.append({
            "id": next_id + n, "date": today, "video_id": vid,
            "title": st.get("title"), "views": st.get("views"),
            "likes": st.get("likes"), "comments": st.get("comments"),
            "subs_gained": subs.get(vid),
            "published_date": pub_by.get(vid) or st.get("published"),
        })

    # idempotent: clear today's rows, then insert fresh
    sb("DELETE", f"/youtube_daily?date=eq.{today}")
    sb("POST", "/youtube_daily", body=payload)
    got_subs = sum(1 for p in payload if p["subs_gained"] is not None)
    print(f"[{today}] wrote {len(payload)} rows  ({got_subs} with subs, "
          f"total views {sum(p['views'] or 0 for p in payload):,})")


if __name__ == "__main__":
    main()
