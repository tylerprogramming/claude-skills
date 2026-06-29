---
name: journal
description: Daily logger with three modes - a personal journal entry, a technical standup, and a full automated end-of-day (eod) report that pulls from Supabase, Skool, Blotato, and YouTube. Also generates and emails weekly summaries. Triggers on: journal, daily log, what did I do, standup, stand up, daily standup, run my standup, eod, end of day, daily summary, how was my day, weekly summary.
argument-hint: blank=journal entry | "standup" | "eod" | "summary"/"week" | "email"
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, Agent]
user-invocable: true
---

Run the daily logger. This skill has three logging modes plus weekly summaries. Pick the mode from the argument (or the user's wording):

| Argument / intent | Mode |
|-------------------|------|
| blank, "log", "entry", "journal" | **Journal entry** (personal daily reflection) |
| "standup" | **Standup** (technical work status) |
| "eod", "end of day", "how was my day" | **End-of-day report** (automated, pulls from all sources) |
| "summary", "week" | **Weekly summary** (display only) |
| "email", "email summary" | **Weekly summary + email** |

Always get today's date from the current date, not from memory. Date format is always `YYYY-MM-DD`. Never use em dashes in saved content — use a plain hyphen with spaces or a comma.

---

## Mode 1: Journal entry (default)

Personal daily reflection. Ask these **one at a time, conversationally** — wait for each answer:

1. **What did you accomplish today?** (work, personal, anything worth noting)
2. **What are you planning to work on next?**
3. **Any blockers, concerns, or things on your mind?**
4. **Anything else you want to remember?** (optional — skip if they say no)

Save to `~/content/journal/YYYY-MM-DD.txt`:

```
# Journal — YYYY-MM-DD (Day of Week)

## Done
- [their answers as bullet points]

## Next
- [their answers as bullet points]

## Blockers
- [their answers, or "None"]

## Notes
- [optional — omit section if empty]
```

If an entry already exists for today, ask whether to **append** or **replace**.

---

## Mode 2: Standup

Technical, tighter than a journal entry. Ask these **one at a time, conversationally**:

1. **What did you work on?** (the focus / project / area)
2. **What did you get done?** (concrete accomplishments)
3. **What's next?** (what you're picking up next)
4. **Any blockers?** ("none" is fine)

Save to `~/content/standup/YYYY-MM-DD.md`:

```
# Standup — YYYY-MM-DD (Day of Week)

## Worked On
- [their answer]

## Done
- [accomplishments]

## Next
- [what's next]

## Blockers
- [their answer, or "None"]
```

Break run-on answers into clean, scannable bullets. Keep the wording theirs — tighten, don't editorialize. If a standup already exists for today, ask whether to **append** or **replace**. After saving, print the final standup and confirm the path.

- "standup show" / "standup last" → display the most recent file in `~/content/standup/`
- "standup week" → 7-day rollup of standups: what got done, what's in progress, recurring blockers (display only)

---

## Mode 3: End-of-day report

A comprehensive automated report of what got done and what's still pending.

### Step 1: Determine the date
Use the user-provided date, else today.

### Step 2: Gather data from all sources (run IN PARALLEL via the Agent tool or multiple Bash calls)

**Social Media (Blotato)** — use `mcp__blotato__blotato_list_schedules` for posts published/scheduled today across YouTube, TikTok, Instagram, LinkedIn, X.

**Skool** — recent post timestamps (Playwright if needed) + new member signups:
```
sqlite3 ~/.claude/skills/skool/data/skool.db "SELECT COUNT(*) FROM skool_members WHERE created_at LIKE 'YYYY-MM-DD%';"
```

**YouTube uploads:**
```
yt-dlp --flat-playlist --print "%(upload_date)s %(title)s" "https://www.youtube.com/@TylerReedAI/videos" 2>/dev/null | head -5
```

