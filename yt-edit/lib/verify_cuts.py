#!/usr/bin/env python3
"""Measure how much real speech a keep-plan throws away, WITHOUT trusting the transcript.

Whisper stretches word timings across pauses and hallucinates over long silences, so
"words that fall in cut regions" over-reports badly. This looks at the audio instead:
any sustained run of above-threshold frames sitting inside a cut region is speech being
lost, and the total of those runs is the number that matters.
"""
import array, json, math, subprocess, sys

SRC = "/Users/tylerreed/Movies/Camtasia/045 - arcade.dev - CAMERA.mp4"
SR, HOP = 8000, 0.05
LOUD = -40.0        # comfortably above the 0.005 (-46dB) gate, well under speech (-22dB)
MINRUN = 0.30       # a syllable; shorter than this is a click or a breath

p = subprocess.run(["ffmpeg", "-v", "error", "-i", SRC, "-vn", "-ac", "1",
                    "-ar", str(SR), "-f", "s16le", "-"], capture_output=True)
pcm = array.array("h"); pcm.frombytes(p.stdout)
n = int(SR * HOP)
db = []
for i in range(0, len(pcm) - n, n):
    fr = pcm[i:i + n]
    rms = math.sqrt(sum(s * s for s in fr) / len(fr)) or 1
    db.append(20 * math.log10(rms / 32768.0))

for path in sys.argv[1:]:
    kr = [(r["start"], r["end"]) for r in json.load(open(path))["keepRanges"]]
    kept = [False] * len(db)
    for a, b in kr:
        for i in range(int(a / HOP), min(int(b / HOP) + 1, len(db))):
            kept[i] = True
    runs, run = [], None
    for i, d in enumerate(db):
        if d > LOUD and not kept[i]:
            if run is None: run = i
        else:
            if run is not None and (i - run) * HOP >= MINRUN:
                runs.append((run * HOP, i * HOP))
            run = None
    lost = sum(e - s for s, e in runs)
    print(f"{path}: {len(runs)} runs of >{LOUD}dB audio inside cuts, {lost:.1f}s lost")
    for s, e in sorted(runs, key=lambda r: r[1] - r[0], reverse=True)[:5]:
        print(f"    {s:8.2f}-{e:8.2f}  ({e - s:.2f}s)")
