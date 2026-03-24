---
name: content
description: Create platform-ready social media text posts and static visuals from a YouTube video package or any topic. Generates X/Twitter, LinkedIn (text + carousel + image), Instagram, YouTube Community, and Skool posts. Triggers on: create a post, social media post, make a linkedin post, write a tweet, content for, post ideas from this video, create content from, make a post about.
argument-hint: [~/youtube/<slug>/ or topic or url]
allowed-tools: Read, Write, Glob, Grep, Bash(python3:*), WebSearch, AskUserQuestion, Skill(post), mcp__blotato__blotato_list_visual_templates, mcp__blotato__blotato_create_visual, mcp__blotato__blotato_get_visual_status, mcp__blotato__blotato_list_accounts, mcp__blotato__blotato_create_post, mcp__blotato__blotato_get_post_status
user-invocable: true
---

Create platform-ready social media posts and visuals from $ARGUMENTS.

## Workflow Context

**Text content step of the weekly content pipeline** — runs after `/seo` for each long-form video, and after `/shorts` to render the 2 Instagram carousel outlines into actual Blotato visuals.

Run twice per week (once per video) for:
- 2 LinkedIn posts (one per video)
- 2 YT Community posts (one per video)
- 2 Skool video posts (one per video)
- 5 standalone LinkedIn posts (same video topics)
- 5 standalone YT Community posts/polls (same video topics)
- 2 Instagram carousels (from `/shorts` outlines)

## Overview

This skill generates text posts + static visuals for X/Twitter, LinkedIn, Instagram, and YouTube Community — from either a YouTube video package or a standalone topic/URL/idea. It is distinct from `/repurpose` (which makes short-form video scripts). This skill also handles publishing directly via Blotato MCP.

**Output locations:**
- YT video mode → `~/youtube/<slug>/social/`
- Standalone mode → `~/social/YYYY-MM-DD-<slug>/`

---

## Step 1: Detect Source Mode

Parse $ARGUMENTS to determine the input type:

- **YouTube video package** — path like `~/youtube/<slug>/` or just a slug name
- **Topic / URL** — a subject, article link, or research query
- **Direct text** — user provides raw copy or idea to adapt

If $ARGUMENTS is empty or ambiguous, ask:
> "What's the source for this content? You can give me:
> 1. A YouTube video package path (e.g. `~/youtube/claude-code-btw/`)
> 2. A topic or URL to research
> 3. Raw text or idea to adapt into posts"

---

## Step 2: Load Content

### YouTube Video Mode
Read these files if they exist (in order of priority):
- `~/youtube/<slug>/script.md` — full script for deep insight extraction
- `~/youtube/<slug>/description.md` — polished summary + key points
- `~/youtube/<slug>/hooks.md` — strong angles and hooks already written
- `~/youtube/<slug>/titles.md` — for post headline ideas

Also look up the YouTube URL for the video by running:
```bash
yt-dlp "https://www.youtube.com/@tylerreedai/videos" --print "%(webpage_url)s | %(title)s | %(upload_date)s" --no-download --playlist-end 20 2>/dev/null
```
Match the video title to find the URL. Store it for use in posts.

### Research Mode (topic or URL)
Run 2-3 targeted `WebSearch` queries on the topic. Look for:
- Recent developments, stats, or expert quotes
- Contrarian angles or surprising findings
- Practical takeaways your audience cares about

Summarize findings internally before writing.

### Direct Text Mode
Accept the user's raw input as-is. Ask if there are any key angles or tones they want emphasized.

---

## Step 3: Extract Core Ideas

Identify **3-5 key insights, angles, or takeaways** that will anchor all platform content. Look for:

- Surprising or counterintuitive facts
- Practical, actionable tips
- Strong opinions or hot takes
- Before/after or transformation moments
- Quotable one-liners

Present these to the user briefly so they can redirect if needed.

---

## Step 4: Ask Platform + Format Preferences

Ask:
> "Which platforms do you want posts for? (default: all)
> - X/Twitter
> - LinkedIn (text post with video link)
> - Instagram (carousel via Blotato)
> - YouTube Community
> - Skool"

If they say "all" or don't specify, generate all platforms.

---

## Step 5: Generate All Text Content

### X/Twitter — Thread Format

Write as a thread: one punchy main tweet + 4-5 reply tweets + final reply with video link.

