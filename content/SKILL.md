---
name: content
description: Create platform-ready social media text posts and static visuals from a YouTube video package or any topic. Generates X/Twitter, LinkedIn (text + carousel + image), Instagram, YouTube Community, and Skool posts. Triggers on: create a post, social media post, make a linkedin post, write a tweet, content for, post ideas from this video, create content from, make a post about.
argument-hint: [~/youtube/<slug>/ or topic or url]
allowed-tools: Read, Write, Glob, Grep, Bash(python3:*), WebSearch, AskUserQuestion, Skill(post), mcp__blotato__blotato_list_visual_templates, mcp__blotato__blotato_create_visual, mcp__blotato__blotato_get_visual_status, mcp__blotato__blotato_list_accounts, mcp__blotato__blotato_create_post, mcp__blotato__blotato_get_post_status
user-invocable: true
---

Create platform-ready social media posts and visuals from $ARGUMENTS.

## Workflow Context

**Text content step of the weekly content pipeline** - runs after `/seo` for each long-form video, and after `/shorts` to render the 2 Instagram carousel outlines into actual Blotato visuals.

Run twice per week (once per video) for:
- 2 LinkedIn posts (one per video)
- 2 YT Community posts (one per video)
- 2 Skool video posts (one per video)
- 5 standalone LinkedIn posts (same video topics)
- 5 standalone YT Community posts/polls (same video topics)
- 2 Instagram carousels (from `/shorts` outlines)

## Overview

This skill generates text posts + static visuals for X/Twitter, LinkedIn, Instagram, and YouTube Community - from either a YouTube video package or a standalone topic/URL/idea. It is distinct from `/repurpose` (which makes short-form video scripts). This skill also handles publishing directly via Blotato MCP.

**Output locations:**
- YT video mode -> `~/youtube/<slug>/social/`
- Standalone mode -> `~/social/YYYY-MM-DD-<slug>/`

---

## Step 1: Detect Source Mode

Parse $ARGUMENTS to determine the input type:

- **YouTube video package** - path like `~/youtube/<slug>/` or just a slug name
- **Topic / URL** - a subject, article link, or research query
- **Direct text** - user provides raw copy or idea to adapt

If $ARGUMENTS is empty or ambiguous, ask:
> "What's the source for this content? You can give me:
> 1. A YouTube video package path (e.g. `~/youtube/claude-code-btw/`)
> 2. A topic or URL to research
> 3. Raw text or idea to adapt into posts"

---

## Step 2: Load Content

### YouTube Video Mode
Read these files if they exist (in order of priority):
- `~/youtube/<slug>/script.md` - full script for deep insight extraction
- `~/youtube/<slug>/description.md` - polished summary + key points
- `~/youtube/<slug>/hooks.md` - strong angles and hooks already written
- `~/youtube/<slug>/titles.md` - for post headline ideas

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

### X/Twitter - Thread Format

Write as a thread: one punchy main tweet + 4-5 reply tweets + final reply with video link.

