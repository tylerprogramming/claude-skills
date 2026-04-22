---
name: tiktok-analytics
description: Track TikTok video performance over time. Import CSVs, read analytics screenshots, scrape public metrics via Apify, and generate performance reports. Triggers on: tiktok analytics, how's my tiktok, tiktok performance, tiktok stats, tiktok report, import tiktok, tiktok screenshots, log tiktok.
argument-hint: [screenshots | import <csv-path> | scrape | report | log <video> <metrics>]
allowed-tools: Bash(python3:*), Read, Write, Edit, Glob, Grep, AskUserQuestion
user-invocable: true
---

Track your TikTok video performance over time using a SQLite database. Combines three data sources:
1. **Apify scraping** - automated public metrics (views, likes, comments, shares, saves)
2. **CSV imports** - TikTok's exported Overview and Content CSVs
3. **Screenshot reading** - you screenshot TikTok's per-video analytics and I extract the deep metrics (watch time, retention, traffic sources, followers)

Database: `~/.claude/skills/tiktok-analytics/data/tiktok.db`
Analysis files: `~/youtube/tiktok-analytics/`

## Parsing Arguments

Parse `$ARGUMENTS` to determine the mode:

### Mode: `screenshots` (or user provides screenshot images)
The user has provided TikTok analytics screenshots. Read each image and extract:
- Video title/caption
- Video views
- Total play time
- Average watch time
- Watched full video %
- New followers
- Traffic source breakdown (For You %, Search %, Personal profile %, Following %, DM %, Sound %, Other %)
- Retention rate info (where viewers stopped watching)

For each screenshot:
1. Match the video to an existing record in the database by caption (search with `search_videos()`)
2. If not found, ask the user for the TikTok URL so you can extract the video ID
3. Save the deep metrics using `save_deep_metrics()`
4. Also update the public metrics from the screenshot header (views, likes, comments, shares) using `save_metrics()`

After processing all screenshots, show a summary table of what was saved.

### Mode: `import <csv-path>`
Import a TikTok CSV export.

Auto-detect the CSV type by reading the header:
- If headers include "Video Views", "Profile Views" -> Overview CSV
- If headers include "Video title", "Video link" -> Content CSV

Run the appropriate import:
```bash
python3 ~/.claude/skills/tiktok-analytics/import_csv.py overview "<csv-path>" --year 2026
# or
python3 ~/.claude/skills/tiktok-analytics/import_csv.py content "<csv-path>" --year 2026
```

Show results after import.

### Mode: `scrape`
Scrape the user's TikTok profile to pull latest public metrics for all videos.

```bash
python3 ~/.claude/skills/tiktok-analytics/scrape_profile.py @codewithtyler --limit 100
```

Show before/after comparison for any videos that had metrics changes since the last snapshot.

### Mode: `report` (or no arguments, or "how's my tiktok")
Generate a performance report from the database.

```bash
python3 ~/.claude/skills/tiktok-analytics/tiktok_db.py
```

Then query the database directly to build the report:

```python
import sys
sys.path.insert(0, str(__import__('pathlib').Path.home() / '.claude/skills/tiktok-analytics'))
from tiktok_db import get_connection, init_all_tables, get_latest_metrics, get_summary, get_daily_overview
```

Build a report that includes:

**Account Overview**
- Total videos tracked
- Total views across all videos
- Date range of data
- Daily overview trends (if available)

**Top Videos (by latest views)**
| # | Video | Posted | Views | Likes | Comments | Shares | Eng% |
With deep metrics columns if available:
| Avg Watch | Full Watch % | FYP % | Search % | New Followers |

**Trends**
- Which videos are still growing (compare snapshots)
- Best performing hooks/formats
- Traffic source patterns

**Recommendations**
- Based on what's working, suggest what to make next

Save the report to `~/youtube/tiktok-analytics/YYYY-MM-DD-report.md`

### Mode: `log <search-term> <metrics>`
Quick manual entry for a single video's deep metrics. The user will say something like:
"log tiktok: carousels video, 13.48s avg watch, 2.9% full watch, 90% FYP, 7% search, 3 new followers"

1. Search for the video by the search term
2. If multiple matches, ask which one
3. Parse the metrics from the natural language
4. Save via `save_deep_metrics()`
5. Confirm what was saved

## Database Access Pattern

All database operations go through the Python module:

```python
import sys
sys.path.insert(0, str(__import__('pathlib').Path.home() / '.claude/skills/tiktok-analytics'))
from tiktok_db import (
    get_connection, init_all_tables,
    upsert_video, get_all_videos, get_video_by_id, search_videos,
    save_metrics, get_metrics_history, get_latest_metrics,
    save_deep_metrics, get_deep_metrics,
    save_daily_overview, get_daily_overview,
    get_summary,
)
```

Or via direct sqlite3 queries for complex reports:
```bash
python3 -c "
import sqlite3
conn = sqlite3.connect(str(__import__('pathlib').Path.home() / '.claude/skills/tiktok-analytics/data/tiktok.db'))
conn.row_factory = sqlite3.Row
# your query here
"
```

## Screenshot Reading Tips

When reading TikTok analytics screenshots, look for these specific elements:
- **Top banner**: video title, post date, view/like/comment/share counts (small icons with numbers)
- **Metrics row**: Video views, Total play time, Average watch time, Watched full video %, New followers
- **Graph**: Daily view trend (first 7 days after posting)
- **Retention rate**: Shows where viewers dropped off (e.g., "Most viewers stopped watching at 0:02")
- **Traffic source**: Bar chart with percentages for For You, Search, Personal profile, Following, DM, Sound, Other

Extract ALL of these fields. Don't skip any.

## Rules

- Always initialize tables before any DB operation: `init_all_tables(conn)`
- Use `--year 2026` when importing CSVs (TikTok only includes month/day, not year)
- Profile is always `@codewithtyler` unless the user says otherwise
- When showing reports, include engagement rate: `(likes + comments + shares) / views * 100`
- Deep metrics are the most valuable - encourage the user to screenshot their top performers
- Save analysis reports to `~/youtube/tiktok-analytics/` not in the skill directory
- When processing screenshots, always confirm what you extracted before saving to DB
