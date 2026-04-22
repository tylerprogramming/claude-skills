---
name: harut
description: Ask Harut questions about growing your business to 100k/month. RAG-powered advisor trained on Harut's full 21-hour teachings, personalized for Tyler's AI content creator business (YouTube, Skool, social media). Answers are grounded in the transcript and applied specifically to Tyler's situation. Triggers on: ask harut, harut, what does harut say, harut advice, harut says, business growth, 100k month, how do I grow, grow my skool, grow my business, pricing advice, harut question.
argument-hint: "<your question about growing your business>"
allowed-tools: [Bash, Read, Write, Glob]
user-invocable: true
---

# Harut - Business Growth RAG Advisor

Harut is Tyler's personal business advisor, trained on Harut's 21-hour masterclass on growing a business to $100k/month. It uses RAG (retrieval-augmented generation) to pull the most relevant teachings and applies them to Tyler's specific situation: YouTube AI content, Skool community, and social media.

## Setup (one-time, auto-runs on first query)

The transcript must be indexed before querying. The skill handles this automatically.

## Steps

1. **Check if the index exists:**
   ```bash
   python3 ~/.claude/skills/harut/harut_rag.py status
   ```

2. **If not indexed yet**, index the transcript:
   ```bash
   python3 ~/.claude/skills/harut/harut_rag.py index ~/scripts/transcript_u2hmXbhTTLE.txt
   ```
   This takes a few minutes and only needs to run once. It will print progress.

3. **Answer the user's question:**
   ```bash
   python3 ~/.claude/skills/harut/harut_rag.py query "QUESTION_HERE"
   ```
   Where QUESTION_HERE is the user's question verbatim.

4. **Present the answer** directly to the user. The answer is already formatted — just show it.

## Notes
- If the transcript file doesn't exist yet, tell the user: "The Harut transcript is still being processed. Run `/transcribe https://youtu.be/u2hmXbhTTLE` first, then try again."
- Index lives at `~/.claude/skills/harut/harut_index.json` — persistent across sessions
- Re-indexing is only needed if the transcript changes
