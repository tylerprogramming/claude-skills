#!/usr/bin/env python3
"""
Scrape a TikTok profile's public video metrics using Apify.

Usage:
  python3 scrape_profile.py @codewithtyler
  python3 scrape_profile.py @codewithtyler --limit 50

Pulls all public video data (views, likes, comments, shares, saves, caption, date)
and saves to the tiktok analytics database.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# Add parent dir for imports
sys.path.insert(0, str(Path(__file__).parent))
from tiktok_db import get_connection, init_all_tables, upsert_video, save_metrics


def load_api_token():
    """Load Apify API token from ~/.claude/.env"""
    env_path = os.path.expanduser("~/.claude/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("APIFY_API_TOKEN="):
                    return line.split("=", 1)[1].strip()

    token = os.environ.get("APIFY_API_TOKEN")
    if token:
        return token

    print("Error: APIFY_API_TOKEN not found in ~/.claude/.env or environment.")
    sys.exit(1)


def api_request(url, token, method="GET", data=None):
    """Make an authenticated Apify API request."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"API Error {e.code}: {error_body}")
        sys.exit(1)


def scrape_profile(token, username, limit=100):
    """Scrape a TikTok profile using Apify."""
    actor = "clockworks~tiktok-scraper"
    url = f"https://api.apify.com/v2/acts/{actor}/runs"

    # Clean username
    username = username.lstrip("@")

    input_data = {
        "profiles": [username],
        "resultsPerPage": limit,
        "shouldDownloadCovers": False,
        "shouldDownloadSlideshowImages": False,
        "shouldDownloadSubtitles": False,
        "shouldDownloadVideos": False,
    }

    print(f"Scraping @{username} profile (limit: {limit} videos)...")

    result = api_request(url, token, method="POST", data=input_data)
    run_id = result["data"]["id"]
    dataset_id = result["data"]["defaultDatasetId"]
    print(f"Run started: {run_id}")

    # Poll for completion
    poll_url = f"https://api.apify.com/v2/actor-runs/{run_id}"
    while True:
        run_data = api_request(poll_url, token)
        status = run_data["data"]["status"]
        sys.stdout.write(f"\rStatus: {status}   ")
        sys.stdout.flush()

        if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            print()
            break
        time.sleep(10)

    if status != "SUCCEEDED":
        print(f"Error: Run ended with status {status}")
        cost = run_data["data"].get("usageTotalUsd", 0)
        print(f"Cost: ${cost:.4f}")
        sys.exit(1)

    cost = run_data["data"].get("usageTotalUsd", 0)
    print(f"Run succeeded. Cost: ${cost:.4f}")

    # Fetch results
    print("Fetching results...")
    items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?format=json"
    items = api_request(items_url, token)
    print(f"Got {len(items)} videos")
    return items, cost


def save_to_db(videos):
    """Save scraped videos to the database."""
    conn = get_connection()
    init_all_tables(conn)
    today = datetime.now().strftime("%Y-%m-%d")

    saved = 0
    for v in videos:
        video_id = v.get("id")
        if not video_id:
            continue

        url = v.get("webVideoUrl", "")
        caption = (v.get("text") or "").strip()
        posted_at = (v.get("createTimeISO") or "")[:10]
        duration = v.get("videoMeta", {}).get("duration", 0)

        upsert_video(conn, video_id, url=url, caption=caption,
                     posted_at=posted_at, duration_seconds=duration)

        save_metrics(
            conn,
            video_id=video_id,
            views=v.get("playCount", 0) or 0,
            likes=v.get("diggCount", 0) or 0,
            comments=v.get("commentCount", 0) or 0,
            shares=v.get("shareCount", 0) or 0,
            saves=v.get("collectCount", 0) or 0,
            source="apify",
            snapshot_date=today,
        )
        saved += 1

    conn.close()
    return saved


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scrape_profile.py @username [--limit 50]")
        sys.exit(1)

    username = sys.argv[1]
    limit = 100

    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])

    token = load_api_token()
    videos, cost = scrape_profile(token, username, limit)

    if not videos:
        print("No videos found.")
        sys.exit(0)

    saved = save_to_db(videos)
    print(f"\nSaved {saved} videos to database")

    # Print top 10 by views
    videos.sort(key=lambda x: x.get("playCount", 0) or 0, reverse=True)
    print(f"\nTop 10 by views:")
    print(f"{'Views':>10} {'Likes':>8} {'Comments':>8} {'Shares':>8} {'Caption'}")
    print("-" * 80)
    for v in videos[:10]:
        views = v.get("playCount", 0) or 0
        likes = v.get("diggCount", 0) or 0
        comments = v.get("commentCount", 0) or 0
        shares = v.get("shareCount", 0) or 0
        caption = (v.get("text") or "")[:45]
        print(f"{views:>10,} {likes:>8,} {comments:>8,} {shares:>8,} {caption}")


if __name__ == "__main__":
    main()
