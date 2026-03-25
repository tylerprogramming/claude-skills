"""
YouTube Analytics — fetch video performance data (public + private analytics).

Usage:
  python3 yt_analytics.py                    # Last 28 days summary
  python3 yt_analytics.py --days 7           # Last 7 days
  python3 yt_analytics.py --video VIDEO_ID   # Single video deep dive
  python3 yt_analytics.py --all              # All videos summary
  python3 yt_analytics.py --shorts           # Shorts only
"""

import sys, json, os, argparse
from pathlib import Path
from datetime import datetime, timedelta

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                           "google-auth-httplib2", "google-auth-oauthlib",
                           "google-api-python-client", "-q"])
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

# Scopes needed: YouTube readonly + YouTube Analytics readonly
SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

CREDS_DIR = Path.home() / ".claude" / "gmail"
CREDS_FILE = CREDS_DIR / "credentials.json"
TOKEN_FILE = Path.home() / ".claude" / "analytics" / "yt_token.json"


def authenticate():
    """OAuth2 flow — reuses Gmail credentials.json, stores separate YT token."""
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDS_FILE.exists():
                print(f"ERROR: credentials.json not found at {CREDS_FILE}", file=sys.stderr)
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        TOKEN_FILE.write_text(creds.to_json())

    return creds


def get_channel_info(youtube):
    """Get authenticated user's channel info."""
    resp = youtube.channels().list(part="snippet,statistics", mine=True).execute()
    if not resp.get("items"):
        print("ERROR: No YouTube channel found for this account", file=sys.stderr)
        sys.exit(1)
    ch = resp["items"][0]
    return {
        "id": ch["id"],
        "title": ch["snippet"]["title"],
        "handle": ch["snippet"].get("customUrl", ""),
        "subscribers": int(ch["statistics"].get("subscriberCount", 0)),
        "totalViews": int(ch["statistics"].get("viewCount", 0)),
        "videoCount": int(ch["statistics"].get("videoCount", 0)),
    }


def get_recent_videos(youtube, channel_id, max_results=50, shorts_only=False):
    """Fetch recent uploads with public metrics."""
    # Get uploads playlist
    ch = youtube.channels().list(part="contentDetails", id=channel_id).execute()
    uploads_id = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    videos = []
    page_token = None
    while len(videos) < max_results:
        resp = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_id,
            maxResults=min(50, max_results - len(videos)),
            pageToken=page_token,
        ).execute()

        video_ids = [item["contentDetails"]["videoId"] for item in resp["items"]]

        # Get full video details (duration, stats)
        details = youtube.videos().list(
            part="statistics,contentDetails,snippet",
            id=",".join(video_ids),
        ).execute()

        for v in details["items"]:
            duration = v["contentDetails"]["duration"]  # ISO 8601 like PT10M30S
            is_short = _is_short(duration)

            if shorts_only and not is_short:
                continue
            if not shorts_only and is_short:
                continue

            videos.append({
                "id": v["id"],
                "title": v["snippet"]["title"],
                "publishedAt": v["snippet"]["publishedAt"],
                "duration": duration,
                "isShort": is_short,
                "views": int(v["statistics"].get("viewCount", 0)),
                "likes": int(v["statistics"].get("likeCount", 0)),
                "comments": int(v["statistics"].get("commentCount", 0)),
            })

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return videos


def _is_short(iso_duration):
    """Check if video is a Short (under 61 seconds)."""
    import re
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_duration)
    if not m:
        return False
    hours = int(m.group(1) or 0)
    minutes = int(m.group(2) or 0)
    seconds = int(m.group(3) or 0)
    total = hours * 3600 + minutes * 60 + seconds
    return total <= 60


def get_analytics(yt_analytics, channel_id, start_date, end_date, video_id=None):
    """Fetch YouTube Analytics data (CTR, impressions, retention, etc.)."""
    metrics = "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,subscribersLost,likes,comments,shares,annotationImpressions,annotationClickThroughRate"

    # Channel-level analytics
    params = {
        "ids": "channel==MINE",
        "startDate": start_date,
        "endDate": end_date,
        "metrics": metrics,
    }

    if video_id:
        params["filters"] = f"video=={video_id}"

    try:
        resp = yt_analytics.reports().query(**params).execute()
        if resp.get("rows") and len(resp["rows"]) > 0:
            row = resp["rows"][0]
            headers = [h["name"] for h in resp["columnHeaders"]]
            return dict(zip(headers, row))
    except Exception as e:
        # Some metrics may not be available, try simpler set
        pass

    # Fallback to core metrics
    try:
        resp = yt_analytics.reports().query(
            ids="channel==MINE",
            startDate=start_date,
            endDate=end_date,
            metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,likes,comments,shares",
            filters=f"video=={video_id}" if video_id else None,
        ).execute()
        if resp.get("rows") and len(resp["rows"]) > 0:
            row = resp["rows"][0]
            headers = [h["name"] for h in resp["columnHeaders"]]
            return dict(zip(headers, row))
    except Exception as e:
        print(f"Analytics query error: {e}", file=sys.stderr)

    return {}


def get_traffic_sources(yt_analytics, start_date, end_date, video_id=None):
    """Get traffic source breakdown."""
    try:
        params = {
            "ids": "channel==MINE",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "views,estimatedMinutesWatched",
            "dimensions": "insightTrafficSourceType",
            "sort": "-views",
        }
        if video_id:
            params["filters"] = f"video=={video_id}"

        resp = yt_analytics.reports().query(**params).execute()
        sources = []
        for row in resp.get("rows", []):
            sources.append({
                "source": row[0],
                "views": row[1],
                "watchTimeMin": round(row[2], 1),
            })
        return sources
    except Exception as e:
        print(f"Traffic source error: {e}", file=sys.stderr)
        return []


