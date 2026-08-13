#!/usr/bin/env python3
"""
Instagram carousel generator.
Bold two-tone typography on a themed ground.
6-slide structure: Cover → Pain → Solution → How → Results → CTA

Colours come from ~/social-studio/themes/<id>.json - default "electric"
(near-white / near-black / electric blue). Pick another with THEME=cream, and
see themes/references/README.md there for what each style is meant to look
like beyond its three hex values.

Usage: python3 instagram_writer.py <slides.json> <output_dir>
Optional: slides can include "image_path" field for composited image slides.
"""

# --- skills venv bootstrap: run under .venv, not whatever python3 resolves to.
# Looks for .venv beside this script and up a few levels, then ~/.claude/skills,
# so a skill works wherever you copied it. Compares realpaths, and re-execs at
# most once, because a symlinked path that never compares equal would otherwise
# loop forever. Rationale: "Why there is a venv" in README.md
import os as _os, sys as _sys
if not _os.environ.get("SKILLS_VENV"):
    _base = _os.path.dirname(_os.path.abspath(__file__))
    for _v in [_os.path.realpath(_os.path.join(_base, *([".."] * _i), ".venv")) for _i in range(4)
               ] + [_os.path.realpath(_os.path.expanduser("~/.claude/skills/.venv"))]:
        if _os.path.exists(_os.path.join(_v, "bin", "python3")):
            if _os.path.realpath(_sys.prefix) != _v:
                _os.environ["SKILLS_VENV"] = _v
                _os.execv(_os.path.join(_v, "bin", "python3"),
                          [_os.path.join(_v, "bin", "python3"), *_sys.argv])
            break
# --- end bootstrap ---------------------------------------------------------

import sys
import json
import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "Pillow", "--quiet"], check=True)
    from PIL import Image, ImageDraw, ImageFont

# ── Design system ─────────────────────────────────────────────────────────────
# Colours come from a social-studio theme when that repo is present, so there is
# one place to change a palette instead of two that quietly drift. They already
# had: this file said #F5F0E8/#C4713A while cream.json said #F5F0EB/#E07355 -
# the same intent, a few points apart, with no way to tell which was current.
#
# Falls back to the electric values below when social-studio is not installed,
# so the skill still runs standalone. Override per run with THEME=<id>.
def _load_theme(name=None):
    name = name or os.environ.get("THEME", "electric")
    fallback = {"bgColor": "#FCFCFC", "textColor": "#0A0A0A", "accentColor": "#2454F0"}
    path = Path.home() / "social-studio" / "themes" / f"{name}.json"
    try:
        t = json.loads(path.read_text())
        if not all(k in t for k in ("bgColor", "textColor", "accentColor")):
            return fallback
        return t
    except Exception:
        return fallback


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


_THEME  = _load_theme()
BG      = _rgb(_THEME["bgColor"])
BLACK   = _rgb(_THEME["textColor"])
ACCENT  = _rgb(_THEME["accentColor"])
# Greys are derived from the ground rather than fixed, so a dark theme does not
# get light-warm-grey dots it cannot show.
def _lighten(rgb, amt=0.42):
    return tuple(int(c + (255 - c) * amt) for c in rgb)


# The accent is chosen against the light ground. The same value on a near-black
# terminal is muddy and low contrast - it reads as a darker grey-blue rather
# than as the brand colour. Dark surfaces get a lifted version.
ACCENT_DARK = _lighten(ACCENT, 0.42)
_dark   = sum(BG) / 3 < 128
GRAY    = tuple(int(c * 0.62 + (255 if _dark else 0) * 0.38) for c in BG) if _dark else (155, 155, 155)
LGRAY   = tuple(max(0, min(255, c - (18 if not _dark else -28))) for c in BG)

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


