#!/usr/bin/env python3
"""
Instagram carousel generator using Kie.ai Nano Banana Pro.
Generates rich visual slides with logos, icons, and visual elements.

Usage: python3 instagram_kie.py <slides.json> <output_dir>
"""

import sys
import json
import os
import time
import urllib.request
import urllib.error
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

API_BASE = "https://api.kie.ai/api/v1"
CREATE_TASK_URL = f"{API_BASE}/jobs/createTask"
RECORD_INFO_URL = f"{API_BASE}/jobs/recordInfo"


# ── Design constants embedded in every prompt ────────────────────────────────
STYLE_BASE = """Instagram carousel slide. Exact specs:
- Background: warm cream/off-white #F5F0E8
- Font: clean bold sans-serif (Inter Bold or Arial Bold style)
- Near-black text: #1C1C1C
- Accent/highlight color: terra cotta burnt orange #C4713A
- 4:5 portrait aspect ratio (1080x1350)
- Minimal flat design, NO shadows, NO gradients, NO borders
- Heavy whitespace, editorial magazine aesthetic
- Text is left-aligned with ~72px left margin
"""

CHROME = """Fixed chrome elements:
- Top-left corner: small gray text "{counter}" (e.g. "1/6")
- Top-right corner: decorative 5x5 grid of tiny light gray dots (#D4CEC8)
- Bottom-left: bold text "{brand}" in terra cotta #C4713A
- Bottom-right: small gray text "{handle}"
"""


def get_api_key():
    key = os.environ.get("KIE_API_KEY")
    if not key:
        env_file = Path.home() / ".claude" / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("KIE_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        print("Error: KIE_API_KEY not found in ~/.claude/.env", file=sys.stderr)
        sys.exit(1)
    return key


def api_post(url, payload, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"  API error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


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
            "aspect_ratio": "4:5",
            "resolution": "1K",
            "output_format": "png",
        },
    }
    resp = api_post(CREATE_TASK_URL, payload, api_key)
    if resp.get("code") != 200:
        print(f"  Task creation failed: {resp}", file=sys.stderr)
        sys.exit(1)
    return resp["data"]["taskId"]


def poll_task(task_id, api_key, max_wait=300):
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
            print(f"  Done ({elapsed}s)")
            return urls
        elif state == "fail":
            print(f"  Generation failed: {data.get('failMsg', 'unknown')}", file=sys.stderr)
            sys.exit(1)
        else:
            elapsed = int(time.time() - start)
            print(f"  {state or 'waiting'}... ({elapsed}s)", end="\r")
            time.sleep(5)
    print(f"\n  Timed out after {max_wait}s", file=sys.stderr)
    sys.exit(1)


