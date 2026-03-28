#!/usr/bin/env python3
"""Campaign runner for Resend email campaigns.

Uses the normalized email_campaigns / email_campaign_steps / email_sends tables.
Finds members due for their next campaign step and sends it.
"""

import argparse
import sqlite3
import sys
import time
import warnings
from datetime import datetime, timedelta
from pathlib import Path

warnings.filterwarnings("ignore", message=".*datetime.datetime.utcnow.*")

try:
    import resend
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "resend"])
    import resend


SKILL_DIR = Path(__file__).parent


# Resolve DB path: prefer the mounted skills folder, fall back to ~/.claude
_db_candidates = [
    Path.home() / "mnt" / "skills" / "skool" / "data" / "skool.db",
    Path.home() / ".claude" / "skills" / "skool" / "data" / "skool.db",
]
DB_PATH = next((p for p in _db_candidates if p.exists()), _db_candidates[0])


def load_env():
    """Load Resend credentials. Checks os.environ first, then ~/.claude/.env."""
    import os
    env = {}

    # 1. Read from file (lowest priority)
    for env_path in [
        Path.home() / ".claude" / ".env",
        Path.home() / "mnt" / "skills" / ".env",
    ]:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    env[key.strip()] = val.strip()
            break

    # 2. Environment variables override file values (highest priority)
    if "RESEND_API_KEY" in os.environ:
        env["RESEND_API_KEY"] = os.environ["RESEND_API_KEY"]

    return env


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def parse_dt(dt_str):
    if not dt_str:
        return None
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S.%f"]:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    return None


def now_str():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def find_candidates(campaign_name=None):
    """Find members due for their next step in any active auto campaign."""
    conn = get_db()
    cur = conn.cursor()

    # Get active auto campaigns (or a specific one)
    if campaign_name:
        campaigns = cur.execute(
            "SELECT * FROM email_campaigns WHERE name = ? AND active = 1", (campaign_name,)
        ).fetchall()
    else:
        campaigns = cur.execute(
            "SELECT * FROM email_campaigns WHERE trigger_type = 'auto' AND active = 1"
        ).fetchall()

    now = datetime.utcnow()
    candidates = []

    for campaign in campaigns:
        cid = campaign["id"]

        # Get steps ordered
        steps = cur.execute(
            "SELECT * FROM email_campaign_steps WHERE campaign_id = ? ORDER BY step_number",
            (cid,),
        ).fetchall()

        if not steps:
            continue

        # Get members matching the campaign's trigger filter
        trigger_filter = campaign["trigger_filter"] or "1=1"
        members = cur.execute(
            f"SELECT id, first_name, full_name, email, approved_at FROM skool_members WHERE {trigger_filter}"
        ).fetchall()

        for member in members:
            approved = parse_dt(member["approved_at"])
            if not approved:
                continue

            hours_since_approval = (now - approved).total_seconds() / 3600

            # Find what step they're on: check which steps have been sent
            sent_steps = cur.execute(
                "SELECT step_number FROM email_sends WHERE campaign_id = ? AND member_id = ?",
                (cid, member["id"]),
            ).fetchall()
            sent_set = {r["step_number"] for r in sent_steps}

            # Find the next step they need
            for step in steps:
                if step["step_number"] in sent_set:
                    continue  # already sent

                # Check if enough time has passed
                if hours_since_approval >= step["delay_hours"]:
                    # For steps after the first, also check the previous step was sent
                    if step["step_number"] > 1 and (step["step_number"] - 1) not in sent_set:
                        break  # previous step not sent yet, skip

                    candidates.append({
                        "campaign": campaign,
                        "step": step,
                        "member": dict(member),
                    })
                break  # only consider the next unsent step

    conn.close()
    return candidates


def send_email(env, to_email, subject, html, tag):
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


