"""
Transcribe a YouTube video or local video/audio file using OpenAI Whisper.

Usage:
  python transcribe_video.py <youtube_url>
  python transcribe_video.py <local_file_path>

For YouTube URLs: Downloads audio via yt-dlp, then transcribes.
For local files: Transcribes directly (supports mp4, mp3, wav, m4a, etc.)

Saves the transcript to ~/scripts/transcript_<id>.txt

For large files (>24MB), automatically splits into 30-min chunks via ffmpeg.

Requires:
  - yt-dlp (for YouTube URLs only)
  - ffmpeg (for splitting large files)
  - openai Python package
  - OPENAI_API_KEY in ~/.claude/.env
"""

import sys
import os
import glob
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from openai import OpenAI

WHISPER_MAX_SIZE = 24 * 1024 * 1024  # 24 MB safe margin
CHUNK_DURATION = 1800                  # 30 minutes per chunk


def load_env():
    env_path = Path.home() / ".claude" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def extract_video_id(url):
    query = urlparse(url)
    if query.hostname == "youtu.be":
        return query.path[1:].split("?")[0]
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
    """Download audio from YouTube at low bitrate mono to minimize file size."""
    cmd = [
        "yt-dlp",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "9",
        "--postprocessor-args", "ffmpeg:-ar 16000 -ac 1 -b:a 32k",
        "-o", output_path,
        "--no-playlist",
        "--quiet",
        "--progress",
        url,
    ]
    print("Downloading audio (32kbps mono for Whisper)...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Fallback without postprocessor args
        cmd_fallback = [
            "yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "9",
            "-o", output_path, "--no-playlist", "--quiet", "--progress", url,
        ]
        result = subprocess.run(cmd_fallback, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp failed: {result.stderr}")

    for candidate in [output_path, output_path + ".mp3"]:
        if os.path.exists(candidate):
            return candidate
    raise FileNotFoundError(f"Audio file not found at {output_path}")


def split_audio(audio_path, tmpdir):
    """Split audio into 30-minute chunks using ffmpeg. Returns sorted chunk paths."""
    pattern = os.path.join(tmpdir, "chunk_%04d.mp3")
    cmd = [
        "ffmpeg", "-i", audio_path,
        "-f", "segment",
        "-segment_time", str(CHUNK_DURATION),
        "-acodec", "libmp3lame",
        "-b:a", "32k",
        "-ar", "16000",
        "-ac", "1",
        pattern,
        "-y", "-loglevel", "error"
    ]
    print("Splitting audio into 30-minute chunks...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg split failed: {result.stderr}")

    chunks = sorted(glob.glob(os.path.join(tmpdir, "chunk_*.mp3")))
    if not chunks:
        raise FileNotFoundError("ffmpeg produced no chunk files")
    print(f"Split into {len(chunks)} chunks")
    return chunks


def transcribe_single(audio_path, client):
    """Transcribe one audio file with Whisper."""
    with open(audio_path, "rb") as f:
        return client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
        )


def format_timestamp(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def is_local_file(path):
    return os.path.exists(path)


def get_file_id(path):
    name, _ = os.path.splitext(os.path.basename(path))
    return name.replace(" ", "_").replace("-", "_")


def transcribe_audio_file(audio_path, client):
    """Transcribe audio, auto-splitting if file exceeds Whisper's 24MB limit."""
    file_size = os.path.getsize(audio_path)
    print(f"Audio file size: {file_size / (1024*1024):.1f} MB")

    if file_size <= WHISPER_MAX_SIZE:
        print("Transcribing with Whisper (single pass)...")
        return transcribe_single(audio_path, client)

    # Large file: chunk and stitch
    print(f"File exceeds 24MB — splitting into 30-minute chunks...")
    chunk_tmpdir = tempfile.mkdtemp(prefix="whisper_chunks_")
    all_segments = []
    total_duration = 0.0

    try:
        chunks = split_audio(audio_path, chunk_tmpdir)

        for i, chunk_path in enumerate(chunks):
            chunk_mb = os.path.getsize(chunk_path) / (1024 * 1024)
            time_offset = i * CHUNK_DURATION
            print(f"  [{i+1}/{len(chunks)}] {chunk_mb:.1f}MB  offset={format_timestamp(time_offset)}")

            resp = transcribe_single(chunk_path, client)

            if hasattr(resp, "segments") and resp.segments:
                for seg in resp.segments:
                    all_segments.append({
                        "start": seg.start + time_offset,
                        "text": seg.text.strip()
                    })
                total_duration = time_offset + resp.segments[-1].end
            else:
                all_segments.append({"start": time_offset, "text": resp.text.strip()})
                total_duration = time_offset + CHUNK_DURATION

    finally:
        for f in glob.glob(os.path.join(chunk_tmpdir, "*.mp3")):
            os.remove(f)
        try:
            os.rmdir(chunk_tmpdir)
        except Exception:
            pass

    class Seg:
        def __init__(self, start, text):
            self.start = start
            self.text = text

    class Combined:
        def __init__(self, segs, dur):
            self.segments = segs
            self.duration = dur
            self.language = "en"

    return Combined([Seg(s["start"], s["text"]) for s in all_segments], total_duration)


def main():
    load_env()

    if len(sys.argv) < 2:
        print("Usage: python transcribe_video.py <youtube_url_or_local_file>")
        sys.exit(1)

    input_path = sys.argv[1]
    client = OpenAI()

    if is_local_file(input_path):
        print(f"Local file: {input_path}")
        file_id = get_file_id(input_path)
        response = transcribe_audio_file(input_path, client)
    else:
        video_id = extract_video_id(input_path)
        if not video_id:
            print(f"Could not extract video ID from: {input_path}")
            sys.exit(1)

        file_id = video_id
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = os.path.join(tmpdir, f"audio_{video_id}")
            actual_path = download_audio(input_path, audio_path)
            response = transcribe_audio_file(actual_path, client)

    # Format output
    lines = []
    if hasattr(response, "segments") and response.segments:
        for seg in response.segments:
            lines.append(f"[{format_timestamp(seg.start)}] {seg.text.strip()}")
        transcript_text = "\n".join(lines)
    else:
        transcript_text = response.text

    # Save
    scripts_dir = os.path.expanduser("~/scripts")
    os.makedirs(scripts_dir, exist_ok=True)
    out_file = os.path.join(scripts_dir, f"transcript_{file_id}.txt")
    with open(out_file, "w") as f:
        f.write(transcript_text)

    duration_str = format_timestamp(response.duration) if hasattr(response, "duration") else "unknown"
    language = getattr(response, "language", "unknown")

    print(f"\n--- Transcript ({duration_str}) ---\n")
    preview = transcript_text[:2000]
    if len(transcript_text) > 2000:
        preview += "\n..."
    print(preview)
    print(f"\n--- End ---")
    print(f"\nFull transcript saved to: {out_file}")
    print(f"Duration: {duration_str} | Language: {language}")


if __name__ == "__main__":
    main()
