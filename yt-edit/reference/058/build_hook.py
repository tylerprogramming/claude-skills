#!/usr/bin/env python3
"""058 hook graphics - recut 0.00-17.53, ONE transparent composition.

One timeline rather than four MOVs so every beat shares a clock and nothing drifts at an
overlay boundary. Every beat is pinned to a word measured off the DELIVERED cut
(transcript/recut_words.json), not to a stated time.

Layout: this stretch is full-frame CAMERA and he sits centred, warm-pixel span measured
x 720-1130 across the first 18s. So everything lives in the left band (x 90-660) and
nothing needs a plate - minimal chrome, text and line only, no panels.

Accent #F8C000 is the Hermes mark's own yellow, sampled off the app capture at src 520.

Registry components used (not hand-built):
  bottom-up-letters       overlays/build/bottom  - the title lockup
  dynamic-grid            overlays/build/dyng    - the ground under the desktop insert

Beats, pinned:
   0.17  "agent"        title lockup rises, letters stagger
   2.58  "Setting up"   title clears
   5.83  "terrible"     TERRIBLE TIME lands
   8.76  "sustainable"  strike draws through it, SUSTAINABLE fades up under
  10.82  "improve"      BUILD ON TOP chip
  11.80  "self"         SELF-IMPROVE chip, accent
  13.62  "day"          everything clears before the 13.97 cut to "weeks"

Output: overlays/movs/hook.mov (transparent ProRes 4444, 17.63s = 0.10 spare tail)
"""
import os, re, subprocess

BASE  = os.path.expanduser("~/Movies/Camtasia/058 - hermes agent")
BUL   = os.path.join(BASE, "overlays/build/bottom/compositions/components/bottom-up-letters.html")
GRD   = os.path.join(BASE, "overlays/build/dyng/compositions/components/dynamic-grid.html")
BUILD = os.path.join(BASE, "overlays/build/hook")
MOVS  = os.path.join(BASE, "overlays/movs")

DUR  = 17.63          # 0.10 of tail past the 17.53 cut, never displayed
W, H = 1920, 1080
FPS  = 30
AC   = "#F8C000"      # Hermes yellow, sampled from the app
LX   = 96             # left safe band; his warm span starts at x=720


def grab(path, tag):
    m = re.search(rf"<{tag}\b.*?</{tag}>", open(path).read(), re.S)
    if not m:
        raise SystemExit(f"no <{tag}> in {path}")
    return m.group(0)


