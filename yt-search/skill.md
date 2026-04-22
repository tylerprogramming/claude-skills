---
name: yt-search
description: Search YouTube by keywords using yt-dlp. Finds recent videos, sorts by views, and generates a markdown report with full metadata. Triggers on: youtube search, search youtube, yt search, what's trending on youtube, youtube research.
argument-hint: [keywords] [--days 30] [--top 15] [--search-count 50]
allowed-tools: Bash(python3:*), Read, Write, Glob, Grep
user-invocable: true
---

Search YouTube for videos matching the given keywords.

## Workflow Context

**Step 1 of the weekly content pipeline.** Run this first — its output feeds everything else:
- `/transcribe` uses the top video URLs to get reference transcripts for `/yt`
- `/shorts` reads the research reports from `~/yt-research/` to generate short-form scripts
- `/yt` uses the transcripts + research context to plan the long-form video

Run once per topic per week. Two topics = two `/yt-search` runs.

## Parsing Arguments

Parse `$ARGUMENTS` for:
- **Keywords**: One or more search terms. Required.
- **--days**: How many days back to include. Default: `30`.
- **--top**: How many top results to show. Default: `15`.
- **--search-count**: How many raw results to fetch from YouTube before filtering. Default: `50`. Increase to 100+ for broad topics.

If the user just provides keywords with no flags, use the defaults.

## Flow

### Step 1: Run the Search

```
python3 ~/.claude/skills/yt-search/search_youtube.py <keywords> --days <days> --top <top> --search-count <search-count> --json
```

This will:
- Search YouTube via yt-dlp for recent videos matching the keywords
- Filter to only videos uploaded within the specified timeframe
- Sort by view count (highest first)
- Save a markdown report to `~/yt-research/<date>-<keywords>.md`
- Save raw JSON to `~/yt-research/<date>-<keywords>.json`

Wait for it to finish. If it fails, check that `yt-dlp` is installed.

### Step 2: Download Thumbnails

After the search completes, download thumbnails for the top results. Create a thumbnails folder for this search:

```bash
mkdir -p ~/yt-research/<date>-<keywords>-thumbnails
```

For each video in the top results, download its thumbnail using yt-dlp:

```bash
yt-dlp --write-thumbnail --skip-download --convert-thumbnails png -o "~/yt-research/<date>-<keywords>-thumbnails/%(playlist_index)s-%(id)s" "https://youtu.be/<video_id>"
```

This saves each thumbnail as a PNG named with the rank number and video ID (e.g., `01-ntDIxaeo3Wg.png`).

After downloading, show the user a few of the top thumbnails so they can see what's working visually. Note any patterns:
- Clean vs busy designs
- Face vs no face
- Text placement and style
- Color schemes
- Arrows, circles, or other visual elements

### Step 3: Read the Report

Read the generated markdown report from `~/yt-research/`. Present the summary table to the user.

### Step 4: Analysis

Read the raw JSON file and provide analysis. Your analysis MUST include:

#### Thumbnail Analysis
- What visual patterns do the top-performing thumbnails share?
- Face vs no face? Text overlay style? Color schemes?
- What makes them clickable at small sizes?
- Recommend 2-3 thumbnail approaches for Tyler's video based on what's working
- Reference the downloaded thumbnails at `~/yt-research/<date>-<keywords>-thumbnails/`

#### Performance Overview
- Total videos found vs. the top N shown
- View count range (highest to lowest)
- Average views, likes, and comments across results

#### Content Patterns
- What video formats dominate? (tutorials, reviews, news, podcasts, etc.)
- What durations perform best?
- Which channels appear multiple times?

#### Title & Thumbnail Patterns
- Common words/phrases in top-performing titles
- Title length patterns
- Use of numbers, brackets, emojis, power words

#### Opportunities
- What angles or topics are underrepresented?
- What could the user make that would stand out?
- Suggested video ideas based on gaps in the results

### Step 5: Present to User

Show the user:
1. The summary stats
2. The top videos table
3. The top 3-5 thumbnails (show the actual images)
4. Thumbnail analysis (patterns, what's working)
5. Key content patterns
6. Your top 3-5 video ideas based on the data
7. The file paths: report, JSON, and thumbnails folder

Ask if they want to dig deeper into any specific video, channel, or trend.

## Rules

- All output goes to `~/yt-research/`
- Report filenames include today's date: `<YYYY-MM-DD>-<keywords>.md`
- Always pass `--json` so we have the data for analysis
- Don't hallucinate data — only analyze what yt-dlp actually returned
- Keep the analysis practical and actionable — this is for content planning
- When suggesting ideas, consider that the user makes AI tools content (Claude Code, etc.)
