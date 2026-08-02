"""
Self-contained YouTube OAuth for the yt-replier skill.

Reuses Tyler's existing Google OAuth client at ~/credentials.json (the same
desktop client the Drive/Gmail/youtube skills use), but stores its own token
inside this skill folder so yt-replier has no dependency on any other skill.

Scopes: youtube.force-ssl (read comment threads + post replies).
First run opens a browser to authorize; the token is cached after that.
"""


from __future__ import annotations

# --- skills venv bootstrap: run under .venv, not whatever python3 resolves to.
# Looks for .venv beside this script and up a few levels, then ~/.claude/skills,
# so a skill works wherever you copied it. Compares realpaths, and re-execs at
# most once, because a symlinked path that never compares equal would otherwise
# loop forever. Rationale: "Why there is a venv" in README.md
import os as _os, sys as _sys
if not _os.environ.get("SKILLS_VENV"):
    _base = _os.path.dirname(_os.path.abspath(__file__))
    for _v in [_os.path.realpath(_os.path.join(_base, *([".."] * _i), ".venv")) for _i in range(4)
               ] + [_os.path.realpath(_os.path.expanduser("~/.claude/skills/.venv"))]:
        if _os.path.exists(_os.path.join(_v, "bin", "python3")):
            if _os.path.realpath(_sys.prefix) != _v:
                _os.environ["SKILLS_VENV"] = _v
                _os.execv(_os.path.join(_v, "bin", "python3"),
                          [_os.path.join(_v, "bin", "python3"), *_sys.argv])
            break
# --- end bootstrap ---------------------------------------------------------

import os
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Reading comment threads and posting replies both fall under force-ssl.
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
CREDS_PATH = os.path.expanduser("~/credentials.json")
TOKEN_PATH = str(Path(__file__).parent / "token.json")


def get_creds(force_reauth: bool = False) -> Credentials:
    creds = None
    if not force_reauth and os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token and not force_reauth:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Refresh failed ({e}), re-running browser auth.", file=sys.stderr)
                creds = None
        if not creds:
            if not os.path.exists(CREDS_PATH):
                sys.exit(
                    f"Missing OAuth client at {CREDS_PATH}. "
                    "Download it from Google Cloud Console and try again."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        Path(TOKEN_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return creds


def get_service():
    return build("youtube", "v3", credentials=get_creds(), cache_discovery=False)


if __name__ == "__main__":
    force = "--reauth" in sys.argv
    creds = get_creds(force_reauth=force)
    print(f"Authenticated. Token saved to {TOKEN_PATH}")
    print(f"Scopes: {', '.join(creds.scopes or SCOPES)}")