def build():
    el, tw = [], []

    # ---- 0.17 "agent": the title lockup. Letters rise (bottom-up-letters), the rule
    # under it wipes in, then the whole thing clears before he starts the real line.
    el.append('<div id="title">'
              '<div id="t1" class="hf-bottom-up-letters">HERMES</div>'
              '<div id="t2" class="hf-bottom-up-letters">AGENT</div>'
              '<div id="t3" class="hf-bottom-up-letters">SETUP GUIDE</div>'
              '<u id="trule"></u></div>')
    tw += ['tl.to("#title",{opacity:1,duration:0.01},0.17);',
           'tl.fromTo("#t1 .hf-bottom-up-letters-char",{opacity:0,y:64},'
           '{opacity:1,y:0,duration:0.46,ease:"back.out(1.7)",stagger:0.028},0.17);',
           'tl.fromTo("#t2 .hf-bottom-up-letters-char",{opacity:0,y:58},'
           '{opacity:1,y:0,duration:0.44,ease:"back.out(1.65)",stagger:0.026},0.48);',
           'tl.fromTo("#t3 .hf-bottom-up-letters-char",{opacity:0,y:46},'
           '{opacity:1,y:0,duration:0.40,ease:"back.out(1.6)",stagger:0.020},0.80);',
           'tl.fromTo("#trule",{scaleX:0},{scaleX:1,duration:0.44,ease:"power3.out"},1.10);',
           # clears on "Setting up", so the frame is empty for his first real sentence
           'tl.to("#title",{opacity:0,y:-26,duration:0.30,ease:"power2.in"},2.40);']

    # ---- 5.83-13.62. This line is about a specific thing existing ("building something
    # that's sustainable ... build on top of ... self-improve"), so the frame shows the
    # thing: real desktop capture, composited by build_hook_shot.py as a rounded rect.
    # The old TERRIBLE TIME / SUSTAINABLE type card was cut - text describing a product
    # is weaker than the product working, and it put two big type blocks back to back.
    #
    # dynamic-grid sits BEHIND the insert as a ground, drifting slowly. It is the one
    # place in the hook where a grid earns itself: the insert is a hard-edged rectangle
    # dropped on a soft blurred room, and the grid gives it something to sit on. It is
    # deliberately text-free, so it cannot shimmer.
    el.append('<div id="gridwrap"><div class="hf-dynamic-grid"></div></div>')
    tw += ['tl.fromTo("#gridwrap",{opacity:0},{opacity:1,duration:0.50,'
           'ease:"power2.out"},8.90);',
           # slow constant drift across the whole beat, no easing: a ground should move
           # under the content, not perform
           'tl.fromTo(".hf-dynamic-grid",{"--hf-grid-x":"0px","--hf-grid-y":"0px"},'
           '{"--hf-grid-x":"-72px","--hf-grid-y":"-48px",duration:4.60,ease:"none"},8.90);',
           'tl.to("#gridwrap",{opacity:0,duration:0.30,ease:"power2.in"},13.20);']

    # Caption naming what is on screen. Text and line, no panel.
    el.append('<div id="icap"><b>HERMES DESKTOP</b><i>running a real session</i></div>')
    tw += ['tl.fromTo("#icap",{opacity:0,x:-34},'
           '{opacity:1,x:0,duration:0.34,ease:"power3.out"},9.70);',
           'tl.to("#icap",{opacity:0,duration:0.26,ease:"power2.in"},13.20);']

    return f"""<!doctype html>
<html lang="en"><head><meta charset="UTF-8"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
{grab(BUL,"style")}
{grab(GRD,"style")}
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:transparent;overflow:hidden}}
body{{width:{W}px;height:{H}px;font-family:Inter,system-ui,sans-serif}}

/* Title stacks THREE short lines instead of two long ones: at 150px "FULL SETUP GUIDE"
   measured ~900px wide and crossed into his warm span, which starts at x=720. */
#title{{position:absolute;left:{LX}px;top:430px;opacity:0}}
#t1,#t2,#t3{{font-family:Anton,sans-serif;color:#fff;text-transform:uppercase;
  letter-spacing:0.01em;line-height:0.90;text-shadow:0 4px 30px rgba(0,0,0,0.95)}}
#t1{{font-size:132px}}
#t2{{font-size:132px}}
#t3{{font-size:132px;color:{AC}}}
#trule{{display:block;margin-top:24px;width:600px;height:8px;border-radius:4px;
  background:#fff;transform:scaleX(0);transform-origin:0 50%;text-decoration:none;
  box-shadow:0 0 22px rgba(0,0,0,0.6)}}

/* Full frame. The insert covers x 160-1760 / y 120-1020, so the grid only ever reads
   in the margins around it - which is the point of a ground. Brighter than the default
   translucent white because it has to carry over a blurred purple room. */
#gridwrap{{position:absolute;inset:0;opacity:0;z-index:0}}
#gridwrap .hf-dynamic-grid{{--hf-grid-size:80px;--hf-grid-line:3px;
  --hf-grid-color:rgba(248,192,0,0.85)}}

/* Caption under the desktop insert (insert occupies x 96-1496, y 176-964). */
/* Caption sits ABOVE the insert, in the 120px band at the top of frame. At the bottom
   it was crammed into the last 54px against the frame edge and read as an afterthought. */
#icap{{position:absolute;left:{LX}px;top:30px;opacity:0;white-space:nowrap;
  display:flex;align-items:baseline;gap:22px}}
#icap b{{font-family:Anton,sans-serif;font-weight:400;font-size:56px;color:#fff;
  text-transform:uppercase;letter-spacing:0.02em;
  text-shadow:0 2px 18px rgba(0,0,0,0.95)}}
#icap i{{font-style:normal;font-family:"Space Mono",monospace;font-weight:700;
  font-size:28px;letter-spacing:0.12em;color:{AC};text-transform:uppercase;
  text-shadow:0 2px 16px rgba(0,0,0,0.95)}}
</style></head>
<body>
<div id="root" data-composition-id="hook" data-width="{W}" data-height="{H}"
     data-start="0" data-duration="{DUR:.2f}">
  <div class="clip" id="hook-clip" data-start="0" data-duration="{DUR:.2f}" data-track-index="0">
    {"".join(el)}
  </div>
</div>
{grab(BUL,"script")}
{grab(GRD,"script")}
<script>
window.__timelines = window.__timelines || {{}};
var tl = gsap.timeline({{paused:true}});
{chr(10).join('  '+x for x in tw)}
window.__timelines["hook"] = tl;
</script>
</body></html>
"""


if __name__ == "__main__":
    os.makedirs(BUILD, exist_ok=True); os.makedirs(MOVS, exist_ok=True)
    html = build()
    # every beat must finish inside data-duration or the tween silently never runs
    for t in (13.20+0.26,):
        assert t < DUR, f"beat at {t} past DUR {DUR}"
    open(os.path.join(BUILD, "index.html"), "w").write(html)
    dst = os.path.join(MOVS, "hook.mov")
    env = dict(os.environ, PRODUCER_BROWSER_GPU_MODE="hardware")
    subprocess.run(["hyperframes", "render", BUILD, "-o", dst, "--format", "mov",
                    "--fps", str(FPS), "--quiet"], env=env, check=True)
    print("->", dst)
