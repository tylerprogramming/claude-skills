#!/usr/bin/env python3
"""The small version — recut 30.40 - 35.55.

"...if it's just for you and just for like your local machine where you have Claude Code
or whatever IDE you're using, then great."

This is deliberately the MINIATURE of the always-on infographic at 37.85: one person, one
machine, a boundary drawn around them. Four seconds later that same shape bursts into many
users -> hub -> agents. Building the small one first is what gives the big one its payoff.

Full-frame camera shot (src 43.99-61.99 is mode="cam"), him centred with head at
x 790-1270, so this lives in the dark couch band on the left: x 78-600, y 520-990. Must be
finished before the cut to the next camera shot at src 51.59 / recut 35.60 — it clears at
35.45 with 0.10 of spare tail.

Whisper writes "cloud code" throughout; he is saying Claude Code.

Pinned to the words:
    30.44  "for you"        the person appears
    32.09  "local machine"  the laptop drops in under him
    33.49  "Claude Code"    the editor mark lights on the laptop
    35.02  "using"          the boundary ring closes around the whole thing

Output: overlays/movs/solo.mov (transparent ProRes 4444).
"""
import os, re, subprocess

BASE = os.path.expanduser("~/Movies/Camtasia/045 - arcade.dev")
BUL = os.path.join(BASE, "overlays", "build", "bul", "compositions",
                   "components", "bottom-up-letters.html")
BUILD = os.path.join(BASE, "overlays", "build", "solo")
MOVS = os.path.join(BASE, "overlays", "movs")

AT = 30.40
DUR = 5.15                      # -> 35.55, clear of the 35.60 cut
W, H = 1920, 1080
FPS = 30
ACCENT = "#46e5b7"


def grab(path, tag):
    m = re.search(rf"<{tag}\b.*?</{tag}>", open(path).read(), re.S)
    if not m:
        raise SystemExit(f"no <{tag}> in {path}")
    return m.group(0)


