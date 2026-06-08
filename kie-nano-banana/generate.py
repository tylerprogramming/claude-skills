#!/usr/bin/env python3
"""Nano Banana (Google) image generation via Kie.ai — all 3 variants.

  nano-banana      -> google/nano-banana (t2i) / google/nano-banana-edit (edit)
  nano-banana-2    -> nano-banana-2 (t2i + edit via image_input, up to 14 refs, 1K/2K/4K)
  nano-banana-pro  -> nano-banana-pro (t2i + edit via image_input, up to 8 refs, 1K/2K/4K)
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_kie"))
import kie_client as kie  # noqa: E402

RATIOS_V1 = ["1:1", "9:16", "16:9", "3:4", "4:3", "3:2", "2:3", "5:4", "4:5", "21:9", "auto"]
RATIOS_V2 = RATIOS_V1 + ["1:4", "1:8", "4:1", "8:1"]
RATIOS_PRO = ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9", "auto"]


def safe_ratio(r, allowed):
    return r if r in allowed else ("16:9" if "16:9" in allowed else allowed[0])


def b_v1(prompt, imgs, a):
    fmt = "jpeg" if a.format == "jpg" else a.format  # v1 uses 'jpeg'
    inp = {"prompt": prompt[:5000], "output_format": fmt,
           "aspect_ratio": safe_ratio(a.aspect_ratio, RATIOS_V1)}
    if imgs:
        inp["image_urls"] = imgs[:10]
    return inp


def b_v2(prompt, imgs, a):
    inp = {"prompt": prompt[:20000],
           "aspect_ratio": safe_ratio(a.aspect_ratio, RATIOS_V2),
           "resolution": a.resolution if a.resolution in ["1K", "2K", "4K"] else "2K",
           "output_format": "png" if a.format == "png" else "jpg"}
    if imgs:
        inp["image_input"] = imgs[:14]
    return inp


def b_pro(prompt, imgs, a):
    inp = {"prompt": prompt[:10000],
           "aspect_ratio": safe_ratio(a.aspect_ratio, RATIOS_PRO),
           "resolution": a.resolution if a.resolution in ["1K", "2K", "4K"] else "2K",
           "output_format": "jpg" if a.format == "jpg" else "png"}
    if imgs:
        inp["image_input"] = imgs[:8]
    return inp


MODELS = {
    "nano-banana":     {"build": b_v1,  "max_imgs": 10,
                        "id_t2i": "google/nano-banana", "id_edit": "google/nano-banana-edit"},
    "nano-banana-2":   {"build": b_v2,  "max_imgs": 14, "id": "nano-banana-2"},
    "nano-banana-pro": {"build": b_pro, "max_imgs": 8,  "id": "nano-banana-pro"},
}
DEFAULT_MODEL = "nano-banana-pro"


def main():
    p = argparse.ArgumentParser(description="Nano Banana image via Kie.ai")
    p.add_argument("prompt", nargs="+")
    p.add_argument("--model", default=DEFAULT_MODEL, choices=list(MODELS))
    p.add_argument("--image", action="append", default=[],
                   help="Reference/edit image(s) URL/path. Enables edit/remix mode.")
    p.add_argument("--aspect-ratio", default="16:9")
    p.add_argument("--resolution", default="2K", help="1K|2K|4K (nano-banana-2 / pro)")
    p.add_argument("--format", default="png", choices=["png", "jpg"])
    p.add_argument("--count", type=int, default=3)
    p.add_argument("--slug", default=None)
    p.add_argument("--output-dir", default=None)
    a = p.parse_args()

    model = MODELS[a.model]
    prompt = " ".join(a.prompt)
    api_key = kie.get_api_key()

    imgs = kie.resolve_media(a.image, api_key, max_items=model["max_imgs"],
                             upload_path="nanobanana/inputs") if a.image else []

    payload = model["build"](prompt, imgs, a)

    # Resolve which model id to send (v1 has separate t2i vs edit ids).
    if "id" in model:
        model_id = model["id"]
    else:
        model_id = model["id_edit"] if imgs else model["id_t2i"]

    out_dir = Path(a.output_dir) if a.output_dir else Path.home() / "images" / "nano-banana"
    today = datetime.now().strftime("%Y-%m-%d")
    slug = a.slug or prompt[:40].lower().replace(" ", "-").rstrip("-")
    out_dir = out_dir / f"{today}-{slug}"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_ext = "png" if payload.get("output_format", "png").startswith("png") else "jpg"

    print("=" * 54)
    print(f"Nano Banana — {model_id}")
    print(f"Mode: {'edit/remix' if imgs else 'text-to-image'}   Variants: {a.count}")
    print(f"Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    print(f"Input: {json.dumps({k: v for k, v in payload.items() if k != 'prompt'})}")
    print(f"Output: {out_dir}")
    print("=" * 54)

    stamp = datetime.now().strftime("%H%M%S")
    all_urls = []
    for n in range(a.count):
        print(f"\n--- Image {n + 1} of {a.count} ---")
        task_id = kie.create_task(model_id, payload, api_key)
        urls = kie.poll_task(task_id, api_key, max_wait=300, label="Painting")
        all_urls.extend(urls)
        for j, url in enumerate(urls):
            suffix = f"_{j + 1}" if len(urls) > 1 else ""
            variant = f"_{n + 1}" if a.count > 1 else ""
            kie.download_file(url, out_dir / f"nanobanana_{stamp}{variant}{suffix}.{out_ext}")

    (out_dir / "metadata.json").write_text(json.dumps({
        "model": model_id, "prompt": prompt, "input": payload,
        "result_urls": all_urls, "generated_at": datetime.now().isoformat(),
    }, indent=2))
    print(f"\nGenerated {len(all_urls)} image(s) -> {out_dir}")


if __name__ == "__main__":
    main()
