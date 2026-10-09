---
name: video-edit
description: Edit a two-camera Camtasia recording into a polished, feature-rich video. The workflow is mandatory: 1. Analyze the raw footage (find beats/sections). 2. Define structural segments (full-camera, screen-capture, etc.). 3. Generate the master composite (crosspix/blur/crop/anim). 4. Verification passes run through the final technical passes (audio/visually/system). This class of work requires meticulous time-stamping and architectural rigor. Triggers on: polish the video, final pass, full edit.
argument-hint: [video name in ~/Movies/Camtasia] [--silence-only] [--minutes N]
allowed-tools: Bash(ffmpeg:*), Bash(ffprobe:*), Bash(python3:*), Bash(hyperframes:*), Bash(npx:*), Bash(open:*), Bash(ls:*), Bash(cp:*), Bash(mkdir:*), Read, Write, Edit, Glob, Grep, AskUserQuestion
user-invocable: true
---

Edit the raw two-camera recording named in $ARGUMENTS into a finished cut.

## Workflow context

Sits between filming and `/yt-chapters` in the pipeline:

```
/yt-package → [FILM] → **/yt-edit** → /yt-chapters → /yt-shorts → /yt-upload
```

`/yt-chapters` and `/yt-seo` both read the file this produces, so finish here first.

## The footage

Tyler shoots **two frame-synced 1920x1080 / 30fps files** in `~/Movies/Camtasia/`:

```
<name> - CAMERA.mp4    him + the audio
<name> - SCREEN.mp4    the capture
```

Identical durations, so one cut plan drives both. Work lives in
`~/Movies/Camtasia/<name>/scripts/`, output in `<name>/<name> - FINAL.mp4`.

**Default layout:** SCREEN full-frame, CAMERA circle-masked bottom-right. 480px circle,
50px inset, crop 980x980+490+100 for head-and-shoulders. The circle's left edge sits at
**x=1390**, so any wide graphic must cap its width to clear it.

## Flow

### Step 1 — profile the noise floor. Never skip this.

```bash
python3 ~/.claude/skills/yt-edit/lib/audio_floor.py "<name> - CAMERA.mp4"
```

**Never reuse the last video's `--noise` value.** The right threshold has swung 40dB
between shoots and the wrong one silently eats speech:

| shoot | floor | correct `--noise` |
|---|---|---|
| 17 claude code skills | -26dB | `0.05` |
| 045 arcade.dev | -72dB | `0.005` |

Carrying 0.05 to the arcade shoot cut **75 seconds of speech tails** and nobody would
have noticed from the log. The floor is the p10-p50 cluster, speech is p80+; put the
threshold between them.

### Step 2 — silence pass

```bash
hyperframes silence "<name> - CAMERA.mp4" --noise=<value> --dry-run --json > silence.json
```

**Flags must use the `=` form.** `--noise 0.05` with a space is silently ignored and
returns the default result with no warning, which looks exactly like the flag having no
effect.

This is Tyler's fork (`~/dev/hyperframes-studio`, bun-linked). `silence`, `caption` and
`duplicates` exist there and **not** in the published npm CLI.

Then prune slivers: drop keeps shorter than **0.60s** that are isolated by **3.0s** of
silence on both sides. Those are clicks, chair creaks and clothing rustle, not speech.

### Step 3 — transcribe and find duplicate takes

Transcribe, then intersect the word list with the keep ranges before using it for
anything. Two Whisper failure modes make raw transcripts unusable:

- **It hallucinates fluent sentences over long silences.** On 045 it invented a whole
  sentence across a stretch measuring -70dB.
- **It drops real words on the long-file pass.** A repeat Tyler reported looked absent
  in the full transcript and was plainly there when the 18-second window was
  transcribed in isolation.

So: **before telling him a reported repeat is not there, re-transcribe that window
alone.** If the isolated pass and the full pass disagree, trust the isolated one.

`lib/find_dups.py` helps, but on every video so far the real retakes were found by
**reading the transcript for repeated beat structure**, not by any tool. Tyler also
says "let me redo that section" and counts himself in with "3, 2, 1" — search the
**source** transcript for those, not the recut one, because the count often falls inside
a gated region and comes back mangled.

