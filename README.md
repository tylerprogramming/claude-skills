# Claude Code Skills

My personal collection of [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills — reusable slash commands that automate workflows directly from the terminal.

## What are Skills?

Skills are saved workflows for Claude Code. Instead of explaining what you want every time, you write it down once as a `SKILL.md` file, and Claude remembers how to do it. Invoke them with `/skill-name` in Claude Code.

## Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **Journal** | `/journal` | Daily logger with three modes — a personal journal entry, a technical standup, and a full automated end-of-day (eod) report (pulls from Supabase, Skool, Blotato, YouTube) — plus weekly summaries. (Consolidates the former `/standup` and `/eod` skills.) |
| **Peeps** | `/peeps` | Personal people tracker — save details about people (birthday, how you know them, family, notes) and generate a searchable HTML page |
| **Lifestyle** | `/lifestyle` | Whole-life OS logger — runs, lifts, meals, water, caffeine, weight, reading, business, YouTube, and the daily check-in — to the `lifestyle` Supabase project via the Supabase MCP. Supports run screenshots and nutrition-label photos. (Consolidates the former `/opm`, `/nutrition`, `/opm-graph`, `/opm-review`, `/fitness`, and `/meal-plan` skills.) |
| **Lifestyle Show** | `/lifestyle-show` | Builds a self-contained `dashboard.html` for the Lifestyle OS — GitHub-style movement grid, consistency ring, four pillar cards with trend sparklines, and a today strip with smart nudges. Pure renderer: pulls a fresh snapshot via the Supabase MCP, bakes it into HTML, no secrets in the file. |
| **Creator HQ** | `/creator-hq` | Shared home-screen dashboard for a YouTube creator (and partner) — a weekly checkup (did we create/release our target videos this week?), channel KPIs, recent uploads with live stats auto-pulled from YouTube via yt-dlp (no API key), and a hand-edited production pipeline. Self-contained HTML, servable to an iPad over the LAN from a Raspberry Pi. |
| **PRD** | `/prd` | Generate a Product Requirements Document for a new feature |
| **Quiz** | `/quiz` | Interactive quiz/coaching from any document — mock interviews, rapid fire, deep practice, study review |
| **Ralph** | `/ralph` | Convert PRDs to prd.json format for the Ralph autonomous agent system |
| **Resize** | `/resize` | Batch resize images to social media presets |
| **Remove BG** | `/rmbg` | Remove backgrounds from images to transparent PNGs |
| **Save Idea** | `/yt-save-idea` | Save a YouTube video idea to your ideas tracker |
| **Thumbnail** | `/yt-thumbnail` | Generate YouTube thumbnails via Kie.ai (Nano Banana 2, Nano Banana Pro, Seedream 4.5) |
| **TikTok** | `/tiktok` | Research TikTok trends by hashtag via Apify — scrape, analyze, and suggest content ideas |
| **Transcribe** | `/transcribe` | Transcribe YouTube videos or local audio/video files using OpenAI Whisper |
| **YT** | `/yt-package` | Full YouTube video package — analysis, research, titles, hooks, script, description, filming guide |
| **YT Search** | `/yt-search` | Search YouTube by keywords via yt-dlp, sort by views, generate report |
| **Shorts** | `/yt-shorts` | Weekly short-form content package: 5 short scripts (YT Shorts/TikTok/Reels) + 2 Instagram carousel outlines from yt-search research |
| **IG Post** | `/ig-post` | Write Instagram captions from a topic in your own voice. Three angles per run (story, blunt claim, useful list), sized for a single image post, carousel, or Reel. Enforces a no-em-dash, no-AI-slang style with a `tells.py` checker that every draft has to pass before you see it. Writing only, no design or publishing |
| **Custom GPT** | `/custom-gpt` | Build a complete Custom GPT package (system-prompt, KB files, README) from course transcripts or raw text |
| **Analytics** | `/yt-analytics` | YouTube channel analytics - views, retention, traffic sources, per-video breakdown, title/thumbnail A/B tracking |
| **YouTube** | `/yt-upload` | Upload videos to YouTube and manage existing videos via the YouTube Data API v3 (titles, descriptions, tags, thumbnails, scheduling, comments) |
| **TikTok Replier** | `/tiktok-replier` | Two-stage TikTok comment management: Apify reads comments, Playwright posts replies using a persistent logged-in browser profile |
| **YouTube Replier** | `/yt-replier` | Manage YouTube comments via the official Data API v3 — monitors uploads for unreplied comments, auto-drafts Skool-link CTA replies, posts approved replies. Self-contained OAuth + data dir |

### AI Media Generation — Kie.ai

One skill per model, all sharing `_kie/kie_client.py` (need `KIE_API_KEY` in `~/.claude/.env`). See `_kie/MODELS.md` for the full model id + schema reference.

| Skill | Command | Description |
|-------|---------|-------------|
| **Kie Seedance Video** | `/kie-seedance-video` | ByteDance Seedance text-to-video + image-to-video (Seedance 2 / 2-Fast / 1.5 Pro / 1.0 Pro·Lite, optional audio) |
| **Kie Seedance Image** | `/kie-seedance-image` | ByteDance Seedream text-to-image + multi-image edit (2K/4K) |
| **Kie Kling Video** | `/kie-kling-video` | Kling (Kuaishou) text/image-to-video (2.6 / 3.0 / 2.1 Master·Pro, native sound, multi-shot) |
| **Kie Veo Video** | `/kie-veo-video` | Google Veo 3 / 3.1 video — native audio, up to 4K (Quality/Fast/Lite). Uses Kie's dedicated `/veo` endpoint |
| **Kie Wan Video** | `/kie-wan-video` | Alibaba Wan text/image-to-video (2.7 / 2.6 / 2.5, first+last frame, audio drive) |
| **Kie Nano Banana** | `/kie-nano-banana` | Google Nano Banana image gen/edit — all 3 variants (Nano Banana, 2, Pro), up to 4K |
| **Kie GPT Image** | `/kie-gpt-image` | OpenAI GPT Image 2 — text-to-image + image-to-image (up to 16 refs), 1K/2K/4K. Strong photorealism + text rendering |

### AI Media Generation — Higgsfield

Higgsfield uses the **official first-party skills** (not vendored in this repo). Install them once with:

```bash
npx skills add higgsfield-ai/skills
```

They land in `~/.agents/skills/` (symlinked to Claude Code) and authenticate via the Higgsfield CLI — run `higgsfield auth login` once (needs a Higgsfield account with credits). No API key in `.env`.

| Skill | Command | Description |
|-------|---------|-------------|
| **Higgsfield Generate** | `/higgsfield-generate` | Image/video across 30+ models (Soul V2/Cinema, Seedance 2.0, Kling 3.0, Nano Banana, GPT Image 2), image-to-image, image-to-video, Marketing Studio ads, and the Virality Predictor |
| **Higgsfield Soul ID** | `/higgsfield-soul-id` | Train a Soul Character (face/identity model) from a few photos; reuse via `--soul-id` for consistent faces |
| **Higgsfield Product Photoshoot** | `/higgsfield-product-photoshoot` | Brand-quality product imagery (studio, lifestyle, hero/banner, ad creative, virtual try-on…) |
| **Higgsfield Marketplace Cards** | `/higgsfield-marketplace-cards` | Marketplace listing images — main + secondary product shots and A+ content modules |

## Video Workflows

These are the end-to-end systems I actually run on my channel, each built from the skills above. Every one has a free companion Google Doc you can open and copy from - the skills it uses, the flow in order, and any one-time setup. Follow along with the video, grab the doc.

### 1. The YouTube Workflow

Take one YouTube video from idea to scheduled, all inside Claude Code. Research what's working, generate the full package, optimize it, make the thumbnail, cut the Shorts, and schedule the upload.

- **Skills:** `/yt-search` · `/yt-deep-research` · `/transcribe` · `/yt-package` · `/yt-seo` · `/yt-thumbnail` · `/yt-shorts` · `/yt-chapters` · `/yt-upload`
- **Doc:** https://docs.google.com/document/d/1JgGYBcrfcDhXowmYt6CRRkZATggf695ZL9umDb1ffFE/edit

### 2. Your First AI Agent

Build a real AI agent the easy way - no framework, no code, about ten minutes. The doc includes the full `SKILL.md` for a Research Agent (give it a topic, it searches the web, reads sources, writes a one-page brief). Copy it, change the topic, run it.

- **Skills / tools:** Claude Code · web search · a single `SKILL.md` (this *is* the agent)
- **Doc:** https://docs.google.com/document/d/1GWUvTLREviFxcneyqkFSSNGXnx9teyvHCZY6Ob1FC0c/edit

### 3. The Publishing Stack

Take one finished video and push it to every platform without opening a single app. Upload and schedule to YouTube, cut the short-form scripts, write the platform posts, generate the pins and carousel, and queue the newsletter - all reviewed before anything goes out.

- **Skills:** `/yt-upload` · `/repurpose` · `/social-copy` · `/pinterest-writer` · `/instagram-writer` · `/ig-post` · `/email` · `/skool` (+ Blotato for scheduling)
- **Setup:** `/yt-upload` needs a one-time `token.json` (10-min Google setup, walked through in the doc)
- **Doc:** https://docs.google.com/document/d/1u9v2Ekpxwq00i2jci5WIoyNpLpG0Ap8aJcIJlEYwYk8/edit

## Installation

Most people already have their own skills, so pick whichever of these fits.

### Option A — take the whole library

```bash
git clone https://github.com/tylerprogramming/claude-skills.git ~/.claude/skills
cd ~/.claude/skills && ./setup.sh
```

Only do this if `~/.claude/skills` is empty. It replaces the folder.

### Option B — clone anywhere, take the skills you want (recommended)

```bash
git clone https://github.com/tylerprogramming/claude-skills.git ~/projects/tyler-skills
cd ~/projects/tyler-skills && ./setup.sh
```

Then just ask Claude Code to do the rest. `CLAUDE.md` in this repo tells it how
to import a skill correctly, so you can point it at the clone and say:

> Look at ~/projects/tyler-skills and import the yt-search and transcribe
> skills into my ~/.claude/skills, then tell me what setup each one needs.

It will copy the folders, put the venv somewhere those skills can actually find
it, verify the imports, and tell you which ones still need credentials.

If you would rather do it by hand:

```bash
cp -r ~/projects/tyler-skills/yt-search ~/.claude/skills/
~/projects/tyler-skills/setup.sh --link ~/.claude/skills   # reuse the venv
~/projects/tyler-skills/setup.sh --check ~/.claude/skills  # confirm it worked
```

The scripts find their venv by looking beside themselves first and walking up a
few levels, then falling back to `~/.claude/skills/.venv`. So a copied skill
works whether the venv sits in the clone, in your own skills folder, or both.

If you copy a skill and its imports fail, you either have no venv yet or it is
missing that skill's packages. Run `./setup.sh` in whichever folder the skill
now lives in, or add the packages to your existing one.

### Checking it

```bash
./setup.sh --check     # is the venv there, and does every package import
./setup.sh --rebuild   # throw it away and build clean
```

`--check` imports each module rather than trusting that pip reported success,
so it tells you what actually works rather than what was supposed to install.

### uv, and where versions come from

`setup.sh` uses [uv](https://docs.astral.sh/uv/) when it is installed and falls
back to `python3 -m venv` plus pip when it is not. uv resolves in seconds, and
it builds an isolated environment rather than negotiating with a Homebrew Python
that marks itself externally managed (PEP 668) — the failure whose usual
workaround is `--break-system-packages`, which does exactly what it says on a
Python other things depend on.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Package versions live in **`requirements.txt`, pinned exactly**. This
environment lives on two Macs, and "works on the laptop, not the desktop" is a
debugging session nobody wants, so a fresh install resolves the same wheels
rather than whatever is newest that week. Bump a version deliberately, then run
`./setup.sh` again.

Playwright is installed as two things — the package and the Chromium build it
drives. Installing only the package gives you an import that succeeds and a
first call that fails, which reads as a bug in the skill rather than a missing
download, so `setup.sh` does both.

### Why there is a venv

Every python script here starts `#!/usr/bin/env python3`, and **`python3` is a
moving target**. A Homebrew upgrade re-points it, the packages installed for the
previous version stop being visible, and scripts fail with
`ModuleNotFoundError` while looking perfectly installed.

That is not hypothetical. It silently broke `/yt-upload`, `/yt-replier`,
`/yt-analytics`, `/gmail`, and `/creator-hq` when `python3` moved from 3.9 to
3.14: the Google API libraries were still on disk, just not reachable from the
interpreter that ran.

So the scripts do not trust `python3`. Each one that needs third-party packages
carries a short bootstrap block that re-execs it under `.venv`. Two details in
that block matter:

- it is placed after the shebang, the module docstring, **and** any
  `__future__` imports, because `from __future__` has to be the first statement
  in a file
- it compares `sys.prefix`, not the executable path. A venv's `bin/python3` is
  a symlink to the base interpreter, so comparing resolved paths matches on
  both sides and the re-exec never fires

If `.venv` is missing the block does nothing and the script runs as before, so
a fresh clone degrades to the old behaviour rather than erroring in a new way.

One shared venv rather than one per skill: `googleapiclient` alone is 99MB and
five skills need it.

### Lifestyle Backend

The `/lifestyle` skill (which consolidates the former `/fitness`, `/opm`, and `/nutrition` skills) logs to the **`lifestyle` Supabase project** via the Supabase MCP — there is no local app or server to run. The deprecated full-stack React + Hono + SQLite app source remains under `lifestyle/app/` for reference only.

## Skill Structure

Each skill has:
- `SKILL.md` — Instructions for Claude (name, description, flow)
- Optional scripts (`.py`, `.sh`) for complex operations

## Secrets & Per-User Setup

None of the secrets in this repo are committed. After cloning, you'll need to create your own:

1. **`.env`** — copy `.env.example` to `.env` and fill in your own keys (OpenAI, Kie.ai, Apify, Resend, Gmail, Skool).

2. **`/yt-upload`** — uses the YouTube Data API v3:
   - Create OAuth credentials at https://console.cloud.google.com/apis/credentials (Desktop app) and save the downloaded file to `~/credentials.json`.
   - First run: `python ~/.claude/skills/yt-upload/yt.py auth` to walk the OAuth flow. This writes `youtube/token.json` (gitignored).

3. **`/tiktok-replier`** — uses a persistent Chromium profile at `tiktok-replier/data/profile/` to stay logged into TikTok. The first run will open a browser; log in once and the session is reused. The `data/` directory (profile, queues, logs, scraped HTML) is gitignored.

4. **`/yt-analytics`** — needs its own OAuth token at `analytics/yt_token.json` (gitignored).

`.venv/` is gitignored, which is why a fresh clone needs `./setup.sh` before
any python-backed skill will run.

The following are also intentionally gitignored: `*.zip` backups, `__pycache__/`, `.venv/`, and the symlinks pointing to local-only agent skills (`hyperframes*`, `gsap`, `find-skills`, `claude-design-hyperframes`).

## License

MIT — use these however you want.
