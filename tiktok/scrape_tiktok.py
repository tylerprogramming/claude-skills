"""
Scrape TikTok videos by hashtag using Apify and generate a clean dataset.

Usage: python scrape_tiktok.py --hashtags claudecode claude --timeframe "3 months" --limit 100

Requires:
  - APIFY_API_TOKEN in ~/.claude/.env
  - requests Python package (or uses urllib)
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error


def load_api_token():
    """Load Apify API token from ~/.claude/.env"""
    env_path = os.path.expanduser("~/.claude/.env")
    if not os.path.exists(env_path):
        print("Error: ~/.claude/.env not found. Set APIFY_API_TOKEN there.")
        sys.exit(1)

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("APIFY_API_TOKEN="):
                return line.split("=", 1)[1].strip()

    # Also check environment
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
    if data is not None:
        body = json.dumps(data).encode("utf-8")
    else:
        body = None

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"API Error {e.code}: {error_body}")
        sys.exit(1)


def run_scraper(token, hashtags, timeframe, limit):
    """Run the TikTok scraper actor and return results."""
    actor = "clockworks~tiktok-scraper"
    url = f"https://api.apify.com/v2/acts/{actor}/runs"

    input_data = {
        "hashtags": hashtags,
        "excludePinnedPosts": False,
        "oldestPostDateUnified": timeframe,
        "resultsPerPage": limit,
        "profileSorting": "popular",
        "shouldDownloadCovers": False,
        "shouldDownloadSlideshowImages": False,
        "shouldDownloadSubtitles": False,
        "shouldDownloadVideos": False,
    }

    print(f"Starting TikTok scraper for hashtags: {', '.join(f'#{h}' for h in hashtags)}")
    print(f"Timeframe: {timeframe} | Limit: {limit} per hashtag")

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
    print(f"Got {len(items)} raw results")
    return items


def deduplicate(videos):
    """Remove duplicate videos (same video can appear under multiple hashtags)."""
    seen = set()
    unique = []
    for v in videos:
        vid_id = v.get("id")
        if vid_id and vid_id not in seen:
            seen.add(vid_id)
            unique.append(v)
    return unique


def classify_video(video, hashtags_searched):
    """Basic relevance check — is this actually about AI/tech Claude?"""
    text = (video.get("text") or "").lower()
    noise = ["alligator", "princess", "diana>>>", "wmmap", "mofagong",
             "ripclaude", "rip claude", "gator", "albino"]
    if any(n in text for n in noise):
        return False
    return True


def compute_stats(video):
    """Compute engagement metrics for a video."""
    plays = video.get("playCount", 0) or 0
    likes = video.get("diggCount", 0) or 0
    comments = video.get("commentCount", 0) or 0
    shares = video.get("shareCount", 0) or 0
    saves = video.get("collectCount", 0) or 0

    total_eng = likes + comments + shares + saves
    eng_rate = (total_eng / plays * 100) if plays > 0 else 0

    return {
        "plays": plays,
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "saves": saves,
        "engagement_rate": round(eng_rate, 1),
    }


def format_number(n):
    """Format large numbers: 1200000 -> 1.2M, 45000 -> 45K"""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def build_report(videos, hashtags, timeframe):
    """Build the markdown analysis report."""
    lines = []
    tags_str = " & ".join(f"#{h}" for h in hashtags)

    lines.append(f"# TikTok Research: {tags_str}")
    lines.append(f"**Scraped: {time.strftime('%b %d, %Y')} | {len(videos)} videos | Timeframe: {timeframe}**")
    lines.append("")

    if not videos:
        lines.append("No results found.")
        return "\n".join(lines)

    # --- Overall Stats ---
    total_plays = sum(v.get("playCount", 0) or 0 for v in videos)
    total_likes = sum(v.get("diggCount", 0) or 0 for v in videos)
    total_shares = sum(v.get("shareCount", 0) or 0 for v in videos)
    total_saves = sum(v.get("collectCount", 0) or 0 for v in videos)
    avg_eng = sum(compute_stats(v)["engagement_rate"] for v in videos) / len(videos)
    durations = [v.get("videoMeta", {}).get("duration", 0) for v in videos if v.get("videoMeta", {}).get("duration")]
    avg_duration = sum(durations) / len(durations) if durations else 0

    lines.append("---")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Videos | {len(videos)} |")
    lines.append(f"| Total Views | {format_number(total_plays)} |")
    lines.append(f"| Total Likes | {format_number(total_likes)} |")
    lines.append(f"| Total Shares | {format_number(total_shares)} |")
    lines.append(f"| Total Saves | {format_number(total_saves)} |")
    lines.append(f"| Avg Engagement Rate | {avg_eng:.1f}% |")
    lines.append(f"| Avg Duration | {int(avg_duration)}s |")
    lines.append("")

    # --- Top Videos Table ---
    sorted_vids = sorted(videos, key=lambda x: x.get("playCount", 0) or 0, reverse=True)

    lines.append("---")
    lines.append("")
    lines.append("## Top Videos by Views")
    lines.append("")
    lines.append("| # | Views | Likes | Shares | Saves | Eng% | Creator | Followers | Duration | Caption |")
    lines.append("|---|-------|-------|--------|-------|------|---------|-----------|----------|---------|")

    for i, v in enumerate(sorted_vids[:30], 1):
        stats = compute_stats(v)
        author = v.get("authorMeta", {})
        username = author.get("name", "?")
        fans = author.get("fans", 0)
        duration = v.get("videoMeta", {}).get("duration", 0)
        caption = (v.get("text") or "")[:60].replace("|", "/").replace("\n", " ")
        url = v.get("webVideoUrl", "")

        lines.append(
            f"| {i} "
            f"| {format_number(stats['plays'])} "
            f"| {format_number(stats['likes'])} "
            f"| {format_number(stats['shares'])} "
            f"| {format_number(stats['saves'])} "
            f"| {stats['engagement_rate']}% "
            f"| [@{username}]({url}) "
            f"| {format_number(fans)} "
            f"| {duration}s "
            f"| {caption} |"
        )

    lines.append("")

    # --- Top Videos Detail Cards ---
    lines.append("---")
    lines.append("")
    lines.append("## Top 15 Video Details")
    lines.append("")

    for i, v in enumerate(sorted_vids[:15], 1):
        stats = compute_stats(v)
        author = v.get("authorMeta", {})
        username = author.get("name", "?")
        fans = author.get("fans", 0)
        duration = v.get("videoMeta", {}).get("duration", 0)
        caption = (v.get("text") or "").replace("\n", " ").strip()
        url = v.get("webVideoUrl", "")
        date = (v.get("createTimeISO") or "")[:10]
        hashtag_list = v.get("hashtags", [])
        tags = " ".join(
            f"#{h.get('name', '') if isinstance(h, dict) else h}"
            for h in hashtag_list[:8]
        )

        lines.append(f"### {i}. @{username} — {format_number(stats['plays'])} views")
        lines.append(f"> {caption}")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Views | {format_number(stats['plays'])} |")
        lines.append(f"| Likes | {format_number(stats['likes'])} |")
        lines.append(f"| Shares | {format_number(stats['shares'])} |")
        lines.append(f"| Saves | {format_number(stats['saves'])} |")
        lines.append(f"| Comments | {format_number(stats['comments'])} |")
        lines.append(f"| Engagement | {stats['engagement_rate']}% |")
        lines.append(f"| Duration | {duration}s |")
        lines.append(f"| Date | {date} |")
        lines.append(f"| Followers | {format_number(fans)} |")
        lines.append(f"| Tags | {tags} |")
        lines.append(f"| Link | {url} |")
        lines.append("")

    # --- Top Creators ---
    lines.append("---")
    lines.append("")
    lines.append("## Top Creators")
    lines.append("")

    creator_stats = {}
    for v in videos:
        name = v.get("authorMeta", {}).get("name", "?")
        if name not in creator_stats:
            creator_stats[name] = {
                "views": 0, "videos": 0,
                "fans": v.get("authorMeta", {}).get("fans", 0),
                "total_eng": 0, "total_saves": 0,
            }
        creator_stats[name]["views"] += v.get("playCount", 0) or 0
        creator_stats[name]["videos"] += 1
        creator_stats[name]["total_saves"] += v.get("collectCount", 0) or 0
        creator_stats[name]["total_eng"] += compute_stats(v)["engagement_rate"]

    top_creators = sorted(creator_stats.items(), key=lambda x: x[1]["views"], reverse=True)[:20]

    lines.append("| Creator | Total Views | Videos | Followers | Avg Eng% | Total Saves |")
    lines.append("|---------|-------------|--------|-----------|----------|-------------|")
    for name, s in top_creators:
        avg = s["total_eng"] / s["videos"] if s["videos"] else 0
        lines.append(
            f"| @{name} "
            f"| {format_number(s['views'])} "
            f"| {s['videos']} "
            f"| {format_number(s['fans'])} "
            f"| {avg:.1f}% "
            f"| {format_number(s['total_saves'])} |"
        )

    lines.append("")

    # --- Engagement Leaders ---
    lines.append("---")
    lines.append("")
    lines.append("## Highest Engagement Rate (min 10K views)")
    lines.append("")

    eng_vids = [v for v in videos if (v.get("playCount", 0) or 0) >= 10000]
    eng_vids.sort(key=lambda v: compute_stats(v)["engagement_rate"], reverse=True)

    lines.append("| # | Eng% | Views | Saves | Creator | Duration | Caption |")
    lines.append("|---|------|-------|-------|---------|----------|---------|")

    for i, v in enumerate(eng_vids[:20], 1):
        stats = compute_stats(v)
        username = v.get("authorMeta", {}).get("name", "?")
        duration = v.get("videoMeta", {}).get("duration", 0)
        caption = (v.get("text") or "")[:50].replace("|", "/").replace("\n", " ")
        url = v.get("webVideoUrl", "")

        lines.append(
            f"| {i} "
            f"| **{stats['engagement_rate']}%** "
            f"| {format_number(stats['plays'])} "
            f"| {format_number(stats['saves'])} "
            f"| [@{username}]({url}) "
            f"| {duration}s "
            f"| {caption} |"
        )

    lines.append("")

    # --- Duration Analysis ---
    lines.append("---")
    lines.append("")
    lines.append("## Duration Analysis")
    lines.append("")

    buckets = {
        "0-15s": {"range": (0, 15), "videos": [], "plays": 0, "eng": []},
        "15-30s": {"range": (15, 30), "videos": [], "plays": 0, "eng": []},
        "30-60s": {"range": (30, 60), "videos": [], "plays": 0, "eng": []},
        "60-120s": {"range": (60, 120), "videos": [], "plays": 0, "eng": []},
        "120s+": {"range": (120, 99999), "videos": [], "plays": 0, "eng": []},
    }

    for v in videos:
        dur = v.get("videoMeta", {}).get("duration", 0) or 0
        stats = compute_stats(v)
        for bname, b in buckets.items():
            if b["range"][0] <= dur < b["range"][1]:
                b["videos"].append(v)
                b["plays"] += stats["plays"]
                b["eng"].append(stats["engagement_rate"])
                break

    lines.append("| Duration | Videos | Total Views | Avg Views | Avg Eng% |")
    lines.append("|----------|--------|-------------|-----------|----------|")
    for bname, b in buckets.items():
        count = len(b["videos"])
        if count > 0:
            avg_views = b["plays"] // count
            avg_e = sum(b["eng"]) / count
            lines.append(
                f"| {bname} | {count} | {format_number(b['plays'])} "
                f"| {format_number(avg_views)} | {avg_e:.1f}% |"
            )

    lines.append("")

    # --- All Video URLs ---
    lines.append("---")
    lines.append("")
    lines.append("## All Video URLs")
    lines.append("")
    lines.append("<details>")
    lines.append("<summary>Click to expand full URL list</summary>")
    lines.append("")

    for i, v in enumerate(sorted_vids, 1):
        stats = compute_stats(v)
        username = v.get("authorMeta", {}).get("name", "?")
        url = v.get("webVideoUrl", "")
        caption = (v.get("text") or "")[:50].replace("\n", " ")
        lines.append(f"{i}. [{format_number(stats['plays'])} views] @{username}: {caption} — {url}")

    lines.append("")
    lines.append("</details>")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Scrape TikTok by hashtag via Apify")
    parser.add_argument("--hashtags", nargs="+", required=True, help="Hashtags to search (without #)")
    parser.add_argument("--timeframe", default="3 months", help="How far back to look (e.g. '3 months', '30 days')")
    parser.add_argument("--limit", type=int, default=100, help="Max results per hashtag")
    parser.add_argument("--output", default=None, help="Output directory (default: ~/youtube/tiktok-research/)")
    parser.add_argument("--raw-json", action="store_true", help="Also save raw JSON data")

    args = parser.parse_args()
    token = load_api_token()

    # Run the scraper
    raw_videos = run_scraper(token, args.hashtags, args.timeframe, args.limit)

    # Clean up
    unique = deduplicate(raw_videos)
    print(f"Deduplicated: {len(raw_videos)} -> {len(unique)} unique videos")

    relevant = [v for v in unique if classify_video(v, args.hashtags)]
    print(f"Filtered: {len(relevant)} relevant videos")

    # Sort by plays
    relevant.sort(key=lambda x: x.get("playCount", 0) or 0, reverse=True)

    # Build output
    output_dir = args.output or os.path.expanduser("~/youtube/tiktok-research")
    os.makedirs(output_dir, exist_ok=True)

    # Generate slug from hashtags
    slug = "-".join(args.hashtags[:3])

    # Save report
    report = build_report(relevant, args.hashtags, args.timeframe)
    report_path = os.path.join(output_dir, f"{slug}-report.md")
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\nReport saved: {report_path}")

    # Save raw JSON if requested
    if args.raw_json:
        json_path = os.path.join(output_dir, f"{slug}-raw.json")
        with open(json_path, "w") as f:
            json.dump(relevant, f, indent=2)
        print(f"Raw JSON saved: {json_path}")

    # Print summary to stdout
    print(f"\n{'='*60}")
    print(f"SUMMARY: {len(relevant)} videos for {' & '.join(f'#{h}' for h in args.hashtags)}")
    print(f"{'='*60}")
    total_plays = sum(v.get("playCount", 0) or 0 for v in relevant)
    print(f"Total views: {format_number(total_plays)}")
    print(f"Top video: {format_number(relevant[0].get('playCount', 0))} views by @{relevant[0].get('authorMeta', {}).get('name', '?')}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
