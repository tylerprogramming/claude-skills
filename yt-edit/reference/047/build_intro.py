#!/usr/bin/env python3
"""Assemble the intro: camera cut -> synthetic montage over the first 11.57s -> graphics.

Regenerates from cutplan-v2.json every time, so nothing depends on leftover scratch files.

  build_intro.py            # rebuild the intro only
  GFX_FONT=Anton build_intro.py   # (after re-running the graphics builders with the same var)
"""
import json, os, subprocess, sys

CAM   = os.path.expanduser("~/Movies/Camtasia")
BASE  = os.path.join(CAM, "047 - arcade.dev full course")
CAMERA= os.path.join(CAM, "047 - arcade.dev full course - CAMERA.mp4")
REC   = os.path.join(BASE, "recut")
CUT   = os.path.join(REC, "047-intro-cut.mp4")
OUT   = os.path.join(REC, "047-intro-FULL.mp4")
MONT  = os.path.join(BASE, "overlays/montage.mp4")
# Cinematic establishing shot (Seedance) over "this is Claude, running on my real
# accounts" - Nate opens on b-roll before any UI. Two earlier generations were
# rejected: v1 produced a hooded figure in a dark room (cybercrime read, wrong for a
# video about doing this safely), v2 put candlestick trading charts on the monitors.
COLD  = os.path.join(BASE, "overlays/coldopen.mp4")
# "even one running on a server every morning while you sleep" - the only line in
# the intro that is a MOOD rather than a fact, and the one place AI video beats a
# graphic. Empty room at dawn; the HUD's scheduled badge lights over it.
DAWN  = os.path.join(BASE, "overlays/dawn.mp4")
DAWN_AT = 29.29
NOENG = os.path.join(BASE, "overlays/noeng.mp4")
NOENG_AT = 35.80
WALL  = os.path.join(BASE, "overlays/wall.mp4")
WALL_AT = 15.55
AUTH  = os.path.join(BASE, "overlays/movs/auth.mov")
AUTH_AT = 33.00
HARD  = os.path.join(BASE, "overlays/hardpart.mp4")
HARD_AT = 45.90
GFX   = os.path.join(BASE, "overlays/movs/intro-gfx.mov")
FACE_AT = 11.57      # montage covers everything before this; face reveals on "six apps"

def run(c):
    r = subprocess.run(c, capture_output=True, text=True)
    if r.returncode: sys.exit(f"FAILED {' '.join(c[:8])}\n{r.stderr[-2000:]}")

