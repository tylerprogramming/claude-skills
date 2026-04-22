#!/usr/bin/env python3
"""
Instagram carousel generator - @aiwithanushka inspired design.
Warm cream background, terra cotta accent, bold two-tone typography.
6-slide structure: Cover → Pain → Solution → How → Results → CTA

Usage: python3 instagram_writer.py <slides.json> <output_dir>
Optional: slides can include "image_path" field for composited image slides.
"""

import sys
import json
import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "Pillow", "--quiet"], check=True)
    from PIL import Image, ImageDraw, ImageFont

# ── Design system ─────────────────────────────────────────────────────────────
BG      = (245, 240, 232)   # Warm cream  #F5F0E8
BLACK   = (28, 28, 28)      # Near-black  #1C1C1C
ACCENT  = (196, 113, 58)    # Terra cotta #C4713A
GRAY    = (155, 155, 155)   # Subdued gray
LGRAY   = (210, 207, 202)   # Light warm gray for dots

W, H    = 1080, 1350        # 4:5 Instagram aspect ratio
PAD     = 72                # Outer margin


# ── Font loading ──────────────────────────────────────────────────────────────
def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates_bold = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Black.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    candidates_reg = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in (candidates_bold if bold else candidates_reg):
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


# ── Drawing helpers ───────────────────────────────────────────────────────────
def tw(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]

def th(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]

def cx(draw, text, font):
    """Return x position to center text horizontally."""
    return (W - tw(draw, text, font)) // 2


def draw_dots(draw, cx_pos, cy_pos, cols=5, rows=5, r=4, gap=13):
    """Decorative dotted grid."""
    total_w = cols * (2 * r + gap) - gap
    total_h = rows * (2 * r + gap) - gap
    x0 = cx_pos - total_w // 2
    y0 = cy_pos - total_h // 2
    for row in range(rows):
        for col in range(cols):
            x = x0 + col * (2 * r + gap) + r
            y = y0 + row * (2 * r + gap) + r
            draw.ellipse([x - r, y - r, x + r, y + r], fill=LGRAY)


def draw_counter(draw, num, total, font):
    text = f"{num}/{total}"
    draw.text((PAD, PAD + 4), text, font=font, fill=GRAY)


def draw_brand(draw, brand_text, handle, font_brand, font_handle):
    """Brand (terra cotta) bottom-left, handle (gray) bottom-right."""
    by = H - PAD - th(draw, brand_text, font_brand) - 4
    draw.text((PAD, by), brand_text, font=font_brand, fill=ACCENT)
    hw = tw(draw, handle, font_handle)
    hy = H - PAD - th(draw, handle, font_handle) - 4
    draw.text((W - PAD - hw, hy), handle, font=font_handle, fill=GRAY)


def render_line_mixed(draw, line, accent_set, x, y, font):
    """Render one line word-by-word with per-word accent coloring.
    Auto-scales down if the line would overflow the right margin."""
    words = line.split()
    space_w = tw(draw, " ", font)
    line_w = sum(tw(draw, w, font) for w in words) + space_w * max(len(words) - 1, 0)
    max_w = W - PAD - x

    render_font = font
    if line_w > max_w:
        scale = max_w / line_w
        new_size = max(int(font.size * scale), 24)
        render_font = load_font(new_size, bold=True)
        space_w = tw(draw, " ", render_font)

    cursor = x
    for word in words:
        clean = word.upper().strip(".,!?:")
        color = ACCENT if clean in accent_set else BLACK
        draw.text((cursor, y), word, font=render_font, fill=color)
        cursor += tw(draw, word, render_font) + space_w
    return cursor


def render_headline(draw, lines, accent_words, y_start, font, line_gap=14):
    """Render multi-line headline with accent words. Returns y after last line."""
    accent_set = {w.upper().strip(".,!?:") for w in accent_words}
    lh = th(draw, "Ag", font) + line_gap
    y = y_start
    for line in lines:
        render_line_mixed(draw, line, accent_set, PAD, y, font)
        y += lh
    return y


