---
name: carousel-app
description: Launch the visual Instagram carousel maker app. Opens the local web app for creating, editing, and exporting branded Instagram carousels with AI-generated background images. Triggers on: open carousel app, launch carousel maker, carousel maker, visual carousel, instagram carousel app, open carousel, start carousel app.
argument-hint: "[optional: nothing needed]"
allowed-tools: Bash(bun:*), Bash(lsof:*), Bash(open:*), Bash(pkill:*), Bash(sleep:*)
user-invocable: true
---

# Visual Instagram Carousel Maker

Launch the visual carousel maker app at `~/carousel-maker/`. This is a React + Hono app for creating branded Instagram carousels with AI-generated background images, multiple slide types, and PDF/PNG export.

## How to Use

### Step 1: Check if already running

```bash
lsof -ti:5175 | head -1
```

If a process is already listening on port 5175, the app is running — skip to Step 3.

### Step 2: Start the dev server

```bash
cd ~/carousel-maker && bun run dev &
```

Wait 3 seconds for the server to boot:

```bash
sleep 3
```

Verify it's up:

```bash
lsof -ti:5175 | head -1
```

If still nothing after 5 more seconds, check for errors:

```bash
lsof -ti:3010 | head -1
```

(The Hono API server runs on 3010, Vite client on 5175.)

### Step 3: Open in browser

```bash
open http://localhost:5175
```

### Step 4: Confirm to the user

Tell the user:
- The carousel maker is open at `http://localhost:5175`
- They can pick a framework (Educational, Hormozi, Quick Wins, Storytelling, Instagram Writer)
- Generate AI background images per slide via the Background Image panel
- Export all slides as PNG or a combined PDF
- Carousels are auto-saved and can be reloaded from the drawer

## What the App Does

- **Frameworks**: Pre-built slide structures for different content styles
- **AI Backgrounds**: Kie.ai image generation per slide or for all slides at once
- **Image Library**: Previously generated backgrounds are saved and reusable
- **Text Scale**: Per-slide font size control (XS → XL + fine slider)
- **Export**: Download individual PNGs or a multi-page PDF
- **Save/Load**: Carousels saved as JSON to `~/carousel-maker/carousels/`, reload from the Library drawer

## Stopping the Server

If the user wants to stop the app:

```bash
pkill -f "bun run dev" 2>/dev/null; lsof -ti:5175 | xargs kill -9 2>/dev/null; lsof -ti:3010 | xargs kill -9 2>/dev/null
```

## Notes

- App lives at `~/carousel-maker/`
- Output PNGs go to `~/carousel-maker/output/`
- Background images saved as `bg_*.png` in that same folder
- Requires `KIE_API_KEY` in `~/.claude/.env` for background image generation
- Requires Supabase credentials for save/load (see `~/carousel-maker/README.md`)

## Carousel Storage (Two Locations)

When creating carousel content, always save to **both** locations:

### 1. App Library — `~/carousel-maker/carousels/<id>.json`

This is what the carousel maker app reads. JSON format with the carousel's slides, colors, and text:

```json
{
  "id": "carousel_<timestamp>",
  "title": "Carousel Title",
  "platform": "instagram",
  "slides": [
    {
      "id": "slide_0_<timestamp>",
      "type": "cover",
      "slideNumber": 1,
      "headline": "Main Headline",
      "emphasisLine": "Accent line in terra cotta",
      "bodyText": "Supporting text.",
      "bgColor": "#F5F0EB",
      "textColor": "#1B1B1B",
      "accentColor": "#E07355"
    }
  ]
}
```

Slide types: `cover` (slide 1), `content` (slides 2-5, include `stepNumber`), `cta` (slide 6).

### 2. Content folder — `~/content/carousel/<slug>/`

This is where the copy, captions, and exported files live:

```
~/content/carousel/<slug>/
  content.md      # 6-slide copy (Cover/Pain/Solution/How/Results/CTA)
  captions.md     # Instagram caption (5 hashtags) + LinkedIn caption (no hashtags)
  slide_1.png     # Exported from app (after building)
  ...
  slide_7.png
  <slug>.pdf      # Combined PDF for LinkedIn
```

### Always create both at the same time

When generating carousel content, save the app JSON **and** the content folder in the same step. This keeps the Library and the content archive in sync.

### Scheduling via Blotato

- **Instagram**: upload slides 1-6 as a carousel (skip CTA slide 7)
- **LinkedIn**: upload the PDF
- **X/Twitter**: post as a 7-post thread (see below)
- Captions at `~/content/carousel/<slug>/captions.md`

## X/Twitter Thread Scheduling

Carousels perform well on X as threads: slide 1 + punchy caption as the main tweet, slides 2-6 as numbered replies, then a Skool link as the final reply.

### Structure
- **Main tweet**: slide_1.png + X-native caption (no hashtags, under 230 chars, punchy)
- **Replies 2-6**: each slide image + text `"2/6"`, `"3/6"` ... `"6/6"`
- **Final reply**: `"join us at skool.com/the-ai-agency — free templates and full community 👇"`

### Timing
- 9 PM EDT = 01:00 UTC the next calendar day
- e.g. May 6 at 9 PM EDT → `scheduledTime: "2026-05-07T01:00:00.000Z"`

### Upload pattern — use Python MCP client directly

Blotato presigned URL tokens get corrupted when passed through bash heredocs or JSON strings. Always upload via the Python MCP client:

```python
def upload_slide(session_id, carousel_id, slide_num):
    path = os.path.expanduser(f"~/content/carousel/{carousel_id}/slide_{slide_num}.png")
    r = mcp_call(session_id, "tools/call", {
        "name": "blotato_create_presigned_upload_url",
        "arguments": {"filename": f"carousel_{carousel_id}_slide{slide_num}.png"}
    })
    data = json.loads(r["result"]["content"][0]["text"])
    presigned_url = data["presignedUrl"]   # use for PUT upload
    public_url    = data["publicUrl"]      # use in post mediaUrls

    with open(path, "rb") as f:
        img_data = f.read()
    urllib.request.urlopen(
        urllib.request.Request(presigned_url, data=img_data, method="PUT",
            headers={"Content-Type": "image/png", "Content-Length": str(len(img_data))}),
        timeout=60
    )
    return slide_num, public_url
```

Upload all 6 slides in parallel with `ThreadPoolExecutor(max_workers=6)` for speed.

### Post creation
```python
post_data = {
    "accountId": "5910",   # Tyler's X account
    "platform": "twitter",
    "text": caption,       # X-native, no hashtags, under 230 chars
    "mediaUrls": [slide_urls[1]],
    "scheduledTime": "2026-05-07T01:00:00.000Z",
    "additionalPosts": [
        {"text": "2/6", "mediaUrls": [slide_urls[2]]},
        {"text": "3/6", "mediaUrls": [slide_urls[3]]},
        {"text": "4/6", "mediaUrls": [slide_urls[4]]},
        {"text": "5/6", "mediaUrls": [slide_urls[5]]},
        {"text": "6/6", "mediaUrls": [slide_urls[6]]},
        {"text": "join us at skool.com/the-ai-agency — free templates and full community 👇", "mediaUrls": []}
    ]
}
```

Reference script: `/tmp/schedule_x_carousels.py`
