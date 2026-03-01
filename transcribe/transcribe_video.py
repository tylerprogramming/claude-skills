"""
Transcribe a YouTube video or local video/audio file using OpenAI Whisper.

Usage:
  python transcribe_video.py <youtube_url>
  python transcribe_video.py <local_file_path>

For YouTube URLs: Downloads audio via yt-dlp, then transcribes.
For local files: Transcribes directly (supports mp4, mp3, wav, m4a, etc.)

Saves the transcript to ~/scripts/transcript_<id>.txt

Requires:
  - yt-dlp (for YouTube URLs only)
  - openai Python package
  - OPENAI_API_KEY environment variable
"""

import sys
import os
import subprocess
import tempfile
from urllib.parse import urlparse, parse_qs

from openai import OpenAI

WHISPER_MAX_SIZE = 25 * 1024 * 1024  # 25 MB


def extract_video_id(url):
    query = urlparse(url)
    if query.hostname == "youtu.be":
        return query.path[1:]
    if query.hostname in ("www.youtube.com", "youtube.com"):
        if query.path == "/watch":
            p = parse_qs(query.query)
            return p["v"][0]
        if query.path.startswith("/embed/"):
            return query.path.split("/")[2]
        if query.path.startswith("/v/"):
            return query.path.split("/")[2]
        if query.path.startswith("/shorts/"):
            return query.path.split("/")[2]
    return None


def download_audio(url, output_path):
    """Download audio from YouTube using yt-dlp."""
    cmd = [
        "yt-dlp",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "5",
        "-o", output_path,
        "--no-playlist",
        "--quiet",
        "--progress",
        url,
    ]
    print(f"Downloading audio...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr}")
    if os.path.exists(output_path):
        return output_path
    if os.path.exists(output_path + ".mp3"):
        return output_path + ".mp3"
    raise FileNotFoundError(f"Audio file not found at {output_path}")


def transcribe_audio(audio_path):
    """Transcribe audio file using OpenAI Whisper API."""
    file_size = os.path.getsize(audio_path)
    print(f"Audio file size: {file_size / (1024*1024):.1f} MB")

    if file_size > WHISPER_MAX_SIZE:
        print(f"Error: File exceeds 25MB Whisper limit ({file_size / (1024*1024):.1f} MB).")
        print(f"Consider using a shorter video.")
        sys.exit(1)

    client = OpenAI()
    print("Transcribing with Whisper...")
    with open(audio_path, "rb") as f:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
        )

    return response


def format_timestamp(seconds):
    """Convert seconds to HH:MM:SS format."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def is_local_file(path):
    """Check if the input is a local file path."""
    return os.path.exists(path)


def get_file_id(path):
    """Generate an ID from a local file path."""
    basename = os.path.basename(path)
    name, _ = os.path.splitext(basename)
    # Clean up the name for use as an ID
    return name.replace(" ", "_").replace("-", "_")


def main():
    if len(sys.argv) < 2:
        print("Usage: python transcribe_video.py <youtube_url_or_local_file>")
        sys.exit(1)

    input_path = sys.argv[1]

    # Check if it's a local file or YouTube URL
    if is_local_file(input_path):
        print(f"Detected local file: {input_path}")
        file_id = get_file_id(input_path)
        audio_path = input_path

        # Transcribe directly
        response = transcribe_audio(audio_path)
    else:
        # Treat as YouTube URL
        video_id = extract_video_id(input_path)

        if not video_id:
            print(f"Could not extract video ID from: {input_path}")
            print("And file does not exist at that path.")
            sys.exit(1)

        file_id = video_id

        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = os.path.join(tmpdir, f"audio_{video_id}")

            # Download
            actual_path = download_audio(input_path, audio_path)

            # Transcribe
            response = transcribe_audio(actual_path)

    # Format output with timestamps
    lines = []
    if hasattr(response, "segments") and response.segments:
        for seg in response.segments:
            ts = format_timestamp(seg.start)
            lines.append(f"[{ts}] {seg.text.strip()}")
        transcript_text = "\n".join(lines)
    else:
        transcript_text = response.text

    # Save to ~/scripts/
    scripts_dir = os.path.expanduser("~/scripts")
    os.makedirs(scripts_dir, exist_ok=True)
    out_file = os.path.join(scripts_dir, f"transcript_{file_id}.txt")
    with open(out_file, "w") as f:
        f.write(transcript_text)

    print(f"\n--- Transcript ({format_timestamp(response.duration)}) ---\n")
    preview = transcript_text[:2000]
    if len(transcript_text) > 2000:
        preview += "\n..."
    print(preview)
    print(f"\n--- End ---")
    print(f"\nFull transcript saved to: {out_file}")
    print(f"Duration: {format_timestamp(response.duration)}")
    print(f"Language: {response.language}")


if __name__ == "__main__":
    main()
