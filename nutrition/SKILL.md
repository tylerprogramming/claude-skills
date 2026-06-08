---
name: nutrition
description: Tyler's nutrition system on the Supabase fitness-tracker project — logs food, reviews how he's eating vs targets, plans/suggests meals from his recipe library, and creates recipe cards. Use whenever Tyler reports what he ate or drank, asks what to eat, asks how his eating is going, gives food preferences, or wants a recipe created/looked up. Owns all food logging (the /opm workout skill hands off here for anything food-related).
---

# Nutrition — Tyler's Food, Review, Planning & Recipes

This skill owns Tyler's **food domain** in the Supabase `fitness-tracker` project. The `/opm` skill handles workouts and defers here for anything nutrition-related.

- **project_id:** `mvxwtltzxkvhmvwkuzvh`
- **Targets:** ~**1,650 cal** / ~**180 g protein** per day. On big OPM training days he burns a lot (circuit + run), so net calories can dip near ~1,000 — prompt a protein-forward dinner to close the gap. He's in **Tampa, FL**.

## ⚠️ Two DB gotchas (same as the other skills)
1. **Explicit IDs:** identity sequences are out of sync — insert with `id = (SELECT COALESCE(MAX(id),0)+1 FROM <table>)`, never bare DEFAULT, or it collides.
2. **Multi-statement reads:** `execute_sql` returns only the LAST statement's rows. To read several tables, use one `SELECT ... UNION ALL`, or separate calls.

## The tables
- **`nutrition_items`** (~92 foods) — the food lookup DB. Columns: `name, serving_size, calories, protein, fat, carbs, sodium, fiber, sugar`. Always search before adding: `SELECT * FROM nutrition_items WHERE name ILIKE '%korean%';`
- **`meal_plan`** (~135 rows) — planned meals per day. `date, meal_code (B/L/D/S1/S2), name, calories, protein, completed, actual_name, actual_calories, actual_protein`. B=breakfast, L=lunch, D=dinner, S1/S2=snacks.
- **`recipes`** + **`recipe_ingredients`** — 13 recipe cards. (Note: recipe **#7 "Chicken & Rice Bowl (recovered)"** is incomplete — null servings/macros/instructions; fix it if it comes up.)
- **`activity_log`** — one-row-per-day macro rollup. `date, weights, running, ate_well, notes, calories, protein, fat, carbs`. Shared with `/opm` (it sets weights/running).

---

## Job 1 — Log food
1. **Confirm the date** and read today's `activity_log` row first so you ADD to existing totals, never double-count: `SELECT * FROM activity_log WHERE date = CURRENT_DATE;`
2. **Parse what he ate.** Voice transcription is messy — if a food/word looks garbled (past example: "semen reason" = cinnamon raisin), confirm before logging. Respect exact quantities ("1.5 servings", "⅔ serving").
3. **Look up each food** in `nutrition_items`. If missing, add it (so it's reusable) then count it. Do the macro math explicitly and show a breakdown table.
4. **Update the daily rollup** in `activity_log` — UPDATE today's row adding the new cal/protein/fat/carbs, or INSERT if today has no row yet. Append a readable note of what was eaten.
5. **Mark plan-vs-actual adherence.** Map the food to its meal slot (B/L/D/S1/S2) for today and update that `meal_plan` row: set `completed=true` and fill `actual_name/actual_calories/actual_protein` with what he actually had (even if it differs from the planned meal — that's the point). Example:
   ```sql
   UPDATE meal_plan SET completed=true, actual_name='8x Wingstop Korean Q + rice',
     actual_calories=1005, actual_protein=84
   WHERE date=CURRENT_DATE AND meal_code='L';
   ```
6. **Report** a clean table + day-to-date totals (cal / protein) vs target, netting out the day's training burn when relevant (ask `/opm` data or read `cardio_log`).

## Job 2 — Review ("how am I doing?")
Pull recent `activity_log` (+ `meal_plan` for adherence, `weekly_review` for the rollup) and assess:
- **Vs targets:** avg calories & protein over the window; how many days hit ≥180 g protein / stayed near 1,650.
- **Adherence:** of planned meals, how many were `completed`; where actuals drifted from the plan.
- **Patterns:** recurring junk (Doritos / sweet tea / fast food — `notes ILIKE`), protein consistency, best vs worst days, and the known tell that his best runs follow clean-eating days.
- Keep it concrete and short: what's working, the 1–2 things to fix, tied to data.

## Job 3 — Suggest & plan
He'll give preferences ("tired of Korean flavor", "more steak", "high-protein snack under 200 cal", "lazy, no cook"). Then:
- Pull his **13 recipes** (`recipes` with category + per-serving macros) and **`nutrition_items`**, pick options that fit the request AND his macro gap for the day/week.
- Offer 2–3 ranked choices with cal/protein and effort, then (if he wants) **write/adjust `meal_plan`** rows for the target dates to hit ~1,650/180.
- **Respect his known preferences** (save new ones to memory: he's done a lot of Korean/General Tso lately; nudge variety; Doritos are a habit to swap). Honor allergies/dislikes if stated.

## Job 4 — Create recipes
Turn an idea or "here's what I made" into a proper card:
1. Break it into ingredients with `amount` + per-ingredient `calories/protein/fat/carbs` (look up each in `nutrition_items`; add any new component foods there too).
2. Insert the `recipes` row: `name, description, category (breakfast/lunch/dinner/snack), prep_time, cook_time, servings, serving_label, calories_per_serving, protein_per_serving, fat_per_serving, carbs_per_serving, instructions (numbered steps), notes`. **Per-serving macros = sum of ingredient macros ÷ servings.**
3. Insert `recipe_ingredients` rows with `sort_order` (use the explicit-id pattern for both tables; capture the recipe id with RETURNING).
4. Read it back and present it like a recipe card. Optionally add it to `meal_plan` for an upcoming day.

---

## Coaching style
Practical and brief, matching `/opm`'s Saitama-flavored tone but food-focused. Tie advice to his data and his patterns: pre-run fueling (light carbs, low fat before runs; shake AFTER), protein consistency, swapping the Doritos habit, hydration on hot Tampa run days. Don't lecture — one sharp, relevant pointer.

## Security
All tables have **RLS enabled, read-only for the anon key** — your MCP writes use the service role and bypass it, so logging works fine. Don't expose the service role; the publishable key can only read.
