# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A collection of Claude Code skills — reusable slash commands (`/skill-name`) that automate workflows. Each skill lives in its own folder with a `SKILL.md` (instructions) and optional Python scripts.

## Skill Structure

Every skill folder contains:
- **`SKILL.md`** — Required. YAML front matter + step-by-step instructions Claude follows.
- **Python scripts** — Optional. Used for heavy lifting (API calls, image processing, transcription).

### SKILL.md Front Matter

```yaml
---
name: skill-name
description: What it does and trigger phrases
argument-hint: Optional hint for parameters
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep, WebSearch, ...]
user-invocable: true
---
```

The `description` field controls trigger matching — it should include natural-language phrases users would say.

## Output Directories

Skills write to these home directory locations (create them if they don't exist):

| Skill | Output Location |
|-------|----------------|
| fitness | `~/fitness-app/fitness.db` (SQLite, auto-created); `~/fitness/` fallback HTML files |
| journal | `~/journal/YYYY-MM-DD.txt` |
| transcribe | `~/scripts/transcript_<id>.txt` |
| yt | `~/youtube/<video-slug>/` (analysis.md, titles.md, hooks.md, script.md, description.md, filming-guide.md) |
| save-idea | `~/youtube/video-ideas.md` |
| thumbnail | `~/youtube/thumbnails/` |
| tiktok | `~/youtube/tiktok-research/<hashtag>-report.md` |
| yt-search | `~/yt-research/<date>-<keywords>.md` |
| shorts | `~/youtube/shorts/YYYY-MM-DD/` (shorts.md, captions.md, instagram-carousels.md, filming-plan.md) |
| resize | `~/images/resized/` |
| rmbg | `~/images/nobg/` |
| prd | `tasks/prd-<name>.md` |

## Environment Variables

All API keys live in `~/.claude/.env`. When writing Python scripts, load from there:

```python
from pathlib import Path
env_path = Path.home() / ".claude" / ".env"
# parse key=value pairs
```

Required keys (see `.env.example`):
- `OPENAI_API_KEY` — Whisper transcription
- `KIE_API_KEY` — thumbnail generation
- `APIFY_API_TOKEN` — TikTok scraping
- `GMAIL_ADDRESS` + `GMAIL_APP_PASSWORD` — journal email summaries

## Python Script Conventions

- Auto-install missing packages via `pip install` in a `try/except ImportError`
- Print status messages for long-running operations
- Return data that Claude can parse (JSON or plain text)
- Accept arguments via `sys.argv`, not stdin

## Fitness Skill Architecture

The fitness skill uses a full-stack app at `fitness/app/` (React + Vite frontend, Hono/Bun backend, SQLite database). The app is included in the repo — copy it to `~/fitness-app/` and run `bun install && bun run dev` to start.

- **Primary storage**: SQLite at `~/fitness-app/fitness.db` via Hono API (port 3001)
- **Fallback**: `~/fitness/data.js` and `strength.js` use `window.FITNESS_DATA` format for browser rendering in `tracker.html` — do not convert to JSON
- **Tables**: `activity_log`, `meal_plan`, `nutrition_items`, `exercises`, `strength_entries`, `strength_sets` — all auto-created on first run via `CREATE TABLE IF NOT EXISTS`

## Weekly Content Pipeline

Skills that work together as a pipeline (run in this order):

```
/yt-search → /transcribe → /yt → /seo          (long-form track)
                 ↓
             /shorts                             (short-form track — feeds from same research)
                 ↓
             /content → /chapters                  (publish track — /content handles Blotato directly)
```

- `/yt-search` feeds both `/yt` (via transcripts) and `/shorts` (via research reports)
- `/shorts` generates 5 short scripts + 2 Instagram carousel outlines per week
- `/content` handles text posts (LinkedIn, YT Community) — separate from `/shorts`
- `/chapters` runs post-edit on the final .mp4, not before filming
- `/content` handles publishing via Blotato directly (no separate post skill needed)

## Skills That Compose

- `/yt` calls `/thumbnail` at the end of its flow
- `/shorts` reads `/yt-search` output from `~/yt-research/`
- `/content` can render Instagram carousels outlined by `/shorts`
- `/chapters` reuses `/transcribe`'s script for audio transcription
- `/ralph` expects an existing PRD (from `/prd`) as input

## Adding a New Skill

1. Create `~/.claude/skills/<skill-name>/SKILL.md`
2. Add Python scripts in the same folder if needed
3. Update `README.md` table
4. Add trigger phrases to the global `~/.claude/CLAUDE.md` skills table
