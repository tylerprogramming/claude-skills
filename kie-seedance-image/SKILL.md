---
name: kie-seedance-image
description: Generate images with ByteDance Seedream via Kie.ai — text-to-image and multi-image edit. Fast, cheap, high quality at 2K/4K. Triggers on: kie seedance image, seedream, seedance image, generate an image, text to image, edit this image, ai image from text.
argument-hint: [image prompt]
allowed-tools: Bash(python3:*), Read, Write, Glob, Grep
user-invocable: true
---

Generate images with **ByteDance Seedream** through the Kie.ai jobs API. (Seedream is ByteDance's image model — the still-image sibling of Seedance video.)

> **Setup:** needs `KIE_API_KEY` in `~/.claude/.env`.

## Models

| Key | Model id | Mode | Notes |
|---|---|---|---|
| `4.5` (default) | `seedream/4.5-text-to-image` | text-to-image | 2K or 4K |
| `4.5-edit` | `seedream/4.5-edit` | image edit | Up to 14 input images; auto-selected when you pass `--image` |
| `5-lite` | `seedream/5-lite-text-to-image` | text-to-image | Lighter/cheaper |

## Flow

1. **Parse** `$ARGUMENTS` for the concept. If the user gives image(s) to edit/combine → edit mode.
2. **Settings** (ask, or defaults on "just do it"):
   - **Aspect ratio:** `16:9` (default), `1:1`, `9:16`, `4:3`, `3:4`, `2:3`, `3:2`, `21:9`.
   - **Quality:** `basic` (2K, default) or `high` (4K).
   - **Variants:** default 3.
3. **Craft the prompt** (≤3000 chars). Show it before generating.
4. **Generate:**
```
python3 ~/.claude/skills/kie-seedance-image/generate.py "<prompt>" \
  --model 4.5 --aspect-ratio 16:9 --quality basic --count 3 \
  [--image <url-or-path> ...]   # any --image switches to seedream/4.5-edit
  --slug <slug>
```
5. **Present:** output → `~/images/seedream/<date>-<slug>/`. Offer more variants, 4K, a different ratio, or an edit pass on a favorite.

## Notes
- Passing `--image` auto-switches to the edit model (combine/restyle up to 14 images).
- Local files are auto-uploaded; URLs pass through.
- For YouTube thumbnails specifically, `/yt-thumbnail` is still the tuned tool; this skill is the general-purpose Seedream image generator.
