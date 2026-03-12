---
name: meal-plan
description: Generate a weekly meal plan with breakfast, lunch, and dinner from a folder of recipe files. Reads your recipes, asks about themed nights and preferences, builds a full 7-day plan, and creates a consolidated shopping list. Triggers on: meal plan, plan meals, weekly meals, what should I eat, grocery list, meal prep.
argument-hint: [recipe_folder_path] (defaults to current directory)
allowed-tools: Read, Write, Glob, Grep
user-invocable: true
---

Generate a weekly meal plan from recipe files at $ARGUMENTS (or current directory if no path given).

## Data Location

The meal plan and shopping list are saved to the same folder as the recipes:
- `meal-plan.md` — the full weekly plan
- `shopping-list.md` — consolidated grocery list

## Flow

### Step 1: Discover & Read Recipes

Glob for all `*.md` files in the recipe folder (excluding `meal-plan.md` and `shopping-list.md` if they already exist). Read every recipe file to understand:

- Recipe name
- Servings
- Prep/cook time
- Full ingredient list with quantities
- Instructions

### Step 2: Categorize Recipes

Sort each recipe into one or more meal categories based on its content:

- **Breakfast** — pancakes, oats, eggs, smoothies, toast, etc.
- **Lunch** — salads, sandwiches, soups, quesadillas, lighter meals
- **Dinner** — proteins with sides, pasta dishes, stir fry, heavier meals
- **Finger food / snack** — items that work as movie night, game day, or party food

A recipe can fit multiple categories (e.g., avocado toast works for breakfast or lunch, quesadillas work for lunch or finger food).

Present the categorization to the user as a quick summary so they can see what's available.

### Step 3: Ask the User

Ask these questions **one at a time, conversationally**:

1. **"Any themed nights this week?"** — e.g., Taco Tuesday, Pizza Sunday, Movie Night Friday. If yes, ask which day and what theme.
2. **"Any dietary restrictions or ingredients to avoid this week?"**
3. **"How many people are you feeding?"** — This determines quantity scaling for the shopping list.
4. **"Any other preferences?"** — e.g., keep lunches light, no repeats, use up specific ingredients, etc.

If the user already provided this info in their initial message, skip questions they've already answered.

### Step 4: Build the Meal Plan

Assign recipes to all 21 meal slots (7 days x 3 meals):

- **Respect themed nights first** — lock those in before filling other slots
- **Balance variety** — don't repeat the same recipe on consecutive days
- **Match categories** — breakfast recipes for breakfast, dinner recipes for dinner, etc.
- **Reuse strategically** — with limited recipes, repeats are fine but spread them apart (e.g., scrambled eggs Monday and Thursday, not Monday and Tuesday)
- **Leverage leftovers** — if a dinner makes 4+ servings, suggest leftovers for the next day's lunch
- **Pair smartly** — soup + sandwich combos, protein + salad sides, etc.

### Step 5: Build the Shopping List

Consolidate all ingredients across all 21 meals:

- **De-duplicate** — combine identical ingredients (e.g., garlic from 5 recipes = "Garlic — 3 heads (used all week)")
- **Scale quantities** — adjust based on number of people vs recipe serving sizes
- **Organize by grocery section:**
  - Meat & Seafood
  - Produce
  - Dairy & Eggs
  - Bread & Dough
  - Pantry & Dry Goods
  - Canned & Jarred
  - Frozen
  - Oils, Sauces & Seasonings
- **Annotate** — note which day/meal each item is for in parentheses
- **Use checkboxes** — format as `- [ ]` for easy use as a checklist

### Step 6: Save Both Files

Write two files to the recipe folder:

#### `meal-plan.md`
```
# Weekly Meal Plan

## Monday
- **Breakfast:** Recipe Name (recipe-file.md)
- **Lunch:** Recipe Name (recipe-file.md)
- **Dinner:** Recipe Name (recipe-file.md)

## Tuesday
...
```

Each entry references the recipe filename so the user can quickly look it up.

#### `shopping-list.md`
```
# Shopping List

## Meat & Seafood
- [ ] Item — quantity (day/meal annotation)

## Produce
...
```

### Step 7: Present & Iterate

After generating both files, show the user:
- A summary table of the week (Day | Breakfast | Lunch | Dinner)
- Any notes about leftovers or prep-ahead suggestions

Ask: **"Want to swap anything out or adjust the plan?"**

If they want changes, update both files accordingly (the shopping list must always reflect the current plan).

## Rules

- Always save `meal-plan.md` and `shopping-list.md` to the same folder as the recipes
- Never overwrite recipe files — only create/update the plan and shopping list files
- Every day MUST have breakfast, lunch, and dinner — no gaps
- Reference recipe filenames in the meal plan so the user can find the full recipe
- Shopping list must use `- [ ]` checkbox format
- Shopping list quantities should be realistic — round up to store-friendly amounts (e.g., "1 bag" not "1.5 cups loose")
- If there aren't enough recipes to fill all 21 slots without heavy repetition, tell the user and suggest they add more recipes to the folder
- Keep it practical — don't assign a 45-minute breakfast on a weekday unless the user says they have time
- Quick breakfasts (overnight oats, smoothie bowls, toast) are great for weekdays; bigger breakfasts (pancakes) are better for weekends
