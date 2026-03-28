#!/usr/bin/env python3
"""Remove backgrounds from images using Kie.ai remix mode."""

import argparse
import base64
import json
import mimetypes
import os
import random
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path


API_BASE = "https://api.kie.ai/api/v1"
UPLOAD_BASE = "https://kieai.redpandaai.co"
CREATE_TASK_URL = f"{API_BASE}/jobs/createTask"
RECORD_INFO_URL = f"{API_BASE}/jobs/recordInfo"
UPLOAD_URL = f"{UPLOAD_BASE}/api/file-base64-upload"

MODEL_ID = "nano-banana-2"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def get_api_key():
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


def api_request(url, data=None, api_key=None):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if data:
        req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method="POST")
    else:
        req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"API error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def upload_local_file(file_path, api_key):
    """Upload a local image to Kie.ai and return the download URL."""
    import subprocess
    import tempfile

    path = Path(file_path)
    if not path.exists():
        print(f"  Error: File not found: {path}", file=sys.stderr)
        return None

    mime_type = mimetypes.guess_type(str(path))[0] or "image/png"
    raw_b64 = base64.b64encode(path.read_bytes()).decode()
    data_url = f"data:{mime_type};base64,{raw_b64}"

    payload = json.dumps({
        "base64Data": data_url,
        "uploadPath": "rmbg/source",
        "fileName": path.name,
    })

    print(f"  Uploading {path.name}...")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        tmp.write(payload)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            [
                "curl", "-sS", "-X", "POST", UPLOAD_URL,
                "-H", f"Authorization: Bearer {api_key}",
                "-H", "Content-Type: application/json",
                "-d", f"@{tmp_path}",
            ],
            capture_output=True, text=True, timeout=120,
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
        else:
            print(f"  Upload failed: {resp}", file=sys.stderr)
            return None
    except (json.JSONDecodeError, KeyError) as e:
        print(f"  Upload parse error: {e}\n  Response: {result.stdout[:200]}", file=sys.stderr)
        return None


def create_task(prompt, api_key, image_url, aspect_ratio="auto", resolution="2K"):
    payload = {
        "model": MODEL_ID,
        "input": {
            "prompt": prompt,
            "image_input": [image_url],
            "aspect_ratio": aspect_ratio,
            "google_search": False,
            "resolution": resolution,
            "output_format": "png",
        },
    }

    print(f"  Creating background removal task...")
    resp = api_request(CREATE_TASK_URL, data=payload, api_key=api_key)
    if resp.get("code") != 200:
        print(f"  Error creating task: {resp}", file=sys.stderr)
        return None
    task_id = resp["data"]["taskId"]
    print(f"  Task ID: {task_id}")
    return task_id


def poll_task(task_id, api_key, max_wait=300, interval=5):
    url = f"{RECORD_INFO_URL}?taskId={task_id}"
    start = time.time()
    state_labels = {
        "waiting": "Waiting",
        "queuing": "In queue",
        "generating": "Generating",
    }
    while time.time() - start < max_wait:
        resp = api_request(url, api_key=api_key)
        data = resp.get("data", {})
        state = data.get("state", "")
        if state == "success":
            result_json_str = data.get("resultJson", "{}")
            if isinstance(result_json_str, str):
                result_json = json.loads(result_json_str)
            else:
                result_json = result_json_str
            urls = result_json.get("resultUrls", [])
            cost_time = data.get("costTime", 0)
            print(f"  Done! ({cost_time}s)")
            return urls
        elif state == "fail":
            fail_msg = data.get("failMsg", "Unknown error")
            print(f"  Generation failed: {fail_msg}", file=sys.stderr)
            return None
        else:
            elapsed = int(time.time() - start)
            label = state_labels.get(state, state or "Processing")
            print(f"  {label}... ({elapsed}s)    ", end="\r")
            time.sleep(interval)
    print(f"\n  Timed out after {max_wait}s", file=sys.stderr)
    return None


