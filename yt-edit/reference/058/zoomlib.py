#!/usr/bin/env python3
"""Shared zoompan helper: hold, then a quick smooth move, then hold.

Every cutaway in this film used a single linear ramp across its whole length. That is a
drift, not a move: the github clip ran 5.4s of continuous creep and the cold open zoomed
in on one shot and back OUT on the next. Both read as sluggish and slightly seasick.

The shape that reads as a camera move is the same one the talking-head zooms use:

    flat  ->  fast eased move (>=8% over ~0.35s)  ->  flat

`zexpr` takes keyframes in CLIP-LOCAL seconds and returns a zoompan `z` expression that
holds between them and eases with smoothstep (p*p*(3-2p)). Linear ramps start and stop
abruptly at the keyframes, which is the other half of what reads as mechanical.

`xy` centres the crop on a point in 1920x1080 space, so a push-in can be aimed at the
thing that matters rather than always at frame centre.
"""

FPS = 30
UP = 2          # sources are upscaled UPx before zoompan, for clean subpixel motion


def zexpr(keys, fps=FPS, ease="smooth"):
    """keys: [(t_seconds, zoom), ...]. Holds between keys, eases across each move.

    ease="smooth"   smoothstep, p*p*(3-2p)          - punchy, symmetric
    ease="inout"    power2.inOut, GSAP's curve      - the ui-focus-zoom camera servo
    """
    kf = [(int(round(t * fps)), z) for t, z in keys]
    expr = f"{kf[0][1]}"
    for (f0, z0), (f1, z1) in zip(kf, kf[1:]):
        if f1 <= f0 or abs(z1 - z0) < 1e-6:
            expr = f"if(lt(on,{f1}),{expr},{z1})"
            continue
        p = f"((on-{f0})/{f1 - f0})"
        if ease == "inout":
            # power2.inOut: 2p^2 below the midpoint, 1-2(1-p)^2 above it
            eased = f"(if(lt({p},0.5),2*{p}*{p},1-2*(1-{p})*(1-{p})))"
        else:
            eased = f"({p}*{p}*(3-2*{p}))"
        expr = f"if(lt(on,{f0}),{expr},if(lt(on,{f1}),{z0}+({z1}-{z0})*{eased},{z1}))"
    return expr


def xy(px=None, py=None, up=UP):
    """zoompan x/y expressions centring the crop on (px,py) in 1920x1080 space.

    Clamped so the crop never runs off the source, which would letterbox one edge.
    """
    ex = "iw/2-(iw/zoom/2)" if px is None else \
         f"max(0,min(iw-iw/zoom,{px * up}-(iw/zoom/2)))"
    ey = "ih/2-(ih/zoom/2)" if py is None else \
         f"max(0,min(ih-ih/zoom,{py * up}-(ih/zoom/2)))"
    return ex, ey
