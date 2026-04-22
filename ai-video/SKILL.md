---
name: ai-video
description: Create animated motion graphics and AI video compositions for YouTube Shorts using Remotion. Build kinetic text, terminal typing effects, stats dashboards, line charts, VS Code interface recreations, card grids, and any custom animation. Renders as MP4 (solid bg) or WebM (transparent overlay). Triggers on: ai video, make a video, video animation, animate this, create a composition, remotion, motion graphic, kinetic text, terminal animation, text overlay, text for short, overlay text, video text, animate text, build a short animation.
argument-hint: describe the animation you want, or paste script lines
allowed-tools: Read, Write, Edit, Bash(npx:*), Bash(npm:*), Bash(open:*), Bash(ls:*), Bash(cd:*), Glob, Grep
user-invocable: true
---

Create animated motion graphics and AI video compositions for YouTube Shorts using Remotion.

## Project Location

Remotion project lives at `~/my-video/`. All compositions go in `src/`, registered in `src/Root.tsx`. Renders go to `~/my-video/out/`.

## Domain Knowledge (Rules)

Load rule files as needed for the task at hand:

- [rules/animations.md](rules/animations.md) - Fundamental animation patterns (spring, interpolate, stagger)
- [rules/timing.md](rules/timing.md) - Interpolation curves, easing, spring configs
- [rules/text-animations.md](rules/text-animations.md) - Typography and text animation patterns
- [rules/sequencing.md](rules/sequencing.md) - Delay, trim, limit duration of items
- [rules/transitions.md](rules/transitions.md) - Scene transition patterns
- [rules/charts.md](rules/charts.md) - Bar, pie, line, stock charts
- [rules/compositions.md](rules/compositions.md) - Defining compositions, default props, dynamic metadata
- [rules/assets.md](rules/assets.md) - Importing images, videos, audio, fonts
- [rules/images.md](rules/images.md) - Embedding images with the Img component
- [rules/videos.md](rules/videos.md) - Embedding videos, trimming, volume, speed, looping
- [rules/audio.md](rules/audio.md) - Audio, sound effects, volume, pitch
- [rules/audio-visualization.md](rules/audio-visualization.md) - Spectrum bars, waveforms, bass-reactive effects
- [rules/fonts.md](rules/fonts.md) - Google Fonts and local fonts
- [rules/subtitles.md](rules/subtitles.md) - Captions and subtitles
- [rules/transparent-videos.md](rules/transparent-videos.md) - Rendering with transparency (WebM/VP9)
- [rules/trimming.md](rules/trimming.md) - Cut the beginning or end of animations
- [rules/lottie.md](rules/lottie.md) - Lottie animations
- [rules/gifs.md](rules/gifs.md) - GIFs synchronized with the timeline
- [rules/light-leaks.md](rules/light-leaks.md) - Light leak overlay effects
- [rules/3d.md](rules/3d.md) - 3D content with Three.js and React Three Fiber
- [rules/maps.md](rules/maps.md) - Mapbox animated maps
- [rules/voiceover.md](rules/voiceover.md) - AI voiceover via ElevenLabs TTS
- [rules/parameters.md](rules/parameters.md) - Parametrizable compositions with Zod
- [rules/measuring-text.md](rules/measuring-text.md) - Measuring text dimensions, fitting to containers
- [rules/measuring-dom-nodes.md](rules/measuring-dom-nodes.md) - Measuring DOM element dimensions
- [rules/calculate-metadata.md](rules/calculate-metadata.md) - Dynamic composition duration and dimensions
- [rules/ffmpeg.md](rules/ffmpeg.md) - FFmpeg for trimming, silence detection, audio extraction
- [rules/tailwind.md](rules/tailwind.md) - TailwindCSS in Remotion

## Installation (first time only)

If `~/my-video/` doesn't exist:

```bash
cd ~ && npx create-video@latest my-video --template blank
cd ~/my-video && npm install
```

## Existing Compositions (Tyler's Style Reference)

