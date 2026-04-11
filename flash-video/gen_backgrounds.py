#!/usr/bin/env python3
"""
Generate reusable background images for flash-video via Kie.ai.
Saves to ~/.claude/skills/flash-video/backgrounds/cream.png and dark.png
"""

import sys
import json
import os
import time
import urllib.request
import urllib.error
import subprocess
from pathlib import Path

API_BASE = "https://api.kie.ai/api/v1"
CREATE_TASK_URL = f"{API_BASE}/jobs/createTask"
RECORD_INFO_URL = f"{API_BASE}/jobs/recordInfo"

ASSETS_DIR = Path(__file__).parent / "backgrounds"
ASSETS_DIR.mkdir(exist_ok=True)


def get_api_key():
    key = os.environ.get("KIE_API_KEY")
    if not key:
        env_file = Path.home() / ".claude" / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("KIE_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        print("Error: KIE_API_KEY not found", file=sys.stderr)
        sys.exit(1)
    return key


def api_post(url, payload, api_key):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def api_get(url, api_key):
    headers = {"Authorization": f"Bearer {api_key}"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def submit_task(prompt, api_key):
    payload = {
        "model": "nano-banana-pro",
        "input": {
            "prompt": prompt,
            "image_input": [],
            "aspect_ratio": "9:16",
            "resolution": "1K",
            "output_format": "png",
        },
    }
    resp = api_post(CREATE_TASK_URL, payload, api_key)
    if resp.get("code") != 200:
        print(f"Task creation failed: {resp}", file=sys.stderr)
        sys.exit(1)
    return resp["data"]["taskId"]


def poll_task(task_id, api_key, label="", max_wait=300):
    url = f"{RECORD_INFO_URL}?taskId={task_id}"
    start = time.time()
    while time.time() - start < max_wait:
        resp = api_get(url, api_key)
        data = resp.get("data", {})
        state = data.get("state", "")
        if state == "success":
            result_json = data.get("resultJson", "{}")
            if isinstance(result_json, str):
                result_json = json.loads(result_json)
            urls = result_json.get("resultUrls", [])
            elapsed = int(time.time() - start)
            print(f"  {label} done ({elapsed}s)")
            return urls
        elif state == "fail":
            print(f"  {label} failed: {data.get('failMsg', 'unknown')}", file=sys.stderr)
            sys.exit(1)
        else:
            elapsed = int(time.time() - start)
            print(f"  {label} {state or 'waiting'}... ({elapsed}s)", end="\r")
            time.sleep(5)
    print(f"\n  Timed out", file=sys.stderr)
    sys.exit(1)


def download(url, path):
    result = subprocess.run(["curl", "-sL", "-o", str(path), url], capture_output=True, timeout=60)
    return result.returncode == 0 and Path(path).exists()


PROMPTS = {
    "cream": """Minimalist warm cream off-white background, color #F5F0E8, clean editorial aesthetic,
very subtle soft paper texture, gentle warm light from top, no text, no people, no objects,
purely abstract background, 9:16 vertical portrait, ultra clean, magazine editorial style""",

    "dark": """Dark moody workspace background, deep charcoal near-black #1C1C1C,
very faint soft blue-grey ambient glow, subtle dark gradient, cinematic editorial feel,
no text, no people, no objects, purely abstract dark background, 9:16 vertical portrait,
minimal clean aesthetic, premium feel""",
}


def main():
    styles = sys.argv[1:] if len(sys.argv) > 1 else list(PROMPTS.keys())
    api_key = get_api_key()

    # Submit all tasks first
    task_ids = {}
    for style in styles:
        if style not in PROMPTS:
            print(f"Unknown style: {style}. Choose from: {list(PROMPTS.keys())}")
            continue
        out_path = ASSETS_DIR / f"{style}.png"
        print(f"\n── Generating {style} background ──")
        task_id = submit_task(PROMPTS[style], api_key)
        print(f"  Task: {task_id}")
        task_ids[style] = task_id

    # Poll and download each
    for style, task_id in task_ids.items():
        out_path = ASSETS_DIR / f"{style}.png"
        urls = poll_task(task_id, api_key, label=style)
        if urls:
            if download(urls[0], out_path):
                print(f"  Saved: {out_path}")
            else:
                print(f"  Download failed for {style}")

    print(f"\nBackgrounds saved to {ASSETS_DIR}")


if __name__ == "__main__":
    main()
