#!/usr/bin/env python3
"""Shared Kie.ai client used by all /kie-* skills.

Kie.ai exposes a single unified job API:
  POST {API_BASE}/jobs/createTask   body: {"model": "<id>", "input": {...}}
  GET  {API_BASE}/jobs/recordInfo?taskId=<id>   -> poll until state == success
  POST {UPLOAD_BASE}/api/file-base64-upload     -> host a local file, get a URL

All skills import the helpers here so the HTTP/auth/polling/upload logic lives
in exactly one place. Per-model skills only define their model registry +
input-payload shape and call these functions.

Import pattern from a skill script (works through the ~/.claude/skills symlinks
because we resolve the real path):

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_kie"))
    import kie_client as kie
"""

# --- skills venv bootstrap: run under .venv, not whatever python3 resolves to.
# Looks for .venv beside this script and up a few levels, then ~/.claude/skills,
# so a skill works wherever you copied it. Compares realpaths, and re-execs at
# most once, because a symlinked path that never compares equal would otherwise
# loop forever. Rationale: "Why there is a venv" in README.md
import os as _os, sys as _sys
if not _os.environ.get("SKILLS_VENV"):
    _base = _os.path.dirname(_os.path.abspath(__file__))
    for _v in [_os.path.realpath(_os.path.join(_base, *([".."] * _i), ".venv")) for _i in range(4)
               ] + [_os.path.realpath(_os.path.expanduser("~/.claude/skills/.venv"))]:
        if _os.path.exists(_os.path.join(_v, "bin", "python3")):
            if _os.path.realpath(_sys.prefix) != _v:
                _os.environ["SKILLS_VENV"] = _v
                _os.execv(_os.path.join(_v, "bin", "python3"),
                          [_os.path.join(_v, "bin", "python3"), *_sys.argv])
            break
# --- end bootstrap ---------------------------------------------------------

import base64
import json
import mimetypes
import os
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

# macOS python.org builds don't trust the system cert store — use certifi's CA
# bundle when available so HTTPS verification works everywhere.
try:
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _SSL_CTX = ssl.create_default_context()

API_BASE = "https://api.kie.ai/api/v1"
UPLOAD_BASE = "https://kieai.redpandaai.co"
CREATE_TASK_URL = f"{API_BASE}/jobs/createTask"
RECORD_INFO_URL = f"{API_BASE}/jobs/recordInfo"
UPLOAD_URL = f"{UPLOAD_BASE}/api/file-base64-upload"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def get_api_key():
    """KIE_API_KEY from env, falling back to ~/.claude/.env."""
    key = os.environ.get("KIE_API_KEY")
    if not key:
        env_file = Path.home() / ".claude" / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line.startswith("KIE_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not key:
        print("Error: KIE_API_KEY not found.", file=sys.stderr)
        print("Set it in ~/.claude/.env as KIE_API_KEY=your_key", file=sys.stderr)
        sys.exit(1)
    return key


def api_request(url, data=None, api_key=None, timeout=30):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if data is not None:
        req = urllib.request.Request(
            url, data=json.dumps(data).encode(), headers=headers, method="POST"
        )
    else:
        req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"API error {e.code}: {body}", file=sys.stderr)
        if e.code == 401:
            print("  -> KIE_API_KEY missing or invalid.", file=sys.stderr)
        elif e.code == 402:
            print("  -> Insufficient credits. Top up at https://kie.ai", file=sys.stderr)
        elif e.code == 429:
            print("  -> Rate limited. Wait a moment and retry.", file=sys.stderr)
        sys.exit(1)


