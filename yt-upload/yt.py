#!/usr/bin/env python3
"""
YouTube Data API v3 CLI for Tyler's content workflow.

Subcommands:
  auth                          One-time OAuth setup. Opens browser, saves token.
  upload                        Upload a video with full metadata, thumbnail, scheduling.
  update <video_id>             Edit title, description, tags, category, privacy on existing video.
  thumbnail <video_id>          Replace the thumbnail on an existing video.
  comment <video_id>            Post a top-level comment on a video (or reply with --reply-to).
  list                          List my recent uploads.
  get <video_id>                Get full metadata for a single video.

OAuth:
  Reuses ~/credentials.json (same Google client as Drive/Gmail skills).
  Token stored at ~/.claude/skills/yt-upload/token.json.
  Required scopes: youtube.upload + youtube.force-ssl.
  First run will open a browser to authorize.

Tags:
  YouTube tags field is capped at 500 chars total. Pass via --tags-file (one tag per line)
  OR --tags "tag1,tag2,tag3". If over 500 chars, the script truncates from the end and warns.

Scheduling:
  Use --publish-at "2026-04-26T13:00:00-04:00" with --privacy private.
  YouTube auto-flips the video to public at that time.

Categories (most-used):
  22 = People & Blogs
  27 = Education
  28 = Science & Technology  (default for Tyler's tech tutorials)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# ---------- config ----------

SCOPES = [
    "https://www.googleapis.com/auth/yt-upload.upload",
    "https://www.googleapis.com/auth/yt-upload.force-ssl",
]
CREDS_PATH = os.path.expanduser("~/credentials.json")
TOKEN_PATH = os.path.expanduser("~/.claude/skills/yt-upload/token.json")
DEFAULT_CATEGORY_ID = "28"  # Science & Technology
TAGS_MAX_CHARS = 500


# ---------- auth ----------


def get_creds(force_reauth: bool = False) -> Credentials:
    creds = None
    if not force_reauth and os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token and not force_reauth:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Refresh failed ({e}), re-running browser auth.", file=sys.stderr)
                creds = None
        if not creds:
            if not os.path.exists(CREDS_PATH):
                sys.exit(
                    f"Missing OAuth client at {CREDS_PATH}. "
                    "Download it from Google Cloud Console and try again."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        Path(TOKEN_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return creds


def get_service():
    return build("youtube", "v3", credentials=get_creds(), cache_discovery=False)


# ---------- helpers ----------


def load_tags(args) -> list[str]:
    """Build tags list from --tags or --tags-file. Truncates if total > 500 chars."""
    tags: list[str] = []
    if args.tags_file:
        text = Path(args.tags_file).read_text()
        # Accept "tag1, tag2, tag3" or one tag per line
        if "\n" in text and "," not in text.split("\n")[0]:
            tags = [t.strip() for t in text.splitlines() if t.strip()]
        else:
            tags = [t.strip() for t in text.split(",") if t.strip()]
    elif args.tags:
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    if not tags:
        return tags

    # Trim to fit YouTube's 500-char field cap (commas count)
    out: list[str] = []
    running = 0
    for tag in tags:
        cost = len(tag) + (2 if out else 0)  # ", " separator
        if running + cost > TAGS_MAX_CHARS:
            print(
                f"warning: tags exceed {TAGS_MAX_CHARS} chars, dropped {len(tags) - len(out)}",
                file=sys.stderr,
            )
            break
        out.append(tag)
        running += cost
    return out


def load_description(args) -> str:
    if args.description_file:
        return Path(args.description_file).read_text()
    return args.description or ""


def progress_print(msg: str):
    print(msg, file=sys.stderr, flush=True)


# ---------- subcommands ----------


def cmd_auth(args):
    creds = get_creds(force_reauth=args.reauth)
    print(f"Authenticated. Token saved to {TOKEN_PATH}")
    print(f"Scopes: {', '.join(creds.scopes or SCOPES)}")


def cmd_upload(args):
    yt = get_service()

    body: dict = {
        "snippet": {
            "title": args.title,
            "description": load_description(args),
            "tags": load_tags(args),
            "categoryId": args.category or DEFAULT_CATEGORY_ID,
        },
        "status": {
            "privacyStatus": args.privacy,
            "selfDeclaredMadeForKids": args.made_for_kids,
            "embeddable": True,
            "publicStatsViewable": True,
        },
    }
    if args.publish_at:
        # Scheduled publish requires privacy=private
        if args.privacy != "private":
            progress_print(
                "note: scheduled publish requires privacy=private; auto-correcting"
            )
            body["status"]["privacyStatus"] = "private"
        body["status"]["publishAt"] = args.publish_at

    media = MediaFileUpload(
        args.video, mimetype="video/*", chunksize=10 * 1024 * 1024, resumable=True
    )

    progress_print(f"Uploading {args.video}...")
    request = yt.videos().insert(
        part="snippet,status", body=body, media_body=media, notifySubscribers=args.notify
    )

    response = None
    last_pct = -1
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            if pct != last_pct:
                progress_print(f"  upload {pct}%")
                last_pct = pct

    video_id = response["id"]
    progress_print(f"Uploaded. Video ID: {video_id}")
    progress_print(f"URL: https://youtube.com/watch?v={video_id}")

    if args.thumbnail:
        progress_print(f"Setting thumbnail {args.thumbnail}...")
        try:
            yt.thumbnails().set(
                videoId=video_id, media_body=MediaFileUpload(args.thumbnail)
            ).execute()
            progress_print("  thumbnail set")
        except HttpError as e:
            progress_print(f"  thumbnail failed: {e}")

    print(json.dumps({"video_id": video_id, "url": f"https://youtube.com/watch?v={video_id}"}))


def cmd_update(args):
    yt = get_service()
    # Fetch current snippet/status so we only overwrite what's specified
    current = yt.videos().list(part="snippet,status", id=args.video_id).execute()
    if not current.get("items"):
        sys.exit(f"video {args.video_id} not found or not owned by you")
    item = current["items"][0]
    snippet = item["snippet"]
    status = item["status"]

    if args.title is not None:
        snippet["title"] = args.title
    if args.description is not None or args.description_file is not None:
        snippet["description"] = load_description(args)
    if args.tags is not None or args.tags_file is not None:
        snippet["tags"] = load_tags(args)
    if args.category is not None:
        snippet["categoryId"] = args.category
    if args.privacy is not None:
        status["privacyStatus"] = args.privacy
    if args.publish_at is not None:
        status["publishAt"] = args.publish_at
        status["privacyStatus"] = "private"

    body = {"id": args.video_id, "snippet": snippet, "status": status}
    progress_print(f"Updating video {args.video_id}...")
    resp = yt.videos().update(part="snippet,status", body=body).execute()
    print(json.dumps({"video_id": resp["id"], "title": resp["snippet"]["title"]}))


def cmd_thumbnail(args):
    yt = get_service()
    progress_print(f"Setting thumbnail on {args.video_id}: {args.image}")
    resp = yt.thumbnails().set(
        videoId=args.video_id, media_body=MediaFileUpload(args.image)
    ).execute()
    print(json.dumps(resp))


def cmd_comment(args):
    yt = get_service()
    if args.reply_to:
        # Reply to a comment ID
        body = {
            "snippet": {"parentId": args.reply_to, "textOriginal": args.text},
        }
        progress_print(f"Replying to comment {args.reply_to}...")
        resp = yt.comments().insert(part="snippet", body=body).execute()
    else:
        # Top-level comment thread on a video
        body = {
            "snippet": {
                "videoId": args.video_id,
                "topLevelComment": {"snippet": {"textOriginal": args.text}},
            }
        }
        progress_print(f"Commenting on {args.video_id}...")
        resp = yt.commentThreads().insert(part="snippet", body=body).execute()
    print(json.dumps(resp.get("snippet", resp), indent=2))


def cmd_list(args):
    yt = get_service()
    # Get my channel's uploads playlist
    ch = yt.channels().list(part="contentDetails", mine=True).execute()
    if not ch.get("items"):
        sys.exit("no channel found for authenticated user")
    uploads = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    progress_print(f"Listing recent uploads (max {args.max})...")
    pl = yt.playlistItems().list(
        part="snippet,contentDetails", playlistId=uploads, maxResults=min(args.max, 50)
    ).execute()

    items = []
    for it in pl.get("items", []):
        items.append(
            {
                "video_id": it["contentDetails"]["videoId"],
                "title": it["snippet"]["title"],
                "published_at": it["contentDetails"].get("videoPublishedAt")
                or it["snippet"]["publishedAt"],
                "url": f"https://youtube.com/watch?v={it['contentDetails']['videoId']}",
            }
        )
    print(json.dumps(items, indent=2))


def cmd_get(args):
    yt = get_service()
    resp = yt.videos().list(
        part="snippet,status,contentDetails,statistics", id=args.video_id
    ).execute()
    if not resp.get("items"):
        sys.exit(f"video {args.video_id} not found")
    item = resp["items"][0]
    out = {
        "video_id": item["id"],
        "title": item["snippet"]["title"],
        "description": item["snippet"]["description"],
        "tags": item["snippet"].get("tags", []),
        "category_id": item["snippet"].get("categoryId"),
        "privacy_status": item["status"]["privacyStatus"],
        "publish_at": item["status"].get("publishAt"),
        "duration": item["contentDetails"]["duration"],
        "stats": item.get("statistics", {}),
        "url": f"https://youtube.com/watch?v={item['id']}",
    }
    print(json.dumps(out, indent=2))


# ---------- argparse ----------


def build_parser():
    p = argparse.ArgumentParser(prog="yt", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("auth", help="One-time OAuth setup")
    a.add_argument("--reauth", action="store_true", help="Force re-authorization")
    a.set_defaults(func=cmd_auth)

    u = sub.add_parser("upload", help="Upload a video")
    u.add_argument("--video", required=True, help="Path to .mp4 file")
    u.add_argument("--title", required=True, help="Video title (max 100 chars)")
    u.add_argument("--description", help="Description text (or use --description-file)")
    u.add_argument("--description-file", help="Path to a file containing the description")
    u.add_argument("--tags", help="Comma-separated tags")
    u.add_argument("--tags-file", help="Path to file with comma-separated or newline tags")
    u.add_argument("--category", help=f"YouTube category ID (default {DEFAULT_CATEGORY_ID})")
    u.add_argument("--thumbnail", help="Optional path to JPG/PNG thumbnail (max 2 MB)")
    u.add_argument(
        "--privacy",
        choices=["private", "unlisted", "public"],
        default="private",
        help="Privacy status (default: private — required when --publish-at is used)",
    )
    u.add_argument("--publish-at", help="ISO 8601 publish time, e.g. 2026-04-26T13:00:00-04:00")
    u.add_argument("--made-for-kids", action="store_true", help="Mark as made for kids")
    u.add_argument("--no-notify", dest="notify", action="store_false", help="Don't notify subscribers")
    u.add_argument("--notify", dest="notify", action="store_true", default=True)
    u.set_defaults(func=cmd_upload)

    upd = sub.add_parser("update", help="Edit metadata on an existing video")
    upd.add_argument("video_id")
    upd.add_argument("--title")
    upd.add_argument("--description")
    upd.add_argument("--description-file")
    upd.add_argument("--tags")
    upd.add_argument("--tags-file")
    upd.add_argument("--category")
    upd.add_argument("--privacy", choices=["private", "unlisted", "public"])
    upd.add_argument("--publish-at")
    upd.set_defaults(func=cmd_update)

    th = sub.add_parser("thumbnail", help="Replace the thumbnail on a video")
    th.add_argument("video_id")
    th.add_argument("--image", required=True, help="Path to JPG/PNG (max 2 MB)")
    th.set_defaults(func=cmd_thumbnail)

    c = sub.add_parser("comment", help="Comment on a video or reply to a comment")
    c.add_argument("video_id", nargs="?", help="Video ID for top-level comment")
    c.add_argument("--reply-to", help="Comment ID to reply to (replaces video_id)")
    c.add_argument("--text", required=True, help="Comment text")
    c.set_defaults(func=cmd_comment)

    ls = sub.add_parser("list", help="List my recent uploads")
    ls.add_argument("--max", type=int, default=10, help="Max results (default 10, max 50)")
    ls.set_defaults(func=cmd_list)

    g = sub.add_parser("get", help="Get metadata for a single video")
    g.add_argument("video_id")
    g.set_defaults(func=cmd_get)

    return p


def main():
    args = build_parser().parse_args()
    try:
        args.func(args)
    except HttpError as e:
        print(f"YouTube API error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
