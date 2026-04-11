---
name: pinterest-writer
description: Generate Pinterest-optimized pins from YouTube videos, shorts, or topics. Creates pin titles, descriptions, board assignments, and visual specs for static pins, video pins, and carousel pins. Triggers on: pinterest, create pins, pinterest post, pin this, pins for, pinterest content.
argument-hint: [youtube URL, video slug, topic, or "from shorts"]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(python3:*), WebSearch
user-invocable: true
---

Generate Pinterest-optimized content from YouTube videos, shorts, or any topic.

## Pinterest is a Visual Search Engine

Everything is driven by **keyword SEO**, not hashtags or social engagement. Think Google for images. Content lives for months/years.

## Pin Formats & Specs

| Format | Size | When to Use |
|--------|------|-------------|
| Static pin | 1000x1500 px (2:3) | Every YouTube video (3-5 designs each) |
| Video pin | 1080x1920 px (9:16) | Repurpose shorts/reels directly |
| Carousel pin | 1000x1500 px/card (2:3), 2-5 cards | Listicles, step-by-step, comparisons |

**2:3 ratio is mandatory for static/carousel** - algorithm penalizes other ratios.

## Workflow

### Step 1: Understand the Input

The user may provide:
- A YouTube video URL or slug (create pins from that video)
- "from shorts" (create video pins from this week's shorts)
- A topic (create pins from scratch)
- A content bundle slug (pull from `~/content/` structure)

### Step 2: Generate Pin Content

For each piece of source content, generate **1 pin**. Each pin needs:

#### Pin Title (required)
- **Keyword-first** - start with the main search term
- Be specific and descriptive
- 100 characters max
- Examples:
  - "Claude Code Tutorial: 5 Features That Save Hours Every Week"
  - "AI Content Automation: How to Post to 7 Platforms in 30 Seconds"
  - "YouTube Research Hack: Free Competitor Analysis with One Command"

#### Pin Description (required)
- 500 characters max, but aim for 200-300
- Natural long-tail keywords woven in (not stuffed)
- Include a call to action ("Watch the full tutorial on YouTube", "Save this for later")
- Write for humans first, SEO second
- Example: "Learn how to use Claude Code to automate your entire social media workflow. This step-by-step AI tutorial shows you how to build custom skills that save 10+ hours per week. No coding experience needed. Watch the full breakdown on YouTube."

#### Board Assignment (required)
- Assign to the most relevant board from Tyler's boards:
  - Claude Code Tutorials
  - AI Automation Tips
  - Social Media Automation
  - YouTube Creator Tips
  - AI for Entrepreneurs
  - AI Tools Reviews
  - AI Content Creation
  - Free AI Resources
  - Productivity Hacks with AI
  - Coding with AI
- Pin to the MOST relevant board first

#### Alt Text (required)
- Describe what's visually on the pin
- Include keywords naturally
- 500 characters max

#### Visual Direction (for static pins)
- Describe the pin design for Kie.ai or Canva generation
- Bold text overlay with the hook/title
- High contrast, readable at small sizes
- Leave space for text (usually top or center)
- Suggest colors that pop (bright on dark, or bold on light)
- Include terminal screenshots if relevant

### Step 3: Format for Each Pin Type

#### For Static Pins (from YouTube videos):
Create 1 infographic-style pin per topic. Use the established style:
- Light white/gray background with subtle tech circuit patterns
- Colorful icons + card layouts for each item
- Bold titles, clear descriptions, bullet points
- @tylerreedai at the bottom
- Generate with: `--count 1 --aspect-ratio 2:3 --resolution 2K`

#### For Video Pins (from shorts/reels):
- Use the same 9:16 video file
- Write a Pinterest-optimized title (keyword-first, not the same as YouTube title)
- Write a Pinterest-optimized description (longer, more keywords than YouTube caption)
- Assign to relevant board

#### For Carousel Pins (from carousel content):
- Adapt existing carousel slides to 2:3 ratio (1000x1500)
- Each card gets its own title and description
- 2-5 cards max
- First card must hook - it's the only one visible in the feed

### Step 4: Output Format

Save each pin to its own folder at `~/content/pinterest/<slug>/` with:
- `pin.png` - the generated image
- `copy.md` - all the Pinterest copy

After saving, update `~/content/pinterest/status.md`:

| Slug | Format | Board | Created | Scheduled | Posted |
|------|--------|-------|---------|-----------|--------|
| claude-code-skills | static | Claude Code Tutorials | 2026-04-09 | - | - |

```markdown
# Pinterest Pin - [Topic]
**Image:** ./pin.png

**Title:** [keyword-first title]

**Description:** [SEO-optimized description]

**Board:** [board name]

**Alt Text:** [visual description with keywords]

**Destination URL:** [YouTube link]
```

Generate the image with Kie.ai:
```bash
python3 ~/.claude/skills/thumbnail/generate_thumbnail.py "<prompt>" --model nano-banana-pro --aspect-ratio 2:3 --resolution 2K --output-dir ~/content/pinterest/ --slug <slug> --count 1
```

Then move the generated image into the pin folder as `pin.png`.

### Step 5: Present to User

Show the user all pin variations and ask:
1. Which pins to generate visuals for (static pins need Kie.ai generation at 2:3 ratio)
2. Which video pins to schedule (can go through Blotato if Pinterest is connected)
3. Any titles or descriptions to adjust

## Keyword Research

When writing pin content, check Pinterest search trends:
- Use WebSearch to look up "Pinterest trending [topic] 2026"
- Think about what someone would TYPE into Pinterest search
- Common Pinterest search patterns: "how to [X]", "[X] tutorial", "[X] tips", "best [X] for [Y]"
- Long-tail > short-tail (e.g., "claude code beginner tutorial step by step" > "claude code")

## Posting Rules

- New account warmup: 1-3 pins/day manually for 2-3 weeks
- After warmup: 5-15 pins/day
- Best times: 8-11 PM, Sun/Mon/Tue
- Fresh pins only - repins have minimal impact in 2026
- Each YouTube video should produce 1-2 Pinterest pins (1 static + optionally 1 video)
- Each short = 1 video pin
- Generate 1 image variant per pin (--count 1), not multiple
- Save each pin to its own folder: ~/content/pinterest/<slug>/pin.png + copy.md
- Pin style: light white/gray bg, tech circuit patterns, card layouts, colorful icons, @tylerreedai at bottom

## Tyler's Content Sources

Check these locations for source content:
- YouTube video packages: `~/youtube/<slug>/`
- Shorts scripts: `~/content/shorts/`
- LinkedIn text posts: `~/content/linkedin/text-posts/`
- Carousel slides: `~/content/linkedin/carousels/` and `~/content/instagram/carousels/`
- Content tracker: `~/content/content-tracker.md`

## Rules

- ALWAYS use keyword-first titles - this is the #1 SEO factor
- NEVER use hashtags in descriptions - they contribute ~1% on Pinterest
- Every pin needs alt text - major ranking factor in 2026
- Static pins MUST be 2:3 ratio (1000x1500) - algorithm penalizes other ratios
- Video pins use 9:16 (1080x1920) - same as shorts/reels
- Write descriptions for Pinterest search, not for social engagement
- Never use em dashes - use plain hyphens or commas
- Multiple pin designs per video is essential - test what works
- Assign every pin to the most relevant board