def load_script(size):
    """Handwritten face for asides. Bradley Hand reads closest to the reference;
    Snell is too formal and Chalkduster too noisy at this size."""
    for path in ("/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf",
                 "/System/Library/Fonts/Supplemental/Brush Script.ttf"):
        if Path(path).exists():
            try: return ImageFont.truetype(path, size)
            except Exception: pass
    return load_font(size)


def load_mono(size, bold=False):
    for path in (("/System/Library/Fonts/Menlo.ttc",) if not bold else
                 ("/System/Library/Fonts/Menlo.ttc",)):
        if Path(path).exists():
            try: return ImageFont.truetype(path, size, index=1 if bold else 0)
            except Exception: pass
    return load_font(size, bold)


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


def draw_grid(draw, step=52, dot=2, major=4):
    """Dotted ground.

    Lines, even at two weights, either vanish or start competing with the type
    for structure. A dot grid gives the same measured feel while staying out of
    the way, and it can carry more contrast without getting noisy - every fourth
    dot is larger and darker, which keeps a rhythm without drawing lines.
    """
    light = sum(BG) / 3 > 128
    minor = tuple(max(0, min(255, c - (18 if light else -22))) for c in BG)
    major_c = tuple(max(0, min(255, c - (34 if light else -40))) for c in BG)
    for iy, y in enumerate(range(step, H, step)):
        for ix, x in enumerate(range(step, W, step)):
            big = (ix % major == 0 and iy % major == 0)
            r = dot + 1 if big else dot
            draw.ellipse([x - r, y - r, x + r, y + r], fill=major_c if big else minor)


def draw_arrow(draw, x, y, size=26, color=None, width=3):
    """A right arrow, drawn.

    Bradley Hand has no arrow glyph and renders U+2192 as tofu, which is how a
    handwritten aside ends up with a box in it. Two lines and a head always
    work, in any face, at any size."""
    color = color or ACCENT
    draw.line([(x, y), (x + size, y)], fill=color, width=width)
    draw.line([(x + size - 9, y - 7), (x + size, y)], fill=color, width=width)
    draw.line([(x + size - 9, y + 7), (x + size, y)], fill=color, width=width)


def mono_rail(draw, num, total, topic, kicker=""):
    """Top rail: counter pill, topic, kicker, swipe marker.

    Everything is measured against the space actually left. The first version
    letterspaced the topic and kicker at a fixed size and ran them straight
    through the swipe marker and off the canvas - legible in isolation, broken
    on the slide."""
    f_pill = load_mono(26, bold=True)
    y = PAD - 6

    label = f"{num:02d} / {total:02d}"
    pw, ph = tw(draw, label, f_pill) + 34, 46
    draw.rounded_rectangle([PAD, y, PAD + pw, y + ph], radius=10, outline=ACCENT, width=2)
    draw.text((PAD + 17, y + 9), f"{num:02d}", font=f_pill, fill=ACCENT)
    draw.text((PAD + 17 + tw(draw, f"{num:02d}", f_pill), y + 9), label[2:],
              font=f_pill, fill=GRAY)

    # reserve the swipe marker on the right, then fit what is left
    f_sw = load_script(30)
    sw_w = tw(draw, "swipe", f_sw) + 40
    sw_x = W - PAD - sw_w
    draw.text((sw_x, y + 8), "swipe", font=f_sw, fill=ACCENT)
    draw_arrow(draw, sw_x + tw(draw, "swipe", f_sw) + 8, y + 24, size=24)

    x = PAD + pw + 26
    avail = sw_x - x - 26
    for size in (24, 22, 20, 18):
        f = load_mono(size, bold=True)
        t = _space(topic.upper())
        k = _space(kicker.upper()) if kicker else ""
        wid = tw(draw, t, f) + (tw(draw, "  \u00b7  " + k, f) if k else 0)
        if wid <= avail or size == 18:
            if wid > avail and k:      # still too wide: drop the kicker
                k = ""
                wid = tw(draw, t, f)
            draw.text((x, y + 13), t, font=f, fill=BLACK)
            if k:
                draw.text((x + tw(draw, t, f), y + 13), "  \u00b7  ", font=f, fill=LGRAY)
                draw.text((x + tw(draw, t + "  \u00b7  ", f), y + 13), k, font=f, fill=GRAY)
            break
    draw.line([(PAD, y + ph + 26), (W - PAD, y + ph + 26)], fill=LGRAY, width=1)


