---
name: lifestyle
description: Log and track Tyler's whole-life OS - runs, lifts, meals, water, caffeine, weight, reading, business, YouTube, and the daily check-in - to the lifestyle Supabase project. Supports text, nutrition-label photos, and running-app screenshots. Triggers on: lifestyle, log workout, worked out, went running, ran, lifted weights, ate well, I had, I ate, drank water, had a coffee, caffeine, weighed in, read a chapter, daily check-in, log my day, fitness, log run, log meal.
argument-hint: [run/lift/meal/water/caffeine/weight/reading/checkin/image path]
allowed-tools: Bash, Read, Write, Glob, Edit, WebSearch
user-invocable: true
---

Log Tyler's whole life to the **lifestyle Supabase project**. This is the day-to-day logger for the Lifestyle OS (mission: $500K ARR by end of 2026; pillars: Content, Fitness, Reading, Business; motto: consistency over intensity).

## Backend (this is the source of truth)

**Supabase project `lifestyle`** (the project id lives in your own config, not in this repo), via the Supabase MCP (service role bypasses RLS). Read/write here directly - there is NO local app or file fallback anymore (the old `~/fitness-app` SQLite app and `~/fitness/data.js` were retired June 2026 and fully migrated into Supabase).

The full human-readable reference lives in `~/lifestyle/`: `README.md` (mission/pillars/rhythm), `TABLES.md` (all 19 tables + columns), `DAILY-LOGGING.md` (what to say → which table). Read those if unsure where something goes.

### Logging gotchas (read before every insert)
- **Out-of-sync id sequences:** a plain insert can throw a duplicate-key error. Always insert with an explicit id: `(select coalesce(max(id),0)+1 from <table>)`.
- **No `date` unique constraint:** never use `on conflict (date)`. Check if the day's row exists first (`select ... where date=...`), then insert or update.
- **`activity_log` macros are cumulative:** calories/protein/fat/carbs are running daily totals. When another meal is reported, GET the existing row and ADD to it - do not overwrite with just the new meal.
- **Always fill meal actuals:** when Tyler says what he ate, fill `actual_name / actual_calories / actual_protein` in `meal_plan` if a planned row exists for that date+meal_code; otherwise add the macros to `activity_log`.
- **Dates:** format `YYYY-MM-DD`. "today" = current date; handle "yesterday" / "last night" / explicit dates by targeting the right day.

## What to say → where it goes

| Tyler reports... | Table | Key columns |
|---|---|---|
| a run / cardio (or shares a run screenshot) | `cardio_log` | date, type, subtype, distance_mi, duration_min, pace_sec_mi, calories_burned, elevation_ft, avg_hr, cadence, notes, pr |
| a lift ("squats 3x8 @185") | `strength_entries` (+ `strength_sets`) | entry: exercise_id, date, notes, duration_min · sets: entry_id, set_order, weight, reps |
| daily flags + macro totals | `activity_log` | date, weights, running, ate_well, notes, calories, protein, fat, carbs |
| what he ate (planned-day) | `meal_plan` actuals | actual_name, actual_calories, actual_protein |
| weigh-in | `weight_log` | date, weight_lb, time_of_day, notes |
| water | `water_log` | date, oz, goal_oz |
| caffeine | `caffeine_log` | date, time, source, mg |
| reading session | `reading_log` | date, book, category, minutes, pages, notes |
| mood/energy/sleep / end-of-day recap | `daily_checkin` | date, mood (1-5), energy (1-5), sleep_hrs, reading_min, shipped, wins, blockers, journal |
| Skool members / MRR / weekly business | `business_weekly` | week_start, skool_members, new_signups, mrr, email_subs, videos_published, notes |
| a video's performance | `youtube_daily` | date, video_id, title, views, impressions, ctr, avg_view_pct, avg_view_sec, subs_gained, notes |
| post-mortem on a video | `video_learnings` | video_id, title, hypothesis, result_summary, diagnosis, lesson, action, status |

`exercises` (id, slug, name) is the movement catalog that `strength_entries.exercise_id` references - look up or add a slug there before inserting a lift for a new movement.

## Flow

1. **Parse** the request for what's being logged (run, lift, meal, water, caffeine, weight, reading, check-in, or an image path). Multiple things can be logged at once.
2. **Handle images** (Read the file - Claude sees images):
   - **Running-app screenshot** (Apple Fitness / Strava / Nike): extract distance, time, avg pace, calories, elevation, cadence, location → `cardio_log`. Convert pace to `pace_sec_mi` (8'28" = 508). Duration to minutes (26:19 = 26.32).
   - **Nutrition label:** extract calories/protein/fat/carbs per serving + serving size; multiply by servings eaten.
   - **Food photo:** identify the food, estimate macros if no label.
   If uncertain what an image shows, confirm before logging.
3. **Check the day's existing rows first** (GET before insert) so you merge instead of duplicate - especially `activity_log` (cumulative macros) and to avoid a second `cardio_log` for the same run.
4. **Insert/update** via the Supabase MCP using the explicit-id pattern.
5. **Confirm** what was logged (table + the human-readable summary) and, when relevant, note where the day stands (e.g. macros so far, current streak, canary status).

## Macro estimates (when no label/DB row)
- Search `nutrition_items` first (`select * from nutrition_items where name ilike '%...%'`) and reuse stored values; add new foods to it after logging.
- 5 oz cooked chicken breast ≈ 230 cal / 43g P. 1 cup cooked white rice ≈ 205 cal / 4g P / 45g C. 1 srv frozen mixed veg ≈ 60 cal / 12g C. Use WebSearch for restaurant/fast-food items.

## Caffeine reference
Coffee 8oz ≈ 95mg · Cold brew 12oz ≈ 155mg · Espresso ≈ 63mg · Pre-workout ≈ 150-200mg · Energy drink 16oz ≈ 160mg · Green tea ≈ 28mg · Black tea ≈ 47mg. Warn if a day exceeds 400mg.

## The canary rule
`daily_checkin` is the keystone and early-warning system. If it goes dark, or mood dips, for 3 days running, **ease the throttle - do not pile on more**. After time away, pull the live data, show where each pillar stands, and close today's loop. Small and current beats a grand new plan.

## Training plan
The weekly split lives in the `workout_plan` table (day_of_week 0=Sun..6=Sat). Read it for "what am I doing today/tomorrow." Month-specific plan notes may also live at `~/lifestyle/` if present.

## Showing the dashboard
To visualize this data (movement grid, consistency ring, pillar cards, nudges), use the companion **`/lifestyle-show`** skill. It rebuilds a self-contained `dashboard.html` from a fresh Supabase snapshot. Trigger it on "show my dashboard", "show the grid", "how am I doing", etc.

The deprecated React app source remains in `app/` and `templates/` for reference only - it reads the retired local SQLite, not Supabase, so do not start it.
