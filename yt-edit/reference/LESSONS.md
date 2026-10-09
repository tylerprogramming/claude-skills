# Gotchas

Every entry here cost real time on a real video. Read before building a graphic or an
ffmpeg filter chain.

## ffmpeg

**`crop` rejects `eval`.** "Error applying option 'eval' to filter 'crop': Option not
found." Its `w`/`h` are init-only; only `x`/`y` are per-frame. For an animated zoom use
`zoompan`; for a constant one use a fixed crop plus scale.

**`crop` freezes `iw`/`ih` at init.** Pair it with an animated `scale` and it silently
crops from the top-left forever, so the thing you were trying to push out of frame never
leaves. Diagnosed by measuring top-row mean RGB over time. Fix: overlay onto a black bed
instead of cropping.

**`zoompan` shakes.** It rounds its crop window to whole pixels, so a slow zoom
oscillates — measured 0.479 against a 0.247 static floor. Fix: supersample 2x before the
zoom (0.273). 3x measured 0.263, not worth the encode time.

**`sendcmd` + `gblur` never reaches sharp.** Constant sigma 30 gave a 0.43 sharpness
ratio and sigma 0 gave 0.95, but every `sendcmd` form plateaued around 0.58 — visibly
still blurry when it should have been clear. Fix: `split` the stream, blur one copy, and
fade the sharp copy in over it.

**Scaling the screen up by k hides `(1080 - 1080/k)/2` off the top**, not
`(1080k - 1080)/2`. Getting that backwards left a sliver of a search field on screen at
k=1.28.

**`-ss <keyframe>` rounds down and lands on the *previous* keyframe.** Asking for exactly
36.376 (a genuine keyframe) seeked back to 28.043 and silently duplicated 8.4 seconds.
Ask for keyframe + 0.024, and size the other segment to `total - measured`.

**`chromakey` destroys black.** Black sits near dark green in its distance metric, so a
black badge and all the dark outlines keyed out along with the background. Fix: key on
green dominance, `min(G-R, G-B)`.

**Default straight-alpha overlay is correct** for `hyperframes render --format mov`
output. `alpha=premultiplied` is wrong and gives dark fringes.

## Overlays

**Render the MOV LONGER than the window it must cover.** With `eof_action=pass`, if the
MOV's last frame lands exactly on a batch boundary the final frame has no overlay left
and the bare footage shows through for exactly one frame. Tyler spots that single frame.
Keep the recut's `dur` at the true window and give the MOV ~0.1s of tail that is never
displayed.

**Animations only composite onto the batches they fall inside.** An `ANIMS` entry that
runs past a shot boundary gets silently dropped at the boundary. Check the shot list
before choosing a duration.

**Do not let a clip fade out under a cut.** A graphic that dissolves over its own last
0.38s reveals whatever is behind it. Hold it opaque and let a flash cover the cut.

**Card backgrounds must be opaque.** At even 7% transparency, bright terminal text ghosts
through and legibility dies.

**Place wide graphics clear of the webcam circle.** Its left edge is at **x=1390** in the
default composite. A 1560-wide chain collided; 1200 cleared. On a `mode="cam"` full-frame
shot there is no circle, so the whole 1920 is free — check which you are on.

**Pick beats where the screen is already dark.** The Claude Code terminal has a large
empty black area below the prompt that needs no scrim. A bright product page does.

## GSAP / hyperframes

**The `text` property needs TextPlugin, which is not loaded.** It fails *silently* — the
first build rendered a title perfectly and no subtitle at all, with no error anywhere.
For typing effects, emit per-character spans and reveal them with `tl.set`.

**`ease: "power2.out"` leaves the start value on only the first frame.** A 0.10 opening
scale therefore flashed past in 1/30s and read as nothing. Use smoothstep, which holds
small, accelerates, then decelerates into the landing.

**Overshoot is what makes a zoom land.** 0.24 → 1.22 → settle at 1.10 punches; 0.24 → 1.10
glides. Keep the overshoot short enough that it is gone before anything enters frame that
the crop would clip.

