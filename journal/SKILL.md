---
name: journal
description: Daily journal and standup logger. Asks what you did, what you're doing, and any blockers, then saves entries to ~/journal/. Can also generate and email weekly summaries. Triggers on: journal, standup, daily log, what did I do, weekly summary.
argument-hint: [action] (leave blank for daily entry, or use "summary", "week", "email summary")
allowed-tools: Bash(python3:*), Read, Write, Edit, Glob, Grep
user-invocable: true
---

Run the daily journal / standup skill.

## Data Location

All journal entries are stored in `~/journal/` as text files named by date: `YYYY-MM-DD.txt`

## Actions

### Default (no arguments or "log" or "entry")
Run a daily journal entry. Ask the user these questions **one at a time, conversationally**:

1. **What did you accomplish yesterday/today?** (work, personal, anything worth noting)
2. **What are you planning to work on next?**
3. **Any blockers, concerns, or things on your mind?**
4. **Anything else you want to remember?** (optional — skip if they say no)

After collecting answers, save the entry to `~/journal/YYYY-MM-DD.txt` using today's date. Format:

```
# Journal — YYYY-MM-DD (Day of Week)

## Done
- [their answers as bullet points]

## Next
- [their answers as bullet points]

## Blockers
- [their answers, or "None" if nothing]

## Notes
- [optional notes, omit section if empty]
```

If an entry already exists for today, ask if they want to **append** to it or **replace** it.

### "summary" or "week" (no email)
Read all entries from the past 7 days in `~/journal/` and generate a summary:
- What was accomplished
- Recurring themes or blockers
- What's planned ahead

Display the summary to the user.

### "email summary" or "email"
1. Generate the weekly summary (same as above)
2. Run the email script to send it:
   ```
   python3 ~/.claude/skills/journal/send_summary.py
   ```
   The script reads the latest `~/journal/weekly_summary.txt` and emails it.
3. Confirm to the user that the email was sent.

## Rules
- Always use `~/journal/` for storage — never save journal files elsewhere
- Date format is always YYYY-MM-DD
- Be conversational and encouraging, not robotic
- Keep entries concise — capture what matters, don't over-format
- When generating summaries, read all .txt files from the past 7 days (exclude weekly_summary.txt)
