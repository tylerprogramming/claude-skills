#!/usr/bin/env python3
"""Long-form recut for "045 - arcade.dev": silence + retake cuts, SCREEN/CAMERA composite.

Same shape as the "17 claude code skills" recut — SCREEN full-frame, CAMERA circle-masked
bottom-right, rendered in batches and joined with the concat demuxer so the film is
encoded exactly once. See scripts/recut_longform.py in that project for why the two
single-pass ffmpeg approaches fail at this length.

What is DIFFERENT about this footage, and why the inherited constants would be wrong:

  * The noise floor here sits near -72 dB — essentially digital silence — not the -26 dB
    of the previous shoot. `--noise=0.05` (amplitude 0.05 == -26 dB) therefore sits INSIDE
    Tyler's speech and ate 75s of speech tails. NOISE is 0.005 (-46 dB), comfortably
    between this floor and the ~-20 dB speech.

  * ~62% of the film is genuine silence: it is a live agent demo and most of the runtime
    is spent waiting on the agent. That is real, not a threshold artifact — every
    threshold from 0.005 to 0.05 lands within 3% of the same cut.

  * The Whisper transcript HALLUCINATES fluent sentences over the long silent stretches
    (measured at -70 dB, i.e. nothing there). Anything derived from the transcript must
    first be intersected with the keep ranges — see transcript/speech.json.

  * No dead air survives the silence pass here (unlike the previous film). What does
    survive is isolated sub-second *slivers* — clicks and rustles during long waits —
    dropped by the isolation rule in build_keeps() rather than a hand-written list.

Importing this module gives you `keeps` (the final cut plan) without rendering.

Usage:
  recut_arcade.py                 # whole film
  recut_arcade.py --minutes 2     # first 2 minutes of the cut, for review
  recut_arcade.py --test 12       # first 12 clips
  recut_arcade.py --keep-take2    # leave the superseded partnership take 2 in
"""
import json, subprocess, os, sys
from concurrent.futures import ThreadPoolExecutor

CAM_DIR = os.path.expanduser("~/Movies/Camtasia")
BASE    = os.path.join(CAM_DIR, "045 - arcade.dev")
SCREEN  = os.path.join(CAM_DIR, "045 - arcade.dev - SCREEN.mp4")
CAMERA  = os.path.join(CAM_DIR, "045 - arcade.dev - CAMERA.mp4")
OUT     = os.path.join(BASE, "recut")
WORK    = os.path.join(OUT, "batches")
MOVS    = os.path.join(BASE, "overlays", "movs")

NOISE     = "0.005"      # see module docstring — 0.05 is wrong for this mic
MIN_KEEP  = 0.10         # drop slivers; the padding leaves them
SLIVER    = 0.60         # a keep shorter than this, marooned in silence, is not speech
ISOLATED  = 3.00         # ...where "marooned" means this much silence on one side

CIRCLE_D  = 480          # final diameter of the webcam circle
CIRC_BUILD = 900         # built at this size so it can scale DOWN, never up
MARGIN    = 50           # inset from the bottom-right corner
RING_W    = 4            # white border, at final size
CROP      = (900, 900, 450, 100)   # w,h,x,y — head+shoulders out of the 1920x1080 cam
BATCH     = 30           # clips per ffmpeg pass
SP_BATCH  = 8            # ...and per cold-open/insert pass, which is per-clip work
WORKERS   = 3            # concurrent ffmpeg passes
ZOOM_SS   = 2            # zoompan supersample factor; see zoom_chain()
FPS       = 30

