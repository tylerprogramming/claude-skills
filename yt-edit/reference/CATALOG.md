# HyperFrames registry — all 383, named with what each is for

Repo lives at **`~/dev/hyperframes-studio`** (moved from `~/hyperframes-studio`; if
`hyperframes` is not on PATH the bun global link is stale — repoint
`~/.bun/install/global/node_modules/@hyperframes/cli`).

## Published vs local — only 3 items are at risk

The published npm registry has **381** items; Tyler's fork has **383**. Diffed
2026-08-31, the fork-only items are:

| local-only | published replacement |
|---|---|
| `roadmap-cards` | `grid-card-assemble` (cards assembling), `split-tilt-cards`, `three-orbiting-cards`, or `onboarding-stepper-flow` for numbered steps |
| `caption-red-pop` | `caption-highlight`, `inline-highlight`, or `marker-highlight` |
| `decision-tree` | `flowchart` / `flowchart-vertical` |

**All three are vendored into `reference/vendored/`**, so they survive a fork reset — copy
from there rather than re-deriving them. Everything else in this file installs normally.

`npx hyperframes@latest add <name>` reads the **published** registry, so it will fail on
those three. For anything else it works. To install a fork-only item, copy the directory
from `~/dev/hyperframes-studio/registry/{blocks,components,examples}/<name>/`.

219 components · 155 blocks · 9 examples. Re-list any time:
```bash
python3 -c "import json;print('\n'.join(sorted(i['name'] for i in json.load(open('$HOME/dev/hyperframes-studio/registry/registry.json'))['items'])))"
```
Compare against published:
```bash
npx hyperframes@latest add __nope__ --dir /tmp/x 2>&1 | tr ',' '\n' | sed 's/^ *//' | grep -E '^[a-z0-9-]+$' | sort -u
```
Install: `npx hyperframes@latest add <name> --dir overlays/build/<short>`

---
## AI / chat / agent — the most on-brand section for this channel

- `claude-exchange` — a styled Claude conversation, prompt and response. **The single most useful block we own and have never used.**
- `chatgpt-exchange` — same for ChatGPT, for comparisons
- `ai-chat-reveal` — a chat answer revealing progressively, like streaming
- `streaming-text` — token-by-token text arrival, the "model is thinking" look
- `typing-indicator` — the three-dot pending bubble
- `typed-prompt` — a prompt being typed into an input
- `chat-message` / `chat-thread` — single bubble / full thread
- `message-thread-reveal` / `thread-message-stack` — a conversation stacking up
- `notes-typing` / `notes-reveal` — a document writing itself

## Terminal / code (35)

- `terminal-simulator` — a live terminal you script; **use instead of hand-building a fake terminal**
- `code-terminal-run` — a command running with output appearing
- `code-typing` — code typing itself in
- `code-scroll` — scroll a long file, land on one target line (used on 047)
- `code-diff` — before/after with additions and deletions
- `code-highlight` — spotlight specific lines in a block
- `code-morph` — one code state morphing into another
- `code-3d-extrude` · `code-particle-assemble` · `code-shader-dissolve` — showy code entrances
- `code-snippet-*` (24 themes) — static frames: the whole Apple Terminal set (`basic`, `pro`, `ocean`, `grass`, `homebrew`, `novel`, `man-page`, `red-sands`, `silver-aerogel`, `clear-dark`, `clear-light`, `solid-colors`) plus editor themes (`dark-plus`, `visual-studio-dark/light`, `monokai`, `solarized-light`, `high-contrast`, `light/dark-modern`, `light/dark-2026`)
- `vscode-theme-visualizer` — theme showcase

## Captions / kinetic text (30+)

- `caption-editorial-emphasis` — word-by-word with emphasis (used on 045)
- `caption-red-pop` / `caption-highlight` — **colour-coded emphasis; this is Nate's signature caption move**
- `caption-kinetic-slam` — words slam in hard
- `caption-neon-glow` / `caption-neon-accent` — glowing treatment
- `caption-gradient-fill` / `caption-texture` — filled type
- `caption-matrix-decode` / `matrix-decode` / `scramble-reveal` — characters resolving from noise
- `caption-glitch-rgb` / `rgb-glitch-text` — chromatic split
- `caption-pill-karaoke` — pill-backed karaoke highlight
- `caption-particle-burst` · `caption-parallax-layers` · `caption-weight-shift` · `caption-clip-wipe` · `caption-blend-difference` · `caption-emoji-pop` · `caption-camera-follow`
- `bottom-up-letters` / `top-down-letters` — letters rise / drop in (our house move)
- `per-word-rise` / `per-word-crossfade` / `text-stagger` / `line-by-line-slide` — staggered text arrival
- `typewriter` — classic type-on
- `headline-slam` / `char-slam-explode` — big impact titles
- `morph-text` / `kinetic-type-swap` / `text-state-swap` / `line-swap` — one phrase becoming another
- `strikethrough-replace` — **strike a word and replace it; exactly the wrong-way/right-way move**
- `inline-highlight` / `marker-highlight` / `text-shimmer` / `tracking-in` / `variable-font-flex` / `variable-axis-type` / `stitched-text-draw` / `texture-mask-text` / `particle-text-dissolve`