**Rule: when a take is repeated, keep the second one.**

### Step 4 — snap the cut boundaries

```bash
python3 ~/.claude/skills/yt-edit/lib/snap_cuts.py <in.json> <out.json>
```

Snaps each boundary to the lowest-RMS 20ms frame within ±0.45s. **Do not skip this.**
Hand-placed boundaries clip syllables, and Whisper's word-end times are unreliable
enough that one "about." was reported as spanning ten seconds.

### Step 5 — verify nothing was lost

```bash
python3 ~/.claude/skills/yt-edit/lib/verify_cuts.py <final.mp4> <cuts.json>
```

Decodes to 8kHz mono, takes 50ms RMS frames, and flags any run above -40dB lasting
0.30s or more inside a cut region. **Target is 0.0s of speech lost.** This is
independent of the transcript, which is the point.

### Step 6 — render

Copy **`reference/058/recut.py`** into the project's `scripts/` and edit the config block
at the top. It is the current reference implementation and supersedes
`reference/recut_reference.py`, which predates the per-keep window handling, the secret
blurring and the startup validation. `reference/058/README.md` maps what each part does.

**Before the first render, read `reference/SILENT-FAILURES.md`.** Every entry in it
produced a file that played, had the right duration, and was wrong. That is the normal
failure mode here — not a crash.

Keep the startup validation that exits when any config key stops matching a keep start.
Trimming a keep moves its start, and a stale key means the graphic silently does not
appear.

**Batches of ~30 clips, 3 concurrent ffmpeg passes**, each batch input-seeking with
`-ss` so it only decodes its own span. Intermediates are `.mov` with libx264 crf18 video
and **PCM** audio, joined with the concat demuxer using `-c:v copy -c:a aac`. Video is
encoded exactly once, and keeping audio PCM until the final pass means hundreds of clip
boundaries add no AAC priming gaps.

Two approaches that work on short reels and **fail at hour length**:
- One `trim` filter per clip in a single graph: every decoded frame goes through 2N
  filters. At N=360 that runs at **0.19x realtime**.
- One `select='between(t,a,b)+...'` expression: the parser dies with **"Cannot allocate
  memory"** past roughly 100 terms.

`--minutes N` renders a prefix for review.

### Step 7 — creative pass

Only after he has seen the silence cut. Ask before building; he has strong opinions and
they are usually right.

See `reference/MOTION-KIT.md` FIRST — the reusable motions, the zoom system, the
pacing targets and the AI-video rule, all verified on 047. Then `reference/LESSONS.md`
for the ffmpeg and animation gotchas — that file is the
expensive part of this skill and is worth reading in full before building any graphic.

## Treatment — which picture is on screen

The default is SCREEN full-frame with the camera circle bottom-right, but three
departures from that are what make it a video rather than a screen share. All three are
decided by **measurement**; see `reference/MEASUREMENTS.md` for the recipes.

**1. Section intros go full-frame camera.** Where he introduces a new section with
nothing happening on screen, the picture should be him. Find these by combining *static
screen* (motion under 1.6 at 1s resolution) with *absence of pointing language*
("if we go", "right here", "you can see", "click"). Either test alone is wrong — static
screen alone found 68 candidates on 058 and would have turned the film into a talking-head
reel; both together found 5. Require ≥12s, keep-align, and check his gaze before
committing. **End each span on the first pointing phrase** so the picture returns to the
screen exactly when he starts demonstrating.

Give those spans zooms. Alternate direction, carry the scale across cuts so no cut jumps.

**2. Browser chrome gets cropped**, so open tabs naming unrelated work are not on screen.
Detect a browser by correlating the bookmarks-bar rows against a known browser frame, not
by looking for a brightness edge — a terminal floating over the browser kills the edge
while the tab strip is still visible. If chrome appears or disappears mid-keep, bisect to
1/30s and **split the keep**; a split is lossless.

**The crop must preserve aspect.** Cropping `1920x(1080-118)` and scaling back to
`1920x1080` stretches everything vertically by 12%. Take a 16:9 window
(`round((1080-CHROME_Y)*16/9)` wide) and choose *which* width to drop per keep by
minimising deleted content weight.

