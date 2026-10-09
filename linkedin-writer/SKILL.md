---
name: linkedin-writer
description: Write LinkedIn posts that actually reach people, using the build-post formula proven on Tyler's own account (31,875 impressions vs a 109 median). Two modes - "build" (the video companion post - named stack, numbered steps, architecture image, link) and "insight" (short confession/correction text post for days between videos). Reads BRAIN/linkedin/brain.md and BRAIN/tyler-voice.md first, drafts, then scores the draft against the evidence before handing it over. Triggers on - linkedin post, write a linkedin post, li post, post for linkedin, linkedin for this video, build post, linkedin writer, promote this video on linkedin.
argument-hint: [video package path | topic] [--insight]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(ls:*), Bash(cat:*), Bash(head:*), Bash(find:*)
user-invocable: true
---

# LinkedIn Writer

Writes LinkedIn posts for Tyler Reed (2,727 followers, objective: **authority first, Skool second**).

This skill exists because the account's own numbers show a 300x spread between two formats. It is not a general-purpose copywriter. It reproduces the one shape that has ever broken out on this account and refuses to ship a draft that does not carry the parts that made it work.

---

## Step 0: Read the evidence (mandatory, never skip)

Read in this order, every run:

1. `~/content/BRAIN/linkedin/brain.md` - the performance playbook. Rules carry `[confirmed YYYY-MM-DD]` stamps. Confirmed rules override your instincts about what "good LinkedIn writing" looks like.
2. `~/content/BRAIN/linkedin/creatives.md` - what visual goes next to the post, the creative quality hierarchy, and the breakdown / tactical-post formats. The brain says what to write; this says what to put beside it.
3. `~/.claude/skills/linkedin-writer/templates/README.md` - the creative templates and the rules learned
   building them (including the zsh 1-indexed array gotcha and the Blotato re-hosting behaviour).
4. `~/content/BRAIN/tyler-voice.md` - how Tyler actually talks. Governs sentence rhythm and the hard bans.
5. Background, read once if unfamiliar: `~/content/research/linkedin/2026-08-19-capitalyst-deck-teardown.md` - why several brain rules are double-sourced, and what was deliberately rejected from that material (outbound pitching, money-amount hooks, controversy hooks).

Rules stamped `[confirmed]` come from this account's own numbers. Rules stamped `[deck-sourced]` are borrowed and untested here. **Confirmed beats deck-sourced on any conflict.**

If the two ever conflict, the resolution is in the brain's post-anatomy section. Where it is genuinely unresolved, follow the brain for **structure** and the voice guide for **wording**, and say so in your handoff.

---

## Step 1: Figure out what we are posting about

**If given a video package path** (`youtube/videos/NNN-slug/`): read `script.md`, `titles.md`, and `description.md`. You are looking for the buildable spine, not the talking points:

- What system gets built, end to end, in one sentence?
- What is the ordered list of steps, and how many?
- Every named tool, product, and service it touches. Write them all down.
- What does the finished thing actually DO? Where does output land (a Doc, a Slack channel, a folder, a database)?
- What is the honest failure mode or gotcha Tyler hit? (This is the credibility line.)

**If given a topic only**: ask Tyler for the stack and the step sequence before drafting. A build post cannot be written from a topic alone. Do not invent tool names or steps. If he only wants a quick post and has no build to point at, switch to insight mode.

**If given neither**: ask which video, or offer insight mode.

---

## Step 2: Pick the mode

| Mode | When | Ceiling |
|---|---|---|
| **build** (default) | There is a video, a repo, or a working system to point at | 31,875 proven |
| **insight** (`--insight`) | Filler day, no artifact to link | 551 proven |

Two further formats live in `BRAIN/linkedin/creatives.md` and are untested here, both worth queuing:
**breakdown** (explain how a respected system actually works, architecture over personality) and
**tactical** (hook, credibility stat, the belief you dropped, 4-5 tactical lines, the principle, no CTA, one photo).

Default to build. Only use insight when there is genuinely nothing buildable to show.

---

## Step 3a: Draft the BUILD post

Follow the anatomy in the brain exactly. Nine parts, in order:

**1. Continuity + authority line.** Open like a practitioner picking up an ongoing thread, not a copywriter swinging for a hook. Pattern: `As I've said before, <TOOL> is <plain assessment>, which means <what it unlocks>.` Variants: "I've been using X for months now, and the part people miss is..." Never open with a bare provocation.

