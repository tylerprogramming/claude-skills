---
name: claude-code-essentials
description: Send the "3 Rules of a Great CLAUDE.md" email to any recipient via Resend. Triggers on: claude code essentials, send the essentials email, claude.md email, 3 rules of claude.md.
argument-hint: [recipient-email] [--name First]
allowed-tools: Read, Write, Edit, Glob, AskUserQuestion, mcp__plugin_resend_resend__send-email, mcp__plugin_resend_resend__get-email
user-invocable: true
---

Sends a fixed, pre-written email about CLAUDE.md files, the memory file Claude Code reads every session. Three rules: write it like day one onboarding, keep it short and specific, and layer it so it grows from your own corrections.

## Assets

- `templates/essentials.html` - branded HTML body, matches the `email` skill house style
- `templates/essentials.txt` - plain text alternative (required by Resend, and better for deliverability)

Both use a single `{first_name}` placeholder.

## Send Config

- **From:** `Tyler Reed <hello@tylerai.dev>` (tylerai.dev is the verified Resend domain)
- **Reply-to:** `hello@tylerai.dev`
- **Tag:** `category: claude-code-essentials`
- Send with the `mcp__plugin_resend_resend__send-email` tool. Do not shell out to the `email` skill's scripts, those log into the Skool database and this email is not a Skool blast.

## What to Do

1. **Get the recipient.** Use the email passed as an argument. If none was given, ask for it with AskUserQuestion. Multiple recipients are fine, pass them all in the `to` array.
2. **Get the first name.** Use `--name` if given. If not, derive it from the email local part when it is obviously a name, otherwise fall back to `there` so the greeting reads "Hey there,".
3. **Fill the templates.** Read both files, replace every `{first_name}`. Never send a body with an unreplaced `{first_name}` in it, check before sending.
4. **Show and confirm.** Print the subject and the plain text body to the user and get explicit approval before sending. Never auto-send.
5. **Send.**
   - `subject`: `The 3 rules of a great CLAUDE.md`
   - `from`: `Tyler Reed <hello@tylerai.dev>`
   - `replyTo`: `["hello@tylerai.dev"]`
   - `html`: filled `essentials.html`
   - `text`: filled `essentials.txt`
   - `tags`: `[{"name": "category", "value": "claude-code-essentials"}]`
   - `idempotencyKey`: `cc-essentials-<recipient>-<yyyy-mm-dd>` so a retry does not double send
6. **Report** the returned email ID.

## Editing the Content

The three rules are the whole point of this skill, do not silently rewrite them. If the user asks for different content, edit both `essentials.html` and `essentials.txt` together so the two bodies stay in sync, and update the subject line above to match.

## Rules

- No em dashes in any email content
- Always confirm before sending
- Keep the HTML and text bodies saying the same thing
