---
name: rmbg
description: Remove backgrounds from images using Kie.ai AI-powered remix. Produces clean transparent PNG cutouts preserving all subject detail. Triggers on: remove background, transparent png, cut out, isolate subject, background removal.
argument-hint: "[file_or_folder] [--output path]"
allowed-tools: Bash(python3:*), Bash(curl:*), Read, Glob
user-invocable: true
---

# Background Remover (Kie.ai)

Remove backgrounds from images using Kie.ai's AI remix mode. Produces clean, transparent PNG cutouts while preserving every detail of the subject - likeness, hair, clothing, edges.

## How to Use

### Step 1: Identify the Source

Parse `$ARGUMENTS` for a file or folder path. If not provided, ask the user.

### Step 2: Confirm Settings

Ask about:
- **Resolution**: 1K, 2K (default, recommended), or 4K
- **Custom prompt** (optional): If the user wants specific instructions beyond standard background removal

Show estimated cost before running:
- 1K/2K: $0.09 per image
- 4K: $0.12 per image
- Example: 5 images at 2K = $0.45

### Step 3: Run

```bash
python3 ~/.claude/skills/rmbg/remove_bg.py "<file_or_folder>" \
  --resolution <1K|2K|4K> \
  [--output "<output_path>"] \
  [--prompt "<custom_prompt>"]
```

### Step 4: Report Results

Tell the user how many images were processed, the output directory, and total cost.

## Output Structure

```
~/images/nobg/
  photo1_nobg.png
  photo2_nobg.png
```

Output is always PNG (transparency requires it). Files are named `<original_name>_nobg.png`.

## How It Works

Uses Kie.ai Nano Banana 2 in remix mode with `auto` aspect ratio. Uploads the original image, then generates a new version with a prompt instructing the AI to isolate the subject on a transparent background. The AI preserves all subject details while cleanly removing the background.

## Rules

- Always show estimated cost before processing
- Default to 2K resolution
- Output is always PNG format (required for transparency)
- Output always goes to `~/images/nobg/` unless overridden
- Uses KIE_API_KEY from `~/.claude/.env`
