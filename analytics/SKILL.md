---
name: analytics
description: YouTube channel analytics - views, CTR, retention, traffic sources, search terms, per-video breakdown. Supports long-form vs shorts split, single video deep dives, and trend analysis. Triggers on: analytics, how are my videos doing, youtube stats, channel performance, video performance, check my analytics, how did my video do.
argument-hint: [--days 28] [--video VIDEO_ID] [--shorts] [--top N]
allowed-tools: Bash(python3:*), Read, Write, Edit, Glob, Grep, WebSearch
user-invocable: true
---

Analyze YouTube channel performance using the YouTube Data API v3 and YouTube Analytics API.

## Prerequisites

- OAuth2 credentials at `~/.claude/gmail/credentials.json` (shared with Gmail skill)
- YouTube token auto-cached at `~/.claude/analytics/yt_token.json` after first auth
- YouTube Data API v3 and YouTube Analytics API enabled in Google Cloud Console

## Flow

### Step 1: Determine What to Analyze

Parse $ARGUMENTS for:

- **No args / "how are my videos doing"**: Run the full channel overview (last 28 days)
- **`--days N`**: Change the lookback period (default 28)
- **`--video VIDEO_ID`**: Single video deep dive
- **`--shorts`**: Shorts-only analysis
- **`--top N`**: Show top N videos (default 10)
- **Specific question** like "how did my Antigravity video do": Search for the video by title, then deep dive

### Step 2: Fetch Data

Run the Python script:

```bash
python3 ~/.claude/skills/analytics/yt_analytics.py --days 28 --json
```

For a single video deep dive:
```bash
python3 ~/.claude/skills/analytics/yt_analytics.py --video VIDEO_ID --days 90 --json
```

For shorts only:
```bash
python3 ~/.claude/skills/analytics/yt_analytics.py --shorts --json
```

Capture the JSON output (printed to stdout). Stderr has status messages.