if __name__ == "__main__":
    os.makedirs(REC, exist_ok=True)
    K = json.load(open(os.path.join(BASE,"cutplan-v2.json")))["intro"]
    # A slow push-in or pull-out on every camera clip - the frame should never sit still on
    # a face. Safe here in a way it was NOT on the synthetic scenes: zoompan rounds its crop
    # window to whole pixels, which shimmers on crisp UI text but is invisible on
    # photographic footage. Supersampled 2x anyway. (z0, z1) per clip, alternating.
    # (z0, z1) is a plain linear ramp; a list of (t, z) is a keyframed move, used where a
    # zoom has to land on a specific WORD rather than drift across the whole clip.
    ZOOM = [
        # clip 0: hold through the face reveal, then PUNCH IN right after "six apps"
        # (ends 12.30) so it lands on "never" at 12.67.
        [(0.00,1.00),(11.40,1.02),(12.28,1.02),(12.66,1.14),(14.36,1.16)],
        (1.07,1.00),
        # clip 2 (recut 22.91-32.52): stepped in/out rather than one drift. Sharp ~0.3s
        # moves between holds, each on a word. Local time = recut - 22.91. The last ~3.4s
        # is under the server b-roll, so the moves live in the visible first 6.4s.
        [(0.00,1.00),(1.12,1.00),(1.40,1.11),   # 24.31  punch IN on "you'll have"
         (3.84,1.11),(4.12,0.99),               # 27.03  snap OUT as the brief fills
         (9.61,1.02)],                          # then hold - the 28.37 punch repeated the
                                                # 24.31 one and read as a tic, so it is out
        (1.08,1.01),
        (1.00,1.06),(1.06,1.00),(1.00,1.05),(1.02,1.09)]

    def zexpr(spec, dur, fps=30):
        """zoompan z-expression: linear ramp, or piecewise-linear across keyframes."""
        if not isinstance(spec, list):
            z0, z1 = spec
            n = max(1, int(round(dur*fps)) - 1)
            return f"{z0}+({z1}-{z0})*on/{n}"
        kf = [(int(round(t*fps)), z) for t, z in spec]
        e = f"{kf[-1][1]}"
        for (f0, z0), (f1, z1) in reversed(list(zip(kf, kf[1:]))):
            span = max(1, f1 - f0)
            e = f"if(lt(on,{f1}),{z0}+({z1}-{z0})*(on-{f0})/{span},{e})"
        return e

    seg, lbl = [], []
    for i,(a,b) in enumerate(K):
        z = zexpr(ZOOM[i % len(ZOOM)], b-a)
        seg.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,"
                   f"scale=3840:2160:flags=bicubic,"
                   f"zoompan=z='{z}'"
                   f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                   f":d=1:s=1920x1080:fps=30,setsar=1[v{i}]")
        seg.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS[a{i}]")
        lbl.append(f"[v{i}][a{i}]")
    fc = ";".join(seg)+";"+"".join(lbl)+f"concat=n={len(K)}:v=1:a=1[v][a]"
    run(["ffmpeg","-v","error","-nostdin","-i",CAMERA,"-filter_complex",fc,
         "-map","[v]","-map","[a]","-c:v","libx264","-preset","medium","-crf","18",
         "-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-r","30","-y",CUT])

    # inputs: 0 camera cut | 1 montage | 2 cold open | 3 wall | 4 auth | 5 hard-part | 6 overlay
    run(["ffmpeg","-v","error","-nostdin","-i",CUT,"-i",MONT,"-i",COLD,
         "-i",WALL,"-i",AUTH,"-i",HARD,"-i",DAWN,"-i",NOENG,"-i",GFX,
         "-filter_complex",
         "[1:v]setpts=PTS-STARTPTS[mo];"
         "[2:v]setpts=PTS-STARTPTS[co];"
         f"[3:v]setpts=PTS-STARTPTS+{WALL_AT}/TB[wa];"
         f"[4:v]setpts=PTS-STARTPTS+{AUTH_AT}/TB[au];"
         f"[5:v]setpts=PTS-STARTPTS+{HARD_AT}/TB[hp];"
         f"[0:v][mo]overlay=x=0:y=0:eof_action=pass:enable='lt(t,{FACE_AT})'[b1];"
         "[b1][co]overlay=x=0:y=0:eof_action=pass:enable='lt(t,3.34)'[b1c];"
         f"[b1c][wa]overlay=x=0:y=0:eof_action=pass:enable='between(t,{WALL_AT},{WALL_AT}+7.50)'[b2];"
         f"[b2][au]overlay=x=0:y=0:eof_action=pass:enable='between(t,{AUTH_AT},{AUTH_AT}+12.10)'[b3];"
         f"[b3][hp]overlay=x=0:y=0:eof_action=pass:enable='between(t,{HARD_AT},{HARD_AT}+4.20)'[b4];"
         f"[6:v]setpts=PTS-STARTPTS+{DAWN_AT}/TB[dw];"
         f"[b4][dw]overlay=x=0:y=0:eof_action=pass:enable='between(t,{DAWN_AT},{DAWN_AT}+3.44)'[b5];"
         f"[7:v]setpts=PTS-STARTPTS+{NOENG_AT}/TB[ne];"
         f"[b5][ne]overlay=x=0:y=0:eof_action=pass:enable='between(t,{NOENG_AT},{NOENG_AT}+2.68)'[b6];"
         "[b6][8:v]overlay=x=0:y=0:eof_action=pass[v]",
         "-map","[v]","-map","0:a","-c:v","libx264","-preset","medium","-crf","17",
         "-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-y",OUT])
    d=float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","csv=p=0",OUT],capture_output=True,text=True).stdout)
    print(f"-> {OUT}  {d:.2f}s  (font {os.environ.get('GFX_FONT','Outfit')})")
