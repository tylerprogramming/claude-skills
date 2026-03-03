#!/usr/bin/env python3
"""Generate YouTube thumbnails using Kie.ai image generation APIs."""

import argparse
import base64
import json
import mimetypes
import os
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

MODELS = {
    "nano-banana-pro": {
        "id": "nano-banana-pro",
        "name": "Nano Banana Pro",
        "supports_image_input": True,
        "max_image_input": 8,
        "supports_google_search": False,
        "max_prompt": 20000,
        "aspect_ratios": ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9", "auto"],
        "resolutions": ["1K", "2K", "4K"],
        "formats": ["png", "jpg"],
    },
    "nano-banana-2": {
        "id": "nano-banana-2",
        "name": "Nano Banana 2",
        "supports_image_input": True,
        "max_image_input": 14,
        "supports_google_search": True,
        "max_prompt": 20000,
        "aspect_ratios": ["1:1", "1:4", "1:8", "2:3", "3:2", "3:4", "4:1", "4:3", "4:5", "5:4", "8:1", "9:16", "16:9", "21:9", "auto"],
        "resolutions": ["1K", "2K", "4K"],
        "formats": ["png", "jpg"],
    },
    "seedream": {
        "id": "seedream/4.5-text-to-image",
        "name": "Seedream 4.5",
        "supports_image_input": False,
        "max_image_input": 0,
        "supports_google_search": False,
        "max_prompt": 3000,
        "aspect_ratios": ["1:1", "2:3", "3:2", "3:4", "4:3", "9:16", "16:9", "21:9"],
        "resolutions": ["basic", "high"],
        "formats": ["png"],
    },
}

DEFAULT_MODEL = "nano-banana-pro"


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
        "uploadPath": "thumbnails/references",
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


def resolve_reference_images(refs, api_key, max_images=8):
    """Take a list of paths/URLs, upload local files, return list of URLs."""
    if not refs:
        return []

    urls = []
    for ref in refs:
        if ref.startswith("http://") or ref.startswith("https://"):
            urls.append(ref)
        else:
            path = Path(ref).expanduser()
            if path.is_dir():
                image_exts = {".jpg", ".jpeg", ".png", ".webp"}
                files = sorted(f for f in path.iterdir() if f.suffix.lower() in image_exts)
                if not files:
                    print(f"  No images found in {path}", file=sys.stderr)
                    continue
                print(f"  Found {len(files)} image(s) in {path}:")
                for f in files:
                    print(f"    - {f.name}")
                max_imgs = max_images or 8
                for f in files[:max_imgs]:
                    url = upload_local_file(f, api_key)
                    if url:
                        urls.append(url)
            elif path.is_file():
                url = upload_local_file(path, api_key)
                if url:
                    urls.append(url)
            else:
                print(f"  Warning: Not found: {ref}", file=sys.stderr)

    max_imgs = max_images or 8
    if len(urls) > max_imgs:
        print(f"  Warning: Trimming to {max_imgs} reference images (had {len(urls)})")
        urls = urls[:max_imgs]

    return urls


def create_task(prompt, api_key, model_key="nano-banana-pro", aspect_ratio="16:9",
                resolution="2K", output_format="png", image_urls=None, google_search=False):
    model_config = MODELS[model_key]
    model_id = model_config["id"]

    if model_key == "seedream":
        payload = {
            "model": model_id,
            "input": {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "quality": resolution,
            },
        }
    elif model_key == "nano-banana-2":
        payload = {
            "model": model_id,
            "input": {
                "prompt": prompt,
                "image_input": image_urls or [],
                "aspect_ratio": aspect_ratio,
                "google_search": google_search,
                "resolution": resolution,
                "output_format": output_format,
            },
        }
    else:
        payload = {
            "model": model_id,
            "input": {
                "prompt": prompt,
                "image_input": image_urls or [],
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "output_format": output_format,
            },
        }

    mode = "Remix" if image_urls else "Text-to-image"
    print(f"Creating task ({mode})...")
    print(f"  Model: {model_config['name']} ({model_id})")
    print(f"  Aspect ratio: {aspect_ratio}")
    if model_key == "seedream":
        print(f"  Quality: {resolution}")
    else:
        print(f"  Resolution: {resolution}")
        print(f"  Format: {output_format}")
    if image_urls:
        print(f"  Reference images: {len(image_urls)}")

    resp = api_request(CREATE_TASK_URL, data=payload, api_key=api_key)
    if resp.get("code") != 200:
        print(f"Error creating task: {resp}", file=sys.stderr)
        sys.exit(1)
    task_id = resp["data"]["taskId"]
    print(f"  Task ID: {task_id}")
    return task_id


