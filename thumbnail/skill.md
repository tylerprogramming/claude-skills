---
name: thumbnail
description: Generate YouTube thumbnails using Kie.ai image APIs (Nano Banana 2, Nano Banana Pro, or Seedream 4.5). Supports text-to-image and remix (image + text). Creates multiple variants with configurable settings. Triggers on: create thumbnail, generate thumbnail, thumbnail for, make a thumbnail, youtube thumbnail, remix thumbnail.
argument-hint: [video title or concept]
allowed-tools: Bash(python3:*), Read, Write, Glob, Grep
user-invocable: true
---

Generate YouTube thumbnail options using Kie.ai image generation APIs.

## Available Models

| | Nano Banana 2 | Nano Banana Pro | Seedream 4.5 |
|---|---|---|---|
| **Model flag** | `--model nano-banana-2` | `--model nano-banana-pro` | `--model seedream` |
| **Remix (image input)** | Yes (up to 14 images) | Yes (up to 8 images) | No (text-to-image only) |
| **Google Search grounding** | Yes (`--google-search`) | No | No |
| **Resolution** | `1K` / `2K` / `4K` | `1K` / `2K` / `4K` | `basic` (2K) / `high` (4K) |
| **Output format** | `png` / `jpg` | `png` / `jpg` | `png` only |
| **Aspect ratios** | 1:1, 1:4, 1:8, 2:3, 3:2, 3:4, 4:1, 4:3, 4:5, 5:4, 8:1, 9:16, 16:9, 21:9, auto | 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9, auto | 1:1, 2:3, 3:2, 3:4, 4:3, 9:16, 16:9, 21:9 |
| **Max prompt** | 20,000 chars | 20,000 chars | 3,000 chars |
| **Cost per image** | $0.09 (1K/2K), $0.12 (4K) | $0.09 (1K/2K), $0.12 (4K) | ~$0.025 |

## Parsing Arguments

Parse `$ARGUMENTS` for a video title, concept, or description. The user may also mention reference images or a specific style. Everything else will be asked interactively.

## Flow

### Step 1: Choose the Model

Ask the user which model they want:

1. **Nano Banana 2** — Latest model, supports up to 14 reference images, Google Search grounding for real-time info (~$0.09/image)
2. **Nano Banana Pro** — Great quality, supports remix with up to 8 reference images (~$0.09/image)
3. **Seedream 4.5** — Fast and cheap (~$0.025/image), text-to-image only, great for rapid iteration

If the user mentions remix or reference images, auto-select Nano Banana 2 (most capable for remix).
If the user mentions Google Search or real-time info, must use Nano Banana 2.
If the user says "defaults" or doesn't care, use Nano Banana 2.

### Step 2: Determine the Mode

Ask the user which mode they want:

1. **Text-to-image** — Generate thumbnails from a text prompt only (all models)
2. **Remix** — Generate thumbnails using reference image(s) + a text prompt (Nano Banana 2 or Pro only)

If the user already specified reference images or said "remix", skip this question.
If they chose Seedream, skip this — it's always text-to-image.

### Step 3: Collect Settings

Ask the user for their preferences. Present the options clearly and let them choose:

**Aspect ratio:**
- `16:9` — Standard YouTube thumbnail (recommended)
- `1:1` — Square (Instagram, etc.)
- `9:16` — Vertical (Shorts, TikTok, Stories)
- Other ratios available depending on model (see table above)
- Nano Banana 2 has extra wide/tall ratios: `1:4`, `1:8`, `4:1`, `8:1`

**Resolution:**
- For Nano Banana 2 / Pro: `1K`, `2K` (recommended), `4K`
- For Seedream: `basic` (2K) or `high` (4K) — the script also accepts `1K`/`2K`/`4K` and auto-maps them

**Number of variants:**
- Default: 3 (suggest this — gives options without being expensive)
- Let the user pick 1-10

**Output format (Nano Banana 2 / Pro only):**
- `png` (default, lossless)
- `jpg` (smaller files)

**Google Search grounding (Nano Banana 2 only):**
- Enable with `--google-search` flag
- Uses real-time web info to inform the generation
- Useful for generating images based on current trends, real products, etc.