## Titles, lower-thirds, branding (20)

- `lt-side-rule` · `lt-soft-pill` · `lt-clean-bar` · `lt-bold-block` · `lt-color-block` · `lt-dark-card` · `lt-neon-border` · `lt-accent-underline` · `lt-kicker-name` · `lt-mask-reveal` · `lt-stack-bars` · `lower-third-bild` — **12 lower-third styles, pick by tone**
- `yt-lower-third` — YouTube-flavoured lower third
- `yt-logo-intro` / `logo-sting` / `logo-brand-close` / `logo-outro` — channel stings
- `yt-prism-title` / `titlecard-lockup` / `titlecard-calm` / `wordmark-tiles` — title cards
- `logo-wall` — **grid of brand marks; the "works with all these apps" shot**
- `cta-lockup` / `cta-close` / `store-badge-lockup` / `trust-strip`

## Diagrams, structure, roadmap

- `constellation-hub` — **hub with satellites; the "one gateway, many apps" diagram**
- `flowchart` / `flowchart-vertical` / `decision-tree` — process flow
- `hw-pipeline` — hand-drawn pipeline
- `roadmap-cards` — **numbered agenda cards; the "in this video" teaser**
- `onboarding-stepper-flow` — numbered steps
- `three-orbiting-cards` / `grid-card-assemble` / `split-tilt-cards` / `spring-stack-shuffle` / `dynamic-grid` / `stagger-lattice`
- `comparison-split` / `before-after-wipe` / `grade-split-reveal` — **A vs B; the old-way/new-way shot**
- `tracing-beam` / `arc-motion-path` / `offset-path-traveler` / `svg-line-draw-loader` / `svg-stroke-trace` / `outline-draw` — self-drawing lines

## Numbers, data, HUD

- `count-up` / `number-wheel` / `slot-machine-roll` / `apple-money-count` — **rolling counters; Nate's kit #6**
- `telemetry-hud` — **a live stats HUD; what we hand-built on 047**
- `animated-bar-chart` / `bar-chart-race` / `data-chart` / `mk-line-graph` / `nyt-graph` / `chart-story` / `decline-chart` / `cut-the-curve` — **charts; Nate's kit #7**
- `mk-progress-stat` / `conic-progress-ring` / `star-rating-fill` / `badge-pop` / `number-pop-in` / `success-check` / `mk-specs-list` / `marker-checklist-card`
- `split-flap-board` / `news-ticker` / `ticker-takeover` — departure-board and ticker looks

## Social proof / receipts

- `x-post` / `reddit-post` / `yt-comment-card` — **real-looking posts; Nate's receipt move without needing screenshots**
- `testimonial-card` / `testimonial-proof-card` / `social-proof-card` / `avatar-cloud` / `avatar-group-hover`
- `instagram-follow` / `tiktok-follow` / `x-follow-card` / `spotify-card` — follow prompts
- `slack-notification-ad` / `macos-notification` / `native-notification-pop` / `notification-cascade` / `notification-pileup` / `notification-stack` / `liquid-glass-notification`

## Device / UI mockups

- `browser-device-stage` / `device-frame-stage` / `vfx-iphone-device` / `multi-device-splay` / `parallax-device-dive`
- `app-showcase` / `product-promo` / `screen-flow-carousel` / `share-sheet-carousel` / `sticky-mock-swap`
- `simulated-cursor` / `oversized-cursor` / `cursor-glyph-trail` / `yt-circle-pointer` / `gesture-tap` / `touch-indicator` / `press-ripple` / `multiplayer-cursors` — **pointer emphasis for screen-shares**
- `ui-focus-zoom` / `ui-3d-reveal` / `modal-morph` / `menu-morph` / `panel-reveal` / `sheet-spring-up` / `tabs-slide-indicator` / `settings-toggle-flow` / `toggle-flip` / `signup-flow` / `input-feedback` / `pull-to-refresh` / `skeleton-reveal` / `scroll-feed` / `swipe-rail`

## Camera moves and transitions

