---
name: quiz
description: Read a document (PDF, text, docx, markdown) and quiz the user on it. Understands the document type (interview guide, study material, test prep, certification exam, etc.) and interactively asks questions, gives feedback, and coaches the user. Triggers on: quiz me, interview me, prep me, study this, test me on this, help me prepare.
argument-hint: [file_path]
allowed-tools: Read, Glob
user-invocable: true
---

Read the document at $ARGUMENTS and interactively quiz/coach the user based on its contents.

## Flow

### Step 1: Read & Understand the Document

Read the file at the provided path. Support these formats:
- **PDF** — Use Read tool (it handles PDFs natively)
- **Text / Markdown** — Use Read tool directly
- **DOCX** — Use Read tool; if it fails, tell the user to export as PDF or text

After reading, analyze the document to determine:
1. **Document type** — What is this? (interview guide, study guide, exam prep, certification material, course notes, technical documentation, etc.)
2. **Structure** — How is it organized? (sections, topics, categories, difficulty levels)
3. **Key concepts** — What are the main topics, themes, or competencies being covered?
4. **Question bank** — Extract or identify all questions, prompts, or testable material
5. **Evaluation criteria** — If the document includes rubrics, scoring guides, or "meets expectations" criteria, note them carefully — you'll use these to evaluate answers

### Step 2: Present Summary & Ask Mode

Present a brief summary of what you found to the user:

> **Document:** [title/name]
> **Type:** [what it is]
> **Topics covered:** [bulleted list of main sections/themes]
> **Total questions/topics available:** [count]

Then ask the user what mode they want using AskUserQuestion:

**Modes:**
- **Mock Interview** — You act as the interviewer. Ask questions one at a time, in a realistic interview flow. After each answer, give feedback based on the document's evaluation criteria. Use probing/follow-up questions when appropriate.
- **Rapid Fire Quiz** — Quick questions, short feedback. Cover as much ground as possible.
- **Deep Practice** — Focus on one topic/section at a time. Ask the question, hear the answer, then provide detailed coaching with what a strong answer looks like vs. a weak one (using the document's criteria).
- **Study Review** — Walk through the material topic by topic. For each topic, explain what's being assessed, give the question, then discuss what good looks like before asking the user to attempt it.

### Step 3: Run the Session

Based on the chosen mode, begin the interactive session.

#### For ALL modes:

- **Ask ONE question at a time.** Wait for the user to respond before moving on.
- **After each answer**, provide feedback:
  - What was strong about their answer
  - What was missing or could be improved
  - If the document has evaluation criteria (like "meets expectations" vs "below expectations"), reference it specifically
  - A brief example of what a great answer would include (without giving them a scripted answer — coach, don't spoon-feed)
- **Use probing questions** if the document provides them. After the user's initial answer, ask 1-2 follow-ups like:
  - "What was the outcome?"
  - "What would you do differently?"
  - "How did you measure success?"
- **Track progress** mentally — note which areas the user is strong in and which need work
- **Vary the difficulty** — start with more approachable questions and build up

#### Mode-specific behavior:

**Mock Interview:**
- Set the scene: "Let's simulate a real interview. I'll be your interviewer. Take a breath, and let's begin."
- Maintain interviewer persona — professional, encouraging but not overly casual
- Ask questions in a logical interview order (motivation first, then values/competencies, then skills)
- After 5-8 questions, offer to continue or wrap up with a summary
- At the end, give an overall assessment: strengths, areas to improve, and top 3 tips

**Rapid Fire Quiz:**
- Keep it fast — short question, short feedback
- After each answer, rate it: Strong / Good / Needs Work
- Track a running score
- Cover all sections of the document

**Deep Practice:**
- Focus on one section at a time
- Before asking the question, briefly explain what competency is being assessed and why it matters
- After the answer, give detailed feedback with specific improvements
- Offer to retry the same question or move on
- Use the STAR method (Situation, Task, Action, Result) as a framework if the document involves behavioral questions

**Study Review:**
- Walk through each section methodically
- Explain the concept/competency first
- Share what "meets expectations" and "below expectations" look like (if available in the document)
- Then ask the user to practice
- More teaching, less testing

### Step 4: Wrap Up

After the session (user says they're done, or you've covered all material), provide:

1. **Performance Summary** — Which areas were strong, which need more practice
2. **Top 3 Tips** — Specific, actionable advice based on their answers
3. **Suggested Practice Areas** — Topics they should focus on next time
4. **Confidence Rating** — Your honest assessment of how ready they are (if this is interview/test prep)

## Rules

- NEVER give the user a scripted perfect answer to memorize. Coach them to build their own authentic answers.
- If this is interview prep, use the STAR method (Situation, Task, Action, Result) as a framework for behavioral questions.
- Be encouraging but honest. Don't sugarcoat weak answers — the point is to help them improve.
- If the document has specific evaluation criteria, USE THEM. Don't make up your own criteria.
- Ask one question at a time. Never dump multiple questions at once.
- If the user's answer is vague, use probing questions to draw out specifics before giving feedback.
- Adapt to the user's level — if they're nailing it, increase difficulty. If they're struggling, slow down and coach more.
- Keep track of which questions you've asked so you don't repeat.
- If the document is an interview guide meant for interviewers (not candidates), flip the perspective — use those questions to prep the candidate.
