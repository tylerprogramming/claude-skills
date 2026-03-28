---
name: eod
description: End of day summary - shows what you accomplished, what's still pending, nutrition, leads/revenue, social media posts, tomorrow's plan, and gives a productivity rating. Triggers on eod, end of day, daily summary, what did I do today, how was my day.
argument-hint: (optional date, defaults to today)
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, Agent]
user-invocable: true
---

# End of Day Summary

Generate a comprehensive end-of-day report showing what was accomplished and what's still pending.

## Step 1: Determine the date

If the user provides a date, use that. Otherwise use today's date.

## Step 2: Gather data from all sources

Run these checks IN PARALLEL using the Agent tool or multiple Bash calls:

### Social Media Posts (Blotato)
- Use `mcp__blotato__blotato_list_schedules` or check Blotato for posts published/scheduled today
- Check for posts on: YouTube, TikTok, Instagram, LinkedIn, X/Twitter

### Skool Activity
- Check if any Skool posts were made today by looking at recent post timestamps
- Use the Skool API via Playwright if needed to check recent posts
- Check for new member signups today:
  ```
  sqlite3 ~/.claude/skills/skool/data/skool.db "SELECT COUNT(*) FROM skool_members WHERE created_at LIKE 'YYYY-MM-DD%';"
  ```

### YouTube Uploads
- Run `yt-dlp --flat-playlist --print "%(upload_date)s %(title)s" "https://www.youtube.com/@TylerReedAI/videos" 2>/dev/null | head -5` to check for uploads today

### Nutrition / Fitness
- Query the fitness database for today's entries:
  ```
  sqlite3 ~/fitness-app/fitness.db "SELECT * FROM activity_log WHERE date = 'YYYY-MM-DD';"
  sqlite3 ~/fitness-app/fitness.db "SELECT * FROM nutrition_items WHERE date = 'YYYY-MM-DD';"
  ```
- Check water intake and caffeine for the day
- Check for workout/exercise entries:
  ```
  sqlite3 ~/fitness-app/fitness.db "SELECT * FROM strength_entries WHERE date = 'YYYY-MM-DD';"
  ```
- Compare against meal plan if one exists for the current week at `~/meal-plans/`
- If water or caffeine is not logged, flag it and ask "Did you track water and caffeine today?"

### Content Created
- Check `~/content/YYYY-MM-DD/` for any files created today
- Check `~/youtube/shorts/` for shorts created today
- Check `~/youtube/*/social/` for social posts created today
- Check for any new carousel slides, PDFs, or other visual content

### Files Modified Today
- Run `find ~ -maxdepth 4 -name "*.md" -newer /tmp/eod-marker -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null | head -30` (create marker file for start of day if needed)
- Or use: `find ~/content ~/youtube ~/yt-research ~/scripts -name "*.md" -mtime 0 2>/dev/null`

### Journal Entry
- Check if `~/journal/YYYY-MM-DD.txt` exists and read it

### Weekly Schedule Check
- Look for the most recent `filming-schedule.md` in `~/content/` subdirectories
- Look for `~/youtube/shorts/*/filming-plan.md`
- Determine what was supposed to happen today vs what actually happened
- Also pull TOMORROW's schedule items for the "Tomorrow" section

## Step 3: Build the summary

Format the output as a clean report:

```
# End of Day Summary - YYYY-MM-DD (Day of Week)

## What Got Done
- [list everything accomplished, grouped by category]

## Social Media Published
| Platform | Post | Status |
|----------|------|--------|
| ... | ... | ... |

## Leads / Revenue
- New Skool members today: X
- Total Skool members: X
- LinkedIn engagement: [any notable comment triggers, DMs, or post performance]
- Sales/Revenue: [any payments, client work, or new leads]

## Nutrition
- Breakfast: ...
- Lunch: ...
- Dinner: ...
- Water: X oz / goal (or "Not logged - did you track today?")
- Caffeine: X mg (or "Not logged")
- Calories: estimated total
- Protein: Xg
- Workout: [what was done, or "Rest day"]

## Still Pending
- [list items from the week's schedule that haven't been done yet]
- [any content that was planned but not created/posted]

## Tomorrow (Day of Week, YYYY-MM-DD)
- [pull from filming schedule what's planned for tomorrow]
- [any content that needs to go out]
- [workout suggestion based on fitness routine]

## Productivity Rating: X/10
[Brief explanation of the rating based on what was planned vs accomplished]
```

## Step 4: Save the summary

Save to `~/journal/eod-YYYY-MM-DD.md`

If the user says "don't save" or "just show me", skip saving.

## Step 5: Present to user

Display the full summary in the conversation. Ask:
1. "Did you track water and caffeine today?" (if not logged)
2. "Anything else you want to note?"
3. "Want me to save this?"

## Rating Guidelines

- **9-10**: Exceeded the plan. Everything scheduled got done plus extra.
- **7-8**: Solid day. Most things got done, maybe 1-2 items pushed.
- **5-6**: Average. Some things got done but significant items were missed.
- **3-4**: Light day. Only a few things got done.
- **1-2**: Basically a rest day. Minimal output.

Be honest but not harsh. The rating should motivate, not discourage. Context matters - if it was a filming day and filming happened, that's a 10 even if social posts didn't go out. Infrastructure/tool-building days (like building skills, fixing APIs, creating workflows) count as high productivity even if no content was published.