*Optional accomplishment variant [deck-sourced]:* LinkedIn actively surfaces status, and Tyler's standing appears in zero of the last 15 posts. Up to ~10% of the post can be what he has actually done (AI engineer at Pfizer, 8 years at IBM and JPMorgan Chase, 30k+ people taught, a content operation that runs out of one folder of text files). Use it as *grounding for the claim*, never as a flex, and never with money amounts. This is the one hook lane with zero attempts on the account.

**2. The system + bounded promise.** Name the specific thing being built and the step count.
`In my latest video, I'll walk you through how to build <SPECIFIC SYSTEM> using <TOOL A> and <TOOL B>. In just N steps, you'll go from zero to a working AI system that:`

**3. Four to six ✅ outcome bullets.** Verb first. Concrete object. A real named service in as many as possible. Each line is a capability the reader will have, not a feature the tool has.
- Right: `✅ Sends the finished workout plan directly to a Slack channel`
- Wrong: `✅ Slack integration`

**4. The video link on its own line.** In the body. Not in the first comment. (Confirmed: the 31k post had an inline link.)

**5. Preview header.** `🎥 Video Preview - Here's what we'll build together:`

**6. N numbered 👉 build steps.** `👉 Step 1: <action> with <named tool>`. Match N to the promise in part 2. Each step names a tool or a concrete artifact.

**7. Value close.** Two sentences: who this is for, and what they walk away able to do. No hype adjectives.

**8. Soft ask, and it must be a comment or DM ask.** `👇 Let me know what you've created!` or a question answerable from the reader's own job in one line, with a concrete unit. The video link belongs in part 4 as reference material; **never make clicking it the call to action.** A click CTA sends people off-platform and suppresses the post. Not "what do you think?" - ask something someone can answer in four words from their own week.

**9. Image brief.** Always. See Step 4.

Insert the credibility line somewhere natural in parts 1, 3, or 7 - the honest gotcha from Step 1 ("Anything Google related makes you reconnect every seven days unless you're a full production app"). This is what makes it read as someone who has actually shipped it.

---

## Step 3b: Draft the INSIGHT post

Six to twelve short lines, one idea per line, heavy white space.

**Line 1 must be a confession or a correction.** These are the only two openers with evidence behind them:

- Confession: `I never learned the video editor.` / `I stopped editing my own videos.`
- Correction: `Most people use Claude Code like a fancier chatbot.` / `Most people think the hard part is X. It really isn't.`

**Banned opener: process narration.** `I used to X, now I do Y` produced the three worst posts on the account (40, 53, 55 impressions). If your first line fits that template, rewrite it.

Line 2 subverts or specifies: `Not because I got better at it. Because I stopped doing the parts I hated.`

Body: one checkable, specific failure mode or mechanism. Name real tools. Land it with "The whole point of all this is..." or similar. Close on a genuine question the reader can answer in one line from their own job.

**Hook lanes** (the confession/correction split maps onto two of three known lanes):

| Lane | Shape | Evidence |
|---|---|---|
| Big Mistake or Threat | confession: "I never learned...", "I stopped..." | 213, 366 |
| Contrast | correction: "Most people think X. It really isn't." | 551, 197 |
| Big Accomplishment | what he built or achieved, stated plainly | untested, see build part 1 |

Skip the controversy lane entirely. It draws argument, not the right readers, and contrast already outperforms without that cost.

**Stuck? Use PAS.** Problem (state what the reader is hitting), Agitation (what it costs them down the line), Solution (the actionable close). The 197-impression arcade post is exactly this: connecting is not the hard part / your agent quietly dies after seven days and never tells you / arcade.dev holds the auth.

---

## Step 4: Write the image brief (build mode: mandatory)

Every all-time winner carried an image. Produce a brief, not the image (Tyler has a designer; see the thumbnails workflow). Spec:

- **Top strip:** branded banner, 2-4 words, high contrast, e.g. "Build AI Agents"
- **Body:** an architecture diagram of the ACTUAL pipeline, left to right or bottom to top, with each named tool as a labeled node and arrows showing data flow. The 31k post's diagram read Google Drive → Research/Summarizer → Excel/Docx → Slack.
- **Why it matters:** this is the part people screenshot and repost. A talking-head thumbnail does not do this job.
- Note in the brief which nodes are real product names so the designer uses correct logos/wordmarks.

