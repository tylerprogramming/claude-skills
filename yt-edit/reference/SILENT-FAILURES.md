# Silent failures — exit code 0, broken video

Every entry here produced a file that rendered, played, had the right duration, and was
wrong. None of them raised an error. This is the most expensive file in the skill; read
it before building anything that composites.

The pattern they share: **the render pipeline has no idea what the video is supposed to
look like.** ffmpeg will happily concat a batch that is missing, overlay a graphic that
never fires, and crop a window that isn't there. Only a measurement of the *output*
catches it.

---

## 1. A keyed dict whose key no longer matches a keep start

The worst one. It ate a graphic three separate times on 058.

Overlays, zooms, crops and blurs are all keyed by **source second of the keep they belong
to**:

```python
CAM_OVERLAYS = {238.17: [".../outline.mov"]}
```

Trim that keep's head to remove dead air and its start becomes `241.04`. The key now
matches nothing. The group renders as bare camera. Duration is correct, ffmpeg is happy,
the log says nothing.

**Fix — fail loudly at startup:**

```python
_starts = {round(a, 2) for a, _ in keeps}
for _name, _d in (("CAM_OVERLAYS", CAM_OVERLAYS), ("CAM_ZOOMS", CAM_ZOOMS),
                  ("SCREEN_ZOOMS", SCREEN_ZOOMS), ("BROWSER_KEEPS", BROWSER_KEEPS),
                  ("BLURS", BLURS)):
    _dead = [k for k in _d if round(k, 2) not in _starts]
    if _dead:
        _near = sorted(_starts, key=lambda s: min(abs(s - x) for x in _dead))[:4]
        sys.exit(f"{_name} keys match no keep start: {_dead}\n"
                 f"  nearest keep starts: {sorted(_near)}\n"
                 f"  a trimmed keep moves its start - update the key.")
```

Related trap: a **span** list like `CAMERA_SPANS` fails the same way but quieter, because
a span is a range test rather than an exact match. After trimming a keep from 322.60 to
325.13, a span written `(322.0, 355.0)` still matches, but one written `(325.0, 355.0)`
stops matching the keep that now starts at 325.13 only if you are unlucky with rounding.
Prefer generous span bounds and exact-match asserts on the dicts.

## 2. ffmpeg exits 0 having written nothing

A malformed filtergraph makes ffmpeg print

```
Nothing was written into output file, because at least one of its streams received no packets.
```

and **return success**, leaving a 0-byte file. The concat demuxer skips it without
complaint. A 5-minute preview came out as 2:28 this way.

```python
def run(c):
    r = subprocess.run(c, capture_output=True, text=True)
    if r.returncode: sys.exit(f"FAILED {' '.join(c[:12])}\n{r.stderr[-2500:]}")
    dst = c[-1]
    if isinstance(dst, str) and dst.endswith((".mov", ".mp4")):
        if not os.path.exists(dst) or os.path.getsize(dst) < 1024:
            sys.exit(f"EMPTY OUTPUT {dst}\n{' '.join(c[:12])}\n{r.stderr[-3000:]}")
```

Always also assert the **final** duration against the sum of the keep ranges. That single
check catches a whole class of dropped-batch bugs:

```python
exp = sum(b - a for a, b in keeps)
got = float(ffprobe_duration(out))
assert abs(got - exp) < 0.05, f"{got:.2f}s rendered, plan says {exp:.2f}s"
```

## 3. Batch cache keyed on index

Batches named `b000.mov`, `b001.mov` are reused across runs with **different clip lists**.
Asking for a 3-minute preview returned the previous 4-minute file: same name, same
duration as last time, no error.

Name every intermediate by a **hash of its own content spec**:

```python
tag = hashlib.md5(repr(clips).encode()).hexdigest()[:6]
dst = os.path.join(WORK, f"b{idx:03d}-{tag}.mov")
```

## 4. Cache signature that doesn't cover everything that changes the picture

The batch directory is keyed on a hash. If that hash covers only `cutplan.json`, then
moving a span to camera, adding an overlay, changing the crop, or **rebuilding a MOV**
all silently reuse the old render.

The signature must include the plan, every treatment constant, and the **mtime of every
graphics MOV**:

