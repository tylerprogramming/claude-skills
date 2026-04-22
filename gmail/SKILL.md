---
name: gmail
description: Search and read Gmail emails using the Gmail API. Use for research, finding information in email, reading threads, or summarizing conversations. Triggers on: search my email, search gmail, find emails about, read this email, check my inbox, look up emails from, what did X send me, gmail search.
argument-hint: [search query or action] e.g. "emails from stripe last week" or "unread newsletters"
allowed-tools: Bash(python3:*), Read, Write, Glob, Grep
user-invocable: true
---

Search and read Gmail for research or information retrieval.

## Setup Check

Before running, verify credentials exist:
```
ls ~/.claude/gmail/credentials.json
```

If missing, tell the user:
> "You need to set up Gmail API credentials first. See the setup instructions below."
>
> **Setup (one-time):**
> 1. Go to [console.cloud.google.com](https://console.cloud.google.com)
> 2. Create a project → Enable **Gmail API**
> 3. Go to **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**
> 4. Application type: **Desktop app**
> 5. Download the JSON → save as `~/.claude/gmail/credentials.json`
> 6. Run `/gmail` again — it will open your browser to authorize (one-time)

## Parsing Arguments

Parse `$ARGUMENTS` for the user's intent:

- **Natural language queries** like "emails from stripe last month" → convert to Gmail search syntax
- **Explicit queries** with Gmail operators (from:, subject:, after:, etc.) → use as-is
- **`--limit N`** → max results, default 10
- **`--body`** → include full body in search results (slower, use only when user wants content)
- **`--thread`** → fetch full thread instead of individual message

### Gmail Search Query Conversion

Convert natural language to Gmail search syntax:
- "from stripe last week" → `from:stripe after:2026/03/14`
- "unread newsletters" → `is:unread label:newsletters`
- "emails about invoice" → `subject:invoice OR invoice`
- "attachments from john" → `from:john has:attachment`
- "today's emails" → `after:2026/03/21`

Today's date: 2026-03-21

## Flow

### Step 1: Search

```bash
python3 ~/.claude/skills/gmail/gmail_client.py search "<query>" --limit <N> [--body]
```

On first run, this opens the browser for OAuth authorization. Tell the user to complete that step, then re-run.

### Step 2: Present Results

Show a clean table of results:

| # | From | Subject | Date | Snippet |
|---|------|---------|------|---------|
| 1 | sender@example.com | Subject line | Mar 20 | Preview... |

### Step 3: Read Full Email (if user wants details)

When user wants to read a specific email:
```bash
python3 ~/.claude/skills/gmail/gmail_client.py read <message_id>
```

Or fetch the full thread:
```bash
python3 ~/.claude/skills/gmail/gmail_client.py thread <thread_id>
```

### Step 4: Analyze / Summarize

After reading emails, synthesize the content for the user's research goal. Focus on:
- Key information, decisions, or action items
- Chronological summaries for threads
- Patterns across multiple emails (e.g., "All 5 emails from Stripe are receipts for X")

## Rules

- Never store or log email content to disk unless the user explicitly asks
- If a query returns 0 results, suggest alternative search terms
- Respect the `--limit` — don't fetch more than requested
- For research tasks, use `--body` only when the snippet isn't enough
- When summarizing threads, preserve chronological order
- If the user asks to "find all emails from X", default limit to 20 and ask if they want more
