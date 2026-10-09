#!/usr/bin/env python3
"""Cutaway for "this used to be the hard part / what actually works now", recut 45.15-50.05.

The last soft spot: 5.25s of talking head with captions over it. This shows the claim
instead of captioning it - the old way (a wall of OAuth boilerplate) against the new way
(one command) - which is the whole argument of the course in one frame.

Beats pinned to the VO:
  45.47  "trust me"        the boilerplate wall is already up, labelled THE HARD PART
  47.30  (mid-sentence)    the wall is struck and collapses
  48.30  "what works now"  one command types itself in its place

Output: overlays/movs/hardpart.mov (transparent ProRes 4444)
"""
import os, subprocess

BASE = os.path.expanduser("~/Movies/Camtasia/047 - arcade.dev full course")
BUILD= os.path.join(BASE, "overlays/build/hardpart")
MOVS = os.path.join(BASE, "overlays/movs")
W,H,FPS = 1920,1080,30
DUR  = 4.25            # placed at 45.15 -> 50.10
AC   = "#46e5b7"
DN   = "#ff5c7a"
FONT = os.environ.get("GFX_FONT","Outfit")
FW   = "800" if FONT in ("Outfit","Poppins","Montserrat") else "400"

OLD = [
 "flow = InstalledAppFlow.from_client_secrets_file(",
 "    'client_secret.json', SCOPES)",
 "creds = flow.run_local_server(port=0)",
 "if creds and creds.expired and creds.refresh_token:",
 "    creds.refresh(Request())",
 "with open('token.json', 'w') as t:",
 "    t.write(creds.to_json())",
 "# ...repeat per user, per app, every 7 days",
]
NEW = "claude mcp add --transport http arcade https://api.arcade.dev/mcp/..."

def build():
    el, tw = [], []
    rows = "".join(f'<div class="cl" id="cl{i}">{l.replace(" ","&nbsp;")}</div>'
                   for i,l in enumerate(OLD))
    el.append(f'<div id="old"><div class="lbl bad">The hard part</div>'
              f'<div class="code">{rows}<u id="slash"></u></div></div>')
    for i in range(len(OLD)):
        tw.append(f'tl.fromTo("#cl{i}",{{opacity:0,x:-18}},{{opacity:1,x:0,duration:0.18,'
                  f'ease:"power2.out"}},{0.02+i*0.035:.2f});')
    tw += [
      'tl.fromTo("#old",{opacity:0,y:20},{opacity:1,y:0,duration:0.34,ease:"power3.out"},0.02);',
      # struck through, then collapses
      'tl.fromTo("#slash",{scaleX:0},{scaleX:1,duration:0.42,ease:"power2.inOut"},1.45);',
      'tl.to("#old",{opacity:0.22,duration:0.30},1.85);',
      'tl.to("#old",{opacity:0,y:-26,scale:0.96,duration:0.42,ease:"power2.in"},2.20);',
    ]
    n=len(NEW)
    el.append(f'<div id="new"><div class="lbl good">What actually works now</div>'
              f'<div class="cmd"><span class="pr">$</span> <span id="typ"></span>'
              f'<span class="cur"></span></div></div>')
    tw += [
      'tl.fromTo("#new",{opacity:0,y:26},{opacity:1,y:0,duration:0.36,ease:"power3.out"},2.45);',
      f'tl.to("#typ",{{duration:0.90,ease:"none",onUpdate:function(){{'
      f'var s="{NEW}";document.getElementById("typ").textContent='
      f's.slice(0,Math.round(this.progress()*s.length));}}}},2.60);',
      'tl.to("#new",{opacity:0,duration:0.28,ease:"power2.in"},3.95);',
    ]
    return f"""<!doctype html><html><head><meta charset="UTF-8"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:transparent;overflow:hidden}}
body{{width:{W}px;height:{H}px;font-family:{FONT},system-ui,sans-serif}}
body::before{{content:"";position:absolute;inset:0;
  background:radial-gradient(1300px 780px at 34% 40%, #101c22 0%, #070d10 62%, #04080a 100%)}}
.lbl{{font-family:{FONT},sans-serif;font-weight:{FW};font-size:52px;text-transform:uppercase;
  margin-bottom:26px}}
.bad{{color:{DN}}} .good{{color:{AC}}}
#old{{position:absolute;left:250px;top:250px;opacity:0}}
.code{{position:relative;padding:30px 36px;border-radius:16px;background:#0b1216;
  border:2px solid #ffffff1f;box-shadow:0 26px 70px rgba(0,0,0,.6)}}
.cl{{font-family:"Space Mono",monospace;font-size:26px;line-height:1.62;color:#b9d4da;opacity:0;
  white-space:nowrap}}
#slash{{position:absolute;left:14px;top:50%;height:8px;width:calc(100% - 28px);background:{DN};
  border-radius:4px;display:block;transform:scaleX(0);transform-origin:0 50%;
  box-shadow:0 0 26px {DN}}}
#new{{position:absolute;left:250px;top:430px;opacity:0;width:1440px}}
.cmd{{padding:34px 38px;border-radius:16px;background:#0b1216;border:2px solid {AC};
  font-family:"Space Mono",monospace;font-size:30px;color:#e6f6f9;white-space:nowrap;
  box-shadow:0 0 52px rgba(70,229,183,.28)}}
.pr{{color:{AC}}}
.cur{{display:inline-block;width:14px;height:30px;background:{AC};vertical-align:-4px;margin-left:4px}}
</style></head><body>
<div id="root" data-composition-id="hp" data-width="{W}" data-height="{H}"
     data-start="0" data-duration="{DUR:.2f}">
  <div class="clip" data-start="0" data-duration="{DUR:.2f}" data-track-index="0">{"".join(el)}</div>
</div>
<script>
window.__timelines=window.__timelines||{{}};
var tl=gsap.timeline({{paused:true}});
{chr(10).join('  '+x for x in tw)}
window.__timelines["hp"]=tl;
</script></body></html>"""

if __name__ == "__main__":
    os.makedirs(BUILD, exist_ok=True); os.makedirs(MOVS, exist_ok=True)
    open(os.path.join(BUILD,"index.html"),"w").write(build())
    env=dict(os.environ, PRODUCER_BROWSER_GPU_MODE="hardware")
    dst=os.path.join(MOVS,"hardpart.mov")
    subprocess.run(["hyperframes","render",BUILD,"-o",dst,"--format","mov",
                    "--fps",str(FPS),"--quiet"], env=env, check=True,
                   capture_output=True, text=True)
    print("->", dst)
