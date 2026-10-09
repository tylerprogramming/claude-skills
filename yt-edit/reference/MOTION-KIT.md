# Motion kit — what to build and how it moves

Built on 047. Every entry here shipped and was verified on screen. Reuse these rather than
inventing per video; the timings and the failure modes are the expensive part.

Source of the pacing rules: `~/content/youtube/analytics/2026-08-16-nate-herk-first-2min-teardown.md`
plus a frame-by-frame pass over his 189K video (`yt-dlp --extractor-args
"youtube:player_client=mweb"` — the default client 403s).

---

## 1. Registry components actually used

| Component | Install | Used for |
|---|---|---|
| `bottom-up-letters` | `npx hyperframes@latest add bottom-up-letters --dir overlays/build/bot` | kinetic captions; letters rise and fade in per character |
| `number-pop-in` | `... add number-pop-in --dir overlays/build/num` | stat/number reveals |
| `code-scroll` | `... add code-scroll --dir overlays/build/cs` | scroll a long file and land on ONE target line |
| `caption-editorial-emphasis` | `... add caption-editorial-emphasis` | word-by-word subtitle emphasis |

**`code-scroll` has no authoring CLI.** It renders from `window.__TOKENS.<seq>.states[0].tokens`,
a flat list of `{key, content, color}` with `"\n"` entries as line breaks, plus
`window.__BLOCK = {id, effect:"scroll", seq, line, duration}`. Generate the token list
yourself with a small tokenizer — the engine only needs content + colour. See
`scripts/build_codescroll.py` in the 047 project.

> **Trap:** injecting that JSON with `re.sub` and a replacement *string* silently corrupts
> it — `re.sub` processes backslash escapes, so json's `\n` becomes a real newline inside a
> JS string literal and the whole script dies (the block renders its chrome and no code).
> Pass a **callable** as the replacement.

---

## 2. Custom motions built (not in the registry)

**Card travel-from-below** — the signature move, measured off Nate's frames at 8fps.
Cards do **not** fade in 20px; they travel from off the bottom of the group into their slot
over **~0.65s**, decelerating hard. Cards already placed never move.
```js
tl.fromTo(el, {opacity:0, y:430, scale:0.94},
              {opacity:1, y:0, scale:1, duration:0.66, ease:"power3.out"}, at);
```
Stagger 0.15s between cards.

**Self-drawing line glyph** — SVG path with `stroke-dasharray` set to the path length and
`stroke-dashoffset` animated to 0. Draw it dim on *arrival*, then only recolour on
activation; a card whose icon appears late looks empty while it waits.

**Fill-up activation** — a state change reads better as a fill than a border swap. An
absolutely-positioned `<i>` with `transform-origin: 50% 100%` and `scaleY` 0→1, plus a
border colour change and a box-shadow bloom on the same beat.

**Strike-through** — `<u>` at `top:52%`, `width:0` → `width:108%`, `ease:"power2.inOut"`,
0.26–0.34s. Hold the struck item at full opacity for **at least 0.9s** before dimming, or
the strike never registers.

**Centralise-and-hold** — collapse a list to its single most important item: fade the
others, then move the survivor with
`{left:"50%", top:"50%", xPercent:-50, yPercent:-50, scale:2.35, ease:"power3.inOut"}`.

**HUD assembly** — rows land on their words, each with a bar filling
(`scaleX` 0→1, 0.52s) and a status dot going accent. Better than static cards because it
is *happening* rather than *displayed*.

**Typing** — per-character reveal via `onUpdate` slicing a string by `this.progress()`.
Never GSAP's `text` property: it needs TextPlugin, is not loaded, and fails **silently**.

---

## 3. Zoom — the whole system

Two forms, both compiled into a `zoompan` expression by `zexpr()` in `build_intro.py`:

```python
ZOOM = [
  (1.00, 1.06),                                  # linear drift across the clip
  [(0.00,1.00),(1.12,1.00),(1.40,1.11),          # keyframed: hold, then PUNCH on a word
   (3.84,1.11),(4.12,0.99),                      # snap out
   (5.18,0.99),(5.46,1.10),(9.61,1.14)],         # punch in again
]
```
Keyframe times are **seconds from the start of that clip**, not recut time.

**Rules learned the hard way:**

- **Photographic footage zooms cleanly; synthetic text does not.** `zoompan` rounds its
  crop window to whole pixels. On camera footage that is invisible. On rendered UI text and
  1px borders it shimmers — measured **0.365** frame-to-frame with nothing animating, versus
  0.002 pixel-locked. GPU layer promotion (`will-change`, `translateZ`) only got it to 0.327.
  **Never zoom a HyperFrames scene.** Give it motion from element builds and a drifting
  *text-free* glow layer instead.
- Supersample **2x** (`scale=3840:2160`) before `zoompan` regardless.
- A move needs **≥8% delta over ~0.3s** to read against a talking head's natural motion.
  A 7% move measured 1.48 against holds of 1.46 — invisible.
- Pin every move to a **word**, not a round number. Re-transcribe the window in isolation
  first (see §5).
- Alternate direction between clips. Hold, move fast, hold — never a constant creep.
- **Set move DURATION from the distance, not a constant.** A move is smooth below about
  **1.9% scale change per frame**; above that it reads as a snap. Camera zooms of 13%
  over 0.4s sit at 1.9%/frame and feel right. Reusing that same 0.4s for a 24% screen
  punch-in doubles the per-frame step to 2.97% and looks harsh — Tyler flagged it before
  any metric did. Holding ~1.7%/frame: 18% → 0.53s, 20% → 0.60s, 22% → 0.63s, 24% → 0.70s.
