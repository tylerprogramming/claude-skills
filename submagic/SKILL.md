---
name: submagic
description: Burn word-by-word on-screen captions onto an edited video using the Submagic API. Uploads the mp4 directly to Submagic (bypassing Google Drive), polls until done, and downloads the captioned video. Does NOT generate platform post copy (use /content or manual captions.md for that) and does NOT replace /transcribe. Triggers on: submagic, burn captions, add captions to video, caption this video, submagic caption.
argument-hint: /path/to/edited-video.mp4
allowed-tools: Bash(python3:*), Read, Write
user-invocable: true
---

Burn word-by-word on-screen captions onto the video at $ARGUMENTS using Submagic.

## Scope

- This skill ONLY burns visual captions onto the video via Submagic.
- It does NOT generate social media post copy (YouTube Shorts / TikTok / Reels / LinkedIn).
- It does NOT replace `/transcribe` - Whisper stays the source for raw transcripts.

## How it works

Uses Submagic's direct upload endpoint `POST /v1/projects/upload` with `multipart/form-data`. The mp4 is streamed straight to Submagic, so there is no Google Drive dependency, no virus-scan redirect problem on large files, and the requested `userThemeId` is preserved reliably (the older Drive-URL path sometimes got themes silently swapped under concurrent jobs).

## Instructions

1. Verify the file exists and is an mp4.

2. Run the script:
   ```
   python3 ~/.claude/skills/submagic/submagic_caption.py "$ARGUMENTS"
   ```

3. The script will:
   - Upload the mp4 directly to Submagic (multipart)
   - Poll `GET /v1/projects/{id}` every 15s until `completed` or `failed`
   - Warn if Submagic silently swapped the requested theme (happens if the theme UUID was very recently edited in the dashboard - propagation delay)
   - Download the captioned mp4 to `~/content/submagic/<original-name> - captioned-<short-project-id>.mp4`

4. If the script fails, check `~/.claude/.env` for:
   - `SUBMAGIC_API_KEY`
   - `SUBMAGIC_THEME_ID` (the custom theme UUID - grab it from the Submagic dashboard if changing)

5. Report the output path to the user. Do NOT generate platform captions unless asked.

## Finding a theme UUID

Submagic's public API has no "list my custom themes" endpoint. To switch themes:

1. Log into https://app.submagic.co
2. Open DevTools (Cmd+Opt+I) -> Network tab
3. Navigate to the themes page
4. Find the XHR that returns a JSON array of themes - each has an `id` field
5. Copy the `id` of the theme you want and paste it into `SUBMAGIC_THEME_ID` in `~/.claude/.env`

Preset templates (Beast, Hormozi 1-5, Doug, etc.) are available via a separate `templateName` field if ever needed - not wired into the script today.
