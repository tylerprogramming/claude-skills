---
name: yt-upload
description: Upload videos to YouTube and manage existing videos via the YouTube Data API v3. Replaces Blotato for long-form YouTube uploads (proper tags, scheduling, custom thumbnails). Edit titles, descriptions, tags, thumbnails, privacy, and publish-at on already-uploaded videos. Post comments on videos. Triggers on - upload to youtube, schedule youtube video, swap youtube thumbnail, edit youtube title, edit youtube description, comment on youtube, post youtube comment, my youtube uploads, youtube api.
argument-hint: [action] e.g. "upload claude design video", "swap thumbnail on VIDEO_ID", "list my uploads"
allowed-tools: Bash(python3:*), Bash(ls:*), Bash(file:*), Read, Write, Edit, Glob, Grep
user-invocable: true
---

Upload to YouTube and manage existing videos using the YouTube Data API v3. Use this instead of Blotato for any long-form YouTube work — Blotato cannot expose the tags field, cannot edit existing videos, and cannot post comments.

## Setup Check

The skill reuses Tyler's existing Google OAuth client at `~/credentials.json` (same one Drive and Gmail use). The first run will need to authorize the YouTube scopes — that's a one-time browser flow.

```bash
python3 ~/.claude/skills/youtube/yt.py auth
```

A browser opens, Tyler approves both scopes (`youtube.upload` + `youtube.force-ssl`), token saves to `~/.claude/skills/youtube/token.json`.

If you see "missing OAuth client" error: `~/credentials.json` was deleted. Tell Tyler to re-export from Google Cloud Console.

## Subcommands

All actions go through one CLI: `python3 ~/.claude/skills/youtube/yt.py <subcommand> [args]`. Outputs JSON on stdout for downstream parsing.

### upload — schedule or publish a long-form video

```bash
python3 ~/.claude/skills/youtube/yt.py upload \
  --video "/Users/tylerreed/Downloads/claude design in 23 minutes.mp4" \
  --title "Claude Design + Claude Code: Prompt to Live URL in 23 Minutes" \
  --description-file ~/content/youtube/claude-design/description.md \
  --tags-file ~/content/youtube/claude-design/tags.txt \
  --thumbnail ~/content/youtube/claude-design/thumbnail-final.jpg \
  --category 28 \
  --privacy private \
  --publish-at 2026-04-26T13:00:00-04:00
```

- `--privacy private --publish-at <ISO 8601>` schedules. YouTube auto-flips to public at that time.
- `--privacy public` (without `--publish-at`) publishes immediately.
- `--privacy unlisted` for share-link-only.
- `--no-notify` to skip subscriber notifications. Default is to notify.
- `--made-for-kids` if applicable. Default is no.
- Categories: 22 = People & Blogs, 27 = Education, 28 = Science & Technology (default for tech tutorials).
- Tags: pass via `--tags "tag1,tag2,..."` OR `--tags-file path` (comma-separated or one per line). YouTube caps the field at 500 chars total — script auto-truncates from the end and warns.

The description file should be plain text. If you have a `description.md` with a markdown H1 and `---` frontmatter, strip those before passing — or pass the body section only.

### update — edit metadata on an already-uploaded video

```bash
python3 ~/.claude/skills/youtube/yt.py update VIDEO_ID --title "New title"
python3 ~/.claude/skills/youtube/yt.py update VIDEO_ID --description-file new.md
python3 ~/.claude/skills/youtube/yt.py update VIDEO_ID --tags-file tags.txt
python3 ~/.claude/skills/youtube/yt.py update VIDEO_ID --privacy public
python3 ~/.claude/skills/youtube/yt.py update VIDEO_ID --publish-at 2026-05-01T13:00:00-04:00
```

Only specified fields are updated; everything else is preserved (the script reads current snippet/status first).

### thumbnail — replace thumbnail on a published video

```bash
python3 ~/.claude/skills/youtube/yt.py thumbnail VIDEO_ID --image ~/content/youtube/claude-design/thumbnail-backup-A.jpg
```

Image must be JPG or PNG, under 2 MB. If your source thumbnail is bigger:

```bash
sips -s format jpeg -s formatOptions 80 input.png --out output.jpg
```

### comment — post a top-level comment or reply

