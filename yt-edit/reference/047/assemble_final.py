#!/usr/bin/env python3
"""Final assembly: callouts onto the body head, then intro + body.

The callouts only cover body 0-190s, so only that span is re-encoded; the remaining ~55
minutes is stream-copied from a real keyframe. -ss onto a keyframe rounds DOWN onto the
previous one, so we ask for keyframe+0.024 and size the head to total-tail (see
references/GOTCHAS.md).

Output: 047 - arcade.dev full course - FINAL.mp4
"""
import os, subprocess, sys

BASE = os.path.expanduser("~/Movies/Camtasia/047 - arcade.dev full course")
REC  = os.path.join(BASE, "recut")
WORK = os.path.join(REC, "asm")
INTRO= os.path.join(REC, "047-intro-FULL.mp4")
BODY = os.path.join(REC, "047-body.mp4")
CALL = os.path.join(BASE, "overlays/movs/callouts.mov")
OUT  = os.path.join(BASE, "047 - arcade.dev full course - FINAL.mp4")
CX, CY = 70, 742          # callout canvas position
COVER  = 190.0            # callouts span body 0..COVER

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: sys.exit(f"FAILED {' '.join(cmd[:9])}\n{r.stderr[-2500:]}")

def dur(p):
    return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","csv=p=0",p],capture_output=True,text=True).stdout)

def keyframes(p, lo, hi):
    out = subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries",
        "frame=key_frame,pts_time","-of","csv=p=0","-read_intervals",f"{lo}%{hi}",p],
        capture_output=True,text=True).stdout
    ks=[]
    for l in out.splitlines():
        p_=l.split(",")
        if len(p_)>=2 and p_[0]=="1":
            try: ks.append(float(p_[1]))
            except ValueError: pass
    return ks

if __name__ == "__main__":
    os.makedirs(WORK, exist_ok=True)
    ks = [k for k in keyframes(BODY, COVER, COVER+30) if k >= COVER]
    if not ks: sys.exit("no keyframe found past the callout span")
    split = ks[0]
    print(f"  body split at keyframe {split:.3f}")

    tail = os.path.join(WORK, "tail.mp4")
    run(["ffmpeg","-v","error","-nostdin","-ss",f"{split+0.024:.3f}","-i",BODY,
         "-c","copy","-avoid_negative_ts","make_zero","-reset_timestamps","1","-y",tail])
    head_t = dur(BODY) - dur(tail)

    head = os.path.join(WORK, "head.mp4")
    run(["ffmpeg","-v","error","-nostdin","-i",BODY,"-i",CALL,
         "-filter_complex",f"[0:v][1:v]overlay=x={CX}:y={CY}:eof_action=pass[v]",
         "-map","[v]","-map","0:a","-t",f"{head_t:.3f}",
         "-c:v","libx264","-preset","medium","-crf","17","-pix_fmt","yuv420p",
         "-profile:v","high","-level","4.0","-c:a","copy","-y",head])

    bodyc = os.path.join(WORK, "body-callouts.mp4")
    lst = os.path.join(WORK,"b.txt"); open(lst,"w").write(f"file '{head}'\nfile '{tail}'\n")
    run(["ffmpeg","-v","error","-nostdin","-f","concat","-safe","0","-i",lst,
         "-c","copy","-y",bodyc])

    # intro + body. Re-encode the join so the two encoders' params cannot disagree.
    lst2 = os.path.join(WORK,"f.txt")
    open(lst2,"w").write(f"file '{INTRO}'\nfile '{bodyc}'\n")
    run(["ffmpeg","-v","error","-nostdin","-f","concat","-safe","0","-i",lst2,
         "-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p",
         "-c:a","aac","-b:a","192k","-movflags","+faststart","-y",OUT])
    d = dur(OUT)
    print(f"-> {OUT}\n   {int(d)//60}:{d%60:05.2f}")
