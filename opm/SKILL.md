---
name: opm
description: One Punch Man workout logger for Tyler's Supabase fitness-tracker. Use whenever Tyler reports a workout — the 100/100/100 bodyweight circuit, a run, or lifting. Logs the OPM strength circuit, runs, and water into Supabase, then gives Saitama-style motivation + one practical tip tied to that day's training. For anything food-related (what he ate, what to eat, recipes, nutrition review) hand off to the **/nutrition** skill.
---

# OPM — One Punch Man Workout Logger

Tyler is doing the **One Punch Man (OPM) challenge** — Saitama's routine — layered on top of a weekly lifting/run split. This skill captures his **workouts** in the Supabase `fitness-tracker` project and coaches him through them. **Food/nutrition lives in the `/nutrition` skill** — defer there for meals, macros, recipes, and "what should I eat".

**The OPM daily circuit:** 100 push-ups · 100 sit-ups · 100 bodyweight squats · 10 km run. Tyler scales reps/distance to how he feels (heat, fatigue). Log what he *actually* did — never round up or assume he hit the full target.

## Project & connection

- **Supabase project:** `fitness-tracker`
- **project_id:** `mvxwtltzxkvhmvwkuzvh`
- Use the `mcp__claude_ai_Supabase__execute_sql` tool with that project_id for all reads/writes.
- **Gotcha:** when a query has multiple statements, the tool returns ONLY the last statement's result set. To inspect several tables at once, combine them into one `SELECT ... UNION ALL ...`, or run separate calls — don't trust a "no rows" read that was actually just shadowed by a later statement. (This caused a duplicate-run insert once because pre-existing `cardio_log` rows looked empty.)
- **Today's date** comes from the session context — always confirm it before writing (`SELECT CURRENT_DATE;` if unsure). Tyler is in **Tampa, FL** (hot — heat matters for run advice).

## ⚠️ ID sequences are unreliable

Rows in this DB were historically inserted with explicit IDs, so the identity sequences are out of sync and a plain `INSERT ... DEFAULT` may collide. **Always insert with an explicit id** computed inline:

```sql
INSERT INTO <table> (id, ...)
VALUES ((SELECT COALESCE(MAX(id),0)+1 FROM <table>), ...);
```

(Exception: `cardio_log` uses a normal serial sequence that works — but the explicit pattern is safe everywhere, so prefer it.)

## Tables & how to log each thing

### 1. OPM bodyweight circuit → `strength_entries` + `strength_sets`
The 100/100/100 must be logged structurally now (not just chat notes). Exercise IDs already seeded:
- push-up = **21**, sit-up = **22**, bodyweight squat = **2**, pull-up = **10**, plank = **23**

For each movement Tyler did, create one `strength_entries` row, then its sets in `strength_sets`. For the OPM circuit he typically does straight reps (e.g. "100 push-ups"), so log a single set with `reps=100, weight=NULL` (or weight = vest lbs if he wore a weighted vest). **`strength_entries.duration_min`** holds the whole-circuit completion time — set the same value on all 3 movement rows for that day (the dashboard reads it for the "Circuit Time" trend).

```sql
-- one entry per movement (duration_min = total circuit minutes, repeated per row)
INSERT INTO strength_entries (id, exercise_id, date, duration_min, notes)
VALUES ((SELECT COALESCE(MAX(id),0)+1 FROM strength_entries), 21, CURRENT_DATE, 16, 'OPM circuit')
RETURNING id;
-- then its set(s) using that entry id
INSERT INTO strength_sets (id, entry_id, set_order, weight, reps)
VALUES ((SELECT COALESCE(MAX(id),0)+1 FROM strength_sets), <entry_id>, 1, NULL, 100);
```

Note in `strength_entries.notes` if it was broken into mini-sets or done in a weighted vest. He does **strength before the run** — worth noting on the run if fatigue affected it.

After logging a workout, remind Tyler he can run **`/opm-graph`** to see the updated charts.

