#!/usr/bin/env python3
"""Kling (Kuaishou) video generation via Kie.ai — text-to-video + image-to-video."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_kie"))
import kie_client as kie  # noqa: E402


def nearest(value, choices):
    return min(choices, key=lambda c: abs(int(c) - int(value)))


def b_26_t2v(prompt, imgs, a):
    return {
        "prompt": prompt[:1000],
        "sound": a.audio,
        "aspect_ratio": a.aspect_ratio if a.aspect_ratio in ["1:1", "16:9", "9:16"] else "16:9",
        "duration": nearest(a.duration or 5, ["5", "10"]),
    }


def b_26_i2v(prompt, imgs, a):
    return {
        "prompt": prompt[:1000],
        "image_urls": imgs[:1],
        "sound": a.audio,
        "duration": nearest(a.duration or 5, ["5", "10"]),
    }


def b_30(prompt, imgs, a):
    inp = {
        "prompt": prompt,
        "sound": a.audio,
        "duration": nearest(a.duration or 5, [str(n) for n in range(3, 16)]),
        "aspect_ratio": a.aspect_ratio if a.aspect_ratio in ["16:9", "9:16", "1:1"] else "16:9",
        "mode": a.mode if a.mode in ["std", "pro", "4K"] else "pro",
    }
    if imgs:
        inp["image_urls"] = imgs
    return inp


def b_21_master_t2v(prompt, imgs, a):
    inp = {
        "prompt": prompt[:5000],
        "duration": nearest(a.duration or 5, ["5", "10"]),
        "aspect_ratio": a.aspect_ratio if a.aspect_ratio in ["16:9", "9:16", "1:1"] else "16:9",
        "cfg_scale": a.cfg_scale,
    }
    if a.negative_prompt:
        inp["negative_prompt"] = a.negative_prompt[:500]
    return inp


def b_21_pro_i2v(prompt, imgs, a):
    inp = {
        "prompt": prompt[:5000],
        "image_url": imgs[0],
        "duration": nearest(a.duration or 5, ["5", "10"]),
        "cfg_scale": a.cfg_scale,
    }
    if a.negative_prompt:
        inp["negative_prompt"] = a.negative_prompt[:500]
    if a.last_frame:
        inp["tail_image_url"] = kie.resolve_media([a.last_frame], a._key, 1)[0]
    return inp


MODELS = {
    "2.6-t2v":        {"id": "kling-2.6/text-to-video",          "mode": "t2v", "build": b_26_t2v},
    "2.6-i2v":        {"id": "kling-2.6/image-to-video",         "mode": "i2v", "build": b_26_i2v},
    "3.0":            {"id": "kling-3.0/video",                  "mode": "both","build": b_30},
    "2.1-master-t2v": {"id": "kling/v2-1-master-text-to-video",  "mode": "t2v", "build": b_21_master_t2v},
    "2.1-pro-i2v":    {"id": "kling/v2-1-pro",                   "mode": "i2v", "build": b_21_pro_i2v},
}
DEFAULT_MODEL = "2.6-t2v"


def main():
    p = argparse.ArgumentParser(description="Kling video via Kie.ai")
    p.add_argument("prompt", nargs="+")
    p.add_argument("--model", default=DEFAULT_MODEL, choices=list(MODELS))
    p.add_argument("--image", action="append", default=[], help="Input image(s) for image-to-video")
    p.add_argument("--last-frame", default=None, help="Tail/last frame (2.1-pro-i2v)")
    p.add_argument("--duration", type=int, default=5)
    p.add_argument("--aspect-ratio", default="16:9")
    p.add_argument("--mode", default="pro", help="kling-3.0 quality: std|pro|4K")
    p.add_argument("--audio", action="store_true", default=False, help="Native sound (sound=true)")
    p.add_argument("--cfg-scale", type=float, default=0.5, help="Prompt adherence 0-1 (v2.1)")
    p.add_argument("--negative-prompt", default=None)
    p.add_argument("--count", type=int, default=1)
    p.add_argument("--slug", default=None)
    p.add_argument("--output-dir", default=None)
    a = p.parse_args()

    model = MODELS[a.model]
    prompt = " ".join(a.prompt)
    api_key = kie.get_api_key()
    a._key = api_key

    if model["mode"] == "i2v" and not a.image:
        print(f"Error: model '{a.model}' is image-to-video — pass --image.", file=sys.stderr)
        sys.exit(1)
    imgs = kie.resolve_media(a.image, api_key, upload_path="kling/inputs") if a.image else []
    if model["mode"] == "i2v" and not imgs:
        print("Error: could not resolve input image.", file=sys.stderr)
        sys.exit(1)

    payload = model["build"](prompt, imgs, a)

    out_dir = Path(a.output_dir) if a.output_dir else Path.home() / "videos" / "kling"
    today = datetime.now().strftime("%Y-%m-%d")
    slug = a.slug or prompt[:40].lower().replace(" ", "-").rstrip("-")
    out_dir = out_dir / f"{today}-{slug}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 54)
    print(f"Kling — {model['id']}")
    print(f"Mode: {'image-to-video' if imgs else 'text-to-video'}   Clips: {a.count}")
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
            kie.download_file(url, out_dir / f"kling_{stamp}{variant}{suffix}.mp4")

    (out_dir / "metadata.json").write_text(json.dumps({
        "model": model["id"], "prompt": prompt, "input": payload,
        "result_urls": all_urls, "generated_at": datetime.now().isoformat(),
    }, indent=2))
    print(f"\nGenerated {len(all_urls)} clip(s) -> {out_dir}")


if __name__ == "__main__":
    main()
