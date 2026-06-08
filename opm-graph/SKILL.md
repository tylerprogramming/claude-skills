---
name: opm-graph
description: Open or rebuild Tyler's live One Punch Man training dashboard — modern charts of run distance/pace, the 100/100/100 circuit time, and daily calories/protein, pulled live from the Supabase fitness-tracker project. Use when Tyler asks to see his graphs, dashboard, progress, trends, or "how am I doing".
---

# OPM Graph — Live Training Dashboard

A single self-contained HTML dashboard that connects **directly** to Tyler's Supabase `fitness-tracker` project and renders live charts. No build step, no server — just open the file and it fetches current data every time.

- **File:** `/Users/tylerreed/opm-dashboard.html`
- **Open it:** `open /Users/tylerreed/opm-dashboard.html` (macOS default browser)
- It uses the **publishable** Supabase key (read-only-ish; RLS is disabled so it can read all tables). Connection details (URL + key) are embedded in the file.

## What it shows
- **Stat cards:** training streak, last run, best pace, OPM circuit days + total reps, total miles.
- **Run distance vs 10K goal** (dashed 6.21 mi target line).
- **Run pace** (min/mi, axis reversed so faster = up).
- **Circuit time** — the 100/100/100 completion time trend (from `strength_entries.duration_min`, reversed so faster = up).
- **Daily calories & protein** — bars vs ~1,650 cal goal, protein line vs ~180 g goal.

## How it pulls data
Live via `@supabase/supabase-js` from the CDN, querying: `cardio_log`, `strength_entries` (+`strength_sets` for reps), and `activity_log`. The "Refresh" button re-fetches without reloading.

## When to edit it
The dashboard reads whatever the `/opm` skill writes, so it usually needs no changes. Edit the HTML only to **add a chart** (e.g. water intake from `water_log`, or weekly volume). Keep the existing dark OPM theme (CSS variables at the top: `--red`, `--yellow`, `--cyan`, `--green`, `--purple`). Goals are constants near the top of the script: `CAL_GOAL`, `PROTEIN_GOAL`, `TEN_K_MI`.

## Security note
The publishable key is embedded in the HTML and all tables have **RLS disabled** — anyone who opens this file can read (and with the key, write) every row. Keep the file local; don't host it publicly or share it as-is.
