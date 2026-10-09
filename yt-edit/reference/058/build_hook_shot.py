#!/usr/bin/env python3
"""058 hook SHOT build - camera zooms + the desktop insert + the graphics overlay.

Three things happen here, in one encode of the camera so the film is never re-encoded
twice:

1. ZOOM. Defined on the FILM timeline, not per clip, and only inside windows where the
   camera is actually visible. Hold, move, hold - a value constant before and after is
   what makes a move read as a move rather than a drift. Every move is >=8% over ~0.3s
   (056 measured 26-63%/s on the moves that were actually visible) and pinned to a word
   from transcript/recut_words.json. Direction alternates; a repeated identical punch
   reads as a tic.

2. THE DESKTOP INSERT. "or building something that's sustainable" is a line about a
   specific thing, so it shows the thing: real Hermes desktop capture in a 1400x788
   rounded rect with a 4px white border, travelling up from below. Generated b-roll can
   only gesture at a mood; on a line about a product, show the product.

3. The graphics MOV from build_hook.py composites last, over the zoomed camera.

Zoom plan (clip-local seconds, from the cut plan):

  clip 0  recut  0.00- 5.03   src  50.90- 55.93
      hold 1.00, punch to 1.13 on "important" (4.06)            IN
  clip 1  recut  5.03-13.93   src  59.80- 68.70
      open 1.12, snap to 1.00 on "terrible" (0.80)              OUT
      hold, punch to 1.13 on "self" (6.77)                      IN
  clip 2  recut 13.93-17.53   src  85.90- 89.50
      hold 1.00, punch to 1.15 on "love" (2.85)                 IN

Output: recut/058-intro.mp4, which recut.py picks up in place of the bare camera cut.
"""
import json, os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zoomlib import zexpr, xy, UP

CAM    = os.path.expanduser("~/Movies/Camtasia")
NAME   = "058 - hermes agent"
BASE   = os.path.join(CAM, NAME)
CAMERA = os.path.join(CAM, f"{NAME} - CAMERA.mp4")
SCREEN = os.path.join(CAM, f"{NAME} - SCREEN.mp4")
OUT    = os.path.join(BASE, "recut")
WORK   = os.path.join(OUT, "hookwork")
GFX    = os.path.join(BASE, "overlays/movs/hook.mov")
RRM    = os.path.join(BASE, "overlays/assets/rr_mask.png")
RRB    = os.path.join(BASE, "overlays/assets/rr_border.png")
DST    = os.path.join(OUT, "058-intro.mov")

FPS = 30

# (src_a, src_b, [zoom keyframes in clip-local seconds], anchor px/py or None)
SHOTS = [
    (50.90, 55.93, [(0.00, 1.00), (3.90, 1.00), (4.24, 1.13), (5.03, 1.13)], None),
    (59.80, 68.70, [(0.00, 1.12), (0.72, 1.12), (1.06, 1.00), (6.69, 1.00),
                    (7.03, 1.13), (8.90, 1.13)], None),
    (85.90, 89.50, [(0.00, 1.00), (2.77, 1.00), (3.11, 1.15), (3.60, 1.15)], None),
]

# The desktop insert. Real capture of the app working, shown while he says the line it
# is about. Recut 9.2-13.5 sits under "sustainable ... build on top ... self-improve".
# src 1846 picked by measurement: content region changing every frame (mean delta 19.8,
# the highest sustained window in the film) and confirmed by eye as the agent actually
# responding, not a settings page or a static doc.
#
# 1600x900 centred at x=160: bigger than the 056 default 1400x788 because this is the
# only product shot in the hook and it has to read. Its right edge is x=1760, clear of
# frame; his head is behind it, which is fine for 4s on a line about the product.
INSERT = dict(src=(1846.0, 1850.30), at=9.20, dur=4.30,
              x=160, y=150, w=1600, h=900)


def run(c):
    r = subprocess.run(c, capture_output=True, text=True)
    if r.returncode: sys.exit(f"FAILED {' '.join(c[:14])}\n{r.stderr[-2500:]}")


def make_rr():
    """Alpha mask + border stroke for the rounded rect. Generated once, not a CSS radius:
    these are video layers, so the corner is antialiased once and identically.

    Regenerates whenever INSERT's size changes. The first version skipped on existence
    alone, so resizing the insert left 1400x788 masks on disk and alphamerge died with
    "Input frame sizes do not match" - a hard failure, but only after a full shot render.
    """
    from PIL import Image, ImageDraw
    W, H, R, B = INSERT["w"], INSERT["h"], 30, 4
    if os.path.exists(RRM) and os.path.exists(RRB) \
       and Image.open(RRM).size == (W, H) and Image.open(RRB).size == (W, H):
        return
    os.makedirs(os.path.dirname(RRM), exist_ok=True)
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, W-1, H-1], radius=R, fill=255)
    m.save(RRM)
    f = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(f).rounded_rectangle([B/2, B/2, W-1-B/2, H-1-B/2],
                                        radius=R, outline=(255, 255, 255, 255), width=B)
    f.save(RRB)
    print(f"  rr mask rebuilt at {W}x{H}")


