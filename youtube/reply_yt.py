"""
Post YouTube replies from a queue file. Uses the official YouTube API
(reuses get_service from yt.py). Tracks posted ids in data/posted_yt.json.

Usage:
  python3 reply_yt.py                 # dry-run on default queue
  python3 reply_yt.py --post          # publish all in default queue
  python3 reply_yt.py --post --limit 1
  python3 reply_yt.py --post --queue ~/.claude/skills/youtube/data/drafts_queue_yt.json
"""

import argparse
import json
import sys
import time
from pathlib import Path

SKILL_DIR = Path(__file__).parent
sys.path.insert(0, str(SKILL_DIR))
from yt import get_service  # noqa: E402

DATA_DIR = SKILL_DIR / "data"
DEFAULT_QUEUE = DATA_DIR / "drafts_queue_yt.json"
POSTED_FILE = DATA_DIR / "posted_yt.json"

DELAY_BETWEEN_POSTS_S = 10  # YouTube is more lenient than TikTok; 10s is plenty


def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def post_reply(yt, parent_id, text):
    body = {"snippet": {"parentId": parent_id, "textOriginal": text}}
    return yt.comments().insert(part="snippet", body=body).execute()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--post", action="store_true", help="actually publish (default: dry-run)")
    p.add_argument("--limit", type=int, default=0, help="only process first N items")
    p.add_argument("--queue", type=str, default=None,
                   help=f"queue JSON path (default: {DEFAULT_QUEUE})")
    args = p.parse_args()

    queue_file = Path(args.queue) if args.queue else DEFAULT_QUEUE
    if not queue_file.exists():
        print(f"queue file not found: {queue_file}")
        sys.exit(1)

    queue = load_json(queue_file, [])
    posted = set(load_json(POSTED_FILE, []))
    queue = [q for q in queue if q["cid"] not in posted]
    if args.limit > 0:
        queue = queue[: args.limit]

    print(f"queue file : {queue_file}")
    print(f"queue size : {len(queue)}")
    print(f"mode       : {'POST (live)' if args.post else 'DRY-RUN'}")
    if not queue:
        print("nothing to do.")
        return

    yt = get_service() if args.post else None

    for i, item in enumerate(queue, start=1):
        snippet = (item.get("comment_text") or "").replace("\n", " ")[:80]
        print(f"\n[{i}/{len(queue)}] @{item['author']}: {snippet!r}")
        print(f"    reply: {item['reply_text'][:100]!r}")

        if not args.post:
            print("    [DRY-RUN] not posted")
            continue

        try:
            resp = post_reply(yt, item["cid"], item["reply_text"])
            new_id = resp.get("id", "?")
            print(f"    POSTED ✓ (reply id: {new_id})")
            posted.add(item["cid"])
            POSTED_FILE.write_text(json.dumps(sorted(posted), indent=2))
        except Exception as e:
            print(f"    ERROR: {e}")
            continue

        if i < len(queue):
            time.sleep(DELAY_BETWEEN_POSTS_S)

    print(f"\ndone. {len(posted)} total posted (cumulative).")


if __name__ == "__main__":
    main()