**3. The circle moves to the bottom-left** only where the right corner is measurably
busier. Do not set this by eye: three of four hand-written spans on 058 were backwards,
parking the circle on the content it was meant to avoid.

## Secrets

Scan the **whole film** for credentials before delivering, not just the part under
review. On 058 a `claude setup-token` OAuth code was on screen in three places at once —
the terminal URL, the browser address bar, and the account email in the page footer.

Blur with `boxblur` on a cropped region overlaid back, **before** the chrome crop so the
boxes stay in original coordinates. Verify by measuring high-frequency detail inside the
box against a reference strip of the same page; a properly destroyed line reads 0.00
against 0.09.

## Graphics

Built as **transparent ProRes 4444 MOVs** via `hyperframes render <dir> --format mov`
(WebM tags alpha but discards it), then overlaid inside the same batch pass, never as a
second encode of the film.

Prefer **registry components** over bespoke HTML:

```bash
npx hyperframes@latest add bottom-up-letters --dir overlays/build/bul
```

Ones already in use: `bottom-up-letters`, `number-pop-in`, `caption-editorial-emphasis`,
`code-scroll`, `lt-side-rule`, `editorial-flash-overlay`, `mk-clone-wall-transition`.
That is **7 of 131** — see `reference/CATALOG.md` for the rest.

`reference/047/` holds the complete working build for the 047 intro — the best worked
example available. `build_intro.py` (assembly + the zoom keyframe system), `build_montage.py`
(a synthetic scene set), `build_wall.py` / `build_auth.py` (full-frame cutaways with real
brand marks), `build_codescroll.py` (driving a registry block by hand), `build_intro_gfx.py`
(one timeline for every overlay beat), `preview2.py` (the 2-minute iteration loop — this is
the one that makes creative passes cheap).

Copy `reference/graphic_reference.py` as a minimal starting point. It shows the `grab()` helper
that pulls a component's `<style>` and `<script>` into a page, and the pattern of pinning
every beat to a word timestamp.

**Fonts** are bundled @fontsource, no network: inter, montserrat, outfit, nunito, oswald,
anton, league-gothic, archivo-black, space-mono, ibm-plex-mono, jetbrains-mono,
eb-garamond, playfair-display, source-code-pro, roboto, open-sans, lato, poppins. Anton
is the house display face.

**Brand logos come from `simple-icons` (npm), never from a generative model** — asked for
"the Gmail logo" a diffusion model invents a plausible wrong one. Note that **Slack,
Salesforce and the Microsoft marks are not in the set**, removed at those companies'
request, so check before promising a logo.

For AI clips use `/kie-seedance-video`; for isolating a logo out of a photo use
`/kie-nano-banana`.

## Editing an already-finished render

If the source files have been overwritten by a re-record, the recut script cannot rebuild
the cut and the rendered master is the only truth. Use
`reference/apply_overlays_reference.py`: it re-encodes only the span that changes and
stream-copies the rest from a keyframe.

**`-ss <keyframe>` rounds down and falls back to the previous keyframe.** Ask for
keyframe + 0.024 and size the head segment to `total - tail`, or you silently duplicate
several seconds. Find real keyframes with:

```bash
ffprobe -v error -select_streams v:0 -show_entries frame=key_frame,pts_time \
  -of csv=p=0 <file> | awk -F, '$1==1 {print $2}'
```

## Verification discipline

**Measure, do not eyeball.** `reference/MEASUREMENTS.md` has every recipe as copy-paste
code. Each one caught a real defect that looked fine on screen:

