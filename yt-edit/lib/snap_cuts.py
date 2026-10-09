#!/usr/bin/env python3
"""Snap cut boundaries to the quietest instant nearby, measured from the audio.

Hand-placed boundaries land mid-word and clip syllables. Nudging them with the transcript
does not generalise: Whisper stretches some words across pauses (one "about." here spans
ten seconds), so its word ends are not reliable edges. Frame energy is.

For each boundary, search +/-WIN seconds for the lowest-RMS 20ms frame and move there.
"""
import array, math, subprocess

SRC = "/Users/tylerreed/Movies/Camtasia/045 - arcade.dev - CAMERA.mp4"
SR, HOP, WIN = 8000, 0.02, 0.45
CUTS = [(834.64, 867.57), (895.39, 905.87), (1164.86, 1192.39), (1793.26, 1892.33),
        (2653.14, 2720.89), (3926.50, 3949.35), (1399.79, 1400.99), (3219.90, 3220.95)]

lo = min(min(c) for c in CUTS) - 2
hi = max(max(c) for c in CUTS) + 2
p = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(lo), "-t", str(hi - lo),
                    "-i", SRC, "-vn", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                   capture_output=True)
pcm = array.array("h"); pcm.frombytes(p.stdout)
n = int(SR * HOP)
db = []
for i in range(0, len(pcm) - n, n):
    fr = pcm[i:i + n]
    rms = math.sqrt(sum(s * s for s in fr) / len(fr)) or 1
    db.append(20 * math.log10(rms / 32768.0))


def snap(t):
    c = int((t - lo) / HOP)
    w = int(WIN / HOP)
    best, bi = 1e9, c
    for i in range(max(0, c - w), min(len(db), c + w + 1)):
        if db[i] < best:
            best, bi = db[i], i
    return lo + bi * HOP, best


print("    original          snapped        dB     shift")
out = []
for a, b in CUTS:
    sa, da = snap(a); sb, dbv = snap(b)
    out.append((sa, sb))
    print(f"  ({a:8.2f},{b:8.2f}) -> ({sa:8.2f},{sb:8.2f})  {da:6.1f}/{dbv:6.1f}  "
          f"{sa-a:+.2f}/{sb-b:+.2f}")
print("\nCUTS = [")
for sa, sb in sorted(out):
    print(f"    ({sa:.2f}, {sb:.2f}),")
print("]")