| Comp ID | File | What It Shows |
|---------|------|---------------|
| S1Terminal | S1Terminal.tsx | `/yt-search claude code` types in terminal, per-char glow |
| S1SearchPrompt | S1SearchPrompt.tsx | 15 YouTube video cards cascading in, dark bg |
| S1TimeGraph | S1TimeGraph.tsx | SVG line chart: 2 hrs → 30 sec, clipPath reveal |
| S2TimeSaved | S2TimeSaved.tsx | "5 min to build → hours saved" kinetic slam |
| S2VideoStats | S2VideoStats.tsx | Single video analytics dashboard, stat cards + ring |
| S3EmailCopy | S3EmailCopy.tsx | Email being written by Claude Code, typing + transitions |
| S4VideoPlan | S4VideoPlan.tsx | "5 min to plan YouTube video" + checklist pop-in |
| S4ClaudeTerminal | S4ClaudeTerminal.tsx | `/yt` command in VS Code Claude Code interface |
| S5SkillReveal | S5SkillReveal.tsx | "What a Claude Code skill is" kinetic text reveal |
| S5TextFile | S5TextFile.tsx | SKILL.md typing in VS Code editor, syntax highlighting |
| S5PinterestSkill | S5PinterestSkill.tsx | `/pinterest-writer` executing in Claude Code terminal |
| SevenPlatforms | SevenPlatforms.tsx | Text building up + platform logos. White bg, multi-phase. |
| TerminalType | TerminalType.tsx | Fake Claude Code terminal, glowing chars, cursor blink |
| BlotaMCP | BlotaMCP.tsx | Logo + connection lines to 7 platform logos in circle |
| TwelveChars | TwelveChars.tsx | Character-by-character reveal, YouTube logo, red glow |

## Conventions

- **Always read `Root.tsx` before modifying** — never overwrite existing compositions
- **Separate compositions per graphic** — one composition per overlay/graphic
- **Naming**: `S{short#}{Description}` — e.g. `S1Terminal`, `S1TimeGraph`, `S2VideoStats`
- **Dimensions**: 1080×1920, 30fps (vertical Shorts format)
- **White background** for kinetic text, stats, checklists
- **Dark Catppuccin theme** for code/terminal animations: `#1e1e2e` bg, `#cba6f7` prompt, `#11111b` title bar
- Durations: 120-360 frames (4-12s) per composition — keep them short and punchy
- All animations driven by `useCurrentFrame()` — no CSS transitions
- Spring configs: `stiffness: 350-440, damping: 11-14, mass: 0.4-0.6` for snappy slams

## Core Animation Patterns

**Typing effect:**
```tsx
const typed = (text: string, startF: number, speed: number, f: number) =>
  text.slice(0, Math.max(0, Math.floor((f - startF) * speed)));
```

**Cursor blink after typing:**
```tsx
const cursorVis = (text: string, startF: number, speed: number, f: number) => {
  const doneAt = startF + text.length / speed;
  return f < doneAt ? true : Math.floor((f - doneAt) / 14) % 2 === 0;
};
```

**Snappy spring entrance:**
```tsx
const spr = spring({ frame, fps, config: { stiffness: 420, damping: 12, mass: 0.5 } });
const scale = interpolate(spr, [0, 1], [3, 1]);  // slams in big
const y = interpolate(spr, [0, 1], [40, 0]);     // slides up
```

**Staggered pop-in (cards, list items):**
```tsx
const STAGGER = 3; // frames between each item
const itemSpr = spring({ frame: Math.max(0, frame - index * STAGGER), fps, config: {...} });
```

**Spinner (braille):**
```tsx
const SPINNER = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"];
const spin = (f: number) => SPINNER[Math.floor(f / 3) % SPINNER.length];
```

**Count up:**
```tsx
const countUp = (to: number, startF: number, dur: number, f: number) => {
  const p = interpolate(f, [startF, startF + dur], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
    easing: (t) => 1 - Math.pow(1 - t, 3),
  });
  return Math.round(to * p);
};
```

**SVG line chart (clipPath reveal):**
```tsx
const revealWidth = interpolate(frame, [startF, startF + dur], [0, 1080], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
// <clipPath id="reveal"><rect x={0} y={0} width={revealWidth} height={1920} /></clipPath>
// Apply clipPath to path and area fill: <path clipPath="url(#reveal)" ... />
```

**Per-character glow (fresh typed chars glow then fade):**
```tsx
// Track charAge = frame - charTypedAtFrame
// interpolate(charAge, [0, GLOW_DUR], [1, 0]) → glow opacity
```

