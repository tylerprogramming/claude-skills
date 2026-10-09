#!/usr/bin/env python3
"""Find retakes: explicit restart markers, then repeated phrases in RECUT time.

`hyperframes duplicates` misses these — at usable thresholds the reworded retake does not
match, and at loose ones it floods with consecutive fragments of one sentence. What works
is reading the transcript for repeated beat structure, so this surfaces the candidates.

Two passes:
  1. restart markers he actually says out loud ("start that over", "let me redo it"...)
  2. n-gram repeats within a short window, longest first
"""
import json, re, sys, bisect

BASE = "."
NOISE = "sweep-0.005.json"
SLIVER, ISOLATED, MIN_KEEP = 0.60, 3.00, 0.10

MARKERS = ["start over", "start that over", "start again", "do that again", "try again",
           "let me redo", "redo that", "scratch that", "never mind", "nevermind",
           "hold on", "wait a", "let me restart", "restart that", "one more time",
           "actually let me", "let me just do"]


def prune(ks):
    out = []
    for i, (a, b) in enumerate(ks):
        if b - a < SLIVER:
            before = a - ks[i - 1][1] if i > 0 else 1e9
            after = ks[i + 1][0] - b if i + 1 < len(ks) else 1e9
            if min(before, after) >= ISOLATED:
                continue
        out.append((a, b))
    return out


ks = [(r["start"], r["end"]) for r in json.load(open(NOISE))["keepRanges"]
      if r["end"] - r["start"] >= MIN_KEEP]
ks = prune(ks)
starts = [a for a, b in ks]
off, acc = [], 0.0
for a, b in ks:
    off.append(acc); acc += b - a
print(f"keeps: {len(ks)} ranges, {acc:.1f}s = {int(acc//60)}:{acc%60:04.1f}\n")


def to_recut(t):
    i = bisect.bisect_right(starts, t) - 1
    if i < 0: return None
    a, b = ks[i]
    return off[i] + (t - a) if t <= b else None


W = [dict(t=x["text"], src=x["start"], r=r)
     for x in json.load(open("transcript/transcript-full.json"))
     if (r := to_recut(x["start"])) is not None]
json.dump(W, open("transcript/recut_words.json", "w"))

def hms(t): return f"{int(t)//60}:{t%60:05.2f}"

txt = " ".join(w["t"] for w in W).lower()
print("=== explicit restart markers")
for m in MARKERS:
    for mo in re.finditer(re.escape(m), txt):
        upto = txt[:mo.start()].count(" ")
        if upto < len(W):
            print(f"  {hms(W[upto]['r']):>9}  ...{' '.join(x['t'] for x in W[max(0,upto-8):upto+9])}")

print("\n=== repeated phrases (recut time), longest first")
norm = [re.sub(r"[^a-z0-9]", "", w["t"].lower()) for w in W]
seen, hits = set(), []
for L in (6, 5, 4, 3):
    for i in range(len(W) - L):
        a = norm[i:i + L]
        if any(not x for x in a) or i in seen: continue
        for k in range(i + L, min(i + L + 10, len(W) - L + 1)):
            if norm[k:k + L] == a and W[k]["r"] - W[i]["r"] < 9:
                hits.append((W[i]["r"], W[k]["r"], W[k + L - 1]["r"], L,
                             " ".join(W[j]["t"] for j in range(i, i + L))))
                seen.update(range(i, k + L))
                break
hits.sort(key=lambda h: (-h[3], h[0]))
for r1, r2, r3, L, s in hits[:60]:
    print(f"  {hms(r1):>9}  1st@{r1:7.1f}  2nd@{r2:7.1f}-{r3:7.1f}  [{L}w] \"{s}\"")
print(f"\n({len(hits)} repeats total)")
