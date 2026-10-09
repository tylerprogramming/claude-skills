#!/usr/bin/env python3
"""058 outline b-roll - rounded video clips on the LEFT, under the agenda cards.

The agenda cards (build_outline.py) now sit to the RIGHT of his face. That leaves the
left band empty for 28 seconds, so the beat shows the thing each card names: real
screen capture, 3s per clip, in a rounded rect with a 4px white border, travelling up
from below exactly like the hook insert.

Four of the six cards get a clip. Hardware and Features are lines he says in passing;
a clip for every card would be a slideshow and would out-pace the narration.

  INSTALL       src  557-560   the Hermes agent TUI running in a terminal. Doubles as
                               the "terminal showing hermes-agent" shot.
  LOCAL MODELS  src 3353-3356  the Ollama site, "Run open models".
  THE DESKTOP   src 1846-1849  the app mid-session, agent responding. Highest sustained
                               frame delta in the film (25.4 measured over 3s).
  MULTI-AGENT   src 4506-4509  the Kanban board with task cards in lanes. Confirmed by
                               eye; the 4117 GitHub PR was the alternative but that is
                               an artifact, not agents working.

Each clip lands on the word its card lands on, so picture and card arrive together.
Border is 4px BLACK: these captures are near-white pages and a white border vanished
into them, while black reads as a frame against both the page and the dark room.

Output: overlays/movs/outline-broll.mov (transparent ProRes 4444)
"""
import os, subprocess, sys

BASE   = os.path.expanduser("~/Movies/Camtasia/058 - hermes agent")
SCREEN = os.path.expanduser("~/Movies/Camtasia/058 - hermes agent - SCREEN.mp4")
ASSETS = os.path.join(BASE, "overlays/assets")
MOVS   = os.path.join(BASE, "overlays/movs")
DST    = os.path.join(MOVS, "outline-broll.mov")

AT   = 58.20                 # recut second the MOV is composited at (same as the cards)
DUR  = 31.00
FPS  = 30
W, H = 1920, 1080
BW, BH = 1000, 562           # 16:9 clip box in the left band
BX, BY = 96, 300             # his warm span starts at x=720, so 96..1096 is clear
RAD, BORD = 26, 4
BORDER_RGBA = (0, 0, 0, 255)
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

# (label, caption, src_start, seconds into THIS composition to appear, hold)
CLIPS = [
    ("install",     "HERMES AGENT IN THE TERMINAL",  557.0, 65.23 - AT, 3.0),
    ("localmodels", "OPEN MODELS, RUNNING LOCALLY", 3353.0, 73.22 - AT, 3.0),
    ("desktop",     "THE HERMES AGENT DESKTOP",     1846.0, 76.41 - AT, 3.0),
    ("multiagent",  "AGENTS WORKING A KANBAN BOARD",4506.0, 84.33 - AT, 3.0),
]


def run(c):
    r = subprocess.run(c, capture_output=True, text=True)
    if r.returncode: sys.exit(f"FAILED {' '.join(c[:14])}\n{r.stderr[-2500:]}")


def make_rr():
    """Mask + border for the rounded rect. Cache key includes the border colour, so
    switching white to black regenerates instead of silently reusing the old PNG."""
    from PIL import Image, ImageDraw
    ck = f"{BW}x{BH}_{BORDER_RGBA[0]}{BORDER_RGBA[1]}{BORDER_RGBA[2]}"
    m_p = os.path.join(ASSETS, f"broll_mask_{BW}x{BH}.png")
    b_p = os.path.join(ASSETS, f"broll_border_{ck}.png")
    if not (os.path.exists(m_p) and os.path.exists(b_p)):
        os.makedirs(ASSETS, exist_ok=True)
        m = Image.new("L", (BW, BH), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, BW-1, BH-1], radius=RAD, fill=255)
        m.save(m_p)
        f = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
        ImageDraw.Draw(f).rounded_rectangle([BORD/2, BORD/2, BW-1-BORD/2, BH-1-BORD/2],
                                            radius=RAD, outline=BORDER_RGBA,
                                            width=BORD)
        f.save(b_p)
        print(f"  rr assets built at {BW}x{BH}, border rgb{BORDER_RGBA[:3]}")
    return m_p, b_p


