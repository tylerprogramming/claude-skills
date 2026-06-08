---
name: kie-nano-banana
description: Generate or edit images with Google Nano Banana via Kie.ai — all 3 variants (Nano Banana, Nano Banana 2, Nano Banana Pro). Text-to-image and multi-image remix/edit, up to 4K. Triggers on: kie nano banana, nano banana, nano banana 2, nano banana pro, generate an image, edit image, remix images, combine images.
argument-hint: [image prompt]
allowed-tools: Bash(python3:*), Read, Write, Glob, Grep
user-invocable: true
---

Generate and edit images with **Google Nano Banana** through the Kie.ai jobs API. General-purpose image skill across all three Nano Banana variants. (For tuned YouTube thumbnails, `/thumbnail` is still the dedicated tool.)

> **Setup:** needs `KIE_API_KEY` in `~/.claude/.env`.

## Variants

| Key | Model id(s) | Max refs | Resolutions | Notes |
|---|---|---|---|---|
| `nano-banana-pro` (default) | `nano-banana-pro` | 8 | 1K/2K/4K | High quality t2i + remix |
| `nano-banana-2` | `nano-banana-2` | 14 | 1K/2K/4K | Most reference images; extra wide/tall ratios (1:4, 8:1…) |
| `nano-banana` | `google/nano-banana` (t2i), `google/nano-banana-edit` (edit) | 10 | — | Original; png/jpeg |

## Flow

1. **Parse** `$ARGUMENTS`. If the user supplies image(s) → edit/remix mode (auto-detected).
2. **Settings** (ask, or defaults):
   - **Variant:** default `nano-banana-pro`. Use `nano-banana-2` when remixing many references or for ultra-wide/tall ratios.
   - **Aspect ratio:** `16:9` (default) and the usual set; `nano-banana-2` adds `1:4`, `1:8`, `4:1`, `8:1`.
   - **Resolution:** `1K`, `2K` (default), `4K` (Pro / v2).
   - **Format:** `png` (default) or `jpg`.
   - **Variants:** default 3.
3. **Craft the prompt.** Show before generating. For edits, say what to keep vs change.
4. **Generate:**
```
python3 ~/.claude/skills/kie-nano-banana/generate.py "<prompt>" \
  --model nano-banana-pro --aspect-ratio 16:9 --resolution 2K --format png --count 3 \
  [--image <url-or-path> ...]   # any --image switches to edit/remix
  --slug <slug>
```
5. **Present:** output → `~/images/nano-banana/<date>-<slug>/`. Offer more variants, 4K, a different variant, or a remix pass on a favorite.

## Notes
- Passing `--image` switches to edit/remix; local files auto-upload.
- `nano-banana-2` supports up to 14 reference images and the widest aspect-ratio set.
