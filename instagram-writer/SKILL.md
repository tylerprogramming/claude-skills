---
name: instagram-writer
description: Create high-engagement Instagram carousels using the proven @aiwithanushka design - warm cream background, terra cotta accent color, bold two-tone typography, 6-slide Cover-Pain-Solution-How-Results-CTA structure optimized for saves and comments. Triggers on: instagram carousel, instagram writer, write carousel, ig carousel, create instagram carousel, make a carousel, carousel for instagram.
argument-hint: [topic] or [topic + cta word]
allowed-tools: Read, Write, Bash(python3:*), Bash(pip3:*)
user-invocable: true
---

# Instagram Carousel Writer

Creates 6-slide Instagram carousels in the @aiwithanushka style that drives saves, shares, and comment-bait CTA engagement.

## Design system (hardcoded in renderer)

- Background: warm cream `#F5F0E8`
- Primary text: near-black `#1C1C1C`, bold
- Accent: terra cotta `#C4713A` on key words
- Font: Arial Bold, clean and large
- Slide counter: top-left (1/6, 2/6...)
- Dotted grid: top-right decorative element
- Brand: `AI` (terra cotta) bottom-left, `@handle` (gray) bottom-right
- Dimensions: 1080x1350 (4:5 ratio)

## Slide structure

| # | Type | Purpose |
|---|------|---------|
| 1 | cover | Big hook headline - stops the scroll |
| 2 | pain | Relatable problem (question format) + bullets |
| 3 | solution | The answer - key noun in accent color |
| 4 | how | Framework / steps with bullets |
| 5 | results | Proof / outcomes with bullets |
| 6 | cta | Summary lines + giant "Comment [WORD]" |

---

## Step 1: Gather inputs

Ask the user for:
- **Topic** - what the carousel teaches (e.g. "Claude Code skills", "AI content automation")
- **CTA word** - one ALL-CAPS word for the comment CTA (e.g. SKILLS, GUIDE, SYSTEM, LIST, TOOLKIT)
- **Handle** - their Instagram handle (default: `@tylerai_dev`)
- **Renderer** - which rendering framework to use:

  > Which renderer do you want?
  > **1. PIL** (default) - fast, free, pixel-perfect typography. Best for text-heavy carousels.
  > **2. Kie.ai** - AI-generated visuals for every slide. Richer look, ~$0.54/carousel, slower.
  > **3. Hybrid** (recommended) - PIL for text slides, Kie.ai asset for cover logo/visuals. Best of both.

If the user provides a topic in their command, infer CTA word from the topic (e.g. "skills" topic → "SKILLS").

**Renderer notes:**
- PIL → use `instagram_writer.py`
- Kie.ai → use `instagram_kie.py`
- Hybrid → use `instagram_writer.py` (it auto-loads logo assets from `assets/logo-{name}.png` when `"logo"` is set in the cover slide)

---

## Step 2: Generate slide content JSON

Create the JSON following this exact structure. Headlines must be SHORT lines (3-5 words max each) so the text is BIG and bold.

```json
{
  "topic": "<topic>",
  "handle": "@tylerai_dev",
  "brand_text": "AI",
  "slides": [
    {
      "type": "cover",
      "headline_lines": ["<2-3 words>", "<KEY WORD here>", "<2-3 words>"],
      "accent_words": ["<KEY WORD>"],
      "subtitle": "<One punchy line that hooks them into sliding>"
    },
    {
      "type": "pain",
      "headline_lines": ["Still doing this", "<PAIN WORD>?"],
      "accent_words": ["<PAIN WORD>"],
      "bullets": [
        "<Pain point 1 - short phrase>",
        "<Pain point 2 - short phrase>",
        "<Pain point 3 - short phrase>",
        "<Pain point 4 - short phrase>"
      ]
    },
    {
      "type": "solution",
      "headline_lines": ["The fix:", "<SOLUTION>", "is simpler"],
      "accent_words": ["<SOLUTION>"],
      "subtitle": "<Supporting line>",
      "bullets": []
    },
    {
      "type": "how",
      "headline_lines": ["The", "<FRAMEWORK>"],
      "accent_words": ["<FRAMEWORK>"],
      "bullets": [
        "<Step 1 - 4-7 words>",
        "<Step 2 - 4-7 words>",
        "<Step 3 - 4-7 words>",
        "<Step 4 - 4-7 words>"
      ]
    },
    {
      "type": "results",
      "headline_lines": ["Real", "<RESULTS>"],
      "accent_words": ["<RESULTS>"],
      "bullets": [
        "<Specific result 1>",
        "<Specific result 2>",
        "<Specific result 3>",
        "<Specific result 4>"
      ]
    },
    {
      "type": "cta",
      "summary_lines": [
        "<1-line takeaway from the carousel>",
        "<2nd supporting line>"
      ],
      "cta_action": "Comment",
      "cta_word": "<CTA_WORD>",
      "cta_subtext": "and I'll send you the full guide"
    }
  ]
}
```

### Content rules

- Headlines: 2-3 SHORT lines (3-5 words each) - the text must fill the slide vertically
- Accent words: 1-2 per slide, the most important noun or concept
- Bullets: max 4 per slide, short phrases (4-8 words)
- Pain slide: question format creates scroll-stopping relatability
- CTA word: single ALL-CAPS word, creates urgency to comment
- No em dashes - use commas or plain hyphens with spaces ( - )
- Write for saves first - the information must be worth saving

---

## Step 3: Save JSON and render

1. Create a 2-3 word kebab-case slug from the topic.

2. Set `OUTPUT_DIR=~/content/instagram/<slug>/`

3. Save the JSON:
   ```bash
   mkdir -p ~/content/instagram/<slug>/
   ```
   Write the JSON to `~/content/instagram/<slug>/slides.json`

4. Run the renderer:
   ```bash
   python3 ~/.claude/skills/instagram-writer/instagram_writer.py \
     ~/content/instagram/<slug>/slides.json \
     ~/content/instagram/<slug>/
   ```

   Output:
   - `slide_01.png` through `slide_06.png` - individual slides
   - `carousel.pdf` - combined PDF for Blotato upload

---

## Step 4: Write the caption

Generate an Instagram caption that drives saves and follows the keyword-first SEO approach:

```
<Hook line matching slide 1 - create urgency to save>

Save this. You'll use it.

<2-3 sentences expanding on the value>

Comment <CTA_WORD> and I'll DM you the full guide.

#claudecode #claudeai #ai #claudecodetips #aiautomation
```

Caption rules:
- Hook = first line, visible before "more" - make it a promise or bold claim
- "Save this" CTA early - saves are the #1 Instagram signal
- Comment CTA = drives comments (2nd biggest signal)
- Exactly 5 hashtags, always the same set
- No em dashes

Save the caption to `~/content/instagram/<slug>/caption.md`

---

## Step 5: Update status.md

After rendering (and again after scheduling), update `~/content/instagram/status.md`:

| Slug | Topic | Created | Scheduled | Posted |
|------|-------|---------|-----------|--------|
| claude-code-skills | Claude Code skills | 2026-04-09 | Apr 10 12pm | - |

---

## Step 6: Present results

Show the user:
1. A summary of each slide's content (1 line each)
2. The full caption
3. File paths:
   - Slides: `~/content/instagram/<slug>/slide_01.png` through `slide_06.png`
   - PDF: `~/content/instagram/<slug>/carousel.pdf`
   - Caption: `~/content/instagram/<slug>/caption.md`
4. Ask if they want to schedule via Blotato or adjust any slides
