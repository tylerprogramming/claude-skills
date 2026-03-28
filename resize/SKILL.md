---
name: resize
description: Resize images to social media aspect ratios using Kie.ai AI-powered remix. Intelligently adjusts composition without distorting or skewing. Triggers on: resize images, resize for social, social media sizes, resize this image.
argument-hint: "[file_or_folder] [--output path]"
allowed-tools: Bash(python3:*), Bash(curl:*), Read, Glob
user-invocable: true
---

# Image Resizer (Kie.ai)

Resize images to social media aspect ratios using Kie.ai's AI remix mode. Instead of dumb cropping or stretching, the AI intelligently adjusts the composition to fit each aspect ratio while preserving the subject's likeness and all visual details.

## How to Use

### Step 1: Identify the Source

Parse `$ARGUMENTS` for a file or folder path. If not provided, ask the user.

### Step 2: Ask Which Sizes

Present the available social media presets and let the user pick which ones they want:

| Preset | Aspect Ratio | Use Case |
|--------|-------------|----------|
| Instagram Post | 1:1 | Square feed posts |
| Instagram Portrait | 4:5 | Tall feed posts |
| Instagram Story / Reels | 9:16 | Vertical stories and reels |
| YouTube Thumbnail | 16:9 | Standard widescreen |
| LinkedIn Post | 3:2 | LinkedIn feed |
| Twitter / X Post | 16:9 | X feed posts |
| Facebook Post | 3:2 | Facebook feed |
| Pinterest Pin | 2:3 | Pinterest vertical |
| Ultrawide Banner | 21:9 | Website banners |

The user can also specify any custom Kie.ai ratio: `1:1, 1:4, 1:8, 2:3, 3:2, 3:4, 4:1, 4:3, 4:5, 5:4, 8:1, 9:16, 16:9, 21:9, auto`

If the user says "all social" or "all presets", use: `1:1 4:5 9:16 16:9 3:2`

### Step 3: Confirm Settings

Ask about:
- **Resolution**: 1K, 2K (default, recommended), or 4K
- **Format**: png (default) or jpg

Show estimated cost before running:
- 1K/2K: $0.09 per image per ratio
- 4K: $0.12 per image per ratio
- Example: 1 image x 5 ratios at 2K = $0.45

### Step 4: Run

```bash
python3 ~/.claude/skills/resize/resize_images.py "<file_or_folder>" \
  --ratios <ratio1> <ratio2> ... \
  --resolution <1K|2K|4K> \
  --format <png|jpg> \
  [--output "<output_path>"]
```

### Step 5: Report Results

Tell the user how many images were generated, the output directory, and total cost.

## Output Structure

```
~/images/resized/
  <original_filename>/
    <original_filename>_1x1.png
    <original_filename>_4x5.png
    <original_filename>_9x16.png
    <original_filename>_16x9.png
    ...
```

## How It Works

Uses Kie.ai Nano Banana 2 in remix mode. Uploads the original image, then generates a new version at each target aspect ratio with a prompt that instructs the AI to preserve the subject, likeness, colors, and style while naturally adjusting the composition to fit. No distortion, no skewing, no dumb cropping.

## Rules

- Always show available ratios and let the user pick
- Always show estimated cost before generating
- Default to 2K resolution and png format
- Output always goes to `~/images/resized/` unless overridden
- Each source image gets its own subfolder
- Uses KIE_API_KEY from `~/.claude/.env`
