# Measurement recipes

Copy-paste checks. Each one caught a real defect that looked fine on screen, and several
contradicted my own eyes. Run them on the **rendered output**, not the source.

Rule that outranks everything else here: **a metric you have not sanity-checked is a
guess with decimal places.** Three of the measurements below were wrong the first time
and shipped a wrong decision. Each one now carries a note on how it failed.

---

## Duration against the plan

The cheapest check in the file and it catches dropped batches, stale caches and empty
renders in one line.

```python
exp = sum(r["end"] - r["start"] for r in json.load(open("cutplan.json"))["keepRanges"])
got = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                            "-of","csv=p=0",OUT],capture_output=True,text=True).stdout)
assert abs(got - exp) < 0.05, f"{got:.2f}s rendered, plan says {exp:.2f}s"
```

## Cut-plan validity

Run after **every** hand edit to the plan. An inverted range survived a whole render:
`{"start": 706.20, "end": 705.50}` — negative length, left over from a retake removal.
`trim` accepts it silently.

```python
probs=[]
for i,r in enumerate(kr):
    if r["end"] <= r["start"]:        probs.append(("inverted", i, r))
    if r["end"] - r["start"] < 0.30:  probs.append(("sliver", i, r))
for i in range(len(kr)-1):
    if kr[i+1]["start"] < kr[i]["end"]:   probs.append(("overlap", i))
    if kr[i+1]["start"] < kr[i]["start"]: probs.append(("out-of-order", i))
```

## Dead air in the delivered audio

Transcript gaps lie; RMS does not. This found 2.65s of room tone the silence pass had
left inside a keep.

```python
subprocess.run(f'ffmpeg -v error -i "{OUT}" -vn -ac 1 -ar 16000 -f s16le /tmp/a.raw -y', shell=True)
a = np.fromfile("/tmp/a.raw", dtype=np.int16).astype(np.float32)/32768
hop = int(0.02*16000); n = (len(a)-hop)//hop
db = np.array([20*np.log10(np.sqrt((a[i*hop:i*hop+hop]**2).mean())+1e-12) for i in range(n)])
# report every run below -45 dB longer than 0.8s
```

To place the new boundary, find the first frame above -40 dB (speech onset) and snap to
the **lowest-RMS 20ms frame in the 0.45s before it**, then frame-align to 1/30.

## Zoom visibility and smoothness

Two different questions. Visibility is total percent; smoothness is **per-frame step**.

```python
def curve(keys, fps=30):       # smoothstep between keyframes
    kf=[(int(round(t*fps)), z) for t,z in keys]; out=[]
    for f in range(kf[0][0], kf[-1][0]+1):
        v=kf[-1][1]
        for (f0,z0),(f1,z1) in zip(kf,kf[1:]):
            if f0<=f<f1:
                p=(f-f0)/(f1-f0); v=z0+(z1-z0)*(p*p*(3-2*p)); break
        out.append(v)
    return out

c=curve(keys); d=[abs(c[i+1]-c[i]) for i in range(len(c)-1)]
mv=[x for x in d if x>1e-6]
print(f"max step {max(mv)*100:.2f}%/frame   total {(max(c)/min(c)-1)*100:.1f}%")
```

**The envelope that matters:** camera zooms that read as smooth measured **1.77-1.92
%/frame**. Screen punch-ins built at the same 0.4s duration but twice the distance hit
**2.97 %/frame** and read as a snap. Tyler noticed before I measured.

So: **set move duration from the distance, not a constant.** Holding ~1.7%/frame gives
18% → 0.53s, 20% → 0.60s, 22% → 0.63s, 24% → 0.70s.

Floor for visibility is ~8% total; under that it reads as nothing.

## Did the zoom actually fire, and by how much

Optical scale measurement, for verifying on the render rather than trusting the keyframes.