def render_bullets(draw, bullets, y_start, font, line_gap=22):
    """Render bullet list with terra cotta dots. Auto-scales long lines. Returns y after last bullet."""
    max_w = W - (PAD + 24) - PAD
    y = y_start
    for bullet in bullets:
        use_font = font
        if tw(draw, bullet, font) > max_w:
            scale = max_w / tw(draw, bullet, font)
            use_font = load_font(max(int(font.size * scale), 28), bold=False)
        dot_size = 10
        dot_y = y + (th(draw, "Ag", use_font) - dot_size) // 2 + 2
        draw.ellipse([PAD, dot_y, PAD + dot_size, dot_y + dot_size], fill=ACCENT)
        draw.text((PAD + 24, y), bullet, font=use_font, fill=BLACK)
        y += th(draw, "Ag", use_font) + line_gap
    return y


def draw_rule(draw, y, color=LGRAY, width=2):
    draw.rectangle([PAD, y, W - PAD, y + width], fill=color)


def add_rounded_corners(img, radius=24):
    """Return RGBA image with rounded corners."""
    img = img.convert("RGBA")
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
    img.putalpha(mask)
    return img


LOGO_DRAWERS = {}

# Assets directory — pre-generated logos saved here for reuse
ASSETS_DIR = Path(__file__).parent / "assets"


def _remove_white_bg(img_rgba, threshold=240):
    """Make near-white pixels transparent so logo blends onto cream bg."""
    import numpy as np
    data = np.array(img_rgba)
    r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
    white_mask = (r > threshold) & (g > threshold) & (b > threshold)
    data[:,:,3] = np.where(white_mask, 0, a)
    return Image.fromarray(data, "RGBA")


def draw_logo_from_asset(name, img, center_x, center_y, width=300):
    """Composite a saved logo asset (assets/logo-<name>.png) onto img.
    Falls back to PIL-drawn version if asset file not found."""
    asset_path = ASSETS_DIR / f"logo-{name}.png"
    if asset_path.exists():
        try:
            import numpy as np
            logo = Image.open(str(asset_path)).convert("RGBA")
            logo = _remove_white_bg(logo)
            # Crop to non-transparent bounding box so whitespace doesn't affect scale
            bbox = logo.getbbox()
            if bbox:
                logo = logo.crop(bbox)
            lw, lh = logo.size
            scale = width / lw
            new_w, new_h = int(lw * scale), int(lh * scale)
            logo = logo.resize((new_w, new_h), Image.LANCZOS)
            x_pos = center_x - new_w // 2
            y_pos = center_y - new_h // 2
            base = img.convert("RGBA")
            base.paste(logo, (x_pos, y_pos), logo)
            return base.convert("RGB")
        except Exception as e:
            print(f"  Warning: could not load asset {asset_path}: {e}")
    # PIL fallback
    return _draw_youtube_logo_pil(img, center_x, center_y, width)


