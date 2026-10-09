#!/usr/bin/env python3
"""058 hardware beat - recut 98.4-120.0, over FULL-FRAME camera.

The screen under this stretch (src 325-355) is the teleprompter document and nothing
else, verified frame by frame. It was running as a screen+circle treatment, so for 21
seconds the viewer watched a wall of his own notes. This beat replaces that with camera
plus a built graphic.

Structure is a 4-slot list, because he says "we basically have four options" and then
only covers the first one here. The other three slots sit as dim numbered placeholders,
so the viewer can see how much is coming. Options 2-4 land later over real footage
(Hostinger at recut 120+), which is why this graphic deliberately stops after slot 1.

Cards sit RIGHT of his warm span (x 720-1130), matching the outline beat.

Beats, pinned to transcript/recut_words.json (recut seconds, not source):
   98.54  "hardware"   title HARDWARE lands
  100.95  "four"       four slots draw in, all dim
  103.35  "dedicated"  slot 1 lights: DEDICATED MACHINE
  105.13  "mini"       slot 1 subtitle: Mac mini, Mac Studio
  108.20  "run"        RUNS LOCAL MODELS chip under slot 1
  117.20               everything clears before the 119.97 cut to Hostinger

Output: overlays/movs/hardware.mov (transparent ProRes 4444)
"""
import os, subprocess, json

BASE  = os.path.expanduser("~/Movies/Camtasia/058 - hermes agent")
BUILD = os.path.join(BASE, "overlays/build/hardware")
MOVS  = os.path.join(BASE, "overlays/movs")

AT_SRC = 322.60       # source second this composition starts at (the "Okay, so let's" keep)
W, H = 1920, 1080
FPS  = 30
AC   = "#F8C000"
LX   = 1150           # right of his warm span, same column as the outline cards

OPTIONS = ["DEDICATED MACHINE", "VPS", "CLOUD MODELS", "EXISTING LAPTOP"]

# Pinned to SOURCE word times and converted through the cut plan, NOT by subtracting
# AT_SRC. The overlay's clock is group-local: if a cut ever lands inside this stretch,
# straight subtraction puts every later beat off by the removed duration and nothing
# fails. Recut seconds are worse still - they move on every cut-plan edit.
KEEPS = [(r["start"], r["end"]) for r in
         json.load(open(os.path.join(BASE, "cutplan.json")))["keepRanges"]
         if 322.0 <= r["start"] < 345.0]
DUR = round(sum(b - a for a, b in KEEPS), 2)


def src2local(t):
    acc = 0.0
    for a, b in KEEPS:
        if a <= t < b:
            return round(acc + (t - a), 2)
        acc += b - a
    raise SystemExit(f"beat at src {t} falls in a REMOVED region, re-pin it")


BEATS_SRC = dict(title=325.21,   # "hardware"
                 four=327.62,    # "four"
                 slot1=330.02,   # "dedicated"
                 sub=331.80,     # "mini"
                 chip=337.86,    # "local models"
                 clear=343.19)   # "things" - the 0.4s fade must finish inside the keep,
                                 # which ends at 344.23. Clearing on "do." (343.95) left
                                 # only 0.28s and the assert caught it.


