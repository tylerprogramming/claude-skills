#!/usr/bin/env python3
"""
Creator HQ - Command Center renderer (pure view layer).

Reads the config + the yt-dlp snapshot + the hand-edited pipeline, computes the
weekly checkup, and bakes a fully self-contained dashboard.html (thumbnails
inlined as data URIs, no external requests - works offline on a Pi and passes
the Artifact CSP). Theme-aware (light + dark) with a swappable accent.

Writes two files:
  ~/creator-hq/dashboard.html          full standalone doc (Pi / kiosk / browser)
  ~/creator-hq/dashboard.artifact.html inner content only (for the Artifact tool)

Usage:
    python3 dashboard.py [config.json] [out.html] [accent] [theme]
      accent: indigo | violet | ocean | blue | coral   (default from config)
      theme:  light | dark | auto                       (default from config)
"""
import json
import sys
import base64
import datetime
from pathlib import Path

HOME = Path.home()
BASE = HOME / "creator-hq"
DATA_DIR = BASE / "data"

STAGES = ["idea", "scripted", "filmed", "editing", "ready"]
STAGE_LABEL = {"idea": "Ideas", "scripted": "Scripted", "filmed": "Filmed",
               "editing": "Editing", "ready": "Ready"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# ---- palettes --------------------------------------------------------------
# Accent is the brand pop; it stays consistent across light/dark. Semantic
# green/amber/red (on-track / partial / behind) are deliberately kept separate
# from the accent so status always reads the same.
ACCENTS = {
    "indigo": {"accent": "#4f46e5", "accent2": "#6366f1", "tint": "#4f46e5"},
    "violet": {"accent": "#7c3aed", "accent2": "#9061f9", "tint": "#7c3aed"},
    "ocean":  {"accent": "#0e7490", "accent2": "#0891b2", "tint": "#0e7490"},
    "blue":   {"accent": "#2563eb", "accent2": "#3b82f6", "tint": "#2563eb"},
    "coral":  {"accent": "#e0483d", "accent2": "#f0655b", "tint": "#e0483d"},
}

# Neutral grounds carry a faint bias toward the accent so they read as chosen,
# not defaulted. One entry per accent for each theme.
LIGHT = {
    "indigo": {"bg": "#f1f3fb", "panel": "#ffffff", "panel2": "#f5f7fd", "border": "#e2e7f4",
               "text": "#151a2b", "muted": "#586179", "dim": "#98a1b6"},
    "violet": {"bg": "#f6f3fb", "panel": "#ffffff", "panel2": "#f9f6fc", "border": "#ebe4f4",
               "text": "#1b1526", "muted": "#655a76", "dim": "#a598b4"},
    "ocean":  {"bg": "#eef5f6", "panel": "#ffffff", "panel2": "#f3f9f9", "border": "#dce8ea",
               "text": "#122023", "muted": "#4f6569", "dim": "#8ba3a6"},
    "blue":   {"bg": "#eff4fc", "panel": "#ffffff", "panel2": "#f4f8fd", "border": "#e0e9f6",
               "text": "#141b2a", "muted": "#556279", "dim": "#95a2b7"},
    "coral":  {"bg": "#faf3f1", "panel": "#ffffff", "panel2": "#fdf6f4", "border": "#f2e4df",
               "text": "#241715", "muted": "#6f5b56", "dim": "#b39d97"},
}
LIGHT_SEM = {"green": "#0f9d51", "amber": "#b7791f", "red": "#d9453b"}
LIGHT_SHADOW = "0 1px 2px rgba(30,40,70,.05), 0 8px 22px rgba(30,40,70,.06)"

DARK_BASE = {"bg": "#0b0f16", "panel": "#141a24", "panel2": "#0f151e", "border": "#252d3a",
             "text": "#e6edf3", "muted": "#8b98a9", "dim": "#5b6675"}
DARK_SEM = {"green": "#3fb950", "amber": "#d8a520", "red": "#f85149"}
DARK_SHADOW = "0 6px 22px rgba(0,0,0,.42)"


# ---- helpers ---------------------------------------------------------------
def fmt_num(n):
    if n is None:
        return "-"
    n = int(n)
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M".replace(".0M", "M")
    if n >= 100_000:
        return f"{n/1000:.0f}K"
    if n >= 1_000:
        return f"{n/1000:.1f}K".replace(".0K", "K")
    return f"{n:,}"


MILESTONES = [1000, 2500, 5000, 10000, 25000, 50000, 100000,
              250000, 500000, 1_000_000, 2_000_000, 5_000_000]


def milestone_sub(subs):
    if not subs:
        return ""
    for m in MILESTONES:
        if m > subs:
            return f"{m - subs:,} to {fmt_num(m)}"
    return f"{subs:,} strong"


def parse_ymd(s):
    if not s or len(str(s)) != 8:
        return None
    try:
        return datetime.date(int(s[0:4]), int(s[4:6]), int(s[6:8]))
    except ValueError:
        return None


def parse_iso(s):
    try:
        return datetime.date.fromisoformat(str(s)[:10])
    except (ValueError, TypeError):
        return None


def fmt_when(d, today):
    if not d:
        return ""
    delta = (today - d).days
    if delta == 0:
        return "today"
    if delta == 1:
        return "yesterday"
    if 0 < delta < 7:
        return f"{delta}d ago"
    return f"{MONTHS[d.month-1]} {d.day}"


def fmt_dur(sec):
    if not sec:
        return ""
    sec = int(sec)
    h, m, s = sec // 3600, (sec % 3600) // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def is_short(sec):
    return bool(sec) and int(sec) <= 180


def week_window(today, start="monday"):
    offset = today.weekday() if start == "monday" else (today.weekday() + 1) % 7
    ws = today - datetime.timedelta(days=offset)
    return ws, ws + datetime.timedelta(days=6)


def data_uri(rel):
    if not rel:
        return None
    p = DATA_DIR / rel
    if not p.exists():
        return None
    b = base64.b64encode(p.read_bytes()).decode()
    return f"data:image/jpeg;base64,{b}"


def sparkline(vals, w=150, h=40):
    vals = [v for v in vals if v is not None]
    if len(vals) < 2:
        return '<div class="spark-empty">not enough data yet</div>'
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1
    n = len(vals)
    pad = 3
    def x(i): return pad + i * (w - 2 * pad) / (n - 1)
    def y(v): return h - pad - (v - lo) / span * (h - 2 * pad)
    pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(vals))
    area = f"{pad},{h-pad} " + pts + f" {w-pad},{h-pad}"
    return (
        f'<svg class="spark" viewBox="0 0 {w} {h}" preserveAspectRatio="none">'
        f'<polygon points="{area}" fill="var(--accent)" opacity="0.13"/>'
        f'<polyline points="{pts}" fill="none" stroke="var(--accent)" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{x(n-1):.1f}" cy="{y(vals[-1]):.1f}" r="2.6" fill="var(--accent)"/>'
        f'</svg>'
    )


def esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# ---- components ------------------------------------------------------------
def checkup_card(label, count, goal):
    if count >= goal:
        var, icon, state = "var(--green)", "&#10003;", "met"
    elif count > 0:
        var, icon, state = "var(--amber)", "&#9679;", "partial"
    else:
        var, icon, state = "var(--red)", "&#10007;", "missed"
    return f'''
      <div class="chk chk-{state}" style="--c:{var}">
        <div class="chk-icon">{icon}</div>
        <div class="chk-body">
          <div class="chk-num">{count}<span class="chk-goal">/{goal}</span></div>
          <div class="chk-label">{label}</div>
        </div>
      </div>'''


def ready_card(count):
    var = "var(--green)" if count > 0 else "var(--dim)"
    return f'''
      <div class="chk chk-ready" style="--c:{var}">
        <div class="chk-icon">&#9650;</div>
        <div class="chk-body">
          <div class="chk-num">{count}</div>
          <div class="chk-label">ready to publish</div>
        </div>
      </div>'''


def kpi(label, value, sub="", spark=""):
    spark_html = f'<div class="kpi-spark">{spark}</div>' if spark else ""
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return f'''
      <div class="kpi">
        <div class="kpi-label">{label}</div>
        <div class="kpi-val">{value}</div>
        {sub_html}{spark_html}
      </div>'''


def video_card(v, today):
    uri = data_uri(v.get("thumb"))
    d = parse_ymd(v.get("upload_date"))
    badge = "SHORT" if is_short(v.get("duration")) else fmt_dur(v.get("duration"))
    if uri:
        thumb = f'<div class="vc-thumb" style="background-image:url({uri})">'
    else:
        thumb = '<div class="vc-thumb vc-thumb-empty">'
    dur_badge = f'<span class="vc-dur">{badge}</span>' if badge else ""
    likes = v.get("likes")
    likes_html = f'<span>&#9829; {fmt_num(likes)}</span>' if likes is not None else ""
    href = v.get("url") or "#"
    return f'''
      <a class="vc" href="{esc(href)}" target="_blank" rel="noopener">
        {thumb}{dur_badge}</div>
        <div class="vc-title">{esc(v.get("title"))}</div>
        <div class="vc-meta">
          <span class="vc-views">&#9654; {fmt_num(v.get("views"))}</span>
          {likes_html}
          <span class="vc-date">{fmt_when(d, today)}</span>
        </div>
      </a>'''


