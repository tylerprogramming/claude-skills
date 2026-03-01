---
name: transcribe
description: Transcribe a YouTube video or local video/audio file using OpenAI Whisper. Use when the user asks to transcribe a video, get a transcript, convert a video to text, provides a YouTube URL, or has a local MP4/audio file to transcribe. Triggers on: transcribe this video, get transcript, transcribe youtube, what does this video say, convert video to text, transcribe this file.
argument-hint: [youtube_url or /path/to/file.mp4]
allowed-tools: Bash(python3:*), Bash(yt-dlp:*)
user-invocable: true
---

Transcribe the video or audio at $ARGUMENTS.

## Instructions

1. Run the transcription script:
   ```
   python3 ~/.claude/skills/transcribe/transcribe_video.py "$ARGUMENTS"
   ```
2. The script will:
   - For YouTube URLs: Download the audio using yt-dlp, then transcribe
   - For local files: Transcribe directly (supports mp4, mp3, wav, m4a, etc.)
   - Save a timestamped transcript to `~/scripts/transcript_<id>.txt`
3. After the script finishes, read the saved transcript file from `~/scripts/` and present the full contents to the user.
4. If the script fails, check:
   - Is `OPENAI_API_KEY` set in the environment?
   - Is `yt-dlp` installed? (only needed for YouTube URLs)
   - For local files: Does the file exist? Is it under 25MB?
   - For YouTube: Is the URL valid and publicly accessible?
