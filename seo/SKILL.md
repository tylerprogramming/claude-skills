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