- Main tweet: bold hook, under 230 chars (Tyler's account limit)
- Reply tweets: one point each, under 230 chars
- Final reply: CTA + YouTube URL
- No hashtags (they reduce engagement on X)
- No em dashes - use commas or plain dashes instead
- Write as punchy standalone insights, not "check out my video"

---

### LinkedIn Text Post

**Structure (8-part framework):**

1. **Hook** (6-8 words max) - Stop the scroll. Use one of these proven formulas:
   - "I [did unexpected thing]. Here's what happened:"
   - "[Number] [things] I wish I knew about [topic]"
   - "Stop doing [common thing]. Do this instead:"
   - "Everyone is wrong about [topic]. Here's why:"
   - "I spent [time] doing [thing]. [Surprising result]."

2. **Rehook** - Second line that challenges or expands the hook. Creates curiosity gap.

3. **Problem** - Call out the reader's exact struggle in 1-2 sentences.

4. **Solution** - Deliver the core value/insight.

5. **Signpost** - "Here's how I did it:" or "Here's the framework:" - hint at the details coming.

6. **Body** - 3-5 key points. Short paragraphs of 1-2 sentences each. Use blank lines between every paragraph. Can use emojis sparingly for visual breaks but NOT as bullet points.

7. **Power ending** - One impactful closing sentence. Pattern interrupt or strong opinion.

8. **Question CTA** - End with a simple, easy-to-answer question (72% better engagement than statements). Include YouTube video URL after the question.

**Formatting rules:**
- Plain text only - NO markdown, NO **bold**, NO hashtags
- No em dashes - use commas or plain dashes
- **14+ short paragraphs** with blank lines between each (1-2 sentences per paragraph)
- 1,242-2,500 characters optimal length
- Grade 5-7 reading level - simple, clear, human
- Write "How I" not "How to" - readers want real stories
- First person, conversational but professional
- Lead with insight, not a promotional pitch

**Algorithm optimization:**
- No external links in the main post body (60% less reach). Put the YouTube URL at the very end after the CTA question, or in a comment.
- Design for dwell time - longer reads with engaging structure
- Posts go live between 10-11 AM ET, especially Tue-Thu

---

### LinkedIn Carousel (PDF via Gamma or Kie.ai)

When the user requests a LinkedIn carousel, create slide content following these specs:

**Specs:**
- PDF format, 1080x1080 (1:1) or 1080x1350 (4:5)
- **6 content slides** (no CTA slide - Tyler adds separately with Kie.ai)
- One idea per slide, large readable text
- Minimal text per slide - 2-4 short lines max

**Slide structure:**
- **Slide 1 (Hook):** Bold headline with specific value/numbers. Under 8-10 words. Answer: "Is this for me?" and "What do I get if I swipe?"
- **Slides 2-5 (Value):** One key point per slide. Big bold heading + short explanation.
- **Slide 6 (Summary):** Key takeaway or actionable closing.

**PDF filename matters** - it becomes the bold clickable headline under the carousel on LinkedIn. Make it compelling.

**Carousel-specific caption:**
- Use the 8-part text post framework above for the caption
- End with "Save this for later" or "Send this to someone who needs it" (targets saves + shares, the top algorithm signals)

If using Gamma API:
```bash
python3 ~/.claude/skills/carousel/gamma_carousel.py "<slides_file>" \
  --theme-id "6mnm4rnohwy7bmr" \
  --num-cards 6
```

---

### Instagram Carousel - Visual Carousel Maker

All Instagram carousels go through the visual carousel maker at `http://localhost:3010`. Exports land in `~/content/carousel/<slug>/`.

**Two ways to create carousels:**

**Option A — From this skill (API):**
Generate and auto-save carousels directly by calling the bulk endpoint:
```bash
curl -s -X POST http://localhost:3010/api/bulk-generate \
  -H 'Content-Type: application/json' \
  -d '{
    "items": [
      {"topic": "<topic 1>", "frameworkId": "educational", "platform": "instagram"},
      {"topic": "<topic 2>", "frameworkId": "hormozi", "platform": "instagram"}
    ]
  }'
```
Returns `{results: [{id, title, savedAt}]}`. Carousels are saved to the app's library.
After generating, tell the user: "Your carousels are ready in the carousel maker — open it at http://localhost:5175 to add backgrounds and export."

Available frameworkIds (check `/api/frameworks` for the current list):
- `educational` — step-by-step, numbered tips
- `hormozi` — contrarian, proof-driven
- `quick-wins` — fast actionable list
- `storytelling` — narrative arc
- `instagram-writer` — Cover/Pain/Solution/How/Results/CTA

**Option B — In-app batch UI:**
Tell the user to click the ⚡ Batch button in the carousel maker header. They paste topics (one per line), pick a framework, and generate all at once.

**Carousel content rules (Instagram-specific):**
- 4:5 aspect ratio (1080x1350) - fills the screen
- First slide: under 8-10 words, answer "Is this for me?" and "What will I get if I swipe?"
- Design for saves and shares - these are the #1 and #2 algorithm signals
- Export as PDF for posting via Blotato (use PDF, not individual PNGs)

**Posting via Blotato:**
After the user exports the PDF from the carousel maker, post using Blotato:
- Upload the PDF as the carousel asset
- Use only slides 1-6 (the exported PDF is already correct)
- The export saves to `~/content/carousel/<slug>/<slug>.pdf`

**Instagram Caption rules:**
- 150-250 words
- Hook line first (must earn the swipe)
- Swipe CTA early ("Swipe to see all 5")
- **Keyword-rich SEO language** - include searchable terms like "Claude Code tutorial", "AI automation tips", "AI workflow" naturally in the caption. Keywords in captions matter MORE than hashtags for Instagram discovery now.
- End with dual CTA: "Save this for later" + "Send to someone who needs this" (targets the top 2 algorithm signals: saves and shares)
- Exactly 5 hashtags at the very end: #claudecode #claudeai #ai #claudecodetips #aiautomation

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
- Hook line that stands on its own - not "new video is up"
- 2-4 short paragraphs with the key insight or takeaway from the video
- End with a genuine question or CTA ("Drop a comment if you've tried this", "Who's already using this?")
- Include `[VIDEO_URL]` at the end
- 150-300 words

**Rules:**
- Plain text only - no markdown bold, no headers (Skool renders them oddly)
- No em dashes - use plain hyphens or commas
- Short paragraphs - 1-3 sentences max
- Lead with the most interesting thing, not background context
- Emojis sparingly for visual breaks only

---

## Step 6: Review Loop

Show all content clearly, organized by platform. Ask if anything needs revision before saving or posting.

**Quality checklist before showing:**
- [ ] LinkedIn hook is 6-8 words, uses a proven formula
- [ ] LinkedIn post has 14+ short paragraphs, 1,242-2,500 chars
- [ ] LinkedIn has no markdown, no bold, no hashtags, no em dashes
- [ ] LinkedIn ends with a simple question CTA
- [ ] Instagram caption includes keyword-rich SEO language
- [ ] Instagram caption ends with save + share dual CTA
- [ ] Instagram has exactly 5 hashtags at the end
- [ ] X tweets are under 230 chars each, no hashtags
- [ ] No em dashes anywhere in any content
- [ ] All posts lead with insight, not promotion

---

## Step 7: Save Outputs

**YT video mode** -> `~/youtube/<slug>/social/`
**Standalone mode** -> `~/content/YYYY-MM-DD-<topic-slug>/`

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
# Post Status - [Video Title]

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

Handle posting directly using Blotato MCP tools - no need to hand off to `/post` skill:
1. Call `blotato_list_accounts` to get account IDs
2. Call `blotato_create_post` for each platform
3. For X threads, use `additionalPosts` array for reply tweets
4. Poll `blotato_get_post_status` if needed
5. Update `status.md` with live URLs after posting

**Account IDs (Tyler's accounts):**
- Instagram: `12074` (@tylerreedai)
- LinkedIn: `4987` (Tyler Reed, personal)
- Twitter/X: `5910` (@TylerReedAI)

**Optimal posting times:**
- LinkedIn: 10-11 AM ET, best on Tue-Thu. Wednesday 11 AM-4 PM is peak.
- Instagram: 6-9 AM, 11 AM-1 PM, or 7-9 PM EST. Best on Tue/Wed/Fri.
- X: Mornings or lunch, weekdays

---

## Rules

- **Never auto-post** - always show content and get confirmation before publishing
- **Never skip the review step** - show all content before saving
- **Run the quality checklist** in Step 6 before presenting content
- LinkedIn: plain text only, no markdown, no hashtags, no em dashes, 8-part framework, 14+ paragraphs
- X/Twitter: 230 char limit per tweet (Tyler's account), thread format with video link in last reply
- Instagram Blotato carousel: use only slides 1-6, skip slide 7 (broken CTA) - replace with custom Kie.ai image
- Instagram captions: keyword-rich SEO language, dual save+share CTA, exactly 5 hashtags
- Always fetch real YouTube URL from channel before writing posts
- Always create/update `status.md` to track what was posted and where
- If a `social/` folder already exists, ask before overwriting existing files
- For standalone mode, always do WebSearch research before writing (2-3 queries minimum)
- **Engagement reminder:** After posting, remind Tyler to reply to comments within 60 minutes (30% engagement boost on LinkedIn, critical for Instagram's 24-48hr algorithm window)