def upload_local_file(file_path, api_key, upload_path="skills/uploads"):
    """Upload a local file to Kie.ai, return a hosted download URL (or None)."""
    path = Path(file_path)
    if not path.exists():
        print(f"  Error: File not found: {path}", file=sys.stderr)
        return None

    mime_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    data_url = f"data:{mime_type};base64,{base64.b64encode(path.read_bytes()).decode()}"
    payload = json.dumps({
        "base64Data": data_url,
        "uploadPath": upload_path,
        "fileName": path.name,
    })

    print(f"  Uploading {path.name}...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        tmp.write(payload)
        tmp_path = tmp.name
    try:
        result = subprocess.run(
            ["curl", "-sS", "-X", "POST", UPLOAD_URL,
             "-H", f"Authorization: Bearer {api_key}",
             "-H", "Content-Type: application/json",
             "-d", f"@{tmp_path}"],
            capture_output=True, text=True, timeout=180,
        )
    finally:
        os.unlink(tmp_path)

    if result.returncode != 0:
        print(f"  Upload failed: {result.stderr}", file=sys.stderr)
        return None
    try:
        resp = json.loads(result.stdout)
        if resp.get("success") or resp.get("code") == 200:
            url = resp["data"]["downloadUrl"]
            print(f"  Uploaded: {url}")
            return url
        print(f"  Upload failed: {resp}", file=sys.stderr)
        return None
    except (json.JSONDecodeError, KeyError) as e:
        print(f"  Upload parse error: {e}\n  Response: {result.stdout[:200]}", file=sys.stderr)
        return None


def resolve_media(refs, api_key, max_items=None, upload_path="skills/uploads"):
    """Turn a list of URLs / local files / folders into a list of hosted URLs.

    URLs pass through untouched; local files/folders are uploaded.
    """
    if not refs:
        return []
    urls = []
    for ref in refs:
        if ref.startswith("http://") or ref.startswith("https://"):
            urls.append(ref)
            continue
        path = Path(ref).expanduser()
        if path.is_dir():
            files = sorted(f for f in path.iterdir() if f.suffix.lower() in IMAGE_EXTS)
            if not files:
                print(f"  No images found in {path}", file=sys.stderr)
                continue
            for f in files:
                url = upload_local_file(f, api_key, upload_path)
                if url:
                    urls.append(url)
        elif path.is_file():
            url = upload_local_file(path, api_key, upload_path)
            if url:
                urls.append(url)
        else:
            print(f"  Warning: not found: {ref}", file=sys.stderr)
    if max_items and len(urls) > max_items:
        print(f"  Trimming to {max_items} item(s) (had {len(urls)})")
        urls = urls[:max_items]
    return urls


def create_task(model_id, input_payload, api_key):
    """Create a generation task, return its taskId."""
    payload = {"model": model_id, "input": input_payload}
    resp = api_request(CREATE_TASK_URL, data=payload, api_key=api_key)
    if resp.get("code") != 200:
        print(f"Error creating task: {resp}", file=sys.stderr)
        sys.exit(1)
    task_id = resp["data"]["taskId"]
    print(f"  Task ID: {task_id}")
    return task_id


def poll_task(task_id, api_key, max_wait=900, interval=8, label="Generating"):
    """Poll recordInfo until success/fail. Returns list of result URLs.

    max_wait defaults to 15 min — video jobs can take several minutes.
    """
    url = f"{RECORD_INFO_URL}?taskId={task_id}"
    start = time.time()
    state_labels = {
        "waiting": "Waiting",
        "queuing": "In queue",
        "generating": label,
    }
    print("Waiting for generation to complete...")
    while time.time() - start < max_wait:
        resp = api_request(url, api_key=api_key)
        data = resp.get("data", {})
        state = data.get("state", "")
        if state == "success":
            result_json = data.get("resultJson", "{}")
            if isinstance(result_json, str):
                result_json = json.loads(result_json or "{}")
            urls = result_json.get("resultUrls", []) or result_json.get("result_urls", [])
            cost_time = data.get("costTime", 0)
            print(f"  Generation complete! ({int(cost_time) // 1000 if cost_time and cost_time > 1000 else cost_time}s)")
            return urls
        if state == "fail":
            print(f"  Generation failed [{data.get('failCode', '')}]: "
                  f"{data.get('failMsg', 'Unknown error')}", file=sys.stderr)
            sys.exit(1)
        elapsed = int(time.time() - start)
        lbl = state_labels.get(state, state or "Processing")
        print(f"  {lbl}... ({elapsed}s)    ", end="\r")
        time.sleep(interval)
    print(f"\n  Timed out after {max_wait}s. Task may still finish — id: {task_id}", file=sys.stderr)
    sys.exit(1)


def download_file(url, output_path):
    """Download a result file (image or video) to disk."""
    output_path = Path(output_path)
    print(f"  Downloading -> {output_path.name} ...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120, context=_SSL_CTX) as resp:
            output_path.write_bytes(resp.read())
        print(f"  Saved: {output_path}")
        return True
    except urllib.error.HTTPError as e:
        print(f"  Direct download failed ({e.code}), trying curl...")
        result = subprocess.run(["curl", "-sL", "-o", str(output_path), url],
                                capture_output=True, text=True)
        if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
            print(f"  Saved: {output_path}")
            return True
        print(f"  Download failed. URL (expires in ~24h): {url}", file=sys.stderr)
        return False
