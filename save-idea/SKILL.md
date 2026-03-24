---
name: save-idea
description: Save a new YouTube video idea to the video ideas tracker. Use when the user has a new video idea, wants to log a content concept, or says things like "save this idea", "add this to my video ideas", "I have an idea for a video". Triggers on: save idea, video idea, add idea, log idea, new video concept.
argument-hint: [idea title or description]
allowed-tools: Read, Edit, Write
user-invocable: true
---

Save a new video idea to the tracker at `~/youtube/video-ideas.md`.

## Instructions

1. First, read the current file at `~/youtube/video-ideas.md` to understand the existing format and avoid duplicates.

2. **Keep it fast.** The user might just say "save idea: Claude Code memory system deep dive" - that's enough. Don't interrogate them.
   - **Title** (required): If not obvious, ask for one. Otherwise infer from what they said.
   - **Topic, Angle, Target Audience, Notes**: Infer from context if possible. Only ask if the idea is vague and you genuinely can't fill these in.
   - **Priority**: Default to Medium if not specified. Only ask if the user seems unsure where to rank it.

3. Add the new idea to the `## Active Ideas` section (if high priority) or `## Backlog Ideas` section (if medium/low priority) in the same markdown format as existing entries:
   ```
   ### N. [Title]
   - **Status:** Planned
   - **Priority:** [High/Medium/Low]
   - **Topic:** [description]
   - **Angle:** [what makes it unique]
   - **Target Audience:** [who watches]
   - **Research:** [link to research file if applicable]
   - **Notes:** [additional context]
   - **Date Added:** [YYYY-MM-DD]
   ```

4. Increment the idea number based on the last entry in the section.

5. Confirm to the user that the idea was saved and show them the entry.

## Status Lifecycle

Ideas move through these statuses:
- **Planned** — idea saved, not started
- **In Progress** — `/yt` is building a video package for this idea (set automatically by `/yt` Step 0)
- **Uploaded** — video is live (move to Completed section manually or via this skill)
- **Backlog** — parked for later

When the user says "mark idea X as done" or "I uploaded idea X", move it to the `## Completed` section and add the video package path and upload date.
