---
name: chapters
description: Generate accurate YouTube chapters from a final edited video. Extracts audio with ffmpeg, transcribes it, then updates the video package description with real timestamps. Triggers on: generate chapters, update chapters, finalize description, chapters from video, update timestamps, post-edit description.
argument-hint: [/path/to/final-video.mp4] [--slug <video-slug>]
allowed-tools: Bash(ffmpeg:*), Bash(python3:*), Bash(yt-dlp:*), Read, Write, Edit, Glob, Grep, AskUserQuestion
user-invocable: true
---

Generate accurate YouTube chapters from the final edited video at $ARGUMENTS.

## Workflow Context

**Final step of the weekly content pipeline** — runs post-edit when the editor delivers the final `.mp4`. Do NOT run this before filming or editing. After this, the description is ready to copy-paste into YouTube.

## Flow

### Step 1: Parse Input

From $ARGUMENTS, extract:
- **Video path**: The local `.mp4` file (required)
- **Slug** (optional): `--slug <video-slug>` to identify the video package at `~/youtube/<slug>/`

If no slug is provided:
- Check if the video filename or parent folder matches an existing `~/youtube/<slug>/` package
- If not, ask the user: **"Which video package does this belong to?"** and list existing packages from `~/youtube/`

If the video path doesn't exist, ask the user for the correct path.

### Step 2: Extract Audio

Extract the audio track from the video using ffmpeg:

```
ffmpeg -i "<video_path>" -vn -acodec libmp3lame -q:a 2 ~/scripts/chapters_audio_<slug>.mp3 -y
```

This is faster and smaller than processing the full video file.

### Step 3: Transcribe

Transcribe the extracted audio using the transcribe skill's script:

```
python3 ~/.claude/skills/transcribe/transcribe_video.py ~/scripts/chapters_audio_<slug>.mp3
```

Read the resulting transcript file. It should contain timestamped segments.

### Step 4: Identify Chapters

Analyze the transcript to identify natural chapter breaks. Look for:

- **Topic transitions** — When the speaker shifts to a new subject
- **Section markers** — Phrases like "next", "now let's", "moving on", "the first thing", "step one"
- **Demo transitions** — Shifts between talking and showing something
- **Energy shifts** — New introductions of concepts after a conclusion of the previous one

Generate **5-15 chapters** depending on video length:
- Videos under 5 min: 3-5 chapters
- Videos 5-15 min: 5-10 chapters
- Videos 15+ min: 8-15 chapters

For each chapter:
- **Timestamp** in `MM:SS` format (or `H:MM:SS` for videos over 1 hour)
- **Title** — Short, descriptive, 2-6 words

The first chapter MUST be `0:00 - Introduction` (or a more specific hook title).

### Step 5: Read Existing Description

Read `~/youtube/<slug>/description.md` if it exists. Identify:
- Is there an existing chapters section with `[UPDATE]` placeholders?
- What's the overall structure of the description?

### Step 6: Present Chapters to User

Show the user the generated chapters:

```
0:00 - Introduction
0:45 - Setting Up the Project
2:12 - First Demo
...
```

Ask: **"Do these chapters look right? Want to adjust any timestamps or titles?"**

### Step 7: Update Description

After the user approves (or after revisions):

**If `description.md` exists with placeholder chapters:**
- Replace the entire chapters section (the `[UPDATE]` placeholders) with the real timestamps

**If `description.md` exists without a chapters section:**
- Add a chapters section in the appropriate location (after the main body, before links/tags)

**If no `description.md` exists:**
- Create `~/youtube/<slug>/description.md` with just the chapters section and a note to fill in the rest

Show the user the updated description and confirm the file was saved.

### Step 8: Cleanup

Delete the temporary audio file:
```
rm ~/scripts/chapters_audio_<slug>.mp3
```

Report what was done:
- Transcript location
- Updated description path
- Number of chapters generated

## Rules

- Always extract audio first — don't try to transcribe the full video file directly (it's slower and larger)
- Chapters must start at `0:00` — YouTube requires this
- Chapter titles should be concise (2-6 words) — they appear in the progress bar
- Minimum 3 chapters for YouTube to recognize them as chapters
- Timestamps must be accurate to within ~5 seconds — round to clean numbers when the transition isn't instant
- Don't create chapters shorter than 10 seconds — YouTube may not display them
- When updating `description.md`, preserve all existing content outside the chapters section
- Clean up the temporary mp3 after transcription
- If the transcription doesn't have clear timestamps, estimate based on word count (~150 words per minute of speech)
