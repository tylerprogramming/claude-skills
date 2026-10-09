#!/usr/bin/env python3
"""The 0:46 "hard part / what works now" beat, built on the registry's code-scroll block.

  npx hyperframes add code-scroll --dir overlays/build/cs

That block animates a scroll down to a target line. Perfect for this beat: scroll through
all the OAuth plumbing you used to write, and land on the one Claude Code command that
replaces it.

The block renders from window.__TOKENS.scroll.states[0].tokens - a flat list of
{key, content, color} with "\\n" as line breaks, normally baked by their Shiki tooling.
There is no authoring CLI here, so this generates the token list directly with a small
tokenizer; the engine only needs content + colour.

Output: overlays/hardpart.mp4 (opaque full-frame cutaway)
"""
import json, os, re, subprocess

BASE = os.path.expanduser("~/Movies/Camtasia/047 - arcade.dev full course")
SRC  = os.path.join(BASE, "overlays/build/cs/compositions/code-scroll.html")
BUILD= os.path.join(BASE, "overlays/build/hardscroll")
OUT  = os.path.join(BASE, "overlays/hardpart.mp4")
FPS, DUR = 30, 4.20
TARGET_LINE = 25          # the claude mcp add line

CODE = '''# the old way: wire up every app yourself
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive.file",
]

def get_credentials(user_id):
    creds = load_token(user_id)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            "client_secret.json", SCOPES)
        creds = flow.run_local_server(port=0)
        save_token(user_id, creds)
    return creds

# ...then repeat all of it for Slack, for ClickUp,
# for every user, every seven days.

# what actually works now
claude mcp add --transport http arcade \\
    https://api.arcade.dev/mcp/multi-tool'''

KW = {"from","import","def","if","not","or","and","return","for","in","None","True","False"}
C_KW, C_STR, C_COM, C_FN, C_NUM, C_DEF, C_HI = (
    "#F97583","#9ECBFF","#6A737D","#B392F0","#79B8FF","#E1E4E8","#46E5B7")

def tokenize(code):
    toks, k = [], 0
    for lineno, line in enumerate(code.split("\n"), start=1):
        hot = lineno >= TARGET_LINE            # the payoff lines glow
        if line.lstrip().startswith("#"):
            toks.append({"key":f"t{k}","content":line,"color":C_COM}); k+=1
        else:
            for m in re.finditer(r'("[^"]*"|\'[^\']*\'|\b\w+\b|\s+|.)', line):
                t = m.group(0)
                if not t: continue
                if t.strip()=="" : col = C_DEF
                elif t[0] in "\"'": col = C_STR
                elif t in KW: col = C_KW
                elif re.fullmatch(r"\d+", t): col = C_NUM
                elif re.fullmatch(r"[A-Za-z_]\w*", t) and t[0].isupper(): col = C_FN
                else: col = C_DEF
                if hot and t.strip(): col = C_HI
                toks.append({"key":f"t{k}","content":t,"color":col}); k+=1
        toks.append({"key":f"n{k}","content":"\n","color":C_DEF}); k+=1
    return toks

if __name__ == "__main__":
    os.makedirs(BUILD, exist_ok=True)
    html = open(SRC).read()
    state = {"code": CODE, "tokens": tokenize(CODE)}
    payload = {"scroll": {"lang":"py","theme":"github-dark","bg":"#0b1216","fg":"#e1e4e8",
                          "states":[state]}}
    # re.sub processes backslash escapes in a REPLACEMENT STRING, so json's \\n would be
    # turned into real newlines inside a JS string literal and break the whole script.
    # Pass a callable instead - its return value is used verbatim.
    tok_js = "window.__TOKENS = " + json.dumps(payload) + ";"
    html = re.sub(r"window\.__TOKENS\s*=\s*\{.*?\n      \};",
                  lambda m: tok_js, html, count=1, flags=re.S)
    blk_js = ('window.__BLOCK = {id:"code-scroll",effect:"scroll",seq:"scroll",'
              f'line:{TARGET_LINE},duration:{DUR}}};')
    html = re.sub(r"window\.__BLOCK\s*=\s*\{.*?\};", lambda m: blk_js, html,
                  count=1, flags=re.S)
    html = html.replace('data-duration="6"', f'data-duration="{DUR}"')
    html = re.sub(r'<span class="accent">[^<]*</span> — Code Scroll To Line',
                  '<span class="accent">auth.py</span> — the part you no longer write', html)
    open(os.path.join(BUILD,"index.html"),"w").write(html)
    env = dict(os.environ, PRODUCER_BROWSER_GPU_MODE="hardware")
    subprocess.run(["hyperframes","render",BUILD,"-o",OUT,"--format","mp4",
                    "--fps",str(FPS),"--quiet"], env=env, check=True,
                   capture_output=True, text=True)
    print("->", OUT)
