#!/usr/bin/env python3
"""Full-frame cutaway for the "that's the wall" beat, recut 15.55 - 22.60.

Why it exists: this was 8.5 seconds of bare talking head with text laid over it - the
longest face-only stretch in the intro, sitting right where the retention graph drops.
Nate's first two minutes are face-free roughly 60% of the time; he cuts to a live demo,
receipts, or a motion graphic every few seconds. This replaces the face entirely for ~7s.

Combines three things from his kit: #9 node/network diagram, #10 crossed-out chips,
#12 red-glow danger framing.

Brand marks are REAL, pulled from the `simple-icons` package (overlays/build/icons).
Slack is not in that set - it was removed at Slack's request - so it stays a text tile
rather than an invented mark.

Beats pinned to the VO:
  15.60  agent node + the six apps, a gap between them
  17.16  "not the AI"      the agent lights teal and is cleared
  18.30  the barrier hardens red across the gap
  20.35  PASSWORDS / TOKENS / SCOPES mount on the barrier
  21.34  each is struck through
  22.55  THAT'S THE WALL

Output: overlays/wall.mp4 (opaque)
"""
import json, os, subprocess

BASE = os.path.expanduser("~/Movies/Camtasia/047 - arcade.dev full course")
ICONS= os.path.join(BASE, "overlays/build/icons/icons.json")
BUILD= os.path.join(BASE, "overlays/build/wall")
OUT  = os.path.join(BASE, "overlays/wall.mp4")
W,H,FPS = 1920,1080,30
AT   = 15.55            # where this is overlaid in the recut
DUR  = 7.60             # ends 23.15; the struck PASSWORDS pill holds through
                        # "that's the wall" (22.55) and we cut back to camera on
                        # "so by the end of this" (23.09)
AC   = "#46e5b7"
DN   = "#ff5c7a"
FONT = os.environ.get("GFX_FONT","Outfit")
FW   = "800" if FONT in ("Outfit","Poppins","Montserrat") else "400"

APPS = ["Gmail","Google Calendar","Google Drive","Google Docs","Slack","ClickUp"]
RISK = ["Passwords","Tokens","Scopes"]