def poll_task(task_id, api_key, max_wait=300, interval=5):
    url = f"{RECORD_INFO_URL}?taskId={task_id}"
    start = time.time()
    print(f"Waiting for generation to complete...")
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
            print(f"  Generation complete! ({cost_time}s)")
            return urls
        elif state == "fail":
            fail_msg = data.get("failMsg", "Unknown error")
            fail_code = data.get("failCode", "")
            print(f"  Generation failed [{fail_code}]: {fail_msg}", file=sys.stderr)
            sys.exit(1)
        else:
            elapsed = int(time.time() - start)
            label = state_labels.get(state, state or "Processing")
            print(f"  {label}... ({elapsed}s)    ", end="\r")
            time.sleep(interval)
    print(f"\n  Timed out after {max_wait}s", file=sys.stderr)
    sys.exit(1)


def download_image(url, output_path):
    print(f"  Downloading to {output_path}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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


def get_cost_estimate(model_key, resolution, count):
    if model_key == "seedream":
        return count * 0.025
    else:
        return count * (0.12 if resolution == "4K" else 0.09)


def main():
    all_aspect_ratios = sorted(set(
        ar for m in MODELS.values() for ar in m["aspect_ratios"]
    ))

    parser = argparse.ArgumentParser(description="Generate YouTube thumbnails via Kie.ai")
    parser.add_argument("prompt", nargs="+", help="Thumbnail description/prompt")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL,
                        choices=list(MODELS.keys()),
                        help=f"Image model (default: {DEFAULT_MODEL})")
    parser.add_argument("--count", type=int, default=3, help="Number of variants (default: 3)")
    parser.add_argument("--aspect-ratio", type=str, default="16:9",
                        choices=all_aspect_ratios,
                        help="Aspect ratio (default: 16:9)")
    parser.add_argument("--resolution", type=str, default="2K",
                        help="Resolution: 1K/2K/4K for Nano Banana Pro, basic/high for Seedream (default: 2K)")
    parser.add_argument("--format", type=str, default="png", choices=["png", "jpg"],
                        help="Output format (default: png, Nano Banana Pro only)")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory")
    parser.add_argument("--reference-images", nargs="*", default=None,
                        help="Reference image URLs/paths for remix (up to 8 for Pro, 14 for Banana 2)")
    parser.add_argument("--google-search", action="store_true", default=False,
                        help="Enable Google Search grounding (Nano Banana 2 only)")
    parser.add_argument("--slug", type=str, default=None, help="Slug for organizing output")
    args = parser.parse_args()

    model_key = args.model
    model_config = MODELS[model_key]

    # Validate model-specific constraints
    if args.reference_images and not model_config["supports_image_input"]:
        print(f"Error: {model_config['name']} does not support reference images. Use nano-banana-pro or nano-banana-2.",
              file=sys.stderr)
        sys.exit(1)

    if args.google_search and not model_config["supports_google_search"]:
        print(f"Error: Google Search grounding is only supported by Nano Banana 2.", file=sys.stderr)
        sys.exit(1)

    if args.aspect_ratio not in model_config["aspect_ratios"]:
        print(f"Error: {model_config['name']} does not support aspect ratio '{args.aspect_ratio}'.",
              file=sys.stderr)
        print(f"  Supported: {', '.join(model_config['aspect_ratios'])}", file=sys.stderr)
        sys.exit(1)

    # Map resolution for Seedream if user passes 1K/2K/4K
    resolution = args.resolution
    if model_key == "seedream":
        res_map = {"1K": "basic", "2K": "basic", "4K": "high"}
        if resolution in res_map:
            resolution = res_map[resolution]
        if resolution not in ["basic", "high"]:
            print(f"Error: Seedream quality must be 'basic' (2K) or 'high' (4K). Got: {resolution}",
                  file=sys.stderr)
            sys.exit(1)

    api_key = get_api_key()
    prompt = " ".join(args.prompt)

    # Truncate prompt if needed
    if len(prompt) > model_config["max_prompt"]:
        print(f"Warning: Prompt truncated to {model_config['max_prompt']} chars for {model_config['name']}")
        prompt = prompt[:model_config["max_prompt"]]

    # Resolve reference images
    max_refs = model_config["max_image_input"]
    resolved_refs = resolve_reference_images(args.reference_images, api_key, max_images=max_refs)
    if resolved_refs and len(resolved_refs) > max_refs:
        print(f"Error: Maximum {max_refs} reference images allowed for {model_config['name']}.", file=sys.stderr)
        sys.exit(1)

    # Set up output directory
    output_dir = Path(args.output_dir) if args.output_dir else Path.home() / "youtube" / "thumbnails"
    today = datetime.now().strftime("%Y-%m-%d")
    if args.slug:
        output_dir = output_dir / f"{today}-{args.slug}"
    else:
        slug = prompt[:40].lower().replace(" ", "-").rstrip("-")
        output_dir = output_dir / f"{today}-{slug}"

    output_dir.mkdir(parents=True, exist_ok=True)

    existing = list(output_dir.glob("thumbnail_*"))
    start_index = len(existing)

    mode = "Remix (image + text)" if resolved_refs else "Text-to-image"
    est_cost = get_cost_estimate(model_key, resolution, args.count)

    print(f"{'=' * 50}")
    print(f"Model: {model_config['name']}")
    print(f"Mode: {mode}")
    print(f"Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    print(f"Variants: {args.count}")
    print(f"Aspect ratio: {args.aspect_ratio}")
    if model_key == "seedream":
        print(f"Quality: {resolution} ({'2K' if resolution == 'basic' else '4K'})")
    else:
        print(f"Resolution: {resolution}")
        print(f"Format: {args.format}")
    if resolved_refs:
        for img in resolved_refs:
            print(f"Reference: {img}")
    if args.google_search:
        print(f"Google Search: enabled")
    print(f"Estimated cost: ${est_cost:.2f}")
    print(f"Output: {output_dir}")
    print(f"{'=' * 50}")

    # Determine output extension
    out_ext = args.format if model_key != "seedream" else "png"

    # Generate thumbnails
    all_urls = []
    for i in range(args.count):
        idx = start_index + i + 1
        print(f"\n--- Thumbnail {i + 1} of {args.count} ---")
        task_id = create_task(
            prompt=prompt,
            api_key=api_key,
            model_key=model_key,
            aspect_ratio=args.aspect_ratio,
            resolution=resolution,
            output_format=args.format,
            image_urls=resolved_refs,
            google_search=args.google_search,
        )
        urls = poll_task(task_id, api_key)
        all_urls.extend(urls)

        for j, url in enumerate(urls):
            filename = f"thumbnail_{idx}_{j + 1}.{out_ext}" if len(urls) > 1 else f"thumbnail_{idx}.{out_ext}"
            download_image(url, output_dir / filename)

    # Save metadata
    meta_path = output_dir / "metadata.json"
    if meta_path.exists():
        existing_meta = json.loads(meta_path.read_text())
        if "generations" not in existing_meta:
            existing_meta = {"generations": [existing_meta]}
    else:
        existing_meta = {"generations": []}

    existing_meta["generations"].append({
        "prompt": prompt,
        "mode": mode,
        "model": model_config["id"],
        "model_name": model_config["name"],
        "count": args.count,
        "aspect_ratio": args.aspect_ratio,
        "resolution": resolution,
        "format": out_ext,
        "reference_images": resolved_refs,
        "generated_at": datetime.now().isoformat(),
        "image_urls": all_urls,
    })
    meta_path.write_text(json.dumps(existing_meta, indent=2))

    print(f"\n{'=' * 50}")
    print(f"Generated {len(all_urls)} thumbnail(s) with {model_config['name']}")
    print(f"Saved to: {output_dir}")
    print(f"Metadata: {meta_path}")
    print(f"Total cost: ${est_cost:.2f}")


if __name__ == "__main__":
    main()