### 2. Runs → `cardio_log`
Columns: `date, type('run'), subtype, distance_mi, duration_min, pace_sec_mi, calories_burned, elevation_ft, avg_hr, cadence, notes, pr`. Pull numbers from the screenshot Tyler shares (distance, time, pace, calories, elevation, cadence). Set `pr=true` only if it genuinely beats his prior best for that distance — check first.

```sql
INSERT INTO cardio_log (date, type, subtype, distance_mi, duration_min, pace_sec_mi, calories_burned, elevation_ft, cadence, notes)
VALUES (CURRENT_DATE, 'run', 'OPM 10k', 3.97, 45.13, 681, 559, 77, 139, 'cut short — Tampa heat');
```

### 3. Water → `water_log`
`date, oz, goal_oz`. One row per day; default goal ~100 oz (higher on run days in Tampa heat). Encourage logging it — Tyler rarely does, and dehydration is his #1 run-quality issue.

### Daily activity flags → `activity_log`
`activity_log` is the one-row-per-day rollup that `/nutrition` owns (it carries the macros + notes). When you log a workout, just make sure today's row reflects training: set `weights=true` and/or `running=true` (UPDATE if the row exists, else INSERT with the explicit-id pattern). Leave calories/protein to `/nutrition`.

### 🍽️ Food, meals, recipes → hand off to `/nutrition`
Do **not** log food here. If Tyler reports what he ate, asks what to eat, wants a recipe, or asks how his eating is going, that's the **`/nutrition`** skill (it owns `nutrition_items`, `meal_plan`, `recipes`, and the macros in `activity_log`). Mention it and switch over.

## Workflow when invoked

1. **Confirm the date** before writing (`SELECT CURRENT_DATE;` if unsure).
2. **Parse the workout.** Voice transcription is messy and quantities matter — log what he *actually* did ("just over 8k of the 10k", "100/100/100 in 16 min"), never round up to the OPM target.
3. **Write to the right tables** (circuit → `strength_entries`/`strength_sets`, run → `cardio_log`, water → `water_log`, set the training flags on `activity_log`) using the explicit-id pattern.
4. **Report back**: a clean table of what was logged, note PRs or the circuit-time trend, and remind him `/opm-graph` shows the charts.
5. **Coach (Saitama-style hype + one tip).** Keep it short. Tie the tip to the actual training — pre-run fueling if fat-heavy before a run, hydration/electrolytes on hot run days, run-first-then-circuit when fatigue hurt the run. Don't lecture; one sharp pointer. (Defer food specifics to `/nutrition`.)

## Coaching cheat-sheet (his known patterns)

- **Pre-run fuel:** light carbs 45–60 min out (banana, rice, plain toast). Keep fat/protein low right before; save the whey shake for *after*. He's run on eggs+butter and felt awful.
- **Hydration:** Tampa June heat is brutal. Pre-load 16–20 oz before; carry a handheld flask; Liquid IV / pinch of salt for electrolytes. Heavy legs mid-run = often electrolytes, not just water.
- **Order:** doing 100/100/100 *before* the run leaves him pre-fatigued. On hard run days, suggest running first, circuit after.
- **Diet tells:** his best runs (3K/5K PRs) came on clean eating days (chicken, rice, veggies, shakes). Rough runs follow Doritos / sweet tea / fast food. Doritos are a recurring snack — nudge toward a wrap or yogurt.
- **Weighted vest:** great for the indoor circuit (very OPM/Saitama). Skip it on outdoor Tampa runs until fall — it traps heat.

## Targets
~1,650 cal / ~180 g protein on a normal day. On big OPM days (circuit + long run) he burns a lot, so net calories can dip near ~1,000 — prompt him to eat a real, protein-forward dinner to close the gap.

## Security note
RLS is **enabled** with read-only anon policies. Your MCP writes use the service role (bypasses RLS) so logging works. The publishable key can read but not write — don't expose the service role.
