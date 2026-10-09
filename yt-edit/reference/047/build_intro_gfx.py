#!/usr/bin/env python3
"""The whole 56.29s intro graphics package as ONE transparent composition.

Built as a single timeline rather than seven MOVs so every beat shares one clock and
nothing can drift at an overlay boundary. Every animation is pinned to a word timestamp
measured off the delivered cut (transcript/intro_words.json), not to the pre-shoot spec.

Layout constraint: clips 1-7 are full-frame CAMERA and he sits centred, warm-pixel span
x 800-1188 measured across six frames. So chips live in the left band (x 90-700) and the
two full-screen beats (the 4-card build, the roadmap) darken the frame behind themselves
with a plate, matching the spec's "Face? No" rows.

Beats:
   0.55-11.2   montage chips: REAL ACCOUNT / GMAIL / DOCS / DRIVE / SLACK
  11.60        "6 APPS" lands on the face reveal
  15.60-22.9   the wall: NOT THE AI, then PASSWORDS/TOKENS/SCOPES struck red
  23.40-32.5   the 4-card deliverable build, flips green   (plate)
  33.30-38.9   objection kill: two crossed lines + NO ENGINEER REQUIRED
  39.60-45.0   8 YEARS + IBM / CHASE / PFIZER lower-thirds
  45.40-49.9   USED TO BE THE HARD PART -> WHAT ACTUALLY WORKS NOW
  50.30-56.3   "In this video" roadmap, item 3 left teased   (plate)

Output: overlays/movs/intro-gfx.mov (transparent ProRes 4444)
"""
import json, os, re, subprocess

BASE = os.path.expanduser("~/Movies/Camtasia/047 - arcade.dev full course")
BUL  = os.path.join(BASE, "overlays/build/bot/compositions/components/bottom-up-letters.html")
BUILD= os.path.join(BASE, "overlays/build/introgfx")
MOVS = os.path.join(BASE, "overlays/movs")

DUR  = 56.40          # 0.11 of spare tail past the 56.29 cut
W,H  = 1920, 1080
FPS  = 30
AC   = "#46e5b7"
FONT = os.environ.get("GFX_FONT", "Outfit")
FW   = "800" if FONT in ("Outfit","Poppins","Montserrat") else "400"      # accent teal
DN   = "#ff5c7a"      # danger
LX   = 90             # left safe band

ICONS = os.path.join(BASE, "overlays/build/icons/icons.json")


def grab(path, tag):
    m = re.search(rf"<{tag}\b.*?</{tag}>", open(path).read(), re.S)
    if not m: raise SystemExit(f"no <{tag}> in {path}")
    return m.group(0)

CHIPS = [("GMAIL", 3.50, 6.40),
         ("GOOGLE DOCS", 6.80, 7.95), ("DRIVE", 8.05, 8.95), ("SLACK", 9.40, 11.45)]
CARDS = [("Email", 26.85), ("Calendar", 27.25), ("Tasks", 29.37), ("Runs at 7AM", 30.80)]
FIRMS = [("IBM", 43.30), ("CHASE", 43.90), ("PFIZER", 44.50)]
# The VO names three phases; the grid shows the six modules they actually contain, and
# each phase lights its own tiles. Deliberately NOT Nate's vertical glass slabs - wide
# tiles, self-drawing line glyphs, phase-grouped activation.
GLYPH = {
 "hub":   "M32 8v14M32 42v14M8 32h14M42 32h14M32 22a10 10 0 100 20 10 10 0 100-20",
 "term":  "M8 12h48v40H8zM8 22h48M17 33l7 6-7 6M31 45h14",
 "server":"M10 12h44v14H10zM10 32h44v14H10zM18 19h2M18 39h2M40 19h8M40 39h8",
 "chain": "M24 24l-7 7a9 9 0 0013 13l7-7M40 40l7-7a9 9 0 00-13-13l-7 7M26 38l12-12",
 "crew":  "M20 30a6 6 0 100-12 6 6 0 100 12M44 30a6 6 0 100-12 6 6 0 100 12M32 50a8 8 0 10 0-16 8 8 0 100 16M10 46c0-6 4-9 10-9M54 46c0-6-4-9-10-9",
 "clock": "M32 10a22 22 0 100 44 22 22 0 100-44M32 20v13l9 6",
}
MODULES = [
 (1, "hub",    "What Arcade is",        0),
 (2, "term",   "Claude Code + MCP",     0),
 (3, "server", "Your own MCP server",   1),
 (4, "chain",  "LangChain",             1),
 (5, "crew",   "CrewAI",                1),
 (6, "clock",  "Runs while you sleep",  2),
]
PHASE_AT = [51.54, 52.80, 53.96]