```python
sig = (open("cutplan.json","rb").read()
       + repr((CAMERA_SPANS, PIP_LEFT, CROP, CHROME_Y, sorted(BROWSER_KEEPS),
               sorted(SCREEN_ZOOMS.items()), sorted(CAM_ZOOMS.items()),
               sorted(BLURS.items()), CIRCLE_D, MARGIN,
               sorted(CAM_OVERLAYS.items()))).encode())
for _, ps in sorted(CAM_OVERLAYS.items()):
    for p in ([ps] if isinstance(ps, str) else ps):
        if os.path.exists(p): sig += str(os.path.getmtime(p)).encode()
h = hashlib.md5(sig).hexdigest()[:8]
```

## 5. Generated PNG assets cached past a size change

`make_rr()` skipped regenerating the rounded-rect mask and border when the files already
existed. Changing the insert from 1400x788 to 1600x900 therefore had **no effect**, and
later the mismatch surfaced as `alphamerge: Input frame sizes do not match` after a full
shot render had already burned minutes.

Put every dimension **and colour** in the cache key:

```python
ck  = f"{BW}x{BH}_{BORDER_RGBA[0]}{BORDER_RGBA[1]}{BORDER_RGBA[2]}"
b_p = os.path.join(ASSETS, f"broll_border_{ck}.png")
```

## 6. A code path that announces the right thing and then does the wrong thing

Verbatim from `recut.py`:

```python
if os.path.exists(gfx):
    print("  hook: using graphics build")     # ← printed
# ...falls through and re-renders bare camera, discarding gfx
```

The log said the graphics build was in use. It wasn't. If a branch claims to use a
prebuilt artifact, it must **return it** and assert its duration matches the group:

```python
got = ffprobe_duration(gfx); want = sum(b - a for a, b in clips)
assert abs(got - want) < 0.05, f"{gfx} is {got:.2f}s, group needs {want:.2f}s"
return gfx
```

## 7. Overlay time is GROUP-LOCAL, not source and not recut

A graphics MOV is composited over the **concatenated** camera group. Its clock starts at
the group's first frame.

- Pinning in **recut** seconds breaks on every cut-plan edit.
- Pinning in **source** seconds and subtracting the span start breaks the moment a cut
  falls inside the beat: everything after the cut fires late by exactly the removed
  duration, and nothing fails.

On 058 the hardware2 beat spans a cut at src 421.90 → 426.47, so straight subtraction put
every beat after it 4.57s late. Walk the cut plan instead:

```python
KEEPS = [(r["start"], r["end"]) for r in json.load(open("cutplan.json"))["keepRanges"]
         if LO <= r["start"] < HI]
DUR = round(sum(b - a for a, b in KEEPS), 2)

def src2local(t):
    acc = 0.0
    for a, b in KEEPS:
        if a <= t < b: return round(acc + (t - a), 2)
        acc += b - a
    raise SystemExit(f"beat at src {t} falls in a REMOVED region, re-pin it")
```

`src2local` raising on removed material is the point: a beat pinned to a word you later
cut should stop the build, not silently slide.

Also assert every beat finishes inside `DUR`. A tween scheduled past the composition's
duration **never runs**:

```python
for k, v in BEATS_SRC.items():
    assert src2local(v) + 0.5 <= DUR, f"beat {k} at src {v} past DUR {DUR}"
```

## 8. Registry component variables that never arrive

`data-composition-variables` on the host element looks like it passes values down. It
does not override the component's own **declared defaults**. `grid-card-assemble`
rendered its stock "Capture / Compose / Render / Publish" cards while the host declared
six real agenda items, and no warning appeared.

Patch the declared defaults in a **copy** of the component, and assert every substitution
landed:

```python
src = open(REGISTRY_COMPONENT).read()
for old, new in subs:
    assert old in src, f"component changed upstream, not found: {old[:60]}"
    src = src.replace(old, new)
open(dst_path, "w").write(src)
```

Two separate places need patching, and the JS fallback alone is not enough:

- the `data-composition-variables` JSON block (~line 64) — this is what the runtime injects
- the `vars.x === undefined ? default : vars.x` fallbacks in the script body