- **Carry the scale across cuts.** If a clip ends at 1.13, the next move starts at 1.13
  and goes out. Resetting to 1.00 at every cut makes the cut itself jump.
- Cap screen zooms at **1.30**. 1080p UI text upscaled past that goes soft.
- Anchor screen punch-ins at the **named thing** (`xy(px, py)`), not frame centre. If the
  frame was cropped first, convert the anchor through the crop on **both** axes.

---

## 4. Pacing targets (from the teardown, verified by measurement)

| Metric | Target | How to measure |
|---|---|---|
| face on screen | **~35%** | warm-pixel count (`r > b+16 and r > 62`) in his frame region, sampled every 0.25s |
| face-free | ~65% | the complement |
| longest bare-face run | **< 7s** | run-length over the same series |
| new visual | every ~3s in the first 30s | contact sheet at 2–3s intervals |

**Anchor the face-detection threshold on a known bare-talking-head window**, not on the
brightest frames in the file. A warm b-roll shot inflates the reference and the ratio reads
several points low — this produced a wrong 32.0% that was really 36.0%.

**Plate opacity decides whether a beat counts as face-free.** 0.72 leaves him visible;
0.90 effectively removes him. If a graphic can carry its own dark ground (cards, tiles),
drop the plate entirely and keep the face — that is how the ratio gets *back up*.

---

## 5. Transcript discipline

Whisper's full-file pass **stretches words over silence**. On 047 it placed "tasks" at
29.37; re-transcribing src 86–102 alone put it at **28.27** — 1.1s out, enough to make a
whole HUD feel sluggish. It also hallucinated a word ("them") 0.5s into pure room tone.

**Before pinning any animation, re-transcribe that window on its own:**
```bash
ffmpeg -ss <t0> -t <dur> -i CAMERA.mp4 -vn -ac 1 -ar 16000 w.wav
whisper-cli -m ~/models/ggml-base.en.bin -f w.wav -ml 1
```
Cross-check boundaries against 20ms RMS energy, not the transcript.

---

## 6. AI video (Seedance) — when it earns its place

**Rule: mood, never fact.** Six generations on 047, three used.

| Used | Why |
|---|---|
| bright workspace, calendar + docs on screen | establishing shot, delays the face |
| dark room, glowing screen, sunrise | "while you sleep" is a mood |
| kitchen, coffee mug, one hand on a laptop | "not an engineer" is a *look* |

| Rejected | Why |
|---|---|
| hooded figure, blacked-out room | cybercrime read on a video about doing this safely |
| candlestick trading charts | says day-trader, not AI automation |

Anything **specific** — real secrets, named employers, actual code, brand marks — must be a
graphic. Generated footage makes specifics vaguer.

Prompt defensively: name what you do **not** want (`NO hoodie, NO dark room, NO candlestick
charts, NO text overlay`) and lock the camera (`push-in only, no lateral drift`) or the
subject drifts out of frame.

---

## 7. Brand marks

`npm i simple-icons`, then `si<Namelowercase>` — `siGooglecalendar`, `siGoogledrive`,
`siGoogledocs`, `siClickup`, `siGmail`, `siClaude`. Casing matters: `siGoogleDrive` is
`undefined`.

**Slack, Salesforce and the Microsoft marks are NOT in the set** — removed at those
companies' request. Use a neutral tile with the app name; never draw a substitute mark.
Employer logos (IBM, Pfizer) are also absent and imply endorsement anyway — set those
typographically.

## Zooms must be defined on the FILM timeline, not per clip

The 056 intro had a zoom per camera clip. It read as sluggish, and the reason was not
easing — it was that **most camera clips are hidden under a full-frame cutaway**. Audited:
of 14 moves, 10 fired entirely underneath a cutaway and were never seen. The punch written
for clip 0 ran 3.20-3.52, and the cold open covered 2.30-4.75. The 4 that were visible ran
at **0.9-2.2%/s** against the 27%/s threshold, because a per-clip ramp spreads one move
across the clip's whole length.

Build it the other way round:

1. Compute the **visible windows** = the timeline minus every cutaway's enable range.
   On 056 that was 21.9s of visible camera in an 87.9s intro, in 9 windows.
2. Put at most one move in each window longer than ~1.2s, pinned to a word. Windows
   under ~1s hold still — there is not enough time for a move to read.
3. **Hold between moves.** A value that is flat until the move and flat after it is what
   makes a move read as a move rather than a drift.
4. Alternate direction. Tyler called a repeated identical punch a tic.

Keep the cutaway list next to the move list; if one drifts from the other the moves start
hiding again silently.

**Ease with smoothstep, not linear.** `p*p*(3-2*p)` in an ffmpeg expression:

```
p    = ((g-a)/(b-a))
eased = z0+(z1-z0)*(p*p*(3-2*p))
```

Linear ramps start and stop abruptly at the keyframes, which is the other half of what
reads as mechanical. Then overshoot and settle — 1.00 -> 1.15 -> 1.11 punches where
1.00 -> 1.11 glides.

After this rewrite every visible move on 056 measured **26-63%/s**, against 2.2%/s before.