def footer_rail(draw, handle, steps, live_index, num, total):
    """Bottom rail: handle, step sequence, slide number.

    Same fitting rule as the top. Three left-aligned, centred and right-aligned
    runs of letterspaced mono will happily overprint each other; the steps are
    the optional one, so they go first when space runs out."""
    f = load_mono(20, bold=True)
    y = H - PAD - 6
    draw.line([(PAD, y - 24), (W - PAD, y - 24)], fill=LGRAY, width=1)

    h = _space(handle.upper())
    n = f"{num:02d} / {total:02d}"
    draw.text((PAD, y), h, font=f, fill=GRAY)
    draw.text((W - PAD - tw(draw, n, f), y), n, font=f, fill=GRAY)

    if not steps:
        return
    left = PAD + tw(draw, h, f) + 30
    right = W - PAD - tw(draw, n, f) - 30
    parts, sep = [_space(s.upper()) for s in steps], "  \u00b7  "
    total_w = sum(tw(draw, p, f) for p in parts) + tw(draw, sep, f) * (len(parts) - 1)
    if total_w > right - left:
        return                      # no room: better absent than overprinted
    x = left + (right - left - total_w) // 2
    for i, part in enumerate(parts):
        draw.text((x, y), part, font=f, fill=ACCENT if i == live_index else GRAY)
        x += tw(draw, part, f)
        if i < len(parts) - 1:
            draw.text((x, y), sep, font=f, fill=LGRAY)
            x += tw(draw, sep, f)


def _space(t, gap=" "):
    """Letterspacing, which PIL has no setting for. Mono type without it reads
    as code; with it, it reads as an instrument panel."""
    return gap.join(t)


def load_display(size, face=None):
    """The headline face.

    SF Pro at Black is the closest thing on a stock Mac to the modern grotesque
    the reference uses - tight, geometric, and it reads as product rather than
    poster. Arial Black, which this used first, is noticeably wider and older
    looking at display size. Helvetica Neue Condensed Black is the tighter
    alternative; set DISPLAY_FACE to pick.
    """
    face = face or os.environ.get("DISPLAY_FACE", "sfpro")
    order = {
        "sfpro":     [("/System/Library/Fonts/SFNS.ttf", 0, "Black")],
        "condensed": [("/System/Library/Fonts/HelveticaNeue.ttc", 9, None)],
        "helvetica": [("/System/Library/Fonts/HelveticaNeue.ttc", 1, None)],
        "avenir":    [("/System/Library/Fonts/Avenir Next.ttc", 8, None)],
        "arial":     [("/System/Library/Fonts/Supplemental/Arial Black.ttf", 0, None)],
    }.get(face, [])
    order += [("/System/Library/Fonts/SFNS.ttf", 0, "Black"),
              ("/System/Library/Fonts/HelveticaNeue.ttc", 9, None),
              ("/System/Library/Fonts/Supplemental/Arial Black.ttf", 0, None)]
    for path, idx, variation in order:
        if not Path(path).exists():
            continue
        try:
            f = ImageFont.truetype(path, size, index=idx)
            if variation:
                f.set_variation_by_name(variation)
            return f
        except Exception:
            continue
    return load_font(size, bold=True)


def tracked_width(draw, text, font, track=0):
    return sum(tw(draw, ch, font) for ch in text) + track * max(0, len(text) - 1)


def draw_tracked(draw, x, y, text, font, fill, track=0):
    """Draw with letterspacing PIL does not otherwise offer.

    Negative tracking is the difference between 'bold text' and a headline."""
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += tw(draw, ch, font) + track
    return x