If the user seems in a hurry or says "just do it" / "defaults are fine", use: Nano Banana 2, 16:9, 2K, 3 variants, png.

### Step 4: Collect Reference Images (Remix Mode Only)

If the user chose remix mode (Nano Banana 2 or Pro), ask for reference images:
- Up to 14 images for Nano Banana 2, up to 8 for Pro (JPEG, PNG, or WebP, max 30MB each)
- The user can provide:
  - **URLs** — pass directly to the API
  - **A local folder path** — the script auto-uploads local files via Kie.ai's upload endpoint
- Ask what they want to keep from the reference (style, composition, colors, subject) and what to change

### Step 5: Craft the Prompt

This is critical. Take the user's video title/concept and their preferences, and craft a detailed image generation prompt.

**Good thumbnail prompts include:**
- Visual composition (close-up face, split screen, object on dark background, etc.)
- Color palette and mood (vibrant, dark/moody, neon, clean/minimal)
- Key visual elements (terminal window, code, person's expression, icons)
- Style direction (photorealistic, 3D render, illustration, cinematic)
- Lighting (dramatic side lighting, soft studio, neon glow)

**Rules for thumbnail prompts:**
- Do NOT include text in the prompt — thumbnail text is always added in an editor afterward
- Keep composition simple — one focal point works best
- Leave visual space for text overlay (usually left or right third)
- High contrast elements read well at small sizes
- Seedream has a 3,000 char limit — keep prompts concise for that model

Show the user the prompt you've crafted and ask if they want to adjust it before generating.

### Step 6: Generate

Run the script with the collected settings:

```
python3 ~/.claude/skills/thumbnail/generate_thumbnail.py "<prompt>" \
  --model <nano-banana-2|nano-banana-pro|seedream> \
  --count <count> \
  --aspect-ratio <ratio> \
  --resolution <resolution> \
  --format <format> \
  --slug <slug> \
  [--reference-images <url1> <url2> ...] \
  [--google-search]
```

Mention the estimated cost before running:
- **Nano Banana 2 / Pro:** 1K/2K = $0.09/image, 4K = $0.12/image
- **Seedream 4.5:** ~$0.025/image regardless of quality
- Example: 3 variants with Nano Banana 2 at 2K = $0.27
- Example: 3 variants with Seedream = $0.075

Wait for it to finish. Each image takes ~10-30 seconds.

If it fails:
- **401**: KIE_API_KEY not set or invalid — check `~/.claude/.env`
- **402**: Insufficient credits — user needs to top up at kie.ai
- **429**: Rate limited — wait a moment and retry
- **500/501**: Server error — retry once, then ask user to try later

### Step 7: Present Results

After generation:
1. Tell the user how many thumbnails were generated and which model was used
2. Show the output directory path so they can open and review
3. Show the actual cost
4. Ask what they want to do next:
   - **More variants** — same prompt, more images (use same `--slug`)
   - **Try a different model** — regenerate with another model for comparison
   - **Remix one** — take a generated thumbnail and remix it (Nano Banana 2 or Pro only)
   - **New concept** — try a completely different visual direction
   - **Done** — they're happy

### Step 8: Iterate

For follow-up generations:
- Use the same `--slug` to keep everything in one folder
- The script auto-increments thumbnail numbers so nothing gets overwritten
- Metadata.json tracks all generations with their prompts, settings, and which model was used

For remixing a previously generated thumbnail:
- The image URLs from Kie.ai expire after 24 hours
- The script can upload local files automatically — just pass the local path to `--reference-images`

## Rules

- All output goes to `~/youtube/thumbnails/` organized by date and slug
- Always ask which model to use — don't assume
- Always ask for settings interactively — don't assume
- Show the crafted prompt to the user before generating
- Mention cost before generating
- Default to 16:9 for YouTube thumbnails
- Do NOT include text/words in image prompts — text overlay is added separately
- Keep compositions simple and high-contrast for thumbnail readability
- Max reference images: 14 for Nano Banana 2, 8 for Pro
- If user wants remix, must use Nano Banana 2 or Pro — Seedream is text-only
- Google Search grounding only available on Nano Banana 2