def build():
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    {grab(BUL, "style")}
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ background: transparent; overflow: hidden; }}
      body {{ width: {W}px; height: {H}px;
             font-family: Inter, system-ui, sans-serif; }}
      #wrap {{ position: absolute; left: 78px; top: 520px; width: 540px; height: 470px; }}

      /* the boundary that closes at the end — drawn as a stroked rounded rect so it can
         wipe on rather than just fade */
      #ring {{ position: absolute; left: 0; top: 0; width: 540px; height: 400px; }}
      #ring rect {{
        fill: none; stroke: {ACCENT}; stroke-width: 5; stroke-linecap: round;
        stroke-dasharray: 1880; stroke-dashoffset: 1880;
        filter: drop-shadow(0 0 16px {ACCENT});
      }}

      /* person */
      #you {{ position: absolute; left: 62px; top: 46px; opacity: 0;
             transform: scale(0.5); }}
      #you .head {{
        width: 62px; height: 62px; border-radius: 50%; background: #fff;
        margin: 0 auto; box-shadow: 0 0 26px rgba(255, 255, 255, 0.5);
      }}
      #you .body {{
        width: 118px; height: 62px; margin-top: 12px;
        border-radius: 60px 60px 12px 12px; background: #fff;
        box-shadow: 0 0 26px rgba(255, 255, 255, 0.5);
      }}
      #ylbl {{
        position: absolute; left: 212px; top: 74px; opacity: 0;
        font-family: Anton, sans-serif; font-size: 62px; color: #fff;
        text-transform: uppercase; letter-spacing: 0.02em; white-space: nowrap;
        text-shadow: 0 3px 22px rgba(0, 0, 0, 0.9);
      }}

      /* connector */
      #stem {{
        position: absolute; left: 120px; top: 190px; width: 5px; height: 46px;
        background: {ACCENT}; border-radius: 3px;
        transform: scaleY(0); transform-origin: 50% 0;
      }}

      /* laptop */
      #mac {{ position: absolute; left: 40px; top: 240px; opacity: 0;
             transform: translateY(24px); }}
      #mac .lid {{
        width: 166px; height: 108px; border: 5px solid #fff; border-radius: 10px;
        background: rgba(255, 255, 255, 0.06);
        display: flex; align-items: center; justify-content: center;
      }}
      #mac .base {{
        width: 210px; height: 12px; margin-left: -22px; margin-top: 6px;
        border-radius: 0 0 8px 8px; background: #fff;
      }}
      #ide {{
        width: 108px; height: 58px; border-radius: 7px; background: {ACCENT};
        opacity: 0; transform: scale(0.4);
        box-shadow: 0 0 26px {ACCENT}; position: relative;
      }}
      #ide::after {{
        content: ""; position: absolute; left: 14px; top: 16px; width: 44px; height: 5px;
        border-radius: 3px; background: #06120f;
        box-shadow: 0 14px 0 #06120f, 26px 14px 0 #06120f;
      }}
      #mlbl {{
        position: absolute; left: 258px; top: 268px; opacity: 0;
        font-family: Anton, sans-serif; font-size: 44px; color: #fff;
        text-transform: uppercase; letter-spacing: 0.02em; line-height: 1.04;
        text-shadow: 0 3px 22px rgba(0, 0, 0, 0.9);
      }}
      #mlbl b {{ display: block; font-weight: 400; font-size: 44px; color: {ACCENT}; }}

      /* the caption under the closed boundary */
      #cap {{
        position: absolute; left: 4px; top: 420px; opacity: 0;
        font-family: "Space Mono", monospace; font-weight: 700; font-size: 27px;
        letter-spacing: 0.14em; text-transform: uppercase; color: {ACCENT};
        text-shadow: 0 2px 16px rgba(0, 0, 0, 0.95);
      }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="solo" data-width="{W}" data-height="{H}"
         data-start="0" data-duration="{DUR:.2f}">
      <div class="clip" data-start="0" data-duration="{DUR:.2f}" data-track-index="0">
        <div id="wrap">
          <svg id="ring" viewBox="0 0 540 400">
            <rect x="4" y="4" width="532" height="392" rx="30" />
          </svg>
          <div id="you"><div class="head"></div><div class="body"></div></div>
          <div id="ylbl" class="hf-bottom-up-letters">Just you</div>
          <div id="stem"></div>
          <div id="mac">
            <div class="lid"><div id="ide"></div></div>
            <div class="base"></div>
          </div>
          <div id="mlbl">Your machine<b>Claude Code</b></div>
          <div id="cap">Local only</div>
        </div>
      </div>
    </div>
    {grab(BUL, "script")}
    <script>
      window.__timelines = window.__timelines || {{}};
      var tl = gsap.timeline({{ paused: true }});

      /* 30.44 "for you" */
      tl.to("#you", {{ opacity: 1, scale: 1, duration: 0.44,
        ease: "back.out(2.2)" }}, 0.04);
      tl.to("#ylbl", {{ opacity: 1, duration: 0.26 }}, 0.20);
      tl.to("#ylbl .hf-bottom-up-letters-char", {{ opacity: 1, y: 0, duration: 0.44,
        ease: "back.out(1.7)", stagger: 0.026 }}, 0.22);

      /* 32.09 "local machine" */
      tl.to("#stem", {{ scaleY: 1, duration: 0.30, ease: "power2.out" }}, 1.45);
      tl.to("#mac", {{ opacity: 1, y: 0, duration: 0.46, ease: "back.out(1.6)" }}, 1.69);
      tl.to("#mlbl", {{ opacity: 1, duration: 0.30 }}, 1.95);

      /* 33.49 "Claude Code or whatever IDE" — the editor lights up on the laptop */
      tl.to("#ide", {{ opacity: 1, scale: 1, duration: 0.40,
        ease: "back.out(2.4)" }}, 3.09);

      /* 35.02 "using," — the boundary closes around the whole thing. THIS is the shape
         the always-on infographic breaks open at 37.85. */
      tl.to("#ring rect", {{ strokeDashoffset: 0, duration: 0.54,
        ease: "power2.inOut" }}, 4.28);
      tl.to("#cap", {{ opacity: 1, duration: 0.24 }}, 4.72);

      /* clear before the cut at 35.60 */
      tl.to("#wrap", {{ opacity: 0, duration: 0.22, ease: "power2.in" }}, 4.93);

      window.__timelines["solo"] = tl;
    </script>
  </body>
</html>
"""


if __name__ == "__main__":
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(MOVS, exist_ok=True)
    with open(os.path.join(BUILD, "index.html"), "w") as f:
        f.write(build())
    dst = os.path.join(MOVS, "solo.mov")
    env = dict(os.environ, PRODUCER_BROWSER_GPU_MODE="hardware")
    subprocess.run(["hyperframes", "render", BUILD, "-o", dst,
                    "--format", "mov", "--fps", str(FPS), "--quiet"],
                   env=env, check=True, capture_output=True, text=True)
    print("->", dst)