- Main tweet: bold hook, under 230 chars (Tyler's account limit)
- Reply tweets: one point each, under 230 chars, use 👉 emoji for points
- Final reply: CTA + YouTube URL
- No hashtags (they reduce engagement on X)
- No em dashes — use commas or plain dashes instead

---

### LinkedIn Text Post (150-300 words)

Structure:
1. **Hook line** — Must earn the click. No "I just posted a video."
2. **Body** — 3-5 points using 👉 emoji (not numbered lists, not markdown bold)
3. **CTA** — Include YouTube video URL at the end

Rules:
- Plain text only — NO markdown, NO **bold**, NO hashtags
- No em dashes — use commas or plain dashes
- Use 👉 emoji instead of numbered points
- Add blank lines between sections for readability
- Write in first person, conversational but professional
- Lead with an insight, not a promotional pitch

---

### Instagram Carousel — Blotato

Use the **Tutorial Carousel with Monocolor Background** template (`e095104b-e6c5-4a81-a89d-b0df3d7c5baf/v1`).

**Known template behavior:**
- The intro slide text is hardcoded white — always use a dark `introBackgroundColor` (charcoal `#1a1a1a` works well)
- The CTA slide (slide 7) is unreliable — it frequently renders blank or broken. **Always skip it.** Use only slides 1-6 when posting.
- `hasAccentLines: true` on content slides has minimal visible effect
- `accentColor` applies to accent elements — red `#e53e3e` works well against white content slides

**Standard settings:**
```
introBackgroundColor: #1a1a1a
contentBackgroundColor: #FFFFFF
accentColor: #e53e3e
ctaBackgroundColor: #FFFFFF
font: font-poppins
aspectRatio: 4:5
authorName: Tyler Reed
companyName: @tylerreedai
```

**Custom slide 7 (CTA):** Instead of the broken Blotato CTA slide, generate a custom Kie.ai image using:
```bash
python3 ~/.claude/skills/thumbnail/generate_thumbnail.py "<prompt>" \
  --model nano-banana-2 \
  --aspect-ratio 4:5 \
  --resolution 2K \
  --count 1 \
  --format jpg \
  --slug slide7-cta \
  --reference-images /Users/tylerreed/youtube/claude-code-skills/thumbnail-ideas-to-use/tylerai.png
```
Prompt should describe: Tyler at laptop, facing camera, clean white background, semi-realistic cartoon/illustration style, bold clean outlines, text at top with yellow highlight boxes saying "Save" "Repost" "Follow @tylerreedai".

Poll `blotato_get_visual_status` every 15 seconds until done. Use only slides 1-6 from Blotato when posting.

**Caption rules:**
- 150-250 words
- Hook line first
- Swipe CTA
- Exactly 5 hashtags at the end: #claudecode #claudeai #ai #claudecodetips #aiautomation

---

### YouTube Community Post (2-4 sentences)

Tone: Casual, like texting a friend about something cool.
- 1-2 sentences about the video
- End with an easy question
- Include `[VIDEO_URL]` placeholder

---

### Skool Post

Tone: Knowledgeable friend sharing something useful in a group chat. Not a newsletter, not a sales pitch.

**For video days (long-form release):**
- Hook line that stands on its own — not "new video is up"
- 2-4 short paragraphs with the key insight or takeaway from the video
- End with a genuine question or CTA ("Drop a comment if you've tried this", "Who's already using this?")
- Include `[VIDEO_URL]` at the end
- 150-300 words

**Rules:**
- Plain text only — no markdown bold, no headers (Skool renders them oddly)
- No em dashes — use plain hyphens or commas
- Short paragraphs — 1-3 sentences max
- Lead with the most interesting thing, not background context
- Emojis sparingly for visual breaks only

---

## Step 6: Review Loop

Show all content clearly, organized by platform. Ask if anything needs revision before saving or posting.

---

## Step 7: Save Outputs

**YT video mode** → `~/youtube/<slug>/social/`
**Standalone mode** → `~/content/YYYY-MM-DD-<topic-slug>/`

Files to write:

| File | Contents |
|---|---|
| `x.md` | Thread (main tweet + replies) |
| `linkedin.md` | Text post with video URL |
| `instagram.md` | Carousel slide URLs + caption |
| `community.md` | 2-3 YT Community post drafts |
| `skool.md` | 2-3 Skool post drafts (video post + variants) |
| `status.md` | Post tracking table (see format below) |

**status.md format:**
```markdown
# Post Status — [Video Title]

## Video
**Title:** ...
**YouTube URL:** ...
**Published:** YYYY-MM-DD

---

## Posted

| Platform | Format | Date | URL | Notes |
|---|---|---|---|---|

## Pending

| Platform | Format | Notes |
|---|---|---|

---

## Assets
- List of files in social/
```

---

## Step 8: Post Inline

After saving, ask: **"Ready to post? Which platforms?"**

Handle posting directly using Blotato MCP tools — no need to hand off to `/post` skill:
1. Call `blotato_list_accounts` to get account IDs
2. Call `blotato_create_post` for each platform
3. For X threads, use `additionalPosts` array for reply tweets
4. Poll `blotato_get_post_status` if needed
5. Update `status.md` with live URLs after posting

**Account IDs (Tyler's accounts):**
- Instagram: `12074` (@tylerreedai)
- LinkedIn: `4987` (Tyler Reed, personal)
- Twitter/X: `5910` (@TylerReedAI)

---

## Rules

- **Never auto-post** — always show content and get confirmation before publishing
- **Never skip the review step** — show all content before saving
- LinkedIn: plain text only, no markdown, no hashtags, no em dashes, 👉 for points
- X/Twitter: 230 char limit per tweet (Tyler's account), thread format with video link in last reply
- Instagram Blotato carousel: use only slides 1-6, skip slide 7 (broken CTA) — replace with custom Kie.ai image
- Always fetch real YouTube URL from channel before writing posts
- Always create/update `status.md` to track what was posted and where
- If a `social/` folder already exists, ask before overwriting existing files
- For standalone mode, always do WebSearch research before writing (2-3 queries minimum)
