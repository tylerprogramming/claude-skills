#!/usr/bin/env python3
"""058 Hermes Agent - silence + retake recut.

Two treatments, chosen per keep by CAMERA_SPANS:

  CAMERA  full-frame presenter. The hook (src 50.90-89.50) and the promise beat
          (src 186.27-218.00, "I'm going to go through my whole setup ... without
          further ado, let's get started"), where the screen is only the teleprompter
          document and there is nothing to show.
  SCREEN  screen capture full frame + CAMERA circle-masked bottom right (bottom LEFT
          across PIP_LEFT, where real content sits under the circle).

The Hermes desktop app is captured full-screen with no browser chrome, so SCREEN is
used uncropped. Circle is the house default: 480px, 50px inset, crop 980x980+490+100.
Its left edge is at x=1390, so any wide graphic must clear that.

Cut plan in cutplan.json (silence pass at --noise=0.005, slivers pruned, retakes and
throat clears removed per RETAKES.md, boundaries snapped + frame-aligned).

  recut.py                 # whole film
  recut.py --minutes 3     # first 3 minutes for review
"""
import hashlib
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zoomlib import zexpr, xy, UP
from concurrent.futures import ThreadPoolExecutor

CAM    = os.path.expanduser("~/Movies/Camtasia")
NAME   = "058 - hermes agent"
BASE   = os.path.join(CAM, NAME)
SCREEN = os.path.join(CAM, f"{NAME} - SCREEN.mp4")
CAMERA = os.path.join(CAM, f"{NAME} - CAMERA.mp4")
OUT    = os.path.join(BASE, "recut")
PREV   = os.path.join(CAM, "058-previews")     # hyphenated: MEDIA cards fail on spaces
MASK   = os.path.join(BASE, "circle_mask.png")
RING   = os.path.join(BASE, "circle_ring.png")
WORK   = os.path.join(OUT, "batches")

# Graphics MOVs laid over a camera group. Keyed by the source second of the clip the MOV
# starts on, NOT the group's first clip: consecutive camera spans merge into one group,
# so the outline (src 238.17) lands inside a group that begins at src 186.27. Keying on
# the group start silently matched nothing and the overlay never appeared.
CAM_OVERLAYS = {238.17: [os.path.join(BASE, "overlays/movs/outline-broll.mov"),
                         os.path.join(BASE, "overlays/movs/outline.mov")],
                325.13: [os.path.join(BASE, "overlays/movs/hardware.mov")],
                407.60: [os.path.join(BASE, "overlays/movs/hardware2.mov")]}

# Camera zooms on bare-face stretches, keyed by the clip's source second.
# hold -> fast eased move -> hold, pinned to a measured word, alternating direction so
# no two consecutive moves push the same way. Clip-local seconds.
#   186.27  "I'm going to go through my whole setup"  push in on "whole" (187.92)
#   195.40  "a big difference for your experience"    pull out on "difference" (195.86)
#   306.60  "no, I still use Claude Code every day"   push in on "still" (309.19)
CAM_ZOOMS = {
    186.27: [(0.0, 1.00), (1.65, 1.00), (2.00, 1.13), (6.63, 1.13)],
    195.40: [(0.0, 1.13), (0.46, 1.13), (0.84, 1.00), (3.80, 1.00)],
    306.60: [(0.0, 1.00), (2.59, 1.00), (2.95, 1.12), (8.30, 1.12)],

    # Section intros after 5:00 (see SECTION_INTROS below). One move per keep, placed
    # ~38% in after a hold, 13% over 0.45s = 1.44%/frame peak, inside the 1.9%/frame
    # camera envelope. Direction alternates across the whole run and the scale carries
    # across cuts, so no two consecutive moves go the same way and no cut jumps scale.
    1069.40: [(0.0,1.00), (6.97,1.00), (7.42,1.13), (18.33,1.13)],   # where files live
    1732.23: [(0.0,1.13), (3.17,1.13), (3.62,1.00), (8.33,1.00)],    # skills intro
    1758.83: [(0.0,1.00), (1.86,1.00), (2.31,1.13), (4.90,1.13)],    # skills intro
    1765.77: [(0.0,1.13), (1.71,1.13), (2.16,1.00), (4.50,1.00)],    # skills intro
    1773.90: [(0.0,1.00), (3.88,1.00), (4.33,1.13), (10.20,1.13)],   # skills intro
    1786.90: [(0.0,1.13), (3.67,1.13), (4.12,1.00), (9.67,1.00)],    # skills intro
    2345.03: [(0.0,1.00), (5.54,1.00), (5.99,1.13), (14.57,1.13)],   # memory intro
    2364.27: [(0.0,1.13), (5.28,1.13), (5.73,1.00), (13.90,1.00)],   # memory intro
    2927.17: [(0.0,1.00), (7.63,1.00), (8.08,1.13), (20.07,1.13)],   # profiles intro
    4627.17: [(0.0,1.13), (3.67,1.13), (4.12,1.00), (9.67,1.00)],    # closing pitch
    4637.50: [(0.0,1.00), (1.89,1.00), (2.34,1.13), (4.97,1.13)],    # closing pitch
    4644.90: [(0.0,1.13), (4.66,1.13), (5.11,1.00), (12.27,1.00)],   # closing pitch
}