def pipeline_bar(pipe):
    counts = {s: 0 for s in STAGES}
    for item in pipe.get("videos", []):
        st = item.get("stage")
        if st in counts:
            counts[st] += 1
    chips = []
    for i, s in enumerate(STAGES):
        cls = "pchip pchip-ready" if s == "ready" else "pchip"
        chips.append(
            f'<div class="{cls}"><div class="pchip-n">{counts[s]}</div>'
            f'<div class="pchip-l">{STAGE_LABEL[s]}</div></div>'
        )
        if i < len(STAGES) - 1:
            chips.append('<div class="parrow">&#8250;</div>')
    total = sum(counts.values())
    return f'''
      <section class="panel pipeline">
        <div class="panel-h"><span>Pipeline</span><span class="panel-h-sub">{total} in production</span></div>
        <div class="pflow">{"".join(chips)}</div>
      </section>'''


# ---- css -------------------------------------------------------------------
def token_block(neutrals, sem, shadow, accent):
    toks = {**neutrals, **sem, "shadow": shadow,
            "accent": accent["accent"], "accent2": accent["accent2"]}
    return "".join(f"--{k}:{v};" for k, v in toks.items())


def build_css(accent_key, theme="auto"):
    acc = ACCENTS.get(accent_key, ACCENTS["indigo"])
    light = token_block(LIGHT.get(accent_key, LIGHT["indigo"]), LIGHT_SEM, LIGHT_SHADOW, acc)
    dark = token_block(DARK_BASE, DARK_SEM, DARK_SHADOW, acc)
    if theme == "light":
        roots = f':root {{ {light} }}'
    elif theme == "dark":
        roots = f':root {{ {dark} }}'
    else:  # auto: follow the viewer, honor an explicit data-theme toggle
        roots = (f':root {{ {light} }} '
                 f'@media (prefers-color-scheme:dark) {{ :root:not([data-theme]) {{ {dark} }} }} '
                 f':root[data-theme="dark"] {{ {dark} }} '
                 f':root[data-theme="light"] {{ {light} }}')
    return f'''
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  {roots}

  html,body {{ background:var(--bg); color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    -webkit-font-smoothing:antialiased; }}
  a {{ color:inherit; text-decoration:none; }}
  .wrap {{ max-width:1440px; margin:0 auto; padding:26px 30px 34px; }}

  .head {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:22px; }}
  .head-l {{ display:flex; align-items:center; gap:16px; }}
  .avatar {{ width:60px; height:60px; border-radius:16px; background-size:cover; background-position:center;
    border:1px solid var(--border); box-shadow:var(--shadow); }}
  .avatar-empty {{ background:linear-gradient(135deg,var(--accent),var(--accent2)); }}
  .head-title {{ font-size:30px; font-weight:800; letter-spacing:-.5px; }}
  .head-sub {{ color:var(--muted); font-size:15px; margin-top:3px; }}
  .head-r {{ text-align:right; }}
  .week {{ font-size:13px; text-transform:uppercase; letter-spacing:1.5px; color:var(--dim); }}
  .week-range {{ font-size:20px; font-weight:700; margin-top:2px; }}
  .live {{ display:flex; align-items:center; justify-content:flex-end; gap:7px; color:var(--dim);
    font-size:12.5px; margin-top:5px; }}
  .dot {{ width:8px; height:8px; border-radius:50%; background:var(--green);
    animation:pulse 2.4s infinite; }}
  @keyframes pulse {{ 0%{{box-shadow:0 0 0 0 color-mix(in srgb,var(--green) 55%,transparent)}}
    70%{{box-shadow:0 0 0 7px transparent}} 100%{{box-shadow:0 0 0 0 transparent}} }}

  .checkup {{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px; margin-bottom:16px; }}
  .chk {{ background:var(--panel); border:1px solid var(--border); border-radius:18px; padding:22px 24px;
    display:flex; align-items:center; gap:18px; position:relative; overflow:hidden; box-shadow:var(--shadow); }}
  .chk::before {{ content:""; position:absolute; left:0; top:0; bottom:0; width:5px; background:var(--c); }}
  .chk-icon {{ width:52px; height:52px; border-radius:14px; display:grid; place-items:center;
    font-size:24px; color:var(--c); background:color-mix(in srgb, var(--c) 15%, transparent); flex:none; }}
  .chk-num {{ font-size:40px; font-weight:800; line-height:1; letter-spacing:-1px; font-variant-numeric:tabular-nums; }}
  .chk-goal {{ font-size:22px; color:var(--dim); font-weight:700; }}
  .chk-label {{ color:var(--muted); font-size:14.5px; margin-top:6px; text-transform:capitalize; }}

  .kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:16px; }}
  .kpi {{ background:var(--panel); border:1px solid var(--border); border-radius:18px; padding:20px 22px;
    min-height:118px; display:flex; flex-direction:column; box-shadow:var(--shadow); }}
  .kpi-label {{ color:var(--muted); font-size:13px; text-transform:uppercase; letter-spacing:1.2px; }}
  .kpi-val {{ font-size:38px; font-weight:800; letter-spacing:-1px; margin-top:6px; font-variant-numeric:tabular-nums; }}
  .kpi-sub {{ color:var(--dim); font-size:13px; margin-top:auto; padding-top:8px; }}
  .kpi-spark {{ margin-top:auto; padding-top:10px; }}
  .spark {{ width:100%; height:40px; display:block; }}
  .spark-empty {{ color:var(--dim); font-size:12px; padding-top:14px; }}

  .panel {{ background:var(--panel); border:1px solid var(--border); border-radius:18px;
    padding:20px 22px; margin-bottom:16px; box-shadow:var(--shadow); }}
  .panel-h {{ display:flex; justify-content:space-between; align-items:baseline; margin-bottom:16px; }}
  .panel-h span:first-child {{ font-size:18px; font-weight:750; }}
  .panel-h-sub {{ color:var(--dim); font-size:13px; }}

  .vgrid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:16px; }}
  .vc {{ display:flex; flex-direction:column; background:var(--panel2); border:1px solid var(--border);
    border-radius:14px; overflow:hidden; transition:transform .12s, border-color .12s; }}
  .vc:hover {{ transform:translateY(-3px); border-color:var(--accent); }}
  .vc-thumb {{ aspect-ratio:16/9; background-size:cover; background-position:center; position:relative; }}
  .vc-thumb-empty {{ background:linear-gradient(135deg,var(--accent),var(--accent2)); opacity:.5; }}
  .vc-dur {{ position:absolute; right:7px; bottom:7px; background:rgba(0,0,0,.82); color:#fff;
    font-size:11.5px; font-weight:700; padding:2px 7px; border-radius:6px; letter-spacing:.3px; }}
  .vc-title {{ font-size:14px; font-weight:650; line-height:1.32; padding:11px 12px 8px;
    display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; min-height:52px; }}
  .vc-meta {{ display:flex; gap:12px; align-items:center; padding:0 12px 12px; color:var(--muted); font-size:12.5px; }}
  .vc-views {{ color:var(--accent); font-weight:700; }}
  .vc-date {{ margin-left:auto; color:var(--dim); }}

  .pflow {{ display:flex; align-items:stretch; gap:8px; }}
  .pchip {{ flex:1; background:var(--panel2); border:1px solid var(--border); border-radius:12px;
    padding:16px 10px; text-align:center; }}
  .pchip-ready {{ border-color:var(--green); background:color-mix(in srgb, var(--green) 12%, var(--panel2)); }}
  .pchip-n {{ font-size:28px; font-weight:800; font-variant-numeric:tabular-nums; }}
  .pchip-ready .pchip-n {{ color:var(--green); }}
  .pchip-l {{ color:var(--muted); font-size:12.5px; margin-top:4px; text-transform:uppercase; letter-spacing:.8px; }}
  .parrow {{ display:grid; place-items:center; color:var(--dim); font-size:22px; }}

  .foot {{ text-align:center; color:var(--dim); font-size:12.5px; margin-top:8px; }}

  @media (max-width:1000px) {{
    .checkup, .kpis {{ grid-template-columns:repeat(2,1fr); }}
    .vgrid {{ grid-template-columns:repeat(2,1fr); }}
  }}
  @media (prefers-reduced-motion:reduce) {{ .dot {{ animation:none; }} .vc {{ transition:none; }} }}
</style>'''


