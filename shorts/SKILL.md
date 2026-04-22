---
name: shorts
description: Generate a weekly short-form content package from yt-search research. Takes top-performing competitor videos, extracts the 5 best angles, and creates ready-to-film short scripts (YT Shorts, TikTok, Reels) plus 2 Instagram carousel outlines. Part of the weekly content pipeline — runs after /yt-search. Triggers on: create shorts, shorts for the week, short form content, weekly shorts, shorts package, make shorts from research, short-form scripts.
argument-hint: [~/yt-research/<report>.md or ~/yt-research/<report>.json] [--topic <topic>]
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion
user-invocable: true
---

Generate a weekly short-form content package from yt-search research at $ARGUMENTS.

## Workflow Context

This skill is part of the **weekly content pipeline**:

```
/yt-search → /transcribe → /yt → /seo  ← long-form track
                ↓
            /shorts  ← short-form track (this skill)
                ↓
            /content → /post
```

Run `/shorts` after `/yt-search` to turn competitor research into 5 original short-form scripts + 2 Instagram carousel outlines for the week.

## Data Location

All output goes to `~/youtube/shorts/YYYY-MM-DD/` (today's date).

---

## Flow

### Step 1: Find the Research

Parse $ARGUMENTS:

- **Report path** (`~/yt-research/<file>.md` or `.json`): Use it directly
- **--topic flag**: Glob `~/yt-research/` for reports matching the topic
- **No argument**: Glob `~/yt-research/` and use the most recent report(s)

Read all matching research files. If JSON files exist alongside the markdown reports, read both — the JSON has raw metadata useful for deeper analysis.

If no research reports exist at all, tell the user:
> "No yt-search reports found. Run `/yt-search <topic>` first to generate research."

Also check `~/scripts/` for any transcripts of top-performing videos from the research (filenames like `transcript_<video_id>.txt`). Read any that exist — they give deeper insight into what those videos actually say.

---

### Step 2: Analyze the Research

From the yt-search reports, extract:

- The **top 10 performing videos** (by view count)
- For each: title, view count, channel, duration, and any observable content patterns
- **What made these videos perform**: title patterns, content formats, specific angles or hooks
- **Topics and angles** that consistently appear in high-performing content
- **Gaps**: angles that are underrepresented despite audience interest

If transcripts are available for any of these videos, read them and note:
- The strongest hooks (first 30 seconds)
- The most quotable or surprising moments
- The structure / pacing they use

---

### Step 3: Identify 5 Short-Form Ideas

Based on the research, identify **5 distinct short-form ideas**. Each should:

- Be grounded in a **proven angle** from the top-performing competitor content
- Be **original** — Tyler's take on the topic, not a clip of someone else's video
- Be **self-contained** — makes sense in 60-90 seconds with no prior context
- Cover **different angles** — don't make 5 versions of the same idea

For each idea, note:
- **Title/concept** — One-line description of the short
- **Why it will work** — Which competitor video or pattern inspired this, and why it performs
- **Format** — Talking head, screen recording, or mixed
- **Core insight** — The one thing viewers will take away

**Present these 5 ideas to the user** before generating full scripts. Ask:
> "Here are 5 short-form ideas based on the research. Want to swap any out or adjust before I write the scripts?"

Wait for confirmation or adjustments before proceeding.

---

### Step 4: Generate 5 Short-Form Scripts

For each approved idea, write a full short-form package:

#### Script Block

```
## Short #[N]: [Title]

**Format:** [Talking head / Screen recording / Mixed]
**Target length:** 60-90 seconds

---

### Hook (first 3 seconds)
[The exact opening line. Must stop the scroll immediately. No "hey guys", no intro.]

### Script
[Full word-for-word script, written for spoken delivery. Short sentences. Punchy.
80-150 words. Natural pauses marked with — or ...]

### On-Screen Text
- [Key phrase 1 — appears at hook]
- [Key phrase 2 — mid-video emphasis]
- [Key phrase 3 — closing punchline or CTA]

### CueCard (copy/paste into teleprompter)
[Just the words Tyler says on camera. No metadata, no [SHOW:] tags, no captions.
Split into sections with ## headers so he can jump between them with arrow keys.
Include a ## Outro section for the closing line/CTA.]

### Filming Checklist
- [ ] [Setup note: e.g., "Screen recording ready", "Teleprompter loaded", "Good lighting"]
- [ ] [Any props or tabs/apps to have open]
- [ ] [Energy note: e.g., "High energy - lean forward at hook"]
- [ ] [Estimated take time: ~X minutes]
```

Rules for scripts:
- Hook must land in the **first 3 seconds** — no exceptions
- Scripts: **80-150 words** (60-90 seconds when spoken)
- Written for **spoken delivery** — short sentences, natural rhythm, not essay prose
- Each short must be **self-contained** — no "as I mentioned", no series callbacks
- End with a **micro-CTA or open loop**, not "like and subscribe"
- Vary formats across the 5 shorts — mix talking head, screen recording, mixed

---

### Step 5: Generate Platform Captions

After all 5 scripts, generate a `captions.md` file with platform-ready captions for each short:

For each short (#1 through #5):

```
## Short #[N] Captions

### YouTube Shorts
[Hook line]
[2-3 sentence body — expand on the insight]
[CTA — "More AI tips below ↓"]
#claudecode #claudeai #ai #claudecodetips #aiautomation

### TikTok
[Punchy hook — often different from YT, more casual]
[1-2 sentence body]
[CTA]
#claudecode #claudeai #ai #claudecodetips #aiautomation

### Instagram Reels
[Same as TikTok caption or slight variation]
#claudecode #claudeai #ai #claudecodetips #aiautomation
```

---

### Step 6: Generate 2 Instagram Carousel Outlines

Instagram gets **2 carousel posts** instead of reels — these are static slide posts, no filming required.

Pull the 2 best insights from the research that work well as a **visual walkthrough** (step-by-step, list, before/after, or comparison format).

For each carousel:

```
## Instagram Carousel #[N]: [Title]

**Concept:** [One-line description]
**Why this format:** [Why this works as slides vs. a video]

---

**Slide 1 (Intro — dark background)**
Headline: [Big bold hook, max 8 words]
Subtext: [Optional 1-line context]

**Slide 2**
Headline: [Point 1 — short and punchy]
Body: [1-2 supporting sentences]

**Slide 3**
[Continue pattern...]

**Slide 4**
[...]

**Slide 5**
[...]

**Slide 6 (Closing)**
Headline: [Takeaway or CTA]
Body: [Optional — "Save this", "Follow for more"]

---

**Caption:**
[Hook line]
[2-3 sentences expanding on the topic]
Swipe to see all [X] tips →
#claudecode #claudeai #ai #claudecodetips #aiautomation
```

Note in the output: use `/content` to generate the actual Blotato carousel visuals from these outlines.

---

### Step 7: Save All Outputs

Create `~/youtube/shorts/YYYY-MM-DD/` and save:

| File | Contents |
|------|----------|
| `shorts.md` | All 5 short-form scripts with hooks, on-screen text, filming checklists |
| `captions.md` | Platform captions for each short (YT Shorts, TikTok, Instagram Reels) |
| `instagram-carousels.md` | 2 carousel outlines for `/content` to render |
| `filming-plan.md` | Quick-reference filming order for the day |

#### `filming-plan.md` contents:

A practical "film these in this order" guide for the day:

```markdown
# Filming Plan — [Date]

## Setup Once
- [ ] Clean desk / background
- [ ] Good lighting (ring light on, window light if available)
- [ ] Teleprompter app loaded with scripts
- [ ] Screen recording software ready (if any shorts use screen recordings)

## Short #1: [Title] (~X min)
- Format: [talking head / screen recording / mixed]
- Key setup: [anything specific]
- Estimated takes: 2-3

## Short #2: [Title] (~X min)
...

## Estimated Total Filming Time: [X] minutes
## Tip: Film all talking-head shorts together, then screen recordings — one context switch is easier than five.
```

---

### Step 8: Present Summary

Show the user:
1. All 5 short titles with their hooks (preview)
2. The 2 carousel concepts
3. File paths for everything saved
4. The estimated total filming time from `filming-plan.md`

Ask: **"Want to adjust any scripts, swap an idea, or generate the carousel visuals now with `/content`?"**

---

## Rules

- Ideas come from **research, not guessing** — every short should be traceable to a top-performing competitor video or pattern
- Scripts must be **original** — Tyler's perspective on the topic, not rephrasing someone else's video
- **Hook first, always** — no intros, no "hey guys", no warm-up
- Scripts: **80-150 words max** — if it can't be said in 90 seconds, it's not a short
- **Vary the 5 formats** — at least 2 talking head, 1 screen recording, 1 mixed
- Instagram gets **2 carousels, not reels** — static slides are the format for Instagram
- Save to `~/youtube/shorts/YYYY-MM-DD/` — always date-stamped
- If a shorts folder already exists for today, ask before overwriting
- Never auto-post — always show content and get confirmation first
- The carousel outlines are for `/content` to render — don't try to render them here