def make_label(text, idx):
    """Caption rendered to a PNG and overlaid as a layer.

    Not drawtext: this ffmpeg build has no drawtext filter ("No such filter"), and a PNG
    also gets the exact typeface and tracking the rest of the film uses rather than
    whatever fontconfig resolves.
    """
    from PIL import Image, ImageDraw, ImageFont
    os.makedirs(ASSETS, exist_ok=True)
    p = os.path.join(ASSETS, f"lab_{idx}.png")
    f = ImageFont.truetype(FONT, 34)
    img = Image.new("RGBA", (BW, 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # a soft dark pad behind the text so it survives both the dark room and a bright page
    d.text((7, 13), text, font=f, fill=(0, 0, 0, 190), stroke_width=6,
           stroke_fill=(0, 0, 0, 190))
    d.text((6, 12), text, font=f, fill=(255, 255, 255, 255))
    img.save(p)
    return p


if __name__ == "__main__":
    os.makedirs(MOVS, exist_ok=True)
    mask, border = make_rr()
    for _, _, _, at, hold in CLIPS:
        assert 0 <= at and at + hold < DUR, f"clip at {at} +{hold} outside {DUR}"

    # transparent bed the clips composite onto, so the result is one alpha MOV that the
    # recut can lay over camera exactly like any other graphics build
    cmd = ["ffmpeg", "-v", "error", "-nostdin",
           "-f", "lavfi", "-i", f"color=c=black@0.0:s={W}x{H}:r={FPS}:d={DUR:.2f},format=rgba"]
    fc, cur = "", "[0:v]"
    for i, (name, caption, src, at, hold) in enumerate(CLIPS):
        lab = make_label(caption, i)
        cmd += ["-ss", f"{src}", "-t", f"{hold}", "-i", SCREEN]
        vi = 1 + i*4
        cmd += ["-i", mask, "-i", border, "-i", lab]
        # travel up into place over 0.5s, hold, then a single fast exit. p is clamped:
        # an unclamped ramp keeps evaluating and the clip drifts for the whole beat.
        p = f"min(1,max(0,(t-{at:.2f})/0.5))"
        y = f"{BY}+420*(1-({p})*({p})*(3-2*({p})))"
        fc += (f"[{vi}:v]scale={BW}:{BH}:flags=lanczos,format=rgba,"
               f"setpts=PTS-STARTPTS+{at:.2f}/TB[c{i}];"
               f"[{vi+1}:v]format=gray[mk{i}];[c{i}][mk{i}]alphamerge[ca{i}];"
               f"[ca{i}][{vi+2}:v]overlay=0:0:format=auto[cb{i}];")
        nxt = f"[bed{i}]"
        fc += (f"{cur}[cb{i}]overlay=x={BX}:y='{y}':"
               f"enable='between(t,{at:.2f},{at+hold:.2f})':eof_action=pass{nxt};")
        cur = nxt
        # the caption follows the clip up, so label and picture arrive as one object
        ly = f"{BY+BH+18}+420*(1-({p})*({p})*(3-2*({p})))"
        out = f"[lab{i}]"
        fc += (f"{cur}[{vi+3}:v]overlay=x={BX}:y='{ly}':"
               f"enable='between(t,{at+0.12:.2f},{at+hold:.2f})'{out};")
        cur = out
    fc = fc.rstrip(";").replace(cur, "[vout]")
    run(cmd + ["-filter_complex", fc, "-map", "[vout]",
               "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
               "-t", f"{DUR:.2f}", "-r", str(FPS), "-y", DST])
    d = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                              "-of","csv=p=0",DST],capture_output=True,text=True).stdout)
    print(f"-> {DST}  {d:.2f}s")
