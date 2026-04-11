#!/usr/bin/env python3
"""
flash-video renderer — PIL text overlay on Kie.ai background → ffmpeg → 7s MP4

Usage: python3 flash_video.py <content.json> <output_dir>

Layout types:
  "statement" — raw centered text wall, big and dense, authentic TikTok feel
  "list"      — bold header banner + numbered/bulleted items, structured info card

content.json fields (all optional except type + lines/items):
{
  "type": "statement",           // "statement" or "list"
  "background": "dark",          // "dark" or "cream"
  "slug": "my-video",            // used in output filename

  // statement type:
  "lines": ["Line one", "line TWO here", "another line"],
  "accent_words": ["TWO"],
  "cta": "skool.com/the-ai-agency",
  "handle": "@tylerai_dev",

  // list type:
  "header": "5 Claude Code skills",
  "subheader": "I use every single week:",
  "items": [
    "/yt-search — YouTube research in 60s",
    "/instagram-writer — 6 slides, one command",
    "/shorts — 5 short scripts from research",
    "/content — LinkedIn, X, IG posts",
    "/yt — full video package with script"
  ],
  "accent_words": ["yt-search", "instagram-writer"],
  "cta": "skool.com/the-ai-agency",
  "handle": "@tylerai_dev"
}
"""

import sys
import json
import subprocess
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "Pillow", "--quiet"], check=True)
    from PIL import Image, ImageDraw, ImageFont

W, H   = 1080, 1920
PAD    = 80
ASSETS      = Path(__file__).parent / "assets"
BACKGROUNDS = Path(__file__).parent / "backgrounds"

PALETTES = {
    "cream": {
        "text":        (28, 28, 28),
        "accent":      (196, 113, 58),
        "cta":         (120, 115, 108),
        "handle":      (155, 155, 155),
        "rule":        (210, 207, 202),
        "header_bg":   (196, 113, 58),
        "header_text": (245, 240, 232),
        "item_dot":    (196, 113, 58),
        "dim":         (80, 75, 70),
    },
    "dark": {
        "text":        (245, 240, 232),
        "accent":      (196, 113, 58),
        "cta":         (160, 155, 148),
        "handle":      (100, 95, 90),
        "rule":        (60, 58, 54),
        "header_bg":   (196, 113, 58),
        "header_text": (245, 240, 232),
        "item_dot":    (196, 113, 58),
        "dim":         (160, 155, 148),
    },
}


def load_font(size, bold=False):
    candidates_bold = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Black.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    candidates_reg = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in (candidates_bold if bold else candidates_reg):
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def tw(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]

def th(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]

def cx(draw, text, font):
    return (W - tw(draw, text, font)) // 2


def render_mixed_centered(draw, line, accent_set, y, font, palette):
    """Render one line centered with per-word accent coloring."""
    words = line.split()
    if not words:
        return
    space_w = tw(draw, " ", font)
    total_w = sum(tw(draw, w, font) for w in words) + space_w * max(len(words) - 1, 0)
    max_w = W - PAD * 2
    render_font = font
    if total_w > max_w:
        scale = max_w / total_w
        render_font = load_font(max(int(font.size * scale), 24), bold=True)
        space_w = tw(draw, " ", render_font)
        total_w = sum(tw(draw, w, render_font) for w in words) + space_w * max(len(words) - 1, 0)
    cursor = (W - total_w) // 2
    for word in words:
        clean = word.upper().strip(".,!?:/—-")
        color = palette["accent"] if clean in accent_set else palette["text"]
        draw.text((cursor, y), word, font=render_font, fill=color)
        cursor += tw(draw, word, render_font) + space_w


def load_bg(bg_name):
    bg_path = BACKGROUNDS / f"{bg_name}.png"
    if bg_path.exists():
        return Image.open(str(bg_path)).convert("RGB").resize((W, H), Image.LANCZOS)
    fill = (245, 240, 232) if bg_name == "cream" else (28, 28, 28)
    return Image.new("RGB", (W, H), fill)


