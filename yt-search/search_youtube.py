#!/usr/bin/env python3
"""Search YouTube via yt-dlp and output a markdown report of top videos.

Results are split into two ranked sections — long-form and Shorts — because
the research feeds two different tracks (long-form planning via /yt-package, short-form
scripts via /shorts) and the two formats are not comparable head to head.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

# A video is treated as a Short if its duration is at or below this many seconds.
# 60s is the classic Shorts cap; YouTube now allows up to ~3 min, so bump
# --short-max to 180 if you want the longer Shorts pulled into the Shorts bucket.
DEFAULT_SHORT_MAX = 60

# Compact per-video JSON so a 50-video detail pass doesn't return megabytes of
# format data we never look at.
DETAIL_TEMPLATE = (
    "%(.{id,title,channel,view_count,like_count,comment_count,"
    "upload_date,duration,duration_string,description})j"
)


def ytdlp_bin():
    """Resolve the yt-dlp to use.

    Old pip-installed builds pinned to system Python 3.9 can't extract YouTube
    metadata any more, so prefer an explicit override, then Homebrew's build,
    then whatever is on PATH.
    """
    override = os.environ.get("YT_DLP_BIN")
    if override:
        return override
    for candidate in ("/opt/homebrew/bin/yt-dlp", "/usr/local/bin/yt-dlp"):
        if Path(candidate).exists():
            return candidate
    return shutil.which("yt-dlp") or "yt-dlp"


def _search_url(query, days):
    """Build a YouTube search URL sorted by upload date and filtered to a window.

    `ytsearchdate:` was removed from yt-dlp, so the date sort now has to ride on
    the search URL itself. `sp` is a base64 protobuf: field 1 = sort (2 = upload
    date), field 2 = filters (upload date bucket).
    """
    if days <= 1:
        sp = "CAISAggC"    # today
    elif days <= 7:
        sp = "CAISAggD"    # this week
    elif days <= 31:
        sp = "CAISAggE"    # this month
    else:
        sp = "CAISAggF"    # this year
    return f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}&sp={sp}"


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def _parse_json_lines(text):
    out = []
    for line in (text or "").strip().split("\n"):
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def search_youtube(keywords, search_count=50, days=30, top_n=15, short_max=DEFAULT_SHORT_MAX):
    query = " ".join(keywords)
    # Quote multi-word queries for phrase matching instead of loose keyword matching
    quoted_query = f'"{query}"' if len(keywords) > 1 else query
    bin_path = ytdlp_bin()

    print(f"Searching YouTube for: {query}")
    print(f"Fetching {search_count} most recent results...")

    # Pass 1: flat listing. One request, no per-video extraction, and it already
    # carries title/channel/views/duration — enough to rank and filter.
    result = _run([
        bin_path,
        _search_url(quoted_query, days),
        "--flat-playlist",
        "--playlist-end", str(search_count),
        "--no-warnings",
        "-J",
    ])

    if result.returncode != 0 and not result.stdout:
        print(f"Error: yt-dlp failed\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    try:
        entries = json.loads(result.stdout).get("entries") or []
    except json.JSONDecodeError:
        print(f"Error: could not parse yt-dlp output\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    candidates = []
    for d in entries:
        if not d.get("id"):
            continue
        candidates.append({
            "title": d.get("title") or "N/A",
            "channel": d.get("channel") or d.get("uploader") or "N/A",
            "views": d.get("view_count") or 0,
            "likes": 0,
            "comments": 0,
            "upload_date": "00000000",
            "duration": d.get("duration_string") or "N/A",
            "duration_seconds": d.get("duration") or 0,
            "url": f"https://youtube.com/watch?v={d['id']}",
            "description": (d.get("description") or "")[:300],
            "id": d["id"],
        })

    # Filter to videos whose title contains at least one keyword (relevance check)
    kw_lower = [k.lower() for k in keywords]
    relevant = [v for v in candidates if any(k in v["title"].lower() for k in kw_lower)]
    if relevant:
        candidates = relevant

    # Pass 2: full metadata (upload date, likes, comments) for the videos that can
    # actually make the report. Detail-fetching all 50 would be slow for no gain,
    # so take a margin above top_n per section to absorb date-filter drops.
    margin = top_n + 5
    by_views = sorted(candidates, key=lambda x: x["views"], reverse=True)
    short_pool = [v for v in by_views if 0 < v["duration_seconds"] <= short_max][:margin]
    long_pool = [v for v in by_views if not (0 < v["duration_seconds"] <= short_max)][:margin]
    detail_pool = short_pool + long_pool

    print(f"Fetching details for {len(detail_pool)} candidates...")
    detail = {}
    if detail_pool:
        detail_result = _run([
            bin_path, "--skip-download", "--no-warnings",
            "--print", DETAIL_TEMPLATE,
        ] + [v["url"] for v in detail_pool])
        for d in _parse_json_lines(detail_result.stdout):
            if d.get("id"):
                detail[d["id"]] = d

    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
    videos = []
    for v in detail_pool:
        d = detail.get(v["id"])
        if not d:
            continue
        upload = d.get("upload_date") or "00000000"
        if upload < cutoff:
            continue
        v.update({
            "views": d.get("view_count") or v["views"],
            "likes": d.get("like_count") or 0,
            "comments": d.get("comment_count") or 0,
            "upload_date": upload,
            "duration": d.get("duration_string") or v["duration"],
            "duration_seconds": d.get("duration") or v["duration_seconds"],
            "description": (d.get("description") or v["description"])[:300],
        })
        videos.append(v)

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