## Catppuccin Mocha Color Theme (VS Code/terminal compositions)

```tsx
const C = {
  bg: "#1e1e2e", sidebar: "#181825", titleBar: "#11111b",
  text: "#cdd6f4", muted: "#6c7086", subtle: "#45475a",
  prompt: "#cba6f7",   // purple
  green: "#a6e3a1", orange: "#fab387", blue: "#89b4fa",
  yellow: "#f9e2af", teal: "#94e2d5", red: "#f38ba8",
  pink: "#f5c2e7", border: "#313244",
};
```

## Pixel Claude Icon (for terminal compositions)

```tsx
const ClaudeIcon: React.FC = () => (
  <div style={{ width: 52, height: 52, background: "#eb6533", borderRadius: 8,
    display: "flex", alignItems: "center", justifyContent: "center",
    boxShadow: "0 2px 8px rgba(235,101,51,0.4)" }}>
    <svg width={32} height={32} viewBox="0 0 8 8">
      <rect x={1} y={2} width={2} height={2} fill="#fff" />
      <rect x={5} y={2} width={2} height={2} fill="#fff" />
      <rect x={2} y={5} width={4} height={1} fill="#fff" />
    </svg>
  </div>
);
```

## Vertical Layout Rules (1080×1920)

Everything must read on a phone. Default LARGER than you think:

- Headlines: 80-120px minimum
- Body text: 68px minimum
- Icons/logos: 80-100px minimum
- Cards: 900-960px wide (nearly full width)
- Charts: 400-500px tall, full width
- List items: ~150px height, full width
- Progress rings: 140-160px diameter
- Spacing: generous (24-40px between elements)
- Spread content across full 1920 height — don't cluster in center

## Reusable Components (in `src/components/`)

```tsx
import { WordByWord, SlamText, HighlightText, StrikeReplace, CountUp, GradientReveal, ProgressRing, PlatformLogos } from "./components";
```

## Platform Logos (SVG)

Available in `SevenPlatforms.tsx` and `BlotaMCP.tsx`: YouTubeLogo, TikTokLogo, InstagramLogo, LinkedInLogo, XLogo, SkoolLogo, ThreadsLogo.

## Static Assets

Place in `~/my-video/public/`, reference with `staticFile("filename.png")`. Existing: `blotato.png`.

## Workflow

### Step 1: Understand the Request

Parse the animation concept. Common types:
- **Kinetic text** — words/phrases slamming in (SlamText pattern)
- **Terminal typing** — VS Code Claude Code interface with command execution
- **Stats/data** — count-up numbers, bars, rings, line charts
- **Card grids** — staggered pop-ins of cards/items
- **Custom** — anything else

### Step 2: Create the Composition

1. Read `~/my-video/src/Root.tsx` first (always)
2. Create `~/my-video/src/<ComponentName>.tsx`
3. Register in `Root.tsx` with `width={1080}` `height={1920}` `fps={30}`

### Step 3: Preview (optional)

```bash
cd ~/my-video && npm run dev
```

Opens Remotion Studio at localhost:3000.

### Step 4: Render

**MP4 (solid background):**
```bash
cd ~/my-video && npx remotion render src/index.ts <CompositionId> out/<name>.mp4
```

**WebM (transparent overlay):**
```bash
cd ~/my-video && npx remotion render src/index.ts <CompositionId> out/<name>.webm --codec vp9
```

**GIF:**
```bash
cd ~/my-video && npx remotion render src/index.ts <CompositionId> out/<name>.gif --codec gif
```

### Step 5: Deliver

Tell the user the output path and open with: `open ~/my-video/out/<name>.mp4`

## Key Rules

- Always read `Root.tsx` before modifying — never overwrite existing compositions
- Each composition gets its own file
- All animations frame-driven via `useCurrentFrame()` — never CSS transitions
- Keep animations snappy — shorts move fast
- White bg for kinetic text/stats; dark Catppuccin for code/terminal
- Default font: `fontFamily: "sans-serif"`, `fontWeight: 900` for impact
- Accent colors: purple (#7c3aed / #cba6f7), blue (#89b4fa), green (#a6e3a1), orange (#fab387)
