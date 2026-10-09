#!/usr/bin/env python3
"""058 outline beat - recut 58.2-86.2, over FULL-FRAME camera.

The outline used to sit on the teleprompter document with a webcam circle on it: 28
seconds where the "screen" was a static page. That reads as a bare talking head to a
viewer even though the face metric says otherwise. Now it is full-frame camera with the
agenda assembling beside him.

Built on the registry component `grid-card-assemble`. That component is ELASTIC by
design - container-type: size, no data-width/data-height - because it is meant to be
MOUNTED by a parent composition that gives it a box, not rendered on its own. Rendering
it directly fails lint with root_missing_dimensions. So this builds a 1920x1080
transparent parent and mounts the component with data-composition-src, which is the
documented way to use it and also keeps our file small.

`cues` places each card on the word that names it (measured off the delivered cut in
transcript/recut_words.json, never a stated time):

    r 61.78  "hardware"        Hardware
    r 65.23  "download"        Install
    r 67.93  "memory"          Features
    r 73.22  "open source"     Local models
    r 76.41  "desktops"        The desktop
    r 84.33  "multi-agent"     Multi-agent

The component's own cascade would spread these evenly; cues override that so each card
lands on its noun.

Layout: he sits x 720-1130 (warm-pixel span measured across the hook), so the mount box
is the left band, 96..736. `list` layout, not `grid`: six cards in a grid would need the
full width and would cross him.

Output: overlays/movs/outline.mov (transparent ProRes 4444)
"""
import json, os, shutil, subprocess, sys

BASE  = os.path.expanduser("~/Movies/Camtasia/058 - hermes agent")
COMP  = os.path.join(BASE, "overlays/build/gridc/compositions/components/grid-card-assemble.html")
BUILD = os.path.join(BASE, "overlays/build/outline")
MOVS  = os.path.join(BASE, "overlays/movs")
DST   = os.path.join(MOVS, "outline.mov")

AT   = 58.20          # recut time this MOV is composited at
DUR  = 31.00          # to 86.40; the tail past the beat is never displayed
W, H = 1920, 1080
FPS  = 30
AC   = "#F8C000"

ITEMS = [
    ("Hardware",     "where your agent lives",        61.78),
    ("Install",      "download and setup",            65.23),
    ("Features",     "memory skills cron profiles",   67.93),
    ("Local models", "open source and private",       73.22),
    ("The desktop",  "the app you live in",           76.41),
    ("Multi-agent",  "a team that works for you",     84.33),
]


def prepare_component(dst_path):
    """Copy the registry component and bake our content into its DEFAULTS.

    Two things go wrong when mounting it with data-composition-variables alone, and both
    fail silently - the render succeeds and shows the stock card set:

    1. The variables did not reach the child. It read vars.items as null and fell back to
       "Capture,Compose,Render,Publish", which is exactly what shipped in the first MOV.
    2. The child keeps its own data-duration="4.5". Our beat is 28.2s, so everything
       vanished after ~6 seconds. The component reads root.dataset.duration directly
       (line ~383), so the attribute is the only thing that matters.

    Patching the defaults in our own copy removes the dependency on variable plumbing
    entirely. Every replacement is asserted: a find/replace that does not match is the
    classic silent failure here.
    """
    src = open(COMP).read()
    items = ",".join(f"{lab}: {body}" for lab, body, _ in ITEMS)
    cues  = ",".join(f"{t-AT:.2f}" for _, _, t in ITEMS)
    subs = [
        # The JS fallbacks in the script body are NOT enough. The runtime reads the
        # declared defaults in data-composition-variables (~lines 64-69) and injects
        # them, so vars.items is never null and the fallback never fires. The declared
        # defaults are what actually decide content, layout, cues and exit.
        ('"default": "Capture,Compose,Render,Publish"', f'"default": {json.dumps(items)}'),
        ('? "Capture,Compose,Render,Publish"', f'? {json.dumps(items)}'),
        ('"label": "Layout", "description": "Grid wraps by columns; list stacks vertically.", "default": "grid"',
         '"label": "Layout", "description": "Grid wraps by columns; list stacks vertically.", "default": "list"'),
        ('"label": "Cues", "description": "Comma-separated per-item entrance times in seconds. Blank entries use the default cascade.", "default": ""',
         f'"label": "Cues", "description": "Comma-separated per-item entrance times in seconds. Blank entries use the default cascade.", "default": {json.dumps(cues)}'),
        ('"label": "Exit", "description": "How the assembled layout leaves the frame. Default none: the hold ends the film.", "default": "none"',
         '"label": "Exit", "description": "How the assembled layout leaves the frame. Default none: the hold ends the film.", "default": "fade"'),
        ('data-composition-duration="4.5"', f'data-composition-duration="{DUR:.2f}"'),
        ('data-duration="4.5"', f'data-duration="{DUR:.2f}"'),
    ]
    for old, new in subs:
        assert old in src, f"component patch did not match: {old[:60]}"
        src = src.replace(old, new)
    for _, new in subs:
        assert new in src, f"component patch did not land: {new[:60]}"
    open(dst_path, "w").write(src)