# ------------------------------------------------------------------ shot list --
# Cold open cut shot-for-shot against what Tyler says, alternating him full-frame with
# the screen full-bleed. He tabbed the screen recording in sync with his own narration
# while shooting, so the destinations already land where the words do:
#   src  4.27  "it just summarized an email of a partnership"  -> Claude Code
#   src  8.70  "...moved into its own folder in drive"         -> Drive /blotato
#   src 11.33  "then a slack message about it"                 -> Slack #ai
# (the 10.97-11.46 silence cut happens to swallow the Drive->Slack tab animation).
# The screen runs until it tabs OFF Slack at src 14.03 and hands straight back to camera
# — Tyler did not want the terminal in this stretch.
#
# zoom is a keyframe list [(t, z), ...] in seconds from the START OF THE SHOT (output
# time, so a silence cut inside a shot does not desync it). overlay is a MOV in MOVS/.
# blur=(sigma, start, dur) is a defocus that resolves to sharp at start+dur.
# fadein=dur opens the shot from black.
SHOTS = [
    # Black, then he appears SMALL and centred in it and the frame rushes in to fill —
    # 0.32 to full in 0.45s, ease-out so it decelerates on arrival. Defocus clears by
    # 0.47s. Then a step back out at 0:03.
    #
    # 1.10 is the zoom ceiling, not a taste call — he holds the 7 Minute Apps bottle up
    # from ~0:01 to ~0:03 and its right edge reaches x~1860 of 1920. A centred crop keeps
    # that visible only while zoom <= 1.13, so anything punchier starts eating the bottle.
    # ease is SMOOTHSTEP here, not ease-out: ease-out leaves its start value on the very
    # first frame, so the tiny opening scale lasted a single frame and never read. With
    # smoothstep it holds small, accelerates, then decelerates into the overshoot.
    dict(a=0.00,  b=4.27,  mode="cam", ease="smooth",
         blur=(34.0, 0.02, 0.45), fadein=0.18,
         # Starts smaller (0.24) and OVERSHOOTS to 1.16 before settling back to 1.10 —
         # the overshoot is what makes it land like a punch rather than a glide. It peaks
         # at 0.42s and is gone by 0.62s, before he raises the bottle at ~0.9s, so it
         # never breaches the 1.13 ceiling while the bottle is in frame.
         zoom=[(0.00, 0.10), (0.40, 1.22), (0.64, 1.10),
               (3.00, 1.10), (3.30, 1.04)],
         # The 7 Minute Apps logo pops in at 2.0s and leaves at 4.0s. It sits left of
         # centre because he is holding the bottle up on the right through that beat.
         overlay="logo.mov", ov_xy=(70, 300)),
    # Screen ends the moment it leaves Slack — src 14.03 is where it tabs BACK to the
    # terminal, and Tyler does not want the terminal here.
    dict(a=4.27,  b=14.03, mode="screen"),
    # Him, holding then stepping out and back in, captioned with what he ACTUALLY says
    # (scripts/build_words.py) rather than the summarised stat rows that used to sit here.
    # Full-frame camera, so there is no webcam circle to dodge and the block can sit low
    # and wide like an ordinary subtitle. scripts/build_stats.py still builds the stat
    # version of this overlay if it is ever wanted back.
    dict(a=14.03, b=21.79, mode="cam",
         zoom=[(0.00, 1.10), (1.20, 1.10), (1.50, 1.00), (5.00, 1.00), (5.30, 1.10)],
         overlay="words.mov", ov_xy=(60, 400)),
    # "So let me show you how to do it." — him, then a HARD CUT to the body. No dissolve
    # and no circle animating in; the composite simply starts on the next clip.
    # ...zooming back out on the word "let" itself, which lands at src 35.84.
    dict(a=35.60, b=37.69, mode="cam",
         zoom=[(0.00, 1.10), (0.24, 1.10), (0.56, 1.00)]),
    # "And you get to customize that how many tools for as many MCP servers as you need."
    # straight through "let's go ahead and get started creating our first MCP server..."
    # — one continuous camera run rather than two shots with a composite sliver between
    # them. b runs to the end of the keep (97.27, the trailing "Okay,") rather than
    # stopping on the sentence at 97.00, which left a 0.27s frame-flash.
    dict(a=80.32, b=97.30, mode="cam",
         zoom=[(0.00, 1.06), (2.00, 1.06), (2.30, 1.00), (7.50, 1.00), (7.80, 1.08)]),
    # "And yes, you can..." through "...then arcade.dev will handle that for you." — on
    # camera the whole way, stepping between 1.00 and ~1.08 every couple of seconds with
    # sharp 0.25s moves. The always-on infographic plays over the middle of this shot, so
    # what gets defocused under it here is HIM rather than the screen.
    dict(a=43.99, b=61.99, mode="cam",
         zoom=[(0.00, 1.08), (2.50, 1.08), (2.75, 1.00),
               (5.20, 1.00), (5.45, 1.09),
               (7.90, 1.09), (8.15, 1.00),
               (10.60, 1.00), (10.85, 1.08),
               (13.30, 1.08), (13.55, 1.00),
               (16.00, 1.00), (16.25, 1.07)]),
    # "Now with that said, let's create something a little bit more complex... a smarter
    # MCP server." Him only, holding then stepping out and back in.
    dict(a=579.27, b=593.27, mode="cam",
         zoom=[(0.00, 1.10), (1.50, 1.10), (1.80, 1.00), (9.00, 1.00), (9.30, 1.10)]),
    # "...I want you to watch in the meantime. Thank you, and I will see you in the next
    # video." Sign-off on camera only, holding then stepping in for the last line.
    dict(a=2273.39, b=2279.00, mode="cam",
         zoom=[(0.00, 1.02), (1.60, 1.02), (1.90, 1.09)]),
]