# Source spans rendered as full-frame camera. Everything else is screen + circle.
#   0-100      the hook
#   186-218.5  the promise beat ("I'm going to go through my whole setup")
#   238-315    the outline + "does this replace Claude Code". The screen here is only
#              the teleprompter document, so the agenda is built as a graphic
#              (build_outline.py) over full-frame camera. Runs to 315 so the
#              multi-agent b-roll clip at recut 84.33 has its full 3 seconds.
#   322.6-355  the hardware beat. Screen here is the teleprompter document, verified
#              frame by frame, so it runs as camera with build_hardware.py on the right.
#              Starts at 322.6, not 325: the keep begins at "Okay, so let's get started".
#   407-434    hardware options 3 and 4. After the Hostinger walkthrough the screen sits
#              idle on the homepage, so this returns to camera with build_hardware2.py.
#
# SECTION INTROS after 5:00. Each is a stretch where he introduces a new section with
# nothing happening on screen, then goes back to the screen when the demo starts.
# Found by measurement, not by scrubbing: screen motion under 1.6 at 1s resolution AND
# no pointing language ("if we go", "right here", "you can see", "click") in a +-4s
# window, run >=12s, then keep-aligned (a keep joins only if >55% of it falls inside)
# and gaze-checked on the camera frames. The end of each is the first pointing phrase,
# so the picture returns to the screen exactly when he starts demonstrating.
#   1069.40-1087.73   6:47  "where does all of this stay on your computer"
#   1732.23-1796.57  11:40  "let's move on to the second feature ... skills"
#   2345.03-2382.30  17:37  "there's one more concept ... that is memory"
#   2927.17-2947.23  22:37  "we're going to talk about profiles"
#   4627.17-4657.17  32:32  closing pitch
# The multi-agent intro at 28:04 was dropped: keep-aligned it collapses to 8.1s.
CAMERA_SPANS = [(0.0, 100.0), (186.0, 218.5), (238.0, 315.0), (322.0, 355.0),
                (407.0, 434.5),
                (1069.40, 1087.75), (1732.20, 1796.60), (2345.00, 2382.35),
                (2927.15, 2947.25), (4627.15, 4657.20)]