def download_image(url, output_path):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "image/*,*/*",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            Path(output_path).write_bytes(resp.read())
        print(f"  Saved: {output_path}")
    except urllib.error.HTTPError as e:
        print(f"  Direct download failed ({e.code}), trying curl...")
        import subprocess
        result = subprocess.run(
            ["curl", "-sL", "-o", str(output_path), url],
            capture_output=True, text=True
        )
        if result.returncode == 0 and Path(output_path).exists() and Path(output_path).stat().st_size > 0:
            print(f"  Saved: {output_path}")
        else:
            print(f"  Download failed. URL (expires in 24h): {url}", file=sys.stderr)


def find_images(source: Path) -> list[Path]:
    """Find all supported image files in a file or folder."""
    if source.is_file():
        if source.suffix.lower() in SUPPORTED_EXTENSIONS:
            return [source]
        else:
            print(f"Error: {source.name} is not a supported format ({', '.join(SUPPORTED_EXTENSIONS)})")
            return []
    images = []
    for f in sorted(source.iterdir()):
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
            images.append(f)
    return images


def main():
    parser = argparse.ArgumentParser(description="Remove backgrounds from images via Kie.ai")
    parser.add_argument("source", help="Image file or folder containing images")
    parser.add_argument("--output", default=None, help="Output folder (default: ~/images/nobg/)")
    parser.add_argument("--resolution", default="2K", choices=["1K", "2K", "4K"],
                        help="Output resolution (default: 2K)")
    parser.add_argument("--prompt", default=None,
                        help="Custom prompt (default: auto-generated background removal prompt)")

    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    if not source.exists():
        print(f"Error: {source} does not exist")
        sys.exit(1)

    images = find_images(source)
    if not images:
        print(f"No supported images found in {source}")
        sys.exit(1)

    output = Path(args.output).expanduser().resolve() if args.output else Path.home() / "images" / "nobg"
    output.mkdir(parents=True, exist_ok=True)

    api_key = get_api_key()

    default_prompt = (
        "Remove the background completely. Isolate the subject with a clean, transparent background. "
        "Preserve every detail of the subject - likeness, hair, clothing, colors, lighting, edges. "
        "Clean crisp cutout with no artifacts, no halo, no remnants of the original background. "
        "The subject should look exactly the same, just on a transparent/blank background."
    )
    prompt = args.prompt or default_prompt

    est_cost = len(images) * (0.12 if args.resolution == "4K" else 0.09)

    print(f"{'=' * 50}")
    print(f"Images: {len(images)}")
    print(f"Resolution: {args.resolution}")
    print(f"Estimated cost: ${est_cost:.2f}")
    print(f"Output: {output}")
    print(f"{'=' * 50}")

    success_count = 0

    for img_path in images:
        print(f"\n--- Processing: {img_path.name} ---")

        image_url = upload_local_file(img_path, api_key)
        if not image_url:
            print(f"  Skipping {img_path.name} - upload failed")
            continue

        task_id = create_task(
            prompt=prompt,
            api_key=api_key,
            image_url=image_url,
            aspect_ratio="auto",
            resolution=args.resolution,
        )
        if not task_id:
            print(f"  Failed to create task for {img_path.name}")
            continue

        urls = poll_task(task_id, api_key)
        if not urls:
            print(f"  Failed to process {img_path.name}")
            continue

        for j, url in enumerate(urls):
            suffix = f"_{j + 1}" if len(urls) > 1 else ""
            filename = f"{img_path.stem}_nobg{suffix}.png"
            download_image(url, output / filename)
            success_count += 1

    print(f"\n{'=' * 50}")
    print(f"Done! Processed {success_count}/{len(images)} images.")
    print(f"Output: {output}")
    print(f"Total cost: ${est_cost:.2f}")


if __name__ == "__main__":
    main()
