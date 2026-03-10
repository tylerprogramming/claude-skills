---
name: fitness
description: Track workouts, nutrition, and eating with a GitHub-style grid. Log weights, running, or food intake for any day. Supports text input, nutrition label photos, running app screenshots, and multi-day updates. Triggers on: fitness, log workout, worked out, went running, lifted weights, ate well, fitness show, I had, I ate.
argument-hint: [weights/running/ate well/food items/image path/show]
allowed-tools: Bash, Read, Write, Glob, Edit, WebSearch
user-invocable: true
---

Track workouts, nutrition, and eating in a GitHub-style contribution grid.

## Data Backend (API-first, fallback to files)

The fitness tracker has two backends. **Always try the API first:**

### Check if API is running
```bash
curl -s --max-time 2 http://localhost:3001/api/health
```

- If it returns `{"ok":true}` → use **API mode** (POST to `http://localhost:3001/api/activity`)
- If it fails / times out → use **file mode** (edit `~/fitness/data.js` directly) and warn the user:
  > ⚠️ Fitness app server isn't running. Logging to ~/fitness/data.js instead. Start it with: `cd ~/fitness-app && bun run dev`

---

## First-Time Setup

Before doing anything else, check if `~/fitness/` exists. If it does NOT:

1. Create the directory: `mkdir -p ~/fitness`
2. Copy all template files from this skill's `templates/` folder into `~/fitness/`:
   - `templates/tracker.html` → `~/fitness/tracker.html`
   - `templates/data.js` → `~/fitness/data.js`
   - `templates/strength.js` → `~/fitness/strength.js`
3. Tell the user: "I've set up your fitness tracker at ~/fitness/. Start the full app with: `cd ~/fitness-app && bun run dev`"

If `~/fitness/` already exists, skip setup and proceed normally.

---

## Parsing Arguments

Parse `$ARGUMENTS` for:
- **Workout types:** "weights", "lifting", "weight training", "strength", "shoulder day", "chest day", "arm day" → weights=true
- **Running:** "ran", "running", "run", "cardio", "jog" → running=true
- **Eating:** "ate well", "ate good", "healthy eating", "good food" → ateWell=true
- **Food/Nutrition:** "I had", "I ate", "ate", food item names, servings → track nutrition with macros
- **Image path:** Any file path ending in .png, .jpg, .jpeg, .heic → analyze with vision
- **Show:** "show", "view", "grid", "open" → open the web viewer
- **Date references:** "yesterday", "last night", "today", specific dates → update the correct day
- **Notes:** Any additional text describing the workout

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
1. If a nutrition label photo is provided, use those exact values
2. If the user references a food they've logged before, check existing entries in `data.js` for stored nutrition info
3. For restaurant/fast food items, use WebSearch to look up nutrition facts
4. For common foods without labels, use standard nutrition estimates
5. Calculate totals based on the number of servings specified
6. Present a nutrition breakdown table before updating:
   - Show each item with calories, protein, fat, carbs
   - Show subtotal of new items
   - Show running day total (existing + new)
7. Track cumulative nutrition in the notes as: `Nutrition: ~[cal] cal, [protein]g protein, [fat]g fat, [carbs]g carbs (item list)`

### Step 2c: Handle Multi-Day Updates

When the user references a different day ("yesterday", "last night", a specific date):
1. Determine the correct date
2. Update that day's entry instead of today
3. Merge with existing data for that day — recalculate nutrition totals

### Step 3: Update the Data

#### API Mode (server is running)

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

The API uses upsert — if the day exists, it will be overwritten with the new values.

**Important for merging:** Before posting, GET the existing day first:
```bash
curl -s http://localhost:3001/api/activity/2026-03-10
```
Then merge the existing data (OR the new data) before posting.

#### File Mode (fallback)

1. Read the current data from `~/fitness/data.js`
2. Parse the JavaScript: extract the object after `window.FITNESS_DATA = `
3. Get today's date in YYYY-MM-DD format
4. Update today's entry, MERGING with any existing data:
   - If weights detected/mentioned → set weights: true
   - If running detected/mentioned → set running: true
   - If ate well mentioned → set ateWell: true
   - Append any notes to existing notes
5. Write the updated data back in JavaScript format
6. Also update `~/fitness/strength.js` for any strength exercises logged

**Important:** Multiple uses per day should ACCUMULATE. If morning log was "weights" and evening is "ran 3 miles", the day should show BOTH (purple square).

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
- **Activity**: `Walked at Busch Gardens`
- **Nutrition** (always last): `Nutrition: ~[total] cal, [protein]g protein, [fat]g fat, [carbs]g carbs (comma-separated item list)`

## Color Reference (for context)

When confirming, you can mention the color their day will show:
- Weights only → Red square
- Running only → Blue square
- Both → Purple square
- Any + ate well → Yellow border around the square

## Strength Data (File Mode Only)

In file mode, also update `~/fitness/strength.js` with exercise entries. In API mode, the strength data is stored in SQLite automatically via the notes text.

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
- If image analysis is uncertain, ask to confirm
- Keep notes concise but useful
- Date format must be YYYY-MM-DD
- When adding food later in the day, recalculate the full day's nutrition totals (don't just append a second Nutrition: line)
- Use WebSearch for restaurant/fast food nutrition when the user doesn't have a label
- Support partial servings (e.g. "half a bag", "1/4 of a bagel", "1.5 filets")
- When the user says "yesterday" or "last night", update the previous day's entry
- Running stats from app screenshots should include: distance, time, pace, calories
- Weight exercises should note: exercise name, number of sets, and max weight x reps