# Stretches where real content sits under the bottom-right circle (measured: 28-97% of
# the circle region is non-background there). Circle moves bottom-LEFT across these.
# Stretches where the circle moves to the bottom-LEFT. Derived by MEASUREMENT, not by
# eye: for every screen keep, compare content density (fraction of pixels with local
# contrast > 12) in the two 480px bottom corners, sampled at 20/50/80% through the keep,
# after any chrome crop. The circle goes left only where the RIGHT corner is clearly
# busier (>1.35x and above 2%).
#
# The previous hand-written list had three of its four spans backwards: at src 930 the
# left corner measures 3.1% against the right's 1.4%, so the circle was sitting ON the
# content it was supposed to avoid. Same at 2820-2850 (3.9 vs 1.0) and 3300 (3.8 vs 1.2).
# The one span that measured busier on the right (6.7% vs 4.4%) was src 4627-4658, but
# that is now a CAMERA span (the closing pitch), so no screen keep needs the left corner
# any more. Kept as an empty list rather than deleted so the mechanism stays in place.
PIP_LEFT = []

CIRCLE_D, MARGIN = 480, 50
CROP  = (980, 980, 490, 100)         # camera head-and-shoulders crop out of 1920x1080
CHROME_Y = 118                       # browser tab strip + address bar height, measured

# The chrome crop MUST preserve aspect. Cropping 1920x962 and scaling back to 1920x1080
# stretches everything vertically by 1080/962 = 1.1227, measured on the render at 1.1220:
# square sidebar icons came out 12% too tall and round avatars became ovals. Take a
# 16:9 window out of the cropped region instead - 1710x962 - which also drops 210px of
# width. That is a clean 1.123x punch-in with no distortion.
BROWSER_CW = 1710                    # round((1080 - CHROME_Y) * 16 / 9)

# Which 210px of width to give up, per keep. Chosen by minimising the CONTENT WEIGHT
# that the crop deletes, scanning every candidate x in steps of 3 rather than picking
# from three presets.
#
# The weight must count flat panels, not just edges. An edge-density metric measured the
# busy browser page behind a floating terminal and ignored the terminal itself, so the
# 26:31 keep was cropped at x=210 and sliced 32px off the terminal's left edge including
# the shell prompt. Weight is now `edge_density*3 + deviation_from_background`, where the
# background is sampled from the outermost 6 columns (always page chrome, never content).
# That makes a dark uniform terminal body expensive to cut.
BROWSER_CROP_X = {
    144.03: 210, 393.33: 0, 460.87: 195, 491.13: 45,
    555.80: 48, 576.87: 3, 739.77: 0, 744.17: 48,
    745.63: 0, 1622.27: 210, 1633.90: 210, 2254.53: 210,
    3177.33: 210, 3183.13: 210, 3352.67: 210, 3381.70: 210,
    3390.57: 0, 3419.97: 174, 4108.17: 210, 4110.80: 36,
    4664.63: 0, 4674.17: 0, 4689.43: 0,
}

# Keeps whose window is a BROWSER, so the tab strip and address bar get cropped off.
# Detected, not guessed: correlate rows 36-62 (the bookmarks bar) against a confirmed
# browser frame at src 396. Reads +0.5 to +1.0 on a browser and below +0.05 otherwise.
#
# An earlier version tested for a brightness edge at y=118 and found only 11 of these.
# It missed every keep where a terminal window floats OVER the browser: the terminal
# body killed the edge, but the tab strip is still on screen behind it. The bookmarks
# bar is the honest signal because it is the browser itself, not the page.
# Two keeps switch windows mid-clip, so they are SPLIT in the cut plan at the exact
# frame the chrome appears/disappears (found by bisecting the correlation to 1/30s):
#   src 2254.53 is browser until 2265.30, then the desktop app
#   src 4103.73 is the desktop app until 4108.17, then browser
# The split is lossless - total duration is unchanged - and it lets the browser half
# get cropped instead of leaving a Slack workspace URL on screen for 11 seconds.
BROWSER_KEEPS = {144.03, 393.33, 460.87, 491.13, 555.80, 576.87, 739.77, 744.17,
                 745.63, 1622.27, 1633.90, 2254.53, 3177.33, 3183.13, 3352.67,
                 3381.70, 3390.57, 3419.97, 4108.17, 4110.80, 4664.63, 4674.17,
                 4689.43}