# ---- render ----------------------------------------------------------------
def render(cfg, snap, pipe, accent_key):
    today = datetime.date.today()
    goals = cfg.get("goals", {})
    g_create = int(goals.get("create_per_week", 2))
    g_release = int(goals.get("release_per_week", 2))
    ws, we = week_window(today, cfg.get("week_start", "monday"))

    creators = snap.get("creators", [])
    c = creators[0] if creators else {"name": "Your channel", "videos": []}
    vids = c.get("videos", [])

    released = sum(1 for v in vids if (d := parse_ymd(v.get("upload_date"))) and ws <= d <= we)
    created = 0
    for item in pipe.get("videos", []):
        d = parse_iso(item.get("filmed"))
        if d and ws <= d <= we:
            created += 1
    ready_count = sum(1 for item in pipe.get("videos", []) if item.get("stage") == "ready")

    view_vals = [v.get("views") for v in vids if v.get("views") is not None]
    avg_views = round(sum(view_vals) / len(view_vals)) if view_vals else None
    dated = sorted(
        [v for v in vids if parse_ymd(v.get("upload_date")) and v.get("views") is not None],
        key=lambda v: v["upload_date"],
    )
    spark_vals = [v["views"] for v in dated[-8:]]
    top = max(vids, key=lambda v: v.get("views") or -1, default=None)
    last30 = sum(1 for v in vids if (d := parse_ymd(v.get("upload_date"))) and (today - d).days <= 30)

    avatar = data_uri(c.get("avatar"))
    avatar_html = (f'<div class="avatar" style="background-image:url({avatar})"></div>'
                   if avatar else '<div class="avatar avatar-empty"></div>')
    week_label = f"{MONTHS[ws.month-1]} {ws.day} &ndash; {MONTHS[we.month-1]} {we.day}"
    fetched = snap.get("fetched_at", "")[:16].replace("T", " ")
    cards = "".join(video_card(v, today) for v in vids[:4])
    top_val = fmt_num(top.get("views")) if top else "-"
    top_sub = esc((top.get("title") or "")[:34]) if top else ""

    body = f'''
  <div class="wrap">
    <header class="head">
      <div class="head-l">
        {avatar_html}
        <div>
          <div class="head-title">Creator HQ</div>
          <div class="head-sub">{esc(c.get("name"))} &middot; {fmt_num(c.get("subs"))} subscribers</div>
        </div>
      </div>
      <div class="head-r">
        <div class="week">This week</div>
        <div class="week-range">{week_label}</div>
        <div class="live"><span class="dot"></span>updated {fetched}</div>
      </div>
    </header>

    <section class="checkup">
      {checkup_card("videos created", created, g_create)}
      {checkup_card("videos released", released, g_release)}
      {ready_card(ready_count)}
    </section>

    <section class="kpis">
      {kpi("Subscribers", fmt_num(c.get("subs")), milestone_sub(c.get("subs")))}
      {kpi("Total videos", fmt_num(c.get("total_videos")), f"{last30} in last 30 days")}
      {kpi("Avg views", fmt_num(avg_views), f"last {len(view_vals)} uploads", sparkline(spark_vals))}
      {kpi("Top recent", top_val, top_sub)}
    </section>

    <section class="panel recent">
      <div class="panel-h"><span>Recent uploads</span><span class="panel-h-sub">newest first</span></div>
      <div class="vgrid">{cards}</div>
    </section>

    {pipeline_bar(pipe)}

    <footer class="foot">Creator HQ &middot; auto-pulled from YouTube &middot; goals: {g_create} created / {g_release} released per week</footer>
  </div>'''

    return build_css(accent_key), body