def build():
    b = {k: src2local(v) for k, v in BEATS_SRC.items()}
    rows = []
    for i, name in enumerate(OPTIONS):
        y = 310 + i*140
        rows.append(f"""
  <div class="row" id="r{i}" style="top:{y}px">
    <div class="num">{i+1}</div>
    <div class="lab" id="l{i}">{name}</div>
  </div>""")
    tw = [
        f'tl.fromTo("#ttl",{{y:40,opacity:0}},{{y:0,opacity:1,duration:0.42,ease:"power3.out"}},{b["title"]});',
        f'tl.fromTo("#rule",{{scaleX:0}},{{scaleX:1,duration:0.5,ease:"power3.out"}},{b["title"]+0.12});',
        f'tl.fromTo(".row",{{x:50,opacity:0}},{{x:0,opacity:1,duration:0.38,stagger:0.09,ease:"power3.out"}},{b["four"]});',
        # slot 1 lights: the number fills, the label goes white and up a size
        f'tl.to("#r0 .num",{{background:"{AC}",color:"#000",duration:0.3,ease:"power2.out"}},{b["slot1"]});',
        # scale, not fontSize: animating fontSize reflows text and snaps glyphs to
        # integer pixels under the seek-by-frame capture engine. hyperframes check
        # flags this as gsap_non_transform_motion.
        f'tl.to("#l0",{{color:"#fff",scale:1.22,duration:0.3,ease:"power2.out"}},{b["slot1"]});',
        f'tl.fromTo("#sub",{{y:14,opacity:0}},{{y:0,opacity:1,duration:0.34,ease:"power3.out"}},{b["sub"]});',
        f'tl.fromTo("#chip",{{y:16,opacity:0}},{{y:0,opacity:1,duration:0.32,ease:"back.out(1.6)"}},{b["chip"]});',
        f'tl.to("#wrap",{{opacity:0,duration:0.4,ease:"power2.in"}},{b["clear"]});',
    ]
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="UTF-8"/>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Space+Mono:wght@700&display=swap" rel="stylesheet"/>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  html,body{{background:transparent;overflow:hidden}}
  body{{width:{W}px;height:{H}px;position:relative;font-family:Anton,sans-serif}}
  #wrap{{position:absolute;left:{LX}px;top:0;width:{W-LX-60}px;height:{H}px}}
  #ttl{{position:absolute;top:150px;font-size:76px;color:#fff;letter-spacing:0.01em;
    text-shadow:0 2px 20px rgba(0,0,0,0.95)}}
  #rule{{position:absolute;top:240px;width:600px;height:5px;background:{AC};
    transform-origin:left center}}
  .row{{position:absolute;left:0;display:flex;align-items:center;gap:22px}}
  .num{{width:54px;height:54px;border:3px solid rgba(255,255,255,0.45);border-radius:50%;
    display:flex;align-items:center;justify-content:center;
    font-family:"Space Mono",monospace;font-size:26px;color:rgba(255,255,255,0.55)}}
  .lab{{font-size:36px;transform-origin:left center;color:rgba(255,255,255,0.45);letter-spacing:0.01em;
    text-shadow:0 2px 18px rgba(0,0,0,0.95)}}
  /* Rows sit at 310, 450, 590, 730, each 54px tall. Slot 1's detail lines sit UNDER
     slot 1 in the 60px gap before row 2, indented to the label column (x=76) so they
     read as belonging to it. Earlier they were parked beside the row at x=420, where
     the chip wrapped to two lines and crossed the VPS row. */
  #sub{{position:absolute;left:76px;top:372px;font-family:"Space Mono",monospace;
    font-size:22px;font-weight:700;color:{AC};letter-spacing:0.04em;opacity:0;
    white-space:nowrap;text-shadow:0 2px 16px rgba(0,0,0,0.95)}}
  /* nowrap + a measured width: "RUNS LOCAL MODELS" at 22px in a 200px pill wrapped to
     two lines and grew downward into row 2. */
  #chip{{position:absolute;left:76px;top:404px;font-family:"Space Mono",monospace;
    font-size:18px;font-weight:700;letter-spacing:0.10em;color:#fff;opacity:0;
    white-space:nowrap;border:2px solid {AC};border-radius:999px;padding:6px 16px;
    text-shadow:0 2px 14px rgba(0,0,0,0.95)}}
</style></head>
<body data-composition-id="hardware" data-duration="{DUR}" data-fps="{FPS}"
      data-width="{W}" data-height="{H}">
<div id="wrap">
  <div id="ttl">HARDWARE</div>
  <div id="rule"></div>
  {''.join(rows)}
  <div id="sub">Mac mini &middot; Mac Studio</div>
  <div id="chip">RUNS LOCAL MODELS</div>
</div>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
<script>
window.__timelines = window.__timelines || {{}};
var tl = gsap.timeline({{paused:true}});
{chr(10).join('  '+x for x in tw)}
window.__timelines["hardware"] = tl;
</script>
</body></html>
"""


if __name__ == "__main__":
    os.makedirs(BUILD, exist_ok=True); os.makedirs(MOVS, exist_ok=True)
    # every beat must finish inside DUR or the tween silently never runs
    for k, v in BEATS_SRC.items():
        assert src2local(v) + 0.5 <= DUR, f"beat {k} at src {v} past DUR {DUR}"
    open(os.path.join(BUILD, "index.html"), "w").write(build())
    dst = os.path.join(MOVS, "hardware.mov")
    env = dict(os.environ, PRODUCER_BROWSER_GPU_MODE="hardware")
    subprocess.run(["hyperframes", "render", BUILD, "-o", dst, "--format", "mov",
                    "--fps", str(FPS), "--quiet"], env=env, check=True)
    d = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                              "-of","csv=p=0",dst],capture_output=True,text=True).stdout)
    print(f"-> {dst}  {d:.2f}s")
