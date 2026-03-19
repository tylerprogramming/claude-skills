---
name: custom-gpt
description: Build a complete Custom GPT package (system-prompt.md, KB files, README.md) from course transcripts or raw text. Triggers on: build a custom gpt, create a custom gpt, make a gpt from, custom gpt from text, gpt from transcripts, build a gpt.
argument-hint: [text, file path, or paste transcripts after invoking]
allowed-tools: Read, Write, Edit, Glob, Grep, AskUserQuestion
user-invocable: true
---

Build a complete Custom GPT package from $ARGUMENTS (transcripts, raw text, or file paths).

## Overview

This skill produces everything needed to set up an OpenAI Custom GPT:
- `system-prompt.md` — Instructor personality, behavior rules, topic scope, response format
- `kb-*.md` — 2–4 knowledge base files, logically grouped, concise but complete
- `README.md` — Setup steps, sample test questions, video/topic coverage map

**Output location:** `~/custom-gpts/<project>/<gpt-slug>/`

---

## Step 1: Gather Input

If transcripts or text were passed as `$ARGUMENTS` or pasted into the message, use them directly.

If a file path was provided, read the file(s).

If no content was provided yet, ask:
> "Please paste your transcripts or point me to a file path. You can paste multiple videos — just separate them with a header like `Video Title: [name]`."

---

## Step 2: Ask Clarifying Questions

