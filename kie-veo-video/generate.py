#!/usr/bin/env python3
"""Google Veo 3 / 3.1 video generation via Kie.ai.

Veo uses Kie.ai's DEDICATED endpoint (not the unified /jobs API):
  POST https://api.kie.ai/api/v1/veo/generate         (flat camelCase body)
  GET  https://api.kie.ai/api/v1/veo/record-info?taskId=...
  GET  https://api.kie.ai/api/v1/veo/get-1080p-video?taskId=...   (hi-res fetch)
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_kie"))
import kie_client as kie  # noqa: E402

GEN_URL = f"{kie.API_BASE}/veo/generate"
INFO_URL = f"{kie.API_BASE}/veo/record-info"
HIRES_URL = f"{kie.API_BASE}/veo/get-1080p-video"

MODELS = {
    "veo3": "veo3",            # Veo 3.1 Quality
    "veo3-fast": "veo3_fast",  # default
    "veo3-lite": "veo3_lite",
}
DEFAULT_MODEL = "veo3-fast"


def veo_request(url, data=None, api_key=None, method="GET"):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers,
                                 method="POST" if data is not None else method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode() if e.fp else ""
        print(f"Veo API error {e.code}: {detail}", file=sys.stderr)
        sys.exit(1)


def poll_veo(task_id, api_key, want_1080=False, max_wait=900, interval=10):
    start = time.time()
    print("Waiting for Veo to render...")
    while time.time() - start < max_wait:
        resp = veo_request(f"{INFO_URL}?taskId={task_id}", api_key=api_key)
        data = resp.get("data", {})
        flag = data.get("successFlag")
        if flag in (1, "1"):
            response = data.get("response", {}) or {}
            urls = response.get("resultUrls") or response.get("result_urls") or []
            if want_1080:
                hi = veo_request(f"{HIRES_URL}?taskId={task_id}", api_key=api_key)
                hi_urls = (hi.get("data", {}) or {}).get("resultUrls") or []
                if hi_urls:
                    urls = hi_urls
            print(f"  Done! ({int(time.time() - start)}s)")
            return urls
        if flag in (2, 3, "2", "3"):
            print(f"  Veo generation failed: {data.get('errorMessage', data)}", file=sys.stderr)
            sys.exit(1)
        print(f"  Generating... ({int(time.time() - start)}s)    ", end="\r")
        time.sleep(interval)
    print(f"\n  Timed out after {max_wait}s — taskId: {task_id}", file=sys.stderr)
    sys.exit(1)


def main():
    p = argparse.ArgumentParser(description="Google Veo 3.1 video via Kie.ai")
    p.add_argument("prompt", nargs="+")
    p.add_argument("--model", default=DEFAULT_MODEL, choices=list(MODELS))
    p.add_argument("--image", action="append", default=[],
                   help="Image URL/path (1-3). 1 = image-to-video; 2 = first+last frames; 3 = reference")
    p.add_argument("--aspect-ratio", default="16:9", choices=["16:9", "9:16", "Auto"])
    p.add_argument("--resolution", default="720p", choices=["720p", "1080p", "4k"])
    p.add_argument("--duration", type=int, default=8, choices=[4, 6, 8])
    p.add_argument("--translate", action="store_true", default=False,
                   help="Enable prompt translation to English")
    p.add_argument("--count", type=int, default=1)
    p.add_argument("--slug", default=None)
    p.add_argument("--output-dir", default=None)
    a = p.parse_args()

    prompt = " ".join(a.prompt)
    api_key = kie.get_api_key()

    imgs = kie.resolve_media(a.image, api_key, max_items=3, upload_path="veo/inputs") if a.image else []

    body = {
        "prompt": prompt,
        "model": MODELS[a.model],
        "aspectRatio": a.aspect_ratio,
        "resolution": a.resolution,
        "duration": a.duration,
        "enableTranslation": a.translate,
    }
    if imgs:
        body["imageUrls"] = imgs

    out_dir = Path(a.output_dir) if a.output_dir else Path.home() / "videos" / "veo"
    today = datetime.now().strftime("%Y-%m-%d")
    slug = a.slug or prompt[:40].lower().replace(" ", "-").rstrip("-")
    out_dir = out_dir / f"{today}-{slug}"
    out_dir.mkdir(parents=True, exist_ok=True)

    mode = {0: "text-to-video", 1: "image-to-video",
            2: "first+last frames", 3: "reference-to-video"}.get(len(imgs), "video")
    print("=" * 54)
    print(f"Google Veo — {MODELS[a.model]}")
    print(f"Mode: {mode}   Clips: {a.count}")
    print(f"Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    print(f"Aspect: {a.aspect_ratio}  Resolution: {a.resolution}  Duration: {a.duration}s")
    print(f"Output: {out_dir}")
    print("=" * 54)

    stamp = datetime.now().strftime("%H%M%S")
    all_urls = []
    want_1080 = a.resolution in ("1080p", "4k")
    for n in range(a.count):
        print(f"\n--- Clip {n + 1} of {a.count} ---")
        resp = veo_request(GEN_URL, data=body, api_key=api_key)
        if resp.get("code") != 200:
            print(f"Error creating Veo task: {resp}", file=sys.stderr)
            sys.exit(1)
        task_id = resp["data"]["taskId"]
        print(f"  Task ID: {task_id}")
        urls = poll_veo(task_id, api_key, want_1080=want_1080)
        all_urls.extend(urls)
        for j, url in enumerate(urls):
            suffix = f"_{j + 1}" if len(urls) > 1 else ""
            variant = f"_{n + 1}" if a.count > 1 else ""
            kie.download_file(url, out_dir / f"veo_{stamp}{variant}{suffix}.mp4")

    (out_dir / "metadata.json").write_text(json.dumps({
        "model": MODELS[a.model], "prompt": prompt, "body": body,
        "result_urls": all_urls, "generated_at": datetime.now().isoformat(),
    }, indent=2))
    print(f"\nGenerated {len(all_urls)} clip(s) -> {out_dir}")


if __name__ == "__main__":
    main()