**A killed render leaves a lock that makes the next one hang, then fail.** `hyperframes
render` writes `.<name>.hf-transaction-*` and `work-*` beside the output. If the process is
killed (a command timeout will do it) those survive, and every later render of the same
output path stalls for minutes and exits 1 with nothing in stderr but a CalledProcessError.
A clean 89s 1080p transparent ProRes render takes about 45 seconds, so anything past a
minute means a stale lock. Fix:

```bash
rm -rf overlays/movs/.<name>.hf-transaction-* overlays/movs/work-*
```

Render to a scratch path and `mv` it into place when in doubt; that also sidesteps the
lock entirely.

## Smoothness

**Seedance renders at 24fps. Your film is 30.** Dropping the clip straight in conforms it
by duplicating every fifth frame: the per-frame delta series reads `0.01, 4.26, 4.28, 7.90,
3.81` on repeat, 22 duplicate frames out of 108, with a double-size jump right after each
duplicate. On 056 that measured a judder ratio of 0.76-0.85 against 0.07-0.29 everywhere
else and was the only place the film visibly stuttered. **Check `r_frame_rate` on every
generated clip before wiring it in.** Fix by rebuilding the frames rather than repeating
them:

```
minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1
```

After: ratio 0.298, zero duplicate frames.

**The judder scan.** Decode to 480x270 gray, `d[i] = mean|f[i]-f[i-1]|` is motion,
`j[i] = |d[i]-d[i-1]|` is judder, and `j/d` over 0.5s windows is the number that matters.
Above ~0.62 with motion above 0.30 is a real problem. **Every hard cut spikes it**, so
build the exclusion list from the actual keep boundaries plus every overlay in/out point,
or you will chase seventeen false positives. A static graphic reads near zero motion and
a meaningless ratio; ignore anything under 0.30 motion.

**Sub-second keeps make the film stutter even when they hold speech.** On 056 a 0.35s clip
and a 0.11s clip landed 0.35s apart, so the camera cut three times inside half a second.
The 0.11s one measured peak -62.8dB with zero frames above -40dB: pure silence, three
frames long. The 0.35s one held a stray "is" between a 3.65s pause and a 2.60s pause, a
false start. The sliver rule (drop keeps under 0.60s isolated by 3.0s of silence on both
sides) missed the cough on the same film because its *leading* gap was only 0.51s. **Print
the keep table with durations and read it** - anything under 0.5s deserves an RMS profile
before it ships.

**A cough looks exactly like a short keep.** 056 had a 0.26s island peaking at -19.9dB
between 0.5s and 4.2s of silence, and Whisper labelled it with the next real word, so the
transcript gave no hint. Profile any isolated sub-0.5s keep: real speech runs -30dB mean
with most frames above -45dB, a cough is a single sharp attack with nothing either side.

**A contact sheet labels frames in the order YOU passed them; ffmpeg emits them in TIME
order.** `select='eq(n,a)+eq(n,b)+...'` returns frames sorted by n regardless of how the
expression was written, so an unsorted timestamp list silently mislabels every tile. It
cost a wrong conclusion about which second of footage held a shot. Sort the list before
building the sheet.

**Pick cutaway footage by measuring it, not by remembering it.** A cold open that looked
fine measured 0.825 mean frame-delta - a still with a zoom on it. Scan the capture for
windows where the CONTENT region is changing every frame while the browser chrome strip is
NOT (a chrome spike means a tab or app switch, not generation), and require the frame to be
dark if the target is a dark-UI app, or the light marketing pages in the same recording
outrank everything.

**Crop the browser chrome out of any screen-capture cutaway.** The tab and bookmark bars
measured y=0..126 on this shoot; leaving them in reads as a raw grab. Find the boundary
with a row-luma profile rather than guessing, then frame the push-in so its top edge clears
it. If the subject sits flush to one edge of the screen, pin the crop to that edge
(`x='iw-iw/zoom'`) instead of centring - a centred crop clips it at every zoom.

