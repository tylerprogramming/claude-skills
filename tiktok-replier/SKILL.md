---
name: tiktok-replier
description: Scrape TikTok comments on @codewithtyler videos via Apify, then post replies via Playwright using a saved logged-in session. Trigger phrases - "tiktok comments", "tiktok replies", "reply to tiktok", "check tiktok comments", "tiktok unreplied", "respond on tiktok".
argument-hint: optional - "fetch", "post", "all" (defaults to fetch + show unreplied)
allowed-tools: [Bash, Read, Write, Edit]
user-invocable: true
---

# TikTok Comment Replier

Two-stage pipeline for managing TikTok comments on @codewithtyler:

- **Read side**: Apify (`clockworks/tiktok-comments-scraper`) — clean structured JSON, $0.001/comment
- **Write side**: Playwright with persistent Chromium profile — needed because TikTok has no official reply API

## Files

- `auth.py` — one-time login, saves persistent profile to `data/profile/`
- `apify_fetch.py` — pulls comments via Apify, writes `data/unreplied.json`
- `reply.py` — reads `data/replies_queue.json`, posts each reply, tracks done in `data/posted.json`
- `data/replies_queue.json` — the queue of {cid, author, comment_text, video_url, reply_text}
- `data/posted.json` — comment IDs already replied to (prevents double-posting)

## The hourly cron + manual draft workflow (PRIMARY pattern)

A cron runs `monitor.py` every hour at :05. It produces three artifacts in `data/`:
- **`inbox.json`** — comments needing Tyler's manual reply (with full metadata: cid, author, text, video_url, etc). This is what Tyler asks Claude to help draft.
- **`drafts_queue.json`** — auto-drafted Skool-link replies for keyword CTAs (System / Plan / Skill / Email / Routine / Tools / VFX / schedule / video / workflow). Already ready to post.
- **`drafts.md`** — human-readable running log.

### When Tyler says "any new comments?" / "check my tiktok inbox"

1. Read `data/inbox.json` (manual-needed) AND `data/drafts_queue.json` (auto-drafts pending).
2. Show Tyler the breakdown — count of each plus the actual text of inbox items.
3. He picks one or all to draft replies for.

### When Tyler asks "draft a reply for the @username one"

1. Read the inbox entry for that comment.
2. Compose a reply that fits Tyler's tone (casual, helpful, drives to skool.com/the-ai-agency when relevant). Use `/harut` for conversion-sensitive wording.
3. Show Tyler the draft, get approval.
4. When approved, run:
   ```
   python3 ~/.claude/skills/tiktok-replier/queue_draft.py --cid <cid> --reply "<text>"
   ```
   This appends to `replies_queue.json` AND removes from `inbox.json`.

### When Tyler says "post them"

```
python3 ~/.claude/skills/tiktok-replier/reply.py --post --headless
```

For auto-drafted Skool-link CTAs:
```
python3 ~/.claude/skills/tiktok-replier/reply.py --post --headless --queue ~/.claude/skills/tiktok-replier/data/drafts_queue.json
```

## Standard workflow (manual / first-time)

### 1. Fetch unreplied comments

Use Apify via MCP (recommended — no token maintenance needed):
```
mcp__apify__call-actor with actor=clockworks/tiktok-comments-scraper
input: {"profiles": ["codewithtyler"], "resultsPerPage": 30, "commentsPerPost": 50, "maxRepliesPerComment": 10, "profileSorting": "latest"}
```
Then `mcp__apify__get-actor-output` with the dataset ID, fields=`cid,uniqueId,text,diggCount,replyCommentTotal,likedByAuthor,repliesToId,createTimeISO,videoWebUrl`.

Filter: top-level (repliesToId is null) AND no reply from @codewithtyler in same thread AND author != codewithtyler.

OR run the local script (needs APIFY_API_TOKEN in `~/.claude/.env`):
```
python3 ~/.claude/skills/tiktok-replier/apify_fetch.py --videos 30 --per 100
```

### 2. Build reply queue

Show Tyler the unreplied list, confirm wording, and write `data/replies_queue.json`. Each entry needs:
- `cid` — comment ID (used to skip already-posted)
- `author` — TikTok username (used to find the row)
- `comment_text` — original comment text (used to verify the right row)
- `video_url` — full video URL
- `reply_text` — what to reply with

For keyword-style CTAs (System / Plan / Skill / Email / Routine / Tools / VFX / schedule), the standard reply is:
```
https://www.skool.com/the-ai-agency is the link! It is in the Social Media Classroom (free of course!)
```

### 3. Post the replies

Login first if `data/profile/` is empty: `python3 auth.py` (interactive, opens browser, auto-detects sessionid cookie).

**Always test on 1 first, then batch:**
```
python3 reply.py --post --limit 1 --headless    # smoke test
python3 reply.py --post --headless              # batch (30s pause between each)
```

For first run or debugging, drop `--headless` so the browser is visible. Default to `--headless` once the flow is confirmed working.

`--post` is required to actually publish. Without it the script does dry-run (composes but doesn't click submit).

## Critical implementation notes (so future sessions don't re-debug TikTok's DOM)

- **Auth** must use `launch_persistent_context(user_data_dir=...)`, NOT `storage_state`. TikTok's session is bound to fingerprint + localStorage + IndexedDB; cookies alone aren't enough.
- **Comment-icon click** opens the proper comments view: `[data-e2e="comment-icon"]` on the video player. The right-side "Comments" tab is a different sidebar preview that doesn't expose proper Reply controls.
- **Per-comment Reply button** is `div[class*="DivReplyTriggerWrapper"]` inside `div[class*="DivCommentItemWrapper"]`. Click it via real Playwright `page.mouse.click(x, y)` at its center — JS `.click()` does NOT trigger TikTok's React handler.
- **Reply composer** is a contenteditable Draft.js editor where the placeholder div intercepts pointer events. Focus it via JS (`el.focus()`), then `page.keyboard.type()`. Don't use Playwright's `.click()` on the contenteditable.
- **Submit button** is `[data-e2e="comment-post"]` (an arrow icon, NOT text "Post"). Same trick: real mouse click at pixel coords.
- **Verification**: composer disappearing OR clearing OR reply text appearing in DOM = success. Don't trust any single signal.
- **First-time tutorial**: TikTok shows an "Introducing keyboard shortcuts" modal that overlays the comments panel. Strip it surgically — DON'T blanket-remove all `[class*="Modal"]` elements (that nukes the legitimate panel).

## Safety rules

- **Default to `--limit 1` on first run** of any new queue
- **Always show drafts to Tyler** before bulk posting (matches his memory: "Always confirm before scheduling, even if approved earlier in session")
- **30s spacing between posts** to stay under TikTok's spam threshold
- **`posted.json` tracks done IDs** so re-runs after a crash skip what already worked
- **No automatic re-fetch + re-post loops** — Tyler initiates each batch

## "Keep checking" - the recurring use case

Two paths Tyler can pick:
1. **Apify scheduler** (recommended): set up in their web console, runs in their cloud, emails him the dataset link. No local laptop dependency.
2. **Local cron** via `/schedule` skill: re-runs `apify_fetch.py` on a schedule, then prompts to review unreplied list.

Both options drop the post step into manual review — Tyler approves before any reply gets published.