# Stretches where the SCREEN is scaled up a little, in SOURCE seconds.
#
# Scaling up by k shows 1080/k of the original, so it hides (1080 - 1080/k)/2 off the top
# — NOT (1080k - 1080)/2. Getting that backwards is what left a sliver of the Skool search
# field on screen at k=1.28. Reference points on this capture: Chrome's tab strip and
# address bar end at y~79, and Skool's own header with the Search field ends at y~141.
# Both windows also trim the same amount per side, which clips the Arcade wordmark and the
# edge of the BOOK A DEMO button; Tyler is fine with that to be rid of the URL bar.
#
# The fourth field is a ramp: the scale eases in over that many seconds instead of
# snapping on. Snapping read as a jolt. `crop` cannot animate, so this scales up with
# eval=frame and crops back to 1920x1080 — crop's w/h are init-only but its x/y are
# per-frame, which is all that is needed once the output size is fixed.
SCREEN_ZOOM = [
    # Runs to 80.32 (the camera shot) rather than 74.90: ending it earlier popped the
    # screen back out for the ~0.8s before the tools clip, which read as a glitch.
    (44.99, 80.32, 1.22, 0.90),  # arcade.dev homepage: hides 97px, clears the URL bar
    # The Skool classroom needs far more, because this page stacks TWO bars: the browser's
    # and Skool's own. 1.38 hides 149px, clearing the search field at y~141 and keeping the
    # nav row and the course cards.
    (2250.49, 2273.39, 1.38, 0.90),
]

# Windows where the finished frame is defocused, in RECUT seconds, so an overlay can read
# on top of it. Done as a blurred copy crossfaded over the sharp one rather than a
# timeline-gated gblur, so the defocus ramps instead of popping.
BLUR_WINDOWS = [
    (37.85, 45.89, 26.0),      # under the always-on infographic
]

# Full-frame animation beats, in RECUT seconds, laid over the finished composite.
# `at` is where the MOV starts in the cut, `dur` its length, `xy` its top-left.
ANIMS = [
    # Camera flash over the cut out of the cold open. The component's hit lands at 58% of
    # its duration; measured on the rendered MOV the alpha actually crests at 0.59s, so
    # placing it at 22.80 lands the peak on the cut at 23.39.
    dict(at=22.80, dur=0.90, mov="flash.mov", xy=(0, 0)),
    # "thousands of prebuilt tools across all the apps you already use" — a wall of real
    # brand marks. The ONLY graphic in the film carrying a dark wash: it plays over the
    # arcade.dev homepage, a bright magenta gradient white type will not hold against.
    # The wash is masked with a hole at the webcam circle so he stays on screen.
    # Ends at 59.65, just before the camera shot at 59.70 — animations only composite
    # onto comp batches, so anything past that boundary would be dropped.
    # scripts/build_tools.py.
    # "multiple users ... agents running 24/7 without worrying about reauthenticating or
    # any of those token issues" — the film's actual argument. Seedance bed (a light
    # ribbon streaming through gates that keep opening) under three text beats on his
    # words. scripts/build_alwayson.py.
    dict(at=37.85, dur=8.04, mov="alwayson.mov", xy=(0, 0)),
    # ...and the same long flash over the cut BACK to the screen and his circle at 46.00,
    # once the infographic is done. Crest is 0.733s in, so 45.27 puts the peak on the cut.
    dict(at=45.20, dur=1.20, mov="flash-long.mov", xy=(0, 0)),
    dict(at=56.00, dur=3.70, mov="tools.mov", xy=(0, 0)),
    # ...and flash over the cut from it into the camera shot at 59.70. A LONGER flash
    # than the cold open's, because the clip no longer dissolves under it: measured on
    # the rendered MOV the 1.20s variant crests at 0.733s, so 58.967 puts the peak on
    # the cut.
    dict(at=58.97, dur=1.20, mov="flash-long.mov", xy=(0, 0)),
    # The demo prompt read out as a chain, over the empty black of the Claude Code
    # terminal — no scrim needed there. scripts/build_pipeline.py.
    dict(at=426.4, dur=9.6, mov="pipeline.mov", xy=(120, 400)),
]

# Retaken segments, in SOURCE seconds — take 1 of each, cut so the LAST take survives.
# `hyperframes duplicates` returns 27 groups on this footage and essentially all of them
# are adjacent fragments of one sentence sharing vocabulary, not retakes; it independently
# corroborated only #4 and #5 below. These came from reading transcript/speech.txt for
# repeated beat structure. Boundaries are word-level exact.
DUPS = [
    (237.70, 240.10),   # "here you will be look. Okay." -> keeps "So here you'll be
                        #   looking at the playground"
    (278.10, 280.50),   # "So I'm going to look up Gmail. I use Gmail." -> keeps the
                        #   second "So I'm going to look up Gmail. I'm going to then
                        #   choose the tools."
    (318.45, 384.45),   # who-can-connect, FOUR passes collapsed into one splice:
                        #   318.5-320.0    "So now you can choose who you want to connect."
                        #                  — only the FULL-FILE Whisper pass missed this;
                        #                  re-transcribing the rendered audio caught it.
                        #   320.16-332.80  narrating members/external users while clicking
                        #   341.93         an orphaned "And" (rest of the line is silence)
                        #   357.36-377.80  the take ending "...you know, let me start that
                        #                  over" at 376.75
                        #   Keeps "connect." at 318.38 (he says it as he clicks the button)
                        #   and resumes on "Then we get to choose who we want to actually
                        #   connect to this project or this MCP server."
    (862.40, 911.90),   # partnership-demo prompt take 1, incl. him noticing "I didn't
                        #   actually specify Gmail" and the "start that over" tail whose
                        #   only surviving word is "over." at 908.49 -> keeps take 2.
    (427.10, 429.45),   # "or just have the basic MCP URL," said twice, ~4s apart ->
                        #   keeps "or you can have the basic MCP URL that you can give
                        #   and attach to any agent anywhere." The long-file transcript
                        #   dropped the second instance entirely; transcribing src
                        #   424-442 in isolation shows both.
    (454.34, 468.70),   # "Okay. Now I have," (false start) then "So now I have a fresh
                        #   terminal." — a third pass at a line he already landed at
                        #   449-451 -> keeps "...after we're done now with a fresh
                        #   terminal. I can just copy, simply copy and paste"
    (569.74, 570.27),   # "out of, out of" -> keeps the second
    (2202.15, 2204.28), # "This is amazing. I will," then "this is absolutely amazing."
                        #   -> keeps the second. Tyler marked this at recut 11:36-11:38;
                        #   it is really at 11:33.3. The long-file transcript drops
                        #   "will, this is" entirely — transcribing src 2198-2212 in
                        #   isolation is what showed the actual boundaries.
]