**Nutrition / Fitness** — query the `lifestyle` Supabase project (project id in your own config) via the Supabase MCP (replace the date):
```sql
select * from activity_log     where date = 'YYYY-MM-DD';  -- flags + macro totals
select * from cardio_log       where date = 'YYYY-MM-DD';  -- runs
select * from strength_entries where date = 'YYYY-MM-DD';  -- lifts
select * from water_log        where date = 'YYYY-MM-DD';
select * from caffeine_log     where date = 'YYYY-MM-DD';
select * from reading_log      where date = 'YYYY-MM-DD';
select * from daily_checkin    where date = 'YYYY-MM-DD';
```
Compare against `meal_plan` rows (planned vs `actual_*`). If water or caffeine is not logged, flag it.

**Content created** — check `~/content/YYYY-MM-DD/`, `~/content/youtube/shorts/`, `~/content/youtube/*/social/`, and any new carousels/PDFs/visuals created today.

**Files modified today:**
```
find ~/content ~/content/youtube ~/content/research -name "*.md" -mtime 0 2>/dev/null | head -30
```

**Journal / standup** — read `~/content/journal/YYYY-MM-DD.txt` and `~/content/standup/YYYY-MM-DD.md` if they exist.

**Schedule** — most recent `filming-schedule.md` in `~/content/` subdirs and `~/content/youtube/shorts/*/filming-plan.md`. Determine planned vs actual, and pull TOMORROW's items.

### Step 3: Build the report

```
# End of Day Summary - YYYY-MM-DD (Day of Week)

## What Got Done
- [accomplishments, grouped by category]

## Social Media Published
| Platform | Post | Status |
|----------|------|--------|

## Leads / Revenue
- New Skool members today: X
- Total Skool members: X
- LinkedIn engagement / DMs / post performance
- Sales / Revenue / new leads

## Nutrition
- Breakfast / Lunch / Dinner
- Water: X oz / goal (or "Not logged")
- Caffeine: X mg (or "Not logged")
- Calories: est. total | Protein: Xg
- Workout: [what was done, or "Rest day"]

## Still Pending
- [scheduled items not yet done; planned-but-unposted content]

## Tomorrow (Day of Week, YYYY-MM-DD)
- [from filming schedule; content that needs to go out; workout suggestion]

## Productivity Rating: X/10
[brief explanation: planned vs accomplished]
```

### Step 4: Save
Save to `~/content/journal/eod-YYYY-MM-DD.md`. If the user says "don't save" or "just show me", skip saving.

### Step 5: Present
Display the full report, then ask: (1) "Did you track water and caffeine today?" if not logged, (2) "Anything else to note?", (3) "Want me to save this?"

### Rating guidelines
- **9-10**: Exceeded the plan. Everything scheduled got done plus extra.
- **7-8**: Solid. Most things done, 1-2 pushed.
- **5-6**: Average. Some done, significant items missed.
- **3-4**: Light day.
- **1-2**: Basically a rest day.

Be honest but motivating. Context matters — a filming day where filming happened is a 10 even if posts didn't go out. Infrastructure/tool-building days count as high productivity even with no published content.

---

## Weekly summary

### "summary" / "week"
Read all entries from the past 7 days in `~/content/journal/` (exclude `weekly_summary.txt` and `eod-*.md`) and generate:
- What was accomplished
- Recurring themes or blockers
- What's planned ahead

Display it.

### "email" / "email summary"
1. Generate the weekly summary (above).
2. Send it:
   ```
   python3 ~/.claude/skills/journal/send_summary.py
   ```
   The script reads the latest `~/content/journal/weekly_summary.txt` and emails it.
3. Confirm the email was sent.

---

## Rules
- Storage: journal + eod → `~/content/journal/`; standups → `~/content/standup/`. Never save elsewhere.
- Be conversational and encouraging, not robotic — ask one question at a time.
- Keep entries concise — capture what matters, don't over-format.
- Never use em dashes in saved content.
