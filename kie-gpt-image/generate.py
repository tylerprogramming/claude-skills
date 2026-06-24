#!/usr/bin/env python3
"""GPT Image 2 (OpenAI) image generation via Kie.ai.

  gpt-image-2-text-to-image    -> t2i
  gpt-image-2-image-to-image   -> edit/remix (input_urls, up to 16 images)

Routes through the shared _kie/kie_client.py unified jobs API. Any --image
switches to image-to-image mode (local files auto-upload).
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_kie"))
import kie_client as kie  # noqa: E402

# GPT Image 2 supports a wide ratio set; 5:4 and 4:5 are 1K-only.
RATIOS = ["auto", "1:1", "3:2", "2:3", "4:3", "3:4", "5:4", "4:5",
          "16:9", "9:16", "2:1", "1:2", "3:1", "1:3", "21:9", "9:21"]
ONE_K_ONLY_RATIOS = {"5:4", "4:5"}
RESOLUTIONS = ["1K", "2K", "4K"]

ID_T2I = "gpt-image-2-text-to-image"
ID_I2I = "gpt-image-2-image-to-image"


def safe_ratio(r):
    return r if r in RATIOS else "auto"


def resolve_resolution(ratio, res):
    """Apply Kie.ai's GPT Image 2 resolution constraints."""
    res = res if res in RESOLUTIONS else "2K"
    if ratio in ONE_K_ONLY_RATIOS and res != "1K":
        print(f"  Note: {ratio} only supports 1K — forcing 1K.")
        return "1K"
    if ratio == "1:1" and res == "4K":
        print("  Note: 1:1 can't go 4K — using 2K.")
        return "2K"
    if ratio == "auto" and res != "1K":
        print("  Note: auto aspect ratio is limited to 1K — using 1K.")
        return "1K"
    return res


def main():
    p = argparse.ArgumentParser(description="GPT Image 2 image via Kie.ai")
    p.add_argument("prompt", nargs="+")
    p.add_argument("--image", action="append", default=[],
                   help="Reference/edit image(s) URL/path. Enables image-to-image. Up to 16.")
    p.add_argument("--aspect-ratio", default="auto", help=f"One of: {', '.join(RATIOS)}")
    p.add_argument("--resolution", default="2K", help="1K|2K|4K")
    p.add_argument("--count", type=int, default=3)
    p.add_argument("--slug", default=None)
    p.add_argument("--output-dir", default=None)
    a = p.parse_args()

    prompt = " ".join(a.prompt)[:20000]
    api_key = kie.get_api_key()

    imgs = kie.resolve_media(a.image, api_key, max_items=16,
                             upload_path="gptimage/inputs") if a.image else []

    ratio = safe_ratio(a.aspect_ratio)
    resolution = resolve_resolution(ratio, a.resolution)

    payload = {"prompt": prompt, "aspect_ratio": ratio, "resolution": resolution}
    if imgs:
        payload["input_urls"] = imgs[:16]
        model_id = ID_I2I
    else:
        model_id = ID_T2I

    out_dir = Path(a.output_dir) if a.output_dir else Path.home() / "images" / "gpt-image"
    today = datetime.now().strftime("%Y-%m-%d")
    slug = a.slug or prompt[:40].lower().replace(" ", "-").rstrip("-")
    out_dir = out_dir / f"{today}-{slug}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 54)
    print(f"GPT Image 2 — {model_id}")
    print(f"Mode: {'image-to-image' if imgs else 'text-to-image'}   Variants: {a.count}")
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
            kie.download_file(url, out_dir / f"gptimage_{stamp}{variant}{suffix}.png")

    (out_dir / "metadata.json").write_text(json.dumps({
        "model": model_id, "prompt": prompt, "input": payload,
        "result_urls": all_urls, "generated_at": datetime.now().isoformat(),
    }, indent=2))
    print(f"\nGenerated {len(all_urls)} image(s) -> {out_dir}")


if __name__ == "__main__":
    main()
