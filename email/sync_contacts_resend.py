#!/usr/bin/env python3
"""Sync Skool members to Resend Contacts.

Full two-way sync: creates new contacts, updates existing ones, and removes
contacts that are no longer in the Skool members database.
"""

import sqlite3
import sys
import time
from pathlib import Path

try:
    import resend
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "resend"])
    import resend


DB_PATH = Path.home() / ".claude" / "skills" / "skool" / "data" / "skool.db"


def load_env():
    env = {}
    env_path = Path.home() / ".claude" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                env[key.strip()] = val.strip()
    return env


def get_members():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT first_name, last_name, full_name, email, membership_tier FROM skool_members "
        "WHERE email IS NOT NULL AND email != '' ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_resend_contacts():
    """Fetch all contacts from Resend."""
    all_contacts = {}

    # list() with no params returns all contacts
    result = resend.Contacts.list()
    data = result.get("data", []) if isinstance(result, dict) else getattr(result, "data", [])

    for contact in data:
        if isinstance(contact, dict):
            email = contact.get("email", "")
            cid = contact.get("id", "")
            first = contact.get("first_name", "")
            last = contact.get("last_name", "")
        else:
            email = getattr(contact, "email", "")
            cid = getattr(contact, "id", "")
            first = getattr(contact, "first_name", "")
            last = getattr(contact, "last_name", "")

        if email:
            all_contacts[email.lower()] = {
                "id": cid,
                "email": email,
                "first_name": first or "",
                "last_name": last or "",
            }

    return all_contacts


def main():
    env = load_env()
    if "RESEND_API_KEY" not in env:
        print("ERROR: RESEND_API_KEY not found in ~/.claude/.env")
        sys.exit(1)

    resend.api_key = env["RESEND_API_KEY"]

    # Get local members and remote contacts
    members = get_members()
    member_emails = {m["email"].lower(): m for m in members}

    print("Fetching existing Resend contacts...")
    resend_contacts = get_resend_contacts()
    print(f"  Local members: {len(members)}")
    print(f"  Resend contacts: {len(resend_contacts)}\n")

    created = 0
    updated = 0
    deleted = 0
    failed = 0
    ops = 0

    # Create or update contacts
    for m in members:
        email_lower = m["email"].lower()
        first = m["first_name"] or ""
        last = m["last_name"] or ""

        if email_lower in resend_contacts:
            # Check if update needed
            existing = resend_contacts[email_lower]
            if existing["first_name"] != first or existing["last_name"] != last:
                try:
                    resend.Contacts.update({
                        "email": m["email"],
                        "first_name": first,
                        "last_name": last,
                    })
                    updated += 1
                except Exception as e:
                    failed += 1
                    if failed <= 5:
                        print(f"  UPDATE FAILED {m['email']}: {e}")
                ops += 1
        else:
            # Create new contact
            try:
                resend.Contacts.create({
                    "email": m["email"],
                    "first_name": first,
                    "last_name": last,
                    "unsubscribed": False,
                })
                created += 1
            except Exception as e:
                err = str(e)
                if "already exists" in err.lower():
                    pass  # Fine, already there
                else:
                    failed += 1
                    if failed <= 5:
                        print(f"  CREATE FAILED {m['email']}: {e}")
            ops += 1

        if ops % 50 == 0 and ops > 0:
            print(f"  Progress: {ops}/{len(members)}")
            time.sleep(1)

    # Delete contacts no longer in Skool
    stale_emails = set(resend_contacts.keys()) - set(member_emails.keys())
    if stale_emails:
        print(f"\n  Removing {len(stale_emails)} stale contacts...")
        for email in stale_emails:
            try:
                resend.Contacts.remove(email=resend_contacts[email]["email"])
                deleted += 1
            except Exception as e:
                failed += 1
                if failed <= 5:
                    print(f"  DELETE FAILED {email}: {e}")
            time.sleep(0.2)

    print(f"\nDone!")
    print(f"  Created: {created}")
    print(f"  Updated: {updated}")
    print(f"  Deleted: {deleted}")
    print(f"  Failed: {failed}")
    print(f"  Total synced: {len(members)}")


if __name__ == "__main__":
    main()