def render_headline_centered(draw, lines, accent_lines, y, size=104, track=-3,
                             kicker="", rule=True):
    """Centred, all-caps, tightly tracked, with a rule under the accent line."""
    if kicker:
        f_k = load_mono(24, bold=True)
        kt = _space(kicker.upper())
        draw.text(((W - tw(draw, kt, f_k)) // 2, y), kt, font=f_k, fill=GRAY)
        y += th(draw, "Ag", f_k) + 26

    f = load_display(size)
    while size > 48 and max(tracked_width(draw, l.upper(), f, track) for l in lines) > W - PAD * 2:
        size -= 4
        f = load_display(size)

    last_accent = None
    for line in lines:
        t = line.upper()
        lw = tracked_width(draw, t, f, track)
        is_accent = line in accent_lines
        x = (W - lw) // 2
        draw_tracked(draw, x, y, t, f, ACCENT if is_accent else BLACK, track)
        # Real drawn extent, not th(). th() returns the glyph box height, which
        # for a display size sits well above the actual bottom of the letters -
        # using it put the accent rule straight through the middle of the word.
        bottom = draw.textbbox((x, y), t, font=f)[3]
        if is_accent:
            last_accent = (bottom, x, x + lw)
        y = bottom + int(size * 0.10)

    if rule and last_accent:
        bottom, x0, x1 = last_accent
        draw.line([(x0, bottom + 16), (x1, bottom + 16)], fill=ACCENT, width=5)
        y = max(y, bottom + 16) + 14
    return y


def soft_shadow(img, box, radius=20, blur=9, offset=(0, 5), opacity=42):
    """A blurred rounded rect behind a tile.

    The reference's tiles sit on a soft shadow, which is most of why they read
    as objects on a surface rather than outlines printed on it. Flat outlined
    tiles looked like wireframe next to it."""
    x0, y0, x1, y1 = box
    pad = blur * 3
    layer = Image.new("RGBA", (int(x1 - x0) + pad * 2, int(y1 - y0) + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(
        [pad, pad, pad + (x1 - x0), pad + (y1 - y0)], radius=radius, fill=(15, 23, 42, opacity))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    img.paste(layer, (int(x0 - pad + offset[0]), int(y0 - pad + offset[1])), layer)


def draw_glyph(draw, name, cx_, cy_, size=34, color=None):
    """Icon marks, drawn heavy.

    The first set were hairline strokes at 40% of the tile and read as faint
    scratches; the reference's marks are solid, fill most of the tile, and use
    the real brand colour where a brand exists. Weight is what makes an icon
    legible at thumbnail size, not detail.
    """
    c = color or ACCENT
    w = max(3, size // 7)
    h = size / 2

    if name == "claude":                      # the Anthropic asterisk
        import math
        c = (217, 119, 87)
        rw = max(2, size // 11)               # eight fat rays merged into a blob
        for i in range(8):
            a = math.pi * i / 8
            dx, dy = math.cos(a), math.sin(a)
            draw.line([(cx_ - dx * h * 0.95, cy_ - dy * h * 0.95),
                       (cx_ + dx * h * 0.95, cy_ + dy * h * 0.95)], fill=c, width=rw)
    elif name == "obsidian":                  # the purple gem
        c = (124, 77, 225)
        draw.polygon([(cx_, cy_ - h), (cx_ + h * 0.8, cy_ - h * 0.1),
                      (cx_, cy_ + h), (cx_ - h * 0.8, cy_ - h * 0.1)], fill=c)
        draw.polygon([(cx_, cy_ - h), (cx_ + h * 0.8, cy_ - h * 0.1), (cx_, cy_ + h * 0.15)],
                     fill=(158, 118, 240))
    elif name == "wave":                      # local voice
        for i, hh in enumerate((0.30, 0.62, 1.0, 0.62, 0.30)):
            x = cx_ + (i - 2) * (size * 0.20)
            draw.line([(x, cy_ - h * hh), (x, cy_ + h * hh)], fill=c, width=w)
    elif name == "grid":                      # the HUD
        r = size * 0.21
        g = size * 0.06
        for gx in (-1, 1):
            for gy in (-1, 1):
                x0, y0 = cx_ + gx * (r + g) - r, cy_ + gy * (r + g) - r
                draw.rounded_rectangle([x0, y0, x0 + r * 2, y0 + r * 2],
                                       radius=max(2, w // 2), fill=c)
    elif name == "folder":
        draw.rounded_rectangle([cx_ - h, cy_ - h * 0.45, cx_ + h, cy_ + h * 0.8],
                               radius=w, fill=c)
        draw.rounded_rectangle([cx_ - h, cy_ - h * 0.8, cx_ - h * 0.05, cy_ - h * 0.35],
                               radius=w, fill=c)
    elif name == "doc":
        fold = h * 0.42
        draw.polygon([(cx_ - h * 0.68, cy_ - h), (cx_ + h * 0.68 - fold, cy_ - h),
                      (cx_ + h * 0.68, cy_ - h + fold), (cx_ + h * 0.68, cy_ + h),
                      (cx_ - h * 0.68, cy_ + h)], fill=c)
        bg = (255, 255, 255) if sum(BG) / 3 > 128 else (30, 30, 34)
        draw.polygon([(cx_ + h * 0.68 - fold, cy_ - h), (cx_ + h * 0.68, cy_ - h + fold),
                      (cx_ + h * 0.68 - fold, cy_ - h + fold)], fill=bg)
        for fy, ln in ((-0.18, 0.44), (0.16, 0.44), (0.50, 0.26)):
            draw.rounded_rectangle([cx_ - h * 0.40, cy_ + h * fy,
                                    cx_ - h * 0.40 + h * ln * 2, cy_ + h * fy + w * 0.9],
                                   radius=w // 2, fill=bg)
    elif name == "tag":
        for dx in (-0.30, 0.24):
            draw.line([(cx_ + h * dx + h * 0.16, cy_ - h * 0.80),
                       (cx_ + h * dx - h * 0.16, cy_ + h * 0.80)], fill=c, width=w)
        for dy in (-0.28, 0.26):
            draw.line([(cx_ - h * 0.80, cy_ + h * dy), (cx_ + h * 0.80, cy_ + h * dy)],
                      fill=c, width=w)
    elif name == "text":                      # plain english
        for i, ln in enumerate((1.0, 0.76, 0.94, 0.52)):
            y = cy_ - h * 0.62 + i * (size * 0.21)
            draw.rounded_rectangle([cx_ - h * 0.82, y, cx_ - h * 0.82 + h * 1.64 * ln, y + w],
                                   radius=w // 2, fill=c)
    elif name == "terminal":
        draw.rounded_rectangle([cx_ - h, cy_ - h * 0.8, cx_ + h, cy_ + h * 0.8],
                               radius=w, outline=c, width=w)
        draw.line([(cx_ - h * 0.5, cy_ - h * 0.2), (cx_ - h * 0.18, cy_ + h * 0.1)],
                  fill=c, width=w)
        draw.line([(cx_ - h * 0.18, cy_ + h * 0.1), (cx_ - h * 0.5, cy_ + h * 0.4)],
                  fill=c, width=w)
        draw.line([(cx_ + h * 0.05, cy_ + h * 0.4), (cx_ + h * 0.55, cy_ + h * 0.4)],
                  fill=c, width=w)
    elif name == "clock":
        draw.ellipse([cx_ - h * 0.88, cy_ - h * 0.88, cx_ + h * 0.88, cy_ + h * 0.88],
                     outline=c, width=w)
        draw.line([(cx_, cy_), (cx_, cy_ - h * 0.48)], fill=c, width=w)
        draw.line([(cx_, cy_), (cx_ + h * 0.40, cy_)], fill=c, width=w)
    elif name == "check":
        draw.line([(cx_ - h * 0.62, cy_ + h * 0.05), (cx_ - h * 0.14, cy_ + h * 0.5)],
                  fill=c, width=w + 2)
        draw.line([(cx_ - h * 0.14, cy_ + h * 0.5), (cx_ + h * 0.66, cy_ - h * 0.52)],
                  fill=c, width=w + 2)
    else:
        f = load_font(size, bold=True)
        draw.text((cx_ - tw(draw, name, f) // 2, cy_ - size // 2), name, font=f, fill=c)


def icon_row(img, draw, x, y, label, sub, glyph=None, tile=84):
    """A rounded tile with a glyph, a bold label, and a grey sub-line.

    The reference uses four of these to carry the components of the system.
    They are what turns a headline into a spec."""
    soft_shadow(img, (x, y, x + tile, y + tile), radius=20)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([x, y, x + tile, y + tile], radius=20,
                           fill=(255, 255, 255) if sum(BG) / 3 > 128 else (30, 30, 34))
    if glyph:
        draw_glyph(draw, glyph, x + tile // 2, y + tile // 2, size=int(tile * 0.54))

    f_lab = load_font(32, bold=True)
    f_sub = load_font(27)
    draw.text((x + tile + 26, y + 12), label.upper(), font=f_lab, fill=BLACK)
    draw.text((x + tile + 26, y + 50), sub, font=f_sub, fill=GRAY)
    return y + tile + 22


def terminal_card(img, draw, x, y, w, lines, title="", h=None, accent_last=True):
    """A dark terminal window with traffic lights, on a shadow.

    Lines may be plain strings, or (text, role) pairs where role is one of
    key/val/dim/accent. Colouring every line the same accent - which is what
    the first version did - reads as a wall of blue rather than as code."""
    lh = 38
    h = h or (72 + lh * len(lines) + 20)
    soft_shadow(img, (x, y, x + w, y + h), radius=18, blur=12, offset=(0, 7), opacity=48)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([x, y, x + w, y + h], radius=18, fill=(18, 20, 26))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        draw.ellipse([x + 22 + i * 26, y + 20, x + 34 + i * 26, y + 32], fill=c)
    if title:
        draw.text((x + 116, y + 18), _space(title.upper()),
                  font=load_mono(20, bold=True), fill=(150, 158, 170))

    ROLE = {"key": ACCENT_DARK, "val": (222, 228, 238), "dim": (108, 116, 130),
            "accent": ACCENT_DARK, "txt": (196, 202, 212)}
    f = load_mono(25, bold=True)
    ty = y + 62
    for i, line in enumerate(lines):
        if isinstance(line, (list, tuple)):
            text, role = line[0], line[1]
            col = ROLE.get(role, ROLE["txt"])
        else:
            text = line
            col = ACCENT_DARK if (accent_last and i == len(lines) - 1) else ROLE["txt"]
        draw.text((x + 26, ty), text, font=f, fill=col)
        ty += lh
    return y + h


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
def make_base(num, total, brand_text, handle, bg_path=None, rich=False):
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

    # The rich layout draws its own rails; the old counter and brand row would
    # collide with them.
    if rich:
        draw_grid(draw)
        return img, draw

    f_counter = load_font(28)
    f_brand   = load_font(32, bold=True)
    f_handle  = load_font(28)

    draw_counter(draw, num, total, f_counter)
    draw_dots(draw, W - PAD - 44, PAD + 44)
    draw_brand(draw, brand_text, handle, f_brand, f_handle)

    return img, draw


# ── Slide renderers ───────────────────────────────────────────────────────────

def slide_cover(data, idx):
    """Cover slide.

    Two layouts from one function. If the slide supplies `rows`, `terminal` or
    `hero_path` it builds the full six-band layout - rail, headline, aside,
    icon rows beside a hero, proof card, footer rail - which is what fills a 4:5
    frame. With none of those it falls back to the original headline-and-rule
    slide, so every carousel already written still renders unchanged.
    """
    s = data["slides"][idx]
    total = len(data["slides"])
    rich = any(s.get(k) for k in ("rows", "terminal", "hero_path"))
    img, draw = make_base(idx + 1, total, data["brand_text"], data["handle"],
                          data.get("bg_path"), rich=rich)

    if not rich:
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
        logo_key = s.get("logo", "")
        if logo_key and logo_key in LOGO_DRAWERS:
            img = LOGO_DRAWERS[logo_key](img, W // 2, (y + 30 + H - 120) // 2, width=300)
        elif s.get("image_path") and Path(s["image_path"]).exists():
            img = composite_image(img, s["image_path"], y_top=y + 30, y_bottom=H - 110)
        return img

    # ---- rich layout
    mono_rail(draw, idx + 1, total, data.get("topic_short", ""), data.get("kicker", ""))

    y = 168
    y = render_headline_centered(
        draw, s["headline_lines"], s.get("accent_lines", s.get("accent_words", [])),
        y, size=s.get("headline_size", 104), kicker=s.get("kicker", ""))

    if s.get("aside"):
        y += 20
        f_a = load_script(40)
        text = s["aside"]
        arrow = text.rstrip().endswith(("\u2192", "->"))
        text = text.rstrip().rstrip("\u2192").rstrip("->").rstrip()
        aw = tw(draw, text, f_a) + (40 if arrow else 0)
        ax = (W - aw) // 2
        draw.text((ax, y), text, font=f_a, fill=ACCENT)
        if arrow:
            draw_arrow(draw, ax + tw(draw, text, f_a) + 14, y + 26, size=26)
        y += th(draw, "Ag", f_a) + 34

    # icon rows on the left, hero on the right
    rows = s.get("rows", [])
    col_w = 470
    row_y = y
    for r in rows[:4]:
        row_y = icon_row(img, draw, PAD, row_y, r.get("label", ""), r.get("sub", ""),
                         r.get("glyph"))

    hero_bottom = row_y
    if s.get("hero_path") and Path(s["hero_path"]).exists():
        hero = Image.open(s["hero_path"]).convert("RGBA")
        box_w = W - PAD - (PAD + col_w) - 10
        box_h = max(row_y - y - 20, 240)
        scale = min(box_w / hero.width, box_h / hero.height)
        hero = hero.resize((max(1, int(hero.width * scale)), max(1, int(hero.height * scale))),
                           Image.LANCZOS)
        hero = add_rounded_corners(hero, radius=18)
        hx = PAD + col_w + 10 + (box_w - hero.width) // 2
        hy = y + (box_h - hero.height) // 2
        soft_shadow(img, (hx, hy, hx + hero.width, hy + hero.height),
                    radius=18, blur=12, offset=(0, 7), opacity=48)
        img.paste(hero, (hx, hy), hero)
        draw = ImageDraw.Draw(img)

    if s.get("terminal"):
        t = s["terminal"]
        top = hero_bottom + 18
        # the footer rail owns the last ~64px; a card sized purely by line count
        # ran straight through it and printed the handle over the last command
        room = (H - PAD - 64) - top
        lines = t.get("lines", [])
        # Drop from the MIDDLE. The last line is the payoff - it is the one
        # rendered in the accent colour and the reason the card is there at all.
        # Truncating from the end fit the box and threw away the point.
        while len(lines) > 2 and (72 + 38 * len(lines) + 20) > room:
            lines = lines[:len(lines) // 2 - 1] + lines[len(lines) // 2:]
        while len(lines) > 1 and (72 + 38 * len(lines) + 20) > room:
            lines = lines[:1] + lines[-1:]
            break
        if lines:
            terminal_card(img, draw, PAD, top, W - PAD * 2, lines, t.get("title", ""))

    footer_rail(draw, data["handle"], data.get("steps", []),
                s.get("live_step", 0), idx + 1, total)
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