def render_shots():
    """Each shot input-seeks its own span, supersamples 2x, then zoompans.

    Audio comes with each shot and is concatenated with it. The three hook clips are
    NON-CONTIGUOUS in the source (50.90-55.93, 59.80-68.70, 85.90-89.50), so taking a
    single 17.53s audio span from 50.90 would run to 68.43 and drag in the retakes the
    cut plan removed. Keep video and audio on the same trim.
    """
    parts = []
    for i, (a, b, keys, anchor) in enumerate(SHOTS):
        dst = os.path.join(WORK, f"s{i}.mov")
        parts.append(dst)
        if os.path.exists(dst): continue
        n = int(round((b-a)*FPS))
        ex, ey = xy(*(anchor or (None, None)))
        z = zexpr(keys)
        vf = (f"scale={1920*UP}:{1080*UP}:flags=lanczos,"
              f"zoompan=z='{z}':x='{ex}':y='{ey}':d=1:s=1920x1080:fps={FPS}")
        run(["ffmpeg", "-v", "error", "-nostdin", "-ss", f"{a}", "-t", f"{b-a}",
             "-i", CAMERA, "-vf", vf, "-frames:v", str(n),
             "-c:v", "libx264", "-preset", "medium", "-crf", "18",
             "-c:a", "pcm_s16le", "-r", str(FPS), "-y", dst])
    return parts


if __name__ == "__main__":
    os.makedirs(WORK, exist_ok=True)
    make_rr()
    parts = render_shots()

    # join the zoomed shots, then lay the insert and the graphics over the join so both
    # are placed in RECUT time rather than per shot
    lst = os.path.join(WORK, "j.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    joined = os.path.join(WORK, "zoomed.mov")
    run(["ffmpeg", "-v", "error", "-nostdin", "-f", "concat", "-safe", "0", "-i", lst,
         "-c", "copy", "-y", joined])

    ia, ib = INSERT["src"]
    t0, t1 = INSERT["at"], INSERT["at"] + INSERT["dur"]
    # Travel from below into place over 0.55s, then hold. `p` MUST be clamped: an
    # unclamped (t-t0)/0.55 keeps growing after the move is over, and since the whole
    # expression is evaluated every frame the card carries on drifting for the rest of
    # the beat instead of landing. First build did exactly that - it was still moving
    # 3s in. min(1,...) is the fix.
    p = f"min(1,max(0,(t-{t0:.2f})/0.55))"
    ty = f"{INSERT['y']}+520*(1-({p})*({p})*(3-2*({p})))"
    # Order matters: graphics MOV goes on the camera FIRST, so the grid it carries lands
    # behind the insert and acts as a ground. Compositing the graphics last would put the
    # grid lines on top of the desktop capture, which reads as dirt on the screenshot.
    # The caption still reads because it sits at y=990, below the insert's 1020 bottom.
    fc = (
        f"[0:v][4:v]overlay=0:0:eof_action=pass[bed];"
        f"[1:v]scale={INSERT['w']}:{INSERT['h']}:flags=lanczos,format=rgba,"
        f"setpts=PTS-STARTPTS+{t0}/TB[ins];"
        f"[2:v]format=gray[mk];[ins][mk]alphamerge[insa];"
        f"[insa][3:v]overlay=0:0:format=auto[insb];"
        f"[bed][insb]overlay=x={INSERT['x']}:y='{ty}':"
        f"enable='between(t,{t0},{t1})':eof_action=pass,format=yuv420p[v]"
    )
    run(["ffmpeg", "-v", "error", "-nostdin",
         "-i", joined,
         "-ss", f"{ia}", "-t", f"{ib-ia}", "-i", SCREEN,
         "-i", RRM, "-i", RRB, "-i", GFX,
         "-filter_complex", fc, "-map", "[v]", "-map", "0:a",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-c:a", "pcm_s16le", "-r", str(FPS), "-y", DST])
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                              "format=duration", "-of", "csv=p=0", DST],
                             capture_output=True, text=True).stdout)
    print(f"-> {DST}  {d:.2f}s")
