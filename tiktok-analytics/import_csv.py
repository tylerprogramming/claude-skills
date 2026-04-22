#!/usr/bin/env python3
"""
Import TikTok CSV exports into the analytics database.

Supports two CSV formats:
  1. Overview CSV - daily account-level stats (Video Views, Profile Views, Likes, Comments, Shares)
  2. Content CSV - per-video stats (Video title, Video link, Post time, Total likes/comments/shares/views)

Usage:
  python3 import_csv.py overview /path/to/Overview.csv
  python3 import_csv.py content /path/to/Content.csv [--year 2026]
"""

import csv
import re
import sys
from datetime import datetime
from pathlib import Path

# Add parent dir for imports
sys.path.insert(0, str(Path(__file__).parent))
from tiktok_db import get_connection, init_all_tables, save_daily_overview, upsert_video, save_metrics


def parse_tiktok_date(date_str, year=None):
    """Parse TikTok's date format (e.g., 'April 6') into ISO format."""
    if not year:
        year = datetime.now().year

    # Try "Month Day" format
    try:
        dt = datetime.strptime(f"{date_str} {year}", "%B %d %Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # Try "YYYY-MM-DD" format
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    print(f"Warning: Could not parse date '{date_str}'")
    return None


def extract_video_id(url):
    """Extract the video ID from a TikTok URL."""
    match = re.search(r'/video/(\d+)', url)
    return match.group(1) if match else None


def import_overview(csv_path, year=None):
    """Import the Overview CSV (daily account stats)."""
    conn = get_connection()
    init_all_tables(conn)

    imported = 0
    skipped = 0

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_str = parse_tiktok_date(row.get("Date", "").strip(), year)
            if not date_str:
                skipped += 1
                continue

            save_daily_overview(
                conn,
                date_str=date_str,
                video_views=int(row.get("Video Views", 0) or 0),
                profile_views=int(row.get("Profile Views", 0) or 0),
                likes=int(row.get("Likes", 0) or 0),
                comments=int(row.get("Comments", 0) or 0),
                shares=int(row.get("Shares", 0) or 0),
            )
            imported += 1

    conn.close()
    print(f"Overview import complete: {imported} days imported, {skipped} skipped")


def import_content(csv_path, year=None):
    """Import the Content CSV (per-video stats)."""
    conn = get_connection()
    init_all_tables(conn)

    imported = 0
    skipped = 0
    today = datetime.now().strftime("%Y-%m-%d")

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get("Video link", "").strip()
            video_id = extract_video_id(url)
            if not video_id:
                skipped += 1
                continue

            posted_at = parse_tiktok_date(row.get("Post time", "").strip(), year)
            caption = row.get("Video title", "").strip()

            # Upsert the video
            upsert_video(
                conn,
                video_id=video_id,
                url=url,
                caption=caption,
                posted_at=posted_at,
            )

            # Save metrics snapshot
            save_metrics(
                conn,
                video_id=video_id,
                views=int(row.get("Total views", 0) or 0),
                likes=int(row.get("Total likes", 0) or 0),
                comments=int(row.get("Total comments", 0) or 0),
                shares=int(row.get("Total shares", 0) or 0),
                saves=0,
                source="csv",
                snapshot_date=today,
            )
            imported += 1

    conn.close()
    print(f"Content import complete: {imported} videos imported, {skipped} skipped")


def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python3 import_csv.py overview /path/to/Overview.csv [--year 2026]")
        print("  python3 import_csv.py content /path/to/Content.csv [--year 2026]")
        sys.exit(1)

    mode = sys.argv[1]
    csv_path = sys.argv[2]

    # Parse optional --year
    year = None
    if "--year" in sys.argv:
        idx = sys.argv.index("--year")
        if idx + 1 < len(sys.argv):
            year = int(sys.argv[idx + 1])

    if not Path(csv_path).exists():
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)

    if mode == "overview":
        import_overview(csv_path, year)
    elif mode == "content":
        import_content(csv_path, year)
    else:
        print(f"Error: Unknown mode '{mode}'. Use 'overview' or 'content'.")
        sys.exit(1)


if __name__ == "__main__":
    main()
