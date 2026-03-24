---
name: repurpose
description: Repurpose a VIDEO transcript or script into short-form VIDEO scripts for YouTube Shorts, TikTok, and Reels — plus matching captions and a community post. Input must be a video transcript, script path, or YouTube URL. Use this for video-first content only. For text posts, LinkedIn posts, carousels, or static visuals, use /content instead. Triggers on: repurpose this video, repurpose transcript, create shorts from, make social posts from, repurpose content, turn this into shorts.
argument-hint: [transcript_path or script_path or youtube_url] [--url <youtube_video_url>]
allowed-tools: Read, Write, Glob, Grep, Skill(transcribe), AskUserQuestion, Skill(post)
user-invocable: true
---

Repurpose the video content at $ARGUMENTS into platform-ready social media content.

## Data Location

Repurposed content is saved to `~/youtube/<slug>/repurposed/` where the slug is derived from the source video or transcript.

## Flow

### Step 1: Get the Source Content

Determine the input type from $ARGUMENTS:

- **Transcript path** (`~/scripts/transcript_*.txt`): Read it directly
- **Script path** (`~/youtube/<slug>/script.md`): Read it directly
- **YouTube URL**: Call the `/transcribe` skill first to get a transcript, then read the resulting file
- **No argument**: Ask the user for a transcript path, script path, or YouTube URL

If the source is from a video package (`~/youtube/<slug>/`), also read `titles.md` and `description.md` if they exist — they provide context for better repurposing.

### Step 2: Identify the Top 5 Most Compelling Moments

Analyze the full transcript/script and extract the **5 best moments** for repurposing. Look for:

- **Quotable insights** — Sharp, memorable statements that stand alone
- **Surprising facts or stats** — "Did you know..." moments
- **Practical tips** — Specific, actionable advice viewers can use immediately
- **Strong opinions** — Hot takes or contrarian views that spark engagement
- **Before/after or transformation moments** — Demonstrations of impact

For each moment, note:
- The approximate timestamp or section
- Why it's compelling (what makes it shareable)
- A one-line summary

Present these 5 moments to the user before generating content.

### Step 3: Ask Platform Preferences

Ask the user: **"Which platforms do you want content for?"**

Options (default: all):
- YouTube Shorts
- YouTube Community post
- LinkedIn
- Twitter/X
- Instagram/TikTok captions

Also ask: **"Do you have the YouTube video URL?"** — needed for the community post link. If they passed `--url` in arguments, use that.

### Step 4: Generate Content Files

Create the `~/youtube/<slug>/repurposed/` directory and generate the requested files:

#### `repurposed-shorts.md` — 3-5 Short-Form Video Scripts

For each short:
- **Title** — Working title for the short
- **Source timestamp** — Where in the original video this comes from (so the user can find the footage)
- **Hook (first 3 seconds)** — The opening line that stops the scroll. Must create immediate curiosity or value.
- **Script (30-60 seconds)** — The full short script, written for spoken delivery
- **Text overlay suggestions** — 2-3 key phrases to display on screen
- **Suggested format** — Talking head, screen recording clip, or mixed

Rules for shorts:
- Each short MUST be self-contained — it needs to make sense without the full video
- Hook must land in the first 3 seconds — no "hey guys" or throat-clearing
- Keep scripts to 80-150 words (30-60 seconds when spoken)
- End with a micro-CTA or open loop (not "subscribe to my channel")
- Vary the formats — don't make 5 identical talking-head shorts

#### `community-post.md` — YouTube Community Post

Generate 2-3 community post options. Each should:
- **Opening line** — Short, punchy hook that makes subscribers want to click
- **Body** — 2-4 sentences about what the video covers and why it matters. Keep it casual and conversational.
- **Video link** — Include the YouTube URL (from `--url` flag or user input)
- **Question/poll option** — Suggest a question to ask the audience (community posts with questions get more engagement)

Rules for community posts:
- Keep it SHORT — community posts that are too long get scrolled past
- Lead with what the viewer gets, not "I just uploaded..."
- The tone should feel like you're texting a friend about something cool you made
- Include the video link naturally, not as a cold "watch here" CTA
- If no URL is available yet, leave a `[VIDEO_URL]` placeholder and note it needs to be filled in

#### `linkedin.md` — 2-3 LinkedIn Post Drafts

For each post:
- **Opening hook** — First line that appears before "see more" (must earn the click)
- **Body** — 500-1500 characters, educational/value-driven tone
- **Closing** — Question or invitation for discussion
- **Source moment** — Which part of the video this draws from

Rules for LinkedIn:
- Do NOT make these promotional — they should teach something from the video
- Use line breaks for readability (LinkedIn rewards scannable posts)
- Lead with an insight, not "I just published a video about..."
- No hashtags on LinkedIn (they reduce engagement)
- Write in first person, conversational but professional

#### `tweets.md` — 5-7 Tweet Options

For each tweet:
- **Tweet text** — Under 280 characters
- **Source moment** — Which part of the video this comes from
- **Thread option** (if applicable) — A 2-3 tweet thread version for deeper topics

Rules for tweets:
- Every tweet must be a standalone insight — not "check out my new video"
- Use punchy, direct language
- At least 2 tweets should be "hot take" style (strong opinion, contrarian view)
- At least 2 tweets should be practical tips (actionable, specific)
- No hashtags in tweets (they reduce engagement on X)

#### `captions.md` — 2-3 Instagram/TikTok Captions

For each caption:
- **Hook line** — First line that appears in the feed
- **Caption body** — Platform-appropriate text
- **Hashtags** — Exactly 5: #claudecode #claudeai #ai #claudecodetips #aiautomation
- **Source moment** — Which part of the video this draws from

Rules for captions:
- Instagram captions can be longer (up to 2200 chars) — use the space for value
- TikTok captions should be shorter and punchier
- Front-load the value — most people won't read past the first 2 lines
- Always use the exact 5 hashtags above, no more, no less

### Step 5: Present Summary

Show the user a summary of everything generated:

- List each file created with the path
- Preview the best short script (full text)
- Preview the community post (full text)
- Preview the best LinkedIn post (first 3 lines)
- Preview the best tweet
- Total pieces of content created

### Step 6: Iterate and Post

Ask: **"Want to revise anything, or post any of these now?"**

- If they want revisions, update the specific file
- If they want to post something, suggest using the `/content` skill to publish via Blotato

## Rules

- Always save to `~/youtube/<slug>/repurposed/` — derive the slug from the video topic or existing package
- If a video package already exists at `~/youtube/<slug>/`, use that slug
- Shorts scripts must be self-contained — no "as I mentioned in the full video"
- Every short needs a hook in the first 3 seconds — no exceptions
- LinkedIn posts should NOT be promotional — teach, don't sell
- Tweets should be standalone insights — not "new video" announcements
- Include source timestamps/sections so the user can find the exact moment in their footage
- If content already exists in the repurposed folder, ask before overwriting
- Quality over quantity — 3 great shorts beat 5 mediocre ones