The same applies to **duration**: an elastic component keeps its own `data-duration`
(4.5s on `grid-card-assemble`) and everything vanishes partway through a 28s beat.

## 9. Compositing order

`overlay` puts the second input **on top**. A "ground" layer composited last lands over
the content it is supposed to sit behind. The dynamic-grid drew lines across the desktop
insert until the graphics MOV was composited onto the camera *first*, with the insert
placed over it.

## 10. An unclamped ramp keeps ramping

```
y = 690 - 510 * (t - t0) / 0.55        # ← keeps growing forever
y = 690 - 510 * min(1, max(0, (t-t0)/0.55))
```

Overlay expressions are evaluated **every frame**. Without the clamp the card travels for
the entire beat instead of landing in half a second. It looked like a slow drift, not a
bug. Measure the element's top edge per frame to confirm it lands:

```
690 → 180 over 0.5s, then flat at 170-180   ✅
690 → 180 → 41 → -97 ...                     ❌ unclamped
```

---

## ffmpeg-specific traps

**`boxblur` radius is bounded by the region, per plane.** Luma must be `< min(w,h)/2`;
the chroma plane is 4:2:0 subsampled so its limit is **half that again**. A 36px-tall box
caps at 17 luma / 8 chroma. Set them independently:

```python
lr = max(2, min(bw, bh)//2 - 1)
cr = max(1, min(bw, bh)//4 - 1)
f"boxblur=luma_radius={lr}:luma_power=4:chroma_radius={cr}:chroma_power=4"
```

Errors: `Invalid luma_param radius value 22, must be >= 0 and < 18`, then
`Invalid chroma_param radius value 17, must be >= 0 and < 9`.

**A `split`/`overlay` cannot be spliced into the middle of a comma chain.** Filters joined
by `,` form one linear chain; anything that forks needs its own `;`-terminated chain with
explicit labels. Splicing produced
`Terminating thread with return code -22 (Invalid argument)` and an empty file.

```python
src = f"[s{i}]"
for bi, (bx, by, bw, bh) in enumerate(BLURS.get(round(a,2), [])):
    o = f"[bo{i}_{bi}]"
    fc += (f"{src}split[bs{i}_{bi}][bm{i}_{bi}];"
           f"[bm{i}_{bi}]crop={bw}:{bh}:{bx}:{by},boxblur=...[bb{i}_{bi}];"
           f"[bs{i}_{bi}][bb{i}_{bi}]overlay={bx}:{by}{o};")
    src = o
```

**This ffmpeg build has no `drawtext`** (`No such filter: 'drawtext'`). Render labels to
PNG with PIL and overlay them — which also gets the house typeface instead of whatever
fontconfig resolves.

**A `zoompan` anchor must be converted if the frame was cropped first.** Anchors are
authored in original 1920x1080 coordinates; after a chrome crop the same feature has
moved:

```python
if cropped:
    ay = (ay - CHROME_Y) * 1080.0 / (1080 - CHROME_Y)
```

Skip it and the punch-in aims ~130px low and the target drifts out of frame.

---

## hyperframes CLI gates — run both, they find real defects

```bash
cd overlays/build/<dir> && hyperframes lint && hyperframes check
```

`lint` catches structural problems that otherwise waste a 45s render:

| error | meaning |
|---|---|
| `root_missing_dimensions` | the composition has no `data-width`/`data-height` |
| missing `data-composition-id` | the host element needs its own id |
| wrong relative `data-composition-src` | resolved relative to `index.html`, not the script |
| missing `data-no-timeline` | parent has no timeline of its own; without it the render waits |

`check` catches rendering defects a screenshot will not show you:

| error | what it caught on 058 |
|---|---|
| `gsap_non_transform_motion` | animating `fontSize` reflows text and snaps glyphs under seek-by-frame capture — use `scale` |
| `content_overlap` | 132px type colliding with chips; a title at y=150 colliding with a row at y=250 |
| `text_occluded` | a strike bar sitting **on** the text instead of through it |

Project layout the CLI expects: **`index.html` at the project root, `compositions/`
beside it.** `hyperframes render <dir>` looks for `<dir>/index.html` and refuses a path
to a file.

Neither gate replaces looking at frames. `check` passed a title that ran into his chin
and chips too small to read.