# Secrets to blur. (x, y, w, h) in ORIGINAL 1920x1080 coordinates, before any chrome
# crop; the crop shift is applied at filter build time.
#
# `claude setup-token` prints an OAuth URL carrying a live authorization code, and the
# browser then shows the SAME code in its address bar. Both must go, plus the account
# email in the page footer. Boxes are generous: the terminal line soft-wraps across two
# rows and the exact wrap point moves between frames.
BLURS = {
    # terminal keep: the wrapped URL (2 rows) + address bar + footer email
    745.63: [(56, 640, 1660, 52), (150, 46, 1420, 36), (760, 1004, 420, 32)],
    744.17: [(56, 640, 1660, 52), (150, 46, 1420, 36), (760, 1004, 420, 32)],
    # oauth page keeps: address bar carries the code, footer carries the email
    739.77: [(150, 46, 1420, 36), (760, 1004, 420, 32)],
}

# Screen punch-ins for the install walkthrough, keyed by keep start. Clip-local seconds,
# pinned to measured words, anchored at the thing being named rather than frame centre.
# Kept under 1.30: 1080p UI text upscaled past that goes soft, and zoompan shimmer hits
# rendered text and 1px borders harder than photographic content.
#
# Move DURATION is set from the distance travelled, not fixed at 0.4s. The camera zooms
# move 12-13% in 0.4s, which is 1.8-1.9% per frame. Running a 24% screen move over the
# same 0.4s doubles the per-frame step to 2.97% and reads as a snap rather than a move.
# These durations hold every screen move at or under the camera's 1.9%/frame:
#   18% -> 0.53s,  20% -> 0.60s,  22% -> 0.63s,  24% -> 0.70s
#
# Anchors are given in ORIGINAL 1920x1080 coordinates. For a clip in BROWSER_KEEPS the
# frame is cropped by CHROME_Y and rescaled first, so the anchor is converted with
# y' = (y - CHROME_Y) * 1080/(1080-CHROME_Y). Skipping that conversion aims the zoom
# ~130px too low and the target drifts out of the punch.
SCREEN_ZOOMS = {
    # "click Mac, Linux, or Windows" 474.10 -> the install tabs; then the curl line
    460.87: ([(0.0,1.00),(12.9,1.00),(13.53,1.22),(19.6,1.22),(20.2,1.26),(21.1,1.26)],
             (640, 553)),
    # "it's just installing right now" 496.00 - hold on the terminal
    491.13: ([(0.0,1.00),(4.6,1.00),(5.13,1.18),(10.1,1.18)], (640, 600)),
    # "simply type hello" 563.78 -> the TUI prompt and its first response
    555.80: ([(0.0,1.00),(7.6,1.00),(8.30,1.24),(20.4,1.24)], (400, 692)),
    # "download from macOS" 583.67 -> the two buttons
    576.87: ([(0.0,1.00),(6.5,1.00),(7.10,1.20),(7.6,1.20)], (500, 441)),
}
BATCH, WORKERS, FPS = 30, 3, 30

def run(c):
    r = subprocess.run(c, capture_output=True, text=True)
    if r.returncode: sys.exit(f"FAILED {' '.join(c[:12])}\n{r.stderr[-2500:]}")
    # ffmpeg can exit 0 having written nothing: a bad filtergraph makes it print
    # "Nothing was written into output file" and still return success, leaving a
    # 0-byte file that concat happily skips. The render then comes out SHORT with no
    # error anywhere - a 5 minute preview arrived as 2:28 this way.
    dst = c[-1]
    if isinstance(dst, str) and dst.endswith((".mov", ".mp4")):
        if not os.path.exists(dst) or os.path.getsize(dst) < 1024:
            sys.exit(f"EMPTY OUTPUT {dst}\n{' '.join(c[:12])}\n{r.stderr[-3000:]}")

def is_cam(a):  return any(lo <= a < hi for lo, hi in CAMERA_SPANS)
def is_left(a): return any(lo <= a < hi for lo, hi in PIP_LEFT)

