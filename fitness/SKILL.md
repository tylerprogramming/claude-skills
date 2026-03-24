---
name: fitness
description: Track workouts, nutrition, eating, water, and caffeine with a GitHub-style grid. Log weights, running, food intake, water oz, or caffeine mg for any day. Supports text input, nutrition label photos, running app screenshots, and multi-day updates. Triggers on: fitness, log workout, worked out, went running, lifted weights, ate well, fitness show, I had, I ate, drank water, had a coffee, drank oz, caffeine.
argument-hint: [weights/running/ate well/food items/image path/show]
allowed-tools: Bash, Read, Write, Glob, Edit, WebSearch
user-invocable: true
---

Track workouts, nutrition, and eating in a GitHub-style contribution grid.

## App Architecture

The fitness tracker is a full-stack app included in this skill at `fitness/app/`.

### First-time install
```bash
cp -r ~/.claude/skills/fitness/app ~/fitness-app
cd ~/fitness-app
bun install   # or: npm install
bun run dev   # or: npm run dev
```

- **Frontend**: React + Vite at http://localhost:5173
- **Backend**: Hono API server (Bun) at http://localhost:3001
- **Database**: SQLite auto-created at `~/fitness-app/fitness.db` on first run
- **Start**: `cd ~/fitness-app && bun run dev`

### SQLite Tables
- `activity_log` — daily workout/nutrition entries
- `meal_plan` — weekly planned meals (B, S1, L, S2, D)
- `water_log` — daily water intake (oz) and goal
- `caffeine_log` — timestamped caffeine entries (source, mg)
- `nutrition_items` — reusable food nutrition database
- `exercises` / `strength_entries` / `strength_sets` — strength tracking

---

## Data Backend (API-first, fallback to files)

**Always try the API first:**

```bash
curl -s --max-time 2 http://localhost:3001/api/health
```

- If it returns `{"ok":true}` → use **API mode**
- If it fails / times out → use **file mode** (edit `~/fitness/data.js` directly) and warn the user:
  > ⚠️ Fitness app server isn't running. Logging to ~/fitness/data.js instead. Start it with: `cd ~/fitness-app && bun run dev`

---

## First-Time Setup

The full app lives at `~/fitness-app/`. The `~/fitness/` folder is only used as a fallback when the server is not running.

If `~/fitness/` does NOT exist (fallback setup only):
1. Create the directory: `mkdir -p ~/fitness`
2. Copy template files from this skill's `templates/` folder:
   - `templates/tracker.html` → `~/fitness/tracker.html`
   - `templates/data.js` → `~/fitness/data.js`
   - `templates/strength.js` → `~/fitness/strength.js`
3. Tell the user: "I've set up a fallback tracker at ~/fitness/. For the full app: `cd ~/fitness-app && bun run dev`"

---

## Parsing Arguments

Parse `$ARGUMENTS` for:
- **Workout types:** "weights", "lifting", "weight training", "strength", "shoulder day", "chest day", "arm day" → weights=true
- **Running:** "ran", "running", "run", "cardio", "jog" → running=true
- **Eating:** "ate well", "ate good", "healthy eating", "good food" → ateWell=true
- **Food/Nutrition:** "I had", "I ate", "ate", food item names, servings → track nutrition with macros
- **Water:** "drank X oz", "drank X cups", "had X oz water", number + "oz" near "water" → log water intake
- **Caffeine:** "had a coffee", "had espresso", "pre-workout", "energy drink", source name + optional mg + optional time → log caffeine entry
- **Image path:** Any file path ending in .png, .jpg, .jpeg, .heic → analyze with vision
- **Show:** "show", "view", "grid", "open" → open the web viewer
- **Date references:** "yesterday", "last night", "today", specific dates → update the correct day
- **Notes:** Any additional text describing the workout

---

## Flow

### Step 1: Determine What's Being Logged

If `$ARGUMENTS` is empty or unclear, ask the user:

"What would you like to log today?"
- Weights/strength training
- Running/cardio
- Both weights and running
- Mark that I ate well
- Just show my grid

Allow multiple selections.

### Step 2: Handle Image Input

If an image path is provided:
1. Read the image file using the Read tool (Claude can see images)
2. Determine the image type and extract data:
   - **Running app screenshots** — Extract distance, time, pace, calories (e.g. Apple Fitness, Strava)
   - **Nutrition labels** — Extract calories, protein, fat, carbs per serving, note the serving size
   - **Food photos** — Identify the food and estimate nutrition if no label is available
   - **Workout screenshots** — Extract exercises, sets, reps, weights
3. Use the extracted data to calculate totals based on the servings the user specifies
4. If uncertain about what the image shows, confirm with the user before logging

### Step 2b: Handle Food/Nutrition Input

When the user mentions food items (with or without images):

1. **Check the Nutrition DB first** (API mode):
   ```bash
   curl -s http://localhost:3001/api/nutrition
   ```
   Search the returned list for the food by name. Use stored values if found.

2. If not in the DB:
   - Use exact values from a nutrition label photo if provided
   - Use WebSearch for restaurant/fast food items
   - Use standard nutrition estimates for common foods

3. **Add new items to the Nutrition DB** after logging (API mode):
   ```bash
   curl -s -X POST http://localhost:3001/api/nutrition \
     -H "Content-Type: application/json" \
     -d '{"name":"Item Name","serving_size":"1 serving (Xg)","calories":0,"protein":0,"fat":0,"carbs":0,"sodium":0,"fiber":0,"sugar":0}'
   ```

4. Calculate totals based on the number of servings specified

5. Present a nutrition breakdown table before updating:
   - Show each item with calories, protein, fat, carbs
   - Show subtotal of new items
   - Show running day total (existing + new)

6. Track cumulative nutrition in the notes as:
   `Nutrition: ~[cal] cal, [protein]g protein, [fat]g fat, [carbs]g carbs (item list)`

### Step 2c: Handle Multi-Day Updates

When the user references a different day ("yesterday", "last night", a specific date):
1. Determine the correct date
2. Update that day's entry instead of today
3. Merge with existing data for that day — recalculate nutrition totals

### Step 3: Update the Activity Log

#### API Mode (server is running)

GET existing day first, then POST merged data:
```bash
curl -s http://localhost:3001/api/activity/2026-03-10
```

POST to `http://localhost:3001/api/activity`:
```json
{
  "date": "2026-03-10",
  "weights": true,
  "running": false,
  "ateWell": true,
  "notes": "Shoulder Day | Military Press: 6 sets | Nutrition: ~1510 cal, 100g protein, 31g fat, 195g carbs (items...)",
  "calories": 1510,
  "protein": 100,
  "fat": 31,
  "carbs": 195
}
```

The API uses upsert — posting to an existing date overwrites it with the merged values.

#### File Mode (fallback)

1. Read `~/fitness/data.js`, extract the object after `window.FITNESS_DATA = `
2. Update the entry for the target date, merging with existing data
3. Write the updated data back in JavaScript format
4. Update `~/fitness/strength.js` for any strength exercises logged

**Important:** Multiple uses per day should ACCUMULATE — morning weights + evening run → show BOTH (purple square).

### Step 3b: Log Water / Caffeine (API mode)

**Water** — adds to the daily cumulative total:
```bash
curl -s -X POST http://localhost:3001/api/hydration/water \
  -H "Content-Type: application/json" \
  -d '{"date":"2026-03-10","oz":16}'
```

**Caffeine** — add a timestamped entry (use current time if not specified, HH:MM format):
```bash
curl -s -X POST http://localhost:3001/api/hydration/caffeine \
  -H "Content-Type: application/json" \
  -d '{"date":"2026-03-10","time":"08:30","source":"Coffee (8oz)","mg":95}'
```

