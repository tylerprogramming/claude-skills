# Creatives for LinkedIn

## Use `/instagram-writer`'s renderer. Do not build your own.

The house system is `~/.claude/skills/instagram-writer/instagram_writer.py`, driven by a
`slides.json` deck. It renders the slides **and the PDF** in one pass.

```bash
cd ~/.claude/skills/instagram-writer
THEME=electric python3 instagram_writer.py <deck>/slides.json <deck>/out/
# -> out/slide_01.png ... out/carousel.pdf
```

**Reference decks** (read these before writing a new one):

- `~/content/platform/instagram/arcade-mcp-gateway/` - electric palette, copper structure,
  per-brand accent via `brand_colors`
- `~/content/platform/instagram/first-claude-skill/` - the plain six-slide arc

**Format spec:** `~/.claude/skills/instagram-writer/SLIDES.md`
**Structure notes:** `~/social-studio/themes/references/copper/STRUCTURE.md`

## Palette

`THEME=electric` is the default and the current look: near-white ground with a faint dot grid,
near-black ink, one blue accent `#2454F0` used only to mark what matters. Themes live in
`~/social-studio/themes/`. **Never hardcode a colour in slide data.** A deck can override the
accent with `brand_colors` when it is about a specific product (the Arcade deck renders magenta
`#C018B4` from the Arcade brand).

## Deck shape

Deck keys: `topic`, `handle`, `brand_text`, `brand_path`, `topic_short`, `kicker`, `steps`, `slides`.
**`brand_text` is required** and the renderer raises `KeyError` without it.

Slide types: `cover`, `pain`, `solution`, `how`, `results`, `cta`. `live_step` indexes into `steps`
to light up the footer rail.

Component vocabulary: `rows` (icon rows), `terminal` / `proof`, `lines` with styled `segments`
(`plain` / `bold` / `underline` / `mark`), `table`, `quad`, `note` (plain or ticked), `pill`,
`closer`, `aside` (handwritten, trailing `→` drawn as a vector), `hero_path`.

Glyphs: `claude obsidian folder doc tag text wave grid terminal clock check`. `claude` and
`obsidian` draw in their real brand colours, not the accent.

## Landscape diagrams

This renderer is 4:5 only. The build-post system diagram is 1200x760 and still uses
`../render.py` (HTML to headless Chrome). **Its palette is currently the old dark look and is now
off-brand** - retarget it to electric, or drop landscape and make build-post images 4:5 decks.

## Diagram doctrine

Show the SYSTEM, not a chapter list. Inputs, the mechanism, outputs, plus when it runs. No timestamps.
**Read the package `script.md` and the real chapter list first**, never the social copy already
written about the video.

## Gotchas

- zsh arrays are **1-indexed**; `for i in 0 1 2 3 4 5` silently drops the last item. Use Python
  for upload and verify loops.
- **Blotato re-hosts images** under its own ids. Verify by md5 against the local file.
- Sampling a look from screenshots gets it wrong. Read the deck JSON and the theme file.