# Take 2 of the partnership demo (912.15-973.04) is ITSELF superseded: at 1395.84 he says
# "we're starting over where we started this demo" and restates the whole prompt a third
# time, now as five steps, explaining that Drive alone cannot create a document so he
# added Google Docs. Take 3 also repeats take 2's "every seven days you have to
# re-authenticate" passage almost verbatim. Cut per Tyler; --keep-take2 puts it back.
TAKE2 = (911.90, 1395.60)

# Tyler's cut: "remove from 00:23 until you get to 'let me show you how'". Taken to the
# clean sentence boundary just before — "And yes," starts at 21.79 — so the cold open
# runs "...And I did it in just a few minutes." straight into "So let me show you how to
# do it." Drops the care-package aside and the "seven at seven minute apps" mention.
CARE_PACKAGE = (21.79, 35.60)

# Non-speech that the silence pass kept because it is loud enough to trip the threshold.
# Tyler reported "a cough at 1:26-1:30"; the cough is really at recut 1:29.8 and the
# window he named is intact speech ("of course, this is your first time, go ahead and
# create an account to sign in"). Verified by RMS — all three are noise, not words:
NOISE_CUTS = [
    (114.45, 115.35),   # the cough: -74dB floor, then a 0.25s burst to -17dB, fast decay
    (165.30, 166.55),   # ~1s of chair/clothing rustle sitting at -36..-52dB
    (235.15, 235.45),   # a 0.12s click at -49dB out of a -75dB floor
]


def _prune_slivers(ks):
    """Drop short keeps marooned in silence — clicks, not words.

    Run again after the cut lists are applied: removing a take can strand the tail of a
    neighbouring keep as a fragment that was not isolated before.
    """
    out = []
    for i, (a, b) in enumerate(ks):
        if b - a < SLIVER:
            before = a - ks[i - 1][1] if i > 0 else 1e9
            after = ks[i + 1][0] - b if i + 1 < len(ks) else 1e9
            if min(before, after) >= ISOLATED:
                continue
        out.append((a, b))
    return out


def build_keeps(cut_take2=True):
    plan = json.loads(subprocess.run(
        ["hyperframes", "silence", CAMERA, f"--noise={NOISE}", "--dry-run", "--json"],
        capture_output=True, text=True).stdout)
    ks = [(r["start"], r["end"]) for r in plan["keepRanges"]
          if r["end"] - r["start"] >= MIN_KEEP]
    ks = _prune_slivers(ks)

    cuts = DUPS + NOISE_CUTS + [CARE_PACKAGE] + ([TAKE2] if cut_take2 else [])
    for a, b in sorted(cuts):
        nxt = []
        for s, e in ks:
            if e <= a or s >= b:
                nxt.append((s, e)); continue
            if s < a: nxt.append((s, a))
            if e > b: nxt.append((b, e))
        ks = [(s, e) for s, e in nxt if e - s >= MIN_KEEP]
    return _prune_slivers(ks)


def tag_shots(ks):
    """Split keeps at shot boundaries and tag each clip with its shot.

    `off` is how far into the shot this clip starts measured in OUTPUT time, so zoom and
    overlay timings stay correct even if a silence cut splits the shot.
    """
    bounds = sorted({t for s in SHOTS for t in (s["a"], s["b"])}
                    | {t for z in SCREEN_ZOOM for t in z[:2]})
    out, used, szused = [], {}, {}
    for s, e in ks:
        marks = [s] + [b for b in bounds if s < b < e] + [e]
        for a, z in zip(marks, marks[1:]):
            shot = next((sh for sh in SHOTS if sh["a"] <= a < sh["b"]), None)
            zw = next((z for z in SCREEN_ZOOM if z[0] <= a < z[1]), None)
            sz = None
            if zw:
                sz = (zw[2], zw[3], szused.get(zw[0], 0.0))
                szused[zw[0]] = szused.get(zw[0], 0.0) + (z - a)
            if shot is None:
                out.append(dict(a=a, b=z, mode="comp", off=0.0, szoom=sz))
            else:
                k = shot["a"]
                out.append(dict(a=a, b=z, off=used.get(k, 0.0), szoom=sz, **
                                {kk: vv for kk, vv in shot.items() if kk not in ("a", "b")}))
                used[k] = used.get(k, 0.0) + (z - a)
    return out