**If a pipeline diagram does not fit the post** (insight, breakdown, or tactical posts), pick from the ranked format list in `BRAIN/linkedin/creatives.md`: a real photo from his life in a professional setting, a proof screenshot (terminal mid-run, an agent's real output, a folder an agent actually filled), a photographed handwritten list, or a repurposed YouTube thumbnail. Never ship a post with no visual.

### Render it, do not generate it

Creatives are rendered from HTML with headless Chrome, never produced by an AI image model. Diagrams carry
exact product names (`CLAUDE.md`, `/rewind`, Notion, Slack) and image models garble label text.

```
python3 ~/.claude/skills/linkedin-writer/render.py <spec.json> out/          # PNGs
python3 ~/.claude/skills/linkedin-writer/render.py <spec.json> guide.pdf     # PDF document post
```

**Start from a template in `templates/`, never from scratch.** See `templates/README.md`.

| Template | Use |
|---|---|
| `diagram-system.json` | the build-post image |
| `carousel-6.json` | a LinkedIn carousel |
| `pdf-guide-5.json` | a LinkedIn document post |

House style lives in `render.py` (`STYLE`): near-black `#141419`, coral `#E07355`, cream `#F5F0EB`, mono for
metadata and body, terminal cards with a green success line. Sampled from Tyler's own IG carousels. It is **not**
the social-studio theme named `electric`, which is blue on near-white.

**Read the source before drawing anything.** The package `script.md` and the real chapter list, not the social
copy already written about the video. The first Cowork diagram was built from secondhand social copy and named
the wrong connectors.

Save the spec JSON next to the PNG so the creative can be restyled later without rewriting copy.

If Tyler wants a photographic or illustrative image instead of a diagram, hand off to `/yt-thumbnail` or
`/carousel` rather than doing it here.

---

## Step 5: Score the draft before handing it over (hard gate)

Print this scorecard filled in. **If build mode scores under 8/10, rewrite before showing Tyler.**

| # | Check | Pass condition |
|---|---|---|
| 1 | Named tools | ≥ 5 real products named |
| 2 | Step count stated | A number appears before the first list |
| 3 | Outcome bullets | 4-6, verb-first, each names a service |
| 4 | Numbered build steps | Present, count matches the promise |
| 5 | Video link in body | Yes, on its own line |
| 6 | Image brief | Architecture diagram spec included |
| 7 | Credibility line | A real gotcha or standing claim appears |
| 8 | Repost test | Could a staff engineer forward this to their team channel as a resource, without clicking? |
| 8b | CTA is on-platform | Closes on a comment or DM ask. The link is reference material, never the ask. |
| 9 | Voice bans | No em dashes, no bold, no markdown, no hashtags, no hype words (insane, crazy, game-changer, mind-blowing, secret, hack) |
| 10 | Positioning | Passes the transfer test in tyler-voice.md: the takeaway works for anyone with repetitive work, not just creators. YouTube is the setting, never the topic. |

Insight mode uses checks 7, 8b, 9, 10 plus: opener sits in one of the three hook lanes and is not process narration, and one checkable specific appears in the body.

**Report the score honestly.** If a check fails and cannot be fixed (no video link exists yet, the stack only has 3 tools), say so plainly rather than padding the post to pass.

---

## Step 5b: Note the slot

When handing over, suggest a posting slot from the cadence defaults in the brain [deck-sourced, unconfirmed here]:
3-5 posts a week, Tuesday to Thursday best, before 9am or after 4pm. Say it is an untested default so Tyler can
overrule it.

## Step 6: Save it

- Tied to a video: `~/content/youtube/videos/NNN-slug/social/linkedin.md`
- Standalone: `~/content/platform/linkedin/YYYY-MM-DD-slug.md`

File format:

```
# LinkedIn - <date> - <mode>
**Topic:** <one line>
**Scorecard:** <n>/10
**Image brief:** <one line summary, full spec below>

---

<the post, exactly as it should be pasted, nothing else>

---

## Image brief
<full spec>

## Notes
<what failed the scorecard and why, open questions for Tyler>
```

The post body between the `---` rules must be paste-ready: no markdown, no commentary, no placeholder brackets.

---

## Step 7: Confirm before anything leaves the machine

Never post, schedule, or publish. Per the repo's standing rule, drafting is the job; Tyler pastes. If he asks to automate posting, confirm explicitly first.

---

## Feeding the brain

After a post has been up ~7 days, if Tyler shares the numbers, update `~/content/BRAIN/linkedin/brain.md`:
- Add the result to the relevant table with a `[confirmed YYYY-MM-DD]` stamp
- Promote a hypothesis to a rule when a second post replicates it
- Retire rules that stop being true

The most important open test named in the brain: whether the build-post format still performs on a current Claude Code topic, or whether the 31,875 was partly mid-2025 CrewAI topic timing. Measure that first.