- `push-in` / `pull-back-reveal` / `cinematic-zoom` / `parallax-zoom` / `parallax-unzoom` / `camera-dolly-zoom` / `yt-camera-move` — **worth testing as jitter-free alternatives to ffmpeg `zoompan` on synthetic scenes**
- `rack-focus` / `focus-rack` / `focus-swap` / `focus-blur-resolve` / `blur-in` / `soft-blur-in` / `blur-out-up`
- `whip-pan` / `whip-pan-cut` / `match-cut` / `type-match-cut` / `beat-freeze-cut` / `zoom-through-transition` / `fade-through` / `directional-wipe` / `iris-reveal` / `svg-mask-reveal` / `slit-scan-reveal`
- `transitions-3d` · `-blur` · `-cover` · `-destruction` · `-dissolve` · `-distortion` · `-grid` · `-light` · `-mechanical` · `-push` · `-radial` · `-scale` · `-other` — **each is a family, not one effect**
- `flash-through-white` / `editorial-flash-overlay` — cut covers
- `cross-warp-morph` / `domain-warp-dissolve` / `halftone-dissolve` / `grid-pixelate-wipe` / `chromatic-aberration-wipe` / `mk-clone-wall-transition` / `hw-scribble-transition`
- `camera-shake` / `motion-blur` / `velocity-throw-snap` / `rubber-band-bumper` / `physical-exit` / `spring-pop` / `stagger-cascade` / `staggered-fade-up` / `drift-hold` / `echo-trail`

## Backgrounds, texture, VFX

- `mesh-gradient-bg` / `aurora-drift` / `vfx-liquid-background` / `mk-background` / `yt-lcd-background` / `cosmic-orb` / `spiral-galaxy` — **animated grounds; better than a flat plate**
- `grain-overlay` / `grain-field` / `warm-grain` / `vignette` / `light-leak` / `organic-light-leak-overlay` / `vfx-anamorphic-flare` / `gloss-sweep` / `light-sweep-pass` / `shimmer-sweep` / `scan-band`
- `ios26-liquid-glass` / `vfx-liquid-glass` / `liquid-glass-widgets` / `liquid-glass-media-controls` / `liquid-glass-context-menu` / `macos-tahoe-liquid-glass` — **the glass-card look, close to Nate's cards**
- `vfx-portal` / `vfx-shatter` / `vfx-magnetic` / `gravitational-lens` / `swirl-vortex` / `ripple-waves` / `thermal-distortion` / `ridged-burn` / `sdf-iris` / `segmentation-flood` / `facet-morph` / `weight-wave` / `oscilloscope-trace` / `halftone-field` / `ascii-render-pass` / `ascii-trail-reveal` / `ordered-dither-pass` / `particle-image-reveal` / `confetti`

## Hand-drawn / annotation

- `hw-arrow` / `hw-underline` / `hw-callout-circle` / `hw-box-label` / `hw-title` / `hw-frame` / `hw-text-cloud` / `hw-path-text` / `hw-boil` / `whiteboard-ink` / `vox-annotate` / `mk-callout-highlight` / `yt-feather-highlight` / `ink-bleed-reveal` — **marker-style callouts over a screen-share**

## Maps

- `world-map` / `us-map` / `us-map-bubble` / `us-map-flow` / `us-map-hex` / `spain-map`

## Misc / examples

- `beat-timeline` / `beat-pulse-background` / `beat-accent` / `icon-morph-beat` / `stop-motion-cadence` — beat-synced motion
- `keyframe-scrub-stack` / `camera-rig-depth-stack` / `camera-scan-gate` / `vector-editor-rig` / `scroll-camera-story` / `pan-stations` / `gallery-tunnel` / `perspective-marquee` / `locked-nucleus-orbit` / `radial-surround` / `overwhelm-surround` / `soft-blob-touch` / `spotlight-card` / `tilt-card` / `card-resize` / `separator` / `shared-axis-y` / `shared-axis-z` / `micro-transitions` / `freeze-frame-dressing` / `camcorder-hud` / `yt-screen-warp` / `yt-vertical-fill` / `mk-emphasis-type` / `mk-usage-arc` / `mk-placeholder-grid` / `heygen-avatar-promo-card` / `blue-sweater-intro-video` / `vpn-youtube-spot` / `north-korea-locked-down` / `nyc-paris-flight` / `swiss-grid` / `vignelli` / `play-mode` / `kinetic-type`

---

## Used so far — 7 of 383

`bottom-up-letters` · `number-pop-in` · `caption-editorial-emphasis` · `code-scroll` ·
`lt-side-rule` · `editorial-flash-overlay` · `mk-clone-wall-transition`

**Grep this file before hand-building anything.** On 047 we hand-built a HUD
(`telemetry-hud`), a card grid (`roadmap-cards`), a hub diagram (`constellation-hub`) and
a terminal (`terminal-simulator`) that all already existed.
