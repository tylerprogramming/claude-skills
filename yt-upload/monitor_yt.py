"""
Hourly YouTube comment monitor.

Uses the official YouTube Data API v3 (via the same OAuth token as yt.py).
Free under quota. Each cron run uses ~30-60 quota units (daily limit: 10,000).

What it does:
  1. Fetches your recent uploads (default 30)
  2. For each, fetches commentThreads + replies
  3. Identifies unreplied top-level comments (you haven't replied)
  4. Diffs against data/last_seen_yt.json
  5. Splits new ones into:
       - data/inbox_yt.json     (manual reply needed - Claude will draft)
       - data/drafts_queue_yt.json  (auto-drafted Skool-link replies for keyword CTAs)
  6. macOS notification with the count
  7. Updates data/last_seen_yt.json for next run

Cron setup (every hour at :07 to space out from the TikTok one):
    7 * * * * /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 \\
      /Users/tylerreed/.claude/skills/yt-upload/monitor_yt.py \\
      >> /Users/tylerreed/.claude/skills/yt-upload/data/monitor_yt.log 2>&1
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Reuse the auth from yt.py (lives next to this script)
SKILL_DIR = Path(__file__).parent
sys.path.insert(0, str(SKILL_DIR))
from yt import get_service  # noqa: E402

DATA_DIR = SKILL_DIR / "data"
LAST_FILE = DATA_DIR / "last_seen_yt.json"
INBOX_FILE = DATA_DIR / "inbox_yt.json"
DRAFTS_QUEUE = DATA_DIR / "drafts_queue_yt.json"
DRAFTS_MD = DATA_DIR / "drafts_yt.md"
POSTED_FILE = DATA_DIR / "posted_yt.json"
CHANNEL_ID_FILE = DATA_DIR / "channel_id.json"

SCAN_VIDEOS = 30           # how many recent uploads to scan
COMMENTS_PER_VIDEO = 50    # max top-level comments per video

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


def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def get_my_channel_id(yt):
    cached = load_json(CHANNEL_ID_FILE, None)
    if cached:
        return cached
    resp = yt.channels().list(part="id", mine=True).execute()
    items = resp.get("items", [])
    if not items:
        sys.exit("no channel found for authenticated user")
    cid = items[0]["id"]
    CHANNEL_ID_FILE.write_text(json.dumps({"channel_id": cid, "saved_at": datetime.now().isoformat()}))
    return {"channel_id": cid}


def get_recent_videos(yt, n):
    ch = yt.channels().list(part="contentDetails", mine=True).execute()
    if not ch.get("items"):
        return []
    uploads = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    pl = yt.playlistItems().list(
        part="snippet,contentDetails", playlistId=uploads, maxResults=min(n, 50)
    ).execute()
    return [
        {
            "video_id": it["contentDetails"]["videoId"],
            "title": it["snippet"]["title"],
            "url": f"https://youtube.com/watch?v={it['contentDetails']['videoId']}",
        }
        for it in pl.get("items", [])
    ]


def fetch_unreplied_for_video(yt, video, my_channel_id):
    """Return list of unreplied top-level comments on this video."""
    try:
        resp = yt.commentThreads().list(
            part="snippet,replies",
            videoId=video["video_id"],
            maxResults=COMMENTS_PER_VIDEO,
            order="time",
            textFormat="plainText",
        ).execute()
    except Exception as e:
        print(f"  WARN fetching {video['video_id']}: {e}", file=sys.stderr)
        return []

    unreplied = []
    for thread in resp.get("items", []):
        top = thread["snippet"]["topLevelComment"]
        author_channel = top["snippet"].get("authorChannelId", {}).get("value", "")
        if author_channel == my_channel_id:
            continue  # skip my own top-level comments

        # Did I reply in this thread?
        creator_replied = False
        for reply in (thread.get("replies", {}) or {}).get("comments", []):
            if reply["snippet"].get("authorChannelId", {}).get("value", "") == my_channel_id:
                creator_replied = True
                break
        if creator_replied:
            continue

        unreplied.append({
            "cid": top["id"],
            "author": top["snippet"].get("authorDisplayName", ""),
            "author_channel": author_channel,
            "text": top["snippet"].get("textDisplay", "")
                    or top["snippet"].get("textOriginal", ""),
            "likes": top["snippet"].get("likeCount", 0),
            "created_at": top["snippet"].get("publishedAt"),
            "video_id": video["video_id"],
            "video_title": video["title"],
            "video_url": video["url"],
        })
    return unreplied


def draft_reply_for(comment):
    """Long comments → manual. Short keyword CTAs → auto-draft."""
    text = (comment.get("text") or "").strip()
    if len(text) > 60:
        return None, "manual:long-comment"
    cleaned = re.sub(r"[^a-z0-9 ]+", " ", text.lower()).strip()
    words = set(cleaned.split())
    for kw, reply in KEYWORD_REPLIES.items():
        if kw in words:
            return reply, f"keyword:{kw}"
    return None, "manual:no-keyword-match"


def notify_mac(title, message):
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{message}" with title "{title}" sound name "Glass"'],
            check=False, timeout=5,
        )
    except Exception:
        pass


def append_drafts_md(new_drafts):
    DRAFTS_MD.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat(timespec="minutes")
    chunks = [f"\n## {timestamp} — {len(new_drafts)} new\n"]
    for d in new_drafts:
        snippet = (d["text"] or "").replace("\n", " ")[:140]
        date = (d.get("created_at") or "")[:10]
        chunks.append(f"\n### [{date}] @{d['author']} — {d['source']}\n")
        chunks.append(f"> {snippet}\n")
        chunks.append(f"\n**Draft reply:** {d['draft'] or '_(needs manual)_'}\n")
        chunks.append(f"\n[video]({d['video_url']}) — \"{d.get('video_title','')[:60]}\" | cid: `{d['cid']}`\n")
    with open(DRAFTS_MD, "a", encoding="utf-8") as f:
        f.write("".join(chunks))


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    yt = get_service()

    my_ch = get_my_channel_id(yt)
    my_channel_id = my_ch["channel_id"] if isinstance(my_ch, dict) else my_ch

    previous_seen = set(load_json(LAST_FILE, []))
    posted = set(load_json(POSTED_FILE, []))

    print(f"[{datetime.now().isoformat(timespec='seconds')}] fetching...")
    t0 = time.time()
    videos = get_recent_videos(yt, SCAN_VIDEOS)
    print(f"  {len(videos)} recent videos found")

    all_unreplied = []
    for v in videos:
        all_unreplied.extend(fetch_unreplied_for_video(yt, v, my_channel_id))
    print(f"  total unreplied: {len(all_unreplied)} (fetch took {time.time()-t0:.1f}s)")

    current_ids = {c["cid"] for c in all_unreplied if c["cid"]}
    new_unreplied = [
        c for c in all_unreplied
        if c["cid"] not in previous_seen and c["cid"] not in posted
    ]
    print(f"  NEW this run: {len(new_unreplied)}")

    if not new_unreplied:
        LAST_FILE.write_text(json.dumps(sorted(current_ids)))
        print("  no new comments; nothing to do.")
        return

    # Carry over inbox
    inbox = load_json(INBOX_FILE, [])
    inbox_cids = {item["cid"] for item in inbox}

    drafted = []
    auto_queue = []
    for c in new_unreplied:
        draft, source = draft_reply_for(c)
        d = {**c, "draft": draft, "source": source}
        drafted.append(d)
        if draft:
            auto_queue.append({
                "cid": c["cid"],
                "author": c["author"],
                "comment_text": c["text"],
                "video_id": c["video_id"],
                "video_url": c["video_url"],
                "reply_text": draft,
                "source": source,
            })
        else:
            if c["cid"] not in inbox_cids:
                inbox.append({
                    "cid": c["cid"],
                    "author": c["author"],
                    "text": c["text"],
                    "likes": c.get("likes", 0),
                    "video_id": c["video_id"],
                    "video_title": c["video_title"],
                    "video_url": c["video_url"],
                    "created_at": c["created_at"],
                    "source": source,
                    "first_seen": datetime.now().isoformat(timespec="seconds"),
                })

    append_drafts_md(drafted)

    # Merge into existing auto-queue (don't clobber unposted entries)
    existing_queue = load_json(DRAFTS_QUEUE, [])
    existing_cids = {q["cid"] for q in existing_queue}
    merged_queue = existing_queue + [q for q in auto_queue if q["cid"] not in existing_cids]
    DRAFTS_QUEUE.write_text(json.dumps(merged_queue, indent=2, ensure_ascii=False))

    INBOX_FILE.write_text(json.dumps(inbox, indent=2, ensure_ascii=False))
    LAST_FILE.write_text(json.dumps(sorted(current_ids)))

    auto_n = len(auto_queue)
    manual_n = len(drafted) - auto_n
    notify_mac(
        "YouTube: new comments",
        f"{len(drafted)} new ({auto_n} auto-drafted, {manual_n} need you, {len(inbox)} pending)",
    )

    print(f"\n  drafted     : {auto_n} auto + {manual_n} manual")
    print(f"  inbox total : {len(inbox)}")
    print(f"  drafts log    -> {DRAFTS_MD}")
    print(f"  auto-queue    -> {DRAFTS_QUEUE}")
    print(f"  inbox (manual)-> {INBOX_FILE}")


if __name__ == "__main__":
    main()
