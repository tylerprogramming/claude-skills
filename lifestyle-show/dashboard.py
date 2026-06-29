#!/usr/bin/env python3
"""
Lifestyle OS dashboard renderer.

Pure view layer: reads a compact JSON snapshot (produced by dashboard.sql run
through the Supabase MCP) and writes a single self-contained dashboard.html.
No database access, no secrets - the data is baked in at generation time.

Usage:
    python dashboard.py [data.json] [out.html]

Defaults:
    data.json -> ~/lifestyle/data/dashboard-data.json
    out.html  -> ~/lifestyle/dashboard.html

Regenerate flow (handled by the /lifestyle-show skill):
    1. Run dashboard.sql via the Supabase MCP (the "lifestyle" project).
    2. Write the returned payload object to the data.json path.
    3. Run this script.
"""
import json
import math
import os
import sys
from datetime import date, datetime, timedelta

HOME = os.path.expanduser("~")
DATA = sys.argv[1] if len(sys.argv) > 1 else f"{HOME}/lifestyle/data/dashboard-data.json"
OUT = sys.argv[2] if len(sys.argv) > 2 else f"{HOME}/lifestyle/dashboard.html"

# Targets (mirror user_fitness_profile). Adjust here if they change.
CAL_TARGET = 2100
PROTEIN_TARGET = 180
WATER_GOAL = 100
WEIGHT_GOAL = 180.0
GRID_WEEKS = 27
CONSISTENCY_WINDOW = 30

