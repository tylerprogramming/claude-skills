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
| lifestyle | Supabase project `lifestyle` (id `mvxwtltzxkvhmvwkuzvh`) via the Supabase MCP — no local files |
| journal | `~/content/journal/YYYY-MM-DD.txt` |
| transcribe | `~/content/transcripts/transcript_<id>.txt` |
| yt-package | `~/content/youtube/<video-slug>/` (analysis.md, titles.md, hooks.md, script.md, description.md, filming-guide.md, performance.md) |
| yt-analytics | `~/content/youtube/analytics/` (channel snapshots); `~/content/youtube/<slug>/performance.md` (per-video A/B tracking) |
| yt-save-idea | `~/content/youtube/video-ideas.md` |
| thumbnail | `~/content/youtube/thumbnails/` |
| tiktok | `~/content/youtube/tiktok-research/<hashtag>-report.md` |
| yt-search | `~/content/research/searches/<date>-<keywords>.md` (report); `~/content/research/_raw/` (json + thumbnails) |
| shorts | `~/content/youtube/shorts/YYYY-MM-DD/` (shorts.md, captions.md, instagram-carousels.md, filming-plan.md) |
| resize | `~/images/resized/` |
| rmbg | `~/images/nobg/` |
| email | Sends via Resend API, tracks in `~/.claude/skills/skool/data/skool.db` |
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
- `KIE_API_KEY` — thumbnail + all `/kie-*` image/video generation
- `APIFY_API_TOKEN` — TikTok scraping
- `GMAIL_ADDRESS` + `GMAIL_APP_PASSWORD` — journal email summaries

## AI Media Generation Skills

**Kie.ai** — one skill per model, all sharing `_kie/kie_client.py` so the HTTP/auth/poll/upload logic lives in one place. Unified jobs API: `createTask` → poll `recordInfo` → download `resultUrls`. Skills import the client via `sys.path.insert(0, Path(__file__).resolve().parent.parent / "_kie")` (`.resolve()` follows the `~/.claude/skills` symlink to the real repo). `_kie/MODELS.md` is the verified model-id + input-schema reference. The clients use `certifi` for SSL (macOS python.org builds don't trust the system store). Validated live (Seedream image, 2026-06-08).

| Skill | Model(s) | Output |
|-------|----------|--------|
| `/kie-seedance-video` | `bytedance/seedance-2`, `…-2-fast`, `seedance-1.5-pro`, `v1-pro/lite-*` | `~/videos/seedance/` |
| `/kie-seedance-image` | `seedream/4.5-text-to-image`, `4.5-edit`, `5-lite-text-to-image` | `~/images/seedream/` |
| `/kie-kling-video` | `kling-2.6/*`, `kling-3.0/video`, `kling/v2-1-*` | `~/videos/kling/` |
| `/kie-veo-video` | `veo3`/`veo3_fast`/`veo3_lite` (dedicated `/veo/generate` endpoint) | `~/videos/veo/` |
| `/kie-wan-video` | `wan/2-7-*`, `wan/2-6-image-to-video`, `wan/2-5-text-to-video` | `~/videos/wan/` |
| `/kie-nano-banana` | `google/nano-banana(-edit)`, `nano-banana-2`, `nano-banana-pro` | `~/images/nano-banana/` |
| `/kie-gpt-image` | `gpt-image-2-text-to-image`, `gpt-image-2-image-to-image` | `~/images/gpt-image/` |

**Higgsfield** — NOT in this repo. Uses the official first-party skills, installed separately with `npx skills add higgsfield-ai/skills` (lands in `~/.agents/skills/`, symlinked to Claude Code): `/higgsfield-generate`, `/higgsfield-soul-id`, `/higgsfield-product-photoshoot`, `/higgsfield-marketplace-cards`. They auth via the Higgsfield CLI (`higgsfield auth login`), not an API key. (An earlier hand-built `/higgsfield-*` set was removed in favor of these.)

## Python Script Conventions

- Auto-install missing packages via `pip install` in a `try/except ImportError`
- Print status messages for long-running operations
- Return data that Claude can parse (JSON or plain text)
- Accept arguments via `sys.argv`, not stdin

## Lifestyle Skill Architecture

The `lifestyle` skill (consolidating the former `fitness`, `opm`, `nutrition`, `opm-graph`, and `opm-review` skills) logs Tyler's whole-life OS to the **`lifestyle` Supabase project** (id `mvxwtltzxkvhmvwkuzvh`) via the Supabase MCP. There is no local app or file fallback — the old `~/fitness-app` SQLite app and `~/fitness/data.js` were retired June 2026 and fully migrated into Supabase.

- **Storage**: Supabase Postgres (fitness/diet + life-OS keystone + business/YouTube + planning tables).
- **Gotchas**: id sequences are out of sync → insert with explicit `(select coalesce(max(id),0)+1 from <table>)`; no `date` unique constraint → check-then-insert; `activity_log` macros are cumulative daily totals.
- **Deprecated app**: the full-stack React + Hono + SQLite source remains under `lifestyle/app/` for reference only (reads the retired SQLite, not Supabase).

## Weekly Content Pipeline

Skills that work together as a pipeline (run in this order):

```
/yt-search → /transcribe → /yt-package → /yt-seo          (long-form track)
                 ↓
             /shorts                             (short-form track — feeds from same research)
                 ↓
             /content → /yt-chapters                  (publish track — /content handles Blotato directly)
```

- `/yt-search` feeds both `/yt-package` (via transcripts) and `/shorts` (via research reports)
- `/shorts` generates 5 short scripts + 2 Instagram carousel outlines per week
- `/content` handles text posts (LinkedIn, YT Community) — separate from `/shorts`
- `/yt-chapters` runs post-edit on the final .mp4, not before filming
- `/content` handles publishing via Blotato directly (no separate post skill needed)

## Skills That Compose

- `/yt-package` calls `/thumbnail` at the end of its flow
- `/shorts` reads `/yt-search` output from `~/content/research/searches/`
- `/content` can render Instagram carousels outlined by `/shorts`
- `/yt-chapters` reuses `/transcribe`'s script for audio transcription
- `/ralph` expects an existing PRD (from `/prd`) as input

## Adding a New Skill

1. Create `~/.claude/skills/<skill-name>/SKILL.md`
2. Add Python scripts in the same folder if needed
3. Update `README.md` table
4. Add trigger phrases to the global `~/.claude/CLAUDE.md` skills table
