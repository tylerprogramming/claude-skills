#!/usr/bin/env python3
"""Send one-off emails via Resend to Skool members.

Records sends in email_sends table (campaign_id=NULL for one-off blasts).
"""

import argparse
import sqlite3
import sys
import time
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


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_recipients(filter_type="all", batch_size=0, batch_offset=0):
    conn = get_db()
    cur = conn.cursor()

    base = "SELECT id, first_name, full_name, email FROM skool_members WHERE email IS NOT NULL AND email != ''"

    if filter_type == "free":
        base += " AND membership_tier = 'free'"
    elif filter_type == "premium":
        base += " AND (monthly_member = 1 OR annual_member = 1)"
    elif filter_type == "vip":
        base += " AND vip_member = 1"

    base += " ORDER BY id"

    if batch_size > 0:
        base += f" LIMIT {batch_size} OFFSET {batch_offset}"

    rows = [dict(r) for r in cur.execute(base).fetchall()]
    conn.close()
    return rows


def send_email(env, to_email, subject, html, tag="blast"):
    params = {
        "from": env["RESEND_FROM"],
        "to": [to_email],
        "subject": subject,
        "html": html,
        "reply_to": env["RESEND_REPLY_TO"],
        "tags": [{"name": "category", "value": tag}],
    }

    try:
        result = resend.Emails.send(params)
        email_id = result.get("id") if isinstance(result, dict) else getattr(result, "id", None)
        return True, {"id": email_id}
    except Exception as e:
        return False, {"error": str(e)}


def record_blast_send(member_id, email, tag, email_id=None):
    """Record a one-off blast in email_sends with campaign_id 0 and step_number 0."""
    conn = get_db()
    cur = conn.cursor()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(
        "INSERT INTO email_sends (campaign_id, step_number, member_id, email, sent_at, mailgun_id) VALUES (0, 0, ?, ?, ?, ?)",
        (member_id, email, now, email_id),
    )
    conn.commit()
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Send one-off email via Resend")
    parser.add_argument("--subject", required=True, help="Email subject line (supports {first_name})")
    parser.add_argument("--html-file", required=True, help="Path to HTML email body")
    parser.add_argument("--filter", default="all", choices=["all", "free", "premium", "vip"],
                        help="Member filter (default: all)")
    parser.add_argument("--to", help="Send to a single email address (for testing)")
    parser.add_argument("--tag", default="blast", help="Email tag (default: blast)")
    parser.add_argument("--batch-size", type=int, default=0, help="Limit to N recipients (for warmup)")
    parser.add_argument("--batch-offset", type=int, default=0, help="Skip first N recipients (for warmup batches)")
    parser.add_argument("--dry-run", action="store_true", help="Show recipients without sending")
    args = parser.parse_args()

    env = load_env()
    for key in ["RESEND_API_KEY", "RESEND_FROM", "RESEND_REPLY_TO"]:
        if key not in env:
            print(f"ERROR: {key} not found in ~/.claude/.env")
            sys.exit(1)

    resend.api_key = env["RESEND_API_KEY"]

    html_path = Path(args.html_file)
    if not html_path.exists():
        print(f"ERROR: HTML file not found: {args.html_file}")
        sys.exit(1)
    html_template = html_path.read_text()

    if args.to:
        recipients = [{"id": 0, "first_name": "Test", "full_name": "Test User", "email": args.to}]
    else:
        recipients = get_recipients(args.filter, args.batch_size, args.batch_offset)

    if not recipients:
        print("No recipients found.")
        sys.exit(0)

    if args.dry_run:
        print(f"DRY RUN - Would send to {len(recipients)} recipients:")
        for r in recipients[:20]:
            print(f"  {r['full_name']} <{r['email']}>")
        if len(recipients) > 20:
            print(f"  ... and {len(recipients) - 20} more")
        sys.exit(0)

    print(f"Sending to {len(recipients)} recipients...")
    sent = 0
    failed = 0

    for r in recipients:
        first_name = r["first_name"] or "there"
        html = html_template.replace("{first_name}", first_name)
        subject = args.subject.replace("{first_name}", first_name)

        ok, result = send_email(env, r["email"], subject, html, tag=args.tag)
        if ok:
            email_id = result.get("id")
            if r["id"] != 0:
                record_blast_send(r["id"], r["email"], args.tag, email_id)
            sent += 1
            print(f"  Sent to {r['email']}")
        else:
            failed += 1
            print(f"  FAILED {r['email']}: {result}")

        if len(recipients) > 1:
            time.sleep(0.25)

    print(f"\nDone. Sent: {sent}, Failed: {failed}")


if __name__ == "__main__":
    main()
