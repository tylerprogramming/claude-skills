# Claude Code Skills

My personal collection of [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills — reusable slash commands that automate workflows directly from the terminal.

## What are Skills?

Skills are saved workflows for Claude Code. Instead of explaining what you want every time, you write it down once as a `SKILL.md` file, and Claude remembers how to do it. Invoke them with `/skill-name` in Claude Code.

## Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **Journal** | `/journal` | Daily standup logger with weekly summaries |
| **OPM** | `/opm` | One Punch Man workout logger — logs the 100/100/100 circuit, runs, and water to the Supabase `fitness-tracker` project, with Saitama-style coaching |
| **Nutrition** | `/nutrition` | Food logging, eating review vs targets, meal suggestions, and recipe cards on the Supabase `fitness-tracker` project |
| **OPM Graph** | `/opm-graph` | Live training dashboard (self-contained HTML) reading charts directly from the Supabase `fitness-tracker` project |
| **OPM Review** | `/opm-review` | Weekly training + nutrition review written to the `weekly_review` table |
| **Fitness** | `/fitness` | (Legacy SQLite version — superseded by `/opm` + `/nutrition`.) Track workouts and nutrition in a GitHub-style contribution grid. Powered by a full React + Hono + SQLite app (included in `fitness/app/`). |
| **Meal Plan** | `/meal-plan` | (Legacy — superseded by `/nutrition`.) Generate a weekly meal plan with shopping list from your recipe folder |
| **PRD** | `/prd` | Generate a Product Requirements Document for a new feature |
| **Quiz** | `/quiz` | Interactive quiz/coaching from any document — mock interviews, rapid fire, deep practice, study review |
| **Ralph** | `/ralph` | Convert PRDs to prd.json format for the Ralph autonomous agent system |
| **Resize** | `/resize` | Batch resize images to social media presets |
| **Remove BG** | `/rmbg` | Remove backgrounds from images to transparent PNGs |
| **Save Idea** | `/yt-save-idea` | Save a YouTube video idea to your ideas tracker |
| **Thumbnail** | `/thumbnail` | Generate YouTube thumbnails via Kie.ai (Nano Banana 2, Nano Banana Pro, Seedream 4.5) |
| **TikTok** | `/tiktok` | Research TikTok trends by hashtag via Apify — scrape, analyze, and suggest content ideas |
| **Transcribe** | `/transcribe` | Transcribe YouTube videos or local audio/video files using OpenAI Whisper |
| **YT** | `/yt-package` | Full YouTube video package — analysis, research, titles, hooks, script, description, filming guide |
| **YT Search** | `/yt-search` | Search YouTube by keywords via yt-dlp, sort by views, generate report |
| **Shorts** | `/shorts` | Weekly short-form content package: 5 short scripts (YT Shorts/TikTok/Reels) + 2 Instagram carousel outlines from yt-search research |
| **Custom GPT** | `/custom-gpt` | Build a complete Custom GPT package (system-prompt, KB files, README) from course transcripts or raw text |
| **Analytics** | `/yt-analytics` | YouTube channel analytics - views, retention, traffic sources, per-video breakdown, title/thumbnail A/B tracking |
| **YouTube** | `/yt-upload` | Upload videos to YouTube and manage existing videos via the YouTube Data API v3 (titles, descriptions, tags, thumbnails, scheduling, comments) |
| **TikTok Replier** | `/tiktok-replier` | Two-stage TikTok comment management: Apify reads comments, Playwright posts replies using a persistent logged-in browser profile |

## Installation

These are global skills. To use them, copy the skill folders to your Claude Code skills directory:

```bash
# Clone the repo
git clone https://github.com/tylerprogramming/claude-skills.git

# Copy to your Claude skills folder
cp -r claude-skills/* ~/.claude/skills/
```

### Fitness App Setup

The `/fitness` skill includes a full-stack app. After installing the skills:

```bash
cp -r ~/.claude/skills/fitness/app ~/fitness-app
cd ~/fitness-app
bun install   # or: npm install
bun run dev   # starts both React frontend and Hono API server
```

- Frontend: http://localhost:5173
- API: http://localhost:3001
- SQLite DB is auto-created at `~/fitness-app/fitness.db` on first run

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

The following are also intentionally gitignored: `*.zip` backups, `__pycache__/`, `.venv/`, and the symlinks pointing to local-only agent skills (`hyperframes*`, `gsap`, `find-skills`, `claude-design-hyperframes`).

## License

MIT — use these however you want.
