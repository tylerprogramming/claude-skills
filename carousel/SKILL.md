---
name: carousel
description: Generate LinkedIn carousel PDFs using the Gamma API. Creates branded, styled carousel slides from text content and exports as PDF. Triggers on: create carousel, linkedin carousel, gamma carousel, make a carousel, carousel pdf, carousel from.
argument-hint: "[topic, slug, or file path]"
allowed-tools: Bash(python3:*), Bash(curl:*), Read, Write, Glob, Grep
user-invocable: true
---

# LinkedIn Carousel Generator (Gamma API)

Generate LinkedIn carousel PDFs using the Gamma API. Takes slide content, applies your brand theme, generates AI images, and exports a ready-to-post PDF.

## How to Use

### Step 1: Get the Content

Parse `$ARGUMENTS` for one of:
- A **topic or concept** to build slides from scratch
- A **file path** to an existing carousel outline (e.g. from `/content` or `/shorts`)
- A **video slug** to pull carousel content from `~/youtube/<slug>/social/`

If given a topic, write the slide content yourself. If given a file, read it and adapt.

### Step 2: Write the Slides

Create a markdown file with **6 slides** (no CTA slide - Tyler adds that separately). Each slide is separated by `\n---\n`.

**Slide structure:**
- **Slide 1 (Hook):** Bold headline that stops the scroll. Short, punchy, curiosity-driven.
- **Slides 2-5 (Value):** One key point per slide. Short paragraphs, bullet points, or numbered steps. Keep text brief - this is a visual format.
- **Slide 6 (Summary/Takeaway):** Wrap up with the key insight or actionable takeaway.

**Rules for slide text:**
- Keep each slide concise - 2-4 short lines max
- No hashtags on slides (those go in the LinkedIn post caption)
- No em dashes - use commas or hyphens instead
- No markdown formatting (bold, italic) - Gamma handles styling
- Each slide should stand alone but flow as a story

Save the slide content to a temp file or directly in the video package folder.

Example format:
```
The #1 Mistake Killing Your AI Workflow

Most people use AI like a search engine.
Here's how to use it like a system.
---
Stop prompting from scratch every time

If you've typed the same prompt twice,
you're wasting time.

Save it. Reuse it. Automate it.
---
Build reusable skills

A skill is a saved prompt template
that runs with one command.

/transcribe, /thumbnail, /seo
One command. Full workflow.
---
Chain skills into pipelines

Skills aren't just standalone tools.
They compose.

Research > Transcribe > Script > SEO > Publish
One session. Full video package.
---
Start with what you repeat

Look at your last week.
What did you prompt Claude to do more than once?

That's your first skill.
---
The system beats the prompt

One good skill saves more time
than a hundred clever prompts.

Build the system. Let AI do the rest.
```

### Step 3: Choose Settings

Ask the user about:

**Theme:** Run `--list-themes` first to show available Gamma themes.
```bash
python3 ~/.claude/skills/carousel/gamma_carousel.py dummy --list-themes
```
If the user has a preferred theme, use its ID. Otherwise let Gamma pick.

**Image model:**
- `flux-1-pro` (default, recommended - high quality)
- `dalle-3` (alternative)
- `flux-1-schnell` (fast, lower quality)

**Image style** (optional): Describe the visual style, e.g. "dark moody tech aesthetic", "clean minimal with blue accents", "vibrant gradients"

If the user says "defaults" or "just do it", use: flux-1-pro, no specific style, 6 slides.

### Step 4: Generate

Save the slide content to a markdown file, then run:

```bash
python3 ~/.claude/skills/carousel/gamma_carousel.py "<input_file>" \
  [--theme-id "<theme_id>"] \
  [--num-cards 6] \
  [--image-model flux-1-pro] \
  [--image-style "<style_description>"] \
  [--output "<output_path>"]
```

The script will:
1. Send the content to Gamma's API
2. Poll every 5 seconds until done
3. Download the PDF to the output path

### Step 5: Present Results

After generation:
1. Show the Gamma URL (user can view/edit in browser)
2. Show the PDF path
3. Show credits used
4. Remind the user to add their CTA slide separately (Kie.ai generated)
5. Ask if they want to regenerate with different settings or create another

## Output

All carousels save to `~/content/carousel/` regardless of source:
- Default: `~/content/carousel/<slug>/<slug>_carousel.pdf`
- User can override with `--output`

Note: This skill generates **LinkedIn PDF carousels** via Gamma API. For **Instagram visual carousels** with AI backgrounds, use `/carousel-app` instead.

## Rules

- Always 6 content slides (no CTA - Tyler adds that separately with Kie.ai)
- Use `textMode: preserve` so Gamma styles the text but doesn't rewrite it
- Use `cardSplit: inputTextBreaks` so `---` separators control slide breaks
- Use `4x5` dimensions for LinkedIn carousel format
- Keep slide text brief and scannable
- No em dashes anywhere
- No hashtags on slides
- Show the user the slide content before generating
- Uses GAMMA_API_KEY from `~/.claude/.env`
