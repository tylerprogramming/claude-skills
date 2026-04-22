#!/usr/bin/env python3
"""Search YouTube via yt-dlp and output a markdown report of top videos."""

import argparse
import json
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path


def search_youtube(keywords, search_count=50, days=30, top_n=15):
    query = " ".join(keywords)
    # Quote multi-word queries for phrase matching instead of loose keyword matching
    quoted_query = f'"{query}"' if len(keywords) > 1 else query
    search_term = f"ytsearchdate{search_count}:{quoted_query}"

    print(f"Searching YouTube for: {query}")
    print(f"Fetching {search_count} most recent results...")

    result = subprocess.run(
        ["yt-dlp", search_term, "-j", "--no-download"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0 and not result.stdout:
        print(f"Error: yt-dlp failed\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
    videos = []

    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        try:
            d = json.loads(line)
            upload = d.get("upload_date", "00000000") or "00000000"
            if upload >= cutoff:
                videos.append({
                    "title": d.get("title", "N/A"),
                    "channel": d.get("channel", "N/A"),
                    "views": d.get("view_count", 0) or 0,
                    "likes": d.get("like_count", 0) or 0,
                    "comments": d.get("comment_count", 0) or 0,
                    "upload_date": upload,
                    "duration": d.get("duration_string", "N/A"),
                    "url": f"https://youtube.com/watch?v={d.get('id')}",
                    "description": (d.get("description", "") or "")[:300],
                    "id": d.get("id"),
                })
        except json.JSONDecodeError:
            continue

    # Filter to videos whose title contains at least one keyword (relevance check)
    kw_lower = [k.lower() for k in keywords]
    relevant = [v for v in videos if any(k in v["title"].lower() for k in kw_lower)]
    # Fall back to unfiltered if relevance filter removes everything
    if relevant:
        videos = relevant

    videos.sort(key=lambda x: x["views"], reverse=True)
    top_videos = videos[:top_n]

    print(f"Found {len(videos)} relevant videos in last {days} days. Returning top {min(top_n, len(videos))}.")

    return {
        "query": query,
        "total_found": len(videos),
        "days": days,
        "top_n": top_n,
        "videos": top_videos,
    }


def generate_markdown(data):
    today = datetime.now().strftime("%Y-%m-%d")
    query = data["query"]
    lines = [
        f"# YouTube Search: \"{query}\"",
        f"",
        f"**Date:** {today}",
        f"**Search query:** {query}",
        f"**Videos found (last {data['days']} days):** {data['total_found']}",
        f"**Showing:** Top {min(data['top_n'], len(data['videos']))} by views",
        f"",
        f"---",
        f"",
    ]

    # Summary table
    lines.append("## Top Videos\n")
    lines.append("| # | Title | Channel | Views | Likes | Comments | Duration | Uploaded |")
    lines.append("|---|-------|---------|------:|------:|---------:|----------|----------|")

    for i, v in enumerate(data["videos"], 1):
        date_fmt = f"{v['upload_date'][:4]}-{v['upload_date'][4:6]}-{v['upload_date'][6:]}"
        title_link = f"[{v['title']}]({v['url']})"
        lines.append(
            f"| {i} | {title_link} | {v['channel']} | {v['views']:,} | {v['likes']:,} | {v['comments']:,} | {v['duration']} | {date_fmt} |"
        )

    lines.append("")

    # Detailed breakdown
    lines.append("## Video Details\n")
    for i, v in enumerate(data["videos"], 1):
        date_fmt = f"{v['upload_date'][:4]}-{v['upload_date'][4:6]}-{v['upload_date'][6:]}"
        lines.append(f"### {i}. {v['title']}\n")
        lines.append(f"- **Channel:** {v['channel']}")
        lines.append(f"- **Views:** {v['views']:,}")
        lines.append(f"- **Likes:** {v['likes']:,}")
        lines.append(f"- **Comments:** {v['comments']:,}")
        lines.append(f"- **Duration:** {v['duration']}")
        lines.append(f"- **Uploaded:** {date_fmt}")
        lines.append(f"- **URL:** {v['url']}")
        lines.append(f"- **Description:** {v['description']}...")
        lines.append("")

    return "\n".join(lines)


def download_thumbnails(videos, thumb_dir: Path):
    """Download thumbnails directly from YouTube's CDN (fast, no yt-dlp needed)."""
    thumb_dir.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    for i, video in enumerate(videos, 1):
        video_id = video.get("id")
        if not video_id:
            continue
        out_path = thumb_dir / f"{i:02d}-{video_id}.jpg"
        # Try HD first, fall back to HQ
        for quality in ["maxresdefault", "hqdefault"]:
            url = f"https://i.ytimg.com/vi/{video_id}/{quality}.jpg"
            try:
                urllib.request.urlretrieve(url, out_path)
                # maxresdefault returns a small placeholder if unavailable — check file size
                if out_path.stat().st_size > 5000:
                    downloaded += 1
                    break
            except Exception:
                continue
    print(f"Downloaded {downloaded}/{len(videos)} thumbnails to {thumb_dir}")
    return downloaded


def main():
    parser = argparse.ArgumentParser(description="Search YouTube via yt-dlp")
    parser.add_argument("keywords", nargs="+", help="Search keywords")
    parser.add_argument("--search-count", type=int, default=50, help="Number of results to fetch from YouTube (default: 50)")
    parser.add_argument("--days", type=int, default=30, help="Only include videos from the last N days (default: 30)")
    parser.add_argument("--top", type=int, default=15, help="Number of top videos to include (default: 15)")
    parser.add_argument("--output-dir", type=str, default=str(Path.home() / "yt-research"), help="Output directory")
    parser.add_argument("--json", action="store_true", help="Also save raw JSON data")
    parser.add_argument("--no-thumbnails", action="store_true", help="Skip thumbnail downloading")
    args = parser.parse_args()

    data = search_youtube(args.keywords, args.search_count, args.days, args.top)
    markdown = generate_markdown(data)

    today = datetime.now().strftime("%Y-%m-%d")
    slug = "-".join(args.keywords).lower().replace(" ", "-")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    md_path = output_dir / f"{today}-{slug}.md"
    md_path.write_text(markdown)
    print(f"\nReport saved: {md_path}")

    if args.json:
        json_path = output_dir / f"{today}-{slug}.json"
        json_path.write_text(json.dumps(data, indent=2))
        print(f"Raw JSON saved: {json_path}")

    # Download thumbnails by default unless --no-thumbnails
    if not args.no_thumbnails and data["videos"]:
        thumb_dir = output_dir / f"{today}-{slug}-thumbnails"
        download_thumbnails(data["videos"], thumb_dir)

    print(f"\n{markdown}")


if __name__ == "__main__":
    main()