keeps = build_keeps("--keep-take2" not in sys.argv)
shots = tag_shots(keeps)


def zoom_chain(zoom, off, ease="smooth"):
    """Push/pull on the camera, from a [(t, z), ...] keyframe list.

    A CONSTANT zoom is a plain fixed crop+scale — exact, and no per-frame machinery.
    An ANIMATED one needs zoompan: `crop` cannot do it, because its w/h are evaluated
    once at init and it rejects `eval` outright ("Option not found"). zoompan counts in
    output frames rather than seconds, hence on/FPS, shifted by `off` so a shot split by
    a silence cut still eases on shot time.

    Multiple keyframes are summed as SATURATING ramps: each segment's term is 0 before
    its start and its full delta after its end, so adding them reproduces the piecewise
    curve without any nested if() in the expression.

    The input is SUPERSAMPLED first because zoompan rounds its source window to whole
    pixels every frame. On a slow move the window size holds for several frames then
    snaps, which reads as a shake — Tyler flagged it. Measured over this shot: frame-to-
    frame oscillation 0.479 at 1x versus a 0.247 floor from his own movement; at 2x it is
    0.273, i.e. gone. 3x measured 0.263, not worth 2.25x the pixels.
    """
    if not zoom:
        return None
    if len(zoom) == 1 or all(abs(z - zoom[0][1]) < 1e-6 for _, z in zoom):
        z0 = zoom[0][1]
        if abs(z0 - 1.0) < 1e-6:
            return None
        w, h = 2 * int(1920 / z0 / 2), 2 * int(1080 / z0 / 2)
        return f"crop={w}:{h}:{(1920 - w) // 2}:{(1080 - h) // 2},scale=1920:1080"

    # A z below 1.0 means "smaller than the frame". zoompan cannot do it — it clamps z to
    # >= 1 — and padding the source out to make room explodes: at z=0.10 the canvas would
    # be 19200x10800, over 200 megapixels a frame.
    #
    # So when the move dips below 1.0, scale the camera per frame and lay it on a black
    # bed instead. `scale` with eval=frame resizes freely, and `overlay` CLIPS whatever
    # overflows the bed, so one mechanism covers the whole range — a tiny picture centred
    # in black at the start, full frame in the middle, and past 1.0 at the end — at no
    # more cost than the frame itself. That is what lets the open start as small as Tyler
    # wants. The bed is made from the clip's own stream so it matches length exactly.
    zmin = min(z for _, z in zoom)
    if zmin < 1.0:
        terms = [f"{zoom[0][1]:.4f}"]
        for (t0, z0), (t1, z1) in zip(zoom, zoom[1:]):
            if abs(z1 - z0) < 1e-6 or t1 <= t0:
                continue
            p = f"clip((t+{off:.3f}-{t0:.3f})/{t1 - t0:.3f}\\,0\\,1)"
            e = f"(1-pow(1-{p}\\,3))" if ease == "out" else f"({p}*{p}*(3-2*{p}))"
            terms.append(f"({z1 - z0:.4f})*{e}")
        Z = "(" + "+".join(terms) + ")"
        return ("SPLITBED",
                f"scale=w='2*floor(1920*{Z}/2)':h='2*floor(1080*{Z}/2)':eval=frame",
                "overlay=x='(W-w)/2':y='(H-h)/2':eval=frame")

    pre, mul = f"scale={1920 * ZOOM_SS}:{1080 * ZOOM_SS}:flags=bicubic", 1.0

    terms = [f"{zoom[0][1] * mul:.4f}"]
    for (t0, z0), (t1, z1) in zip(zoom, zoom[1:]):
        if abs(z1 - z0) < 1e-6 or t1 <= t0:
            continue
        p = f"clip((on/{FPS}+{off:.3f}-{t0:.3f})/{t1 - t0:.3f}\\,0\\,1)"
        e = f"(1-pow(1-{p}\\,3))" if ease == "out" else f"({p}*{p}*(3-2*{p}))"
        terms.append(f"({(z1 - z0) * mul:.4f})*{e}")
    Z = "(" + "+".join(terms) + ")"
    return (f"{pre},"
            f"zoompan=z='{Z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d=1:s=1920x1080:fps={FPS},setpts=PTS-STARTPTS")