Before generating anything, ask these questions **all at once** in a single message (don't drag it out):

1. **GPT name** — What should this GPT be called? (e.g., "Sales OS Assistant")
2. **Instructor** — Who teaches this content? Name, role, credentials.
3. **Module context** — Is this part of a larger course/platform? What are the other modules? (Helps define what's out of scope.)
4. **Voice profile** — Is there already a voice profile file for this instructor? If so, where? (If yes, it gets uploaded as a separate Knowledge file — no need to bake it into system-prompt.)
5. **Conciseness level** — How long is the content? Should KB files be detailed or highly condensed? (Default: condensed — extract frameworks and scripts, not transcripts.)

If any of these are obvious from the content or context, skip asking and state your assumption.

---

## Step 3: Analyze the Content

Read through all transcripts/text and extract:

### Instructor Voice
- Tone and energy (casual, formal, fired up, calm)
- Signature phrases and filler words
- Teaching method (example-first, framework-first, story-based)
- What they explicitly say NOT to do (common mistakes they call out)
- Credentials and real numbers they reference

### Topics & Scope
- Full list of topics covered, with the video/section each comes from
- What is explicitly outside scope (mentioned as belonging to another module)
- Key frameworks, named systems, and processes
- Word-for-word scripts, templates, or formulas worth preserving verbatim

### KB Groupings
Identify 2–4 logical groupings for the knowledge base files. Good grouping criteria:
- By phase (e.g., strategy → execution → optimization)
- By topic cluster (e.g., ads + tracking vs. organic content)
- By video block (e.g., Videos 1–7 vs. Videos 8–14)

Aim for each KB file to be self-contained and focused.

---

## Step 4: Generate the Files

Create the output directory: `~/custom-gpts/<project>/<gpt-slug>/`

Where:
- `<project>` = the platform/course name in kebab-case (e.g., `kourse`)
- `<gpt-slug>` = the GPT name in kebab-case (e.g., `sales-os-gpt`)

If no project name is clear from context, use `custom-gpts` as the project folder.

---

### `system-prompt.md`

Structure:

```
# [GPT Name] — System Prompt

[1-2 sentence description of what this GPT is and who it serves]

## Your Instructor / Personality

[Instructor name, role, credentials]
[Tone descriptors — 4-6 bullet points]

### How You Talk
[Signature phrases, voice characteristics]

### How You DON'T Talk
[What to avoid — e.g., generic advice, pressure tactics, vague theory]

## How You Answer Questions

[4-5 numbered rules for answering — e.g., check KB first, be specific, give scripts not summaries]

## Topics You Can Help With

[Organized by category — mirror the KB structure. For each category, list 6-12 specific sub-topics as bullets. Be specific enough that the GPT knows what's covered.]

## Topics Outside Your Scope

[List other modules/sections and what topics belong there. Include a redirect template.]

## Response Format

[Formatting rules — length, use of bullets/bold/numbered lists, whether to end with action steps, etc.]
```

**Rules for system-prompt:**
- Instructor voice must be specific — generic "be helpful and friendly" is useless
- Topics list should be detailed enough that the GPT can self-identify whether a question is in scope
- Out-of-scope section prevents hallucination about topics not in the KB
- Do NOT include long scripts or frameworks here — those belong in KB files
- If a voice profile file exists (user confirmed in Step 2), skip voice details and add a note: "Voice and credentials are defined in the uploaded `voice-profile.md` knowledge file."

---

### `kb-*.md` (2–4 files)

Name files descriptively: `kb-<topic-group>.md`

Structure per file:

```
# Knowledge Base: [Topic Group Name]

## [Module/Course Name] — [Video or Section Range]

---

## [Section Title]

### [Sub-topic]

[Condensed, actionable content. Preserve:]
- Named frameworks with their components
- Word-for-word scripts (formatted in italics or blockquotes)
- Step-by-step processes (numbered)
- Key data points, thresholds, or rules of thumb
- Tables for multi-column information

[Do NOT preserve:]
- Filler, repetition, or motivational padding
- Long storytelling tangents (summarize the point they illustrate)
- Jokes or asides that don't add information
```

**Conciseness rules:**
- Extract the framework, not the explanation of the framework
- If a script is word-for-word, keep it word-for-word — that's the value
- If a concept takes 3 paragraphs to explain in the transcript, distill it to 3-5 sentences
- Tables > bullet lists > paragraphs (in that order of preference)
- Each KB file should be self-contained — someone reading just that file should understand the topic

---

### `README.md`

Structure:

```
# [GPT Name] — Setup Guide

## What's in This Folder

[Table: File | Purpose | Upload To]
[Include voice-profile.md row if applicable]

> Note: [Any important setup notes — e.g., "Do NOT upload X" or "Y's voice is in system-prompt directly"]

## Setup Steps (OpenAI Custom GPT)

1. Go to chat.openai.com → Explore GPTs → Create
2. In the Configure tab:
   - Name: [GPT Name]
   - Description: [1-sentence description]
   - Instructions: Copy/paste system-prompt.md
3. Under Knowledge, upload: [list all KB files + voice-profile if applicable]
4. Under Capabilities:
   - Disable Web Browsing
   - Code Interpreter: not needed
5. Save and test

## Sample Test Questions

[10-15 questions that cover the most important topics. For each, add → [what the correct answer should reference]]

## Knowledge Base Coverage Map

[Table: Video/Section | Topic | Knowledge File]
```

---

## Step 5: Review & Output

After generating all files, show the user:

1. A summary of what was created (file list + brief description of each)
2. The KB groupings chosen and why
3. The sample test questions (most useful for verifying coverage)

Ask: "Want me to adjust anything — the voice, add more topics, regroup KB files, or add more sample questions?"

If they're happy, confirm the output path and remind them:
- Paste `system-prompt.md` into the Instructions field
- Upload all `kb-*.md` files as Knowledge
- Upload `voice-profile.md` as Knowledge if applicable
- Disable web browsing

---

## Rules

- **Condense, don't transcribe.** KB files are not transcripts. They're distilled references.
- **Preserve scripts verbatim.** If the instructor gives a word-for-word script, keep it exactly.
- **Be specific in the system prompt.** Generic personality descriptions produce generic GPT behavior.
- **Group KB files by logical topic, not by video number** — unless the content is so large that video-number grouping is the only way to keep files manageable.
- **Never put long scripts or frameworks in system-prompt.** That's what KB files are for.
- **Out-of-scope = hallucination prevention.** Always include a clear out-of-scope section with redirect language.
- **Sample test questions should be hard enough to actually test coverage.** Not "what is X" but "walk me through how to do X" or "someone said Y — what do I do?"
- **If content is very large** (15+ videos, 50k+ words), create 3–4 KB files and be more aggressive about condensing. If content is small (3–5 short videos), one KB file may be enough.
- Save all files to `~/custom-gpts/<project>/<gpt-slug>/` — never anywhere else.
