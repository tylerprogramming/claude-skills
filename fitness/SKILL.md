---
name: fitness
description: Track workouts and eating with a GitHub-style grid. Log weights, running, or eating well for any day. Supports text input or image uploads from other fitness apps. Use when logging a workout, tracking eating, or viewing the fitness grid. Triggers on: fitness, log workout, worked out, went running, lifted weights, ate well, fitness show.
argument-hint: [weights/running/ate well/image path/show]
allowed-tools: Bash, Read, Write, Glob
user-invocable: true
---

Track workouts and eating in a GitHub-style contribution grid.

## First-Time Setup

Before doing anything else, check if `~/fitness/` exists. If it does NOT:

1. Create the directory: `mkdir -p ~/fitness`
2. Copy all template files from this skill's `templates/` folder into `~/fitness/`:
   - `templates/tracker.html` → `~/fitness/tracker.html`
   - `templates/data.js` → `~/fitness/data.js`
   - `templates/strength.js` → `~/fitness/strength.js`
3. Tell the user: "I've set up your fitness tracker at ~/fitness/. You can customize it by:
   - Editing your name, handle, bio, and city in tracker.html
   - Dropping a profile.png into ~/fitness/ for your avatar
   - The default strength exercises are just starting points — add, remove, or rename them in strength.js to match YOUR routine (e.g. deadlifts, pull-ups, curls, whatever you do)"

If `~/fitness/` already exists, skip setup and proceed normally.

## Data Location

- Data file: `~/fitness/data.js` (JavaScript format for browser compatibility)
- Strength data: `~/fitness/strength.js` (tracks exercise progress over time)
- Web viewer: `~/fitness/tracker.html`

## Parsing Arguments

Parse `$ARGUMENTS` for:
- **Workout types:** "weights", "lifting", "weight training", "strength" → weights=true
- **Running:** "ran", "running", "run", "cardio", "jog" → running=true
- **Eating:** "ate well", "ate good", "healthy eating", "good food" → ateWell=true
- **Image path:** Any file path ending in .png, .jpg, .jpeg, .heic → analyze with vision
- **Show:** "show", "view", "grid", "open" → open the web viewer
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
2. Analyze what type of workout it shows (weights, running, both, other)
3. Extract any useful details for notes (exercises, distance, duration)
4. Confirm with the user what you detected before logging

### Step 3: Update the Data

1. Read the current data from `~/fitness/data.js`
2. Parse the JavaScript: extract the object after `window.FITNESS_DATA = `
3. Get today's date in YYYY-MM-DD format
4. Update today's entry, MERGING with any existing data for today:
   - If weights detected/mentioned → set weights: true
   - If running detected/mentioned → set running: true
   - If ate well mentioned → set ateWell: true
   - Append any notes to existing notes
5. Write the updated data back in this format:
   ```javascript
   // Fitness data - updated by /fitness skill
   window.FITNESS_DATA = {
     "2026-03-01": { ... },
     ...
   };
   ```

**Important:** Multiple uses per day should ACCUMULATE. If morning log was "weights" and evening is "ran 3 miles", the day should show BOTH (purple square).

### Step 4: Confirm and Summarize

After logging, confirm what was recorded:
- "Logged for [date]: [weights icon] Weights, [running icon] Running, [food icon] Ate well"
- Show the notes if any
- Mention they can run `/fitness show` to see their grid

### Step 5: Show Grid (if requested)

If user asked to show/view the grid:
```bash
open ~/fitness/tracker.html
```

## Data Format

The data is stored as a JavaScript file (`data.js`) so browsers can load it directly:

```javascript
// Fitness data - updated by /fitness skill
window.FITNESS_DATA = {
  "2026-03-01": {
    "weights": true,
    "running": false,
    "ateWell": true,
    "notes": "bench press 3x10, squats 4x8"
  }
};
```

## Color Reference (for context)

When confirming, you can mention the color their day will show:
- Weights only → Red square
- Running only → Blue square
- Both → Purple square
- Any + ate well → Yellow border around the square

## Strength Data Format

The strength data tracks exercises over time for progress charts. The template includes common exercises but **users can track ANY exercises they want** — just add new keys to the object:

```javascript
// Strength tracking data - updated by /fitness skill
window.STRENGTH_DATA = {
  "bench-press": {
    "name": "Bench Press",
    "entries": [
      { "date": "2026-03-01", "sets": [135, 185, 205], "notes": "3 sets" }
    ]
  },
  "pull-ups": {
    "name": "Pull-ups",
    "entries": []
  }
};
```

When logging a weight exercise, also update `~/fitness/strength.js` with the exercise entry. If the exercise key doesn't exist yet, create it.

## Rules

- Always merge with existing day data, never overwrite
- If image analysis is uncertain, ask to confirm
- Keep notes concise but useful
- Date format must be YYYY-MM-DD
- Run first-time setup if `~/fitness/` doesn't exist
- Strength exercises are fully customizable — add new ones as needed
