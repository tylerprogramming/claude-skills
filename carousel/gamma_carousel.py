#!/usr/bin/env python3
"""Generate LinkedIn carousel PDFs using the Gamma API."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


API_BASE = "https://public-api.gamma.app/v1.0"
GENERATIONS_URL = f"{API_BASE}/generations"
THEMES_URL = f"{API_BASE}/themes"


def get_api_key():
    key = os.environ.get("GAMMA_API_KEY")
    if not key:
        env_file = Path.home() / ".claude" / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line.startswith("GAMMA_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not key:
        print("Error: GAMMA_API_KEY not found.", file=sys.stderr)
        print("Set it in ~/.claude/.env as GAMMA_API_KEY=your_key", file=sys.stderr)
        sys.exit(1)
    return key


def api_request(url, data=None, api_key=None, method=None):
    """Make API requests via curl to avoid Cloudflare blocks on urllib."""
    cmd = ["curl", "-sS", "-X", method or ("POST" if data else "GET"), url,
           "-H", f"X-API-KEY: {api_key}",
           "-H", "Content-Type: application/json"]

    if data:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            json.dump(data, tmp)
            tmp_path = tmp.name
        cmd.extend(["-d", f"@{tmp_path}"])
    else:
        tmp_path = None

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    finally:
        if tmp_path:
            os.unlink(tmp_path)

    if result.returncode != 0:
        print(f"curl error: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"Invalid JSON response: {result.stdout[:500]}", file=sys.stderr)
        sys.exit(1)


def list_themes(api_key):
    """List available workspace themes."""
    resp = api_request(THEMES_URL, api_key=api_key)
    themes = resp if isinstance(resp, list) else resp.get("themes", resp.get("data", []))
    print(f"Found {len(themes)} theme(s):")
    for t in themes:
        theme_id = t.get("id", "unknown")
        name = t.get("name", "Unnamed")
        print(f"  - {name} (ID: {theme_id})")
    return themes


def create_generation(api_key, input_text, theme_id=None, num_cards=6,
                      image_model="flux-1-pro", image_style=None,
                      tone=None, audience=None):
    """Create a carousel generation and return the generation ID."""
    payload = {
        "inputText": input_text,
        "textMode": "preserve",
        "format": "social",
        "numCards": num_cards,
        "cardSplit": "inputTextBreaks",
        "exportAs": "pdf",
        "cardOptions": {
            "dimensions": "4x5",
        },
        "textOptions": {
            "amount": "brief",
        },
        "imageOptions": {
            "source": "aiGenerated",
        },
    }

    if theme_id:
        payload["themeId"] = theme_id
    if tone:
        payload["textOptions"]["tone"] = tone
    if audience:
        payload["textOptions"]["audience"] = audience
    if image_style:
        payload["imageOptions"]["style"] = image_style

    print(f"Creating carousel generation...")
    print(f"  Slides: {num_cards}")
    print(f"  Dimensions: 4:5 (LinkedIn carousel)")
    print(f"  Image model: {image_model}")
    print(f"  Text mode: preserve (your text, styled by Gamma)")
    if theme_id:
        print(f"  Theme: {theme_id}")

    resp = api_request(GENERATIONS_URL, data=payload, api_key=api_key)
    gen_id = resp.get("id") or resp.get("generationId")
    if not gen_id:
        print(f"Error: No generation ID returned: {resp}", file=sys.stderr)
        sys.exit(1)

    print(f"  Generation ID: {gen_id}")
    return gen_id


def poll_generation(api_key, generation_id, max_wait=300, interval=5):
    """Poll until generation completes. Returns the final response."""
    url = f"{GENERATIONS_URL}/{generation_id}"
    start = time.time()
    print(f"Waiting for generation to complete...")

    while time.time() - start < max_wait:
        resp = api_request(url, api_key=api_key)
        status = resp.get("status", "")

        if status == "completed":
            print(f"  Generation complete!")
            return resp
        elif status == "failed":
            error = resp.get("error", resp.get("failureReason", "Unknown error"))
            print(f"  Generation failed: {error}", file=sys.stderr)
            sys.exit(1)
        else:
            elapsed = int(time.time() - start)
            print(f"  {status or 'Processing'}... ({elapsed}s)    ", end="\r")
            time.sleep(interval)

    print(f"\n  Timed out after {max_wait}s", file=sys.stderr)
    sys.exit(1)


def download_file(url, output_path):
    """Download a file from a URL via curl."""
    result = subprocess.run(
        ["curl", "-sL", "-o", str(output_path), url],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode == 0 and Path(output_path).exists() and Path(output_path).stat().st_size > 0:
        print(f"  Saved: {output_path}")
    else:
        print(f"  Download failed. URL: {url}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Generate LinkedIn carousel PDF via Gamma API")
    parser.add_argument("input_file", help="Markdown file with slide content (separated by \\n---\\n)")
    parser.add_argument("--theme-id", default=None, help="Gamma theme ID for branding")
    parser.add_argument("--num-cards", type=int, default=6, help="Number of slides (default: 6)")
    parser.add_argument("--image-model", default="flux-1-pro",
                        choices=["dalle-3", "flux-1-pro", "flux-1-schnell"],
                        help="AI image model (default: flux-1-pro)")
    parser.add_argument("--image-style", default=None, help="Image style description")
    parser.add_argument("--tone", default=None, help="Writing tone")
    parser.add_argument("--audience", default=None, help="Target audience")
    parser.add_argument("--output", default=None, help="Output PDF path")
    parser.add_argument("--list-themes", action="store_true", help="List available themes and exit")

    args = parser.parse_args()

    api_key = get_api_key()

    if args.list_themes:
        list_themes(api_key)
        return

    input_path = Path(args.input_file).expanduser().resolve()
    if not input_path.exists():
        print(f"Error: {input_path} does not exist")
        sys.exit(1)

    input_text = input_path.read_text().strip()
    if not input_text:
        print(f"Error: {input_path} is empty")
        sys.exit(1)

    # Count slides from --- separators
    slide_count = input_text.count("\n---\n") + 1
    num_cards = args.num_cards or slide_count

    print(f"{'=' * 50}")
    print(f"Input: {input_path}")
    print(f"Slides detected: {slide_count}")
    print(f"Cards requested: {num_cards}")
    print(f"{'=' * 50}")

    # Create generation
    gen_id = create_generation(
        api_key=api_key,
        input_text=input_text,
        theme_id=args.theme_id,
        num_cards=num_cards,
        image_model=args.image_model,
        image_style=args.image_style,
        tone=args.tone,
        audience=args.audience,
    )

    # Poll for completion
    result = poll_generation(api_key, gen_id)

    # Extract URLs
    gamma_url = result.get("gammaUrl", "")
    export_url = result.get("exportUrl", "")
    credits_used = result.get("credits", {})

    print(f"\n{'=' * 50}")
    if gamma_url:
        print(f"Gamma URL: {gamma_url}")
    if credits_used:
        used = credits_used.get("used", "?")
        remaining = credits_used.get("remaining", "?")
        print(f"Credits: {used} used, {remaining} remaining")

    # Download PDF
    if export_url:
        if args.output:
            output_path = Path(args.output).expanduser().resolve()
        else:
            output_dir = input_path.parent
            output_path = output_dir / f"{input_path.stem}_carousel.pdf"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"\nDownloading PDF...")
        download_file(export_url, output_path)
    else:
        print("Warning: No export URL returned. Check the Gamma URL to view your carousel.")

    print(f"{'=' * 50}")
    print(f"Done!")


if __name__ == "__main__":
    main()