```python
def prof(t):                      # vertical-edge strength per column
    grab(t); im = np.asarray(Image.open(o).convert("L")).astype(float)
    return np.abs(np.diff(im, axis=1)).mean(0)

def measure(t0, t1, cx=960.0):
    a,b = prof(t0), prof(t1); N=len(a); xs=np.arange(N); best=None
    for s in np.arange(0.85, 1.30, 0.002):
        idx=(xs-cx)/s+cx; ok=(idx>=0)&(idx<=N-1)
        c=np.corrcoef(np.interp(idx[ok],xs,a), b[ok])[0,1]
        if best is None or c>best[1]: best=(s,c)
    return best                    # (scale, correlation)
```

**Trust it only when the correlation is high (>0.8).** Sample either side of the move
with a small margin, and be aware of two ways it lies:

- **Page content changed between the two samples** (a terminal printed, a page scrolled).
  Correlation collapses to 0.3-0.6 and the scale is meaningless.
- **The webcam circle does not scale with the screen**, so including it in the profile
  corrupts the fit. Restrict to rows above the circle.

When content is moving throughout, verify the **expression and the timing** instead
(evaluate the curve, compare the move start against a frame-delta scan) rather than
forcing an optical fit.

## Aspect distortion

This is the one that shipped. A chrome crop of `1920x962` scaled back to `1920x1080`
stretches vertically by 1.1227 and leaves width alone. Round avatars became ovals.

Fit **both axes independently** and compare:

```python
rows = lambda im: np.abs(np.diff(im[:,100:1300], axis=0)).mean(1)   # horizontal edges
cols = lambda im: np.abs(np.diff(im[100:900,:],  axis=1)).mean(0)   # vertical edges
v = fit(rows(src), rows(out), offsets=range(100,140,2))
h = fit(cols(src), cols(out), offsets=range(-20,40,4))
print(f"aspect error {abs(v[0]-h[0])/h[0]*100:.2f}%")     # 0.00% is the target
```

Before: vertical 1.1220, horizontal 1.0000 → **12.2% error**.
After taking a proper 16:9 window (`1710x962`): both 1.1220 → **0.00%**.

Any crop that changes only one dimension needs the other cropped to match:
`CW = round((1080 - CHROME_Y) * 16/9)`.

## Which corner for the webcam circle

Do not eyeball this either. Three of four hand-written `PIP_LEFT` spans were **backwards**
— the circle was sitting on the content it was meant to avoid.

```python
D, M = 480, 50
y0, y1 = 1080-D-M, 1080-M
dens = lambda a: float((np.abs(np.diff(a, axis=1)) > 12).mean())
L = dens(im[y0:y1, M:M+D]); R = dens(im[y0:y1, 1920-D-M:1920-M])
# circle goes LEFT only when the right corner is clearly busier
```

Sample at 20/50/80% through each keep (a window can change mid-clip) and require
`R > L*1.35` and `R > 0.02` before moving it. Measured example: src 930 reads left 3.1%
vs right 1.4%, so the circle belongs **right** — the opposite of what the list said.

## Which side to crop

Same trap, worse consequences: it cuts content off frame. Score every candidate x by the
**weight it deletes** and take the minimum.

```python
bg = np.median(np.concatenate([im[:, :6].ravel(), im[:, -6:].ravel()]))
e  = np.zeros(im.shape[1]); e[1:] = (np.abs(np.diff(im, axis=1)) > 18).mean(0)
dv = (np.abs(im - bg) > 30).mean(0)
W  = e*3.0 + dv                                  # edges matter more, flat panels count
cost = {x: float(W[:x].sum() + W[x+CW:].sum()) for x in range(0, CUT+1, 3)}
best = min(cost, key=cost.get)
```

**Edges alone are not enough.** A floating terminal is a large flat dark panel with almost
no internal edges; an edge-only metric scored the busy browser page behind it and cropped
32px off the terminal including the shell prompt. The deviation term is what fixes it.
Take the max weight across several samples per keep, because windows open and close.

## Is a window a browser (does it need the chrome crop)

Correlate the **bookmarks-bar rows** against a confirmed browser frame:

```python
ref = strip(KNOWN_BROWSER_SECOND, y0=36, y1=62).ravel(); ref -= ref.mean()
x = strip(t, 36, 62).ravel(); x -= x.mean()
corr = float((x*ref).sum()/np.sqrt((x*x).sum()*(ref*ref).sum()))
# > 0.40 = browser
```

