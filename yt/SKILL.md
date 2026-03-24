---
name: yt
description: Plan a YouTube video from a reference transcript and your own ideas. Analyzes source video structure, researches the topic online, asks for your angle, then generates titles, hooks, description, full script, and a filming guide. Triggers on: youtube video, video script, plan a video, video from transcript, yt plan.
argument-hint: [transcript_path]
allowed-tools: Read, Write, Glob, Grep, WebSearch, WebFetch, Bash(python3:*), Bash(yt-dlp:*)
user-invocable: true
---

Plan a YouTube video inspired by a reference transcript at $ARGUMENTS.

## Workflow Context

**Step 3 of the weekly content pipeline** (after `/yt-search` → `/transcribe`).

Run twice per week — once per long-form video topic. Each run produces a full package at `~/youtube/<slug>/`. After this, run `/seo` to optimize titles/descriptions, then `/content` to generate the LinkedIn + YT Community text posts for that video.

## Data Location

All video packages are saved to `~/youtube/<video-slug>/` where the slug is derived from the working title.

## Flow

### Step 0: Check Video Ideas Tracker

Before doing anything else, read `~/youtube/video-ideas.md` and scan for ideas related to the topic of this video.

1. **Duplicate check** — If an Active or Backlog idea closely matches this topic, tell the user:
   > "Found a matching idea in your tracker: **[title]** ([status], [priority]). Want me to use this as the starting point?"
   - If yes, pull in the idea's angle, target audience, and notes as additional context for the planning process.
   - If the idea's status is "Planned" or "Backlog", update it to "In Progress" and add a research link: `**Research:** [Video Package](./slug/)`

2. **Related ideas** — If other ideas share the same tool/theme (even if not an exact match), briefly list them:
   > "Related ideas in your tracker: [titles]. Want to reference any of these angles?"
   - The user might want to weave in a related angle or set up a sequel.

3. **No match** — If nothing matches, continue normally. Don't ask about it.

After this check, proceed to Step 1.

### Step 1: Read & Analyze the Source Transcript

Read the transcript file provided. Produce a thorough analysis and present it to the user:

- **Structure breakdown** — Segments with timestamps, duration, and purpose (hook, demo, teaching, CTA)
- **What works well** — Effective hooks, pacing, rhetorical techniques, key phrases worth noting
- **Weaknesses / gaps** — What's missing, what could be improved, what questions go unanswered (these are opportunities for differentiation)
- **Target audience** — Who the source video is for and what technical level it assumes

**Download the reference thumbnail:** If the transcript came from a YouTube video (check for a video ID in the filename like `transcript_<video_id>.txt`), download the thumbnail for reference:

```
yt-dlp --write-thumbnail --skip-download -o "~/youtube/<slug>/reference-thumbnails/<source-name>" "https://youtu.be/<video_id>"
```

Save it to `~/youtube/<slug>/reference-thumbnails/` and show it to the user during the analysis.

**Analyze the reference thumbnail:** After downloading, read/view the thumbnail image and create `~/youtube/<slug>/thumbnail.md` with a detailed breakdown:

- **Layout** — Where are elements positioned? (left/right thirds, centered, split-screen, etc.)
- **Color scheme** — Background colors, accent colors, overall palette (dark/light, warm/cool)
- **Typography** — What text is on the thumbnail? Font style (bold, serif, sans), size, color, placement
- **Visual elements** — Icons, logos, screenshots, illustrations, arrows, badges, effects (glow, shadow, gradient)
- **Face/person** — Is there a person? Expression, position, size relative to frame
- **Composition style** — Minimal/clean vs busy, how much whitespace, focal point placement
- **What makes it clickable** — Why would someone click this? Curiosity, contrast, clarity, emotion?
- **Recommended approach for our thumbnail** — Based on this analysis, suggest 2-3 specific thumbnail concepts for our video, each with a detailed prompt description

This file becomes the brief for Step 5 (thumbnail generation). When generating thumbnails later, read `thumbnail.md` and use the analysis to craft prompts that match the proven style while differentiating our version.

### Step 2: Research the Topic Online

After analyzing the transcript, use **WebSearch** to research the topic thoroughly. This is NOT optional — always do real web research. Search for:

- **The tool/topic itself** — Official website, features, pricing, recent updates, documentation
- **Competitor landscape** — How this tool compares to alternatives. What are the key differentiators?
- **Existing YouTube content** — What videos already exist on this topic? Who are the main creators? What angles have been covered?
- **Content gaps** — What hasn't been covered well? What questions are unanswered? These are opportunities.
- **Community sentiment** — What are people saying on Reddit, forums, social media? What do they love/hate?
- **Recent news** — Any recent updates, controversies, or developments?

Run multiple searches (at least 4-6 different queries) to get comprehensive coverage. Include all findings and source URLs in the `analysis.md` file.

### Step 3: Interactive Q&A

After presenting the analysis AND research, ask the user these questions **one at a time, conversationally**:

1. **"What's your angle on this topic? What would you do differently or better?"**
2. **"What examples or demos will you show on screen?"**
3. **"Who's your target audience?"**
4. **"Anything specific you want to include or avoid?"**

If the user gives short answers, that's fine — don't over-ask. If they give detailed answers, absorb everything.

### Step 4: Generate the Video Package

After collecting answers, create the `~/youtube/<video-slug>/` directory and generate these files:

#### `titles.md`
- 5 title options, each under 70 characters
- For each title: one sentence explaining why it works (curiosity, specificity, contrast, etc.)
- Mark the recommended title

#### `hooks.md`
- 3 hook options for the first 30 seconds
- Each hook is a **word-for-word script** the user can read/memorize
- Each hook uses a different technique (curiosity gap, bold claim, story open, pattern interrupt)
- Note which technique each hook uses

#### `description.md`
- YouTube description with:
  - 2-3 sentence summary (front-loaded for search)
  - "In this video:" bullet list of what's covered
  - Chapters section with `00:00 - Title` format (use placeholder timestamps, mark with [UPDATE])
  - Relevant tags/keywords at the bottom

#### `script.md`
- Full video script organized by sections
- Each section has:
  - **Timestamp estimate** (e.g., `## [0:00 - 0:30] Hook`)
  - **What to say** — Written in natural speaking rhythm, not essay prose. Short sentences. Conversational.
  - **[SHOW: ...]** markers — What should be on screen (screen recording, b-roll, slide, etc.)
  - **[NOTE: ...]** markers — Production notes (pause here, speed up, cut to demo, etc.)
- Include transitions between sections
- End with a CTA

#### `analysis.md`
- The full source video analysis from Step 1
- **The full web research from Step 2** — include all findings organized by category (tool overview, features, competitive landscape, content gaps, community sentiment, etc.)
- **All source URLs** as clickable markdown links at the bottom under a `## Sources` section
- This file is the reference hub — everything the user needs to know about the topic lives here

#### `filming-guide.md`
- A practical, step-by-step playbook for what to ACTUALLY DO on screen while recording
- Organized by filming steps (Step 1, Step 2, etc.) in chronological order
- Each step includes:
  - **What you do** — Exact UI clicks, actions, and navigation steps
  - **Exact prompts/commands to type** — Copy-paste ready, in code blocks
  - **What you say** — Suggested narration for each moment (in blockquotes)
  - **What happens next** — What to expect on screen so the user isn't surprised
  - **How to fill dead air** — What to talk about while waiting for AI to process
- **Pre-recording setup section** — Settings to configure, files to prepare, environment cleanup
- **Timing cheat sheet** — Table showing target duration for each section and running total
- **On-camera tips** — How to handle errors/bugs on camera, energy/pacing advice, visual moments to capture
- **Any markdown files or templates** the user should have ready — include the full content of these files so they can be copy-pasted
- If the video involves a tool with UI (like an IDE, app builder, etc.), include specific button names, menu paths, and keyboard shortcuts

### Step 5: Generate Thumbnails

After generating all written files, generate thumbnail options using the `/thumbnail` skill's script.

1. **Read `thumbnail.md` first.** Use the reference thumbnail analysis and recommended approaches from Step 1 to craft your prompts. The prompts should be informed by what's proven to work in the reference, not generic guesses. If `thumbnail.md` recommends specific layouts, colors, or compositions — use those.

2. Based on the thumbnail analysis, video title, script, and overall concept, craft 2-3 different thumbnail prompts. Each should be a distinct visual concept but grounded in the reference analysis:
   - One that closely follows the reference thumbnail's proven style/layout
   - One that takes the reference style but adds the user's face (use `--reference-images ~/youtube/tyler-reference-images/tylerai.png`)
   - One that differentiates — a fresh take that still incorporates elements that work from the analysis

2. For each prompt, run the thumbnail generator:
   ```
   python3 ~/.claude/skills/thumbnail/generate_thumbnail.py "<prompt>" --count 1 --resolution 2K --slug <video-slug> --aspect-ratio 16:9
   ```

3. Thumbnails are saved to `~/youtube/thumbnails/<date>-<video-slug>/`

4. Show the user the generated thumbnails and ask which direction they prefer. Offer to:
   - Generate more variants of a style they like
   - Remix a specific thumbnail with changes
   - Try a completely different concept

**Thumbnail prompt tips:**
- Do NOT include text in the prompt — text overlay is added in an editor afterward
- Keep compositions simple with one focal point
- Leave visual space for text overlay (usually left or right third)
- High contrast reads well at small thumbnail sizes
- Mention estimated cost before generating ($0.09/image at 2K)

### Step 6: Present & Iterate

After generating all files and thumbnails, show the user:
- The recommended title
- The recommended hook (full text)
- The script outline (section headers + time estimates)
- The generated thumbnail options

Ask: "Want to revise anything — titles, hooks, script sections, filming guide, thumbnails, or the overall structure?"

If they want changes, update the relevant files or regenerate thumbnails. If they're happy, confirm the output location and wrap up.

## Rules

- Always save to `~/youtube/<slug>/` — never save video files elsewhere
- Slug should be lowercase, hyphenated, derived from the topic (e.g., `claude-code-skills`)
- Be honest in the analysis — calling out weaknesses is useful, not rude
- Scripts should sound like a person talking, not an article being read aloud
- Keep sentences short in scripts. People breathe between sentences.
- Use `[SHOW: ...]` liberally — the user needs to know what to record
- Don't pad the script with filler — every line should earn its place
- If the user already provided their angle/ideas in the initial message, skip the Q&A questions they already answered
- ALWAYS do web research — never skip Step 2. The research makes everything better.
- Include ALL source URLs in analysis.md — the user needs to be able to trace where information came from
- The filming guide should be practical enough that someone could follow it without reading the script first — it's the "do this, click that" version