def build_parent():
    items = ",".join(f"{lab}: {body}" for lab, body, _ in ITEMS)
    cues  = ",".join(f"{t-AT:.2f}" for _, _, t in ITEMS)
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="UTF-8"/>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  html,body{{background:transparent;overflow:hidden}}
  body{{width:{W}px;height:{H}px;font-family:Inter,system-ui,sans-serif}}
  /* the mount box: left band only. His warm-pixel span starts at x=720. */
  /* Cards sit to the RIGHT of his face. His warm-pixel span is x 720-1130, so the
     column starts at 1180 and runs to the 1860 margin. Narrower than the left-hand
     version, so the body line is dropped and the label carries the card. */
  #stage{{position:absolute;left:1180px;top:150px;width:680px;height:800px}}
  #stage .gca-card{{padding:22px 26px!important;border-radius:18px!important}}
  #stage .gca-label{{font-size:30px!important;letter-spacing:0.10em!important}}
  #stage .gca-body{{font-size:22px!important}}
  #stage .gca-icon{{width:52px!important;height:52px!important}}
  /* the component ships light card surfaces for a white frame; this is a dark room */
  #stage .gca-card,#stage [class*="card"]{{
    background:rgba(8,12,15,0.88)!important;
    border-color:rgba(255,255,255,0.22)!important;
    box-shadow:0 18px 50px rgba(0,0,0,0.55)!important}}
  #stage [class*="label"],#stage strong{{color:#fff!important}}
  #stage [class*="body"],#stage p,#stage small{{color:rgba(255,255,255,0.72)!important}}
  #stage svg path{{stroke:{AC}!important}}
</style></head>
<body>
<!-- data-no-timeline: the mounted child owns the only timeline. Without it the producer
     polls for a registration on THIS root for 45s before giving up, on every render. -->
<div id="root" data-composition-id="outline" data-width="{W}" data-height="{H}"
     data-start="0" data-duration="{DUR:.2f}" data-no-timeline>
  <div class="clip" id="outline-clip" data-start="0" data-duration="{DUR:.2f}"
       data-track-index="0">
    <!-- src resolves relative to THIS file, which sits at the project root, so the
         path includes compositions/. Every data-composition-src host also needs its
         own data-composition-id. -->
    <div id="stage" data-composition-id="outline-cards"
         data-composition-src="compositions/components/grid-card-assemble.html"
         data-composition-variables='{json.dumps({"items": items, "cues": cues,
             "layout": "list", "accent": "green", "exit": "fade"})}'></div>
  </div>
</div>
</body></html>
"""


if __name__ == "__main__":
    # Project layout the CLI expects: index.html at the root, compositions/ beside it.
    # `hyperframes render <dir>` looks for <dir>/index.html and refuses a path to a
    # file, and it will not find a composition nested under compositions/.
    comps = os.path.join(BUILD, "compositions", "components")
    os.makedirs(comps, exist_ok=True); os.makedirs(MOVS, exist_ok=True)
    prepare_component(os.path.join(comps, "grid-card-assemble.html"))
    for _, _, t in ITEMS:
        assert AT <= t < AT + DUR, f"cue {t} outside the composition window"
    open(os.path.join(BUILD, "index.html"), "w").write(build_parent())
    env = dict(os.environ, PRODUCER_BROWSER_GPU_MODE="hardware")
    subprocess.run(["hyperframes", "render", BUILD,
                    "-o", DST, "--format", "mov", "--fps", str(FPS), "--quiet"],
                   env=env, check=True)
    print("->", DST)
