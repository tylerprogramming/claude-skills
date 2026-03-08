# Claude Code Skills

My personal collection of [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills — reusable slash commands that automate workflows directly from the terminal.

## What are Skills?

Skills are saved workflows for Claude Code. Instead of explaining what you want every time, you write it down once as a `SKILL.md` file, and Claude remembers how to do it. Invoke them with `/skill-name` in Claude Code.

## Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **Journal** | `/journal` | Daily standup logger with weekly summaries |
| **Fitness** | `/fitness` | Track workouts and nutrition in a GitHub-style contribution grid with image analysis support |
| **Meal Plan** | `/meal-plan` | Generate a weekly meal plan with shopping list from your recipe folder |
| **Post** | `/post` | Post to social media via Blotato MCP (Twitter, LinkedIn, Instagram, etc.) |
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

## Installation

These are global skills. To use them, copy the skill folders to your Claude Code skills directory:

```bash
# Clone the repo
git clone https://github.com/tylerprogramming/claude-skills.git

# Copy to your Claude skills folder
cp -r claude-skills/* ~/.claude/skills/
```

## Skill Structure

Each skill has:
- `SKILL.md` — Instructions for Claude (name, description, flow)
- Optional scripts (`.py`, `.sh`) for complex operations

## License

MIT — use these however you want.
