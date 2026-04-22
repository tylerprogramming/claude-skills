#!/usr/bin/env python3
"""
Gmail API client for Claude Code /gmail skill.
Uses OAuth2 — on first run, opens browser to authorize. Token is cached.
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

# Auto-install dependencies
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
                           "google-auth-oauthlib", "google-api-python-client"])
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDS_DIR = Path.home() / ".claude" / "gmail"
CREDS_FILE = CREDS_DIR / "credentials.json"
TOKEN_FILE = CREDS_DIR / "token.json"


def get_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDS_FILE.exists():
                print(f"ERROR: credentials.json not found at {CREDS_FILE}", file=sys.stderr)
                print("Setup: Download OAuth2 credentials from Google Cloud Console → save as ~/.claude/gmail/credentials.json", file=sys.stderr)
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        CREDS_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def decode_body(payload):
    """Recursively extract plain text body from a message payload."""
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    if payload.get("mimeType") == "text/html":
        data = payload.get("body", {}).get("data", "")
        if data:
            # Return raw HTML as fallback — Claude can parse it
            return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        result = decode_body(part)
        if result:
            return result
    return ""


def header(msg, name):
    for h in msg.get("payload", {}).get("headers", []):
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def cmd_search(service, query, max_results, include_body):
    results = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        print(json.dumps({"results": [], "query": query}))
        return

    output = []
    for m in messages:
        msg = service.users().messages().get(
            userId="me", id=m["id"],
            format="full" if include_body else "metadata",
            metadataHeaders=["From", "To", "Subject", "Date"]
        ).execute()

        entry = {
            "id": msg["id"],
            "threadId": msg["threadId"],
            "from": header(msg, "From"),
            "to": header(msg, "To"),
            "subject": header(msg, "Subject"),
            "date": header(msg, "Date"),
            "snippet": msg.get("snippet", ""),
            "labelIds": msg.get("labelIds", []),
        }
        if include_body:
            entry["body"] = decode_body(msg.get("payload", {}))[:4000]  # cap at 4k chars

        output.append(entry)

    print(json.dumps({"results": output, "query": query, "total": len(output)}, indent=2))


def cmd_read(service, msg_id):
    msg = service.users().messages().get(
        userId="me", id=msg_id, format="full"
    ).execute()

    output = {
        "id": msg["id"],
        "threadId": msg["threadId"],
        "from": header(msg, "From"),
        "to": header(msg, "To"),
        "subject": header(msg, "Subject"),
        "date": header(msg, "Date"),
        "snippet": msg.get("snippet", ""),
        "labelIds": msg.get("labelIds", []),
        "body": decode_body(msg.get("payload", {})),
    }
    print(json.dumps(output, indent=2))


def cmd_thread(service, thread_id):
    thread = service.users().threads().get(
        userId="me", id=thread_id, format="full"
    ).execute()

    messages = []
    for msg in thread.get("messages", []):
        messages.append({
            "id": msg["id"],
            "from": header(msg, "From"),
            "date": header(msg, "Date"),
            "snippet": msg.get("snippet", ""),
            "body": decode_body(msg.get("payload", {}))[:3000],
        })

    print(json.dumps({
        "threadId": thread_id,
        "subject": header(thread["messages"][0], "Subject") if thread.get("messages") else "",
        "messages": messages,
    }, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Gmail API client")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # search
    s = sub.add_parser("search", help="Search emails")
    s.add_argument("query", help="Gmail search query (same syntax as Gmail search bar)")
    s.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")
    s.add_argument("--body", action="store_true", help="Include email body in results")

    # read
    r = sub.add_parser("read", help="Read a single email by ID")
    r.add_argument("id", help="Message ID")

    # thread
    t = sub.add_parser("thread", help="Read a full email thread")
    t.add_argument("id", help="Thread ID")

    args = parser.parse_args()
    service = get_service()

    if args.cmd == "search":
        cmd_search(service, args.query, args.limit, args.body)
    elif args.cmd == "read":
        cmd_read(service, args.id)
    elif args.cmd == "thread":
        cmd_thread(service, args.id)


if __name__ == "__main__":
    main()