def build():
    el, tw = [], []
    # ---------- Claude mark over the cold open (replaces the old REAL ACCOUNT pill)
    cl = json.load(open(ICONS)).get("Claude")
    if cl:
        el.append(f'<div id="claudeterm">'
                  f'<div class="ctbar">'
                  f'<i></i><i></i><i></i>'
                  f'<svg viewBox="0 0 24 24"><path d="{cl["path"]}"/></svg>'
                  f'<span>claude</span></div>'
                  f'<div class="ctbody">'
                  f'<div class="ctline"><b>&gt;</b> <em id="ctxt"></em><u></u></div>'
                  f'<div class="ctok" id="ctok">&#10003; 6 apps connected</div>'
                  f'</div></div>')
        typed = "on my real accounts"
        tw += ['tl.fromTo("#claudeterm",{opacity:0,scale:0.72,y:26},'
               '{opacity:1,scale:1,y:0,duration:0.52,ease:"back.out(2.2)"},0.40);',
               'tl.fromTo("#claudeterm .ctbar svg",{rotation:-140,scale:0.4},'
               '{rotation:0,scale:1,duration:0.66,ease:"back.out(2.0)"},0.52);',
               f'tl.to("#ctxt",{{duration:0.62,ease:"none",onUpdate:function(){{'
               f'var s="{typed}";document.getElementById("ctxt").textContent='
               f's.slice(0,Math.round(this.progress()*s.length));}}}},0.90);',
               'tl.to("#ctok",{opacity:1,y:0,duration:0.34,ease:"back.out(2.0)"},1.72);',
               'tl.to("#claudeterm",{opacity:0,scale:0.95,duration:0.30,ease:"power2.in"},3.02);']

    # ---------- montage chips (bottom-left, one at a time)
    for i,(t,a,b) in enumerate(CHIPS):
        el.append(f'<div class="chip" id="ch{i}">{t}</div>')
        tw += [f'tl.fromTo("#ch{i}",{{opacity:0,x:-46}},{{opacity:1,x:0,duration:0.34,ease:"power3.out"}},{a:.2f});',
               f'tl.to("#ch{i}",{{opacity:0,x:26,duration:0.24,ease:"power2.in"}},{b:.2f});']

    # ---------- 6 APPS on the face reveal
    el.append('<div id="six"><b>6</b><span>APPS</span><i>none touched by hand</i></div>')
    tw += ['tl.fromTo("#six",{opacity:0,scale:0.72},{opacity:1,scale:1,duration:0.42,ease:"back.out(2.3)"},11.60);',
           'tl.to("#six",{opacity:0,y:-24,duration:0.30,ease:"power2.in"},13.85);']

    # ---------- the wall beat now lives in overlays/wall.mp4 as a FULL-FRAME cutaway
    # (build_wall.py). It used to be text over 8.5s of talking head, which was the longest
    # face-only stretch in the intro and sat right on the retention drop.

    # ---------- the promise, as a live morning-brief HUD (Nate kit #6, the one dashboard
    # type we had not used). Sits in the left band so his face stays fully visible - no
    # plate at all, which is what keeps the face ratio where it should be.
    el.append('<div id="hud"><div class="hhead"><b>Morning brief</b><em id="hclock">7:00 AM</em></div>'
              '<div class="hrow" id="hr0"><i></i><span>Email</span><u></u><s>12 threads &rarr; 1 summary</s></div>'
              '<div class="hrow" id="hr1"><i></i><span>Calendar</span><u></u><s>4 events today</s></div>'
              '<div class="hrow" id="hr2"><i></i><span>Tasks</span><u></u><s>7 open in ClickUp</s></div>'
              '<div id="hsched"><b>&#9210;</b>Runs on a server, daily</div></div>')
    tw += ['tl.fromTo("#hud",{opacity:0,x:-46},{opacity:1,x:0,duration:0.44,ease:"power3.out"},25.30);']
    # re-transcribing src 86-102 in isolation put 'tasks' at 28.27, not the 29.37 the
    # full-file pass reported - Whisper had stretched it. Rows now land on the words.
    for i,at in enumerate([26.85, 27.22, 28.27]):
        tw += [f'tl.fromTo("#hr{i}",{{opacity:0,x:-26}},{{opacity:1,x:0,duration:0.30,ease:"power3.out"}},{at:.2f});',
               f'tl.to("#hr{i} u",{{scaleX:1,duration:0.52,ease:"power2.out"}},{at+0.10:.2f});',
               f'tl.to("#hr{i} i",{{backgroundColor:"{AC}",boxShadow:"0 0 18px {AC}",duration:0.30}},{at+0.44:.2f});',
               f'tl.to("#hr{i} s",{{opacity:1,duration:0.28}},{at+0.46:.2f});']
    tw += ['tl.fromTo("#hsched",{opacity:0,y:20},{opacity:1,y:0,duration:0.36,ease:"back.out(1.8)"},29.93);',
           'tl.to("#hclock",{color:"' + AC + '",duration:0.30},30.80);',
           'tl.to("#hsched",{boxShadow:"0 0 40px rgba(70,229,183,0.5)",duration:0.5,repeat:1,yoyo:true},30.40);',
           'tl.to("#hud",{opacity:0,x:-34,duration:0.34,ease:"power2.in"},32.05);']

    # ---------- "you don't need to be an engineer" rides ON the kitchen b-roll
    el.append('<div id="noeng">No engineer required</div>')
    tw += ['tl.fromTo("#noeng",{opacity:0,scale:0.86},{opacity:1,scale:1,duration:0.38,'
           'ease:"back.out(2.1)"},37.19);',
           'tl.to("#noeng",{opacity:0,duration:0.28,ease:"power2.in"},38.30);']

    # ---------- the objection-kill and credibility beats are now FULL-FRAME cutaways in
    # overlays/movs/auth.mov (build_auth.py). Together with the wall cutaway they break up
    # what measured as 18.2s of unbroken talking head.

    # ---------- the hard-part / works-now beat is now a FULL-FRAME cutaway in
    # overlays/movs/hardpart.mov (build_hardpart.py) - the old-way boilerplate struck out
    # and replaced by the one command. It was the last 5.25s bare-face stretch.

    # ---------- roadmap (full-screen, plate)
    el.append('<div id="plate2" class="plate"></div>')
    tw += ['tl.to("#plate2",{opacity:1,duration:0.32,ease:"power2.out"},50.30);',
           'tl.to("#plate2",{backgroundColor:"rgba(4,8,10,0.62)",duration:0.34},50.30);',
           'tl.to("#plate2",{opacity:0,duration:0.34,ease:"power2.in"},55.60);']
    el.append('<div id="rhead" class="rhead">In this video</div>')
    tw += ['tl.fromTo("#rhead",{opacity:0,y:-18},{opacity:1,y:0,duration:0.34,ease:"power3.out"},50.55);',
           'tl.to("#rhead",{opacity:0,duration:0.30},55.62);']
    tiles=[]
    for i,(num,gl,label,phase) in enumerate(MODULES):
        # one row of six. 262 wide + 26 gap = 1706 total, centred at x=107.
        tiles.append(
          f'<div class="tile" id="tl{i}" style="left:{107+i*288}px">'
          f'<i class="fill"></i><em>{num}</em>'
          f'<svg class="gl" viewBox="0 0 64 64"><path d="{GLYPH[gl]}"/></svg>'
          f'<span>{label}</span><u></u></div>')
        # Nate's actual arrival: the card TRAVELS from below the group into its slot over
        # ~0.65s, decelerating in. Measured off his 8fps frames at 16.32-17.07s. The cards
        # already placed do not move.
        st = 50.35 + i*0.15
        tw.append(f'tl.fromTo("#tl{i}",{{opacity:0,y:430,scale:0.94}},'
                  f'{{opacity:1,y:0,scale:1,duration:0.66,ease:"power3.out"}},{st:.2f});')
        tw.append(f'tl.to("#tl{i} .gl path",{{strokeDashoffset:0,duration:0.50,'
                  f'ease:"power2.out"}},{st+0.22:.2f});')
        at = PHASE_AT[phase]
        tw += [f'tl.to("#tl{i}",{{borderColor:"{AC}",duration:0.34}},{at:.2f});',
               f'tl.to("#tl{i} .fill",{{scaleY:1,duration:0.52,ease:"power2.out"}},{at:.2f});',
               f'tl.to("#tl{i} .gl path",{{stroke:"{AC}",duration:0.34}},{at:.2f});',
               f'tl.to("#tl{i} span",{{color:"#ffffff",duration:0.30}},{at:.2f});',
               f'tl.to("#tl{i}",{{boxShadow:"0 0 46px rgba(70,229,183,0.42), inset 0 0 40px rgba(70,229,183,0.14)",duration:0.40}},{at:.2f});',
               f'tl.to("#tl{i} u",{{scaleX:1,duration:0.42,ease:"power2.out"}},{at+0.06:.2f});',
               f'tl.to("#tl{i}",{{opacity:0,y:-30,duration:0.32,ease:"power2.in"}},{55.55+i*0.02:.2f});']
    tw.append('tl.to("#tl5",{boxShadow:"0 0 66px rgba(70,229,183,0.72), inset 0 0 46px rgba(70,229,183,0.20)",'
              'duration:0.46,repeat:2,yoyo:true,ease:"sine.inOut"},54.30);')
    # a slow light swoosh behind the row - text-free, so it cannot shimmer
    el.append('<div id="swoosh"></div>')
    tw.append('tl.fromTo("#swoosh",{opacity:0,x:-460,rotation:-8},{opacity:1,x:0,rotation:-8,'
              'duration:0.6,ease:"power2.out"},50.30);')
    tw.append('tl.to("#swoosh",{x:420,duration:5.2,ease:"none"},50.90);')
    tw.append('tl.to("#swoosh",{opacity:0,duration:0.34},55.55);')
    el += tiles

    return f"""<!doctype html>
<html lang="en"><head><meta charset="UTF-8"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
{grab(BUL,"style")}
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:transparent;overflow:hidden}}
body{{width:{W}px;height:{H}px;font-family:Inter,system-ui,sans-serif}}
#hud{{position:absolute;left:84px;top:392px;width:706px;opacity:0;border-radius:20px;
  background:rgba(6,12,14,0.90);border:2px solid #ffffff2b;padding:24px 26px 26px;
  box-shadow:0 22px 60px rgba(0,0,0,0.6)}}
.hhead{{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:20px}}
.hhead b{{font-family:{FONT},sans-serif;font-weight:{FW};font-size:34px;color:#fff;
  text-transform:uppercase;letter-spacing:0.02em}}
.hhead em{{font-style:normal;font-family:"Space Mono",monospace;font-weight:700;font-size:24px;
  color:#ffffff7a}}
.hrow{{position:relative;opacity:0;padding:13px 0 15px;border-top:1px solid #ffffff17}}
.hrow i{{display:inline-block;width:13px;height:13px;border-radius:50%;background:#ffffff38;
  margin-right:15px;vertical-align:1px}}
.hrow span{{font-family:{FONT},sans-serif;font-weight:{FW};font-size:31px;color:#fff;
  text-transform:uppercase}}
.hrow s{{display:block;margin:7px 0 0 28px;opacity:0;text-decoration:none;
  font-family:"Space Mono",monospace;font-size:21px;color:{AC}}}
.hrow u{{position:absolute;left:28px;right:0;bottom:6px;height:4px;border-radius:2px;
  background:{AC};transform:scaleX(0);transform-origin:0 50%;text-decoration:none;opacity:.65}}
#hsched{{margin-top:20px;opacity:0;display:flex;align-items:center;gap:14px;
  padding:13px 20px;border-radius:12px;background:rgba(70,229,183,0.12);border:2px solid {AC};
  font-family:{FONT},sans-serif;font-weight:{FW};font-size:25px;color:{AC};
  text-transform:uppercase}}
#hsched b{{font-size:26px}}
.plate{{position:absolute;inset:0;background:rgba(6,10,12,0.42);opacity:0}}
#danger{{position:absolute;inset:0;opacity:0;pointer-events:none;
  box-shadow:inset 0 0 240px 90px rgba(255,92,122,0.42)}}

#claudeterm{{position:absolute;left:96px;top:742px;width:520px;opacity:0;border-radius:16px;
  overflow:hidden;background:rgba(7,12,15,0.94);border:2px solid #ffffff2e;
  box-shadow:0 22px 60px rgba(0,0,0,0.62)}}
.ctbar{{height:52px;background:rgba(255,255,255,0.06);display:flex;align-items:center;
  gap:9px;padding:0 18px;border-bottom:1px solid #ffffff17}}
.ctbar i{{width:11px;height:11px;border-radius:50%;background:#3b4b54;flex:none}}
.ctbar svg{{width:26px;height:26px;flex:none;margin-left:12px;transform-origin:50% 50%}}
.ctbar svg path{{fill:#D97757}}
.ctbar span{{font-family:"Space Mono",monospace;font-size:21px;color:#ffffff8a;margin-left:8px}}
.ctbody{{padding:22px 22px 24px}}
.ctline{{font-family:"Space Mono",monospace;font-size:25px;color:#e4f2f5;white-space:nowrap}}
.ctline b{{color:{AC};font-weight:400}}
.ctline em{{font-style:normal}}
.ctline u{{display:inline-block;width:11px;height:24px;background:{AC};vertical-align:-4px;
  margin-left:3px;text-decoration:none}}
.ctok{{margin-top:16px;opacity:0;transform:translateY(10px);
  font-family:"Space Mono",monospace;font-size:21px;color:{AC}}}
.chip{{position:absolute;left:{LX}px;top:892px;opacity:0;
  padding:16px 30px;border-radius:999px;background:rgba(8,14,16,0.82);
  border:2px solid {AC};font-family:"Space Mono",monospace;font-weight:700;
  font-size:32px;letter-spacing:0.12em;color:{AC};white-space:nowrap;
  box-shadow:0 0 34px rgba(70,229,183,0.30)}}

#six{{position:absolute;left:{LX}px;top:706px;opacity:0;display:flex;
  align-items:baseline;gap:20px;flex-wrap:wrap;width:600px}}
#six b{{font-family:{FONT},sans-serif;font-weight:{FW};font-size:186px;line-height:0.82;color:{AC};
  text-shadow:0 6px 40px rgba(0,0,0,0.95)}}
#six span{{font-family:{FONT},sans-serif;font-weight:{FW};font-size:82px;color:#fff;
  text-transform:uppercase;text-shadow:0 4px 26px rgba(0,0,0,0.95)}}
#six i{{flex-basis:100%;font-style:normal;font-family:"Space Mono",monospace;
  font-weight:700;font-size:25px;letter-spacing:0.14em;color:#ffffffcc;
  text-transform:uppercase;text-shadow:0 2px 16px rgba(0,0,0,0.95)}}

.kin{{position:absolute;left:{LX}px;top:470px;opacity:0;width:920px;white-space:nowrap;
  font-family:{FONT},sans-serif;font-weight:{FW};font-size:106px;line-height:0.98;color:#fff;
  text-transform:uppercase;text-shadow:0 4px 32px rgba(0,0,0,0.95)}}
.risk{{position:absolute;left:{LX}px;top:640px;opacity:0;white-space:nowrap;
  font-family:{FONT},sans-serif;font-weight:{FW};font-size:64px;color:#fff;text-transform:uppercase;
  text-shadow:0 3px 24px rgba(0,0,0,0.95)}}
.risk u{{position:absolute;left:-6px;top:52%;height:8px;width:0;background:{DN};
  border-radius:4px;display:block;box-shadow:0 0 20px {DN}}}
.stamp{{position:absolute;left:{LX}px;top:930px;opacity:0;white-space:nowrap;
  font-family:{FONT},sans-serif;font-weight:{FW};font-size:72px;color:{DN};text-transform:uppercase;
  text-shadow:0 4px 28px rgba(0,0,0,0.95)}}

.phead{{position:absolute;left:0;top:250px;width:{W}px;text-align:center;opacity:0;
  font-family:{FONT},sans-serif;font-weight:{FW};font-size:62px;color:#fff;text-transform:uppercase;
  letter-spacing:0.02em}}
.card{{position:absolute;top:430px;width:390px;height:250px;opacity:0;
  border:3px solid #ffffff3d;border-radius:22px;background:rgba(6,12,14,0.82);
  box-shadow:0 16px 44px rgba(0,0,0,0.5);
  padding:28px 30px;display:flex;flex-direction:column;justify-content:space-between}}
.card em{{font-style:normal;font-family:"Space Mono",monospace;font-weight:700;
  font-size:26px;color:{AC};letter-spacing:0.16em}}
.card span{{font-family:{FONT},sans-serif;font-weight:{FW};font-size:44px;color:#fff;line-height:1.02;
  text-transform:uppercase;white-space:nowrap}}
.card b{{position:absolute;right:26px;top:22px;opacity:0;transform:scale(0.4);
  font-size:46px;color:{AC};line-height:1}}

.neg{{position:absolute;left:{LX}px;top:560px;opacity:0;display:flex;align-items:center;
  gap:20px;font-family:{FONT},sans-serif;font-weight:{FW};font-size:52px;color:#fff;text-transform:uppercase;
  text-shadow:0 3px 24px rgba(0,0,0,0.95);white-space:nowrap}}
.neg i{{font-style:normal;color:{DN};font-size:56px}}
.stamp2{{position:absolute;left:{LX}px;top:790px;opacity:0;padding:18px 34px;
  border-radius:16px;background:rgba(70,229,183,0.14);border:3px solid {AC};
  font-family:{FONT},sans-serif;font-weight:{FW};font-size:48px;white-space:nowrap;color:{AC};text-transform:uppercase;
  box-shadow:0 0 44px rgba(70,229,183,0.30)}}

#yrs{{position:absolute;left:{LX}px;top:520px;opacity:0;display:flex;align-items:center;gap:26px}}
#yrs b{{font-family:{FONT},sans-serif;font-weight:{FW};font-size:180px;line-height:0.82;color:{AC};
  text-shadow:0 6px 40px rgba(0,0,0,0.95)}}
#yrs span{{font-family:{FONT},sans-serif;font-weight:{FW};font-size:44px;line-height:1.04;color:#fff;
  text-transform:uppercase;text-shadow:0 3px 22px rgba(0,0,0,0.95)}}
.firm{{position:absolute;top:830px;opacity:0;padding:16px 26px;border-radius:14px;
  background:rgba(8,14,16,0.86);border:2px solid #ffffff4d;
  font-family:{FONT},sans-serif;font-weight:{FW};font-size:52px;color:#fff;letter-spacing:0.04em;
  box-shadow:0 8px 30px rgba(0,0,0,0.6)}}

.kin2{{position:absolute;left:{LX}px;top:520px;opacity:0;width:860px;white-space:nowrap;
  font-family:{FONT},sans-serif;font-weight:{FW};font-size:82px;line-height:1.04;color:#fff;
  text-transform:uppercase;text-shadow:0 4px 30px rgba(0,0,0,0.95)}}
.kin2 u{{position:absolute;left:0;top:52%;height:9px;width:0;background:{DN};
  border-radius:5px;display:block;box-shadow:0 0 22px {DN}}}
#worksnow{{top:760px;color:{AC}}}

.rhead{{position:absolute;left:0;top:196px;width:{W}px;text-align:center;opacity:0;
  font-family:"Space Mono",monospace;font-weight:700;font-size:36px;letter-spacing:0.24em;
  text-transform:uppercase;color:{AC}}}
.tile{{position:absolute;top:352px;width:262px;height:340px;opacity:0;border-radius:26px;
  border:2px solid #ffffff30;overflow:hidden;
  background:linear-gradient(160deg, rgba(255,255,255,0.11) 0%, rgba(255,255,255,0.04) 46%,
             rgba(8,16,18,0.55) 100%);
  box-shadow:0 18px 50px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.20);
  padding:24px 22px 26px;display:flex;flex-direction:column;justify-content:space-between}}
.tile .fill{{position:absolute;left:0;right:0;bottom:0;height:100%;
  background:linear-gradient(0deg, rgba(70,229,183,0.30) 0%, rgba(70,229,183,0.05) 70%,
             rgba(70,229,183,0) 100%);
  transform:scaleY(0);transform-origin:50% 100%}}
.tile em{{position:relative;font-style:italic;font-family:{FONT},sans-serif;font-weight:{FW};
  font-size:30px;color:#ffffff6b;line-height:1}}
.tile .gl{{position:relative;width:74px;height:74px;overflow:visible;margin:2px auto 0}}
.tile .gl path{{fill:none;stroke:#ffffff70;stroke-width:4;stroke-linecap:round;
  stroke-linejoin:round;stroke-dasharray:260;stroke-dashoffset:260}}
.tile span{{position:relative;font-family:{FONT},sans-serif;font-weight:{FW};font-size:29px;
  color:#ffffffa8;text-transform:uppercase;line-height:1.14;letter-spacing:0.01em}}
.tile u{{position:absolute;left:0;bottom:0;height:5px;width:100%;background:{AC};
  transform:scaleX(0);transform-origin:0 50%;text-decoration:none}}
#swoosh{{position:absolute;left:180px;top:210px;width:1560px;height:620px;opacity:0;
  border-radius:50%;pointer-events:none;
  background:radial-gradient(closest-side at 30% 40%, rgba(120,255,220,0.20), rgba(120,255,220,0) 72%)}}
</style></head>
<body>
<div id="root" data-composition-id="introgfx" data-width="{W}" data-height="{H}"
     data-start="0" data-duration="{DUR:.2f}">
  <div class="clip" data-start="0" data-duration="{DUR:.2f}" data-track-index="0">
    <div id="riskwrap"></div>
    {"".join(el)}
  </div>
</div>
{grab(BUL,"script")}
<script>
window.__timelines = window.__timelines || {{}};
var tl = gsap.timeline({{paused:true}});
{chr(10).join('  '+x for x in tw)}
window.__timelines["introgfx"] = tl;
</script>
</body></html>
"""

if __name__ == "__main__":
    os.makedirs(BUILD, exist_ok=True); os.makedirs(MOVS, exist_ok=True)
    open(os.path.join(BUILD,"index.html"),"w").write(build())
    dst = os.path.join(MOVS,"intro-gfx.mov")
    env = dict(os.environ, PRODUCER_BROWSER_GPU_MODE="hardware")
    subprocess.run(["hyperframes","render",BUILD,"-o",dst,"--format","mov",
                    "--fps",str(FPS),"--quiet"], env=env, check=True,
                   capture_output=True, text=True)
    print("->", dst)
