---
name: kie-wan-video
description: Generate AI video with Alibaba Wan via Kie.ai — text-to-video and image-to-video, with first/last-frame control and optional audio drive. Supports Wan 2.7, 2.6, and 2.5. Triggers on: kie wan, wan video, wan, generate a wan video, animate this with wan, image to video wan.
argument-hint: [video prompt]
allowed-tools: Bash(python3:*), Read, Write, Glob, Grep
user-invocable: true
---

Generate video with **Alibaba Wan** through the Kie.ai jobs API.

> **Setup:** needs `KIE_API_KEY` in `~/.claude/.env`.

## Models

| Key | Model id | Mode | Notes |
|---|---|---|---|
| `2.7-t2v` (default) | `wan/2-7-text-to-video` | text-to-video | 2–15s; 720p/1080p; optional `--audio-url` |
| `2.7-i2v` | `wan/2-7-image-to-video` | image-to-video | first + last frame; 2–15s |
| `2.6-i2v` | `wan/2-6-image-to-video` | image-to-video | 5/10/15s |
| `2.5-t2v` | `wan/2-5-text-to-video` | text-to-video | ≤800-char prompt |

## Flow

1. **Parse** `$ARGUMENTS`. A start image → image-to-video.
2. **Settings** (ask, or defaults):
   - **Model:** default `2.7-t2v`. Use `2.7-i2v` for first→last-frame interpolation.
   - **Duration:** seconds. 2.7 = 2–15 (free int); 2.6 = 5/10/15; 2.5 = 5/10. Script snaps to allowed.
   - **Resolution:** `720p` or `1080p` (default `1080p` for 2.x).
   - **Aspect ratio:** `16:9` (default), `9:16`, `1:1`, `4:3`, `3:4`. (Wan 2.7 t2v calls this field `ratio` — handled for you.)
   - **Negative prompt / audio drive (2.7-t2v):** `--negative-prompt`, `--audio-url`.
   - **Prompt extension:** on by default; `--no-prompt-extend` to disable.
3. **Craft the prompt.** Show before generating.
4. **Generate:**
```
python3 ~/.claude/skills/kie-wan-video/generate.py "<prompt>" \
  --model 2.7-t2v --duration 5 --resolution 1080p --aspect-ratio 16:9 \
  [--image <url-or-path>] [--last-frame <url-or-path>] \
  [--negative-prompt "..."] [--audio-url <url>] [--no-prompt-extend] \
  --slug <slug>
```
5. **Present:** output → `~/videos/wan/<date>-<slug>/`. Offer longer/higher-res, a different Wan version, or first→last-frame mode.

## Notes
- Wan 2.7 supports continuation and audio-driven motion; great for precise first/last-frame shots.
- Local input images are auto-uploaded.
