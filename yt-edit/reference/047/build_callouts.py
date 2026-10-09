#!/usr/bin/env python3
"""Module-1 callout labels, body 0-190s (film 56.3-246.3).

The spec singles this stretch out: "the second minute is where our last video collapsed
into a 48-second graphic-free screen-share. Do NOT repeat that." So a new overlay lands
every ~5-11s across the whole first gateway build, plus one re-tease of the open loop
planted in the intro roadmap.

Rendered on a SMALL canvas (1160x300) pinned bottom-left rather than a full 1920x1080
frame - a 190s transparent ProRes 4444 at full size is several GB for content that only
ever occupies one corner. Overlaid at (70, 742), which clears the camera PIP at x>=1390.

Times are BODY-relative; the film adds 56.29s.

Output: overlays/movs/callouts.mov (transparent ProRes 4444, 1160x300)
"""
import os, re, subprocess

BASE = os.path.expanduser("~/Movies/Camtasia/047 - arcade.dev full course")
BUL  = os.path.join(BASE, "overlays/build/bot/compositions/components/bottom-up-letters.html")
BUILD= os.path.join(BASE, "overlays/build/callouts")
MOVS = os.path.join(BASE, "overlays/movs")

W, H = 1160, 300
DUR  = 190.0
FPS  = 30
AC   = "#46e5b7"
FONT = os.environ.get("GFX_FONT", "Outfit")
FW   = "800" if FONT in ("Outfit","Poppins","Montserrat") else "400"

#  at,   hold, kicker,        label
CALLS = [
    (  3.50, 4.2, "STEP",  "Sign up free"),
    ( 11.00, 4.4, "",      "The Arcade dashboard"),
    ( 26.60, 5.0, "TERM",  "Gateway = a collection of servers"),
    ( 31.30, 4.6, "TERM",  "Server = a collection of tools"),
    ( 44.60, 4.4, "1",     "Create MCP gateway"),
    ( 48.45, 4.8, "2",     "Name it"),
    ( 59.45, 5.4, "3",     "Pick your tools"),
    ( 73.40, 5.0, "",      "Every tool the app has"),
    ( 92.90, 5.2, "TIP",   "Uncheck what you don't need"),
    (104.75, 5.2, "4",     "Choose who can connect"),
    (113.60, 4.6, "5",     "Create the gateway"),
    (119.50, 6.0, "",      "Connect from VS Code, Cursor, Claude"),
]
# the open loop planted by the intro roadmap, re-teased once
LOOP = (84.0, 6.4, "Still coming: the one that runs while you sleep")


def grab(path, tag):
    m = re.search(rf"<{tag}\b.*?</{tag}>", open(path).read(), re.S)
    if not m: raise SystemExit(f"no <{tag}> in {path}")
    return m.group(0)


def build():
    el, tw = [], []
    for i, (at, hold, kick, label) in enumerate(CALLS):
        k = f'<em>{kick}</em>' if kick else ''
        el.append(f'<div class="co" id="co{i}"><i></i>{k}<span>{label}</span></div>')
        tw += [f'tl.fromTo("#co{i}",{{opacity:0,x:-70}},{{opacity:1,x:0,duration:0.40,ease:"power3.out"}},{at:.2f});',
               f'tl.fromTo("#co{i} i",{{scaleY:0}},{{scaleY:1,duration:0.34,ease:"power3.out"}},{at+0.04:.2f});',
               f'tl.to("#co{i}",{{opacity:0,x:-34,duration:0.30,ease:"power2.in"}},{at+hold:.2f});']
    at, hold, label = LOOP
    el.append(f'<div id="loop"><b>&#8627;</b><span>{label}</span></div>')
    tw += [f'tl.fromTo("#loop",{{opacity:0,y:26}},{{opacity:1,y:0,duration:0.42,ease:"power3.out"}},{at:.2f});',
           f'tl.to("#loop",{{opacity:0,y:-18,duration:0.30,ease:"power2.in"}},{at+hold:.2f});']

    return f"""<!doctype html>
<html lang="en"><head><meta charset="UTF-8"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
{grab(BUL,"style")}
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:transparent;overflow:hidden}}
body{{width:{W}px;height:{H}px;font-family:Inter,system-ui,sans-serif}}
.co{{position:absolute;left:0;top:60px;opacity:0;display:flex;align-items:center;gap:20px;
  padding:18px 32px 18px 26px;border-radius:16px;background:rgba(7,12,14,0.90);
  border:2px solid #ffffff2e;box-shadow:0 14px 44px rgba(0,0,0,0.66);white-space:nowrap}}
.co i{{width:7px;height:52px;border-radius:4px;background:{AC};flex:none;
  transform-origin:50% 50%;box-shadow:0 0 18px {AC}}}
.co em{{font-style:normal;font-family:"Space Mono",monospace;font-weight:700;font-size:23px;
  letter-spacing:0.16em;color:{AC};flex:none}}
.co span{{font-family:{FONT},sans-serif;font-weight:{FW};font-size:52px;color:#fff;text-transform:uppercase;
  letter-spacing:0.01em;line-height:1}}
#loop{{position:absolute;left:0;top:196px;opacity:0;display:flex;align-items:center;gap:16px;
  padding:13px 26px;border-radius:999px;background:rgba(7,12,14,0.90);
  border:2px solid {AC};white-space:nowrap}}
#loop b{{color:{AC};font-size:28px;line-height:1}}
#loop span{{font-family:"Space Mono",monospace;font-weight:700;font-size:25px;
  letter-spacing:0.10em;text-transform:uppercase;color:{AC}}}
</style></head>
<body>
<div id="root" data-composition-id="callouts" data-width="{W}" data-height="{H}"
     data-start="0" data-duration="{DUR:.2f}">
  <div class="clip" data-start="0" data-duration="{DUR:.2f}" data-track-index="0">
    {"".join(el)}
  </div>
</div>
{grab(BUL,"script")}
<script>
window.__timelines = window.__timelines || {{}};
var tl = gsap.timeline({{paused:true}});
{chr(10).join('  '+x for x in tw)}
window.__timelines["callouts"] = tl;
</script>
</body></html>
"""

if __name__ == "__main__":
    os.makedirs(BUILD, exist_ok=True); os.makedirs(MOVS, exist_ok=True)
    open(os.path.join(BUILD,"index.html"),"w").write(build())
    dst = os.path.join(MOVS,"callouts.mov")
    env = dict(os.environ, PRODUCER_BROWSER_GPU_MODE="hardware")
    subprocess.run(["hyperframes","render",BUILD,"-o",dst,"--format","mov",
                    "--fps",str(FPS),"--quiet"], env=env, check=True,
                   capture_output=True, text=True)
    sz = os.path.getsize(dst)/1e9
    print(f"-> {dst}  {sz:.2f} GB")