def blur_pull(blur, i):
    """Defocus that resolves to sharp — as a crossfade between a blurred and a sharp copy.

    NOT via sendcmd. gblur's sigma advertises runtime support (the 'T' flag) but driving
    it that way does not actually land: measured against the source on this shot, constant
    sigma=30 gives a sharpness ratio of 0.43 and sigma=0 gives 0.95, yet a sendcmd ramp —
    inline `c=` or `f=` file, 31 steps or 9, even a single "set sigma 0" command — plateaus
    at 0.58 and never reaches sharp. That residual is exactly what Tyler saw still blurred
    two seconds in.

    So: split the frame, blur one copy hard, and fade the sharp copy in on top of it with
    `fade`'s alpha, which is well-understood and verifiable. Both layers are the same
    image, so the blend reads as a focus pull rather than a dissolve between two shots.

    blur = (sigma, start, dur); sharp is fully resolved at start+dur.
    """
    sigma, at, dur = blur
    return ([f"split=2[bl{i}][sh{i}]",
             f"[bl{i}]gblur=sigma={sigma:.2f}[blb{i}]",
             f"[sh{i}]format=rgba,fade=t=in:st={at:.3f}:d={dur:.3f}:alpha=1[shf{i}]",
             f"[blb{i}][shf{i}]overlay=x=0:y=0"], f"[bo{i}]")


