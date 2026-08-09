---
name: skool-post
description: Draft a ready-to-paste Skool community post from a YouTube video package, a topic, or a rough idea. Produces a title + body in Skool's plain style, with an optional discussion CTA. Skool has no public posting API, so this generates the post for you to paste (or hand to Claude-in-Chrome). Triggers on - skool post, post to skool, skool community post, write a skool post, community post, draft a skool post, skool update.
argument-hint: [~/content/youtube/<slug>/ or a topic or a rough idea]
allowed-tools: Read, Write, Glob, Grep, WebSearch, AskUserQuestion
user-invocable: true
---

Draft a Skool community post from $ARGUMENTS.

## What this does

Turns a video, topic, or rough idea into one clean Skool post: a scroll-stopping **title** and a short, plain-text **body** that reads like a real person, ending in a question that invites replies. Skool has no official posting API, so the output is a ready-to-paste draft (you post it, or pass it to Claude-in-Chrome).

## Step 1: Detect the source

Parse $ARGUMENTS:
- **YouTube package** — a path like `~/content/youtube/<slug>/` or a slug. Read `script.md`, `description.md`, `hooks.md`, `titles.md` if present.
- **Topic / URL** — run 1-2 `WebSearch` queries for fresh, specific detail.
- **Rough idea / raw text** — use it as-is.

If empty or ambiguous, ask what the post should be about.

## Step 2: Pick the post type

If not obvious from the request, ask (AskUserQuestion) which type:
- **Value post** — teach one useful thing, then ask a question
- **Announcement** — a new video / resource is live, with the link
- **Discussion starter** — a single sharp question to drive comments
- **Win / story** — a short real story that lands a lesson

## Step 3: Write the post

**Title** (one line): specific and curiosity-driven, no hype words, no clickbait. Under ~80 chars.

**Body:**
- Plain text. No markdown headers, no bold, no em dashes.
- Short paragraphs, 1-2 sentences each, blank line between them.
- Conversational and human — write "I" and "you", not marketing voice.
- Lead with the hook, deliver one clear idea, keep it skimmable.
- If it points to a video/resource, put the link on its own line near the end.
- **End with one easy-to-answer question** (Skool rewards comments).

Follow `BRAIN/tyler-voice.md` if it exists in the user's content repo (no em dashes, no hype, honest, first person).

## Step 4: Save + present

Save to:
- YouTube mode: `~/content/youtube/<slug>/social/skool.md` (append if the file exists — do not overwrite other posts)
- Standalone mode: `~/social/YYYY-MM-DD-<slug>/skool.md`

Then show the title + body in chat so it can be copied. Offer a second variant or a shorter version.

## Rules

- **Never auto-post.** Skool has no API here; this only drafts. If asked to actually post, use Claude-in-Chrome and confirm before publishing.
- One post per run unless asked for variants.
- Keep it genuinely useful — a Skool post that only sells gets ignored.
- No em dashes, no hype words, no fake numbers.
