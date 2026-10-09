#!/usr/bin/env python3
"""Render ONLY the first 2 minutes, for iterating on the intro without touching 56 minutes.

intro (56.29s) + enough body clips to reach 120s. Writes recut/047-first2min.mp4.
Body batches are cached in recut/prev/ and reused, so repeat runs only redo the intro.
"""
import json, os, subprocess, sys

CAM   = os.path.expanduser("~/Movies/Camtasia")
BASE  = os.path.join(CAM, "047 - arcade.dev full course")
SCREEN= os.path.join(CAM, "047 - arcade.dev full course - SCREEN.mp4")
CAMERA= os.path.join(CAM, "047 - arcade.dev full course - CAMERA.mp4")
REC   = os.path.join(BASE, "recut")
PREV  = os.path.join(REC, "prev")
MASK  = os.path.join(REC, "mask_43.png")
RING  = os.path.join(REC, "ring_43.png")
CALL  = os.path.join(BASE, "overlays/movs/callouts.mov")
INTRO = os.path.join(REC, "047-intro-FULL.mp4")
OUT   = os.path.join(REC, "047-first2min.mp4")

PIP_W, PIP_H, MARGIN = 480, 360, 50
CROP = (1040, 780, 474, 170)
BODY_SECONDS = 64.0
CX, CY = 70, 742

def run(c):
    r = subprocess.run(c, capture_output=True, text=True)
    if r.returncode: sys.exit(f"FAILED {' '.join(c[:8])}\n{r.stderr[-2000:]}")

if __name__ == "__main__":
    os.makedirs(PREV, exist_ok=True)
    body = json.load(open(os.path.join(BASE,"cutplan-v2.json")))["body"]
    clips, acc = [], 0.0
    for a,b in body:
        clips.append((a,b)); acc += b-a
        if acc >= BODY_SECONDS: break

    head = os.path.join(PREV, "body-head.mp4")
    if "--rebuild-body" in sys.argv or not os.path.exists(head):
        lo = min(a for a,_ in clips)-0.5; hi = max(b for _,b in clips)+0.5
        seg, n = [], len(clips)
        for i,(a,b) in enumerate(clips):
            seg.append(f"[0:v]trim={a-lo}:{b-lo},setpts=PTS-STARTPTS[s{i}]")
            seg.append(f"[1:v]trim={a-lo}:{b-lo},setpts=PTS-STARTPTS[c{i}]")
            seg.append(f"[1:a]atrim={a-lo}:{b-lo},asetpts=PTS-STARTPTS[a{i}]")
        fc = ";".join(seg)+";"
        fc += "".join(f"[s{i}]" for i in range(n))+f"concat=n={n}:v=1:a=0[scr];"
        fc += "".join(f"[c{i}]" for i in range(n))+f"concat=n={n}:v=1:a=0[cam];"
        fc += "".join(f"[a{i}]" for i in range(n))+f"concat=n={n}:v=0:a=1[aud];"
        cw,ch,cx,cy = CROP
        fc += (f"[cam]crop={cw}:{ch}:{cx}:{cy},scale={PIP_W}:{PIP_H},format=rgba[cs];"
               f"[2:v]format=gray[mk];[cs][mk]alphamerge[pip];"
               f"[scr][pip]overlay=x=W-{PIP_W}-{MARGIN}:y=H-{PIP_H}-{MARGIN}[bp];"
               f"[bp][3:v]overlay=x=W-{PIP_W}-{MARGIN}:y=H-{PIP_H}-{MARGIN}[bp2];"
               f"[bp2][4:v]overlay=x={CX}:y={CY}:eof_action=pass,format=yuv420p[v]")
        run(["ffmpeg","-v","error","-nostdin",
             "-ss",f"{lo}","-t",f"{hi-lo}","-i",SCREEN,
             "-ss",f"{lo}","-t",f"{hi-lo}","-i",CAMERA,
             "-i",MASK,"-i",RING,"-i",CALL,
             "-filter_complex",fc,"-map","[v]","-map","[aud]",
             "-c:v","libx264","-preset","medium","-crf","18","-c:a","aac","-b:a","192k",
             "-r","30","-y",head])
        print(f"  body head rendered ({len(clips)} clips)")
    else:
        print("  body head cached (pass --rebuild-body to redo)")

    lst = os.path.join(PREV,"j.txt")
    open(lst,"w").write(f"file '{INTRO}'\nfile '{head}'\n")
    run(["ffmpeg","-v","error","-nostdin","-f","concat","-safe","0","-i",lst,
         "-c:v","libx264","-preset","fast","-crf","18","-pix_fmt","yuv420p",
         "-c:a","aac","-b:a","192k","-y",OUT])
    d=float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","csv=p=0",OUT],capture_output=True,text=True).stdout)
    print(f"-> {OUT}  {int(d)//60}:{d%60:05.2f}")
