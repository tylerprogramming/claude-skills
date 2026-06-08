---
name: opm-review
description: Generate or refresh Tyler's weekly One Punch Man training + nutrition review from the Supabase fitness-tracker project. Use when Tyler asks for a weekly recap, "how was my week", a progress review, or wants the dashboard's weekly summary refreshed with richer coaching. Reads training + nutrition, writes a row to the weekly_review table, and can enrich the auto-generated summary with real coaching prose.
---

# OPM Review — Weekly Recap

A weekly review of Tyler's training + nutrition. There are **two layers**:

1. **Automatic (always runs):** a Postgres function `generate_weekly_review(week_start)` runs every **Sunday 23:00 UTC (7pm ET)** via pg_cron (job `opm-weekly-review`) and upserts a row into `public.weekly_review`. This guarantees the numbers + a templated summary are captured even if no session is open. The dashboard reads this table.
2. **On-demand (this skill):** when Tyler asks, recompute the current/!requested week and **overwrite `summary` + `focus` with sharper, personalized coaching** based on the actual data.

- **project_id:** `mvxwtltzxkvhmvwkuzvh`

## How to run it

1. Decide the week. Default = current week's Monday: `date_trunc('week', CURRENT_DATE)::date`. For "last week" subtract 7.
2. Refresh the numbers (idempotent upsert):
   ```sql
   SELECT public.generate_weekly_review(date_trunc('week', CURRENT_DATE)::date);
   ```
3. Read the row back and the raw data behind it:
   ```sql
   SELECT * FROM weekly_review WHERE week_start = '<monday>';
   ```
   Also pull the week's `cardio_log`, `strength_entries`+`strength_sets`, `activity_log` (incl. `notes`), and compare `meal_plan` (planned) vs `activity_log` (actual) for adherence.
4. **Write better prose.** Replace the templated `summary`/`focus` with a real coach's take — tie callouts to the data (pace trend, circuit-time drop, protein consistency, run quality vs prior-day eating, junk-food days, streak). Keep it tight: a 2-3 sentence recap + 2-3 concrete focus items for next week.
   ```sql
   UPDATE weekly_review SET summary = $$...$$, focus = $$...$$ WHERE week_start = '<monday>';
   ```
5. Present the recap to Tyler in chat too (Saitama-style, like the /opm skill), and remind him `/opm-graph` shows it on the dashboard.

## What the columns mean
`active_days, streak, run_count, total_miles, avg_pace_sec_mi, best_pace_sec_mi, run_cal, circuit_days, avg_circuit_min, total_reps, logged_days, avg_calories, avg_protein, days_protein_hit (>=180g), days_over_cal (>1650), junk_days (notes mention doritos/sweet tea/mcdonald), summary, focus, metrics(jsonb)`.

Targets: ~1,650 cal / ~180g protein; OPM goal = full 100/100/100 + 10K (6.21 mi).

## Notes
- The function bypasses RLS (runs as table owner), so it always works regardless of the anon read-only policies.
- To change the schedule: `SELECT cron.alter_job((SELECT jobid FROM cron.job WHERE jobname='opm-weekly-review'), schedule := '<cron>');`
- The richer your `/opm` logging (especially filling `meal_plan.completed`/`actual_*`), the better the adherence analysis.
