---
name: seo
description: Optimize YouTube titles, descriptions, and tags using competitive research. Analyzes top-performing videos on the topic, identifies keyword patterns and CTR hooks, and generates SEO-optimized titles with scorecards. Optionally generates social media titles. Triggers on: seo optimize, optimize title, youtube seo, optimize description, title ideas, seo this video, improve my title.
argument-hint: [topic or ~/youtube/<slug>/]
allowed-tools: Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, AskUserQuestion
user-invocable: true
---

Optimize YouTube SEO for the video topic or package at $ARGUMENTS.

## Workflow Context

**Step 4 of the weekly content pipeline** (after `/yt`). Run once per long-form video package. After this, run `/content` to generate the LinkedIn + YT Community text posts for that video.

## Data Location

- If a video package exists at `~/youtube/<slug>/`: updates `titles.md` and `description.md` in place (adds SEO section)
- Standalone: outputs to `~/youtube/<slug>/seo.md`

## Flow

### Step 1: Gather Context

Determine the input:

- **Video package path** (`~/youtube/<slug>/`): Read `titles.md`, `script.md`, `description.md`, and `analysis.md` if they exist
- **Topic/title string**: Use it directly as the starting point
- **No argument**: Ask the user for their video topic or title

Extract:
- The core topic and primary keyword
- Any existing titles to improve on
- The video's key points and value proposition (from script if available)

Check if `--social` flag is present in $ARGUMENTS — if so, also generate social media titles in the output.

### Step 2: Competitive Research (WebSearch)

This step is NOT optional — always do real research. Run at least 5-6 searches:

1. **Top videos on this topic**: Search `"<topic>" site:youtube.com` and `<topic> youtube` to find the top-performing videos
2. **Title patterns**: Search for variations of the topic to see how different creators title similar content
3. **YouTube autocomplete**: Search `<topic> youtube autocomplete suggestions` and `<topic> how to / vs / best / tutorial` to find what people actually search for
4. **Related keywords**: Search for synonyms, related terms, and long-tail variations
5. **Trending angles**: Search for recent news/developments about the topic that could inform timely title angles
6. **Competitor analysis**: Search for the top creators in this niche and analyze their title patterns

For each search, note:
- Video titles that appeared
- View counts where visible
- Common keywords and phrases
- Title formulas being used (How to X, X vs Y, I tried X, etc.)

Present a **research summary** to the user:
- Top 10-15 competitor titles with view counts
- Most common keywords (ranked by frequency)
- Title formulas that appear to perform well
- Content gaps — angles nobody is using

### Step 3: Generate SEO-Optimized Content

#### Title Options (5 titles)

For each title:
- **The title** — Under 70 characters (YouTube truncates after that)
- **Character count** — Show the exact count
- **CTR formula used** — Name the technique (curiosity gap, specific number, how-to, comparison, bold claim, etc.)
- **Primary keyword** — What search term this targets
- **Why it works** — One sentence on the psychology/SEO reasoning

Rules for titles:
- Front-load the most important keyword in the first 40 characters
- Never use clickbait the video can't deliver on
- Include at least one title using a number/specific claim
- Include at least one curiosity-driven title
- Include at least one direct/search-optimized title
- Avoid overused words: "INSANE", "CRAZY", "YOU WON'T BELIEVE"

#### Title Scorecard

Rate each title on a 1-5 scale:

| Title | Curiosity | Specificity | SEO Strength | Click Factor | Total |
|-------|-----------|-------------|--------------|--------------|-------|

- **Curiosity (1-5)** — Does it create an information gap the viewer wants to close?
- **Specificity (1-5)** — Does it promise something concrete vs vague?
- **SEO Strength (1-5)** — Does it contain high-volume searchable keywords?
- **Click Factor (1-5)** — Would YOU click this in a sea of other thumbnails?

Mark the recommended title with the highest total score.

#### Optimized Description

- **First 2 lines** — These show in search results. Front-load keywords and value proposition. No fluff.
- **Body** — Natural keyword density (2-3% target keyword occurrence). Include related keywords organically.
- **Chapters section** — `00:00 - Title` format (use placeholders if timestamps unknown, mark with [UPDATE])
- **Links section** — Placeholder for relevant links
- **Tags line** — Keywords at the bottom for additional SEO signal

If an existing `description.md` exists, add a `## SEO-Optimized Version` section rather than replacing the original.

#### Tags (15-20)

Organize tags in three tiers:
1. **Exact match** (3-5) — The exact phrases people search for
2. **Broad match** (5-7) — Related topics and category terms
3. **Long-tail** (5-8) — Specific, lower-competition phrases

#### Social Media Titles (if `--social` flag)

Generate platform-native titles:
- **LinkedIn headline** — Professional, insight-driven (under 150 chars). Focus on the lesson or takeaway, not the video.
- **TikTok/Reels caption** — Short, punchy, hook-first (under 100 chars). Create urgency or curiosity.
- **Twitter/X post** — Under 280 chars, curiosity-driven. Make it a standalone insight that happens to link to a video.

Rules for social titles:
- These should NOT just be the YouTube title copy-pasted
- Each platform has different psychology — LinkedIn = professional growth, TikTok = entertainment/discovery, Twitter = hot takes/insights
- The social title should make the content feel native to that platform