**Get current hydration totals** (to report back to user):
```bash
curl -s http://localhost:3001/api/hydration/2026-03-10
```

Common caffeine values:
- Coffee 8oz: 95mg | Cold brew 12oz: 155mg | Espresso: 63mg
- Pre-workout: 150–200mg | Energy drink 16oz: 160mg | Green tea: 28mg | Black tea: 47mg

After logging, report back: current oz vs goal, total caffeine mg, warn if over 400mg.

### Step 3c: Update the Meal Plan (when correcting today's meals)

To upsert meal plan entries for a date (POST accepts an array):
```bash
curl -s -X POST http://localhost:3001/api/meal-plan \
  -H "Content-Type: application/json" \
  -d '[
    {"date":"2026-03-10","meal_code":"B","name":"Meal description","calories":300,"protein":20},
    {"date":"2026-03-10","meal_code":"L","name":"Meal description","calories":400,"protein":35}
  ]'
```

Meal codes: `B` (Breakfast), `S1` (Snack 1), `L` (Lunch), `S2` (Snack 2), `D` (Dinner)

To toggle a meal as completed/eaten:
```bash
curl -s -X POST http://localhost:3001/api/meal-plan/toggle \
  -H "Content-Type: application/json" \
  -d '{"date":"2026-03-10","meal_code":"S1"}'
```

### Step 4: Confirm and Summarize

After logging, confirm what was recorded:
- "Logged for [date]: [weights icon] Weights, [running icon] Running, [food icon] Ate well"
- Show the notes if any
- If API mode: mention they can view the app at http://localhost:5173
- If file mode: mention they can run `/fitness show` or start the app with `cd ~/fitness-app && bun run dev`

### Step 5: Show Grid (if requested)

If server is running, open the React app:
```bash
open http://localhost:5173
```

Otherwise fall back:
```bash
open ~/fitness/tracker.html
```

---

## Notes Format

Notes should follow this structure, separated by ` | `:
- **Running stats**: `5K Race - 3.10 mi, 27:54, 8'59"/mi pace, 469 cal`
- **Weight exercises**: `Military Press: 6 sets, max 115x2 | Lateral Raises: 5 sets, max 30x7`
- **Meals**: `Meals: B (bagel + cream cheese), L (4x flounder + green beans)`
- **Nutrition** (always last): `Nutrition: ~[total] cal, [protein]g protein, [fat]g fat, [carbs]g carbs (comma-separated item list)`

## Color Reference (for context)

When confirming, you can mention the color their day will show:
- Weights only → Red square
- Running only → Blue square
- Both → Purple square
- Any + ate well → Yellow border around the square

## Strength Data (File Mode Only)

In file mode, also update `~/fitness/strength.js` with exercise entries. In API mode, strength data is stored in SQLite automatically.

```javascript
window.STRENGTH_DATA = {
  "bench-press": {
    "name": "Bench Press",
    "entries": [
      { "date": "2026-03-01", "sets": [135, 185, 205], "notes": "3 sets" }
    ]
  }
};
```

---

## Rules

- Always merge with existing day data, never overwrite — GET first in API mode
- Try API first, fall back to file mode with a warning
- **Always check `/api/nutrition` before estimating macros** — use DB values when available
- Add new food items to the Nutrition DB after logging them
- If image analysis is uncertain, ask to confirm
- Keep notes concise but useful
- Date format must be YYYY-MM-DD
- When adding food later in the day, recalculate the full day's nutrition totals (don't append a second Nutrition: line)
- Use WebSearch for restaurant/fast food nutrition when the user doesn't have a label
- Support partial servings (e.g. "half a bag", "1/4 of a bagel", "1.5 fillets")
- When the user says "yesterday" or "last night", update the previous day's entry
- Running stats from app screenshots should include: distance, time, pace, calories
- Weight exercises should note: exercise name, number of sets, and max weight x reps
