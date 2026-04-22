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

## The Winning Design System (Proven)

Tyler's top-performing pin is `~/content/pinterest/001-5-skills/pin.png` (Day 1). All new pins should match its design system:

- **Background:** warm cream / off-white (`#FAF7F2`) with a very subtle circuit-pattern texture (barely visible). NOT purple, NOT lavender.
- **Icons:** square icon per card, Claude terracotta orange gradient (`#D97757 → #C96342`). This is the Anthropic/Claude brand color.
- **Cards:** 5 horizontal white rectangles with soft shadow and rounded corners, stacked vertically.
- **Typography:** dark navy (almost black) ALL CAPS headline at top, 2 lines max. Bold uppercase label per card, one-line descriptor, 3 checkmark bullets with small orange checkmarks.
- **Handle:** small `@tylerreedai` centered at bottom.

**The 5-card format is the winning pattern.** Headline uses a number ("5 X That Y", "25 Skills", "30 Pieces"). Each card: icon + bold label + descriptor + 3 checkmarks. Proven to be save-worthy.

### Consistency trick
When generating a new pin, **pass Day 1 as a reference image** so Nano Banana keeps the design system matched:
```
--reference-images ~/content/pinterest/001-5-skills/pin.png
```

## Title Formulas That Work (Pinterest SEO)

Pinterest is a search engine. Titles that ranked for Tyler:
- `"5 [X] That [Outcome]"` — "5 AI Tools That Replaced Canva in My Content Workflow"
- `"How to [X] in N Minutes"` — "How to Create Your First Claude Code Routine in 2 Minutes"
- `"[Tool] vs [Tool]"` — "Seedance 2 vs Kling 3: Same Prompt, Shocking Difference"
- `"[Outcome] for [Price]"` — "Kling 3 VFX Shots That Used to Cost $10,000 (Now 50 Cents Each)"
- `"The [Thing] [Playbook|Blueprint|Stack] in 2026"` — "The Solopreneur AI Stack 2026"

Always lead with the primary search keyword. <100 chars.

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
- Use one of the formulas above
- 100 characters max

#### Pin Description (required)
- 500 characters max, aim for 200-300
- Natural long-tail keywords woven in (not stuffed)
- Include a "Save this" CTA
- Write for humans first, SEO second

#### Board Assignment (required)
Tyler's boards:
- Claude Code Tutorials
- AI Automation Tips
- Social Media Automation
- YouTube Creator Tips
- AI for Entrepreneurs
- AI Tools Reviews
- **AI Content Creation** ← current top performer, test new pins here first
- Free AI Resources
- Productivity Hacks with AI
- Coding with AI

**Testing insight:** AI Content Creation is Tyler's best-performing board. New pins should go there first, then diversify to other boards only after you see performance data.

#### Alt Text (required)
- Describe what's visually on the pin
- Include keywords naturally
- 500 characters max

### Step 3: Folder + File Layout

Create folder `~/content/pinterest/NNN-slug/` where NNN is zero-padded (001, 002, ... 028). This sorts correctly in Finder and matches the established pattern.

Inside each folder:
- `pin.png` - the generated image (1000x1500, 2:3)
- `copy.md` - all Pinterest copy (see template below)

### Step 4: Image Generation

Generate via Kie.ai Nano Banana Pro with Day 1 as reference:

```bash
python3 ~/.claude/skills/thumbnail/generate_thumbnail.py "<prompt>" \
  --model nano-banana-pro \
  --aspect-ratio 2:3 \
  --resolution 2K \
  --slug pinterest-NNN \
  --count 1 \
  --reference-images ~/content/pinterest/001-5-skills/pin.png
```

Prompt template (fill in the bracketed bits):
```
Vertical Pinterest infographic 2:3 aspect ratio. Clean warm off-white cream colored background (#FAF7F2) with very subtle light circuit-pattern texture barely visible, NOT purple or lavender. Bold dark navy almost black all-caps headline at top split across two lines. 5 horizontal cards stacked vertically, each card is a white rectangle with soft shadow and rounded corners. Each card has a square icon on the left with a warm Claude terracotta orange gradient (#D97757 to #C96342, the Claude AI brand color), then bold uppercase label, one-line descriptor, and 3 checkmark bullet points with small orange checkmarks. Small '@tylerreedai' handle at bottom center. Clean minimalist style, warm Anthropic Claude brand aesthetic.

Headline: '<HEADLINE IN CAPS>'.
Card 1 <icon> icon '<LABEL> - <descriptor> / <bullet 1> / <bullet 2> / <bullet 3>'.
Card 2 <icon> icon '<LABEL> - <descriptor> / <bullet 1> / <bullet 2> / <bullet 3>'.
Card 3 <icon> icon '<LABEL> - <descriptor> / <bullet 1> / <bullet 2> / <bullet 3>'.
Card 4 <icon> icon '<LABEL> - <descriptor> / <bullet 1> / <bullet 2> / <bullet 3>'.
Card 5 <icon> icon '<LABEL> - <descriptor> / <bullet 1> / <bullet 2> / <bullet 3>'.
```

After generation, `mv` the image from the thumbnail output dir into the pin folder as `pin.png`.

### Step 5: Copy File Template

Save to `~/content/pinterest/NNN-slug/copy.md`:

```markdown
# Pinterest Pin - [Day Number or Topic]
**Image:** ./pin.png

**Title:** [keyword-first title]

**Description:** [SEO-optimized description, 200-300 chars, with Save this CTA]

**Board:** [board name]

**Alt Text:** [visual description with keywords, 500 chars max]

**Destination URL:** [YouTube video or channel URL]
```

### Step 6: Scheduling via Blotato

**ALWAYS ask for explicit confirmation before scheduling anything to Blotato.** Never auto-schedule. Show the user the full list of pins (titles, dates, times, board) and wait for a clear "yes" / "go" / "schedule it" before running any `blotato_create_post` calls. Even when the user said "schedule them" earlier in the session, re-confirm the specific batch + dates before firing. Uploading presigned URLs is also part of the scheduling flow and should not happen without confirmation.

**Tyler's Blotato setup (saved in memory `reference_pinterest_board_ids.md`):**
- Pinterest account ID: `5421`
- Username: `tylerreedytlearning`
- Board `AI Content Creation` → `1121537182144777258`

**Flow (three API calls per pin):**

1. Call `mcp__blotato__blotato_create_presigned_upload_url` with `filename: "NNN-slug.png"` — returns `presignedUrl` + `publicUrl`
2. PUT the local pin.png to the presignedUrl via curl:
   ```bash
   curl -sS -X PUT "<presignedUrl>" --data-binary "@~/content/pinterest/NNN-slug/pin.png" -H "Content-Type: image/png"
   ```
3. Call `mcp__blotato__blotato_create_post` with:
   ```
   accountId: "5421"
   platform: "pinterest"
   boardId: "1121537182144777258"  // AI Content Creation
   title: <pin title>
   text: <pin description>
   altText: <alt text>
   link: <destination URL>
   mediaUrls: [<publicUrl from step 1>]
   scheduledTime: "YYYY-MM-DDT20:00:00-04:00"  // 8 PM ET during EDT
   ```

**Schedule cadence:** 1 pin/day at 8 PM ET. Record the `postSubmissionId` in `status.md` so the pin can be checked or cancelled later via `blotato_get_post_status` / `blotato_delete_schedule`.

**DST note:** From March through early November, use `-04:00` (EDT). From November to March use `-05:00` (EST).

### Step 7: Update status.md

Append each new pin to `~/content/pinterest/status.md`:

| Slug | Board | Created | Scheduled | Posted | Blotato Submission ID |
|------|-------|---------|-----------|--------|----------------------|
| 015-5-tools-replaced-canva | AI Content Creation | 2026-04-20 | 2026-05-01 8pm ET | — | 47092c52-... |

### Step 8: Present to User

Show the user:
- The pin title, description, board, destination URL
- The generated pin.png preview (open it in Preview with `open` command)
- The scheduled date/time

Ask: "Want to tweak anything before I commit the schedule?"

## Pin Type Variants

### Static Pins (default — what most of this skill covers)
Follow the full design system above.

### Video Pins (from shorts/reels)
- Reuse the 9:16 video file directly
- Write a Pinterest-optimized title (keyword-first, different from the YouTube title)
- Longer, more keyword-rich description than the YouTube caption
- Same Blotato flow but `mediaUrls` points to the uploaded video

### Carousel Pins (from LinkedIn/IG carousel content)
- Adapt each slide to 2:3 ratio (1000x1500)
- 2-5 cards max
- First card must hook on its own — it is the only one visible in the feed

## Keyword Research

Before writing pin content, check Pinterest search trends:
- WebSearch "Pinterest trending [topic] 2026"
- Think about what someone would TYPE into Pinterest search
- Long-tail > short-tail ("claude code beginner tutorial step by step" > "claude code")
- Common patterns: "how to [X]", "[X] tutorial", "[X] tips", "best [X] for [Y]"

## Posting Rules

- New account warmup: 1-3 pins/day manually for 2-3 weeks
- After warmup: 5-15 pins/day
- Best times: 8-11 PM, best days Sun/Mon/Tue
- Fresh pins only - repins have minimal impact in 2026
- Each YouTube video should produce 1-2 Pinterest pins (1 static + optionally 1 video)
- Each short = 1 video pin
- Generate 1 image variant per pin (`--count 1`), not multiple

## Tyler's Content Sources

- YouTube video packages: `~/youtube/<slug>/`
- Shorts packages: `~/youtube/shorts/NNN - Title/`
- LinkedIn text posts: `~/content/linkedin/text-posts/`
- Carousel slides: `~/content/carousel/<slug>/`
- Content tracker: `~/content/tracker.md`

## Rules

- **ALWAYS** use keyword-first titles — #1 SEO factor
- **NEVER** use hashtags in descriptions — ~1% ranking weight
- **Every pin** needs alt text — major 2026 ranking factor
- **Static pins MUST** be 2:3 ratio (1000x1500) — algorithm penalizes others
- Video pins use 9:16 (1080x1920) — same as shorts/reels
- Write descriptions for Pinterest **search**, not social engagement
- **Never use em dashes** — plain hyphens or commas only
- **Folder naming**: zero-padded `NNN-slug`, never `dayN-slug`
- **Design matches Day 1**: cream bg, Claude terracotta orange icons, 5-card format, @tylerreedai handle
- **AI Content Creation board** is the default for new/test pins (top performer)
- Record Blotato `postSubmissionId` in status.md for every scheduled pin
- **ALWAYS ask before scheduling** — confirm pins, dates, times, and board with the user before any `blotato_create_post` call. Never auto-schedule.
