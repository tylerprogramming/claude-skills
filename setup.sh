#!/usr/bin/env bash
# Build the shared python environment these skills run in.
#
# Why this exists: every python script here starts `#!/usr/bin/env python3`,
# and `python3` is a moving target. A Homebrew upgrade re-points it, the
# packages installed for the old version stop being visible, and the scripts
# fail with ModuleNotFoundError while looking perfectly installed. That is not
# hypothetical - it silently broke /yt-upload, /yt-replier, /yt-analytics,
# /gmail, and /creator-hq when python3 moved from 3.9 to 3.14.
#
# So the scripts do not trust `python3`. Each one re-execs under the venv this
# script builds. Run it once after cloning, and again if you ever delete .venv.
#
#   ./setup.sh          create the venv and install everything
#   ./setup.sh --check  report what is missing without changing anything
set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$DIR/.venv"

# Every third-party import across the skills, as pip package names.
PACKAGES=(
  google-api-python-client google-auth-oauthlib google-auth-httplib2  # yt-upload, yt-replier, yt-analytics, gmail, creator-hq
  Pillow                                                              # flash-video, instagram-writer
  numpy                                                               # harut, instagram-writer
  openai                                                              # harut, transcribe
  resend                                                              # email
  icalendar                                                           # lifestyle
  certifi                                                             # _kie
  playwright                                                          # tiktok-replier
)

# module name -> what to import, for verification
MODULES=(googleapiclient google_auth_oauthlib google PIL numpy openai resend icalendar certifi playwright)

say() { printf "  %s\n" "$*"; }
die() { printf "\n  %s\n\n" "$*" >&2; exit 1; }

check() {
  if [ ! -x "$VENV/bin/python3" ]; then
    say "venv      : missing. run ./setup.sh"
    return 1
  fi
  say "venv      : $("$VENV/bin/python3" --version)"
  local missing=()
  for m in "${MODULES[@]}"; do
    "$VENV/bin/python3" -c "import $m" 2>/dev/null || missing+=("$m")
  done
  if [ ${#missing[@]} -eq 0 ]; then
    say "packages  : all ${#MODULES[@]} present"
  else
    say "packages  : MISSING ${missing[*]}"
    say "            run ./setup.sh to install them"
    return 1
  fi
}

[ "${1:-}" = "--check" ] && { check; exit $?; }

command -v python3 >/dev/null 2>&1 || die "python3 not found"

# 3.10+ because several of these packages dropped older versions
py_ok=$(python3 -c 'import sys; print(1 if sys.version_info >= (3,10) else 0)')
[ "$py_ok" = "1" ] || die "python3 is $(python3 -c 'import sys;print(".".join(map(str,sys.version_info[:3])))'), need 3.10 or newer"

say "creating .venv with $(python3 --version)"
python3 -m venv "$VENV" || die "could not create the venv"

say "installing ${#PACKAGES[@]} packages (a few hundred MB, once)"
"$VENV/bin/pip" install --quiet --upgrade pip >/dev/null 2>&1
"$VENV/bin/pip" install --quiet "${PACKAGES[@]}" || die "pip install failed"

say "verifying"
check || die "some packages did not import after install"

echo
say "done. The scripts find this automatically, so nothing else to configure."
say "Secrets are separate: see 'Secrets & Per-User Setup' in the README."
