# Claude Code Skills

My personal collection of [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills — reusable slash commands that automate workflows directly from the terminal.

## What are Skills?

Skills are saved workflows for Claude Code. Instead of explaining what you want every time, you write it down once as a `SKILL.md` file, and Claude remembers how to do it. Invoke them with `/skill-name` in Claude Code.

## Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **Journal** | `/journal` | Daily standup logger with weekly summaries |

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