def get_top_search_terms(yt_analytics, start_date, end_date, video_id=None):
    """Get top search terms driving traffic."""
    try:
        params = {
            "ids": "channel==MINE",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "views",
            "dimensions": "insightTrafficSourceDetail",
            "filters": "insightTrafficSourceType==YT_SEARCH",
            "sort": "-views",
            "maxResults": 20,
        }
        if video_id:
            params["filters"] += f";video=={video_id}"

        resp = yt_analytics.reports().query(**params).execute()
        return [{"term": row[0], "views": row[1]} for row in resp.get("rows", [])]
    except Exception as e:
        print(f"Search terms error: {e}", file=sys.stderr)
        return []


def get_daily_views(yt_analytics, start_date, end_date, video_id=None):
    """Get daily view counts for trend analysis."""
    try:
        params = {
            "ids": "channel==MINE",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "views,estimatedMinutesWatched",
            "dimensions": "day",
            "sort": "day",
        }
        if video_id:
            params["filters"] = f"video=={video_id}"

        resp = yt_analytics.reports().query(**params).execute()
        return [{"date": row[0], "views": row[1], "watchTimeMin": round(row[2], 1)}
                for row in resp.get("rows", [])]
    except Exception as e:
        print(f"Daily views error: {e}", file=sys.stderr)
        return []


def get_per_video_analytics(yt_analytics, start_date, end_date, max_results=25):
    """Get per-video breakdown with analytics metrics."""
    try:
        resp = yt_analytics.reports().query(
            ids="channel==MINE",
            startDate=start_date,
            endDate=end_date,
            metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,likes,comments,shares",
            dimensions="video",
            sort="-views",
            maxResults=max_results,
        ).execute()
        results = []
        for row in resp.get("rows", []):
            results.append({
                "videoId": row[0],
                "views": row[1],
                "watchTimeMin": round(row[2], 1),
                "avgViewDuration": round(row[3]),
                "avgViewPct": round(row[4], 1),
                "subsGained": row[5],
                "likes": row[6],
                "comments": row[7],
                "shares": row[8],
            })
        return results
    except Exception as e:
        print(f"Per-video analytics error: {e}", file=sys.stderr)
        return []


def main():
    parser = argparse.ArgumentParser(description="YouTube Analytics")
    parser.add_argument("--days", type=int, default=28, help="Number of days to look back")
    parser.add_argument("--video", help="Specific video ID for deep dive")
    parser.add_argument("--all", action="store_true", help="All videos summary")
    parser.add_argument("--shorts", action="store_true", help="Shorts only")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    creds = authenticate()

    youtube = build("youtube", "v3", credentials=creds)
    yt_analytics = build("youtubeAnalytics", "v2", credentials=creds)

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")

    result = {
        "period": {"start": start_date, "end": end_date, "days": args.days},
    }

    # Channel info
    channel = get_channel_info(youtube)
    result["channel"] = channel
    print(f"Channel: {channel['title']} ({channel['handle']})", file=sys.stderr)
    print(f"Subscribers: {channel['subscribers']:,} | Total views: {channel['totalViews']:,}", file=sys.stderr)

    if args.video:
        # Single video deep dive
        print(f"\nFetching analytics for video {args.video}...", file=sys.stderr)

        # Get video details
        details = youtube.videos().list(part="snippet,statistics,contentDetails", id=args.video).execute()
        if details["items"]:
            v = details["items"][0]
            result["video"] = {
                "id": args.video,
                "title": v["snippet"]["title"],
                "publishedAt": v["snippet"]["publishedAt"],
                "duration": v["contentDetails"]["duration"],
                "views": int(v["statistics"].get("viewCount", 0)),
                "likes": int(v["statistics"].get("likeCount", 0)),
                "comments": int(v["statistics"].get("commentCount", 0)),
            }

        result["analytics"] = get_analytics(yt_analytics, channel["id"], start_date, end_date, args.video)
        result["trafficSources"] = get_traffic_sources(yt_analytics, start_date, end_date, args.video)
        result["searchTerms"] = get_top_search_terms(yt_analytics, start_date, end_date, args.video)
        result["dailyViews"] = get_daily_views(yt_analytics, start_date, end_date, args.video)

    else:
        # Channel overview
        print(f"\nFetching {args.days}-day analytics...", file=sys.stderr)

        result["analytics"] = get_analytics(yt_analytics, channel["id"], start_date, end_date)
        result["trafficSources"] = get_traffic_sources(yt_analytics, start_date, end_date)
        result["searchTerms"] = get_top_search_terms(yt_analytics, start_date, end_date)
        result["perVideo"] = get_per_video_analytics(yt_analytics, start_date, end_date)

        # Get video titles for the per-video breakdown
        if result["perVideo"]:
            video_ids = [v["videoId"] for v in result["perVideo"]]
            details = youtube.videos().list(part="snippet,contentDetails", id=",".join(video_ids[:50])).execute()
            title_map = {}
            for v in details["items"]:
                title_map[v["id"]] = {
                    "title": v["snippet"]["title"],
                    "duration": v["contentDetails"]["duration"],
                }
            for v in result["perVideo"]:
                info = title_map.get(v["videoId"], {})
                v["title"] = info.get("title", "Unknown")
                v["isShort"] = _is_short(info.get("duration", "PT0S"))

        # Recent videos list
        result["recentVideos"] = get_recent_videos(youtube, channel["id"],
                                                    max_results=20,
                                                    shorts_only=args.shorts)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
