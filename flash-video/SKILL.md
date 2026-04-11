---
name: flash-video
description: Generate 7-second static Reels/TikToks — PIL text burned onto a Kie.ai background image, converted to MP4 via ffmpeg with a 1s fade out. Two layout types: statement (raw text wall) and list (header banner + numbered items + stat). Triggers on: flash video, 7 second video, text reel, static reel, create a reel, tip video, quick video, flash reel.
argument-hint: [topic] or [topic + layout type]
allowed-tools: Read, Write, Bash(python3:*), Bash(ffmpeg:*)
user-invocable: true
---

# Flash Video

Generates 7-second MP4s for TikTok and Instagram Reels. PIL text on a Kie.ai background image → ffmpeg → MP4 with 1s fade to black.

## Design system

- Canvas: 1080x1920 (9:16 vertical)
- Backgrounds: `~/.claude/skills/flash-video/backgrounds/cream.png` or `dark.png`
- Accent: terra cotta `#C4713A` on key words and skill names
- CTA always shows: "Join my Skool community:" → `skool.com/the-ai-agency` → "Link in bio"
- Handle: `@tylerai_dev` bottom-right
- Duration: 7 seconds, 1s fade to black at end

## Layout types

| Type | Use when |
|------|----------|
| `statement` | Raw centered text wall — bold claims, lists of outputs, authentic TikTok feel |
| `list` | Terra cotta header banner + numbered items + stat line — structured, scannable |

## Background styles

| Style | Vibe |
|-------|------|
| `dark` | Dark charcoal with ambient blue-grey glow — high contrast, scroll-stopping |
| `cream` | Warm off-white — matches Instagram carousel brand, clean editorial |

Reuse backgrounds across the week. Regenerate via:
```bash
python3 ~/.claude/skills/flash-video/gen_backgrounds.py cream dark
```

---

## Step 1: Gather inputs

Ask the user for:
- **Topic / content** — what the video says
- **Layout** — `statement` or `list`
- **Background** — `dark` (default) or `cream`

If not provided, default to `dark` + `statement`.

---

## Step 2: Generate content JSON

### Statement layout
```json
{
  "type": "statement",
  "background": "dark",
  "slug": "my-video",
  "lines": [
    "I automated my ENTIRE",
    "content system",
    "with Claude Code.",
    "",
    "YouTube research.",
    "Instagram carousels.",
    "LinkedIn posts.",
    "",
    "All in under 5 minutes.",
    "Every single week."
  ],
  "accent_words": ["ENTIRE", "Claude", "Code", "5"],
  "cta": "skool.com/the-ai-agency",
  "handle": "@tylerai_dev"
}
```

**Statement rules:**
- 8-12 lines total including blank spacer lines (`""`)
- Group related lines together with blank lines between sections
- 1-2 accent words per section
- Last section = punchy payoff line

### List layout
```json
{
  "type": "list",
  "background": "dark",
  "slug": "my-video",
  "header": "5 Claude Code skills",
  "subheader": "I use every single week:",
  "items": [
    "/yt-search — YouTube research",
    "/instagram-writer — 6 slides",
    "/shorts — 5 short scripts",
    "/content — LinkedIn, X, IG posts",
    "/yt — full video + script"
  ],
  "stat": "Saves me 3+ hours. Every single week.",
  "accent_words": ["yt-search", "instagram-writer", "shorts", "content", "yt", "3+"],
  "cta": "skool.com/the-ai-agency",
  "handle": "@tylerai_dev"
}
```

**List rules:**
- Header: short, bold (3-5 words)
- Subheader: one supporting line
- Items: 4-6, keep each under ~30 chars so they don't wrap
- Stat: one punchy payoff line after the list, with 1-2 accent words
- accent_words: include the skill/command names (without `/`) so they highlight in terra cotta

---

## Step 3: Save JSON and render

1. Create a 2-3 word slug.

2. Save JSON to `~/content/flash-video/<slug>-<layout>-<bg>.json`

3. Run renderer:
```bash
python3 ~/.claude/skills/flash-video/flash_video.py \
  ~/content/flash-video/<slug>-<layout>-<bg>.json \
  ~/content/flash-video/
```

Output:
- `<slug>-<layout>-<bg>-frame.png` — the static frame
- `<slug>-<layout>-<bg>.mp4` — 7-second MP4, ready to post

---

## Step 4: Present results

Show the frame PNG so the user can review it, then confirm the MP4 path.

Ask if they want:
- The other background style (cream vs dark)
- Both layout types
- Any text tweaks

---

## Step 5: Update status.md

After rendering (and again after scheduling), update `~/content/flash-video/status.md`:

| Slug | Layout | BG | Created | IG Scheduled | TikTok Scheduled | IG Posted | TikTok Posted |
|------|--------|----|---------|-------------|-----------------|-----------|---------------|
| my-video | statement | dark | 2026-04-09 | Apr 10 12pm | Apr 10 12pm | - | - |

Fill in scheduled times when posting via Blotato. Mark Posted when confirmed live.

---

## Weekly usage pattern

Generate 1-2 backgrounds per week (reuse them). Create 7 flash videos — one per day — varying between statement and list layouts, all pointing to Skool.

Content angles for Claude Code / social media:
- What each skill does in one sentence
- Time saved stats ($928/mo saved, 20+ hrs → 2 hrs)
- Before/after (manual vs automated)
- "Did you know Claude Code can..."
- Weekly output numbers (32 pieces, one content day)
- Direct sell ("What $37/mo in my Skool gets you")
