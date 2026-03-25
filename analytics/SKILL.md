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

### Step 5: Title/Thumbnail A/B Tracking

Each video package at `~/youtube/<slug>/` should have a `performance.md` file that tracks what's been tried and what to try next. When the user asks to update a title or thumbnail, or when a video is underperforming, create or update this file.

**Create `~/youtube/<slug>/performance.md`:**

```markdown
# Performance Tracker: [Video Title]

**Video ID:** [ID]
**Published:** [date]
**URL:** https://youtu.be/[ID]

---

## Current Live
- **Title:** [current title on YouTube]
- **Thumbnail:** [description or path to current thumbnail]

## Title History
| # | Title | Date Set | Views At Change | Notes |
|---|-------|----------|-----------------|-------|
| 1 | [original title] | [publish date] | 0 | Original |
| 2 | [updated title] | [change date] | [views] | [why changed] |

## Thumbnail History
| # | Description | Date Set | Views At Change | Notes |
|---|-------------|----------|-----------------|-------|
| 1 | [description] | [publish date] | 0 | Original |
| 2 | [description] | [change date] | [views] | [why changed] |

## Performance Snapshots
| Date | Views | Retention | CTR (if available) | Subs Gained |
|------|-------|-----------|---------------------|-------------|
| [date] | [views] | [%] | [%] | [+N] |

## Next To Try
- **Title idea:** [suggestion based on SEO research or analytics]
- **Thumbnail idea:** [suggestion - what to change visually]
- **Why:** [reasoning from data - low CTR, bad retention, etc.]

## Notes
[Any observations - what's working, what's not, audience feedback from comments]
```

**When to create/update performance.md:**
- When a video is underperforming (below channel average retention or views)
- When the user asks "how is [video] doing" and it needs help
- When the user changes a title or thumbnail
- When running a full channel overview and spotting underperformers

**When suggesting title/thumbnail changes:**
1. Read the existing `performance.md` to see what's been tried
2. Read `titles.md` and `seo.md` if they exist - there may be unused title variants
3. Never suggest a title that's already been tried
4. Use `/seo` research data to inform suggestions
5. For thumbnails, suggest specific changes (text, colors, expression, layout) not vague "make it better"

### Step 6: Save Report (optional)

If the user asks to save or the data is particularly insightful, save a snapshot:

```
~/youtube/analytics/YYYY-MM-DD-overview.md
~/youtube/analytics/YYYY-MM-DD-VIDEO_ID.md
```

## Rules

- Always separate long-form from shorts - they're different content strategies
- When the user asks about a specific video by name, search their recent uploads to find the video ID
- Retention % is the most important metric for long-form - highlight it prominently
- For shorts, views and completion rate matter most
- Don't just dump numbers - always include analysis and actionable insights
- Compare against channel averages to show what's above/below normal
- Note content era shifts (CrewAI era, n8n era, Claude Code era) when relevant to search terms
- Legacy search traffic (crewai, splay tree, radix sort) is passive income - don't suggest abandoning it, but note it's not the growth driver
- External URL traffic = social media distribution working. If it drops, social strategy needs attention.
- Suggested/Related video traffic under 10% = thumbnail + title CTR opportunity
- No em dashes in output