def download_image(url, output_path):
    import subprocess
    result = subprocess.run(
        ["curl", "-sL", "-o", str(output_path), url],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0 or not Path(output_path).exists():
        print(f"  Download failed for {output_path}", file=sys.stderr)
        return False
    print(f"  Saved: {Path(output_path).name}")
    return True


# ── Prompt builders per slide type ───────────────────────────────────────────

def chrome_block(slide_num, total, brand, handle):
    return CHROME.format(counter=f"{slide_num}/{total}", brand=brand, handle=handle)


def headline_block(lines, accent_words):
    """Describe a multi-line headline with per-word accent coloring."""
    accent_set = {w.upper().strip(".,!?:") for w in accent_words}
    desc_lines = []
    for line in lines:
        colored = []
        for word in line.split():
            clean = word.upper().strip(".,!?:")
            if clean in accent_set:
                colored.append(f'"{word}" in terra cotta #C4713A')
            else:
                colored.append(f'"{word}" in near-black #1C1C1C')
        desc_lines.append("  - " + " + ".join(colored))
    return "HEADLINE (very large bold text, ~100-120px, left-aligned):\n" + "\n".join(desc_lines)


def bullets_block(bullets):
    items = "\n".join(f'  • "{b}"' for b in bullets)
    return f"BULLET LIST (bold terra cotta dot • then regular near-black text, ~44px):\n{items}"


def prompt_cover(slide, data, num, total):
    visual = slide.get("visual_hint", "")
    subtitle = slide.get("subtitle", "")

    visual_section = ""
    if visual:
        visual_section = f"\nVISUAL ELEMENT (lower half of slide): {visual}"
    else:
        # Infer from topic
        topic = data.get("topic", "").lower()
        if "youtube" in topic:
            visual_section = "\nVISUAL ELEMENT (centered in lower half): large YouTube logo - red rectangle with white play triangle, cleanly rendered, ~200px"
        elif "claude" in topic or "skill" in topic:
            visual_section = "\nVISUAL ELEMENT (lower half): clean terminal window showing a slash command like \"/yt-search\" with output text, dark background, monospace font"
        elif "instagram" in topic or "linkedin" in topic:
            visual_section = "\nVISUAL ELEMENT (lower half): 2x4 grid of recognizable social platform logos (Instagram, LinkedIn, TikTok, YouTube, X/Twitter, Pinterest, Threads, Facebook)"
        else:
            visual_section = ""

    subtitle_section = ""
    if subtitle:
        subtitle_section = f'\nThin horizontal gray line (#D4CEC8) spanning full width below headline.\nSUBTITLE (smaller gray text ~42px, below the rule): "{subtitle}"'

    return f"""{STYLE_BASE}
{chrome_block(num, total, data['brand_text'], data['handle'])}
{headline_block(slide['headline_lines'], slide.get('accent_words', []))}
{subtitle_section}
{visual_section}

The headline takes up the upper 45% of the slide. The visual fills the remaining space.
Generous padding on all sides. Extremely clean and minimal.
"""


def prompt_pain(slide, data, num, total):
    subtitle_section = ""
    if slide.get("subtitle"):
        subtitle_section = f'\nSUBTITLE below headline (gray ~42px): "{slide["subtitle"]}"'

    return f"""{STYLE_BASE}
{chrome_block(num, total, data['brand_text'], data['handle'])}
{headline_block(slide['headline_lines'], slide.get('accent_words', []))}
{subtitle_section}

{bullets_block(slide.get('bullets', []))}

Layout: headline at top (~35% of height), bullets below with breathing room between each.
Each bullet: small filled terra cotta circle (8px) then regular near-black text.
Lots of vertical whitespace between bullets (~20px gap).
"""


def prompt_solution(slide, data, num, total):
    subtitle_section = ""
    if slide.get("subtitle"):
        subtitle_section = f'\nSUBTITLE (gray text ~42px below headline): "{slide["subtitle"]}"'

    bullets_section = ""
    if slide.get("bullets"):
        bullets_section = "\n" + bullets_block(slide["bullets"])

    return f"""{STYLE_BASE}
{chrome_block(num, total, data['brand_text'], data['handle'])}
{headline_block(slide['headline_lines'], slide.get('accent_words', []))}
{subtitle_section}
{bullets_section}

Very large impactful headline. The key concept word is in terra cotta. Heavy use of whitespace.
"""


def prompt_cta(slide, data, num, total):
    summary = slide.get("summary_lines", [])
    cta_action = slide.get("cta_action", "Comment")
    cta_word = slide.get("cta_word", "")
    cta_subtext = slide.get("cta_subtext", "")

    summary_lines = "\n".join(f'  "{line}"' for line in summary)

    return f"""{STYLE_BASE}
{chrome_block(num, total, data['brand_text'], data['handle'])}

SUMMARY LINES (top of slide, small gray text ~36px):
{summary_lines}

TERRA COTTA HORIZONTAL DIVIDER LINE (2px, full width, color #C4713A) below summary lines.

BELOW DIVIDER:
- Medium bold black text ~52px: "{cta_action}"
- GIANT bold terra cotta text ~155px (the CTA word, very dominant): "{cta_word}"
- Regular near-black text ~36px below the giant word: "{cta_subtext}"

The giant "{cta_word}" in terra cotta #C4713A is the visual anchor of the slide.
It should be massive, filling most of the horizontal width.
"""


PROMPT_BUILDERS = {
    "cover":    prompt_cover,
    "pain":     prompt_pain,
    "solution": prompt_solution,
    "how":      prompt_pain,     # same layout
    "results":  prompt_pain,     # same layout
    "cta":      prompt_cta,
}


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 3:
        print("Usage: instagram_kie.py <slides.json> <output_dir>")
        sys.exit(1)

    json_path = sys.argv[1]
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(json_path) as f:
        data = json.load(f)

    api_key = get_api_key()
    total = len(data["slides"])
    slide_paths = []

    for i, slide in enumerate(data["slides"]):
        slide_num = i + 1
        slide_type = slide.get("type", "cover")
        builder = PROMPT_BUILDERS.get(slide_type, prompt_cover)
        prompt = builder(slide, data, slide_num, total)

        print(f"\n── Slide {slide_num}/{total} ({slide_type}) ──")
        task_id = submit_task(prompt, api_key)
        print(f"  Task: {task_id}")
        urls = poll_task(task_id, api_key)

        out_path = output_dir / f"slide_{slide_num:02d}.png"
        if urls:
            download_image(urls[0], out_path)
            slide_paths.append(out_path)
        else:
            print(f"  No URLs returned for slide {slide_num}", file=sys.stderr)

    # Assemble PDF
    if PIL_AVAILABLE and slide_paths:
        try:
            images = [Image.open(p).convert("RGB") for p in slide_paths]
            pdf_path = output_dir / "carousel.pdf"
            images[0].save(
                str(pdf_path), "PDF",
                resolution=150,
                save_all=True,
                append_images=images[1:],
            )
            print(f"\n  PDF: {pdf_path}")
        except Exception as e:
            print(f"\n  PDF assembly skipped: {e}")
    else:
        print("\n  Pillow not available - skipping PDF assembly")
        print("  Run: pip install Pillow && python3 -c \"from PIL import Image; ...\" to assemble PDF manually")

    print(f"\n  {len(slide_paths)}/{total} slides generated to {output_dir}")
    est_cost = len(slide_paths) * 0.09
    print(f"  Estimated cost: ~${est_cost:.2f}")


if __name__ == "__main__":
    main()
