"""
Fetch TikTok comments via Apify (clockworks/tiktok-comments-scraper).

Pulls comments from @codewithtyler videos, fetches replies too so we can tell
which ones the creator has already responded to, and writes everything the user
still needs to reply to into data/unreplied.json.

Usage:
  python3 apify_fetch.py                # default: 10 latest videos, 50 comments/video
  python3 apify_fetch.py --videos 20 --per 100
  python3 apify_fetch.py --all          # every video on the profile
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib import request
from urllib.error import HTTPError

SKILL_DIR = Path(__file__).parent
DATA_DIR = SKILL_DIR / "data"
ENV_FILE = Path.home() / ".claude" / ".env"
ALL_FILE = DATA_DIR / "all_comments.json"
UNREPLIED_FILE = DATA_DIR / "unreplied.json"

USERNAME = "codewithtyler"
ACTOR = "clockworks~tiktok-comments-scraper"  # tilde form for the API path


def load_env():
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def call_actor(token, payload):
    url = f"https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items?token={token}"
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, headers={"Content-Type": "application/json"})
    print(f"calling apify ({ACTOR})...")
    t0 = time.time()
    try:
        with request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read())
    except HTTPError as e:
        print(f"apify error {e.code}: {e.read().decode()[:500]}", file=sys.stderr)
        sys.exit(1)
    print(f"  done in {time.time() - t0:.1f}s, got {len(data)} comments")
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--videos", type=int, default=10, help="how many recent videos to scan")
    parser.add_argument("--per", type=int, default=50, help="comments per video")
    parser.add_argument("--all", action="store_true", help="scan every video on the profile (overrides --videos)")
    args = parser.parse_args()

    env = load_env()
    token = env.get("APIFY_API_TOKEN") or os.environ.get("APIFY_API_TOKEN")
    if not token:
        print("ERROR: APIFY_API_TOKEN not found in ~/.claude/.env", file=sys.stderr)
        sys.exit(1)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    payload = {
        "profiles": [USERNAME],
        "resultsPerPage": 200 if args.all else args.videos,
        "commentsPerPost": args.per,
        "profileSorting": "latest",
        "excludePinnedPosts": False,
        # Always pull replies so we can detect creator-replied threads
        "maxRepliesPerComment": 10,
    }

    raw = call_actor(token, payload)

    # Split top-level comments from replies
    top_level = [c for c in raw if c.get("repliesToId") is None]
    replies = [c for c in raw if c.get("repliesToId") is not None]

    # Build set of comment IDs the creator has replied to
    creator_replied_to = set()
    for r in replies:
        if r.get("uniqueId", "").lower() == USERNAME.lower():
            creator_replied_to.add(r["repliesToId"])

    # Annotate top-level comments
    cleaned = []
    for c in top_level:
        cid = c.get("cid")
        cleaned.append({
            "cid": cid,
            "author": c.get("uniqueId"),
            "text": c.get("text"),
            "likes": c.get("diggCount", 0),
            "reply_count": c.get("replyCommentTotal", 0),
            "liked_by_creator": c.get("likedByAuthor", False),
            "creator_replied": cid in creator_replied_to,
            "created_at": c.get("createTimeISO"),
            "video_url": c.get("videoWebUrl"),
        })

    # Sort newest first
    cleaned.sort(key=lambda c: c.get("created_at") or "", reverse=True)

    # The list the user still needs to reply to
    unreplied = [
        c for c in cleaned
        if not c["creator_replied"]
        and (c["author"] or "").lower() != USERNAME.lower()
    ]

    ALL_FILE.write_text(json.dumps(cleaned, indent=2, ensure_ascii=False))
    UNREPLIED_FILE.write_text(json.dumps(unreplied, indent=2, ensure_ascii=False))

    print(f"\n  total top-level comments: {len(cleaned)}")
    print(f"  already replied to      : {sum(1 for c in cleaned if c['creator_replied'])}")
    print(f"  needing your reply      : {len(unreplied)}")
    print(f"\n  all       -> {ALL_FILE}")
    print(f"  unreplied -> {UNREPLIED_FILE}")

    if unreplied:
        print("\n  unreplied comments (newest first):")
        for c in unreplied:
            snippet = (c["text"] or "").replace("\n", " ")[:100]
            marker = " 👍" if c["liked_by_creator"] else ""
            date = (c["created_at"] or "")[:10]
            print(f"    [{date}] @{c['author']}{marker}: {snippet}")


if __name__ == "__main__":
    main()