Reads +0.5 to +1.0 on a browser, below +0.05 otherwise.

An earlier version tested for a **brightness edge at y=118** and found only 11 of 21. It
missed every keep where a terminal floats **over** the browser: the terminal body kills
the edge, but the tab strip is still on screen. The bookmarks bar is the honest signal
because it belongs to the browser, not the page.

When chrome appears or disappears **mid-keep**, bisect the correlation to 1/30s and
**split the keep** there rather than leaving it uncropped:

```python
def find(lo, hi):                     # chrome present at lo, absent at hi
    for _ in range(12):
        mid=(lo+hi)/2
        if corr(mid) > 0.4: lo=mid
        else: hi=mid
    return round(round(hi*30)/30, 4)  # frame-aligned
```

The split is lossless — total duration is unchanged — and it stopped a Slack workspace
URL being on screen for 11 seconds.

## Secrets

Scan the **whole film**, not the part under review. A contact sheet every 60s, read at
full resolution wherever anything looks like a credential.

Verify a blur by measuring high-frequency detail inside the box against a reference strip
of the same page:

```python
hf  = np.abs(np.diff(im[by:by+bh, bx:bx+bw], axis=1)).mean()
ref = np.abs(np.diff(im[300:336,   bx:bx+bw], axis=1)).mean()
assert hf < ref*0.5          # blurred
```

`0.00 vs 0.09` is a properly destroyed line.

One secret is usually several: an OAuth code appeared in the **terminal URL**, the
**browser address bar**, and the account **email in the page footer** simultaneously.

## Circle integrity

```python
reg  = im[550:1030, x0:x0+480]
rows = np.where(reg.max(axis=1) > 200)[0]; cols = np.where(reg.max(axis=0) > 200)[0]
h, w = rows[-1]-rows[0]+1, cols[-1]-cols[0]+1
assert abs(h-w) <= 6 and abs(h-480) <= 14      # round, and not scaled by a zoom
```

Also check the **border is outside the camera**. The mask was drawn at the full 480px
while the ring's outer edge stopped at 477, leaving ~2px of raw camera beyond the border
on every frame. Tyler spotted it; no metric was watching for it.

```python
on  = np.where(mask_row > 127)[0]      # camera extent
onr = np.where(ring_alpha_row > 20)[0] # ring extent
assert on[-1] <= onr[-1] and on[0] >= onr[0]
```

Generate them together so they cannot drift: mask diameter `D - 2*B`, ring annulus from
`D - 2*B` out to `D`, both at 8x supersample.

## Face ratio and pacing

```python
# warm-pixel ratio per frame, threshold anchored on a known bare-face window
# cuts: frame-delta spikes above mean + 1.2*std, runs >= 4 frames
```

Targets, from the teardown and confirmed on a delivered cut:

| | target | 056 delivered |
|---|---|---|
| face on screen, intro | ~35% | 28.4% |
| graphic/cutaway | 70%+ | 77.3% |
| longest bare talking head | under 7s | 4.0s |
| cuts in first 50s | ~21 | 21 |
| first cut away from face | ~1.2s | 2.30s |

## Finding talking-head stretches automatically

For deciding where the picture should leave the screen and go full-frame camera. Two
conditions **together**; either alone is wrong:

1. screen motion under 1.6 at 1s resolution (nothing happening on screen), and
2. no pointing language within ±4s

```python
POINT = re.compile(r"\b(if (we|you) (go|click|open|scroll|come)|come (over|down|up) here|"
                   r"right here|over here|you can see|click|let me show|here it is|"
                   r"i go to|go all the way|paste|type|scroll|down here|up here|"
                   r"this (page|screen|tab|file)|at the top|top left)\b", re.I)
```

Then require the run to be **≥12s**, keep-align it (a keep joins only if >55% of it falls
inside), and **check his gaze** on the camera frames before committing.

The end of each span is the **first pointing phrase**, so the picture returns to the
screen exactly when he starts demonstrating.

On 058 this found 30 raw candidates, which narrowed to 5 after those filters. Static
screen alone would have given 68 and turned the film into a talking-head reel.
