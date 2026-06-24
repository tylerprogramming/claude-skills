---
name: standup
description: Daily standup logger. Asks what you worked on, what you did, what's next, and any blockers, then generates a clean dated standup and saves it. Triggers on: standup, stand up, daily standup, run my standup, log standup.
argument-hint: (leave blank to run today's standup, or "show"/"last" to view the most recent, or "week" for a 7-day rollup)
allowed-tools: Read, Write, Edit, Glob, Bash(ls:*), Bash(date:*)
user-invocable: true
---

Run the daily standup skill.

## Data Location

All standups are stored in `~/content/standup/` as markdown files named by date: `YYYY-MM-DD.md`

## Default (no arguments)

Ask the user these four questions **one at a time, conversationally** — wait for each answer before asking the next:

1. **What did you work on?** (the focus / project / area)
2. **What did you get done?** (concrete accomplishments)
3. **What's next?** (what you're picking up next)
4. **Any blockers?** (anything stuck, waiting, or on your mind — "none" is fine)

After collecting answers, generate a clean standup and save it to `~/content/standup/YYYY-MM-DD.md` using today's date.

Use this exact format:

```
# Standup — YYYY-MM-DD (Day of Week)

## Worked On
- [their answer as bullet points]

## Done
- [their accomplishments as bullet points]

## Next
- [what they're picking up next]

## Blockers
- [their answer, or "None"]
```

Break run-on answers into clean, scannable bullets. Keep the wording theirs — tighten, don't editorialize.

If a standup already exists for today, ask whether to **append** to it or **replace** it before writing.

After saving, print the final standup to the terminal and confirm the file path.

## "show" or "last"
Read and display the most recent standup file in `~/content/standup/`.

## "week"
Read all standups from the past 7 days and produce a short rollup: what got done, what's still in progress, and any recurring blockers. Display it — do not save unless asked.

## Rules
- Always use `~/content/standup/` for storage — never save standup files elsewhere
- Date format is always YYYY-MM-DD; get today's date from the current date, not from memory
- Be conversational, not robotic — one question at a time
- Keep it tight: a standup is a quick status, not a journal entry
- Never use em dashes in the saved content — use a plain hyphen with spaces or a comma
