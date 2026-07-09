---
name: yt-search
description: Search YouTube by keywords using yt-dlp. Finds recent videos, splits them into long-form and Shorts, ranks each by views, downloads thumbnails, and writes a research report to ~/content/research/. Use whenever the user wants to research what's working on YouTube for a topic, scout competitors, find proven angles, or kick off the weekly content pipeline. Triggers on: youtube search, search youtube, yt search, what's trending on youtube, youtube research, research this topic on youtube, what's working on youtube, scout videos about.
argument-hint: [keywords] [--days 30] [--top 15] [--search-count 50] [--short-max 60]
allowed-tools: Bash(python3:*), Read, Write, Glob, Grep
user-invocable: true
---

Search YouTube for videos matching the given keywords and turn the results into an actionable research report.

## Workflow Context

**Step 1 of the weekly content pipeline.** Run this first — its output feeds everything else:
- `/transcribe` uses the top long-form URLs to get reference transcripts for `/yt-package`
- `/yt-shorts` reads the research reports from `~/content/research/` to generate short-form scripts (it cares about the Shorts section)
- `/yt-package` uses the transcripts + research context to plan the long-form video (it cares about the long-form section)

Run once per topic per week. Two topics = two `/yt-search` runs.

## Parsing Arguments

Parse `$ARGUMENTS` for:
- **Keywords**: One or more search terms. Required.
- **--days**: How many days back to include. Default: `30`.
- **--top**: How many top results to show **per section**. Default: `15`.
- **--search-count**: How many raw results to fetch from YouTube before filtering. Default: `50`. Increase to 100+ for broad topics.
- **--short-max**: Max duration in seconds for a video to count as a Short. Default: `60`. Bump to `180` to capture YouTube's longer Shorts.

If the user just provides keywords with no flags, use the defaults.

## Flow

### Step 1: Run the Search

```
python3 ~/.claude/skills/yt-search/search_youtube.py <keywords> --days <days> --top <top> --search-count <search-count> --json
```

This single command does everything mechanical:
- Searches YouTube via yt-dlp for recent videos matching the keywords
- Filters to videos uploaded within the timeframe and whose title matches the keywords
- **Splits results into two ranked sections — Long-form and Shorts** — each sorted by view count
- Saves a markdown report to `~/content/research/<date>-<keywords>.md`
- Saves raw JSON to `~/content/research/<date>-<keywords>.json`
- **Downloads thumbnails automatically** to `~/content/research/<date>-<keywords>-thumbnails/`, named `long-NN-<id>.jpg` and `short-NN-<id>.jpg`

Wait for it to finish. The script already handles the output folder and thumbnails — do **not** re-run yt-dlp to fetch thumbnails again; that work is done. If it fails, check that `yt-dlp` is installed (`yt-dlp --version`).

### Step 2: Read the Report and Thumbnails

Read the generated markdown report and the raw JSON from `~/content/research/`. The thumbnails are already on disk in the `-thumbnails/` folder. Show the user the top 3-5 thumbnails from the **section they care about** (long-form by default — ask if it's a Shorts research run) by referencing the actual `.jpg` files so they render.

### Step 3: Analysis

This is the part that matters — the user can read a table themselves; what they need from you is the pattern recognition they can act on. Read the JSON and the thumbnails, then deliver analysis that is concrete and grounded in the actual data. Cite specific videos by title and view count. Never invent numbers.

Keep long-form and Shorts analysis separate where it makes sense — what works as a Short rarely maps 1:1 to a long-form video.

#### Thumbnail Analysis
Look at the downloaded thumbnails (don't guess from titles). For the top performers:
- Face vs no face? Expression? Text overlay style, length, and placement? Color scheme and contrast? Arrows, circles, brackets, product UI?
- What reads clearly at the small mobile size where the click actually happens?
- Recommend 2-3 specific thumbnail directions for the user's next video, tied to what the data shows is working.

#### Title Patterns
- Recurring words, hooks, and structures in the top titles (numbers, brackets, "I built…", tool-vs-tool, dollar outcomes).
- Title length patterns of the winners.
- Cross-check against the user's proven formula (specific number + specific outcome + specific tool — see global CLAUDE.md). Call out which top titles follow it.

#### Content & Performance Patterns
- View/like/comment ranges per section; which channels appear more than once (and why they might be winning).
- Dominant formats (tutorial, build-along, news, reaction, listicle) and the durations that perform.
- Note any outlier — a video massively over-indexing its channel's norm is a signal worth naming.

#### Opportunities (the payoff)
- Underserved angles: what's getting searched/made but done poorly, or not made at all.
- 3-5 specific video ideas the user could film, each with a working title in their formula and a one-line reason it would land. Bias toward AI-tools content (Claude Code, etc.) since that's the channel.
- Separate the long-form ideas from the Shorts ideas.

### Step 4: Present to User

Show, in this order:
1. Headline stats (videos found, long-form vs Shorts counts, view ranges)
2. The top long-form table, then the top Shorts table
3. The top 3-5 thumbnails (actual images) for the relevant section
4. Thumbnail + title pattern analysis
5. Your top 3-5 video ideas, split long-form vs Shorts, each with a formula-fit title
6. The file paths: report, JSON, and thumbnails folder

Then ask if they want to dig into a specific video, channel, or trend, or kick off `/transcribe` on the top long-form results.

## Rules

- All output goes to `~/content/research/` — the script defaults there, so don't override `--output-dir` unless asked
- Report filenames include today's date: `<YYYY-MM-DD>-<keywords>.md`
- Always pass `--json` so the analysis has structured data to work from
- Thumbnails are `.jpg` and already downloaded by the script — reference them, don't re-fetch
- Don't hallucinate data — only analyze what yt-dlp actually returned; cite titles and real view counts
- Keep the analysis practical and actionable — this is for content planning, not a stats dump
- The user makes AI-tools content (Claude Code, AntiGravity, etc.) — weight ideas and patterns toward that
- Never use em dashes in any saved or presented content — use a plain hyphen with spaces or a comma
