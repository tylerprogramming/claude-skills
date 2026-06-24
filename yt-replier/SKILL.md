---
name: yt-replier
description: Manage and reply to YouTube comments on Tyler's channel via the official YouTube Data API v3. Monitors recent uploads for unreplied comments, auto-drafts Skool-link replies for keyword CTAs, and posts approved replies. Self-contained (own OAuth token, own data dir). Trigger phrases - "youtube comments", "yt comments", "reply to youtube comments", "check youtube comments", "youtube comment inbox", "yt replies", "youtube unreplied", "respond on youtube".
argument-hint: optional - "fetch", "post", "all" (defaults to fetch + show unreplied)
allowed-tools: [Bash, Read, Write, Edit]
user-invocable: true
---

# YouTube Comment Replier

Two-stage pipeline for managing YouTube comments on Tyler's channel - mirrors `/tiktok-replier`, but YouTube has an official API so there is **no Playwright**. Both reading comments and posting replies go through the YouTube Data API v3.

Fully self-contained: own OAuth token (`token.json`), own auth module (`auth_yt.py`), own `data/` dir. No dependency on other skills.

## Files

- `auth_yt.py` — OAuth (`youtube.force-ssl` scope). Reuses `~/credentials.json` client, caches token in `token.json` next to it. Run `python3 auth_yt.py` to authorize, `--reauth` to redo.
- `monitor_yt.py` — fetches recent uploads, finds unreplied top-level comments, splits new ones into `data/inbox_yt.json` (manual) + `data/drafts_queue_yt.json` (auto keyword CTAs). Cron-friendly.
- `queue_draft_yt.py` — moves a drafted reply from `inbox_yt.json` → `drafts_queue_yt.json`.
- `reply_yt.py` — posts each reply in a queue via `comments().insert`, tracks done in `data/posted_yt.json`. Dry-run by default; `--post` to publish.
- `data/inbox_yt.json` — comments needing Tyler's manual reply (full metadata: cid, author, text, video_id, video_url, etc).
- `data/drafts_queue_yt.json` — replies ready to post.
- `data/posted_yt.json` — comment IDs already replied to (prevents double-posting).
- `data/last_seen_yt.json` — dedupe state for the monitor.
- `data/drafts_yt.md` — human-readable running log.

## The hourly cron + manual draft workflow (PRIMARY pattern)

A cron runs `monitor_yt.py` every hour at :07. It produces three artifacts in `data/`:
- **`inbox_yt.json`** — comments needing Tyler's manual reply. This is what Tyler asks Claude to help draft.
- **`drafts_queue_yt.json`** — auto-drafted Skool-link replies for short keyword CTAs (System / Plan / Skill / Email / Routine / Tools / VFX / schedule / video / workflow). Already ready to post.
- **`drafts_yt.md`** — human-readable running log.

### When Tyler says "any new youtube comments?" / "check my yt inbox"

1. Read `data/inbox_yt.json` (manual-needed) AND `data/drafts_queue_yt.json` (auto-drafts pending).
2. Show Tyler the breakdown — count of each plus the actual text of inbox items.
3. He picks one or all to draft replies for.

### When Tyler asks "draft a reply for the @username one"

1. Read the inbox entry for that comment.
2. Compose a reply in Tyler's tone (casual, helpful, drives to skool.com/the-ai-agency when relevant). Use `/harut` for conversion-sensitive wording. No em dashes.
3. Show Tyler the draft, get approval.
4. When approved, run:
   ```
   python3 ~/.claude/skills/yt-replier/queue_draft_yt.py --cid <cid> --reply "<text>"
   ```
   This appends to `drafts_queue_yt.json` AND removes from `inbox_yt.json`.

### When Tyler says "post them"

```
python3 ~/.claude/skills/yt-replier/reply_yt.py --post
```

`--post` is required to actually publish. Without it the script does a dry-run (prints what it would post). 10s spacing between posts.

## Standard workflow (manual / first-time)

### 0. Authorize (one time)

```
python3 ~/.claude/skills/yt-replier/auth_yt.py
```

A browser opens, Tyler approves the YouTube scope, token saves to `token.json`. (The token was migrated from the `/yt-upload` skill on creation, so this is usually already done.)

### 1. Fetch unreplied comments

```
python3 ~/.claude/skills/yt-replier/monitor_yt.py
```

Scans the 30 most recent uploads, up to 50 top-level comments each. A comment is "unreplied" when it's top-level, not authored by Tyler's channel, and Tyler hasn't replied in that thread. New ones get split into inbox (manual) vs auto-queue (keyword CTA).

### 2. Build reply queue

Show Tyler the unreplied list, confirm wording, then either:
- auto-drafts are already in `drafts_queue_yt.json`, or
- draft a manual reply and move it with `queue_draft_yt.py` (see above).

### 3. Post the replies

**Always dry-run first, then test on 1, then batch:**
```
python3 reply_yt.py                      # dry-run (shows everything, posts nothing)
python3 reply_yt.py --post --limit 1     # smoke test - post a single reply
python3 reply_yt.py --post               # batch (10s pause between each)
```

To post the auto-drafted keyword CTAs from a specific queue:
```
python3 reply_yt.py --post --queue ~/.claude/skills/yt-replier/data/drafts_queue_yt.json
```

## Editing the auto-reply behavior

`monitor_yt.py` holds the auto-draft logic near the top:
- `SKOOL_LINK_REPLY` — the canned reply text for keyword CTAs.
- `KEYWORD_REPLIES` — the keyword → reply map (System / Plan / Skill / Email / Routine / Tools / VFX / schedule / video / workflow).
- `draft_reply_for()` — comments longer than 60 chars always go to the manual inbox; short ones matching a keyword get auto-drafted.

## Safety rules

- **Default to dry-run**, then `--limit 1` on first run of any new queue.
- **Always show drafts to Tyler** before bulk posting (matches `feedback_confirm_before_scheduling.md` — confirm before posting even if approved earlier in the session).
- **`posted_yt.json` tracks done IDs** so re-runs after a crash skip what already worked.
- **No em dashes** in any reply (matches `feedback_no_em_dashes.md`).
- **No automatic re-fetch + re-post loops** — Tyler initiates each batch.

## Quota

YouTube Data API v3: 10,000 units/day. Per monitor run is ~30-60 units; each posted reply (`comments.insert`) is 50 units. Plenty of headroom for normal use.

## Cron

```
7 * * * * /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 \
  /Users/tylerreed/.claude/skills/yt-replier/monitor_yt.py \
  >> /Users/tylerreed/.claude/skills/yt-replier/data/monitor_yt.log 2>&1
```

This runs at :07 each hour (TikTok monitor runs at :05). The monitor posts a macOS notification with the new-comment count. It never posts replies on its own — posting is always a manual `reply_yt.py --post`.
