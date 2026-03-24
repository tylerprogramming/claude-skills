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