LEVEL_COLORS = ["#1b1f27", "#0e4429", "#006d32", "#26a641", "#39d353"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
GREEN, AMBER, RED, BLUE, PURPLE = "#39d353", "#e3b341", "#f85149", "#58a6ff", "#cba6f7"


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def pace(sec):
    if not sec:
        return "-"
    return f"{int(sec) // 60}'{int(sec) % 60:02d}\""


def level_for(x):
    if not x:
        return 0
    acts = (1 if x.get("run") else 0) + (1 if x.get("lift") else 0)
    dist = x.get("dist") or 0
    if x.get("pr") or dist >= 6 or acts >= 2:
        return 4
    if acts == 1 and dist >= 4:
        return 3
    if acts == 1:
        return 2
    return 1  # logged a day (ate well / rest) but no workout


def sunday_of(dt):
    return dt - timedelta(days=(dt.weekday() + 1) % 7)


def spark_line(vals, w=190, h=38, color=GREEN, pad=4):
    vals = [v for v in vals if v is not None]
    if len(vals) < 2:
        return '<div class="spark-empty">not enough data yet</div>'
    mn, mx = min(vals), max(vals)
    rng = (mx - mn) or 1
    n = len(vals)
    pts = [(pad + i / (n - 1) * (w - 2 * pad), pad + (1 - (v - mn) / rng) * (h - 2 * pad))
           for i, v in enumerate(vals)]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = poly + f" {pts[-1][0]:.1f},{h} {pts[0][0]:.1f},{h}"
    ex, ey = pts[-1]
    return (f'<svg class="spark" viewBox="0 0 {w} {h}" preserveAspectRatio="none">'
            f'<polygon points="{area}" fill="{color}" opacity="0.10"/>'
            f'<polyline points="{poly}" fill="none" stroke="{color}" stroke-width="2" '
            f'stroke-linejoin="round" stroke-linecap="round"/>'
            f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="2.6" fill="{color}"/></svg>')


def spark_bars(pairs, w=190, h=38, color=GREEN, pad=2):
    vals = [v for _, v in pairs]
    if not vals:
        return '<div class="spark-empty">not enough data yet</div>'
    mx = max(vals) or 1
    n = len(vals)
    bw = (w - (n + 1) * pad) / n
    rects = []
    for i, (lab, v) in enumerate(pairs):
        bh = (v / mx) * (h - 2)
        x = pad + i * (bw + pad)
        rects.append(f'<rect x="{x:.1f}" y="{h - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
                     f'rx="1.5" fill="{color}"><title>{esc(lab)}: {v} mi</title></rect>')
    return f'<svg class="spark" viewBox="0 0 {w} {h}">{"".join(rects)}</svg>'


def ring(pct, size=92, stroke=9):
    color = GREEN if pct >= 70 else AMBER if pct >= 40 else RED
    r = (size - stroke) / 2
    circ = 2 * math.pi * r
    off = circ * (1 - pct / 100)
    c = size / 2
    return f'''<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" class="ring">
      <circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="#21262d" stroke-width="{stroke}"/>
      <circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="{color}" stroke-width="{stroke}"
        stroke-linecap="round" stroke-dasharray="{circ:.1f}" stroke-dashoffset="{off:.1f}"
        transform="rotate(-90 {c} {c})"/>
      <text x="{c}" y="{c}" text-anchor="middle" dominant-baseline="central" class="ring-t">{pct}<tspan class="ring-p">%</tspan></text>
    </svg>'''


def main():
    with open(DATA) as f:
        d = json.load(f)

    today = date.fromisoformat(d["today"])
    days = {x["date"]: x for x in d.get("days", [])}

    # ---- streaks + consistency (a day counts if it has a run or a lift) ----
    active = sorted(date.fromisoformat(k) for k, v in days.items()
                    if v.get("run") or v.get("lift"))
    active_set = set(active)
    streak, last_active, days_since = 0, None, None
    if active:
        last_active = active[-1]
        c = last_active
        while c in active_set:
            streak += 1
            c -= timedelta(days=1)
        days_since = (today - last_active).days
    best = 0
    for dt in active:
        if (dt - timedelta(days=1)) not in active_set:
            s, c = 0, dt
            while c in active_set:
                s += 1
                c += timedelta(days=1)
            best = max(best, s)
    win_active = sum(1 for i in range(CONSISTENCY_WINDOW)
                     if (today - timedelta(days=i)) in active_set)
    consistency = round(win_active / CONSISTENCY_WINDOW * 100)

    # ---- grid ----
    end_week = sunday_of(today)
    start_week = end_week - timedelta(weeks=GRID_WEEKS - 1)
    weeks = []
    cur = start_week
    while cur <= end_week:
        weeks.append([cur + timedelta(days=i) for i in range(7)])
        cur += timedelta(weeks=1)
    month_labels, last_month = [], None
    for wi, wk in enumerate(weeks):
        if wk[0].month != last_month:
            # skip crowded labels (<3 cols apart); a leading 1-week sliver yields to the next month
            if month_labels and wi - month_labels[-1][0] < 3:
                if month_labels[-1][0] == 0:
                    month_labels[-1] = (wi, MONTHS[wk[0].month - 1])
            else:
                month_labels.append((wi, MONTHS[wk[0].month - 1]))
            last_month = wk[0].month
    cells = []
    for wk in weeks:
        col = []
        for dt in wk:
            rec = days.get(dt.isoformat())
            future = dt > today
            lv = 0 if future else level_for(rec)
            if future:
                title = ""
            elif rec:
                bits = []
                if rec.get("run"):
                    bits.append(f"run {rec['dist']} mi" if rec.get("dist") else "run")
                if rec.get("lift"):
                    bits.append("lift")
                if rec.get("ate_well"):
                    bits.append("ate well")
                if rec.get("pr"):
                    bits.append("PR")
                title = f"{dt.strftime('%b %d')}: " + (", ".join(bits) if bits else "logged")
            else:
                title = f"{dt.strftime('%b %d')}: nothing logged"
            col.append((lv, title, future, dt == today))
        cells.append(col)

    f_ = d.get("fitness") or {}
    c_ = d.get("content") or {}
    rd = d.get("reading") or {}
    b = d.get("business") or {}
    ts = d.get("today_strip") or {}
    tr = d.get("trends") or {}
    ll = d.get("last_logged") or {}
    lr = f_.get("last_run") or {}
    wt = f_.get("weight") or {}

    def days_ago(dstr):
        return (today - date.fromisoformat(dstr)).days if dstr else None

    # ---- nudges (#5) ----
    nudges = []
    gc = days_ago(ll.get("checkin"))
    if ts.get("checkin_today"):
        nudges.append(("ok", "Check-in logged today. The keystone is green."))
    elif gc is None or gc >= 3:
        nudges.append(("warn", f"Check-in is the canary &mdash; "
                       f"{gc if gc is not None else 'no'} days since the last one. Log one tonight."
                       .replace("&mdash;", "-")))
    else:
        nudges.append(("idle", f"Last check-in {gc}d ago. Close today's loop tonight."))
    gw = days_ago(ll.get("weigh_in"))
    if gw is not None and gw >= 7:
        nudges.append(("warn", f"No weigh-in for {gw} days. Sunday is weigh-in day - step on the scale."))
    gr = days_ago(ll.get("reading"))
    if gr is None or gr >= 3:
        nudges.append(("idle", f"Reading has been quiet {gr if gr is not None else 'a while'}d - "
                               f"a few pages tonight restarts the streak."))
    gl = days_ago(ll.get("lift"))
    if gl is not None and gl >= 7:
        nudges.append(("idle", f"Last strength day was {gl} days ago - work a lift back in."))
    if days_since and days_since >= 2:
        nudges.insert(0, ("warn", f"{days_since} days since your last run or lift - "
                                  f"get one in to restart the streak (best was {best})."))

    weight_line = "-"
    if wt.get("weight_lb") is not None:
        togo = float(wt["weight_lb"]) - WEIGHT_GOAL
        weight_line = f"{wt['weight_lb']} lb"
        if togo > 0:
            weight_line += f" &middot; {togo:.1f} to goal"

    # ---------- grid html (float-free: day column + [months row over cols]) ----------
    labels_by_week = {wi: name for wi, name in month_labels}
    g = ['<div class="cal"><div class="cal-day">']
    for lab in ["", "Mon", "", "Wed", "", "Fri", ""]:
        g.append(f"<span>{lab}</span>")
    g.append('</div><div class="cal-main"><div class="months">')
    for wi in range(len(weeks)):
        g.append(f'<span>{labels_by_week.get(wi, "")}</span>')
    g.append('</div><div class="cols">')
    for col in cells:
        g.append('<div class="col">')
        for lv, title, future, is_today in col:
            cls = "cell" + (" future" if future else "") + (" today" if is_today else "")
            style = f"background:{LEVEL_COLORS[lv]}" if not future else ""
            t = f' title="{esc(title)}"' if title else ""
            g.append(f'<div class="{cls}" style="{style}"{t}></div>')
        g.append("</div>")
    g.append("</div></div></div>")
    grid_html = "\n".join(g)
    legend = ('<div class="legend">Less '
              + "".join(f'<span class="cell" style="background:{c}"></span>' for c in LEVEL_COLORS)
              + " More</div>")

    # ---------- pillar cards ----------
    def pillar(icon, name, big, sub, rows, spark="", cap=""):
        rh = "".join(f'<div class="row"><span>{k}</span><b>{v}</b></div>' for k, v in rows)
        sp = f'<div class="sparkwrap">{spark}{f"<div class=spark-cap>{cap}</div>" if cap else ""}</div>' if spark else ""
        return f'''<div class="card">
          <div class="card-h"><span class="ic">{icon}</span>{name}</div>
          <div class="big">{big}</div><div class="sub">{sub}</div>
          {sp}<div class="rows">{rh}</div></div>'''

    run_paces = [r["pace"] for r in tr.get("runs", [])]
    pace_cap = ""
    if run_paces:
        pace_cap = f"pace, last {len(run_paces)} runs &middot; best {pace(min(run_paces))} &middot; last {pace(run_paces[-1])}"
    fitness_card = pillar("&#127939;", "Fitness",
        f"{f_.get('total_miles', 0)}<small>mi</small>", f"{f_.get('total_runs', 0)} runs logged",
        [("Last 7 days", f"{f_.get('miles_7d', 0)} mi"),
         ("Last 30 days", f"{f_.get('miles_30d', 0)} mi"),
         ("Last run", f"{lr.get('dist', '-')} mi &middot; {pace(lr.get('pace_sec_mi'))}/mi" if lr else "-"),
         ("Best 5K pace", f"{pace(f_.get('best_5k_pace'))}/mi"),
         ("PRs", f_.get("prs", 0)), ("Weight", weight_line)],
        spark=spark_line(run_paces, color=PURPLE), cap=pace_cap)

    wm = [(w["week"], w["mi"]) for w in tr.get("weekly_miles", [])]
    content_card = pillar("&#127909;", "Content",
        f"{c_.get('views', 0):,}<small>views</small>", f"{c_.get('videos', 0)} videos tracked",
        [("Subs gained", f"+{c_.get('subs', 0)}"),
         ("Top video", f"{c_.get('top', {}).get('views', 0):,} views" if c_.get("top") else "-"),
         ("This week", f"{b.get('videos_published', 0)} published")])

    reading_card = pillar("&#128214;", "Reading",
        f"{rd.get('minutes', 0)}<small>min</small>", f"{rd.get('sessions', 0)} sessions logged",
        [("Current book", esc(rd.get("last_book") or "-")),
         ("Last session", f"{gr}d ago" if gr is not None else "-")])

    mrr_vals = [m["mrr"] for m in tr.get("mrr", [])]
    business_card = pillar("&#128176;", "Business",
        f"${b.get('mrr', 0):,}<small>MRR</small>", f"week of {b.get('week_start', '-')}",
        [("Skool members", f"{b.get('skool_members', 0):,}"),
         ("Email subs", f"{b.get('email_subs', 0):,}"),
         ("Goal", "$500K ARR / 2026")],
        spark=spark_line(mrr_vals, color=GREEN), cap="MRR trend" if len(mrr_vals) > 1 else "")

    # weekly-miles spark lives under fitness as a second mini row
    miles_spark = (f'<div class="card-spark"><div class="card-h"><span class="ic">&#128202;</span>'
                   f'Weekly miles &middot; 12 wks</div>{spark_bars(wm, w=400, h=46)}</div>') if wm else ""

    def chip(label, val, target=None, unit=""):
        t = f"<span> / {target}{unit}</span>" if target is not None else ""
        return f'<div class="chip"><div class="chip-v">{val}{unit}{t}</div><div class="chip-l">{label}</div></div>'

    strip = "".join([
        chip("Calories", int(ts.get("cal", 0)), CAL_TARGET),
        chip("Protein", int(ts.get("protein", 0)), PROTEIN_TARGET, "g"),
        chip("Water", int(ts.get("water", 0)), WATER_GOAL, "oz"),
        chip("Caffeine", int(ts.get("caffeine", 0)), None, "mg"),
        chip("Check-in", "Done" if ts.get("checkin_today") else "Open"),
    ])
    nudge_html = "".join(f'<div class="nudge {lv}">{txt}</div>' for lv, txt in nudges)

    streak_sub = f"best {best}"
    if days_since:
        streak_sub += f" &middot; {days_since}d since last"
    gen = datetime.now().strftime("%b %d, %Y %I:%M %p")

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lifestyle OS</title>
<style>
:root{{--bg:#0d1017;--panel:#161b22;--line:#21262d;--text:#e6edf3;--dim:#8b949e;--accent:#cba6f7;}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:1040px;margin:0 auto;padding:32px 24px 64px}}
header{{display:flex;align-items:baseline;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:4px}}
h1{{font-size:26px;margin:0;letter-spacing:-.02em}}
.gen{{color:var(--dim);font-size:12px}}
.tag{{color:var(--accent);font-size:13px;margin:2px 0 24px;font-weight:500}}
.panel{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:20px;margin-bottom:20px}}
.panel-h{{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}}
.panel-h h2{{font-size:14px;text-transform:uppercase;letter-spacing:.06em;color:var(--dim);margin:0;font-weight:600}}
.move-top{{display:flex;align-items:center;gap:22px;margin-bottom:20px;flex-wrap:wrap}}
.ring-wrap{{display:flex;align-items:center;gap:12px}}
.ring-t{{fill:var(--text);font-size:24px;font-weight:700}} .ring-p{{fill:var(--dim);font-size:13px}}
.ring-cap{{font-size:12px;color:var(--dim);line-height:1.3}} .ring-cap b{{color:var(--text);font-size:13px;text-transform:uppercase;letter-spacing:.04em}}
.move-stats{{display:flex;gap:26px;margin-left:auto;flex-wrap:wrap}}
.stat .v{{font-size:24px;font-weight:700}} .stat .v b{{color:#39d353}} .stat .l{{font-size:11px;color:var(--dim);text-transform:uppercase;letter-spacing:.05em}}
.cal{{display:flex;gap:6px;overflow-x:auto;padding-bottom:4px}}
.cal-day{{display:flex;flex-direction:column;gap:3px;width:26px;padding-top:16px;font-size:9px;color:var(--dim)}}
.cal-day span{{height:12px;line-height:12px}}
.cal-main{{display:inline-block}}
.months{{display:flex;gap:3px;height:12px;margin-bottom:4px}}
.months span{{flex:0 0 12px;width:12px;font-size:10px;line-height:12px;color:var(--dim);white-space:nowrap;overflow:visible}}
.cols{{display:flex;gap:3px}}
.col{{display:flex;flex-direction:column;gap:3px}}
.cell{{width:12px;height:12px;border-radius:3px;background:var(--line)}}
.cell.future{{background:transparent}} .cell.today{{outline:1.5px solid var(--accent);outline-offset:1px}}
.legend{{display:flex;align-items:center;gap:4px;justify-content:flex-end;font-size:11px;color:var(--dim);margin-top:12px}}
.legend .cell{{display:inline-block}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px}}
.card{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px}}
.card-h{{display:flex;align-items:center;gap:8px;font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:var(--dim);font-weight:600}}
.card-h .ic{{font-size:16px}}
.big{{font-size:32px;font-weight:700;margin-top:10px;letter-spacing:-.02em}}
.big small{{font-size:14px;color:var(--dim);font-weight:500;margin-left:4px}}
.sub{{color:var(--dim);font-size:12px}}
.sparkwrap{{margin:12px 0 6px}} .spark{{width:100%;height:38px;display:block}}
.spark-cap{{font-size:11px;color:var(--dim);margin-top:3px}}
.spark-empty{{font-size:11px;color:var(--dim);padding:12px 0;font-style:italic}}
.rows{{margin-top:8px}}
.rows .row{{display:flex;justify-content:space-between;padding:5px 0;border-top:1px solid var(--line);font-size:13px}}
.rows .row span{{color:var(--dim)}} .rows .row b{{font-weight:600}}
.card-spark{{margin-top:16px}} .card-spark .spark{{height:46px;margin-top:8px}}
.strip{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:12px}}
.chip{{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:12px 14px}}
.chip-v{{font-size:20px;font-weight:700}} .chip-v span{{color:var(--dim);font-size:13px;font-weight:500}}
.chip-l{{color:var(--dim);font-size:11px;text-transform:uppercase;letter-spacing:.05em;margin-top:2px}}
.nudges{{margin-top:16px;display:flex;flex-direction:column;gap:8px}}
.nudge{{font-size:13px;padding:10px 14px;border-radius:10px;border:1px solid var(--line);border-left-width:3px;background:var(--bg)}}
.nudge.ok{{border-left-color:#39d353;background:rgba(57,211,83,.07)}}
.nudge.warn{{border-left-color:#e3b341;background:rgba(227,179,65,.07)}}
.nudge.idle{{border-left-color:#30363d}}
</style></head>
<body><div class="wrap">
<header><h1>Lifestyle OS</h1><span class="gen">generated {gen}</span></header>
<div class="tag">$500K ARR by end of 2026 &middot; consistency over intensity</div>

<div class="panel">
  <div class="move-top">
    <div class="ring-wrap">{ring(consistency)}
      <div class="ring-cap"><b>Consistency</b><br>active {win_active} of last {CONSISTENCY_WINDOW} days</div>
    </div>
    <div class="move-stats">
      <div class="stat"><div class="v"><b>{streak}</b></div><div class="l">day streak</div></div>
      <div class="stat"><div class="v">{best}</div><div class="l">best streak</div></div>
      <div class="stat"><div class="v">{f_.get('miles_7d', 0)}</div><div class="l">mi this week</div></div>
    </div>
  </div>
  {grid_html}
  {legend}
</div>

<div class="cards">{fitness_card}{content_card}{reading_card}{business_card}</div>
{miles_spark}

<div class="panel" style="margin-top:20px">
  <div class="panel-h"><h2>Today &middot; {today.strftime('%A, %b %d')}</h2></div>
  <div class="strip">{strip}</div>
  <div class="nudges">{nudge_html}</div>
</div>

</div></body></html>"""

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        fh.write(html)
    print(f"Wrote {OUT}")
    print(f"  consistency {consistency}% ({win_active}/{CONSISTENCY_WINDOW}), "
          f"streak {streak} (best {best}), {len(nudges)} nudges, {len(days)} logged days")


if __name__ == "__main__":
    main()
