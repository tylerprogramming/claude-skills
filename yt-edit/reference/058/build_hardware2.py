#!/usr/bin/env python3
"""058 hardware options 3 and 4 - src 407.60-433.97, over FULL-FRAME camera.

Continuation of build_hardware.py. Option 1 (dedicated machine) is covered before the
Hostinger walkthrough; option 2 (VPS) is the Hostinger walkthrough itself, on screen.
When he says "third option" the screen is still the Hostinger homepage sitting idle, so
this stretch goes back to camera and the same 4-slot list returns with slots 3 and 4
lighting in turn.

The list rebuilds in its finished state - slots 1 and 2 already marked done, no
re-animation of what the viewer has seen - so it reads as the same object returning
rather than a new graphic.

Beats pinned to SOURCE word times (transcript/source_words.json):
  407.60  list returns, slots 1-2 already done
  408.10  "third option"      slot 3 lights
  409.85  "spare laptop"      slot 3 subtitle
  415.00  "local models"      NO LOCAL MODELS chip, struck
  423.50  "of course"         slot 4 lights: the computer you already have
  428.50  "24-7"              RUNNING 24/7 chip
  432.80                      clears before the 433.97 cut

Output: overlays/movs/hardware2.mov (transparent ProRes 4444)
"""
import os, subprocess, json

BASE  = os.path.expanduser("~/Movies/Camtasia/058 - hermes agent")
BUILD = os.path.join(BASE, "overlays/build/hardware2")
MOVS  = os.path.join(BASE, "overlays/movs")

AT_SRC = 407.60
W, H   = 1920, 1080
FPS    = 30
AC     = "#F8C000"
LX     = 1150

OPTIONS = ["DEDICATED MACHINE", "VPS", "SPARE LAPTOP", "THE ONE YOU HAVE"]

# This beat spans TWO keeps with a cut between them (src 421.90 -> 426.47). The overlay
# is composited over the concatenated group, so its clock is GROUP-LOCAL, not source.
# Pinning in source seconds and subtracting AT_SRC would put every beat after the cut
# 4.57s late, with nothing failing. src2local() walks the cut plan instead.
KEEPS = [(r["start"], r["end"]) for r in
         json.load(open(os.path.join(BASE, "cutplan.json")))["keepRanges"]
         if 407.0 <= r["start"] < 434.5]
DUR = round(sum(b - a for a, b in KEEPS), 2)


def src2local(t):
    acc = 0.0
    for a, b in KEEPS:
        if a <= t < b:
            return round(acc + (t - a), 2)
        acc += b - a
    raise SystemExit(f"beat at src {t} falls in a REMOVED region, re-pin it")


BEATS_SRC = dict(back=407.70,    # the list returns
                 slot3=407.91,   # "option"
                 sub3=409.28,    # "spare"
                 chip3=414.57,   # "local models"
                 slot4=427.76,   # "of course" - after the cut
                 chip4=432.96,   # "24-7"
                 clear=433.40)   # clears before the 433.97 cut


