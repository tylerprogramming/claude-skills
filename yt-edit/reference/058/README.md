# 058 — the reference build

The most complete worked example in this skill. A 78-minute two-camera capture cut to
33:24, with graphics, punch-ins, secret blurring and per-keep window handling.

`recut.py` is the file to read first and the one to copy. Everything below is a map of
what it does and why, so you can lift the parts you need.

## The shape of it

One config block at the top, all keyed by **source second of a keep start**:

| dict | what it controls |
|---|---|
| `CAMERA_SPANS` | source ranges rendered full-frame camera instead of screen+circle |
| `CAM_OVERLAYS` | graphics MOVs composited over a camera group |
| `CAM_ZOOMS` | camera zoom keyframes, clip-local seconds |
| `SCREEN_ZOOMS` | screen punch-ins, plus an anchor in original 1920x1080 coords |
| `BROWSER_KEEPS` | keeps whose window is a browser (chrome gets cropped) |
| `BROWSER_CROP_X` | which 210px of width that keep gives up |
| `BLURS` | secret regions, in pre-crop coordinates |
| `PIP_LEFT` | keeps where the circle moves to the bottom-left |

Every one of those is validated against the cut plan at startup. A key that matches no
keep start is a hard exit, not a warning — see SILENT-FAILURES.md §1 for why.

## Order of operations inside a screen clip

This order is load-bearing:

```
trim → BLUR (pre-crop coords) → chrome crop + rescale → supersample 2x → zoompan
     → concat → overlay circle mask → overlay circle ring
```

- Blurs run **before** the crop so their boxes stay in original coordinates.
- The circle is composited **after** the zoompan, so a screen punch-in never scales it.
- Zoom anchors are authored in original coordinates and converted through the crop
  (both axes — see below).

## Things that took a rebuild to get right

**The chrome crop must preserve aspect.** Cropping `1920x962` and scaling to `1920x1080`
stretches vertically by 1.1227. Take a 16:9 window instead:

```python
BROWSER_CW = 1710      # round((1080 - CHROME_Y) * 16 / 9)
```

Then the anchor conversion needs **both** axes, because the crop now moves x too:

```python
if cropped:
    cx = BROWSER_CROP_X.get(round(a, 2), (1920 - BROWSER_CW)//2)
    k_ = 1920.0 / BROWSER_CW
    ax = (ax - cx) * k_
    ay = (ay - CHROME_Y) * k_
```

**Which side to crop is a measurement**, and the metric must count flat panels, not just
edges — a floating terminal is a big dark rectangle with almost no internal edges. See
MEASUREMENTS.md → "Which side to crop".

**Camera and screen moves need different durations for the same feel.** Camera zooms at
13% over 0.4s measure 1.9%/frame. A 24% screen punch at the same duration hits 2.97% and
reads as a snap. Scale duration with distance.

**Section intros go full-frame camera.** Found by combining static screen with absence of
pointing language, then keep-aligned and gaze-checked. MEASUREMENTS.md has the recipe.
This is what turns a screen-share into a video.

## Graphics builders

`build_hook.py` — one transparent composition for the whole 17.5s hook, registry
components (`bottom-up-letters`, `dynamic-grid`) pulled in with `grab()`, every beat
pinned to a word from `recut_words.json`. One timeline, so nothing drifts between beats.

`build_hook_shot.py` — the hook's camera zooms, the desktop insert with its travel-up
landing, and the graphics composite in a single encode.

`build_outline.py` — mounting a registry component (`grid-card-assemble`) as a child of a
1920x1080 host. Shows the two things that go wrong: variables that never arrive, and the
child keeping its own 4.5s duration. Both patched in a copy of the component, with an
assert on every substitution.

`build_outline_broll.py` — rounded-rect video insets with a 4px border and a caption that
travels with the clip. Note the cache key includes the border colour.

`build_hardware.py` / `build_hardware2.py` — a 4-slot list that appears, is interrupted by
a walkthrough, then **returns carrying its history** (covered slots stay ticked). The
second file spans a cut, which is what forced `src2local()`.

`zoomlib.py` — `zexpr` (hold → smoothstep move → hold), `xy` (anchor a crop on a point),
`UP` (supersample factor).

## Numbers from this build

- 176 keeps, 33:24.53 from 78.4 min raw
- camera 244s / screen 1761s after the section-intro pass
- accent `#F8C000`, sampled from the app capture
- his warm span on camera is x 720-1130, so the free band is x 90-650 (or the mirror,
  x 1180-1860, used for the outline cards)
- browser chrome is 118px tall; 21 of 159 screen keeps are browsers
