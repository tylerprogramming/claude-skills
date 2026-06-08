---
name: kie-kling-video
description: Generate AI video with Kling (Kuaishou) via Kie.ai — text-to-video and image-to-video, with optional native sound and multi-shot. Supports Kling 2.6, 3.0, and 2.1 Master/Pro. Triggers on: kie kling, kling video, kling, generate a kling video, animate this with kling, image to video kling.
argument-hint: [video prompt]
allowed-tools: Bash(python3:*), Read, Write, Glob, Grep
user-invocable: true
---

Generate video with **Kling (Kuaishou)** through the Kie.ai jobs API.

> **Setup:** needs `KIE_API_KEY` in `~/.claude/.env`.

## Models

| Key | Model id | Mode | Notes |
|---|---|---|---|
| `2.6-t2v` (default) | `kling-2.6/text-to-video` | text-to-video | sound optional; 5/10s; 1:1\|16:9\|9:16 |
| `2.6-i2v` | `kling-2.6/image-to-video` | image-to-video | 1 input image; 5/10s |
| `3.0` | `kling-3.0/video` | t2v + i2v | 3–15s, multi-shot, native audio, std/pro/4K |
| `2.1-master-t2v` | `kling/v2-1-master-text-to-video` | text-to-video | cfg_scale + negative prompt |
| `2.1-pro-i2v` | `kling/v2-1-pro` | image-to-video | tail/last frame support |

## Flow

1. **Parse** `$ARGUMENTS`. A start image → image-to-video.
2. **Settings** (ask, or defaults):
   - **Model:** default `2.6-t2v`. Use `3.0` for the best quality / 4K / multi-shot; `2.1-pro-i2v` for first→last-frame control.
   - **Duration:** 5 or 10s (Kling 3.0: 3–15s). The script snaps to allowed values.
   - **Aspect ratio:** `16:9` (default), `9:16`, `1:1`.
   - **Audio:** `--audio` for native sound (2.6 / 3.0).
   - **3.0 quality mode:** `--mode std|pro|4K` (default `pro`).
   - **2.1 tuning:** `--cfg-scale 0.5` and `--negative-prompt "..."`.
3. **Craft the prompt** (≤1000 chars for 2.6, ≤5000 for 2.1). Show before generating.
4. **Generate:**
```
python3 ~/.claude/skills/kie-kling-video/generate.py "<prompt>" \
  --model 2.6-t2v --duration 5 --aspect-ratio 16:9 [--audio] \
  [--image <url-or-path>] [--last-frame <url-or-path>] \
  [--mode pro] [--cfg-scale 0.5] [--negative-prompt "..."] \
  --slug <slug>
```
5. **Present:** output → `~/videos/kling/<date>-<slug>/`. Offer a longer clip, different model, or audio.

## Notes
- Kling is a strong, cost-effective image-to-video workhorse — good default for animating a still.
- Local input images are auto-uploaded.
- Default `9:16` for Shorts/Reels/TikTok.
