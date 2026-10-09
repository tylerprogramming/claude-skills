#!/usr/bin/env python3
"""Two cutaways across recut 33.00 - 45.05, the last long talking-head stretch.

That run measured 18.2 seconds of unbroken face with only chips over it - the worst
remaining stretch after the wall cutaway landed. Nate breaks anything like it with a
live demo, a receipt, or a motion graphic.

Rendered as ONE transparent ProRes so the middle 1.55s can be fully clear, letting the
camera show through: cutaway, presenter beat, cutaway. That is his rhythm, not a single
12-second graphic wall.

  local 0.00-5.55   (33.00-38.55)  the auth problem: a .env of secrets, struck out
  local 5.55-7.10   (38.55-40.10)  TRANSPARENT - back to camera
  local 7.10-12.05  (40.10-45.05)  the credibility receipt: 8 years, IBM / Chase / Pfizer

Company names are set typographically, not as logos: only Chase exists in simple-icons
(IBM and Pfizer do not), a mixed set would read as broken, and an employer's mark on
screen implies an endorsement he does not have.

Output: overlays/movs/auth.mov (transparent ProRes 4444)
"""
import os, subprocess

BASE = os.path.expanduser("~/Movies/Camtasia/047 - arcade.dev full course")
BUILD= os.path.join(BASE, "overlays/build/auth")
MOVS = os.path.join(BASE, "overlays/movs")
W,H,FPS = 1920,1080,30
DUR  = 12.15
AC   = "#46e5b7"
DN   = "#ff5c7a"
FONT = os.environ.get("GFX_FONT","Outfit")
FW   = "800" if FONT in ("Outfit","Poppins","Montserrat") else "400"

SECRETS = [("GOOGLE_CLIENT_SECRET", "GOCSPX-8vQ2p_1nR4yZ7kLm"),
           ("SLACK_BOT_TOKEN",      "xoxb-4471-99182-Kd8sQ2"),
           ("GOOGLE_REFRESH_TOKEN", "1//0eXa9pL_bTn4CgYIARAA")]
FIRMS = [("IBM", 10.20), ("Chase", 10.76), ("Pfizer", 11.32)]