**A string patch that does not match fails silently and the build still "succeeds".**
A scratch-render-then-`os.replace` pattern was added to four builder scripts by find/replace.
In one of them the anchor was `print("->",dst)` without a space, the patch expected a space,
so the `os.replace` line never landed. The render wrote to /tmp, the old .mov stayed in
place, the script printed its success line, and the stale graphic went into the film. Only
a contact sheet caught it. **Assert that a patch applied** (`assert new in s`) rather than
trusting `str.replace`, and check the output file's mtime after any render.

**A GSAP tween scheduled past `data-duration` never runs, and the element POPS.** On 056
a beat's fade-out sat at 14.66s in a 14.64s composition - two hundredths past the end. The
render succeeded, the file was the right length, and the graphic vanished on a hard cut
instead of fading. Nothing in the build reported it; the judder scan caught it as a
5.75-motion spike that no edit point explained. **Assert that the last tween finishes
inside the duration** rather than trusting the numbers to line up, especially after
retiming a composition:

    assert EXIT + FADE < DUR, f"exit runs past the end: {EXIT+FADE} vs {DUR}"

The matching trap is the overlay's own `enable='between(t,AT,AT+N)'` in the assembly: if N
is shorter than the composition, the fade is cut off the same way even when the tween is
correct. Keep the two in sync.

**Never slice CSS by `s.index(start)` to `s.index("</style>")`.** Removing one rule that
way takes every rule after it. On 056 that silently deleted the card styling from a
composition whose text beats were being rewritten - the build succeeded, the render
succeeded, and the cards came out as bare icons stacked in the top-left corner. Nothing
downstream can tell you; only a contact sheet of that beat can. Match the single rule with
a non-greedy regex and assert the rest survived:

    s = re.sub(r'#dsmark\{\{.*?\}\}\n', '', s, flags=re.S)
    assert '.hc{{' in s, "card CSS was collateral damage"

The general form: when a patch DELETES, assert what must REMAIN, not just what must go.

## zsh

**`set -- $xy` does not word-split unquoted in zsh.** Three crop tests all silently ran
with the same bad arguments; the giveaway was output files named `crop_510 90_.png`.

**A glob with no matches aborts the command.** `rm -f tpl_*.png` with nothing to match
errors out and kills the rest of an `&&` chain.

## Reporting

**Verify overlays by looking at frames, not by a colour metric.** A green-channel test
once "proved" no leak when the page underneath was dark magenta — the metric could not
tell it from the teal clip it was supposed to be detecting.

**If a reported problem is not there, say so.** Tyler once reported a cough at 2:28; that
stretch is continuous clean speech with no gap over 0.7s, and a whole-film scan for
isolated bursts found nothing near it. Saying that is more useful than cutting something
to look responsive.

## Recuts

**`snap_cuts.py`'s ±0.45s window fails silently on a badly-placed marker.** It snaps to
the quietest 20ms frame inside WIN. When a hand-placed boundary sits *further* than WIN
from the intended phrase boundary, the snap still succeeds — it finds a real energy
minimum, just the wrong one, and the plan looks clean at a convincing -49dB. On the
Blotato recut one marker snapped into the gap *between* "I've" and "actually" (cold open
began on "actually helped a content creator…"); another was marked 2.2s late and landed
mid-phrase inside "subscribers". Fix: dump a 20ms dB profile of the region and pick the
gap by eye. Widening WIN is not the fix — it just finds a different wrong minimum.

**Verify seams by transcribing the RENDERED OUTPUT, not the plan and not the source.**
Whisper word timings are useless for *placing* edges, but Whisper on the finished cut is
an excellent seam detector: a broken join shows up immediately as a sentence fragment.
Transcribe 10s centred on every structural seam before shipping.

**Frame-align every boundary to 1/30s after snapping.** Snapped points land on 20ms
audio frames, which do not divide into 33.3ms video frames; ffmpeg then reports
`dup=N drop=N` and the output frame count drifts from the plan.

**A content recut is not a silence pass — `verify_cuts.py` will look alarming.** It
reports every run of >-40dB audio inside a cut region as "lost speech". On a recut driven
by editor notes that number is the removed *content* (243.7s on Blotato) and is expected.
Read it for cuts landing outside the intended windows, not for the total.