def _draw_youtube_logo_pil(img, center_x, center_y, width=300):
    """PIL fallback: draw YouTube logo as red rounded rect + white triangle."""
    draw = ImageDraw.Draw(img)
    h = int(width * 9 / 16)
    x0 = center_x - width // 2
    y0 = center_y - h // 2
    x1 = center_x + width // 2
    y1 = center_y + h // 2
    radius = h // 5
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=(255, 0, 0))
    tw_tri = int(width * 0.32)
    th_tri = int(h * 0.55)
    tcx = center_x + int(width * 0.025)
    tcy = center_y
    triangle = [
        (tcx - tw_tri // 2, tcy - th_tri // 2),
        (tcx - tw_tri // 2, tcy + th_tri // 2),
        (tcx + tw_tri // 2, tcy),
    ]
    draw.polygon(triangle, fill=(255, 255, 255))
    return img


def _make_logo_drawer(name):
    return lambda img, cx, cy, width=300: draw_logo_from_asset(name, img, cx, cy, width)


LOGO_DRAWERS["youtube"] = _make_logo_drawer("youtube")


def composite_image(base_img, overlay_path, y_top, y_bottom):
    """Paste overlay_path into base_img between y_top and y_bottom, centered."""
    try:
        overlay = Image.open(str(overlay_path)).convert("RGBA")
    except Exception as e:
        print(f"  Warning: could not open image {overlay_path}: {e}")
        return base_img

    area_w = W - PAD * 2
    area_h = y_bottom - y_top
    ow, oh = overlay.size
    scale = min(area_w / ow, area_h / oh, 1.0)   # never upscale
    new_w = int(ow * scale)
    new_h = int(oh * scale)
    overlay = overlay.resize((new_w, new_h), Image.LANCZOS)
    overlay = add_rounded_corners(overlay, radius=20)

    x_pos = (W - new_w) // 2
    y_pos = y_top + (area_h - new_h) // 2

    base_img = base_img.convert("RGBA")
    base_img.paste(overlay, (x_pos, y_pos), overlay)
    return base_img.convert("RGB")


# ── Base slide factory ────────────────────────────────────────────────────────
def make_base(num, total, brand_text, handle, bg_path=None):
    if bg_path and Path(bg_path).exists():
        bg_img = Image.open(bg_path).convert("RGB")
        bg_w, bg_h = bg_img.size
        scale = max(W / bg_w, H / bg_h)
        new_w, new_h = int(bg_w * scale), int(bg_h * scale)
        bg_img = bg_img.resize((new_w, new_h), Image.LANCZOS)
        x_off = (new_w - W) // 2
        y_off = (new_h - H) // 2
        bg_img = bg_img.crop((x_off, y_off, x_off + W, y_off + H))
        # Subtle white overlay so text stays readable
        overlay = Image.new("RGBA", (W, H), (255, 255, 255, 60))
        img = bg_img.convert("RGBA")
        img = Image.alpha_composite(img, overlay).convert("RGB")
    else:
        img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    f_counter = load_font(28)
    f_brand   = load_font(32, bold=True)
    f_handle  = load_font(28)

    draw_counter(draw, num, total, f_counter)
    draw_dots(draw, W - PAD - 44, PAD + 44)
    draw_brand(draw, brand_text, handle, f_brand, f_handle)

    return img, draw


# ── Slide renderers ───────────────────────────────────────────────────────────

def slide_cover(data, idx):
    s = data["slides"][idx]
    total = len(data["slides"])
    img, draw = make_base(idx + 1, total, data["brand_text"], data["handle"], data.get("bg_path"))

    f_head = load_font(120, bold=True)
    f_sub  = load_font(46)

    y = 185
    y = render_headline(draw, s["headline_lines"], s.get("accent_words", []), y, f_head)

    if s.get("subtitle"):
        y += 38
        draw_rule(draw, y, LGRAY)
        y += 20
        sub_font = f_sub
        max_w = W - PAD * 2
        if tw(draw, s["subtitle"], f_sub) > max_w:
            scale = max_w / tw(draw, s["subtitle"], f_sub)
            sub_font = load_font(max(int(46 * scale), 24))
        draw.text((PAD, y), s["subtitle"], font=sub_font, fill=GRAY)
        y += th(draw, "Ag", sub_font) + 20

    # Draw logo if specified (e.g. "logo": "youtube")
    logo_key = s.get("logo", "")
    if logo_key and logo_key in LOGO_DRAWERS:
        # Center logo in remaining space above brand row
        logo_top = y + 30
        logo_bottom = H - 120
        logo_cy = (logo_top + logo_bottom) // 2
        img = LOGO_DRAWERS[logo_key](img, W // 2, logo_cy, width=300)
    elif s.get("image_path") and Path(s["image_path"]).exists():
        img = composite_image(img, s["image_path"], y_top=y + 30, y_bottom=H - 110)

    return img


def slide_pain(data, idx):
    """Pain, How, Results slides - headline + bullets."""
    s = data["slides"][idx]
    total = len(data["slides"])
    img, draw = make_base(idx + 1, total, data["brand_text"], data["handle"], data.get("bg_path"))

    f_head   = load_font(110, bold=True)
    f_bullet = load_font(50)

    y = 170
    y = render_headline(draw, s["headline_lines"], s.get("accent_words", []), y, f_head)

    if s.get("bullets"):
        y += 52
        render_bullets(draw, s["bullets"], y, f_bullet)

    return img


def slide_solution(data, idx):
    """Solution slide - headline + optional subtitle + optional composited image."""
    s = data["slides"][idx]
    total = len(data["slides"])
    img, draw = make_base(idx + 1, total, data["brand_text"], data["handle"], data.get("bg_path"))

    f_head = load_font(116, bold=True)
    f_sub  = load_font(46)

    y = 185
    y = render_headline(draw, s["headline_lines"], s.get("accent_words", []), y, f_head)

    if s.get("subtitle"):
        y += 38
        sub_font = f_sub
        max_w = W - PAD * 2
        if tw(draw, s["subtitle"], f_sub) > max_w:
            scale = max_w / tw(draw, s["subtitle"], f_sub)
            sub_font = load_font(max(int(46 * scale), 24))
        draw.text((PAD, y), s["subtitle"], font=sub_font, fill=GRAY)
        y += th(draw, "Ag", sub_font) + 16

    if s.get("bullets"):
        f_bullet = load_font(50)
        y += 10
        render_bullets(draw, s["bullets"], y, f_bullet)
        y += len(s["bullets"]) * (th(draw, "Ag", f_bullet) + 22)

    # Composite image into lower portion if provided
    image_path = s.get("image_path")
    if image_path and Path(image_path).exists():
        img = composite_image(img, image_path, y_top=y + 30, y_bottom=H - 110)

    return img


def slide_cta(data, idx):
    """CTA slide - centered layout matching @aiwithanushka exactly.
    Summary lines (bold, centered) → Comment (large, centered) → "word" in quotes (accent, centered) → handle (centered)
    """
    s = data["slides"][idx]
    total = len(data["slides"])
    img, draw = make_base(idx + 1, total, data["brand_text"], data["handle"], data.get("bg_path"))

    f_summary = load_font(52, bold=True)
    f_comment = load_font(88, bold=True)
    f_word    = load_font(108, bold=True)
    f_handle  = load_font(46)

    # Summary lines - centered, bold, near-black (auto-scale if too wide)
    y = 200
    for line in s.get("summary_lines", []):
        use_font = f_summary
        max_w = W - PAD * 2
        if tw(draw, line, use_font) > max_w:
            scale = max_w / tw(draw, line, use_font)
            use_font = load_font(max(int(52 * scale), 28), bold=True)
        lh_s = th(draw, "Ag", use_font) + 18
        x = cx(draw, line, use_font)
        draw.text((x, y), line, font=use_font, fill=BLACK)
        y += lh_s

    # Large gap before CTA
    y += 80

    # "Comment" - large, bold, centered
    comment_text = s.get("cta_action", "Comment")
    x = cx(draw, comment_text, f_comment)
    draw.text((x, y), comment_text, font=f_comment, fill=BLACK)
    y += th(draw, "Ag", f_comment) + 12

    # CTA word in curly quotes, terra cotta, centered
    cta_word = f'\u201c{s.get("cta_word", "")}\u201d'   # "word"
    x = cx(draw, cta_word, f_word)
    draw.text((x, y), cta_word, font=f_word, fill=ACCENT)
    y += th(draw, "Ag", f_word) + 60

    # Handle centered prominently in middle of slide
    handle = data["handle"]
    x = cx(draw, handle, f_handle)
    draw.text((x, y), handle, font=f_handle, fill=BLACK)

    return img


RENDERERS = {
    "cover":    slide_cover,
    "pain":     slide_pain,
    "solution": slide_solution,
    "how":      slide_pain,
    "results":  slide_pain,
    "cta":      slide_cta,
}


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 3:
        print("Usage: instagram_writer.py <slides.json> <output_dir> [bg_image.png]")
        sys.exit(1)

    json_path  = sys.argv[1]
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(json_path) as f:
        data = json.load(f)

    # Optional background image (3rd positional arg or bg_path in JSON)
    if len(sys.argv) >= 4:
        data["bg_path"] = sys.argv[3]

    total  = len(data["slides"])
    images = []

    for i, slide in enumerate(data["slides"]):
        slide_type = slide.get("type", "cover")
        renderer   = RENDERERS.get(slide_type, slide_cover)
        img        = renderer(data, i)

        out_path = output_dir / f"slide_{i + 1:02d}.png"
        img.save(str(out_path), "PNG")
        images.append(img)
        print(f"  slide {i + 1}/{total}: {out_path.name}")

    # PDF for Blotato upload
    pdf_path = output_dir / "carousel.pdf"
    images[0].save(
        str(pdf_path), "PDF",
        resolution=150,
        save_all=True,
        append_images=images[1:],
    )

    print(f"\n  PDF: {pdf_path}")
    print(f"  {total} slides ready")


if __name__ == "__main__":
    main()
