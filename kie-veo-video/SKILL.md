---
name: kie-veo-video
description: Generate AI video with Google Veo 3 / 3.1 via Kie.ai — text-to-video and image-to-video with native audio, up to 4K. Quality, Fast, and Lite tiers. Triggers on: kie veo, veo video, veo 3, veo 3.1, generate a veo video, google veo, cinematic ai video with audio.
argument-hint: [video prompt]
allowed-tools: Bash(python3:*), Read, Write, Glob, Grep
user-invocable: true
---

Generate video with **Google Veo 3 / 3.1** through Kie.ai's dedicated Veo endpoint. Veo's standout: **native synchronized audio** (dialogue, SFX, music) and strong prompt adherence.

> **Setup:** needs `KIE_API_KEY` in `~/.claude/.env`. Veo is premium — most expensive of the video skills (4K ~2× Fast). Mention this before generating.

## Models (tiers)

| Key | model | Notes |
|---|---|---|
| `veo3` | `veo3` | Veo 3.1 **Quality** — best fidelity |
| `veo3-fast` (default) | `veo3_fast` | Faster, cheaper, great default |
| `veo3-lite` | `veo3_lite` | Cheapest tier |

## Flow

1. **Parse** `$ARGUMENTS`. Images change the mode automatically:
   - 0 images → text-to-video
   - 1 image → image-to-video
   - 2 images → first + last frames
   - 3 images → reference-to-video
2. **Settings** (ask, or defaults):
   - **Tier:** default `veo3-fast`. Suggest `veo3` for hero shots.
   - **Aspect ratio:** `16:9` (default), `9:16`, `Auto`.
   - **Resolution:** `720p` (default), `1080p`, `4k`. (Script auto-fetches the hi-res file for 1080p/4k.)
   - **Duration:** `4`, `6`, or `8` seconds (default 8).
3. **Craft the prompt** — Veo rewards detail incl. audio cues (e.g. "she says: '…'", ambient sound, music). Show before generating.
4. **Generate:**
```
python3 ~/.claude/skills/kie-veo-video/generate.py "<prompt>" \
  --model veo3-fast --aspect-ratio 16:9 --resolution 720p --duration 8 \
  [--image <url-or-path> ...] [--translate] \
  --slug <slug>
```
5. **Present:** output → `~/videos/veo/<date>-<slug>/`. Note the audio is baked in. Offer Quality tier, 1080p/4k, or a vertical 9:16 cut.

## Notes
- Veo audio is included by default — no separate step needed.
- 4K costs roughly double Fast; confirm with the user before large batches.
- Local input images are auto-uploaded.