```bash
# Top-level comment on a video
python3 ~/.claude/skills/youtube/yt.py comment VIDEO_ID --text "🎯 link to my Skool community in the description!"

# Reply to a specific comment
python3 ~/.claude/skills/youtube/yt.py comment --reply-to COMMENT_ID --text "thanks!"
```

### list — list my recent uploads

```bash
python3 ~/.claude/skills/youtube/yt.py list --max 10
```

Returns JSON array with video_id, title, published_at, url for each. Useful when Tyler wants to find a video ID without opening the browser.

### get — fetch full metadata for a single video

```bash
python3 ~/.claude/skills/youtube/yt.py get VIDEO_ID
```

Returns title, description, tags, category, privacy_status, publish_at, duration, stats (views/likes/comments), URL.

## Common Tyler workflows

### Schedule a longform video (replaces Blotato YouTube uploads)

1. Pull the title from `~/content/youtube/<slug>/titles.md` (recommended title).
2. Strip the H1 and frontmatter from `~/content/youtube/<slug>/description.md` and write to a temp file.
3. Pull tags from the `Tags:` line at the bottom of `description.md` and write to a temp file.
4. Compress thumbnail if > 2 MB:
   ```bash
   sips -s format jpeg -s formatOptions 80 input.png --out output.jpg
   ```
5. Upload with `--publish-at` set to Tyler's chosen time in his timezone (Eastern).
6. Save the video_id to `~/content/youtube/<slug>/youtube_video_id.txt` so future updates can find it.

### Swap a thumbnail because CTR is weak

1. Find the video_id (`yt.py list --max 10` if needed).
2. Compress backup thumbnail to JPG < 2 MB.
3. Run `yt.py thumbnail VIDEO_ID --image NEW.jpg`.
4. Append a note to `~/content/youtube/<slug>/fallbacks.md` under "Thumbnail change log" with date + reason.

### Edit a title or description after publish

1. Edit `~/content/youtube/<slug>/description.md` or `titles.md` first (single source of truth).
2. Run `yt.py update VIDEO_ID --title "..."` or `--description-file path`.
3. If swapping the title to an A/B backup, also note it in `fallbacks.md`.

### Post a comment

```bash
python3 ~/.claude/skills/youtube/yt.py comment VIDEO_ID --text "$(cat comment.txt)"
```

## Rules

- **Always confirm before scheduling/uploading**, even if Tyler approved earlier in the session (matches `feedback_confirm_before_scheduling.md`).
- **Description bodies must not contain em dashes** — replace with hyphens before sending (matches `feedback_no_em_dashes.md`).
- **Strip the H1 and `---` frontmatter** from `description.md` before passing as `--description-file`.
- **Thumbnail max 2 MB** — compress with sips before uploading.
- **Tags max 500 chars total** — script auto-truncates but warn Tyler if any get dropped.
- **Default category is 28 (Science & Technology)** for tech tutorials. Use 27 (Education) for course-style content.
- **Save the video_id** after upload so future edits can find it. Recommend `~/content/youtube/<slug>/youtube_video_id.txt`.
- **Eastern Time** is Tyler's default timezone for `--publish-at` unless he says otherwise.

## Quotas

YouTube Data API v3 has a daily quota of 10,000 units (default project quota). Cost per call:
- `videos.insert` (upload): 1600 units — burns ~6 uploads/day max
- `videos.update`: 50 units
- `thumbnails.set`: 50 units
- `commentThreads.insert`: 50 units
- `videos.list` / `playlistItems.list`: 1 unit
- `search.list`: 100 units

If quota errors hit, tell Tyler to wait 24 hours or request a quota bump in Google Cloud Console.

## Troubleshooting

**`invalid_grant: Token has been expired or revoked`**
Run `python3 ~/.claude/skills/youtube/yt.py auth --reauth` to redo the browser flow.

**`forbidden: The user is not enabled for using the YouTube Partner Program`**
Some scopes (like setting custom thumbnails) require the YouTube channel to have verified the phone number on the channel. Tyler did this when he set up the channel — should not hit this in practice.

**`videoNotFound`**
The video_id is wrong, or it was deleted, or the channel that owns it isn't the authorized channel. Run `yt.py list` to verify which channel is authorized.

**`uploadLimitExceeded`**
You hit the daily upload limit (15 uploads/day for unverified channels, 100/day for verified). Tyler is verified — should not hit.