def render_cam(args):
    """Full-frame camera clips.

    Group 0 is the hook. If build_hook_shot.py has produced recut/058-intro.mov, USE it
    rather than re-rendering a bare camera cut: it already carries the zooms, the desktop
    insert and the graphics. The first version of this function printed "graphics build
    exists" and then rendered over it anyway, and because the concat still succeeded at
    the right duration nothing failed loudly - the graphics just silently vanished from
    the film. Same trap the 056 script documents.
    """
    idx, clips = args
    gfx = os.path.join(OUT, "058-intro.mov")
    if idx == 0 and os.path.exists(gfx) and "--rebuild-intro" not in sys.argv:
        want = sum(b-a for a,b in clips)
        got = float(subprocess.run(["ffprobe","-v","error","-show_entries",
              "format=duration","-of","csv=p=0",gfx],
              capture_output=True,text=True).stdout or 0)
        # the build must cover exactly the clips this group represents, or the audio
        # would drift against every later batch
        assert abs(got-want) < 0.05, f"058-intro.mov is {got:.2f}s, hook needs {want:.2f}s"
        print(f"  hook: using graphics build ({got:.2f}s)")
        return gfx
    tag = hashlib.md5(repr(clips).encode()).hexdigest()[:6]
    dst = os.path.join(WORK, f"c{idx:03d}-{tag}.mov")
    if os.path.exists(dst): return dst
    lo = min(a for a,_ in clips)-0.5; hi = max(b for _,b in clips)+0.5
    seg, lbl = [], []
    for i,(a,b) in enumerate(clips):
        z = CAM_ZOOMS.get(round(a, 2))
        if z:
            # supersample 2x before zoompan: at native res the filter samples on integer
            # pixels and rendered text/edges shimmer through the move.
            assert abs(z[-1][0] - (b-a)) < 0.15, \
                f"zoom at src {a} runs {z[-1][0]}s, clip is {b-a:.2f}s"
            seg.append(f"[0:v]trim={a-lo}:{b-lo},setpts=PTS-STARTPTS,"
                       f"scale={1920*UP}:{1080*UP}:flags=lanczos,"
                       f"zoompan=z='{zexpr(z)}':x='{xy()[0]}':y='{xy()[1]}':"
                       f"d=1:s=1920x1080:fps=30[v{i}]")
        else:
            seg.append(f"[0:v]trim={a-lo}:{b-lo},setpts=PTS-STARTPTS[v{i}]")
        seg.append(f"[0:a]atrim={a-lo}:{b-lo},asetpts=PTS-STARTPTS[a{i}]")
        lbl.append(f"[v{i}][a{i}]")
    fc = ";".join(seg)+";"+"".join(lbl)+f"concat=n={len(clips)}:v=1:a=1[cv][a]"
    cmd = ["ffmpeg","-v","error","-nostdin","-ss",f"{lo}","-t",f"{hi-lo}","-i",CAMERA]
    # A graphics MOV composites over the CONCATENATED camera, so its offset is measured
    # in group-local time: the durations of the clips before the one it starts on. The
    # clips are non-contiguous in the source, so source time and group time differ.
    ovs, local = [], 0.0
    for a,b in clips:
        movs = CAM_OVERLAYS.get(round(a, 2)) or []
        if isinstance(movs, str): movs = [movs]
        for mov in movs:
            if os.path.exists(mov):
                cmd += ["-i", mov]
                ovs.append((len(ovs)+1, local))
        local += b-a
    for i, at in ovs:
        fc += f";[{i}:v]setpts=PTS-STARTPTS+{at:.3f}/TB[ov{i}]"
    cur = "[cv]"
    for n, (i, _) in enumerate(ovs):
        nxt = "[vo]" if n == len(ovs)-1 else f"[m{i}]"
        fc += f";{cur}[ov{i}]overlay=0:0:eof_action=pass{nxt}"
        cur = nxt
    fc += f";{cur}format=yuv420p[v]"
    run(cmd + ["-filter_complex",fc,"-map","[v]","-map","[a]",
         "-c:v","libx264","-preset","medium","-crf","18","-c:a","pcm_s16le",
         "-r",str(FPS),"-y",dst])
    return dst

