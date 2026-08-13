# The slide format

Two layouts live in this skill. Which one you get is decided by the **data**,
not by `type`:

- A slide carrying any of `lines`, `table`, `quad`, `proof`, `note`, `closer`,
  `pill`, `rows` or `hero_path` gets the **rich layout** documented here.
- Anything else falls through to the original headline-and-bullets renderer, so
  every carousel written before this still renders exactly as it did.

The rich layout is modelled on the carousel styles in
`~/content/BRAIN/instagram/carousel-styles.md`, with reference slides in
`~/social-studio/themes/references/`. Read those before authoring - they
explain *why* the bands are what they are, which this file does not.

## Colours

Come from `~/social-studio/themes/<id>.json`. Pick with `THEME=electric`
(default), `THEME=cream`, etc. Never hardcode a colour in slide data.

Dark surfaces automatically use `ACCENT_DARK`, the accent lifted toward white,
because an accent chosen against a near-white ground goes muddy on a terminal.

## Deck-level keys

```json
{
  "handle": "@tylerreedai",
  "topic_short": "FIRST SKILL",
  "kicker": "THE 2-MINUTE BUILD",
  "steps": ["FOLDER", "FILE", "SAVE", "RUN"],
  "slides": [ ... ]
}
```

| Key | What it does |
|---|---|
| `handle` | Bottom-left of the footer rail. Use the account it actually posts to. |
| `topic_short` | Top rail, after the counter pill. Keep it to two words. |
| `kicker` | Top rail, after the topic. **Dropped automatically** if the rail runs out of room. |
| `steps` | The sequence in the footer rail. The live one is accented per slide. |

## Cover slide

```json
{
  "type": "cover",
  "kicker": "THE 2-MINUTE BUILD",
  "headline_lines": ["Build your", "first skill"],
  "accent_lines": ["first skill"],
  "headline_size": 112,
  "aside": "no code, and it runs forever →",
  "rows": [{"label": "Folder", "sub": "where it lives", "glyph": "folder"}],
  "hero_path": "assets/hero-skillmd.png",
  "terminal": {"title": "skill · live", "lines": [["> claude", "txt"], ["> RUNS FOREVER_", "accent"]]},
  "live_step": 0
}
```

Centred, ALL CAPS, tracked tight, with a rule under the accent line. Two lines
plus a kicker beats three lines - move the third into the kicker.

`accent_lines` matches **whole lines**. `accent_words` still works on the old
layout but does nothing here.

A trailing `→` in `aside` is drawn as a vector arrow. Do not rely on the glyph:
the handwriting face has no arrow and renders it as tofu.

## Body slide

```json
{
  "headline_lines": ["What", "a skill is."],
  "accent_lines": ["a skill is."],
  "note": ["One folder.", "One file.", "Zero code."],
  "lines": [
    {"glyph": "doc", "segments": [
      ["SKILL.md", "bold"], [" is the ", "plain"], ["file", "underline"]]}
  ],
  "quad": [{"glyph": "folder", "label": "Make"}],
  "live_step": 1
}
```

Left-aligned headline, no rule. The note goes top-right.

**`note`** is either a list of strings (plain sticky note, last line accented)
or an object for the ticked variant:

```json
"note": {"title": "The advantage", "items": ["No app to install", "No code to write"]}
```

**`segments`** are `[text, style]` with style one of:

| Style | Renders as |
|---|---|
| `plain` | body text |
| `bold` | bold |
| `underline` | accent rule beneath the words |
| `mark` | white text in an accent block, padded both sides |

This is the whole point of the body slide: `SKILL.md is the file` needs the
filename bold and the role underlined, which a label-plus-subtitle row cannot
express.

## Table slide

```json
"table": {
  "header": ["Step", "What you do"],
  "rows": [{"glyph": "folder", "name": "Make",
            "segments": [["A folder in ", "plain"], ["~/.claude/skills", "bold"]]}]
}
```

Use a table, not `lines`, when the second column does different work from the
first - one names the piece, the other says what it is for.

## Proof, closer, pill

```json
"proof":  {"title": "skool-post · run", "lines": [["> claude", "txt"], ["> DONE_", "accent"]]},
"closer": "start with the one you did twice",
"pill":   "Do this now"
```

`proof` is a wide terminal above the footer. Terminal lines are plain strings
(last one accented) or `[text, role]` with role in `key` / `val` / `dim` /
`accent` / `txt`. Colour the keys and not their values, or it reads as a wall
of blue rather than as a file.

`closer` and `pill` sit **just under the content above them**, not pinned to
the footer.

## Glyphs

`claude` `obsidian` `folder` `doc` `tag` `text` `wave` `grid` `terminal`
`clock` `check`

`claude` and `obsidian` draw in their real brand colours, not the theme accent.
A blue-tinted brand mark reads as wrong rather than as themed.

## Spacing rules the renderer enforces

You do not position anything vertically. It works these out:

- Rows spread across the space left, clamped to a 78-102px pitch, and the block
  **centres in its slack** rather than stretching the gaps.
- Rows reserve room for whatever is actually below them - quad card, proof
  terminal, or closer row.
- The proof terminal drops lines **from the middle** when short of space, never
  the last one, because the last line is the payoff.
- The top rail drops the kicker rather than overflowing into `swipe →`.
- The footer drops the step sequence rather than overprinting the handle.

## Rendering

```bash
THEME=electric python3 instagram_writer.py slides.json out/
```

Writes `slide_01.png`... plus `carousel.pdf`. `DISPLAY_FACE` switches the
headline face: `sfpro` (default), `condensed`, `helvetica`, `avenir`, `arial`.

**Always look at the output.** Every layout bug in this file's history - a rail
running off-canvas, arrows as tofu, a rule struck through the headline, a
terminal that deleted its own payoff line, a slide silently falling back to the
old renderer - looked correct in the code and was obvious in the image.
