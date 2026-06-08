#!/usr/bin/env python3
"""ByteDance Seedream image generation via Kie.ai — text-to-image + image edit.

(The ByteDance image model is "Seedream"; this skill is named kie-seedance-image
to match the Seedance media family.)
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_kie"))
import kie_client as kie  # noqa: E402

ASPECTS = ["1:1", "4:3", "3:4", "16:9", "9:16", "2:3", "3:2", "21:9"]

MODELS = {
    "4.5":      {"id": "seedream/4.5-text-to-image",   "edit": False},
    "4.5-edit": {"id": "seedream/4.5-edit",            "edit": True},
    "5-lite":   {"id": "seedream/5-lite-text-to-image","edit": False},
}
DEFAULT_MODEL = "4.5"


def main():
    p = argparse.ArgumentParser(description="Seedream image via Kie.ai")
    p.add_argument("prompt", nargs="+")
    p.add_argument("--model", default=DEFAULT_MODEL, choices=list(MODELS))
    p.add_argument("--image", action="append", default=[],
                   help="Input image(s) for edit mode (URL/path; up to 14). Forces seedream/4.5-edit.")
    p.add_argument("--aspect-ratio", default="16:9", choices=ASPECTS)
    p.add_argument("--quality", default="basic", choices=["basic", "high"],
                   help="basic = 2K, high = 4K")
    p.add_argument("--count", type=int, default=3)
    p.add_argument("--slug", default=None)
    p.add_argument("--output-dir", default=None)
    a = p.parse_args()

    # If images were given, switch to the edit model.
    model_key = "4.5-edit" if a.image and a.model not in ("4.5-edit",) else a.model
    model = MODELS[model_key]
    prompt = " ".join(a.prompt)
    api_key = kie.get_api_key()

    imgs = []
    if model["edit"]:
        imgs = kie.resolve_media(a.image, api_key, max_items=14, upload_path="seedream/inputs")
        if not imgs:
            print("Error: edit mode needs at least one --image.", file=sys.stderr)
            sys.exit(1)

    payload = {"prompt": prompt, "aspect_ratio": a.aspect_ratio, "quality": a.quality}
    if model["edit"]:
        payload["image_urls"] = imgs

    out_dir = Path(a.output_dir) if a.output_dir else Path.home() / "images" / "seedream"
    today = datetime.now().strftime("%Y-%m-%d")
    slug = a.slug or prompt[:40].lower().replace(" ", "-").rstrip("-")
    out_dir = out_dir / f"{today}-{slug}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 54)
    print(f"Seedream — {model['id']}")
    print(f"Mode: {'image edit' if model['edit'] else 'text-to-image'}   Variants: {a.count}")
    print(f"Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    print(f"Aspect: {a.aspect_ratio}   Quality: {a.quality} ({'2K' if a.quality == 'basic' else '4K'})")
    print(f"Output: {out_dir}")
    print("=" * 54)

    stamp = datetime.now().strftime("%H%M%S")
    all_urls = []
    for n in range(a.count):
        print(f"\n--- Image {n + 1} of {a.count} ---")
        task_id = kie.create_task(model["id"], payload, api_key)
        urls = kie.poll_task(task_id, api_key, max_wait=300, label="Painting")
        all_urls.extend(urls)
        for j, url in enumerate(urls):
            suffix = f"_{j + 1}" if len(urls) > 1 else ""
            variant = f"_{n + 1}" if a.count > 1 else ""
            kie.download_file(url, out_dir / f"seedream_{stamp}{variant}{suffix}.png")

    (out_dir / "metadata.json").write_text(json.dumps({
        "model": model["id"], "prompt": prompt, "input": payload,
        "result_urls": all_urls, "generated_at": datetime.now().isoformat(),
    }, indent=2))
    print(f"\nGenerated {len(all_urls)} image(s) -> {out_dir}")


if __name__ == "__main__":
    main()
