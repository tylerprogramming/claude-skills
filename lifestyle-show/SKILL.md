---
name: lifestyle-show
description: Build and open the Lifestyle OS dashboard - a self-contained HTML page with a GitHub-style movement grid, a consistency ring, four pillar cards (Fitness, Content, Reading, Business) with trend sparklines, and a today strip with smart nudges. Reads from the lifestyle Supabase project via the Supabase MCP. Triggers on: lifestyle dashboard, show my dashboard, show the grid, show my lifestyle, how am I doing, lifestyle overview, open my dashboard, my stats page.
argument-hint: (no args - rebuilds from the latest Supabase data)
allowed-tools: Bash, Read, Write, Edit
user-invocable: true
---

Build the **Lifestyle OS dashboard**: one self-contained `dashboard.html` that visualizes the whole-life OS (mission: $500K ARR by end of 2026; pillars: Content, Fitness, Reading, Business; motto: consistency over intensity). Companion to the `/lifestyle` logging skill - that one writes, this one reads.

## How it works (no app, no server, no secrets)

The renderer (`dashboard.py`) is a pure view layer: it reads a compact JSON snapshot and writes the HTML. All data comes through the Supabase MCP at build time, so the page is current as of the last rebuild and nothing sensitive (keys, tokens, the project id) is baked into the committed code or the output file.

## Rebuild flow (3 steps)

1. **Pull the snapshot.** Run `dashboard.sql` (in this folder) via the Supabase MCP against the **lifestyle** project. Use the project id from your own config (Tyler's lives in the private global CLAUDE.md / the `life-os-supabase-backend` memory - it is intentionally not in this repo). The query returns one `payload` JSON object.
2. **Write the data file.** Save that `payload` object to `~/lifestyle/data/dashboard-data.json` (create the dir if needed).
3. **Render and open.**
   ```bash
   python3 ~/.claude/skills/lifestyle-show/dashboard.py
   open ~/lifestyle/dashboard.html
   ```
   Optional args: `dashboard.py [data.json] [out.html]`.

## What's on the page

- **Movement grid** - GitHub-style, ~27 weeks. Single "did I move" signal: a day lights up if it has a run or a lift, shaded darker→brighter by how much (logged-only → one activity → two activities / long run / PR). Month labels and day rows are float-free aligned to the same 12px column geometry.
- **Consistency ring** - % of the last 30 days that were active (green ≥70, amber ≥40, red below). Plus current streak, best streak, miles this week.
- **Four pillar cards** - Fitness (total miles, 7/30-day, last run, best 5K pace, PRs, weight-to-goal, pace sparkline), Content (views, videos, subs), Reading (minutes, sessions, current book), Business (MRR, members, email subs, MRR sparkline). Sparklines show "not enough data yet" until there are ≥2 points.
- **Today strip** - calories / protein / water / caffeine vs targets, check-in status.
- **Smart nudges** - extends the canary beyond check-ins: flags days since last run/lift, an overdue weigh-in (≥7d), quiet reading (≥3d), and a missing daily check-in. These are what drive the logging habit.

## Targets
Defined at the top of `dashboard.py` (mirror `user_fitness_profile`): 2100 cal, 180g protein, 100oz water, 180 lb goal weight. Adjust there if they change.

## Notes
- The grid's single-signal design is intentional (a clean movement heatmap), not a multi-pillar grid.
- The sparse pillars (weight, reading, water) will fill in as logging continues - the nudges are designed to pull toward that.
- A daily auto-rebuild can be wired with `/schedule` so the page is always fresh on open.
