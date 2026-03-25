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

### Step 3: Present the Channel Overview

When showing the full overview, present in this order:

**1. Channel snapshot**
- Subscribers, total views, video count
- Period analyzed (start - end date)

**2. Period summary**
- Total views, watch time (hours), avg view duration, avg retention %
- Net subscribers (gained - lost)
- Total likes, comments, shares

**3. Top performing long-form videos (table)**

| Video | Published | Views | Avg Duration | Retention | Subs Gained | Engagement |
|-------|-----------|-------|-------------|-----------|-------------|------------|

- Engagement rate = (likes + comments) / views * 100
- Sort by views descending
- Separate long-form from shorts automatically (shorts = under 61 seconds)

**4. Shorts performance (if any exist)**

| Short | Published | Views | Likes |
|-------|-----------|-------|-------|

**5. Traffic sources breakdown**
- Show top 5 sources with view counts and percentages
- Highlight which sources are strong vs weak

**6. Top search terms**
- Show top 10 search terms driving traffic
- Note which terms align with current content strategy vs legacy content

**7. Analysis and recommendations**
Based on the data, provide:
- **What's working** - which topics, formats, lengths get the best retention and views
- **What's not working** - videos that underperformed and why
- **Content strategy insights** - which search terms suggest demand you're not filling
- **Retention patterns** - are shorter videos retaining better? Is there a sweet spot?
- **Growth signals** - subscriber gain rate, which videos drive the most subs
- **Actionable next steps** - 2-3 specific recommendations

### Step 4: Single Video Deep Dive

When analyzing a specific video, show:

1. **Video stats** - views, likes, comments, shares, duration, publish date
2. **Analytics** - avg view duration, retention %, subs gained/lost
3. **Traffic sources** - where views came from for THIS video
4. **Search terms** - what searches led to THIS video
5. **Daily view trend** - show the view curve (first 7 days vs steady state)
6. **Comparison** - how does this compare to your channel average?