def render_batch(args):
    """Screen full-frame + camera circle. The circle never scales with the screen.

    The filename carries a hash of THIS batch's clip list, not just its index. Keyed on
    index alone, a shorter run reused the previous run's longer final batch: asking for
    3 minutes returned the 4-minute file, same duration, no error. Content-addressed
    names make a stale batch impossible.
    """
    idx, clips = args
    tag = hashlib.md5(repr(clips).encode()).hexdigest()[:6]
    dst = os.path.join(WORK, f"b{idx:03d}-{tag}.mov")
    if os.path.exists(dst): return dst
    lo = min(a for a,_ in clips)-0.5; hi = max(b for _,b in clips)+0.5
    seg, n = [], len(clips)
    for i,(a,b) in enumerate(clips):
        seg.append(f"[0:v]trim={a-lo}:{b-lo},setpts=PTS-STARTPTS[s{i}]")
        seg.append(f"[1:v]trim={a-lo}:{b-lo},setpts=PTS-STARTPTS[c{i}]")
        seg.append(f"[1:a]atrim={a-lo}:{b-lo},asetpts=PTS-STARTPTS[a{i}]")
    fc = ";".join(seg)+";"
    # Browser chrome crop, applied PER CLIP rather than to the whole batch. The tab
    # strip and address bar occupy the top 118px of a browser window; cropping them
    # hides tab titles naming unrelated work and enlarges the page ~11%. Only the
    # clips in BROWSER_KEEPS have chrome - a blanket crop cut real content off the
    # desktop app and terminal frames, which have none.
    for i,(a,b) in enumerate(clips):
        cropped = round(a, 2) in BROWSER_KEEPS
        src = f"[s{i}]"
        # Blur secrets BEFORE the chrome crop, so the boxes stay in original coords.
        # Each blur is its OWN filter chain terminated by ';', not a comma link: a
        # split/overlay cannot be spliced into the middle of a comma chain, which
        # produced "Terminating thread with return code -22" and an empty output file.
        for bi, (bx, by, bw, bh) in enumerate(BLURS.get(round(a, 2), [])):
            o = f"[bo{i}_{bi}]"
            # boxblur radius is bounded by the plane: luma must be < min(w,h)/2, and
            # the CHROMA plane is 4:2:0 subsampled so its own limit is half that again
            # ("Invalid chroma_param radius value 17, must be >= 0 and < 9"). Set the
            # two independently rather than letting chroma inherit the luma value.
            lr = max(2, min(bw, bh)//2 - 1)
            cr = max(1, min(bw, bh)//4 - 1)
            fc += (f"{src}split[bs{i}_{bi}][bm{i}_{bi}];"
                   f"[bm{i}_{bi}]crop={bw}:{bh}:{bx}:{by},"
                   f"boxblur=luma_radius={lr}:luma_power=4:"
                   f"chroma_radius={cr}:chroma_power=4[bb{i}_{bi}];"
                   f"[bs{i}_{bi}][bb{i}_{bi}]overlay={bx}:{by}{o};")
            src = o
        pre = ""
        if cropped:
            cx = BROWSER_CROP_X.get(round(a, 2), (1920 - BROWSER_CW)//2)
            pre += (f"crop={BROWSER_CW}:{1080-CHROME_Y}:{cx}:{CHROME_Y},"
                    f"scale=1920:1080:flags=lanczos,")
        z = SCREEN_ZOOMS.get(round(a, 2))
        if z:
            keys, (ax, ay) = z
            assert abs(keys[-1][0] - (b-a)) < 0.2, \
                f"screen zoom at src {a} runs {keys[-1][0]}s, clip is {b-a:.2f}s"
            assert max(k[1] for k in keys) <= 1.30, \
                f"screen zoom at src {a} exceeds 1.30 - UI text goes soft"
            # Anchors are authored in ORIGINAL 1920x1080 coords. The chrome crop moves
            # them on BOTH axes now that it is a 16:9 window: x shifts by the crop
            # origin and both scale by 1920/BROWSER_CW. Converting y only (the old
            # behaviour) left the punch-in aiming wide on any keep cropped off-centre.
            if cropped:
                cx = BROWSER_CROP_X.get(round(a, 2), (1920 - BROWSER_CW)//2)
                k_ = 1920.0/BROWSER_CW
                ax = (ax - cx) * k_
                ay = (ay - CHROME_Y) * k_
            ex, ey = xy(ax, ay)
            # supersample before zoompan or rendered text shimmers through the move
            fc += (f"{src}{pre}scale={1920*UP}:{1080*UP}:flags=lanczos,"
                   f"zoompan=z='{zexpr(keys)}':x='{ex}':y='{ey}':"
                   f"d=1:s=1920x1080:fps={FPS}[sc{i}];")
        else:
            fc += f"{src}{pre}null[sc{i}];"
    fc += "".join(f"[sc{i}]" for i in range(n))+f"concat=n={n}:v=1:a=0[scrz];"
    fc += "".join(f"[c{i}]" for i in range(n))+f"concat=n={n}:v=1:a=0[cam];"
    fc += "".join(f"[a{i}]" for i in range(n))+f"concat=n={n}:v=0:a=1[aud];"
    cw,ch,cx,cy = CROP

    # Which stretches of THIS batch want the circle on the left. Clips concatenate in
    # order, so a source span maps to a batch-local span and the overlay x is one
    # expression rather than a second pass.
    left, loc = [], 0.0
    for a,b in clips:
        if is_left(a):
            if left and abs(left[-1][1]-loc) < 1e-6: left[-1][1] = loc+(b-a)
            else: left.append([loc, loc+(b-a)])
        loc += b-a
    XL, XR = MARGIN, 1920-CIRCLE_D-MARGIN
    if not left:
        ex = f"{XR}"
    elif len(left) == 1 and abs(left[0][0]) < 1e-6 and abs(left[0][1]-loc) < 1e-6:
        ex = f"{XL}"
    else:
        cond = "+".join(f"between(t,{a:.3f},{b:.3f})" for a,b in left)
        ex = f"if(gt({cond},0),{XL},{XR})"
    ey = f"H-{CIRCLE_D}-{MARGIN}"
    fc += (f"[cam]crop={cw}:{ch}:{cx}:{cy},scale={CIRCLE_D}:{CIRCLE_D},format=rgba[cs];"
           f"[2:v]format=gray[mk];[cs][mk]alphamerge[pip];"
           f"[scrz][pip]overlay=x='{ex}':y={ey}[bp];"
           f"[bp][3:v]overlay=x='{ex}':y={ey},format=yuv420p[v]")
    run(["ffmpeg","-v","error","-nostdin",
         "-ss",f"{lo}","-t",f"{hi-lo}","-i",SCREEN,
         "-ss",f"{lo}","-t",f"{hi-lo}","-i",CAMERA,
         "-i",MASK,"-i",RING,"-filter_complex",fc,
         "-map","[v]","-map","[aud]","-c:v","libx264","-preset","medium","-crf","18",
         "-c:a","pcm_s16le","-r",str(FPS),"-y",dst])
    return dst

if __name__ == "__main__":
    keeps = [(r["start"], r["end"]) for r in
             json.load(open(os.path.join(BASE,"cutplan.json")))["keepRanges"]]
    # Every overlay/zoom key MUST match a keep start. Keys are source seconds, and
    # trimming a keep's head moves that start - the key then matches nothing, the group
    # renders as bare camera, and NOTHING fails: duration is right, ffmpeg is happy.
    # This has silently eaten a graphic three times, so it is an error, not a warning.
    _starts = {round(a, 2) for a, _ in keeps}
    for _name, _d in (("CAM_OVERLAYS", CAM_OVERLAYS), ("CAM_ZOOMS", CAM_ZOOMS),
                      ("SCREEN_ZOOMS", SCREEN_ZOOMS), ("BROWSER_KEEPS", BROWSER_KEEPS),
                      ("BROWSER_CROP_X", BROWSER_CROP_X),
                      ("BLURS", BLURS)):
        _dead = [k for k in _d if round(k, 2) not in _starts]
        if _dead:
            _near = sorted(_starts, key=lambda s: min(abs(s - x) for x in _dead))[:4]
            sys.exit(f"{_name} keys match no keep start: {_dead}\n"
                     f"  nearest keep starts: {sorted(_near)}\n"
                     f"  a trimmed keep moves its start - update the key.")
    if "--minutes" in sys.argv:
        lim = float(sys.argv[sys.argv.index("--minutes")+1])*60
        acc, keep = 0.0, []
        for a,b in keeps:
            if acc >= lim: break
            keep.append((a,b)); acc += b-a
        keeps = keep

    # Group consecutive keeps by treatment so the parts concat in timeline order.
    groups, mode = [], None
    for a,b in keeps:
        m = "cam" if is_cam(a) else "scr"
        if m != mode: groups.append((m, [])); mode = m
        groups[-1][1].append((a,b))

    # Hash the plan AND the treatment config. Keying on the plan alone silently reused
    # batches rendered under a different CAMERA_SPANS, so a span moved to camera still
    # came out as screen with no error anywhere. CAM_OVERLAYS is in the signature too:
    # adding a graphics MOV to a group must invalidate that group's cached render, and
    # without it the outline overlay was written but the stale camera-only file was used.
    sig = (open(os.path.join(BASE,"cutplan.json"),"rb").read()
           + repr((CAMERA_SPANS, PIP_LEFT, CROP, CHROME_Y, sorted(BROWSER_KEEPS),
                   BROWSER_CW, sorted(BROWSER_CROP_X.items()),
                   sorted(SCREEN_ZOOMS.items()), sorted(CAM_ZOOMS.items()),
                   sorted(BLURS.items()),
                   CIRCLE_D, MARGIN,
                   sorted(CAM_OVERLAYS.items()))).encode())
    # a rebuilt MOV must also invalidate: fold in each overlay's mtime
    for _, ps in sorted(CAM_OVERLAYS.items()):
        for p in ([ps] if isinstance(ps, str) else ps):
            if os.path.exists(p): sig += str(os.path.getmtime(p)).encode()
    h = hashlib.md5(sig).hexdigest()[:8]
    globals()["WORK"] = os.path.join(OUT, f"batches-{h}")
    os.makedirs(WORK, exist_ok=True); os.makedirs(PREV, exist_ok=True)
    cam_s = sum(b-a for m,g in groups if m=="cam" for a,b in g)
    scr_s = sum(b-a for m,g in groups if m=="scr" for a,b in g)
    print(f"  {len(groups)} groups  camera {cam_s:.1f}s / screen {scr_s:.1f}s   [plan {h}]")

    jobs, ci, bi = [], 0, 0
    for m, g in groups:
        if m == "cam":
            jobs.append((render_cam, (ci, g))); ci += 1
        else:
            for i in range(0, len(g), BATCH):
                jobs.append((render_batch, (bi, g[i:i+BATCH]))); bi += 1
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        parts = list(ex.map(lambda j: j[0](j[1]), jobs))

    lst = os.path.join(WORK, "join.txt")
    open(lst,"w").write("".join(f"file '{p}'\n" for p in parts))
    if "--minutes" in sys.argv:
        dst = os.path.join(PREV, f"058-preview-{sys.argv[sys.argv.index('--minutes')+1]}min.mp4")
    else:
        dst = os.path.join(BASE, f"{NAME} - CUT.mp4")
    run(["ffmpeg","-v","error","-nostdin","-f","concat","-safe","0","-i",lst,
         "-c:v","copy","-c:a","aac","-b:a","192k","-movflags","+faststart","-y",dst])
    d = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","csv=p=0",dst],capture_output=True,text=True).stdout)
    print(f"-> {dst}  {int(d)//60}:{d%60:05.2f}")
