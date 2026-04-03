---
name: video-text
description: Generate animated text overlays and motion graphics for YouTube Shorts using Remotion. Takes script lines, creates kinetic text, terminal typing effects, platform logo animations, and renders as transparent WebM (for overlay) or MP4. Triggers on: video text, text overlay, animate text, kinetic text, text for short, overlay text, remotion, motion graphics.
argument-hint: <script text or "lines separated by |"> or describe what you want
allowed-tools: Read, Write, Edit, Bash(npx:*), Bash(npm:*), Bash(open:*), Bash(ls:*), Bash(cd:*), Glob, Grep
user-invocable: true
---

Generate animated text overlays and motion graphics for YouTube Shorts using Remotion.

## Project Location

Remotion project lives at `~/my-video/`. All compositions go in `src/`, registered in `src/Root.tsx`.

## Installation (first time only)

If `~/my-video/` doesn't exist, set up Remotion:

```bash
cd ~ && npx create-video@latest my-video --template blank
cd ~/my-video && npm install
```

Then verify it works:
```bash
cd ~/my-video && npm run dev
```

This opens Remotion Studio at localhost:3000 where you can preview compositions.

## Existing Compositions (reference these for style)

| Composition | File | What It Does |
|-------------|------|-------------|
| SevenPlatforms | `src/SevenPlatforms.tsx` | Text lines building up + platform logos popping in + platform pills. White bg, multi-phase animation. |
| TerminalType | `src/TerminalType.tsx` | Fake Claude Code terminal with typing effect, glowing characters, cursor blink. Dark terminal theme. |
| BlotaMCP | `src/BlotaMCP.tsx` | Blotato logo center with connection lines radiating to 7 platform logos in a circle. Dark gradient bg with grid pattern. |
| TwelveChars | `src/TwelveChars.tsx` | Character-by-character text reveal with YouTube logo and subtle red glow. White bg. |

## Reusable SVG Logos Available

The following platform logo components exist in `SevenPlatforms.tsx` and `BlotaMCP.tsx` - import or copy them:
- `YouTubeLogo` (red play button)
- `TikTokLogo` (TikTok icon)
- `InstagramLogo` (gradient icon)
- `LinkedInLogo` (blue square)
- `XLogo` (black X)
- `SkoolLogo` (purple S)
- `ThreadsLogo` (black threads icon)

## Workflow

### Step 1: Understand the Request

The user may ask for:
- **Kinetic text** - Animated words/phrases popping in (like TwelveChars)
- **Terminal typing** - Fake Claude Code terminal with typing effect (like TerminalType)
- **Logo animations** - Platform logos with connections (like BlotaMCP)
- **Custom motion graphics** - Anything else

Parse the user's input into the animation concept. If unclear, ask what style they want.

### Step 2: Ask Rendering Preferences

Ask the user (but use sensible defaults if they say "just do it"):
1. **Background**: Transparent (WebM, for overlaying on footage) or solid color? Default: white for text, dark for terminal
2. **Style**: Any color/glow preferences? Default: dark navy text (#1a1f36) on white, subtle colored glow
3. **Output format**: MP4 (solid bg) or WebM (transparent overlay)? Default: MP4

### Step 3: Create the Composition

Create a new component file in `~/my-video/src/` named after the slug (e.g., `TwelveChars.tsx`).

**ALWAYS read the current `Root.tsx` before modifying it** to avoid overwriting other compositions.

### Animation Patterns (Tyler's Preferences)

**Character-by-character reveal (preferred for text hooks):**
```tsx
// Each character springs in individually, staggered 2 frames apart
const charDelay = 2;
const charSpring = spring({
  frame: frame - startFrame - i * charDelay,
  fps,
  config: { stiffness: 300, damping: 15, mass: 0.4 },
});
```

**Subtle glow (not heavy - Tyler's preference):**
```tsx
// Light glow behind text, not overpowering
const subtleGlow = (color: string): React.CSSProperties => ({
  textShadow: `0 0 8px ${color}, 0 0 16px ${color}`,
});
```

**Terminal typing with glowing characters (for code/command demos):**
```tsx
// Characters glow orange when first typed, then fade to normal
// See TerminalType.tsx for full implementation
const CHARS_PER_FRAME = 0.8;
const GLOW_DURATION = 14; // frames
```

**Spring animations (snappy, not floaty):**
```tsx
// Pop-in: high stiffness, low mass
spring({ frame, fps, config: { stiffness: 220, damping: 18, mass: 0.5 } })

// Slide up: combine spring with interpolate
const y = interpolate(springVal, [0, 1], [40, 0]);
```

**Multi-phase compositions:**
- Use frame ranges to transition between phases
- Fade out phase 1, fade in phase 2
- See SevenPlatforms.tsx for a 4-phase example

**Available Remotion imports:**
```tsx
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig, Sequence } from "remotion";
```

Register the new composition in `~/my-video/src/Root.tsx` with:
- `width={1080}` `height={1920}` (vertical shorts)
- `fps={30}`
- Appropriate `durationInFrames` (~30 frames per line + 30 frames hold at end)

### Step 4: Preview (optional)

If the user wants to preview before rendering:
```bash
cd ~/my-video && npm run dev
```
Opens Remotion Studio where they can scrub through the timeline.

### Step 5: Render

Run from `~/my-video/`:

**For solid background (MP4/H264):**
```bash
cd ~/my-video && npx remotion render src/index.ts <CompositionId> out/<filename>.mp4
```

**For transparent background (WebM/VP9):**
```bash
cd ~/my-video && npx remotion render src/index.ts <CompositionId> out/<filename>.webm --codec vp9
```

### Step 6: Deliver

Tell the user:
- Output file path and size
- Open with: `open ~/my-video/out/<filename>.mp4`
- Composition ID for tweaking in Remotion Studio

## Static Assets

Place images/logos in `~/my-video/public/` and reference with `staticFile("filename.png")`.

Existing assets:
- `blotato.png` - Blotato mascot logo

## Key Rules

- **Always read `Root.tsx` before modifying** - don't overwrite existing compositions
- Each video gets its own component file
- These are mobile-first (1080x1920) - text must be BIG (80-120px)
- Keep animations snappy - shorts move fast
- Tyler prefers subtle glow, not heavy
- Tyler prefers character-by-character reveals for text hooks
- Use platform SVG logos from existing compositions when needed
- Default font: `fontFamily: "sans-serif"`, `fontWeight: 900`
- Default colors: dark navy (#1a1f36) on white, or white on dark (#0d0e17)
- Accent colors: blue (#4da6ff), red (#FF0000 for YouTube), orange (#ff9e64), green (#22c55e)
