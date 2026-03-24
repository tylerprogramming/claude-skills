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