def build():
    ic = json.load(open(ICONS))
    el, tw = [], []
    for i,name in enumerate(APPS):
        col,row = i%2, i//2
        d = ic.get(name)
        if d:
            mark = (f'<svg viewBox="0 0 24 24"><path fill="#{d["hex"]}" d="{d["path"]}"/></svg>')
        else:
            # no invented marks: Slack is not in simple-icons
            mark = '<b class="nomark">#</b>'
        short = name.replace("Google ","")
        el.append(f'<div class="app" id="ap{i}" style="left:{col*268}px;top:{row*104}px">'
                  f'{mark}<span>{short}</span></div>')
        tw.append(f'tl.fromTo("#ap{i}",{{opacity:0,x:34}},{{opacity:1,x:0,duration:0.34,'
                  f'ease:"power3.out"}},{0.22+i*0.07:.2f});')

    # ONE pill, centred, struck - no stacked list. Tyler: "at 0:20 go to the passwords
    # pill with red line through it, and keep it through 'that's the wall'."
    el.append('<div class="risk" id="rk0">Passwords<u></u></div>')
    tw += ['tl.to("#agent,#apps,#beam,#barrier,#spark",{opacity:0,duration:0.36,ease:"power2.in"},4.30);',
           'tl.to("#danger",{opacity:0.58,duration:0.36},4.30);',
           'tl.fromTo("#rk0",{opacity:0,scale:0.72},{opacity:1,scale:1,duration:0.44,'
           'ease:"back.out(2.0)"},4.45);',
           'tl.to("#rk0 u",{width:"108%",duration:0.34,ease:"power2.inOut"},4.95);']

    tw += [
      # the agent, then the reach that gets blocked
      'tl.fromTo("#agent",{opacity:0,scale:0.8},{opacity:1,scale:1,duration:0.42,ease:"back.out(2)"},0.10);',
      'tl.fromTo("#beam",{scaleX:0},{scaleX:1,duration:0.52,ease:"power2.inOut"},0.90);',
      'tl.to("#agent",{borderColor:"'+AC+'",boxShadow:"0 0 54px rgba(70,229,183,0.55)",duration:0.36},1.61);',
      'tl.to("#agentok",{opacity:1,scale:1,duration:0.34,ease:"back.out(2.4)"},1.61);',
      'tl.to("#alabel",{color:"'+AC+'",duration:0.30},1.61);',
      # barrier hardens
      'tl.fromTo("#barrier",{opacity:0,scaleY:0.2},{opacity:1,scaleY:1,duration:0.46,ease:"power3.out"},2.75);',
      'tl.to("#beam",{backgroundImage:"linear-gradient(90deg, rgba(255,92,122,.15), '+DN+')",duration:0.34},2.75);',
      'tl.to("#danger",{opacity:1,duration:0.40,ease:"power2.out"},2.80);',
      'tl.fromTo("#spark",{opacity:0},{opacity:1,duration:0.18,repeat:5,yoyo:true,ease:"none"},2.85);',
      # stamp
    ]
    return f"""<!doctype html><html><head><meta charset="UTF-8"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W}px;height:{H}px;font-family:{FONT},system-ui,sans-serif;
  background:radial-gradient(1300px 760px at 28% 34%, #101f26 0%, #080e12 62%, #05090b 100%)}}
#danger{{position:absolute;inset:0;opacity:0;box-shadow:inset 0 0 260px 100px rgba(255,92,122,0.40)}}
#agent{{position:absolute;left:150px;top:398px;width:290px;height:290px;border-radius:34px;
  border:3px solid #ffffff33;background:rgba(255,255,255,0.05);opacity:0;
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px}}
#agent svg{{width:104px;height:104px}}
#agentok{{position:absolute;right:-18px;top:-18px;width:56px;height:56px;border-radius:50%;
  background:{AC};color:#06120f;font-size:32px;font-weight:800;display:flex;align-items:center;
  justify-content:center;opacity:0;transform:scale(0.4)}}
#alabel{{font-family:{FONT},sans-serif;font-weight:{FW};font-size:34px;color:#ffffffb5;
  text-transform:uppercase;letter-spacing:0.02em}}
#beam{{position:absolute;left:452px;top:536px;width:396px;height:8px;border-radius:4px;
  transform:scaleX(0);transform-origin:0 50%;
  background-image:linear-gradient(90deg, rgba(70,229,183,.15), {AC})}}
#barrier{{position:absolute;left:846px;top:214px;width:26px;height:650px;border-radius:13px;
  background:linear-gradient(180deg,{DN},#b3324a);opacity:0;transform-origin:50% 50%;
  box-shadow:0 0 60px rgba(255,92,122,0.6)}}
#spark{{position:absolute;left:806px;top:496px;width:110px;height:110px;border-radius:50%;
  background:radial-gradient(closest-side,rgba(255,180,190,.9),rgba(255,92,122,0) 70%);opacity:0}}
#apps{{position:absolute;left:1020px;top:352px;width:540px;height:320px}}
.app{{position:absolute;width:250px;height:86px;border-radius:16px;opacity:0;
  border:2px solid #ffffff26;background:rgba(255,255,255,0.055);
  display:flex;align-items:center;gap:18px;padding:0 22px}}
.app svg{{width:40px;height:40px;flex:none}}
.app .nomark{{width:40px;height:40px;flex:none;border-radius:9px;background:#ffffff26;color:#fff;
  font-size:24px;display:flex;align-items:center;justify-content:center}}
.app span{{font-family:{FONT},sans-serif;font-weight:{FW};font-size:26px;color:#eaf5f7;
  white-space:nowrap}}
.risk{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);opacity:0;
  padding:30px 64px;border-radius:22px;background:rgba(10,6,8,0.94);border:4px solid {DN};
  font-family:{FONT},sans-serif;font-weight:{FW};font-size:118px;color:#fff;
  text-transform:uppercase;white-space:nowrap;box-shadow:0 0 70px rgba(255,92,122,.45)}}
.risk u{{position:absolute;left:-10px;top:52%;height:14px;width:0;background:{DN};
  border-radius:7px;display:block;box-shadow:0 0 26px {DN}}}
#wall{{position:absolute;left:0;top:882px;width:{W}px;text-align:center;opacity:0;
  font-family:{FONT},sans-serif;font-weight:{FW};font-size:92px;color:{DN};
  text-transform:uppercase;text-shadow:0 4px 34px rgba(0,0,0,.9)}}
</style></head><body>
<div id="root" data-composition-id="wall" data-width="{W}" data-height="{H}"
     data-start="0" data-duration="{DUR:.2f}">
  <div class="clip" data-start="0" data-duration="{DUR:.2f}" data-track-index="0">
    <div id="danger"></div>
    <div id="agent">
      <div id="agentok">✓</div>
      <svg viewBox="0 0 40 40"><g><path d="M20 3v34M3 20h34M8 8l24 24M32 8L8 32"
        stroke="{AC}" stroke-width="4" stroke-linecap="round" fill="none"/></g></svg>
      <div id="alabel">The AI</div>
    </div>
    <div id="beam"></div>
    <div id="spark"></div>
    <div id="barrier"></div>
    <div id="apps">{"".join(el[:len(APPS)])}</div>
    {"".join(el[len(APPS):])}
  </div>
</div>
<script>
window.__timelines=window.__timelines||{{}};
var tl=gsap.timeline({{paused:true}});
{chr(10).join('  '+x for x in tw)}
window.__timelines["wall"]=tl;
</script></body></html>"""

if __name__ == "__main__":
    os.makedirs(BUILD, exist_ok=True)
    open(os.path.join(BUILD,"index.html"),"w").write(build())
    env = dict(os.environ, PRODUCER_BROWSER_GPU_MODE="hardware")
    subprocess.run(["hyperframes","render",BUILD,"-o",OUT,"--format","mp4",
                    "--fps",str(FPS),"--quiet"], env=env, check=True,
                   capture_output=True, text=True)
    print("->", OUT)
