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
# You do not have to keep these skills in ~/.claude/skills. Clone this anywhere
# and copy over the ones you want. The venv just has to sit at or above wherever
# the skill ended up, so point this script at that folder:
#
#   ./setup.sh                      venv next to this script
#   ./setup.sh ~/.claude/skills     venv in your own skills folder instead
#   ./setup.sh --link ~/.claude/skills
#                                   reuse the venv this script already built,
#                                   no second few-hundred-MB download
#   ./setup.sh --check [dir]        report what is missing, change nothing
#   ./setup.sh --rebuild [dir]      throw the venv away and build it clean
#
# Versions come from requirements.txt, pinned exactly. This environment lives on
# two Macs and "works on the laptop, not the desktop" is a debugging session
# nobody wants, so a fresh install six months from now resolves the same wheels
# rather than whatever is newest.
set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

LINK=0
[ "${1:-}" = "--link" ] && { LINK=1; shift; }
MODE=""
[ "${1:-}" = "--check" ] && { MODE="check"; shift; }
[ "${1:-}" = "--rebuild" ] && { MODE="rebuild"; shift; }

TARGET="${1:-$DIR}"
mkdir -p "$TARGET" 2>/dev/null
TARGET="$(cd "$TARGET" && pwd)" || { echo "  no such folder: ${1:-}" >&2; exit 1; }
VENV="$TARGET/.venv"

# Package versions live in requirements.txt, not here. One list, pinned, and it
# is the thing a fresh machine reproduces from.
REQ="$DIR/requirements.txt"

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
    say "packages  : all ${#MODULES[@]} import cleanly"
  else
    say "packages  : MISSING ${missing[*]}"
    say "            run ./setup.sh to install them"
    return 1
  fi
}

[ "$MODE" = "check" ] && { check; exit $?; }

if [ "$LINK" = "1" ]; then
  [ -x "$DIR/.venv/bin/python3" ] || die "no venv here yet. run ./setup.sh first, then --link"
  [ "$VENV" = "$DIR/.venv" ] && die "that is where the venv already is"
  [ -e "$VENV" ] && die "$VENV already exists. remove it first if you want to relink"
  ln -s "$DIR/.venv" "$VENV"
  say "linked $VENV -> $DIR/.venv"
  check
  exit $?
fi

[ -f "$REQ" ] || die "requirements.txt is missing next to this script"

# uv if it is here: it resolves in seconds, and it builds an isolated venv rather
# than negotiating with a Homebrew python that marks itself externally managed
# (PEP 668). The pip path below still works; it is just slower and noisier.
if command -v uv >/dev/null 2>&1; then
  if [ "$MODE" = "rebuild" ] || [ ! -x "$VENV/bin/python3" ]; then
    say "creating $VENV with uv"
    uv venv ${MODE:+--clear} "$VENV" >/dev/null || die "uv could not create the venv"
  else
    say "using existing $VENV ($("$VENV/bin/python3" --version))"
  fi
  say "syncing packages from requirements.txt"
  uv pip install --quiet --python "$VENV/bin/python3" -r "$REQ" || die "uv pip install failed"
else
  say "uv not found, using pip. uv is one command and much faster:"
  say "    curl -LsSf https://astral.sh/uv/install.sh | sh"
  command -v python3 >/dev/null 2>&1 || die "python3 not found"

  # 3.10+ because several of these packages dropped older versions
  py_ok=$(python3 -c 'import sys; print(1 if sys.version_info >= (3,10) else 0)')
  [ "$py_ok" = "1" ] || die "python3 is $(python3 -c 'import sys;print(".".join(map(str,sys.version_info[:3])))'), need 3.10 or newer"

  if [ "$MODE" = "rebuild" ] && [ -d "$VENV" ]; then rm -rf "$VENV"; fi
  if [ ! -x "$VENV/bin/python3" ]; then
    say "creating $VENV with $(python3 --version)"
    python3 -m venv "$VENV" || die "could not create the venv"
  fi

  say "installing packages (a few hundred MB, once)"
  "$VENV/bin/pip" install --quiet --upgrade pip >/dev/null 2>&1
  "$VENV/bin/pip" install --quiet -r "$REQ" || die "pip install failed"
fi

# Playwright is two installs: the package, and the browser it drives. With only
# the package you get an import that succeeds and a first call that fails, which
# reads as a bug in the skill rather than a missing download.
if "$VENV/bin/python3" -c "import playwright" 2>/dev/null; then
  "$VENV/bin/python3" -m playwright install chromium >/dev/null 2>&1 \
    || say "note: chromium download failed. /tiktok-replier will not run until it succeeds"
fi

say "verifying"
check || die "some packages did not import after install"

echo
say "done. The scripts find this automatically, so nothing else to configure."
say "Secrets are separate: see 'Secrets & Per-User Setup' in the README."
