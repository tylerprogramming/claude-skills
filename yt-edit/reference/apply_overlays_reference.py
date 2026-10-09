#!/usr/bin/env python3
"""Lay the three new opening graphics onto the finished film.

The Aug-15 re-record OVERWROTE 045 - arcade.dev - SCREEN/CAMERA.mp4, so recut_arcade.py can
no longer rebuild this cut — it would now trim from the wrong footage. The rendered FINAL is
the master. So instead of re-cutting, this overlays onto it, and only where it has to:

    head  0 -> 36.376   re-encoded with the three overlays
    tail  36.376 -> end  stream-copied, untouched

36.376 is a real keyframe in the FINAL (the next ones are 38.076 and 46.043), which is what
makes the copy possible. It also sits clear of the blur + always-on infographic at 37.85,
so nothing already in the film is re-rendered.

Overlays, all in RECUT time (SHOTS in recut_arcade.py are in SOURCE time; ANIMS are in
recut time — these match ANIMS):

    inbox.mov   5.10  email -> summary -> document, over the empty terminal black
    answer.mov  27.95 "And yes, you can."
    solo.mov    30.40 just you / your machine — the miniature of the 37.85 infographic

Output: recut/045-arcade-dev-FINAL-v2.mp4 (the original is left in place).
"""
import os, subprocess, sys

BASE = os.path.expanduser("~/Movies/Camtasia/045 - arcade.dev")
MOVS = os.path.join(BASE, "overlays", "movs")
SRC = os.path.join(BASE, "recut", "045-arcade-dev-FINAL.mp4")
OUT = os.path.join(BASE, "recut", "045-arcade-dev-FINAL-v2.mp4")
WORK = os.path.join(BASE, "recut", "ovl")

SPLIT = 36.376                  # keyframe in SRC

OVERLAYS = [
    ("inbox.mov",  5.10),
    ("answer.mov", 27.95),
    ("solo.mov",   30.40),
]


def dur_of(path):
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], capture_output=True, text=True).stdout)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"FAILED: {' '.join(cmd[:9])}...\n{r.stderr[-2500:]}")


def main():
    os.makedirs(WORK, exist_ok=True)
    head = os.path.join(WORK, "head.mp4")
    tail = os.path.join(WORK, "tail.mp4")

    # ---- head: re-encode with the overlays
    ins, fc, cur = [], [], "[0:v]"
    for i, (mov, at) in enumerate(OVERLAYS, start=1):
        ins += ["-i", os.path.join(MOVS, mov)]
        # shift the overlay onto its recut time, then gate it so it can never paint
        # outside its own window
        fc.append(f"[{i}:v]setpts=PTS-STARTPTS+{at}/TB[o{i}]")
        dur = float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", os.path.join(MOVS, mov)],
            capture_output=True, text=True).stdout)
        nxt = f"[v{i}]"
        fc.append(f"{cur}[o{i}]overlay=x=0:y=0:eof_action=pass:"
                  f"enable='between(t,{at:.3f},{at + dur:.3f})'{nxt}")
        cur = nxt

    # ---- tail FIRST, untouched.
    #
    # -ss must be asked for slightly PAST the keyframe. Requesting exactly 36.376 rounds
    # down inside ffmpeg's timebase maths and falls back to the previous keyframe at
    # 28.043, which silently duplicated 8.4s and made the film 12:09 instead of 12:00.
    run(["ffmpeg", "-v", "error", "-nostdin", "-ss", f"{SPLIT + 0.024:.3f}", "-i", SRC,
         "-c", "copy", "-avoid_negative_ts", "make_zero", "-reset_timestamps", "1",
         "-y", tail])

    # ---- head is then sized to exactly the remainder, so the join preserves the runtime
    # rather than trusting two independent seeks to agree.
    total = dur_of(SRC)
    head_t = total - dur_of(tail)

    run(["ffmpeg", "-v", "error", "-nostdin", "-i", SRC] + ins
        + ["-filter_complex", ";".join(fc),
           "-map", cur, "-map", "0:a",
           "-t", f"{head_t:.3f}",
           "-c:v", "libx264", "-preset", "medium", "-crf", "16",
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.0",
           "-c:a", "copy", "-y", head])

    # ---- join
    lst = os.path.join(WORK, "join.txt")
    with open(lst, "w") as f:
        for p in (head, tail):
            f.write(f"file '{p}'\n")
    run(["ffmpeg", "-v", "error", "-nostdin", "-f", "concat", "-safe", "0",
         "-i", lst, "-c", "copy", "-movflags", "+faststart", "-y", OUT])

    d = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", OUT], capture_output=True, text=True).stdout)
    print(f"-> {OUT}  {int(d)//60}:{d % 60:05.2f}")


if __name__ == "__main__":
    main()
