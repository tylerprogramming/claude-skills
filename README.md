# Claude Code Skills

My personal collection of [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills — reusable slash commands that automate workflows directly from the terminal.

## What are Skills?

Skills are saved workflows for Claude Code. Instead of explaining what you want every time, you write it down once as a `SKILL.md` file, and Claude remembers how to do it. Invoke them with `/skill-name` in Claude Code.

## Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **Journal** | `/journal` | Daily standup logger with weekly summaries |
| **Fitness** | `/fitness` | Track workouts and nutrition in a GitHub-style contribution grid. Powered by a full React + Hono + SQLite app (included in `fitness/app/`). Falls back to static HTML when the server isn't running. |
| **Meal Plan** | `/meal-plan` | Generate a weekly meal plan with shopping list from your recipe folder |
| **PRD** | `/prd` | Generate a Product Requirements Document for a new feature |
| **Quiz** | `/quiz` | Interactive quiz/coaching from any document — mock interviews, rapid fire, deep practice, study review |
| **Ralph** | `/ralph` | Convert PRDs to prd.json format for the Ralph autonomous agent system |
| **Resize** | `/resize` | Batch resize images to social media presets |
| **Remove BG** | `/rmbg` | Remove backgrounds from images to transparent PNGs |
| **Save Idea** | `/save-idea` | Save a YouTube video idea to your ideas tracker |
| **Thumbnail** | `/thumbnail` | Generate YouTube thumbnails via Kie.ai (Nano Banana 2, Nano Banana Pro, Seedream 4.5) |
| **TikTok** | `/tiktok` | Research TikTok trends by hashtag via Apify — scrape, analyze, and suggest content ideas |
| **Transcribe** | `/transcribe` | Transcribe YouTube videos or local audio/video files using OpenAI Whisper |
| **YT** | `/yt` | Full YouTube video package — analysis, research, titles, hooks, script, description, filming guide |
| **YT Search** | `/yt-search` | Search YouTube by keywords via yt-dlp, sort by views, generate report |
| **Shorts** | `/shorts` | Weekly short-form content package: 5 short scripts (YT Shorts/TikTok/Reels) + 2 Instagram carousel outlines from yt-search research |
| **Custom GPT** | `/custom-gpt` | Build a complete Custom GPT package (system-prompt, KB files, README) from course transcripts or raw text |

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

## License

MIT — use these however you want.
