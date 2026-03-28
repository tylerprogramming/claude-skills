---
name: email
description: Send emails via Resend - one-off blasts to Skool members or run the 3-email drip campaign for new members. Triggers on: send email, email campaign, drip campaign, resend, blast email, email members, welcome emails.
argument-hint: [send/campaign/status/list] [options]
allowed-tools: Bash(python3:*), Read, Write, Edit, Glob, Grep, AskUserQuestion
user-invocable: true
---

Email automation for The AI Agency Skool community via Resend. Two capabilities: one-off emails and multi-step drip campaigns.

## Config

From `~/.claude/.env`:
- `RESEND_API_KEY` - Resend API key
- `RESEND_FROM` - Sender name and email (e.g. `Tyler <tyler@tylerai.dev>`)
- `RESEND_REPLY_TO` - Reply-to email address

Pro tier: 50,000 emails/month, unlimited daily, 5 req/s.

## Database

SQLite at `~/.claude/skills/skool/data/skool.db`. Uses a normalized 3-table design:

**`email_campaigns`** - defines campaigns (name, trigger_type, trigger_filter, active)
**`email_campaign_steps`** - steps in each campaign (step_number, delay_hours, subject_template, html_template, tag)
**`email_sends`** - log of every email sent (campaign_id, step_number, member_id, email, sent_at, mailgun_id, opened_at)

Members come from `skool_members` table. The campaign runner matches members against the campaign's `trigger_filter` SQL, checks `email_sends` for what step they're on, and sends the next one if enough time has passed since approval.

Contacts are also synced to Resend Contacts (via `sync_contacts_resend.py`) so they're available in the Resend dashboard for broadcasts and segments.

## What to Do Based on User Request

### "send email" / "blast email" / "email members"

One-off email to all members (or a filtered subset).

1. Ask for: subject, email body content (or a topic to draft from)
2. Draft the HTML email and show it to the user
3. Ask which members to target (all, free only, premium only, or a custom filter)
4. Show recipient count and get confirmation
5. Run: `python3 ~/.claude/skills/email/send_email.py --subject "..." --html-file /tmp/email.html [--filter free|premium|vip|all] [--batch-size N] [--batch-offset N]`

### "drip campaign" / "welcome emails" / "email campaign"

Run campaign checker. Finds members due for their next step and sends it.

1. Run: `python3 ~/.claude/skills/email/email_campaign.py [--campaign name]`
2. Report what was sent (or that no one is due)

### "campaign status" / "email status"

Check without sending.

1. Run: `python3 ~/.claude/skills/email/email_campaign.py --dry-run`
2. Show who is due for which step

### "list campaigns"

Show all campaigns, their steps, and send counts.

1. Run: `python3 ~/.claude/skills/email/email_campaign.py --list`

### "sync contacts" / "update resend contacts"

Sync Skool members to Resend Contacts (create, update, delete).

1. Run: `python3 ~/.claude/skills/email/sync_contacts_resend.py`
2. Report creates, updates, and deletes

## Current Campaigns

**new_member_welcome** (auto, 3 steps):
- Step 1 "Welcome" - +1h after approval (templates/welcome.html)
- Step 2 "Getting Started" - +24h after approval (templates/getting_started.html)
- Step 3 "Self-Hosting" - +72h after approval (templates/self_hosting.html)

## Adding a New Campaign

To add a campaign, insert into `email_campaigns` and `email_campaign_steps`:
```sql
INSERT INTO email_campaigns (name, description, trigger_type, trigger_filter, active, created_at, updated_at)
VALUES ('campaign_name', 'description', 'auto|manual', 'SQL WHERE clause for skool_members', 1, datetime('now'), datetime('now'));

INSERT INTO email_campaign_steps (campaign_id, step_number, delay_hours, subject_template, html_template, tag)
VALUES (campaign_id, 1, 0, 'Subject with {first_name}', 'templates/template.html', 'tag_name');
```

## Templates

HTML templates at `~/.claude/skills/email/templates/`. Use `{first_name}` as placeholder.

## Rules

- Always show email content and get confirmation before sending
- Never auto-send without user approval
- No em dashes in any email content
- Tag emails with their type for Resend tracking
- All sends are logged in `email_sends` (both campaign and one-off blasts)
- Contacts are synced to Resend daily alongside the Skool member sync
