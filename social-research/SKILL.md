---
name: social-research
description: Research a topic across social platforms (YouTube, Instagram, X, TikTok) end to end - find the top-performing content on each, read the winners' hooks, spot the cross-platform patterns and content gaps, and compile a decision-ready brief with concrete content ideas. Grounded entirely in real data from Apify + transcripts, never invented. Use when asked to research a topic, scope a niche, see what is working on social, or get content ideas across platforms.
---

# Social Media Research Agent

Given a topic, research the current landscape **across social platforms** and return a
**decision-ready brief**: what is winning on each platform, the patterns that travel across all of
them, where the gaps are, and what to make next. Every claim is grounded in real data you pull with
the tools below - never invent a title, a handle, a view count, or a trend.

## Inputs
- **topic** (required): the subject/niche, e.g. "Claude Code AI agents".
- **platforms** (optional, default `all`): any of `youtube` `instagram` `x` `tiktok`.
- **window** (optional, default "last 6 months"): recency filter.
- **depth** (optional, default `3`): how many top items per platform to read in full.

## Tools this skill uses (MCP + bundled code)
- **Apify MCP** (the flipped-on tool) - one server, every platform, pick the actor per platform:
  - YouTube: the youtube scraper (search + sort by views).
  - Instagram: the instagram scraper / reel scraper.
  - TikTok: the tiktok scraper.
  - X: the X / Twitter scraper actor.
- **`scripts/yt_transcript.py`** (this skill's OWN code): tries `yt-dlp` for a YouTube transcript.
  If it prints `YTDLP_FAILED`, fall back to Apify subtitles (yt-dlp gets 403'd a lot - Apify is the backup).

That split - the skill's own yt-dlp code PLUS the Apify MCP tools - is the point: a skill can carry
code AND call MCP tools, and they work together.

## Process (run per requested platform, then synthesize)

### 1. Find the top content (each platform)
Call the Apify actor for the platform. Search the **topic**, sort by **views/plays/engagement**,
keep to the **window**, pull ~20-30 per platform. Collect: title/caption, channel/handle,
views/plays/likes, date, url, and (video) duration. If a platform returns nothing, say so and skip it.

### 2. Rank and find the outliers (each platform)
Sort by reach. Flag **outliers** - a mid-size account massively over its own norm is a stronger
signal than a huge account's baseline. State the real numbers.

### 3. Read the winners
- **YouTube:** for the top **{depth}**, get the transcript via `python3 scripts/yt_transcript.py "<url>"`.
  On `YTDLP_FAILED`, fall back to the Apify youtube scraper with subtitles (downloadSubtitles=true,
  subtitlesFormat=plaintext). Focus on the **first ~2 minutes** (the hook).
- **Instagram / TikTok / X:** read the top posts' **hook line / first caption line** and format
  (reel vs carousel vs text, length, CTA). The opening line is where these are won.

### 4. Analyze - ground everything in the data
Per platform: **title/caption patterns**, **hook patterns**, **formats/angles that overperform**.
Then **cross-platform synthesis**: what works everywhere vs what is platform-specific.
Then **content gaps** (clear demand, weak/missing coverage) and **saturated** angles (everyone's doing it).
Only state what the data supports. If a number is not in the data, do not state it.

### 5. Compile the brief - use this exact shape
```
## Social Research Brief - {topic} ({today})
Scope: {platforms}, {N} items scanned, {window}.

### Per platform - what's winning
For each platform:
- Leaderboard (top 5): | Title/Caption | Handle | Reach | Date |
- What's working: {title/hook/format patterns, with 2 real examples}

### Cross-platform patterns
- Travels everywhere: {the angles/hooks that win on all platforms}
- Platform-specific: {what only works on one}

### Content gaps (make these)
- {underserved angle + why there is demand + which platform}

### Saturated (avoid / differentiate)
- {overdone angle}

### Content ideas (5-7), each mapped to a platform + format
1. {idea} - {platform + format} - {one-line why, tied to a gap + a proven pattern}

### Sources
- {urls / handles}
```

## Run it on a schedule
To get a fresh brief before you wake up, put the invocation on a cron or a Claude routine, e.g. a
daily job that runs this skill on your core topics and writes the brief to a file.

## Rules
- Grounded only. Real titles/handles/numbers, real quotes. No fabrication.
- If a platform or a step fails, say so and continue - a partial brief beats a made-up one.
- Keep it skimmable: tables and short bullets, not essays.
