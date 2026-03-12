---
name: tiktok
description: Research TikTok trends by hashtag using Apify. Scrapes videos, analyzes what's performing, identifies content patterns, and suggests video ideas. Triggers on: tiktok research, tiktok trends, scrape tiktok, what's trending on tiktok, tiktok analysis.
argument-hint: [hashtags (space-separated)] [--timeframe "3 months"] [--limit 100]
allowed-tools: Bash(python3:*), Read, Write, Glob, Grep
user-invocable: true
---

Research TikTok trends for the given hashtags.

## Parsing Arguments

Parse `$ARGUMENTS` for:
- **Hashtags**: One or more words (strip any leading `#`). Required.
- **--timeframe**: How far back to search. Default: `"3 months"`. Accepts Apify-style strings like `"30 days"`, `"2 weeks"`, `"6 months"`.
- **--limit**: Max results per hashtag. Default: `100`.

If the user just provides hashtags with no flags, use the defaults.

## Flow

### Step 1: Scrape TikTok

Run the scraper script:
```
python3 ~/.claude/skills/tiktok/scrape_tiktok.py --hashtags <hashtag1> <hashtag2> ... --timeframe "<timeframe>" --limit <limit> --raw-json
```

This will:
- Hit the Apify TikTok Scraper API
- Poll until the run completes
- Deduplicate and filter results
- Save a markdown report to `~/youtube/tiktok-research/<hashtags>-report.md`
- Save raw JSON to `~/youtube/tiktok-research/<hashtags>-raw.json`

Wait for it to finish. If it fails, check that `APIFY_API_TOKEN` is set in `~/.claude/.env`.

### Step 2: Read the Report

Read the generated report file from `~/youtube/tiktok-research/`. Present the **Overview** and **Top Videos** table to the user.

### Step 3: Deep Analysis

Read the raw JSON file and perform a deeper analysis. Write your findings as an additional section appended to the report file. Your analysis MUST include:

#### Hooks & Formats That Work
- What opening lines/hooks do the top videos use?
- What video formats dominate? (talking head, screen recording, text overlay, slideshow, etc.)
- What's the optimal duration based on the data?

#### Content Themes
Categorize every video into themes (e.g., "tutorials", "comparisons", "hot takes", "demos", "news"). Show which themes get the most views AND the most engagement. Present as a table:

| Theme | Videos | Total Views | Avg Engagement |
|-------|--------|-------------|----------------|

#### Creators to Watch
Who are the top creators in this niche? Who has the best engagement-to-follower ratio (punching above their weight)?

#### Content Gaps & Opportunities
Based on what exists and what's performing, what content is MISSING? What angles haven't been explored? What could the user make that would stand out?

#### Suggested TikTok Ideas
Based on all the data, suggest 5-10 specific TikTok video ideas tailored to the user. For each idea:
- **Title/hook** — The opening line
- **Format** — How to shoot it (duration, style)
- **Why it'll work** — Which pattern from the data supports it

### Step 4: Present to User

After appending the analysis, show the user:
1. The overview stats
2. The top 10 videos table
3. The content themes breakdown
4. Your top 5 suggested TikTok ideas
5. The file path where the full report lives

Ask if they want to dig deeper into any specific video, creator, or theme.

## Rules

- All output goes to `~/youtube/tiktok-research/`
- Always pass `--raw-json` so we have the data for analysis
- If the scraper costs money, mention the estimated cost from the output
- Don't hallucinate data — only analyze what the scraper actually returned
- Keep the analysis practical and actionable — this is for content planning, not academic research
- When suggesting ideas, consider what the user already makes (AI tools, Claude Code, practical tutorials)
