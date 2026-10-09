#!/usr/bin/env python3
"""The 0:00-11.57 payoff montage, built SYNTHETICALLY in HyperFrames.

Replaces the real screen-grabs. Two reasons: the ClickUp-settings grab juddered badly
(source measured 0.04 frame-to-frame, the zoompan version 0.46 - zoompan rounds its crop
window to whole pixels and 2x supersampling was not enough for fine UI text), and a built
scene lets every beat land exactly on its word instead of hoping the recording cooperates.

Motion here is CSS transform, which is subpixel and cannot judder.

Four scenes, cut to the VO measured off the delivered cut:
   0.00  "This is Claude, running on my real accounts"   terminal + the six apps connecting
   3.30  "read my email, found the one thread that..."    inbox streams, one thread highlights
   6.60  "wrote it up as a doc, filed it in my Drive"     the doc assembles and files itself
   9.10  "posted the summary to my team in Slack"         the Slack message composes
  11.57  face reveal

Nate kit used: #1 cold-open b-roll, #8 receipt + animated highlighter, #15 self-drawing,
#16 constant push-in, #3 chips (those ride in intro-gfx.mov on top).

Output: overlays/montage.mp4 (opaque; the VO comes from the camera track)
"""
import json, os, subprocess

BASE = os.path.expanduser("~/Movies/Camtasia/047 - arcade.dev full course")
BUILD= os.path.join(BASE, "overlays/build/montage")
ICONS= os.path.join(BASE, "overlays/build/icons/icons.json")
OUT  = os.path.join(BASE, "overlays/montage.mp4")
W, H, FPS, DUR = 1920, 1080, 30, 11.70
AC   = "#46e5b7"
FONT = os.environ.get("GFX_FONT", "Outfit")
FW   = "800" if FONT in ("Outfit","Poppins","Montserrat") else "400"

APPS  = [("Gmail","Gmail"),("Calendar","Google Calendar"),("Drive","Google Drive"),
         ("Docs","Google Docs"),("Slack",None),("ClickUp","ClickUp")]
MAILS = [("Newsletter digest","09:02"), ("Re: invoice #4471","08:41"),
         ("Blotato partnership — YouTube Partnership AI","08:12"),
         ("Standup notes","07:58"), ("Calendar invite: Miles x Tyler","07:30")]
HIT = 2   # the thread that actually mattered

