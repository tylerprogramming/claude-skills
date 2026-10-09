#!/usr/bin/env python3
"""047 body recut - everything after the new intro, SCREEN + rectangular camera PIP.

The Aug-18 re-export prepended a ~164s intro to the same body. The v1 hand cuts were
ported forward through a fitted map (new = 0.99964488*old + 164.804, accurate to 24ms -
the offset DRIFTS, it is not a constant, because the new export runs ~0.036% faster).
Cut plan lives in cutplan-v2.json; ported cuts and their v1 comments in ported_cuts.json.

Camera treatment changed this pass: Tyler asked for a rounded RECTANGLE instead of the
circle. 480x360 (4:3) with a 5px radius and a 4px white ring, 50px inset bottom-right.
4:3 rather than 16:9 because the 047 framing is tight - measured warm-pixel span x 800-1188
across six frames - so a 16:9 box leaves him floating with dead air either side.

Batches of 30, 3 workers, PCM intermediates, concat demuxer: the video encodes once.

  recut_body.py                 # whole body
  recut_body.py --minutes 3     # first 3 minutes, for review
"""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

CAM   = os.path.expanduser("~/Movies/Camtasia")
BASE  = os.path.join(CAM, "047 - arcade.dev full course")
SCREEN= os.path.join(CAM, "047 - arcade.dev full course - SCREEN.mp4")
CAMERA= os.path.join(CAM, "047 - arcade.dev full course - CAMERA.mp4")
OUT   = os.path.join(BASE, "recut")
WORK  = os.path.join(OUT, "batches")
MASK  = os.path.join(OUT, "mask_43.png")
RING  = os.path.join(OUT, "ring_43.png")

PIP_W, PIP_H = 480, 360
MARGIN  = 50
CROP    = (1040, 780, 474, 170)     # w,h,x,y - head+shoulders, 4:3
BATCH   = 30
WORKERS = 3
FPS     = 30

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"FAILED: {' '.join(cmd[:10])}\n{r.stderr[-2500:]}")

def render_batch(args):
    idx, clips = args
    dst = os.path.join(WORK, f"b{idx:03d}.mov")
    if os.path.exists(dst):
        return dst
    lo = min(a for a, b in clips) - 0.5
    hi = max(b for a, b in clips) + 0.5
    seg, av = [], []
    for i, (a, b) in enumerate(clips):
        seg.append(f"[0:v]trim={a-lo}:{b-lo},setpts=PTS-STARTPTS[s{i}]")
        seg.append(f"[1:v]trim={a-lo}:{b-lo},setpts=PTS-STARTPTS[c{i}]")
        seg.append(f"[1:a]atrim={a-lo}:{b-lo},asetpts=PTS-STARTPTS[a{i}]")
        av.append(f"[s{i}][c{i}][a{i}]")
    n = len(clips)
    fc = ";".join(seg) + ";"
    fc += "".join(f"[s{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[scr];"
    fc += "".join(f"[c{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[cam];"
    fc += "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[aud];"
    cw, ch, cx, cy = CROP
    fc += (f"[cam]crop={cw}:{ch}:{cx}:{cy},scale={PIP_W}:{PIP_H},format=rgba[cs];"
           f"[2:v]format=gray[mk];[cs][mk]alphamerge[pip];"
           f"[scr][pip]overlay=x=W-{PIP_W}-{MARGIN}:y=H-{PIP_H}-{MARGIN}[bp];"
           f"[bp][3:v]overlay=x=W-{PIP_W}-{MARGIN}:y=H-{PIP_H}-{MARGIN},format=yuv420p[v]")
    run(["ffmpeg", "-v", "error", "-nostdin",
         "-ss", f"{lo}", "-t", f"{hi-lo}", "-i", SCREEN,
         "-ss", f"{lo}", "-t", f"{hi-lo}", "-i", CAMERA,
         "-i", MASK, "-i", RING,
         "-filter_complex", fc, "-map", "[v]", "-map", "[aud]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-c:a", "pcm_s16le", "-r", str(FPS), "-y", dst])
    return dst

if __name__ == "__main__":
    body = json.load(open(os.path.join(BASE, "cutplan-v2.json")))["body"]
    if "--minutes" in sys.argv:
        lim = float(sys.argv[sys.argv.index("--minutes") + 1]) * 60
        acc, keep = 0.0, []
        for a, b in body:
            keep.append((a, b)); acc += b - a
            if acc >= lim: break
        body = keep
    os.makedirs(WORK, exist_ok=True)
    batches = [(i // BATCH, body[i:i+BATCH]) for i in range(0, len(body), BATCH)]
    print(f"  {len(body)} clips, {sum(b-a for a,b in body)/60:.1f} min, {len(batches)} batches")
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        parts = list(ex.map(render_batch, batches))
    lst = os.path.join(WORK, "join.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    dst = os.path.join(OUT, "047-body.mp4")
    run(["ffmpeg", "-v", "error", "-nostdin", "-f", "concat", "-safe", "0", "-i", lst,
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-y", dst])
    d = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","csv=p=0",dst],capture_output=True,text=True).stdout)
    print(f"-> {dst}  {int(d)//60}:{d%60:05.2f}")