def record_send(campaign_id, step_number, member_id, email, email_id=None):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO email_sends (campaign_id, step_number, member_id, email, sent_at, mailgun_id) VALUES (?, ?, ?, ?, ?, ?)",
        (campaign_id, step_number, member_id, email, now_str(), email_id),
    )
    conn.commit()
    conn.close()


def list_campaigns():
    conn = get_db()
    cur = conn.cursor()
    campaigns = cur.execute("SELECT * FROM email_campaigns ORDER BY id").fetchall()

    if not campaigns:
        print("No campaigns configured.")
        return

    for c in campaigns:
        steps = cur.execute(
            "SELECT * FROM email_campaign_steps WHERE campaign_id = ? ORDER BY step_number", (c["id"],)
        ).fetchall()
        total_sent = cur.execute(
            "SELECT COUNT(*) as cnt FROM email_sends WHERE campaign_id = ?", (c["id"],)
        ).fetchone()["cnt"]

        status = "ACTIVE" if c["active"] else "INACTIVE"
        print(f"\n  [{c['name']}] ({status}, {c['trigger_type']})")
        print(f"    {c['description']}")
        print(f"    Filter: {c['trigger_filter']}")
        print(f"    Steps: {len(steps)}, Total sends: {total_sent}")
        for s in steps:
            step_sent = cur.execute(
                "SELECT COUNT(*) as cnt FROM email_sends WHERE campaign_id = ? AND step_number = ?",
                (c["id"], s["step_number"]),
            ).fetchone()["cnt"]
            print(f"      Step {s['step_number']}: +{s['delay_hours']}h - {s['tag']} ({step_sent} sent)")

    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Run email campaigns via Resend")
    parser.add_argument("--dry-run", action="store_true", help="Show who is due without sending")
    parser.add_argument("--campaign", help="Run a specific campaign by name (default: all active auto campaigns)")
    parser.add_argument("--list", action="store_true", help="List all campaigns and their status")
    args = parser.parse_args()

    if args.list:
        list_campaigns()
        return

    env = load_env()
    for key in ["RESEND_API_KEY", "RESEND_FROM", "RESEND_REPLY_TO"]:
        if key not in env:
            print(f"ERROR: {key} not found in ~/.claude/.env")
            sys.exit(1)

    resend.api_key = env["RESEND_API_KEY"]

    candidates = find_candidates(args.campaign)

    if not candidates:
        print("No members are due for a campaign email right now.")
        sys.exit(0)

    # Group by campaign + step for display
    by_group = {}
    for c in candidates:
        key = f"{c['campaign']['name']} / step {c['step']['step_number']} ({c['step']['tag']})"
        by_group.setdefault(key, []).append(c)

    if args.dry_run:
        print(f"DRY RUN - {len(candidates)} emails would be sent:\n")
        for group, items in by_group.items():
            print(f"  [{group}] ({len(items)} members)")
            for item in items[:20]:
                m = item["member"]
                print(f"    {m['full_name']} <{m['email']}> (approved: {m['approved_at']})")
            if len(items) > 20:
                print(f"    ... and {len(items) - 20} more")
            print()
        return

    print(f"Sending {len(candidates)} campaign emails...\n")
    sent = 0
    failed = 0

    for c in candidates:
        member = c["member"]
        step = c["step"]
        campaign = c["campaign"]

        first_name = member["first_name"] or "there"

        # Load template
        template_path = SKILL_DIR / step["html_template"]
        html = template_path.read_text().replace("{first_name}", first_name)
        subject = step["subject_template"].replace("{first_name}", first_name)

        ok, result = send_email(env, member["email"], subject, html, tag=step["tag"])

        if ok:
            email_id = result.get("id")
            record_send(campaign["id"], step["step_number"], member["id"], member["email"], email_id)
            sent += 1
            print(f"  [{step['tag']}] Sent to {member['email']}")
        else:
            failed += 1
            print(f"  [{step['tag']}] FAILED {member['email']}: {result}")

        time.sleep(0.25)

    print(f"\nDone. Sent: {sent}, Failed: {failed}")


if __name__ == "__main__":
    main()