def build():
    ic = json.load(open(ICONS))
    rows, tw = [], []
    for i,(label,key) in enumerate(APPS):
        d = ic.get(key) if key else None
        # real marks from simple-icons; Slack is not in that set (removed at their
        # request) so it gets a neutral tile rather than an invented logo
        mark = (f'<svg class="mk" viewBox="0 0 24 24"><path fill="#{d["hex"]}" d="{d["path"]}"/></svg>'
                if d else '<i class="mk nomk">#</i>')
        rows.append(f'<div class="app" id="ap{i}">{mark}<span>{label}</span><b>✓</b></div>')
        tw += [f'tl.fromTo("#ap{i}",{{opacity:0,x:-24}},{{opacity:1,x:0,duration:0.26,ease:"power3.out"}},{0.90+i*0.13:.2f});',
               f'tl.to("#ap{i} b",{{opacity:1,scale:1,duration:0.24,ease:"back.out(2.6)"}},{1.16+i*0.13:.2f});']
    mails=[]
    for i,(s,t) in enumerate(MAILS):
        cls = "mail hit" if i==HIT else "mail"
        mails.append(f'<div class="{cls}" id="ml{i}"><u></u><span>{s}</span><em>{t}</em></div>')
        tw += [f'tl.fromTo("#ml{i}",{{opacity:0,x:22}},{{opacity:{0.42 if i!=HIT else 1},x:0,duration:0.24,ease:"power2.out"}},{3.60+i*0.12:.2f});']
    tw += [f'tl.to("#ml{HIT} u",{{width:"100%",duration:0.52,ease:"power2.inOut"}},4.55);',
           f'tl.fromTo("#mtag",{{opacity:0,scale:0.8}},{{opacity:1,scale:1,duration:0.32,ease:"back.out(2.4)"}},5.05);']

    scenes = "".join([
      f'<div class="sc" id="s0"><div class="win"><div class="bar"><i></i><i></i><i></i>'
      f'<svg id="star" viewBox="0 0 40 40"><g>'
      f'<path d="M20 3v34M3 20h34M8 8l24 24M32 8L8 32"/></g></svg>'
      f'<p>claude — real accounts</p></div><div class="pane">'
      f'<div class="cmd"><span class="pr">claude&gt;</span> <span id="typ"></span><span class="cur"></span></div>'
      f'<div class="apps">{"".join(rows)}</div></div></div></div>',

      f'<div class="sc" id="s1"><div class="win"><div class="bar"><i></i><i></i><i></i>'
      f'<p>Gmail.ListEmails</p></div><div class="pane">'
      f'<div class="cmd"><span class="pr">→</span> scanning 24 threads</div>'
      f'<div class="mails">{"".join(mails)}</div>'
      f'<div id="mtag">the one that mattered</div></div></div></div>',

      f'<div class="sc" id="s2"><div class="doc" id="doc"><div class="dbar"></div>'
      f'<div class="dmark"></div><div class="dtitle" id="dt"></div>'
      f'<div class="dl" id="dl0"></div><div class="dl" id="dl1"></div><div class="dl" id="dl2"></div></div>'
      f'<div class="folder" id="fold"><b></b><span>My Drive / blotato</span></div></div>',

      f'<div class="sc" id="s3"><div class="slack"><div class="sbar"><b>#</b>ai</div>'
      f'<div class="msg" id="msg"><div class="av"></div><div class="mb">'
      f'<div class="who">tyleryt <em>1:49 PM</em></div>'
      f'<div class="mt" id="mt"></div>'
      f'<div class="ml" id="sl0"></div><div class="ml" id="sl1"></div></div></div></div></div>',
    ])

    # scene cross-fades + a continuous drift so no frame is ever still
    CUT=[(0.00,3.30),(3.30,6.60),(6.60,9.10),(9.10,11.70)]
    for i,(a,b) in enumerate(CUT):
        # NO transform on the scene itself. A continuous scale forces the renderer to
        # re-rasterize every glyph and 1px border each frame, which reads as shimmer
        # (measured 0.365 with nothing building; GPU layer promotion only got it to 0.327).
        # Motion comes from the element builds plus the text-free glow layer below.
        tw += [f'tl.to("#s{i}",{{opacity:1,duration:0.26,ease:"power2.out"}},{max(0,a-0.13):.2f});']
        if i < len(CUT)-1:
            tw.append(f'tl.to("#s{i}",{{opacity:0,duration:0.26,ease:"power2.in"}},{b-0.13:.2f});')

    typed = "use my real accounts"
    tw.append(f'tl.to("#typ",{{duration:0.62,ease:"none",onUpdate:function(){{'
              f'var s="{typed}";document.getElementById("typ").textContent='
              f's.slice(0,Math.round(this.progress()*s.length));}}}},0.18);')
    dtitle = "Blotato Partnership — Summary"
    tw.append(f'tl.to("#dt",{{duration:0.50,ease:"none",onUpdate:function(){{'
              f'var s="{dtitle}";document.getElementById("dt").textContent='
              f's.slice(0,Math.round(this.progress()*s.length));}}}},7.10);')
    for i in range(3):
        tw.append(f'tl.fromTo("#dl{i}",{{scaleX:0}},{{scaleX:1,duration:0.26,ease:"power2.out"}},{7.55+i*0.13:.2f});')
    tw += ['tl.fromTo("#fold",{opacity:0,y:26},{opacity:1,y:0,duration:0.34,ease:"back.out(1.8)"},8.15);',
           'tl.to("#doc",{x:250,y:150,scale:0.34,opacity:0,duration:0.52,ease:"power2.in"},8.45);',
           'tl.to("#fold b",{backgroundColor:"'+AC+'",duration:0.28},8.90);']
    mtxt = "Blotato partnership — summary"
    tw.append(f'tl.fromTo("#msg",{{opacity:0,y:26}},{{opacity:1,y:0,duration:0.34,ease:"power3.out"}},9.35);')
    tw.append(f'tl.to("#mt",{{duration:0.52,ease:"none",onUpdate:function(){{'
              f'var s="{mtxt}";document.getElementById("mt").textContent='
              f's.slice(0,Math.round(this.progress()*s.length));}}}},9.60);')
    for i in range(2):
        tw.append(f'tl.fromTo("#sl{i}",{{scaleX:0}},{{scaleX:1,duration:0.28,ease:"power2.out"}},{10.20+i*0.16:.2f});')

    return f"""<!doctype html><html><head><meta charset="UTF-8"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W}px;height:{H}px;font-family:{FONT},system-ui,sans-serif;
  background:radial-gradient(1200px 700px at 30% 20%, #12222a 0%, #080e12 62%, #05090b 100%)}}
.sc{{position:absolute;inset:0;opacity:0;display:flex;align-items:center;justify-content:center;gap:64px}}
#glow{{position:absolute;left:-18%;top:-22%;width:136%;height:150%;
  background:radial-gradient(closest-side at 34% 40%, rgba(70,229,183,.16), rgba(70,229,183,0) 70%),
             radial-gradient(closest-side at 74% 66%, rgba(66,133,244,.13), rgba(66,133,244,0) 70%)}}
.win{{width:1560px;border-radius:20px;overflow:hidden;background:#0b1216;
  border:1px solid #ffffff1f;box-shadow:0 40px 120px rgba(0,0,0,.7)}}
.bar{{height:64px;background:#101a1f;display:flex;align-items:center;gap:10px;padding:0 20px;
  border-bottom:1px solid #ffffff14}}
.bar i{{width:16px;height:16px;border-radius:50%;background:#3a4b53}}
.bar p{{margin-left:12px;color:#ffffff7a;font-size:25px;font-family:"Space Mono",monospace}}
#star{{width:30px;height:30px;margin-left:22px;overflow:visible;transform-origin:50% 50%}}
#star path{{stroke:{AC};stroke-width:5;stroke-linecap:round;fill:none;
  stroke-dasharray:44;stroke-dashoffset:44;filter:drop-shadow(0 0 8px {AC})}}
.pane{{padding:46px 54px 56px}}
.cmd{{font-family:"Space Mono",monospace;font-size:40px;color:#dfeef2;margin-bottom:26px}}
.pr{{color:{AC}}}
.cur{{display:inline-block;width:16px;height:40px;background:{AC};vertical-align:-4px;margin-left:3px}}
.apps{{display:grid;grid-template-columns:1fr 1fr;gap:20px 40px}}
.app{{display:flex;align-items:center;gap:22px;padding:22px 26px;border-radius:12px;
  background:#ffffff08;border:1px solid #ffffff14;opacity:0}}
.mk{{width:44px;height:44px;flex:none}}
.nomk{{border-radius:10px;background:#ffffff2e;color:#fff;font-style:normal;font-size:26px;
  display:flex;align-items:center;justify-content:center}}
.app span{{font-size:40px;font-weight:{FW};color:#eef7f9;flex:1}}
.app b{{opacity:0;transform:scale(.4);color:{AC};font-size:38px}}
.mails{{display:flex;flex-direction:column;gap:11px}}
.mail{{position:relative;display:flex;align-items:center;gap:24px;padding:22px 26px;
  border-radius:11px;background:#ffffff07;border:1px solid #ffffff12;opacity:0}}
.mail span{{font-size:34px;color:#e6f3f6;flex:1;white-space:nowrap;overflow:hidden}}
.mail em{{font-style:normal;font-family:"Space Mono",monospace;font-size:25px;color:#ffffff5c}}
.mail u{{position:absolute;left:0;top:0;bottom:0;width:0;background:rgba(70,229,183,.20);
  border-left:4px solid {AC};text-decoration:none;border-radius:11px}}
.mail.hit span{{color:#fff;font-weight:{FW}}}
#mtag{{margin-top:30px;display:inline-block;padding:15px 30px;border-radius:999px;
  border:2px solid {AC};color:{AC};font-family:"Space Mono",monospace;font-size:27px;
  letter-spacing:.10em;text-transform:uppercase;opacity:0}}
.doc{{width:1000px;height:650px;border-radius:20px;background:#f9fbfd;position:relative;
  overflow:hidden;box-shadow:0 34px 90px rgba(0,0,0,.65)}}
.dbar{{height:12px;background:#4285f4}}
.dmark{{position:absolute;left:48px;top:76px;width:84px;height:112px;border-radius:8px;background:#4285f4}}
.dtitle{{position:absolute;left:158px;top:88px;right:34px;font-size:50px;font-weight:{FW};
  color:#101418;white-space:nowrap;overflow:hidden}}
.dl{{position:absolute;left:158px;height:13px;border-radius:6px;background:#c2cedb;
  transform:scaleX(0);transform-origin:0 50%}}
#dl0{{top:290px;width:720px}} #dl1{{top:346px;width:780px}} #dl2{{top:402px;width:540px}}
.folder{{display:flex;align-items:center;gap:26px;padding:36px 44px;border-radius:18px;
  background:#ffffff14;border:2px solid #ffffff4d;opacity:0}}
.folder b{{width:86px;height:68px;border-radius:8px;background:#5f6b73;display:block}}
.folder span{{font-size:38px;font-weight:{FW};color:#eaf5f7}}
.slack{{width:1420px;border-radius:20px;overflow:hidden;background:#151f26;
  border:2px solid #ffffff3d;box-shadow:0 34px 90px rgba(0,0,0,.65)}}
.sbar{{height:92px;background:#1d2a33;display:flex;align-items:center;padding:0 34px;
  font-size:36px;font-weight:{FW};color:#eaf5f7;gap:8px}}
.sbar b{{color:#ffffff66}}
.msg{{display:flex;gap:26px;padding:40px 38px 50px;opacity:0}}
.av{{width:70px;height:70px;border-radius:14px;background:{AC};flex:none}}
.mb{{flex:1}}
.who{{font-size:31px;font-weight:{FW};color:#eaf5f7;margin-bottom:12px}}
.who em{{font-style:normal;font-size:19px;color:#ffffff52;margin-left:12px;font-weight:400}}
.mt{{font-size:42px;color:#f2fbfd;min-height:46px;white-space:nowrap;overflow:hidden}}
.ml{{height:12px;border-radius:6px;background:#ffffff4d;margin-top:18px;
  transform:scaleX(0);transform-origin:0 50%}}
#sl0{{width:740px}} #sl1{{width:560px}}
</style></head><body>
<div id="root" data-composition-id="mont" data-width="{W}" data-height="{H}"
     data-start="0" data-duration="{DUR:.2f}">
  <div class="clip" data-start="0" data-duration="{DUR:.2f}" data-track-index="0"><div id="glow"></div>{scenes}</div>
</div>
<script>
window.__timelines=window.__timelines||{{}};
  var tl0=gsap.timeline({{paused:true}});
var tl=gsap.timeline({{paused:true}});
{chr(10).join('  '+x for x in tw)}
  tl.fromTo("#star",{{opacity:0,scale:0.3,rotation:-90}},{{opacity:1,scale:1,rotation:0,duration:0.52,ease:"back.out(2.2)"}},0.10);
  tl.to("#star path",{{strokeDashoffset:0,duration:0.46,ease:"power2.out"}},0.24);
  tl.to("#star",{{opacity:0.5,duration:0.55,repeat:4,yoyo:true,ease:"sine.inOut"}},1.20);
  tl.fromTo("#glow",{{x:-70,y:-40}},{{x:70,y:40,duration:11.70,ease:"none"}},0);
window.__timelines["mont"]=tl;
</script></body></html>"""

if __name__ == "__main__":
    os.makedirs(BUILD, exist_ok=True)
    open(os.path.join(BUILD,"index.html"),"w").write(build())
    env = dict(os.environ, PRODUCER_BROWSER_GPU_MODE="hardware")
    subprocess.run(["hyperframes","render",BUILD,"-o",OUT,"--format","mp4",
                    "--fps",str(FPS),"--quiet"], env=env, check=True,
                   capture_output=True, text=True)
    print("->", OUT, f"(font: {FONT})")