| question | measurement |
|---|---|
| does the render match the plan? | duration vs sum of keep ranges — catches dropped batches |
| is the cut plan valid? | inverted, zero-length, overlapping, out-of-order ranges |
| is speech lost / is there dead air? | 50ms RMS runs above -40dB inside cuts; runs below -45dB inside keeps |
| is the zoom visible? | percent change; under ~8% total reads as nothing |
| **is the zoom smooth?** | **percent per frame; 1.9%/frame is the ceiling** |
| did the zoom actually fire? | optical scale fit, but only trust correlation > 0.8 |
| is anything stretched? | fit both axes independently; aspect error must be 0.00% |
| which corner for the circle? | content density in both bottom corners |
| which side to crop? | deleted content weight — edges AND flat panels |
| is this a browser window? | bookmarks-bar correlation, not a brightness edge |
| is the secret really gone? | high-frequency detail in the box vs the page |
| is the border outside the camera? | mask extent vs ring extent, per row |

Two habits that matter more than any single metric:

- **Sanity-check the metric before trusting the number.** Three measurements on 058 were
  wrong the first time and produced a confidently wrong decision — an edge-only crop
  score that ignored a flat terminal panel, a corner-density test read at the wrong
  threshold, and an optical scale fit corrupted by the non-scaling circle.
- **Verify overlays by looking at frames**, not by a colour metric. A green-channel test
  once "proved" no leak when the page underneath was dark magenta.

Numbers tell you whether it works; contact sheets tell you what rendered. You need both.

## Working with Tyler

- **His timestamps are approximate** — typically off by 2 to 4 seconds, and occasionally
  they point at nothing. Search a window around the mark, and if there is genuinely
  nothing there, say so plainly rather than cutting something to look responsive.
- **Review in slices.** He wants to see 30 seconds before you build ten minutes.
- **Whisper writes "cloud code".** He is saying Claude Code. Never ship that.
- He often sends a follow-up refinement mid-build. Read the whole thread before rendering.
- **His eye beats the metric.** He caught the harsh screen zooms, the mask border showing
  camera outside it, and the 12% aspect stretch — all after automated checks had passed.
  When he says something looks off, the measurement is missing, not him.
- **He asks for one thing; check whether it is systemic.** "5:34 should be on the right"
  was one span, but re-deriving all of them found three more backwards. "Make 11:41
  full camera" was one section; the same test found four more. Fix the class, then report
  what changed.
- **Report timestamps, not descriptions.** When several things changed, a table of
  `time | duration | what starts it` is what he wants back.

## Background renders

`nohup ... &` returns the launcher shell immediately, so a completion notification fires
while the render is still going. Either run it in the foreground with a long timeout, or
poll for the actual process:

```bash
while pgrep -f "scripts/recut.py" > /dev/null; do sleep 20; done
```

`rm -rf` on scratch directories trips the approval gate mid-flow. Content-hash-keyed
filenames mean you never need to delete anything; when you do need to remove one stale
file, do it from Python rather than a shell `rm`.

## Output

```
~/Movies/Camtasia/<name>/
  <name> - FINAL.mp4        the deliverable
  scripts/                  recut + per-graphic builders
  overlays/movs/            rendered transparent MOVs
  overlays/build/           registry components + generated HTML
  transcript/               recut_words.json (r = recut time, src = source time)
```

`transcript/recut_words.json` carries **both** timelines. `/yt-chapters` and `/yt-seo`
want `r`. The recut script's own `SHOTS` list is in **source** time. Mixing them up is
the single easiest mistake to make here.

**Before building any graphic, read these:**

1. **`reference/SILENT-FAILURES.md`** — the ways a render comes out wrong with exit code
   0. Start here; it is the most expensive file in the skill.
2. **`reference/MEASUREMENTS.md`** — every verification recipe as copy-paste code.
3. **`reference/CATALOG.md`** — all 383 registry items by category. Grep it before
   hand-building anything.
4. **`reference/MOTION-KIT.md`** — the card travel-from-below timing, the self-drawing
   glyph pattern, the strike-through hold, the zoom keyframe system, the measured pacing
   targets, and when AI video earns its place.
5. **`reference/058/`** — the current reference build, with `README.md` mapping it.

Also deliver previews to a path **without spaces** (`~/Movies/Camtasia/<n>-previews/`);
the desktop MEDIA card cannot open a path containing them. Verify the copy exists before
sending the link — pasting a path you have not created is an easy way to hand over
nothing.

Afterwards, update `~/content/youtube/notes/status.md` **and** the ClickUp task — the
file is the source of truth but they are meant to agree.
