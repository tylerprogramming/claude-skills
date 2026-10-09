# Red Pop

Heavy outlined caps, **one line always**; the spoken word turns red and pops.

Built for split-screen talking-head reels (screen above, camera below) where captions
need to sit tight under the seam and never wrap into the subject's face.

![style](https://static.heygen.ai/hyperframes-oss/docs/images/catalog/components/caption-highlight.png)

```bash
hyperframes add caption-red-pop
```

## Config

All knobs sit at the top of the script block.

| Name            | Default   | What it does                                                                                                                          |
| --------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `CAPTION_SCALE` | `1.5`     | `1` fits ~4 words per line at 1080 wide. Larger keeps the one-line rule by packing **fewer** words per card — `1.5` ≈ 3–4, `2` ≈ 2–3. |
| `ANCHOR`        | `"seam"`  | `"seam"` puts the top edge at `H*ANCHOR_AT + ANCHOR_OFFSET`; `"bottom"` is a classic lower-third.                                     |
| `ANCHOR_AT`     | `0.5`     | Where the seam is, as a fraction of height.                                                                                           |
| `ANCHOR_OFFSET` | `30`      | Clearance below the seam, in px. Enough to clear a 10px divider bar plus the text stroke.                                             |
| `ACTIVE_COLOR`  | `#ff1a1a` | Colour of the word being spoken.                                                                                                      |
| `POP_SCALE`     | `1.07`    | How far the active word grows. `back.out(1.8)` adds a little overshoot.                                                               |

## How it differs from `caption-highlight`

`caption-highlight` sweeps a red **background pill** behind the active word and wraps to
as many lines as it needs. Red Pop recolours the **word itself**, and guarantees a single
line by choosing group size from measured width.

Three behaviours worth knowing, each fixing something that bit us in production:

**One line, never two.** Grouping measures each candidate card's real DOM width at the
target font size and breaks before it would overflow, so words-per-card falls out of the
geometry instead of being a fixed count. One uniform size is used for every card in the
video — sizing per-card makes the type jump between ~55px and ~90px.

> Don't size with canvas `measureText`: it silently falls back to a wider system font when
> the webfont isn't registered in the canvas context. And if you probe a `.hl-group`
> directly you'll measure the _container_ (it's `width:100%` with padding) — shrink-wrap
> the probe with `width: max-content`.

**No dangling card ends.** A card ending on "…IT'S JUST **A**" reads as a sentence break
that isn't there. Trailing conjunctions, articles and prepositions carry to the next card.
Words with terminal punctuation are exempt — "MACHINE YOU'RE **ON.**" really is a sentence
end. The carry stops with two words left behind; going further strands one-word cards,
which reads worse than the danglers it fixes.

**No inter-card flicker.** Cards hold until the next one starts. The upstream
`nextStart - 0.05` blanks the screen for 1.5 frames between _every_ card — 107 gaps and
5.4s of dropout on a 2-minute clip. There's no fade-out for the same reason: it dips to
transparent exactly as the next card ramps in.

## Rendering

Alpha output requires **`--format mov`** (ProRes 4444, `yuva444p12le`). `--format webm`
silently encodes `yuv420p` with no alpha, which composites as an opaque black frame.
`--resolution` is rejected for alpha formats, so set the size in the composition.

The compiler reads the **static** `data-width` / `data-height` / `data-duration` on the
root before the script runs — the runtime overrides them from `caption-data.json`, but by
then the render is already framed. Set them to your clip first.

```bash
hyperframes render --format mov -o captions.mov
ffmpeg -i clip.mp4 -i captions.mov \
  -filter_complex "[0:v][1:v]overlay=0:0:format=auto:shortest=1[v]" \
  -map "[v]" -map 0:a -c:a copy -crf 18 out.mp4
```

## Input

Standard caption-data contract — `{ version, resolution, segments: [{ words: [{text, start, end}] }] }`,
same as every other caption component. `hyperframes transcribe <video> --json` produces it.
