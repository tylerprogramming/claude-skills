#!/usr/bin/env python3
"""RMS percentile profile of the camera audio, to pick `hyperframes silence --noise`.

The right threshold swings by 40dB between Tyler's shoots — the "17 claude code skills"
room tone sat near -26dB, "045 - arcade.dev" near -72dB — and carrying the wrong one over
silently eats speech. Always measure before recutting.
Floor is the p10-p50 cluster, speech is p80+; put the threshold between them.
"""
import array, math, subprocess, sys

SRC = sys.argv[1]
SR, HOP = 8000, 0.05
p = subprocess.run(["ffmpeg", "-v", "error", "-i", SRC, "-vn", "-ac", "1",
                    "-ar", str(SR), "-f", "s16le", "-"], capture_output=True)
pcm = array.array("h"); pcm.frombytes(p.stdout)
n = int(SR * HOP)
db = []
for i in range(0, len(pcm) - n, n):
    fr = pcm[i:i + n]
    rms = math.sqrt(sum(s * s for s in fr) / len(fr)) or 1
    db.append(20 * math.log10(rms / 32768.0))
db.sort()
print(f"{len(db)} frames ({len(db) * HOP:.0f}s)")
for pct in (1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 99):
    v = db[int(len(db) * pct / 100)]
    print(f"  p{pct:<3} {v:7.1f} dB   (amplitude {10 ** (v / 20):.4f})")
