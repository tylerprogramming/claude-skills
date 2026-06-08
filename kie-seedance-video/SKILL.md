---
name: kie-seedance-video
description: Generate AI video with ByteDance Seedance via Kie.ai — text-to-video and image-to-video, with optional audio. Supports Seedance 2, 2-Fast, 1.5 Pro, and 1.0 Pro/Lite. Triggers on: kie seedance, seedance video, seedance, generate a video, text to video, image to video, animate this image, make an ai video.
argument-hint: [video prompt]
allowed-tools: Bash(python3:*), Read, Write, Glob, Grep
user-invocable: true
---

Generate video with **ByteDance Seedance** through the Kie.ai jobs API.

> **Setup:** needs `KIE_API_KEY` in `~/.claude/.env`. Get one at https://kie.ai.

## Models

| Key | Model id | Modes | Audio | Notes |
|---|---|---|---|---|
| `seedance-2` (default) | `bytedance/seedance-2` | t2v + i2v | yes (on by default) | Flagship multimodal; 480p/720p/1080p; 4–15s |
| `seedance-2-fast` | `bytedance/seedance-2-fast` | t2v + i2v | yes | Faster; 480p/720p only |
| `1.5-pro` | `bytedance/seedance-1.5-pro` | t2v + i2v | optional (off) | Durations 4/8/12s |
| `1-pro-t2v` / `1-pro-i2v` | `bytedance/v1-pro-*` | t2v / i2v | no | Seedance 1.0 Pro; 5 or 10s |
| `1-pro-fast-i2v` | `bytedance/v1-pro-fast-image-to-video` | i2v | no | 720p/1080p only |
| `1-lite-t2v` / `1-lite-i2v` | `bytedance/v1-lite-*` | t2v / i2v | no | Cheapest tier |

## Flow

### Step 1: Parse the request
`$ARGUMENTS` is the video prompt. Detect whether the user gave a **start image** (path/URL) → that means image-to-video.

### Step 2: Pick the model & settings (ask, or use defaults on "just do it")
- **Model:** default `seedance-2`. Use a `1-lite-*` for cheap drafts; `1.5-pro` for a good audio/cost balance.
- **Mode:** image-to-video if a start image was given (`--image`), else text-to-video. `seedance-2` / `1.5-pro` do both; the `*-t2v`/`*-i2v` ids are mode-locked.
- **Duration:** seconds. seedance-2 = 4–15; 1.5-pro = 4/8/12; v1 = 5/10. The script snaps your number to the model's allowed set.
- **Resolution:** `480p` / `720p` (default) / `1080p`.
- **Aspect ratio:** `16:9` (default), `9:16`, `1:1`, `4:3`, `3:4`, `21:9`.
- **Audio:** add `--audio` for seedance-2 / 1.5-pro (native sound).
- **Last frame (optional):** `--last-frame <url/path>` for first+last-frame interpolation (seedance-2, lite-i2v).

### Step 3: Craft the prompt
Describe motion, subject, camera moves, lighting, pace. Show it to the user before generating. For image-to-video, the prompt describes how the still should move.

### Step 4: Generate
```
python3 ~/.claude/skills/kie-seedance-video/generate.py "<prompt>" \
  --model seedance-2 \
  [--image <url-or-path>] [--last-frame <url-or-path>] \
  --duration 5 --resolution 720p --aspect-ratio 16:9 \
  [--audio] [--camera-fixed] [--count 1] \
  --slug <slug>
```
Videos take ~1–5 min. Mention that cost scales with model, resolution, duration, and audio (Kie.ai bills per generation — exact price is on the Kie Market page).

### Step 5: Present results
Output → `~/videos/seedance/<date>-<slug>/`. Show the path and offer: another duration/resolution, switch to a cheaper/pricier model, add audio, or animate a different still.

## Rules
- Image-to-video models require `--image`; the script auto-uploads local files.
- Don't bake on-screen text into the prompt — burn captions later (e.g. `/submagic`).
- Default to `16:9` for YouTube, `9:16` for Shorts/Reels/TikTok.