def main():
    from PIL import Image, ImageDraw

    test_n = int(sys.argv[sys.argv.index("--test") + 1]) if "--test" in sys.argv else None
    minutes = float(sys.argv[sys.argv.index("--minutes") + 1]) if "--minutes" in sys.argv else None

    suffix = "-TEST" if test_n else (f"-first{minutes:g}min" if minutes else "")
    if "--keep-take2" in sys.argv:
        suffix += "-take2"
    dst = os.path.join(OUT, f"045-arcade-dev-recut{suffix}.mp4")
    os.makedirs(WORK, exist_ok=True)

    ss = CIRC_BUILD * 4
    m = Image.new("L", (ss, ss), 0)
    ImageDraw.Draw(m).ellipse((0, 0, ss - 1, ss - 1), fill=255)
    mask_png = os.path.join(OUT, "circle_mask.png")
    m.resize((CIRC_BUILD, CIRC_BUILD), Image.LANCZOS).save(mask_png)

    # PIL strokes INWARD from the bounding box, so the box has to be the full square —
    # insetting it leaves a sliver of video outside the white, which reads as a halo.
    bw = RING_W * CIRC_BUILD / CIRCLE_D
    r = Image.new("RGBA", (ss, ss), (0, 0, 0, 0))
    ImageDraw.Draw(r).ellipse((0, 0, ss - 1, ss - 1),
                              outline=(255, 255, 255, 255), width=int(round(bw * 4)))
    ring_png = os.path.join(OUT, "circle_ring.png")
    r.resize((CIRC_BUILD, CIRC_BUILD), Image.LANCZOS).save(ring_png)

    clips_all = shots
    if test_n:
        clips_all = clips_all[:test_n]
    elif minutes:
        acc, cut = 0.0, []
        for c in clips_all:
            cut.append(c); acc += c["b"] - c["a"]
            if acc >= minutes * 60:
                break
        clips_all = cut

    # Batch so that plain-composite runs stay on the cheap path (concat once, composite
    # once for the whole batch) and the shot-cut runs, which are per-clip work, sit in
    # their own small passes.
    batches, cur = [], []
    for c in clips_all:
        special = c["mode"] != "comp"
        cap = SP_BATCH if special else BATCH
        if cur and ((cur[0]["mode"] != "comp") != special or len(cur) >= cap):
            batches.append(cur); cur = []
        cur.append(c)
    if cur:
        batches.append(cur)

    # Each batch's start in OUTPUT time, so a full-frame animation placed at a recut
    # timestamp can be trimmed to whatever slice of it falls inside a given batch.
    offsets, acc = [], 0.0
    for b in batches:
        offsets.append(acc)
        acc += sum(c["b"] - c["a"] for c in b)

    total = sum(c["b"] - c["a"] for c in clips_all)
    n_sp = sum(1 for c in clips_all if c["mode"] != "comp")
    anims = [a for a in ANIMS if os.path.exists(os.path.join(MOVS, a["mov"]))]
    print(f"{len(clips_all)} clips, {total:.1f}s = {int(total//60)}:{total%60:04.1f}, "
          f"{len(batches)} batches ({n_sp} shot-cut), {len(anims)} animations", flush=True)

    cw, ch, cx, cy = CROP

    def render(idx_clips):
        idx, clips = idx_clips
        out = os.path.join(WORK, f"batch{idx:03d}.mov")
        base = clips[0]["a"]                    # input-seek here; trim times go relative
        span = clips[-1]["b"] - base + 1.0
        special = clips[0]["mode"] != "comp"
        n = len(clips)
        extra = []
        b0 = offsets[idx]
        b1 = b0 + sum(c["b"] - c["a"] for c in clips)

        if not special:
            parts, scr_lbl, cam_lbl = [], [], []
            for i, c in enumerate(clips):
                s, e = c["a"] - base, c["b"] - base
                sz = c.get("szoom")
                if not sz:
                    parts.append(f"[0:v]trim=start={s}:end={e},setpts=PTS-STARTPTS[s{i}]")
                else:
                    # Animated screen push-in. NOT scale+crop: `crop` freezes iw/ih at
                    # init, so once scale starts growing the frame its (iw-ow)/2 stays 0
                    # and it crops from the top-left — the browser chrome never leaves.
                    # Overlay onto a black bed instead; overlay re-reads w/h every frame
                    # and clips the overflow, which is exactly the crop that was wanted.
                    k, ramp, zoff = sz
                    pr = f"clip((t+{zoff:.3f})/{ramp:.3f}\\,0\\,1)"
                    Z = f"(1+{k - 1:.4f}*({pr}*{pr}*(3-2*{pr})))"
                    parts.append(f"[0:v]trim=start={s}:end={e},setpts=PTS-STARTPTS,"
                                 f"split=2[sa{i}][sb{i}]")
                    parts.append(f"[sb{i}]drawbox=x=0:y=0:w=iw:h=ih:color=black@1:t=fill"
                                 f"[sbed{i}]")
                    parts.append(f"[sa{i}]scale=w='2*floor(1920*{Z}/2)'"
                                 f":h='2*floor(1080*{Z}/2)':eval=frame[ssc{i}]")
                    parts.append(f"[sbed{i}][ssc{i}]"
                                 f"overlay=x='(W-w)/2':y='(H-h)/2':eval=frame[s{i}]")
                parts.append(f"[1:v]trim=start={s}:end={e},setpts=PTS-STARTPTS[c{i}]")
                parts.append(f"[1:a]atrim=start={s}:end={e},asetpts=PTS-STARTPTS[a{i}]")
                scr_lbl.append(f"[s{i}]")
                cam_lbl.append(f"[c{i}][a{i}]")
            fg = (";".join(parts) + ";"
                  + "".join(scr_lbl) + f"concat=n={n}:v=1:a=0[scr];"
                  + "".join(cam_lbl) + f"concat=n={n}:v=1:a=1[cam][ac];"
                  + f"[cam]crop={cw}:{ch}:{cx}:{cy},"
                  + f"scale={CIRC_BUILD}:{CIRC_BUILD},format=rgba[camS];"
                  + "[2:v]format=gray[mask];"
                  + "[camS][mask]alphamerge[circB];"
                  + "[circB][3:v]overlay=x=0:y=0[circR];"
                  + f"[circR]scale={CIRCLE_D}:{CIRCLE_D}[circF];"
                  + f"[scr][circF]overlay=x=W-w-{MARGIN}:y=H-h-{MARGIN}[v0]")

            vbase = "[v0]"
        else:
            # Trims are emitted per mode — filter_complex rejects any labelled output
            # that nothing consumes, so a cam-only clip must not also trim the screen.
            ovs = {}
            for c in clips:
                if c.get("overlay") and c["overlay"] not in ovs:
                    ovs[c["overlay"]] = 4 + len(ovs)
            extra = [x for name in ovs for x in ("-i", os.path.join(MOVS, name))]

            seg, av = [], []
            for i, c in enumerate(clips):
                s, e, mode = c["a"] - base, c["b"] - base, c["mode"]
                if mode == "screen":
                    seg.append(f"[0:v]trim=start={s}:end={e},setpts=PTS-STARTPTS[s{i}]")
                if mode == "cam":
                    seg.append(f"[1:v]trim=start={s}:end={e},setpts=PTS-STARTPTS[c{i}]")
                seg.append(f"[1:a]atrim=start={s}:end={e},asetpts=PTS-STARTPTS[a{i}]")

                zc = zoom_chain(c.get("zoom"), c.get("off", 0.0), c.get("ease", "smooth"))
                if mode == "screen":
                    seg.append(f"[s{i}]format=yuv420p[v{i}]")
                elif mode == "cam":
                    cur = f"[c{i}]"
                    if isinstance(zc, tuple):
                        # per-frame scale onto a black bed; the bed is drawn from the
                        # clip's own stream so it is exactly as long as the clip
                        _, sc, ov = zc
                        seg.append(f"{cur}split=2[za{i}][zb{i}]")
                        seg.append(f"[zb{i}]drawbox=x=0:y=0:w=iw:h=ih"
                                   f":color=black@1:t=fill[zbed{i}]")
                        seg.append(f"[za{i}]{sc}[zsc{i}]")
                        seg.append(f"[zbed{i}][zsc{i}]{ov}[cz{i}]")
                        cur = f"[cz{i}]"
                    elif zc:
                        seg.append(f"{cur}{zc}[cz{i}]"); cur = f"[cz{i}]"
                    if c.get("blur") and c.get("off", 0.0) < 0.01:
                        parts_b, out_b = blur_pull(c["blur"], i)
                        seg.append(f"{cur}{parts_b[0]}")
                        seg += parts_b[1:-1]
                        seg.append(f"{parts_b[-1]}{out_b}")
                        cur = out_b
                    if c.get("fadein") and c.get("off", 0.0) < 0.01:
                        # Opens on near-black and lifts into the shot.
                        seg.append(f"{cur}fade=t=in:st=0:d={c['fadein']:.3f}[fi{i}]")
                        cur = f"[fi{i}]"
                    if c.get("overlay"):
                        k, off = ovs[c["overlay"]], c.get("off", 0.0)
                        ox, oy = c.get("ov_xy", (130, 380))
                        seg.append(f"[{k}:v]trim=start={off:.3f},setpts=PTS-STARTPTS[ov{i}]")
                        seg.append(f"{cur}[ov{i}]overlay=x={ox}:y={oy}"
                                   f":eof_action=pass[vo{i}]")
                        cur = f"[vo{i}]"
                    seg.append(f"{cur}format=yuv420p[v{i}]")
                av.append(f"[v{i}][a{i}]")
            fg = ";".join(seg) + ";" + "".join(av) + f"concat=n={n}:v=1:a=1[v0][ac]"
            vbase = "[v0]"

        # Full-frame animation beats, laid ON TOP of the finished frame (so they sit over
        # the webcam circle too) at their recut timestamps, on BOTH paths — a transition
        # that straddles a cut needs to reach into the camera batch as well. Each is
        # trimmed to the slice falling inside this batch, exactly like the title cards on
        # the previous film; the film is still encoded only once.
        # Defocus windows: blur a copy of the finished frame and crossfade it over the
        # sharp one, so the blur ramps in and out rather than snapping. Times are
        # batch-local; a window that starts before this batch simply enters at 0.
        cur = vbase
        for j, (bs, be, sig) in enumerate(BLUR_WINDOWS):
            if be <= b0 or bs >= b1:
                continue
            a0, a1 = max(bs - b0, 0.0), min(be, b1) - b0
            fi = 0.30 if bs >= b0 else 0.0
            fo = 0.30 if be <= b1 else 0.0
            fg += (f";{cur}split=2[nb{j}][bb{j}]"
                   f";[bb{j}]gblur=sigma={sig:.1f},format=rgba"
                   + (f",fade=t=in:st={a0:.3f}:d={fi:.2f}:alpha=1" if fi else "")
                   + (f",fade=t=out:st={a1 - fo:.3f}:d={fo:.2f}:alpha=1" if fo else "")
                   + f"[bf{j}]"
                   f";[nb{j}][bf{j}]overlay=x=0:y=0"
                   f":enable='between(t,{a0:.3f},{a1:.3f})'[vb{j}]")
            cur = f"[vb{j}]"

        hits = [a for a in anims if a["at"] + a["dur"] > b0 and a["at"] < b1]
        for j, a in enumerate(hits):
            k = 4 + len(ovs if special else {}) + j    # 0-3 are screen/cam/mask/ring
            local = max(0.0, b0 - a["at"])             # where in the anim we enter
            at = max(a["at"] - b0, 0.0)                # where in this batch it starts
            end = min(a["at"] + a["dur"], b1) - b0
            ax, ay = a.get("xy", (0, 0))
            fg += (f";[{k}:v]trim=start={local:.4f},setpts=PTS-STARTPTS+{at:.4f}/TB[an{j}]"
                   f";{cur}[an{j}]overlay=x={ax}:y={ay}"
                   f":enable='between(t,{at:.4f},{end:.4f})':eof_action=pass[va{j}]")
            extra += ["-i", os.path.join(MOVS, a["mov"])]
            cur = f"[va{j}]"
        fg += f";{cur}null[vout]"

        fg_path = os.path.join(WORK, f"fg{idx:03d}.txt")
        with open(fg_path, "w") as f:
            f.write(fg)

        subprocess.run([
            "ffmpeg", "-v", "error", "-nostdin",
            "-ss", f"{base:.3f}", "-t", f"{span:.3f}", "-i", SCREEN,
            "-ss", f"{base:.3f}", "-t", f"{span:.3f}", "-i", CAMERA,
            "-i", mask_png, "-i", ring_png, *extra,
            "-filter_complex_script", fg_path,
            "-map", "[vout]", "-map", "[ac]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "pcm_s16le", "-y", out], check=True)
        print(f"  batch {idx+1}/{len(batches)} done", flush=True)
        return out

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        outs = list(ex.map(render, enumerate(batches)))

    lst = os.path.join(WORK, "concat.txt")
    with open(lst, "w") as f:
        for o in outs:
            f.write(f"file '{o}'\n")

    subprocess.run([
        "ffmpeg", "-v", "error", "-stats", "-f", "concat", "-safe", "0", "-i", lst,
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", "-y", dst], check=True)
    print("->", dst)


if __name__ == "__main__":
    main()
