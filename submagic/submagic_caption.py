#!/usr/bin/env python3
"""Burn on-screen captions onto a video via the Submagic API.

Direct-upload path: pushes the mp4 straight to POST /v1/projects/upload
(multipart/form-data). Bypasses Google Drive, avoiding virus-scan redirects
on large files. Also preserves the requested theme reliably (the Drive-URL
path occasionally got the theme silently swapped on concurrent jobs).

Scope: captions only. Does NOT generate platform post copy and does NOT
replace /transcribe.
"""

import json
import os
import sys
import time
import uuid as uuidlib
import urllib.request
import urllib.error
from pathlib import Path

ENV_PATH = Path.home() / ".claude" / ".env"
OUTPUT_DIR = Path.home() / "content" / "submagic"
SUBMAGIC_BASE = "https://api.submagic.co/v1"
POLL_INTERVAL_SEC = 15
POLL_TIMEOUT_SEC = 60 * 45

DEFAULT_DICTIONARY = [
    "claude code", "claude", "anthropic", "routines", "skills",
    "n8n", "submagic", "apify", "blotato", "kie.ai", "nano banana",
]


def load_env() -> dict:
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def upload_direct(api_key: str, theme_id: str, file_path: Path) -> str:
    boundary = "------boundary" + uuidlib.uuid4().hex
    CRLF = b"\r\n"
    fields = {
        "title": file_path.stem,
        "language": "en",
        "userThemeId": theme_id,
        "dictionary": json.dumps(DEFAULT_DICTIONARY),
        "magicZooms": "false",
        "magicBrolls": "false",
        "removeSilencePace": "fast",
        "removeBadTakes": "false",
    }
    parts = []
    for name, value in fields.items():
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}".encode()
        )
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    file_part = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"video\"; filename=\"{file_path.name}\"\r\n"
        f"Content-Type: video/mp4\r\n\r\n"
    ).encode() + file_bytes
    body = CRLF.join(parts) + CRLF + file_part + CRLF + f"--{boundary}--\r\n".encode()

    print(f"Uploading {len(body) / 1e6:.1f} MB direct to Submagic...")
    req = urllib.request.Request(
        f"{SUBMAGIC_BASE}/projects/upload",
        data=body,
        headers={
            "x-api-key": api_key,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=900) as r:
        resp = json.loads(r.read().decode())
    pid = resp["id"]
    stored = resp.get("userThemeId")
    print(f"  project id: {pid}")
    print(f"  theme stored: {stored}")
    if stored != theme_id:
        print(f"  WARNING: Submagic swapped theme. Requested {theme_id}, got {stored}.")
    return pid


def poll_and_download(api_key: str, pid: str, src: Path) -> Path:
    start = time.time()
    last = None
    while time.time() - start < POLL_TIMEOUT_SEC:
        req = urllib.request.Request(
            f"{SUBMAGIC_BASE}/projects/{pid}",
            headers={"x-api-key": api_key},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode())
        s = d.get("status")
        if s != last:
            print(f"  status: {s}")
            last = s
        if s == "completed":
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            out = OUTPUT_DIR / f"{src.stem} - captioned-{pid.split('-')[0]}.mp4"
            with urllib.request.urlopen(d["downloadUrl"], timeout=900) as rr, open(out, "wb") as f:
                while True:
                    chunk = rr.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
            print()
            print("Done.")
            print(f"  local: {out}")
            print(f"  duration: {d.get('videoMetaData', {}).get('duration')}s")
            return out
        if s == "failed":
            raise RuntimeError(f"Submagic failed: {d.get('failureReason')}")
        time.sleep(POLL_INTERVAL_SEC)
    raise RuntimeError("polling timed out")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: submagic_caption.py /path/to/video.mp4", file=sys.stderr)
        return 1
    src = Path(sys.argv[1]).expanduser()
    if not src.exists():
        print(f"File not found: {src}", file=sys.stderr)
        return 1

    env = load_env()
    api_key = env.get("SUBMAGIC_API_KEY") or os.environ.get("SUBMAGIC_API_KEY")
    theme_id = env.get("SUBMAGIC_THEME_ID") or os.environ.get("SUBMAGIC_THEME_ID")
    if not api_key:
        print("Missing SUBMAGIC_API_KEY in ~/.claude/.env", file=sys.stderr)
        return 1
    if not theme_id:
        print("Missing SUBMAGIC_THEME_ID in ~/.claude/.env", file=sys.stderr)
        return 1

    pid = upload_direct(api_key, theme_id, src)
    poll_and_download(api_key, pid, src)
    return 0


if __name__ == "__main__":
    sys.exit(main())