# ── Layout: statement ─────────────────────────────────────────────────────────
def render_statement(img, data):
    """Raw centered text wall - big, dense, authentic feel."""
    draw    = ImageDraw.Draw(img)
    palette = PALETTES.get(data.get("background", "dark"), PALETTES["dark"])

    lines       = data.get("lines", [])
    accent_set  = {w.upper().strip(".,!?:/—-") for w in data.get("accent_words", [])}
    cta         = data.get("cta", "")
    handle      = data.get("handle", "@tylerai_dev")

    f_main   = load_font(82, bold=True)
    f_label  = load_font(40)
    f_url    = load_font(44, bold=True)
    f_bio    = load_font(38)
    f_handle = load_font(36)

    line_gap = 18
    lh = th(draw, "Ag", f_main) + line_gap

    # CTA block height: "Join my Skool community:" + url + "Link in bio"
    cta_label = "Join my Skool community:"
    cta_url   = data.get("cta", "skool.com/the-ai-agency")
    cta_h = th(draw, cta_label, f_label) + 10 + th(draw, cta_url, f_url) + 10 + th(draw, "Link in bio", f_bio)

    block_h = lh * len(lines) + 70 + cta_h
    y = (H - block_h) // 2

    # Main lines
    for line in lines:
        render_mixed_centered(draw, line, accent_set, y, f_main, palette)
        y += lh

    # CTA block
    y += 70
    draw.rectangle([PAD, y, W - PAD, y + 2], fill=palette["rule"])
    y += 22
    x = cx(draw, cta_label, f_label)
    draw.text((x, y), cta_label, font=f_label, fill=palette["dim"])
    y += th(draw, cta_label, f_label) + 10
    x = cx(draw, cta_url, f_url)
    draw.text((x, y), cta_url, font=f_url, fill=palette["accent"])
    y += th(draw, cta_url, f_url) + 10
    x = cx(draw, "Link in bio", f_bio)
    draw.text((x, y), "Link in bio", font=f_bio, fill=palette["dim"])

    # Handle bottom-right
    hw = tw(draw, handle, f_handle)
    draw.text((W - PAD - hw, H - PAD - th(draw, handle, f_handle)), handle,
              font=f_handle, fill=palette["handle"])

    return img


