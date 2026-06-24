---
name: kie-gpt-image
description: Generate or edit images with OpenAI GPT Image 2 via Kie.ai — text-to-image and multi-image edit (up to 16 references), 1K/2K/4K. Strong photorealism, clean editing, sharp text rendering. Triggers on: kie gpt image, gpt image, gpt image 2, gpt-image-2, openai image, generate an image, edit image, remix images.
argument-hint: [image prompt]
allowed-tools: Bash(python3:*), Read, Write, Glob, Grep
user-invocable: true
---

Generate and edit images with **OpenAI GPT Image 2** through the Kie.ai jobs API. Best for photorealism, accurate text-in-image, product shots, and clean edits.

> **Setup:** needs `KIE_API_KEY` in `~/.claude/.env`.

## Modes

| Mode | Model id | Refs | Notes |
|---|---|---|---|
| text-to-image (default) | `gpt-image-2-text-to-image` | — | Pure prompt → image |
| image-to-image / edit | `gpt-image-2-image-to-image` | up to 16 | Auto-selected when any `--image` is passed |

## Flow

1. **Parse** `$ARGUMENTS`. If the user supplies image(s) → image-to-image mode (auto-detected).
2. **Settings** (ask, or defaults):
   - **Aspect ratio:** `auto` (default). Options: `1:1`, `3:2`, `2:3`, `4:3`, `3:4`, `5:4`, `4:5`, `16:9`, `9:16`, `2:1`, `1:2`, `3:1`, `1:3`, `21:9`, `9:21`.
   - **Resolution:** `1K`, `2K` (default), `4K`.
   - **Variants:** default 3.
3. **Craft the prompt.** Show before generating. For edits, say what to keep vs change.
4. **Generate:**
```
python3 ~/.claude/skills/kie-gpt-image/generate.py "<prompt>" \
  --aspect-ratio auto --resolution 2K --count 3 \
  [--image <url-or-path> ...]   # any --image switches to image-to-image (up to 16)
  --slug <slug>
```
5. **Present:** output → `~/images/gpt-image/<date>-<slug>/`. Offer more variants, 4K, or an edit pass on a favorite.

## Resolution constraints (enforced by the script)
- `5:4` and `4:5` → **1K only**.
- `1:1` cannot go **4K** (falls back to 2K).
- `auto` aspect ratio is limited to **1K** — set an explicit ratio for 2K/4K.

## Notes
- Output is PNG. Local `--image` files auto-upload via the shared `_kie` client.
- For YouTube thumbnails specifically, `/thumbnail` is still the tuned tool; this is general-purpose.
