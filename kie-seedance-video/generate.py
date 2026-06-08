#!/usr/bin/env python3
"""Seedance (ByteDance) video generation via Kie.ai — text-to-video + image-to-video."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_kie"))
import kie_client as kie  # noqa: E402


def nearest(value, choices):
    """Return the element of `choices` closest to numeric `value`."""
    return min(choices, key=lambda c: abs(int(c) - int(value)))


# Each model: id, mode (t2v/i2v/both), and a builder(prompt, imgs, a) -> input dict.
def b_seedance2(prompt, imgs, a, fast=False):
    res_choices = ["480p", "720p"] if fast else ["480p", "720p", "1080p"]
    res = a.resolution if a.resolution in res_choices else "720p"
    inp = {
        "prompt": prompt,
        "resolution": res,
        "aspect_ratio": a.aspect_ratio or "16:9",
        "duration": max(4, min(15, int(a.duration or 5))),
        "generate_audio": a.audio,
    }
    if imgs:
        inp["first_frame_url"] = imgs[0]
    if a.last_frame:
        inp["last_frame_url"] = kie.resolve_media([a.last_frame], a._key, 1)[0]
    return inp


def b_15pro(prompt, imgs, a):
    inp = {
        "prompt": prompt,
        "aspect_ratio": a.aspect_ratio or "16:9",
        "duration": nearest(a.duration or 4, ["4", "8", "12"]),
        "resolution": a.resolution if a.resolution in ["480p", "720p", "1080p"] else "720p",
        "generate_audio": a.audio,
    }
    if imgs:
        inp["input_urls"] = imgs[:2]
    return inp


def b_v1_t2v(prompt, imgs, a):
    return {
        "prompt": prompt,
        "aspect_ratio": a.aspect_ratio or "16:9",
        "resolution": a.resolution if a.resolution in ["480p", "720p", "1080p"] else "720p",
        "duration": nearest(a.duration or 5, ["5", "10"]),
        "camera_fixed": a.camera_fixed,
    }


def b_v1_i2v(prompt, imgs, a):
    inp = {
        "prompt": prompt,
        "image_url": imgs[0],
        "resolution": a.resolution if a.resolution in ["480p", "720p", "1080p"] else "720p",
        "duration": nearest(a.duration or 5, ["5", "10"]),
        "camera_fixed": a.camera_fixed,
    }
    if a.last_frame:
        inp["end_image_url"] = kie.resolve_media([a.last_frame], a._key, 1)[0]
    return inp


MODELS = {
    "seedance-2":       {"id": "bytedance/seedance-2",                "mode": "both", "build": lambda p, i, a: b_seedance2(p, i, a, fast=False)},
    "seedance-2-fast":  {"id": "bytedance/seedance-2-fast",           "mode": "both", "build": lambda p, i, a: b_seedance2(p, i, a, fast=True)},
    "1.5-pro":          {"id": "bytedance/seedance-1.5-pro",          "mode": "both", "build": b_15pro},
    "1-pro-t2v":        {"id": "bytedance/v1-pro-text-to-video",      "mode": "t2v",  "build": b_v1_t2v},
    "1-pro-i2v":        {"id": "bytedance/v1-pro-image-to-video",     "mode": "i2v",  "build": b_v1_i2v},
    "1-pro-fast-i2v":   {"id": "bytedance/v1-pro-fast-image-to-video","mode": "i2v",  "build": b_v1_i2v},
    "1-lite-t2v":       {"id": "bytedance/v1-lite-text-to-video",     "mode": "t2v",  "build": b_v1_t2v},
    "1-lite-i2v":       {"id": "bytedance/v1-lite-image-to-video",    "mode": "i2v",  "build": b_v1_i2v},
}
DEFAULT_MODEL = "seedance-2"


def main():
    p = argparse.ArgumentParser(description="Seedance video via Kie.ai")
    p.add_argument("prompt", nargs="+")
    p.add_argument("--model", default=DEFAULT_MODEL, choices=list(MODELS))
    p.add_argument("--image", action="append", default=[],
                   help="Start-frame image URL/path for image-to-video (repeatable; seedance-2 uses first)")
    p.add_argument("--last-frame", default=None, help="Optional last-frame image (URL/path)")
    p.add_argument("--duration", type=int, default=5, help="Seconds (coerced to model's allowed set)")
    p.add_argument("--resolution", default="720p", help="480p|720p|1080p")
    p.add_argument("--aspect-ratio", default="16:9")
    p.add_argument("--audio", dest="audio", action="store_true", default=False,
                   help="Generate audio (seedance-2 / 1.5-pro)")
    p.add_argument("--camera-fixed", action="store_true", default=False)
    p.add_argument("--count", type=int, default=1, help="Number of clips")
    p.add_argument("--slug", default=None)
    p.add_argument("--output-dir", default=None)
    a = p.parse_args()

    model = MODELS[a.model]
    prompt = " ".join(a.prompt)
    api_key = kie.get_api_key()
    a._key = api_key

    if model["mode"] == "i2v" and not a.image:
        print(f"Error: model '{a.model}' is image-to-video — pass --image <url/path>.", file=sys.stderr)
        sys.exit(1)

    imgs = kie.resolve_media(a.image, api_key, upload_path="seedance/inputs") if a.image else []
    if model["mode"] == "i2v" and not imgs:
        print("Error: could not resolve input image.", file=sys.stderr)
        sys.exit(1)

    payload = model["build"](prompt, imgs, a)

    out_dir = Path(a.output_dir) if a.output_dir else Path.home() / "videos" / "seedance"
    today = datetime.now().strftime("%Y-%m-%d")
    slug = a.slug or prompt[:40].lower().replace(" ", "-").rstrip("-")
    out_dir = out_dir / f"{today}-{slug}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 54)
    print(f"Seedance — {model['id']}")
    mode = "image-to-video" if imgs else "text-to-video"
    print(f"Mode: {mode}   Clips: {a.count}")
    print(f"Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    print(f"Input: {json.dumps({k: v for k, v in payload.items() if k != 'prompt'})}")
    print(f"Output: {out_dir}")
    print("=" * 54)

    stamp = datetime.now().strftime("%H%M%S")
    all_urls = []
    for n in range(a.count):
        print(f"\n--- Clip {n + 1} of {a.count} ---")
        task_id = kie.create_task(model["id"], payload, api_key)
        urls = kie.poll_task(task_id, api_key, max_wait=900, label="Rendering")
        all_urls.extend(urls)
        for j, url in enumerate(urls):
            suffix = f"_{j + 1}" if len(urls) > 1 else ""
            variant = f"_{n + 1}" if a.count > 1 else ""
            kie.download_file(url, out_dir / f"seedance_{stamp}{variant}{suffix}.mp4")

    (out_dir / "metadata.json").write_text(json.dumps({
        "model": model["id"], "prompt": prompt, "input": payload,
        "result_urls": all_urls, "generated_at": datetime.now().isoformat(),
    }, indent=2))
    print(f"\nGenerated {len(all_urls)} clip(s) -> {out_dir}")


if __name__ == "__main__":
    main()