def build():
    b = {k: src2local(v) for k, v in BEATS_SRC.items()}
    rows = []
    for i, name in enumerate(OPTIONS):
        y = 310 + i*140
        done = "done" if i < 2 else ""
        rows.append(f"""
  <div class="row {done}" id="r{i}" style="top:{y}px">
    <div class="num" id="n{i}">{i+1}</div>
    <div class="lab" id="l{i}">{name}</div>
  </div>""")
    tw = [
        # the list returns as one object, already carrying its history
        f'tl.fromTo("#wrap",{{x:60,opacity:0}},{{x:0,opacity:1,duration:0.42,ease:"power3.out"}},{b["back"]});',
        f'tl.to("#n2",{{background:"{AC}",color:"#000",borderColor:"{AC}",duration:0.3,ease:"power2.out"}},{b["slot3"]});',
        f'tl.to("#l2",{{color:"#fff",scale:1.18,duration:0.3,ease:"power2.out"}},{b["slot3"]});',
        f'tl.fromTo("#sub3",{{y:14,opacity:0}},{{y:0,opacity:1,duration:0.34,ease:"power3.out"}},{b["sub3"]});',
        f'tl.fromTo("#chip3",{{y:16,opacity:0}},{{y:0,opacity:1,duration:0.32,ease:"back.out(1.6)"}},{b["chip3"]});',
        f'tl.fromTo("#strike",{{scaleX:0}},{{scaleX:1,duration:0.34,ease:"power3.inOut"}},{b["chip3"]+0.34});',
        # slot 3 hands off to slot 4 and becomes DONE, not pending. Reverting it to the
        # dim white pending style left slot 3 as the only covered option without a
        # yellow ring while 1 and 2 kept theirs.
        f'tl.to("#l2",{{color:"rgba(255,255,255,0.30)",scale:1,duration:0.3}},{b["slot4"]});',
        f'tl.to("#n2",{{background:"transparent",color:"{AC}",borderColor:"{AC}",duration:0.3}},{b["slot4"]});',
        f'tl.to("#sub3",{{opacity:0,duration:0.25}},{b["slot4"]});',
        f'tl.to("#chip3w",{{opacity:0,duration:0.25}},{b["slot4"]});',
        f'tl.to("#n3",{{background:"{AC}",color:"#000",borderColor:"{AC}",duration:0.3,ease:"power2.out"}},{b["slot4"]});',
        f'tl.to("#l3",{{color:"#fff",scale:1.18,duration:0.3,ease:"power2.out"}},{b["slot4"]});',
        f'tl.fromTo("#chip4",{{y:16,opacity:0}},{{y:0,opacity:1,duration:0.32,ease:"back.out(1.6)"}},{b["chip4"]});',
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
  #rule{{position:absolute;top:240px;width:600px;height:5px;background:{AC}}}
  .row{{position:absolute;left:0;display:flex;align-items:center;gap:22px}}
  .num{{width:54px;height:54px;border:3px solid rgba(255,255,255,0.45);border-radius:50%;
    display:flex;align-items:center;justify-content:center;
    font-family:"Space Mono",monospace;font-size:26px;color:rgba(255,255,255,0.55)}}
  .lab{{font-size:36px;color:rgba(255,255,255,0.45);letter-spacing:0.01em;
    transform-origin:left center;text-shadow:0 2px 18px rgba(0,0,0,0.95)}}
  /* slots already covered read as done: dim, but ticked rather than pending */
  .done .num{{border-color:{AC};color:{AC}}}
  .done .lab{{color:rgba(255,255,255,0.30)}}
  /* Rows sit at 310, 450, 590, 730. Slot 3's detail lines sit UNDER row 3 in the gap
     before row 4, indented to the label column, matching build_hardware.py. Parked
     beside the row at x=420 the chip wrapped and crossed into row 4. */
  #sub3{{position:absolute;left:76px;top:652px;font-family:"Space Mono",monospace;
    font-size:22px;font-weight:700;color:{AC};letter-spacing:0.04em;opacity:0;
    white-space:nowrap;text-shadow:0 2px 16px rgba(0,0,0,0.95)}}
  #chip3w{{position:absolute;left:76px;top:684px}}
  #chip3{{position:relative;display:inline-block;font-family:"Space Mono",monospace;
    font-size:18px;font-weight:700;letter-spacing:0.10em;color:#fff;opacity:0;
    white-space:nowrap;border:2px solid rgba(255,255,255,0.5);border-radius:999px;
    padding:6px 16px;text-shadow:0 2px 14px rgba(0,0,0,0.95)}}
  /* the strike sits ON the x-height midline and UNDER the glyphs, never over them */
  #strike{{position:absolute;left:12px;top:19px;width:calc(100% - 24px);height:4px;
    background:{AC};transform-origin:left center;z-index:1}}
  #chip3 span{{position:relative;z-index:2}}
  /* slot 4 is the last row, so its chip sits BESIDE the label - there is no row below
     to clear, and below y=784 it would run off the safe area. */
  #chip4{{position:absolute;left:76px;top:800px;font-family:"Space Mono",monospace;
    font-size:18px;font-weight:700;letter-spacing:0.10em;color:#fff;opacity:0;
    white-space:nowrap;border:2px solid {AC};border-radius:999px;padding:6px 16px;
    text-shadow:0 2px 14px rgba(0,0,0,0.95)}}
</style></head>
<body data-composition-id="hardware2" data-duration="{DUR}" data-fps="{FPS}"
      data-width="{W}" data-height="{H}">
<div id="wrap">
  <div id="ttl">HARDWARE</div>
  <div id="rule"></div>
  {''.join(rows)}
  <div id="sub3">Any spare machine</div>
  <div id="chip3w"><div id="chip3"><span>NO LOCAL MODELS</span><div id="strike"></div></div></div>
  <div id="chip4">RUNNING 24/7</div>
</div>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
<script>
window.__timelines = window.__timelines || {{}};
var tl = gsap.timeline({{paused:true}});
{chr(10).join('  '+x for x in tw)}
window.__timelines["hardware2"] = tl;
</script>
</body></html>
"""


if __name__ == "__main__":
    os.makedirs(BUILD, exist_ok=True); os.makedirs(MOVS, exist_ok=True)
    for k, v in BEATS_SRC.items():
        assert src2local(v) + 0.5 <= DUR, f"beat {k} at src {v} past DUR {DUR}"
    open(os.path.join(BUILD, "index.html"), "w").write(build())
    dst = os.path.join(MOVS, "hardware2.mov")
    env = dict(os.environ, PRODUCER_BROWSER_GPU_MODE="hardware")
    subprocess.run(["hyperframes", "render", BUILD, "-o", dst, "--format", "mov",
                    "--fps", str(FPS), "--quiet"], env=env, check=True)
    d = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                              "-of","csv=p=0",dst],capture_output=True,text=True).stdout)
    print(f"-> {dst}  {d:.2f}s")