def build():
    el, tw = [], []
    # ---------- scene A: the .env of secrets
    lines=[]
    for i,(k,v) in enumerate(SECRETS):
        lines.append(f'<div class="ln" id="ln{i}"><b>{k}</b>=<i>{v}</i><u></u></div>')
        tw.append(f'tl.fromTo("#ln{i}",{{opacity:0,x:-26}},{{opacity:1,x:0,duration:0.26,'
                  f'ease:"power3.out"}},{0.16+i*0.10:.2f});')
    el.append(f'<div id="sceneA"><div id="env"><div class="envbar">'
              f'<span>.env</span><em id="expiry">expires in 7 days</em></div>'
              f'<div class="envbody">{"".join(lines)}</div></div>'
              f'<div id="negs">'
              f'<div class="neg" id="ng0"><i>✕</i>No stored passwords</div>'
              f'<div class="neg" id="ng1"><i>✕</i>No tokens in a file</div></div>'
              f'</div>')
    tw += [
      'tl.fromTo("#env",{opacity:0,y:34,scale:0.97},{opacity:1,y:0,scale:1,duration:0.44,ease:"power3.out"},0.06);',
      # "passwords" 0.64 -> strike the secret line
      'tl.to("#ln0 u",{width:"100%",duration:0.30,ease:"power2.inOut"},0.64);',
      'tl.to("#ln0",{opacity:0.34,duration:0.26},0.94);',
      'tl.fromTo("#ng0",{opacity:0,x:-30},{opacity:1,x:0,duration:0.30,ease:"power3.out"},0.70);',
      # "tokens" 1.71 -> strike both token lines, expiry badge fires then dies
      'tl.fromTo("#expiry",{opacity:0,scale:0.8},{opacity:1,scale:1,duration:0.28,ease:"back.out(2.2)"},1.55);',
      'tl.to("#ln1 u",{width:"100%",duration:0.30,ease:"power2.inOut"},1.71);',
      'tl.to("#ln2 u",{width:"100%",duration:0.30,ease:"power2.inOut"},1.88);',
      'tl.to("#ln1,#ln2",{opacity:0.34,duration:0.26},2.10);',
      'tl.fromTo("#ng1",{opacity:0,x:-30},{opacity:1,x:0,duration:0.30,ease:"power3.out"},1.80);',
      # the whole file goes
      'tl.to("#env",{opacity:0,y:-22,scale:0.96,duration:0.42,ease:"power2.in"},3.05);',
      # "engineer" 4.19
      'tl.fromTo("#noeng",{opacity:0,scale:0.88},{opacity:1,scale:1,duration:0.36,ease:"back.out(2.1)"},4.19);',
      'tl.to("#sceneA",{opacity:0,duration:0.34,ease:"power2.in"},2.72);',
    ]
    # ---------- scene B: the receipt
    cards=[]
    for i,(name,at) in enumerate(FIRMS):
        cards.append(f'<div class="firm" id="fm{i}" style="left:{330+i*430}px">'
                     f'<span>{name}</span><em>Enterprise integrations</em></div>')
        tw.append(f'tl.fromTo("#fm{i}",{{opacity:0,y:300,scale:0.95}},{{opacity:1,y:0,scale:1,'
                  f'duration:0.60,ease:"power3.out"}},{at:.2f});')
    el.append(f'<div id="sceneB"><div id="yrs"><b>8</b><span>years building<br>these integrations</span></div>'
              f'{"".join(cards)}</div>')
    tw += ['tl.to("#sceneB",{opacity:1,duration:0.30,ease:"power2.out"},7.10);',
           'tl.fromTo("#yrs",{opacity:0,scale:0.90},{opacity:1,scale:1,duration:0.46,ease:"back.out(1.9)"},7.20);',
           'tl.to("#yrs",{y:-130,scale:0.72,duration:0.60,ease:"power3.inOut"},9.70);',
           'tl.to("#sceneB",{opacity:0,duration:0.30,ease:"power2.in"},11.85);']

    return f"""<!doctype html><html><head><meta charset="UTF-8"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:transparent;overflow:hidden}}
body{{width:{W}px;height:{H}px;font-family:{FONT},system-ui,sans-serif}}
#sceneA,#sceneB{{position:absolute;inset:0}}
#sceneB{{opacity:0}}
/* full-bleed dark ground so these read as true cutaways, not overlays */
#sceneA::before,#sceneB::before{{content:"";position:absolute;inset:0;
  background:radial-gradient(1300px 760px at 32% 36%, #101c22 0%, #070d10 62%, #04080a 100%)}}
#env{{position:absolute;left:250px;top:300px;width:900px;border-radius:18px;opacity:0;
  overflow:hidden;background:#0b1216;border:2px solid #ffffff26;
  box-shadow:0 30px 80px rgba(0,0,0,.6)}}
.envbar{{height:66px;background:#131e24;display:flex;align-items:center;
  justify-content:space-between;padding:0 26px;border-bottom:1px solid #ffffff14}}
.envbar span{{font-family:"Space Mono",monospace;font-size:26px;color:#ffffff8a}}
.envbar em{{font-style:normal;opacity:0;font-family:"Space Mono",monospace;font-size:21px;
  color:{DN};border:2px solid {DN};border-radius:999px;padding:6px 16px}}
.envbody{{padding:26px 30px 30px;display:flex;flex-direction:column;gap:16px}}
.ln{{position:relative;font-family:"Space Mono",monospace;font-size:25px;color:#cfe3e8;
  opacity:0;white-space:nowrap}}
.ln b{{color:#8fd8c4;font-weight:400}}
.ln i{{font-style:normal;color:#ffffff70}}
.ln u{{position:absolute;left:-4px;top:52%;height:5px;width:0;background:{DN};
  border-radius:3px;display:block;box-shadow:0 0 14px {DN}}}
#negs{{position:absolute;left:1250px;top:344px;display:flex;flex-direction:column;gap:26px}}
.neg{{opacity:0;display:flex;align-items:center;gap:18px;font-family:{FONT},sans-serif;
  font-weight:{FW};font-size:44px;color:#fff;text-transform:uppercase;white-space:nowrap}}
.neg i{{font-style:normal;color:{DN};font-size:40px}}
#noeng{{position:absolute;left:0;top:760px;width:{W}px;text-align:center;opacity:0;
  font-family:{FONT},sans-serif;font-weight:{FW};font-size:76px;color:{AC};
  text-transform:uppercase}}
#yrs{{position:absolute;left:0;top:330px;width:{W}px;display:flex;align-items:center;
  justify-content:center;gap:34px;opacity:0}}
#yrs b{{font-family:{FONT},sans-serif;font-weight:{FW};font-size:214px;line-height:0.84;
  color:{AC}}}
#yrs span{{font-family:{FONT},sans-serif;font-weight:{FW};font-size:56px;line-height:1.06;
  color:#fff;text-transform:uppercase}}
.firm{{position:absolute;top:596px;width:370px;height:210px;opacity:0;border-radius:24px;
  border:2px solid #ffffff2e;overflow:hidden;
  background:linear-gradient(160deg, rgba(255,255,255,0.10) 0%, rgba(255,255,255,0.035) 46%,
             rgba(8,16,18,0.55) 100%);
  box-shadow:0 18px 50px rgba(0,0,0,.55), inset 0 1px 0 rgba(255,255,255,0.18);
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px}}
.firm span{{font-family:{FONT},sans-serif;font-weight:{FW};font-size:64px;color:#fff;
  letter-spacing:0.02em}}
.firm em{{font-style:normal;font-family:"Space Mono",monospace;font-size:19px;
  letter-spacing:0.12em;text-transform:uppercase;color:{AC}}}
</style></head><body>
<div id="root" data-composition-id="auth" data-width="{W}" data-height="{H}"
     data-start="0" data-duration="{DUR:.2f}">
  <div class="clip" data-start="0" data-duration="{DUR:.2f}" data-track-index="0">{"".join(el)}</div>
</div>
<script>
window.__timelines=window.__timelines||{{}};
var tl=gsap.timeline({{paused:true}});
{chr(10).join('  '+x for x in tw)}
window.__timelines["auth"]=tl;
</script></body></html>"""

if __name__ == "__main__":
    os.makedirs(BUILD, exist_ok=True); os.makedirs(MOVS, exist_ok=True)
    open(os.path.join(BUILD,"index.html"),"w").write(build())
    env = dict(os.environ, PRODUCER_BROWSER_GPU_MODE="hardware")
    dst = os.path.join(MOVS,"auth.mov")
    subprocess.run(["hyperframes","render",BUILD,"-o",dst,"--format","mov",
                    "--fps",str(FPS),"--quiet"], env=env, check=True,
                   capture_output=True, text=True)
    print("->", dst, f"{os.path.getsize(dst)/1e9:.2f} GB")
