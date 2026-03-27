---
name: yt-deep-research
description: Search YouTube by keywords, transcribe the top 2 videos, and return a deep analysis of both. Triggers on: deep research, yt deep research, research and transcribe, search and transcribe youtube, deep dive youtube.
argument-hint: [keywords] [--days 30] [--top 15] [--search-count 50]
allowed-tools: Bash(python3:*), Read, Write, Glob, Grep
user-invocable: true
---

Search YouTube, transcribe the top 2 results, and deliver a deep analysis.

This skill chains `/yt-search` and `/transcribe` together automatically.

## Parsing Arguments

Parse `$ARGUMENTS` for:
- **Keywords**: One or more search terms. Required.
- **--days**: How many days back to include. Default: `30`.
- **--top**: How many top results to show. Default: `15`.
- **--search-count**: How many raw results to fetch from YouTube before filtering. Default: `50`.

If the user just provides keywords with no flags, use the defaults.

## Flow

### Step 1: Run the YouTube Search

```
python3 ~/.claude/skills/yt-search/search_youtube.py <keywords> --days <days> --top <top> --search-count <search-count> --json
```

Wait for it to finish. Read the generated JSON from `~/yt-research/`.

### Step 2: Present the Search Results

Show the user the top videos table (same as `/yt-search` output).

### Step 3: Transcribe the Top 2 Videos

Take the top 2 videos by view count from the JSON results. Run transcription on both:

```
python3 ~/.claude/skills/transcribe/transcribe_video.py "<video_url_1>"
python3 ~/.claude/skills/transcribe/transcribe_video.py "<video_url_2>"
```

Run these sequentially (not in parallel) to avoid rate limits. Read both saved transcripts from `~/scripts/`.

### Step 4: Deep Analysis

After reading both transcripts, provide a comprehensive analysis that covers:

#### Per-Video Breakdown (for each of the 2 transcribed videos)
- **Hook** (first 30 seconds): How do they open? What's the hook strategy?
- **Structure**: How is the video organized? (sections, transitions, story arc)
- **Key talking points**: The 3-5 main arguments or ideas
- **Engagement tactics**: Questions to the viewer, pattern interrupts, callbacks
- **CTA placement**: Where and how do they pitch? (mid-roll, end, soft vs hard)
- **Quotable moments**: 3-5 lines that would make great secondary text / clips

#### Cross-Video Comparison
- What do both videos have in common? (themes, structure, tone)
- Where do they differ?
- Which approach is more effective and why?

#### Content Opportunities
- What angles or subtopics are mentioned but not fully explored?
- What gaps exist that the user could fill with their own video?
- 3-5 specific video ideas based on what these creators covered (and didn't)

#### Applicable Patterns for the User
- Title patterns worth borrowing
- Hook strategies that would work for AI tools content
- Structural techniques to try

### Step 5: Save the Analysis

Save the full analysis to:
```
~/yt-research/<date>-<keywords>-deep-analysis.md
```

Include the video URLs, titles, and transcript file paths at the top for reference.

### Step 6: Present to User

Show the user:
1. The search results table
2. Which 2 videos were transcribed
3. The full deep analysis
4. File paths for the report, transcripts, and analysis

Ask if they want to dig deeper into anything specific or use either transcript for `/yt`.

## Rules

- All output goes to `~/yt-research/`
- Always pass `--json` to the search script
- Only transcribe the top 2 by view count - don't transcribe more unless the user asks
- Don't hallucinate transcript content - only analyze what Whisper actually returned
- Keep analysis practical and actionable for content planning
- When suggesting ideas, remember the user makes AI tools content (Claude Code, etc.)
- If a transcription fails (private video, age-restricted, etc.), skip it and transcribe the next one in the list
