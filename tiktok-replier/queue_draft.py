"""
Add a drafted reply to the post queue.

When you and Claude agree on a reply text for a comment in inbox.json:
  1. Claude removes the comment from inbox.json
  2. Claude appends a queue entry to replies_queue.json with the reply text
  3. You run reply.py --post --headless to publish

Usage:
  python3 queue_draft.py --cid <comment_id> --reply "your draft text"

The --cid must match an entry currently in data/inbox.json.
"""

import argparse
import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent
DATA_DIR = SKILL_DIR / "data"
INBOX_FILE = DATA_DIR / "inbox.json"
QUEUE_FILE = DATA_DIR / "replies_queue.json"


def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cid", required=True, help="comment id from inbox.json")
    p.add_argument("--reply", required=True, help="reply text to post")
    args = p.parse_args()

    inbox = load_json(INBOX_FILE, [])
    target = next((c for c in inbox if c["cid"] == args.cid), None)
    if not target:
        print(f"ERROR: cid {args.cid} not in inbox.json", file=sys.stderr)
        print(f"  inbox cids: {[c['cid'] for c in inbox]}", file=sys.stderr)
        sys.exit(1)

    queue_entry = {
        "cid": target["cid"],
        "author": target["author"],
        "comment_text": target["text"],
        "video_url": target["video_url"],
        "reply_text": args.reply,
        "source": "manual:claude-drafted",
    }

    queue = load_json(QUEUE_FILE, [])
    if any(q["cid"] == target["cid"] for q in queue):
        print(f"WARN: cid {target['cid']} already in queue, skipping append")
    else:
        queue.append(queue_entry)
        QUEUE_FILE.write_text(json.dumps(queue, indent=2, ensure_ascii=False))

    inbox = [c for c in inbox if c["cid"] != args.cid]
    INBOX_FILE.write_text(json.dumps(inbox, indent=2, ensure_ascii=False))

    print(f"queued reply to @{target['author']}")
    print(f"  comment: {target['text'][:80]!r}")
    print(f"  reply:   {args.reply[:80]!r}")
    print(f"  inbox now: {len(inbox)} pending")
    print(f"  queue now: {len(queue)} ready to post")
    print(f"\npost with: python3 reply.py --post --headless")


if __name__ == "__main__":
    main()
