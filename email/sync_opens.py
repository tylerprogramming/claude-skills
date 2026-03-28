#!/usr/bin/env python3
"""Sync open/delivery events from Resend API back into email_sends table.

Note: Resend's free tier shows deliverability insights in the dashboard.
For programmatic open tracking, Resend uses webhooks or the dashboard.
This script checks email status via the Resend API for recent sends.
"""

import sqlite3
import sys
from datetime import datetime, timezone
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


def main():
    env = load_env()
    if "RESEND_API_KEY" not in env:
        print("ERROR: RESEND_API_KEY not found in ~/.claude/.env")
        sys.exit(1)

    resend.api_key = env["RESEND_API_KEY"]

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Get recent sends that have a Resend email ID and no opened_at
    rows = conn.execute(
        "SELECT id, mailgun_id FROM email_sends WHERE mailgun_id IS NOT NULL AND mailgun_id != '' AND opened_at IS NULL ORDER BY id DESC LIMIT 200"
    ).fetchall()

    if not rows:
        print("No recent sends to check.")
        conn.close()
        return

    print(f"Checking {len(rows)} recent email statuses...")
    updated = 0

    for row in rows:
        try:
            email_data = resend.Emails.get(row["mailgun_id"])
            # Check last_event or status
            last_event = None
            if isinstance(email_data, dict):
                last_event = email_data.get("last_event")
            else:
                last_event = getattr(email_data, "last_event", None)

            if last_event in ("opened", "clicked"):
                now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                conn.execute(
                    "UPDATE email_sends SET opened_at = ? WHERE id = ?",
                    (now, row["id"]),
                )
                updated += 1
        except Exception as e:
            # Skip errors (rate limits, etc.)
            continue

    conn.commit()

    total_sends = conn.execute("SELECT COUNT(*) FROM email_sends").fetchone()[0]
    total_opened = conn.execute("SELECT COUNT(*) FROM email_sends WHERE opened_at IS NOT NULL").fetchone()[0]

    print(f"Updated {updated} new opens")
    print(f"Total sends: {total_sends}, Total opened: {total_opened}")

    conn.close()
    print("Done!")


if __name__ == "__main__":
    main()
