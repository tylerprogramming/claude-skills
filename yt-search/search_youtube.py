#!/usr/bin/env python3
"""Search YouTube via yt-dlp and output a markdown report of top videos.

Results are split into two ranked sections — long-form and Shorts — because
the research feeds two different tracks (long-form planning via /yt-package, short-form
scripts via /shorts) and the two formats are not comparable head to head.
"""

import argparse
import json
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

# A video is treated as a Short if its duration is at or below this many seconds.
# 60s is the classic Shorts cap; YouTube now allows up to ~3 min, so bump
# --short-max to 180 if you want the longer Shorts pulled into the Shorts bucket.
DEFAULT_SHORT_MAX = 60


def search_youtube(keywords, search_count=50, days=30, top_n=15, short_max=DEFAULT_SHORT_MAX):
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
                    "duration_seconds": d.get("duration") or 0,
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

    # Split into Shorts vs long-form. A known, non-zero duration at or under the
    # threshold is a Short; everything else (including unknown durations and
    # live streams) is treated as long-form so we never hide a real video.
    shorts = [v for v in videos if 0 < v["duration_seconds"] <= short_max]
    long_form = [v for v in videos if not (0 < v["duration_seconds"] <= short_max)]

    shorts.sort(key=lambda x: x["views"], reverse=True)
    long_form.sort(key=lambda x: x["views"], reverse=True)

    top_long = long_form[:top_n]
    top_shorts = shorts[:top_n]

    print(
        f"Found {len(videos)} relevant videos in last {days} days "
        f"({len(long_form)} long-form, {len(shorts)} Shorts). "
        f"Returning top {len(top_long)} long-form and top {len(top_shorts)} Shorts."
    )

    return {
        "query": query,
        "total_found": len(videos),
        "long_form_found": len(long_form),
        "shorts_found": len(shorts),
        "days": days,
        "top_n": top_n,
        "short_max": short_max,
        "long_form": top_long,
        "shorts": top_shorts,
    }


def _fmt_date(yyyymmdd):
    return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:]}"


def _section(title, videos, thumb_prefix):
    """Render one ranked section: a summary table plus per-video detail."""
    lines = [f"## {title} ({len(videos)})\n"]
    if not videos:
        lines.append("_No videos in this category for the search window._\n")
        return lines

    lines.append("| # | Title | Channel | Views | Likes | Comments | Duration | Uploaded |")
    lines.append("|---|-------|---------|------:|------:|---------:|----------|----------|")
    for i, v in enumerate(videos, 1):
        title_link = f"[{v['title']}]({v['url']})"
        lines.append(
            f"| {i} | {title_link} | {v['channel']} | {v['views']:,} | "
            f"{v['likes']:,} | {v['comments']:,} | {v['duration']} | {_fmt_date(v['upload_date'])} |"
        )
    lines.append("")

    lines.append(f"### {title} details\n")
    for i, v in enumerate(videos, 1):
        lines.append(f"#### {i}. {v['title']}\n")
        lines.append(f"- **Channel:** {v['channel']}")
        lines.append(f"- **Views:** {v['views']:,}")
        lines.append(f"- **Likes:** {v['likes']:,}")
        lines.append(f"- **Comments:** {v['comments']:,}")
        lines.append(f"- **Duration:** {v['duration']}")
        lines.append(f"- **Uploaded:** {_fmt_date(v['upload_date'])}")
        lines.append(f"- **URL:** {v['url']}")
        lines.append(f"- **Thumbnail:** {thumb_prefix}-{i:02d}-{v['id']}.jpg")
        lines.append(f"- **Description:** {v['description']}...")
        lines.append("")
    return lines


def generate_markdown(data):
    today = datetime.now().strftime("%Y-%m-%d")
    query = data["query"]
    lines = [
        f"# YouTube Search: \"{query}\"",
        "",
        f"**Date:** {today}",
        f"**Search query:** {query}",
        f"**Videos found (last {data['days']} days):** {data['total_found']} "
        f"({data['long_form_found']} long-form, {data['shorts_found']} Shorts)",
        f"**Shorts cutoff:** videos at or under {data['short_max']}s are classed as Shorts",
        "",
        "---",
        "",
    ]
    lines += _section("Long-form", data["long_form"], "long")
    lines += _section("Shorts", data["shorts"], "short")
    return "\n".join(lines)


def download_thumbnails(videos, thumb_dir: Path, prefix: str):
    """Download thumbnails directly from YouTube's CDN (fast, no yt-dlp needed)."""
    thumb_dir.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    for i, video in enumerate(videos, 1):
        video_id = video.get("id")
        if not video_id:
            continue
        out_path = thumb_dir / f"{prefix}-{i:02d}-{video_id}.jpg"
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
    return downloaded


def main():
    parser = argparse.ArgumentParser(description="Search YouTube via yt-dlp")
    parser.add_argument("keywords", nargs="+", help="Search keywords")
    parser.add_argument("--search-count", type=int, default=50, help="Number of results to fetch from YouTube (default: 50)")
    parser.add_argument("--days", type=int, default=30, help="Only include videos from the last N days (default: 30)")
    parser.add_argument("--top", type=int, default=15, help="Top videos to include per section (default: 15)")
    parser.add_argument("--short-max", type=int, default=DEFAULT_SHORT_MAX, help=f"Max duration in seconds to count a video as a Short (default: {DEFAULT_SHORT_MAX})")
    parser.add_argument("--output-dir", type=str, default=str(Path.home() / "content" / "research"), help="Output directory (default: ~/content/research)")
    parser.add_argument("--json", action="store_true", help="Also save raw JSON data")
    parser.add_argument("--no-thumbnails", action="store_true", help="Skip thumbnail downloading")
    args = parser.parse_args()

    data = search_youtube(args.keywords, args.search_count, args.days, args.top, args.short_max)
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

    # Download thumbnails by default unless --no-thumbnails. Long-form and Shorts
    # go in the same folder but are prefixed so the two rank-1s never collide.
    if not args.no_thumbnails and (data["long_form"] or data["shorts"]):
        thumb_dir = output_dir / f"{today}-{slug}-thumbnails"
        n_long = download_thumbnails(data["long_form"], thumb_dir, "long")
        n_short = download_thumbnails(data["shorts"], thumb_dir, "short")
        print(f"Downloaded {n_long} long-form + {n_short} Shorts thumbnails to {thumb_dir}")

    print(f"\n{markdown}")


if __name__ == "__main__":
    main()