def main():
    cfg_path = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "config.json"
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else BASE / "dashboard.html"
    cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
    accent = sys.argv[3] if len(sys.argv) > 3 else cfg.get("accent", "indigo")
    theme = sys.argv[4] if len(sys.argv) > 4 else cfg.get("theme", "auto")

    snap_path = DATA_DIR / "youtube.json"
    snap = json.loads(snap_path.read_text()) if snap_path.exists() else {"creators": []}
    pipe_path = BASE / "pipeline.json"
    pipe = json.loads(pipe_path.read_text()) if pipe_path.exists() else {"videos": []}

    css, body = render(cfg, snap, pipe, accent)
    theme_attr = f' data-theme="{theme}"' if theme in ("light", "dark") else ""

    full = (
        f'<!doctype html><html lang="en"{theme_attr}><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
        '<meta http-equiv="refresh" content="900">'
        '<title>Creator HQ</title>' + css + '</head><body>' + body + '</body></html>'
    )
    out_path.write_text(full)
    (BASE / "dashboard.artifact.html").write_text("<title>Creator HQ</title>" + css + body)
    print(f"Wrote {out_path}  (accent={accent}, theme={theme})")
    print(f"Wrote {BASE / 'dashboard.artifact.html'}")


if __name__ == "__main__":
    main()
