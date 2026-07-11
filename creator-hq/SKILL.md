---
name: creator-hq
description: Build and serve the Creator HQ dashboard - a shared home screen for a YouTube creator (and partner) showing a weekly checkup (did we create/release our target videos this week?), published videos with live stats auto-pulled from YouTube, channel KPIs, and a hand-edited production pipeline (idea to ready). Self-contained HTML, servable to an iPad over the LAN from a Raspberry Pi. Triggers on: creator hq, creator dashboard, content dashboard, youtube dashboard, show my channel dashboard, are we on track this week, did we release our videos, content home screen, studio dashboard.
argument-hint: (no args to rebuild) | "serve" | "pipeline" (help me edit the board)
allowed-tools: Bash, Read, Write, Edit
user-invocable: true
---

Build the **Creator HQ dashboard**: one self-contained `dashboard.html` that answers "are we on track this week?" at a glance, shows what's published and how it's doing, and tracks how many videos are in the pipeline. Designed as a shared home screen for a creator and a partner, viewable on a wall/desk iPad served from a Raspberry Pi over the local wifi.

## How it works (no app, no API key, no secrets)

Three small pieces, all in this skill folder:
- **`fetch_stats.py`** - pulls channel meta + recent uploads via `yt-dlp` (no API key), downloads thumbnails, writes a snapshot to `~/creator-hq/data/youtube.json`.
- **`dashboard.py`** - pure renderer. Reads the config + the snapshot + the hand-edited pipeline, computes the weekly checkup, and bakes a fully self-contained `~/creator-hq/dashboard.html` (thumbnails inlined as data URIs - works offline, passes the Artifact CSP).
- **`serve.py`** - serves `~/creator-hq` to the LAN so the iPad can open it; can auto-rebuild on an interval.

Personal data lives **outside this repo** in `~/creator-hq/` (config, pipeline, snapshot, built HTML). Nothing sensitive is committed - the channel handle and goals live in `~/creator-hq/config.json`, which is created from `config.example.json`.

## First-time setup

1. `mkdir -p ~/creator-hq`
2. Copy `config.example.json` to `~/creator-hq/config.json` and set the creator `handle` (e.g. `@YourChannel`) and weekly `goals`. Add a second creator object to `creators` later to cover a partner's channel.
3. Copy `pipeline.example.json` to `~/creator-hq/pipeline.json` and replace the example rows with real ones (or start empty: `{"videos": []}`).

## Rebuild flow

```bash
python3 ~/.claude/skills/creator-hq/fetch_stats.py     # pull latest YouTube stats
python3 ~/.claude/skills/creator-hq/dashboard.py       # render dashboard.html
open ~/creator-hq/dashboard.html                       # or serve it (below)
```

`fetch_stats.py` makes ~3 yt-dlp calls per creator (channel meta, total count, recent N with full metadata) and caches thumbnails, so a rebuild is quick after the first run.

## Serving it to the iPad (Raspberry Pi kiosk)

```bash
python3 ~/.claude/skills/creator-hq/serve.py --rebuild 30
```

Prints a `http://<pi-ip>:8080/` URL - open that in the iPad's browser (or your existing kiosk). `--rebuild 30` re-pulls YouTube + re-renders every 30 minutes; the served page also self-refreshes every 15 min via a meta tag, so the display stays current on its own. To run it unattended, add `serve.py` to the Pi's existing kiosk/startup (systemd service or `@reboot` cron).

## What's on the page (Command Center layout)

- **Weekly checkup band** - three big cards: *videos created* this week (from the pipeline's `filmed` dates) vs goal, *videos released* this week (from real YouTube upload dates) vs goal, and *ready to publish* (pipeline items in the `ready` stage). Green = goal met, amber = partial, red = none yet.
- **KPI row** - Subscribers, Total videos, Avg views (last N uploads) with a sparkline, and Top recent video.
- **Recent uploads** - thumbnail cards with live view counts, likes, publish date, and a duration/SHORT badge. Each links to the video.
- **Pipeline bar** - idea -> scripted -> filmed -> editing -> ready with a count per stage; the ready stage is highlighted green.

## The pipeline file

`~/creator-hq/pipeline.json` is hand-edited (by you or your partner). Each row:
```json
{ "title": "...", "stage": "editing", "created": "2026-07-07", "filmed": "2026-07-09", "notes": "" }
```
- `stage`: one of `idea`, `scripted`, `filmed`, `editing`, `ready`.
- `filmed` date drives the "created this week" checkup (a video "exists" once filmed). Falls back to `created` if `filmed` is null.
- Delete a row once the video is published - it then shows up automatically from YouTube.

When the user says "we filmed X" / "move X to editing" / "X is ready", update `pipeline.json` for them, then rebuild.

## Config / targets

`~/creator-hq/config.json`:
- `creators`: list of `{ name, handle }` (handle like `@YourChannel`). One for now; add more to track a partner.
- `goals.create_per_week` / `goals.release_per_week`: the weekly checkup targets.
- `week_start`: `monday` (default) or `sunday`.
- `recent_count`: how many recent uploads to pull (default 15).

## Notes
- Everything auto-pulled is real (yt-dlp), so no manual stat entry. The only hand-maintained file is the pipeline.
- The built HTML is fully self-contained (offline-safe, Artifact-safe). To preview it on the iPad instantly via claude.ai, publish `~/creator-hq/dashboard.artifact.html` as an Artifact.
- Multi-creator (a partner's channel side by side) is a future extension - the data model is already a list; v1 renders the first creator.
