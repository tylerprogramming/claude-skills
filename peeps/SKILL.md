---
name: peeps
description: Personal people tracker. Save details about people (name, birthday, how you know them, contact, family, notes) as JSON and generate a modern searchable HTML page to browse them. Use when the user wants to remember info about someone, log a person, look someone up, or check upcoming birthdays. Triggers on: peeps, add a person, remember this person, save contact info, who is, whose birthday, show my peeps, open peeps.
argument-hint: [add/update/show/remove + person details]
allowed-tools: Read, Edit, Write, Bash, Glob
user-invocable: true
---

A lightweight personal CRM. People are stored as one JSON file per person at `~/peeps/data/`, and a self-contained searchable HTML page is generated at `~/peeps/index.html`.

## Locations

- Data (source of truth): `~/peeps/data/<id>.json` — one file per person
- Generated page: `~/peeps/index.html`
- Photos (optional): `~/peeps/assets/photos/<id>.jpg`
- Page generator: `~/.claude/skills/peeps/build.py`

`<id>` is a kebab-case slug of the person's name (e.g. "Jane Smith" → `jane-smith`). If two people share a name, append a differentiator (`john-smith-work`).

## Detect intent from how the user invokes the skill

| User intent | Action |
|-------------|--------|
| Add a new person ("peeps: add Jane Smith, college roommate, birthday April 12") | **Add** — see below |
| Update someone ("peeps: update Mike, new phone 555-1234") | **Edit** — see below |
| View / open ("peeps", "show my peeps", "open peeps") | **View** — rebuild page and open it |
| Query ("whose birthday is coming up?", "who do I know in Austin?") | **Query** — read all JSON, answer in chat |
| Remove ("peeps: remove Mike") | **Delete** — confirm, delete file, rebuild |

## Adding a person

**Keep it fast** — infer everything you can from the one sentence the user gave. Only ask if something important is genuinely ambiguous (e.g. you can't tell the person's name). Don't interrogate.

1. Build the JSON record using the schema below. Fill what you can infer; leave unknown fields as `null` or empty arrays/objects. Always set `created` and `updated` to today's date (YYYY-MM-DD).
2. Write it to `~/peeps/data/<id>.json`.
3. Rebuild the page (see "Rebuild the page").
4. Confirm to the user and show the saved record.

### Schema

```json
{
  "id": "jane-smith",
  "name": "Jane Smith",
  "nickname": "Janie",
  "photo": "assets/photos/jane-smith.jpg",
  "how_we_met": "College roommate, 2008",
  "location": "Austin, TX",
  "tags": ["friend", "college"],
  "dates": {
    "birthday": "1988-04-12",
    "anniversary": null,
    "met_on": "2008-09-01"
  },
  "contact": {
    "phone": "555-0142",
    "email": "jane@example.com",
    "socials": { "instagram": "@janie", "linkedin": "in/janesmith" }
  },
  "relationships": {
    "partner": "Tom",
    "kids": ["Ava", "Leo"],
    "family_notes": "Has a dog named Biscuit"
  },
  "interests": ["pottery", "trail running"],
  "gift_ideas": ["pottery class voucher"],
  "notes": "Free-form notes.",
  "created": "2026-06-13",
  "updated": "2026-06-13"
}
```

**Birthday format:** ISO `YYYY-MM-DD`. If the year is unknown, use `--MM-DD` (e.g. `--04-12`) — the page still shows the day and "days until" but skips age. `photo` is optional; omit or leave `null` if there's no image (the page shows a colored initials avatar instead).

## Editing a person

1. Find the file via the slug, or Glob `~/peeps/data/*.json` and match by name if unsure.
2. Read it, apply the changes, set `updated` to today.
3. Write it back and rebuild the page.

## Rebuild the page

Run the generator after any add/edit/delete:

```bash
python3 ~/.claude/skills/peeps/build.py
```

It reads every `~/peeps/data/*.json` and writes a fresh `~/peeps/index.html` with all people inlined (works offline, no server needed). To open it after a "view" request:

```bash
open ~/peeps/index.html
```

## Querying

For questions like "whose birthday is coming up" or "who do I know in Austin", Glob and Read the JSON files, compute the answer, and respond in chat. You don't need to rebuild the page for a pure query.

## Notes

- Always confirm before deleting a person's file.
- Never overwrite an existing person on "add" — if the slug already exists, treat it as an edit or ask whether to create a differentiated id.
- The page is regenerated from scratch each build, so the JSON files are the single source of truth — never hand-edit `index.html`.
