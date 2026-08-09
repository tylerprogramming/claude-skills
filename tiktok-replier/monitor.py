"""
Hourly monitor: fetch TikTok comments, diff against last run, draft replies
for any NEW unreplied ones. Designed to run from cron.

What it does:
  1. Calls Apify clockworks/tiktok-comments-scraper for @codewithtyler
  2. Computes current unreplied-comment set
  3. Compares to data/last_unreplied.json (set of comment IDs from previous run)
  4. For each NEW unreplied comment: drafts a reply using keyword routing
  5. Appends new drafts to data/drafts.md (running log) and data/drafts_queue.json
  6. macOS desktop notification with the count of new items needing review
  7. Updates data/last_unreplied.json for next run

The user reviews data/drafts.md, edits if needed, then approves via:
    python3 reply.py --post --queue drafts_queue.json

Cron setup (every hour at :05 to avoid the top-of-hour scheduler crowd):
    5 * * * * /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 \\
      /Users/tylerreed/.claude/skills/tiktok-replier/monitor.py \\
      >> /Users/tylerreed/.claude/skills/tiktok-replier/data/monitor.log 2>&1

Tune --videos and --per below as your account grows.
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib import request
from urllib.error import HTTPError

SKILL_DIR = Path(__file__).parent
DATA_DIR = SKILL_DIR / "data"
ENV_FILE = Path.home() / ".claude" / ".env"
LAST_FILE = DATA_DIR / "last_unreplied.json"   # set of cids seen previously
DRAFTS_MD = DATA_DIR / "drafts.md"             # human-readable running log
DRAFTS_QUEUE = DATA_DIR / "drafts_queue.json"  # auto-drafted (keyword) ready to post
INBOX_FILE = DATA_DIR / "inbox.json"           # comments needing manual review (full metadata)
POSTED_FILE = DATA_DIR / "posted.json"         # already-posted (from reply.py)

USERNAME = "codewithtyler"
ACTOR = "clockworks~tiktok-comments-scraper"
SCAN_VIDEOS = 30
PER_VIDEO = 20

# Keyword → reply mapping for the standard CTA replies.
# Add to this as new CTAs come up in your videos.
SKOOL_LINK_REPLY = (
    "https://www.skool.com/the-ai-agency is the link! "
    "It is in the Social Media Classroom (free of course!)"
)
KEYWORD_REPLIES = {
    "system": SKOOL_LINK_REPLY,
    "plan": SKOOL_LINK_REPLY,
    "skill": SKOOL_LINK_REPLY,
    "email": SKOOL_LINK_REPLY,
    "routine": SKOOL_LINK_REPLY,
    "tools": SKOOL_LINK_REPLY,
    "vfx": SKOOL_LINK_REPLY,
    "schedule": SKOOL_LINK_REPLY,
    "video": SKOOL_LINK_REPLY,
    "workflow": SKOOL_LINK_REPLY,
}


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


def call_apify(token):
    payload = {
        "profiles": [USERNAME],
        "resultsPerPage": SCAN_VIDEOS,
        "commentsPerPost": PER_VIDEO,
        "profileSorting": "latest",
        "excludePinnedPosts": False,
        "maxRepliesPerComment": 10,
    }
    url = f"https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items?token={token}"
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read())
    except HTTPError as e:
        print(f"apify error {e.code}: {e.read().decode()[:300]}", file=sys.stderr)
        sys.exit(1)


def derive_unreplied(raw):
    """Filter raw comments to those still needing a reply."""
    top_level = [c for c in raw if c.get("repliesToId") is None]
    replies = [c for c in raw if c.get("repliesToId") is not None]

    creator_replied_to = {
        r["repliesToId"]
        for r in replies
        if r.get("uniqueId", "").lower() == USERNAME.lower()
    }

    unreplied = []
    for c in top_level:
        cid = c.get("cid")
        author = c.get("uniqueId", "")
        if cid in creator_replied_to:
            continue
        if author.lower() == USERNAME.lower():
            continue
        unreplied.append({
            "cid": cid,
            "author": author,
            "text": c.get("text", ""),
            "likes": c.get("diggCount", 0),
            "created_at": c.get("createTimeISO"),
            "video_url": c.get("videoWebUrl"),
        })
    return unreplied


def draft_reply_for(comment):
    """Return (draft_text, source). Auto-drafts only short keyword-CTA comments."""
    raw_text = comment.get("text") or ""
    # Long substantive comments are ALWAYS manual — don't auto-draft Skool link
    # to a multi-sentence critique just because it happens to contain "system"
    if len(raw_text) > 60:
        return None, "manual:long-comment"

    text = raw_text.strip().lower()
    cleaned = re.sub(r"[^a-z0-9 ]+", " ", text).strip()
    words = set(cleaned.split())

    for kw, reply in KEYWORD_REPLIES.items():
        if kw in words:
            return reply, f"keyword:{kw}"

    return None, "manual:no-keyword-match"


def notify_mac(title, message):
    """Show a macOS desktop notification."""
    try:
        subprocess.run(
            [
                "osascript",
                "-e",
                f'display notification "{message}" with title "{title}"',
            ],
            check=False,
            timeout=5,
        )
    except Exception:
        pass


def append_drafts_md(new_drafts):
    """Append new drafts to the running drafts.md log."""
    DRAFTS_MD.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat(timespec="minutes")
    chunks = [f"\n## {timestamp} — {len(new_drafts)} new\n"]
    for d in new_drafts:
        snippet = (d["text"] or "").replace("\n", " ")[:140]
        date = (d.get("created_at") or "")[:10]
        chunks.append(f"\n### [{date}] @{d['author']} — {d['source']}\n")
        chunks.append(f"> {snippet}\n")
        if d["draft"]:
            chunks.append(f"\n**Draft reply:** {d['draft']}\n")
        else:
            chunks.append(f"\n**Draft reply:** _(needs manual)_ \n")
        chunks.append(f"\n[video]({d['video_url']}) | cid: `{d['cid']}`\n")
    with open(DRAFTS_MD, "a", encoding="utf-8") as f:
        f.write("".join(chunks))


def main():
    env = load_env()
    token = env.get("APIFY_API_TOKEN") or os.environ.get("APIFY_API_TOKEN")
    if not token:
        print("ERROR: APIFY_API_TOKEN not in ~/.claude/.env", file=sys.stderr)
        sys.exit(1)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Load previous state
    previous_seen = set()
    if LAST_FILE.exists():
        try:
            previous_seen = set(json.loads(LAST_FILE.read_text()))
        except Exception:
            previous_seen = set()

    posted = set()
    if POSTED_FILE.exists():
        try:
            posted = set(json.loads(POSTED_FILE.read_text()))
        except Exception:
            posted = set()

    print(f"[{datetime.now().isoformat(timespec='seconds')}] fetching...")
    t0 = time.time()
    raw = call_apify(token)
    print(f"  apify returned {len(raw)} items in {time.time()-t0:.1f}s")

    unreplied = derive_unreplied(raw)
    current_ids = {c["cid"] for c in unreplied if c["cid"]}

    # NEW = current unreplied that we haven't seen before AND we haven't posted to
    new_unreplied = [
        c for c in unreplied
        if c["cid"] not in previous_seen and c["cid"] not in posted
    ]

    print(f"  current unreplied: {len(unreplied)}")
    print(f"  previously seen  : {len(previous_seen)}")
    print(f"  NEW this run     : {len(new_unreplied)}")

    if not new_unreplied:
        # Still update last-seen so we don't re-flag old ones if they get edited
        LAST_FILE.write_text(json.dumps(sorted(current_ids)))
        print("  no new comments; nothing to do.")
        return

    # Draft replies for new ones
    drafted = []
    auto_queue = []  # ones with confident keyword draft (ready to post)
    inbox = []       # ones needing manual review (Claude will help draft)

    # Carry over existing inbox so older items aren't dropped
    if INBOX_FILE.exists():
        try:
            inbox = json.loads(INBOX_FILE.read_text())
        except Exception:
            inbox = []
    inbox_cids = {item["cid"] for item in inbox}

    for c in new_unreplied:
        draft, source = draft_reply_for(c)
        d = {**c, "draft": draft, "source": source}
        drafted.append(d)
        if draft:
            auto_queue.append({
                "cid": c["cid"],
                "author": c["author"],
                "comment_text": c["text"],
                "video_url": c["video_url"],
                "reply_text": draft,
                "source": source,
            })
        else:
            # Needs manual reply; add to inbox unless already there
            if c["cid"] not in inbox_cids:
                inbox.append({
                    "cid": c["cid"],
                    "author": c["author"],
                    "text": c["text"],
                    "likes": c.get("likes", 0),
                    "video_url": c["video_url"],
                    "created_at": c["created_at"],
                    "source": source,  # 'manual:long-comment' or 'manual:no-keyword-match'
                    "first_seen": datetime.now().isoformat(timespec="seconds"),
                })

    append_drafts_md(drafted)

    # Persist queue files
    DRAFTS_QUEUE.write_text(json.dumps(auto_queue, indent=2, ensure_ascii=False))
    INBOX_FILE.write_text(json.dumps(inbox, indent=2, ensure_ascii=False))

    auto_n = len(auto_queue)
    manual_n = len(drafted) - auto_n
    inbox_n = len(inbox)
    notify_mac(
        "TikTok: new comments",
        f"{len(drafted)} new ({auto_n} auto-drafted, {manual_n} need you, {inbox_n} pending)",
    )

    print(f"\n  drafted     : {auto_n} auto + {manual_n} manual")
    print(f"  inbox total : {inbox_n} (including older unresolved)")
    print(f"  drafts log    -> {DRAFTS_MD}")
    print(f"  auto-queue    -> {DRAFTS_QUEUE}")
    print(f"  inbox (manual)-> {INBOX_FILE}")

    # Update last-seen for next run (everything we just processed)
    LAST_FILE.write_text(json.dumps(sorted(current_ids)))


if __name__ == "__main__":
    main()