# ── Layout: list ──────────────────────────────────────────────────────────────
def render_list(img, data):
    """Bold header banner + numbered items + CTA. Structured info card."""
    draw    = ImageDraw.Draw(img)
    palette = PALETTES.get(data.get("background", "dark"), PALETTES["dark"])

    header    = data.get("header", "")
    subheader = data.get("subheader", "")
    items     = data.get("items", [])
    accent_set = {w.upper().strip(".,!?:/—-") for w in data.get("accent_words", [])}
    cta       = data.get("cta", "")
    handle    = data.get("handle", "@tylerai_dev")

    f_header    = load_font(76, bold=True)
    f_subheader = load_font(48)
    f_item      = load_font(58, bold=True)
    f_label     = load_font(40)
    f_url       = load_font(44, bold=True)
    f_bio       = load_font(38)
    f_handle    = load_font(36)

    stat   = data.get("stat", "")
    f_stat = load_font(54, bold=True)

    header_pad_v = 32
    item_gap     = 28
    text_x       = PAD + 60

    # ── Pre-measure all heights to center the content block ───────────────────
    lh_item  = th(draw, "Ag", f_item)
    lh_stat  = th(draw, "Ag", f_stat) if stat else 0
    header_h = th(draw, "Ag", f_header) + header_pad_v * 2
    if subheader:
        header_h += th(draw, "Ag", f_subheader) + 14

    cta_label = "Join my Skool community:"
    cta_url   = data.get("cta", "skool.com/the-ai-agency")
    f_label_m = load_font(38)
    f_url_m   = load_font(42, bold=True)
    f_bio_m   = load_font(36)
    cta_h = 2 + 20 + th(draw, cta_label, f_label_m) + 8 + th(draw, cta_url, f_url_m) + 8 + th(draw, "Link in bio", f_bio_m)
    handle_h  = th(draw, handle, f_handle) + 24

    items_h   = (lh_item + item_gap) * len(items) - item_gap
    stat_h    = (20 + lh_stat) if stat else 0
    content_h = header_h + 40 + items_h + stat_h + 40 + cta_h + 24 + handle_h

    y_start = max(PAD, (H - content_h) // 2)

    # ── Header banner ─────────────────────────────────────────────────────────
    y = y_start
    banner_text_w = max(tw(draw, header, f_header),
                        tw(draw, subheader, f_subheader) if subheader else 0)
    banner_pad_h = 48
    banner_w = min(banner_text_w + banner_pad_h * 2, W)
    banner_x = (W - banner_w) // 2
    draw.rectangle([banner_x, y, banner_x + banner_w, y + header_h], fill=palette["header_bg"])
    y += header_pad_v
    x = cx(draw, header, f_header)
    draw.text((x, y), header, font=f_header, fill=palette["header_text"])
    y += th(draw, "Ag", f_header) + 14
    if subheader:
        x = cx(draw, subheader, f_subheader)
        draw.text((x, y), subheader, font=f_subheader, fill=palette["header_text"])
        y += th(draw, "Ag", f_subheader)
    y += header_pad_v + 40

    # ── Items ─────────────────────────────────────────────────────────────────
    lh_item = th(draw, "Ag", f_item)
    for i, item in enumerate(items):
        num_text = f"{i + 1}."
        draw.text((PAD, y), num_text, font=f_item, fill=palette["item_dot"])

        words = item.split()
        space_w = tw(draw, " ", f_item)
        max_item_w = W - text_x - PAD
        render_font = f_item
        line_w = sum(tw(draw, w, f_item) for w in words) + space_w * max(len(words)-1, 0)
        if line_w > max_item_w:
            scale = max_item_w / line_w
            render_font = load_font(max(int(f_item.size * scale), 28), bold=True)
            space_w = tw(draw, " ", render_font)

        cursor = text_x
        for word in words:
            clean = word.upper().strip(".,!?:/—-")
            color = palette["accent"] if clean in accent_set else palette["text"]
            draw.text((cursor, y), word, font=render_font, fill=color)
            cursor += tw(draw, word, render_font) + space_w
        y += lh_item + item_gap

    # ── Stat line ─────────────────────────────────────────────────────────────
    if stat:
        y += 20
        stat_accent = {w.upper().strip(".,!?:/—-") for w in data.get("accent_words", [])}
        render_mixed_centered(draw, stat, stat_accent, y, f_stat, palette)
        y += th(draw, "Ag", f_stat) + 10

    # ── CTA block — flows naturally after content ──────────────────────────────
    y += 40
    draw.rectangle([PAD, y, W - PAD, y + 2], fill=palette["rule"])
    y += 20
    x = cx(draw, cta_label, f_label_m)
    draw.text((x, y), cta_label, font=f_label_m, fill=palette["dim"])
    y += th(draw, cta_label, f_label_m) + 8
    x = cx(draw, cta_url, f_url_m)
    draw.text((x, y), cta_url, font=f_url_m, fill=palette["accent"])
    y += th(draw, cta_url, f_url_m) + 8
    x = cx(draw, "Link in bio", f_bio_m)
    draw.text((x, y), "Link in bio", font=f_bio_m, fill=palette["dim"])
    y += th(draw, "Link in bio", f_bio_m) + 24

    # Handle bottom-right
    hw = tw(draw, handle, f_handle)
    draw.text((W - PAD - hw, y), handle, font=f_handle, fill=palette["handle"])

    return img


# ── Main ──────────────────────────────────────────────────────────────────────
LAYOUTS = {
    "statement": render_statement,
    "list":      render_list,
}


def render_frame(data, output_path):
    bg_name = data.get("background", "dark")
    img = load_bg(bg_name)
    layout = LAYOUTS.get(data.get("type", "statement"), render_statement)
    img = layout(img, data)
    img.save(str(output_path), "PNG")
    return output_path


def render_video(frame_path, output_path, duration=7, fade_start=6, fade_duration=1):
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", str(frame_path),
        "-t", str(duration),
        "-vf", f"fade=t=out:st={fade_start}:d={fade_duration}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def main():
    if len(sys.argv) < 3:
        print("Usage: flash_video.py <content.json> <output_dir>")
        sys.exit(1)

    json_path  = sys.argv[1]
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(json_path) as f:
        data = json.load(f)

    bg   = data.get("background", "dark")
    slug = data.get("slug", "flash")
    kind = data.get("type", "statement")

    frame_path = output_dir / f"{slug}-{kind}-{bg}-frame.png"
    video_path = output_dir / f"{slug}-{kind}-{bg}.mp4"

    print(f"  Rendering [{kind}] on [{bg}]...")
    render_frame(data, frame_path)
    print(f"  Frame: {frame_path.name}")

    print(f"  Encoding video...")
    if render_video(frame_path, video_path):
        print(f"  Video: {video_path.name}")
    else:
        print(f"  ffmpeg failed", file=sys.stderr)
        sys.exit(1)

    print(f"\n  Done: {video_path}")


if __name__ == "__main__":
    main()
