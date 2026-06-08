#!/usr/bin/env python3
"""Wan (Alibaba) video generation via Kie.ai — text-to-video + image-to-video."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_kie"))
import kie_client as kie  # noqa: E402


def nearest(value, choices):
    return min(choices, key=lambda c: abs(int(c) - int(value)))


def b_27_t2v(prompt, imgs, a):
    # NOTE: Wan 2.7 t2v uses `ratio`, not `aspect_ratio`.
    inp = {
        "prompt": prompt[:5000],
        "ratio": a.aspect_ratio if a.aspect_ratio in ["16:9", "9:16", "1:1", "4:3", "3:4"] else "16:9",
        "resolution": a.resolution if a.resolution in ["720p", "1080p"] else "1080p",
        "duration": max(2, min(15, int(a.duration or 5))),
        "prompt_extend": not a.no_prompt_extend,
        "watermark": a.watermark,
    }
    if a.negative_prompt:
        inp["negative_prompt"] = a.negative_prompt[:500]
    if a.audio_url:
        inp["audio_url"] = a.audio_url
    return inp


def b_27_i2v(prompt, imgs, a):
    inp = {
        "prompt": prompt[:5000],
        "resolution": a.resolution if a.resolution in ["720p", "1080p"] else "1080p",
        "duration": max(2, min(15, int(a.duration or 5))),
        "prompt_extend": not a.no_prompt_extend,
        "watermark": a.watermark,
    }
    if imgs:
        inp["first_frame_url"] = imgs[0]
    if a.last_frame:
        inp["last_frame_url"] = kie.resolve_media([a.last_frame], a._key, 1)[0]
    if a.negative_prompt:
        inp["negative_prompt"] = a.negative_prompt[:500]
    return inp


def b_26_i2v(prompt, imgs, a):
    return {
        "prompt": prompt[:5000],
        "image_urls": imgs[:1],
        "duration": nearest(a.duration or 5, ["5", "10", "15"]),
        "resolution": a.resolution if a.resolution in ["720p", "1080p"] else "1080p",
    }


def b_25_t2v(prompt, imgs, a):
    inp = {
        "prompt": prompt[:800],
        "duration": nearest(a.duration or 5, ["5", "10"]),
        "aspect_ratio": a.aspect_ratio if a.aspect_ratio in ["16:9", "9:16", "1:1"] else "16:9",
        "resolution": a.resolution if a.resolution in ["720p", "1080p"] else "720p",
    }
    if a.negative_prompt:
        inp["negative_prompt"] = a.negative_prompt[:500]
    return inp


MODELS = {
    "2.7-t2v": {"id": "wan/2-7-text-to-video",  "mode": "t2v", "build": b_27_t2v},
    "2.7-i2v": {"id": "wan/2-7-image-to-video", "mode": "i2v", "build": b_27_i2v},
    "2.6-i2v": {"id": "wan/2-6-image-to-video", "mode": "i2v", "build": b_26_i2v},
    "2.5-t2v": {"id": "wan/2-5-text-to-video",  "mode": "t2v", "build": b_25_t2v},
}
DEFAULT_MODEL = "2.7-t2v"


def main():
    p = argparse.ArgumentParser(description="Wan video via Kie.ai")
    p.add_argument("prompt", nargs="+")
    p.add_argument("--model", default=DEFAULT_MODEL, choices=list(MODELS))
    p.add_argument("--image", action="append", default=[], help="Input image(s) for image-to-video")
    p.add_argument("--last-frame", default=None, help="Last frame (2.7-i2v)")
    p.add_argument("--duration", type=int, default=5)
    p.add_argument("--resolution", default="1080p", help="720p|1080p")
    p.add_argument("--aspect-ratio", default="16:9")
    p.add_argument("--negative-prompt", default=None)
    p.add_argument("--audio-url", default=None, help="Drive with an audio track (2.7-t2v)")
    p.add_argument("--watermark", action="store_true", default=False)
    p.add_argument("--no-prompt-extend", action="store_true", default=False,
                   help="Disable Wan's automatic prompt expansion")
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
    imgs = kie.resolve_media(a.image, api_key, upload_path="wan/inputs") if a.image else []
    if model["mode"] == "i2v" and not imgs:
        print("Error: could not resolve input image.", file=sys.stderr)
        sys.exit(1)

    payload = model["build"](prompt, imgs, a)

    out_dir = Path(a.output_dir) if a.output_dir else Path.home() / "videos" / "wan"
    today = datetime.now().strftime("%Y-%m-%d")
    slug = a.slug or prompt[:40].lower().replace(" ", "-").rstrip("-")
    out_dir = out_dir / f"{today}-{slug}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 54)
    print(f"Wan — {model['id']}")
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
            kie.download_file(url, out_dir / f"wan_{stamp}{variant}{suffix}.mp4")

    (out_dir / "metadata.json").write_text(json.dumps({
        "model": model["id"], "prompt": prompt, "input": payload,
        "result_urls": all_urls, "generated_at": datetime.now().isoformat(),
    }, indent=2))
    print(f"\nGenerated {len(all_urls)} clip(s) -> {out_dir}")


if __name__ == "__main__":
    main()
