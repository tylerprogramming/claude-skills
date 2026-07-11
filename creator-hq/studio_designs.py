#!/usr/bin/env python3
"""
Creator HQ - distinctive design explorations (anti-generic).

Two editorial directions that deliberately avoid the rounded-card / soft-shadow /
accent-rail / generic-sans look:

  rundown : Swiss / broadcast-rundown editorial. Hairline rules, Helvetica Neue
            grotesque + Menlo monospace for data, numbered ranking list, ink on
            newsprint with one signal red.
  marquee : Mid-century broadcast poster. Futura display, a full-width colour
            hero block, big geometric numerals, thumbnail filmstrip, petrol
            accent on warm ivory.

Both use faces present on macOS AND iPadOS (no web fonts), so they render crisp
on the kiosk and pass the Artifact CSP. Self-contained (thumbnails inlined).

Usage:
    python3 studio_designs.py            # writes preview-rundown/-marquee .html + .artifact.html
"""
import json
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


MILESTONES = [1000, 2500, 5000, 10000, 25000, 50000, 100000, 250000, 500000, 1_000_000]


def milestone_sub(subs):
    if not subs:
        return ""
    for m in MILESTONES:
        if m > subs:
            return f"{m - subs:,} to {fmt_num(m)}"
    return f"{subs:,}"


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
        return "TODAY"
    if delta == 1:
        return "YESTERDAY"
    if 0 < delta < 7:
        return f"{delta}D AGO"
    return f"{MONTHS[d.month-1].upper()} {d.day}"


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
    return f"data:image/jpeg;base64,{base64.b64encode(p.read_bytes()).decode()}"


def esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def spark(vals, color, dates=None, w=260, h=48, unit="views"):
    """Filled mini area chart: baseline + area + line + a hoverable dot per point."""
    vals = [v for v in vals if v is not None]
    if not vals:
        return ""
    if len(vals) == 1:
        vals = vals * 2
        dates = (dates or [""]) * 2
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1
    n = len(vals)
    pt, pb, px = 10, 7, 3
    def x(i): return px + i * (w - 2 * px) / (n - 1)
    def y(v): return pt + (1 - (v - lo) / span) * (h - pt - pb)
    line = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(vals))
    area = f"{px:.1f},{h-pb:.1f} " + line + f" {x(n-1):.1f},{h-pb:.1f}"
    dots = ""
    for i, v in enumerate(vals):
        d = dates[i] if (dates and i < len(dates)) else ""
        r = 3.2 if i == n - 1 else 2.3
        dots += (f'<circle class="pt" cx="{x(i):.1f}" cy="{y(v):.1f}" r="{r}" fill="{color}" '
                 f'data-d="{d}" data-v="{v}" data-u="{unit}"/>')
    return (f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" style="width:100%;height:{h}px;display:block">'
            f'<line x1="{px}" y1="{h-pb}" x2="{w-px}" y2="{h-pb}" stroke="{color}" stroke-opacity="0.22" stroke-width="1"/>'
            f'<polygon points="{area}" fill="{color}" opacity="0.14"/>'
            f'<polyline points="{line}" fill="none" stroke="{color}" stroke-width="2.2" '
            f'stroke-linecap="round" stroke-linejoin="round"/>{dots}</svg>')


# ---- shared metrics --------------------------------------------------------
def metrics():
    cfg = json.loads((BASE / "config.json").read_text()) if (BASE / "config.json").exists() else {}
    snap = json.loads((DATA_DIR / "youtube.json").read_text()) if (DATA_DIR / "youtube.json").exists() else {"creators": []}
    pipe = json.loads((BASE / "pipeline.json").read_text()) if (BASE / "pipeline.json").exists() else {"videos": []}

    today = datetime.date.today()
    goals = cfg.get("goals", {})
    g_create = int(goals.get("create_per_week", 2))
    g_release = int(goals.get("release_per_week", 2))
    ws, we = week_window(today, cfg.get("week_start", "monday"))

    c = (snap.get("creators") or [{}])[0]
    vids = c.get("videos", [])

    released = sum(1 for v in vids if (d := parse_ymd(v.get("upload_date"))) and ws <= d <= we)
    created = sum(1 for it in pipe.get("videos", [])
                  if (d := parse_iso(it.get("filmed"))) and ws <= d <= we)
    ready = sum(1 for it in pipe.get("videos", []) if it.get("stage") == "ready")

    view_vals = [v.get("views") for v in vids if v.get("views") is not None]
    avg_views = round(sum(view_vals) / len(view_vals)) if view_vals else None
    dated = sorted([v for v in vids if parse_ymd(v.get("upload_date")) and v.get("views") is not None],
                   key=lambda v: v["upload_date"])
    spark_vals = [v["views"] for v in dated[-8:]]
    top = max(vids, key=lambda v: v.get("views") or -1, default=None)
    last30 = sum(1 for v in vids if (d := parse_ymd(v.get("upload_date"))) and (today - d).days <= 30)

    pcounts = {s: 0 for s in STAGES}
    for it in pipe.get("videos", []):
        if it.get("stage") in pcounts:
            pcounts[it["stage"]] += 1

    rows = []
    for v in vids[:4]:
        d = parse_ymd(v.get("upload_date"))
        rows.append({
            "title": v.get("title", ""),
            "views": v.get("views"),
            "likes": v.get("likes"),
            "when": fmt_when(d, today),
            "dur": "SHORT" if is_short(v.get("duration")) else fmt_dur(v.get("duration")),
            "thumb": data_uri(v.get("thumb")),
            "url": v.get("url") or "#",
        })

    # --- tracked cohort (from Supabase youtube_daily via cohort.json) ---
    cpath = DATA_DIR / "cohort.json"
    cohort = json.loads(cpath.read_text()) if cpath.exists() else None
    crows, since = [], None
    histories = (cohort or {}).get("histories", {})
    subs_map = (cohort or {}).get("subs", {})
    if cohort:
        for v in sorted(cohort["videos"], key=lambda x: x.get("views") or 0, reverse=True):
            pd = parse_iso(v.get("published_date"))
            hist = histories.get(v["video_id"], [])
            latest = v.get("views")
            first = hist[0][1] if hist else latest
            prev = hist[-2][1] if len(hist) >= 2 else first
            crows.append({
                "video_id": v["video_id"],
                "title": v.get("title", ""), "views": latest, "delta": v.get("delta"),
                "likes": v.get("likes"), "comments": v.get("comments"),
                "subs": subs_map.get(v["video_id"]),
                "ctr": v.get("ctr"), "avd": v.get("avg_view_pct"),
                "pub": f"{MONTHS[pd.month-1].upper()} {pd.day}" if pd else "",
                "pub_iso": v.get("published_date") or "",
                "thumb": data_uri(f"thumbs/{v['video_id']}.jpg"),
                "url": f"https://youtu.be/{v['video_id']}",
                "hist": hist, "first": first, "prev": prev,
            })
        prevs = [parse_iso(v["prev_date"]) for v in cohort["videos"] if v.get("prev_date")]
        since = max(prevs) if prevs else None

    return {
        "name": c.get("name") or "Your channel", "subs": c.get("subs"),
        "total": c.get("total_videos"), "avatar": data_uri(c.get("avatar")),
        "week_label": f"{MONTHS[ws.month-1].upper()} {ws.day}–{MONTHS[we.month-1].upper()} {we.day}",
        "wk": ws.isocalendar()[1], "year": ws.year,
        "fetched": snap.get("fetched_at", "")[:16].replace("T", " "),
        "created": created, "g_create": g_create,
        "released": released, "g_release": g_release, "ready": ready,
        "avg_views": avg_views, "nviews": len(view_vals), "spark": spark_vals,
        "top_val": fmt_num(top.get("views")) if top else "-",
        "top_title": (top.get("title") or "")[:40] if top else "",
        "milestone": milestone_sub(c.get("subs")), "last30": last30,
        "pc": pcounts, "ptotal": sum(pcounts.values()), "rows": rows,
        "crows": crows, "cohort_size": (cohort or {}).get("cohort_size", len(crows)),
        "cohort_views": (cohort or {}).get("total_views"),
        "cohort_gained": (cohort or {}).get("total_delta"),
        "avg_ctr": (cohort or {}).get("avg_ctr"),
        "cohort_asof": (cohort or {}).get("as_of", ""),
        "since": f"{MONTHS[since.month-1].upper()} {since.day}" if since else "",
        "series": (cohort or {}).get("series", {}),
        "cohort_subs": (cohort or {}).get("cohort_subs"),
    }


RUNDOWN_JS = """
<script>
(function(){
  var container=document.getElementById('rows');
  var rows=[].slice.call(container.querySelectorAll('.trow'));
  var toggle=document.getElementById('toggle');
  var filter=document.getElementById('filter');
  var baseline=document.getElementById('baseline');
  var gained=document.getElementById('gained');
  var gainedsub=document.getElementById('gainedsub');
  var tip=document.getElementById('tip');
  var LIMIT=5, expanded=false, sortKey='views', dir='desc';
  function num(el,a){ return parseFloat(el.getAttribute(a))||0; }
  function recompute(){
    var mode = baseline? baseline.value : 'last', total=0;
    rows.forEach(function(el){
      var latest=num(el,'data-latest');
      var base = mode==='begin'? num(el,'data-first') : num(el,'data-prev');
      var d = latest-base; el.setAttribute('data-delta', d);
      var cell=el.querySelector('.t-d');
      if(d>0) cell.innerHTML='<span class="t-up">+'+d+'</span>';
      else if(d<0) cell.innerHTML='<span class="t-flat">'+d+'</span>';
      else cell.innerHTML='<span class="t-flat">\\u2014</span>';
      total+=d;
    });
    if(gained) gained.textContent='+'+total.toLocaleString();
    if(gainedsub) gainedsub.textContent = mode==='begin'? 'since first tracked' : 'since last snapshot';
  }
  function val(el,k){ return k==='title'? el.getAttribute('data-title') : num(el,'data-'+k); }
  function apply(){
    var q=(filter.value||'').trim().toLowerCase();
    var sorted=rows.slice().sort(function(a,b){
      var va=val(a,sortKey), vb=val(b,sortKey), r;
      if(sortKey==='title'){ r = va<vb?-1:(va>vb?1:0); } else { r = va-vb; }
      return dir==='asc'? r : -r;
    });
    sorted.forEach(function(el){ container.appendChild(el); });
    var matched=0, shown=0;
    sorted.forEach(function(el){
      var ok = !q || el.getAttribute('data-title').indexOf(q)>-1;
      if(ok) matched++;
      var show = ok && (q || expanded || shown<LIMIT);
      el.classList.toggle('hidden', !show);
      if(show) shown++;
    });
    var i=0;
    sorted.forEach(function(el){ if(!el.classList.contains('hidden')){ i++; el.querySelector('.t-i').textContent=('0'+i).slice(-2); } });
    if(q || matched<=LIMIT){ toggle.style.display='none'; }
    else { toggle.style.display='block'; toggle.textContent = expanded? 'Show less \\u25B2' : ('Show all '+matched+' videos \\u00B7 '+(matched-LIMIT)+' more \\u25BC'); }
  }
  document.querySelectorAll('.sortable').forEach(function(h){
    h.addEventListener('click',function(){
      var k=h.getAttribute('data-key');
      if(sortKey===k){ dir = dir==='asc'?'desc':'asc'; } else { sortKey=k; dir = k==='title'?'asc':'desc'; }
      document.querySelectorAll('.sortable').forEach(function(x){ x.classList.remove('act','asc'); });
      h.classList.add('act'); if(dir==='asc') h.classList.add('asc');
      apply();
    });
  });
  filter.addEventListener('input', apply);
  toggle.addEventListener('click', function(){ expanded=!expanded; apply(); });
  if(baseline) baseline.addEventListener('change', function(){ recompute(); apply(); });
  var dh=document.querySelector('.sortable[data-key="views"]'); if(dh) dh.classList.add('act');
  function showTip(c){
    var r=c.getBoundingClientRect();
    var v=(+c.getAttribute('data-v')).toLocaleString();
    var u=c.getAttribute('data-u')||'', d=c.getAttribute('data-d')||'';
    tip.textContent=(d? d+'  ':'')+v+(u?' '+u:'');
    tip.style.left=(r.left+r.width/2)+'px'; tip.style.top=r.top+'px'; tip.style.opacity='1';
  }
  function hideTip(){ tip.style.opacity='0'; }
  document.addEventListener('pointerover',function(e){ if(e.target.classList && e.target.classList.contains('pt')) showTip(e.target); });
  document.addEventListener('pointerout',function(e){ if(e.target.classList && e.target.classList.contains('pt')) hideTip(); });
  document.addEventListener('touchstart',function(e){ var t=e.target; if(t.classList && t.classList.contains('pt')){ showTip(t); setTimeout(hideTip,1500); } },{passive:true});
  recompute();
  apply();
})();
</script>"""


# ---- DESIGN A: THE RUNDOWN -------------------------------------------------
def design_rundown(m):
    INK, PAPER, RED, FAINT, MUTED = "#1a1a17", "#f4f3ef", "#d5321c", "rgba(26,26,23,.15)", "rgba(26,26,23,.55)"

    def status_word(count, goal):
        if count >= goal:
            return '<span class="ontrack">ON TRACK</span>'
        return f'<span class="behind">{goal - count} TO GO</span>'

    checks = f'''
      <div class="stat"><div class="st-l">VIDEOS CREATED</div>
        <div class="st-n">{m['created']}<span>/{m['g_create']}</span></div>{status_word(m['created'], m['g_create'])}</div>
      <div class="stat"><div class="st-l">VIDEOS RELEASED</div>
        <div class="st-n">{m['released']}<span>/{m['g_release']}</span></div>{status_word(m['released'], m['g_release'])}</div>
      <div class="stat"><div class="st-l">READY TO PUBLISH</div>
        <div class="st-n">{m['ready']}</div><span class="ontrack">IN THE CAN</span></div>'''

    BLUE, GREEN, AMBER, VIEWC = "#2f6fed", "#1a9e4b", "#c98a1a", "#3b4a6b"
    ser = m.get("series", {})

    def prog(subs):
        nxt = next((mm for mm in [1000, 2500, 5000, 10000, 25000, 50000, 100000,
                                  250000, 500000, 1_000_000] if mm > (subs or 0)), None)
        if not nxt or not subs:
            return ""
        pct = min(100, round(subs / nxt * 100))
        return f'<div class="bar"><span style="width:{pct}%;background:{BLUE}"></span></div>'

    dts = ser.get('dates', [])
    kpis = f'''
      <div class="kp kp-blue"><div class="kp-l">SUBSCRIBERS</div><div class="kp-n">{fmt_num(m['subs'])}</div><div class="kp-s">{m['milestone']}</div><div class="kp-g">{prog(m['subs'])}</div></div>
      <div class="kp kp-viewc"><div class="kp-l">COHORT VIEWS</div><div class="kp-n">{fmt_num(m['cohort_views'])}</div><div class="kp-s">{m['cohort_size']} tracked videos</div><div class="kp-g">{spark(ser.get('views', []), VIEWC, dts, unit='views')}</div></div>
      <div class="kp kp-green"><div class="kp-l">VIEWS GAINED</div><div class="kp-n" id="gained" style="color:{GREEN}">+{m['cohort_gained']}</div><div class="kp-s" id="gainedsub">since last snapshot</div><div class="kp-g">{spark(ser.get('views', []), GREEN, dts, unit='views')}</div></div>
      <div class="kp kp-amber"><div class="kp-l">AVG CTR</div><div class="kp-n">{m['avg_ctr']}%</div><div class="kp-s">as of {m['cohort_asof'][5:]}</div><div class="kp-g">{spark(ser.get('ctr', []), AMBER, unit='% CTR')}</div></div>'''

    def dcell(d):
        if d is None:
            return '<span class="t-new">NEW</span>'
        if d and d > 0:
            return f'<span class="t-up">+{d}</span>'
        return '<span class="t-flat">&mdash;</span>'

    def hd(key, label, r=False):
        return f'<span class="{"r sortable" if r else "sortable"}" data-key="{key}">{label}</span>'

    thead = (f'<div class="thead"><span>#</span><span></span>{hd("title", "Video")}<span>Trend</span>'
             f'{hd("views", "Views", 1)}{hd("delta", "Growth", 1)}{hd("subs", "Subs", 1)}'
             f'{hd("ctr", "CTR", 1)}{hd("comments", "Cmts", 1)}</div>')
    trow_html = []
    for r in m["crows"]:
        thumb = f'<span class="t-th" style="background-image:url({r["thumb"]})"></span>' if r["thumb"] else '<span class="t-th"></span>'
        ctr = f'{r["ctr"]}%' if r["ctr"] is not None else '&mdash;'
        cmts = f'{r["comments"]}' if r["comments"] is not None else '&mdash;'
        subs = f'+{r["subs"]}' if r.get("subs") else ('&mdash;' if r.get("subs") is None else '0')
        likes = f'{r["likes"]} likes' if r["likes"] is not None else ''
        hist = r.get("hist") or []
        vals = [p[1] for p in hist]
        dates = [p[0] for p in hist]
        trend = (spark(vals, INK, dates, w=120, h=30) if len(vals) >= 2
                 else '<span class="t-flat">&mdash;</span>')
        d = r["delta"]
        data = (f'data-title="{esc(r["title"].lower())}" data-views="{r["views"] or 0}" '
                f'data-delta="{d if d is not None else 0}" data-subs="{r["subs"] or 0}" '
                f'data-ctr="{r["ctr"] or 0}" data-comments="{r["comments"] or 0}" data-pub="{r["pub_iso"]}" '
                f'data-latest="{r["views"] or 0}" data-first="{r["first"] or 0}" data-prev="{r["prev"] or 0}"')
        trow_html.append(f'''
        <a class="trow" {data} href="{esc(r['url'])}" target="_blank" rel="noopener">
          <span class="t-i"></span>{thumb}
          <span class="tt"><span class="t-name">{esc(r['title'])}</span><span class="t-pub">{r['pub']} &middot; {likes}</span></span>
          <span class="t-trend">{trend}</span>
          <span class="t-v">{fmt_num(r['views'])} <em>views</em></span>
          <span class="t-d">{dcell(d)}</span>
          <span class="t-s">{subs}</span>
          <span class="t-c">{ctr}</span>
          <span class="t-m">{cmts}</span>
        </a>''')
    rows_html = "".join(trow_html)

    pipe = ""
    for i, s in enumerate(STAGES):
        cls = "pp ready" if s == "ready" else "pp"
        pipe += f'<div class="{cls}"><div class="pp-n">{m["pc"][s]}</div><div class="pp-l">{STAGE_LABEL[s].upper()}</div></div>'
        if i < len(STAGES) - 1:
            pipe += '<div class="pp-x">/</div>'

    css = f'''<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  html,body{{background:{PAPER};color:{INK};
    font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased}}
  .mono{{font-family:"Menlo","Courier New",monospace}}
  a{{color:inherit;text-decoration:none}}
  .wrap{{max-width:1360px;margin:0 auto;padding:30px 34px 40px}}
  .mast{{display:flex;justify-content:space-between;align-items:flex-end;padding-bottom:10px}}
  .brand{{font-size:38px;font-weight:800;letter-spacing:-1.4px;text-transform:uppercase;line-height:.9}}
  .brand em{{font-style:normal;color:{RED}}}
  .ed{{font-family:"Menlo","Courier New",monospace;font-size:11.5px;letter-spacing:1.5px;text-align:right;color:{MUTED};line-height:1.7;text-transform:uppercase}}
  .rule{{height:3px;background:{INK}}}
  .subrow{{display:flex;justify-content:space-between;font-family:"Menlo","Courier New",monospace;
    font-size:11px;letter-spacing:1.2px;text-transform:uppercase;color:{MUTED};padding:8px 0;border-bottom:1px solid {FAINT}}}
  .band{{display:grid;grid-template-columns:repeat(3,1fr);border-bottom:1px solid {FAINT}}}
  .stat{{padding:26px 24px 24px}}
  .stat+.stat{{border-left:1px solid {FAINT}}}
  .st-l{{font-family:"Menlo","Courier New",monospace;font-size:11px;letter-spacing:1.4px;color:{MUTED}}}
  .st-n{{font-size:66px;font-weight:800;letter-spacing:-3px;line-height:1;margin:8px 0 6px;font-variant-numeric:tabular-nums}}
  .st-n span{{font-size:30px;color:{MUTED};letter-spacing:-1px}}
  .ontrack,.behind{{font-family:"Menlo","Courier New",monospace;font-size:12px;letter-spacing:1.5px;font-weight:700}}
  .ontrack{{color:{INK}}}
  .behind{{color:{RED}}}
  .kprow{{display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid {FAINT}}}
  .kp{{padding:20px 22px}}
  .kp+.kp{{border-left:1px solid {FAINT}}}
  .kp-l{{font-family:"Menlo","Courier New",monospace;font-size:10.5px;letter-spacing:1.3px;color:{MUTED}}}
  .kp-n{{font-size:38px;font-weight:800;letter-spacing:-1.5px;margin-top:7px;font-variant-numeric:tabular-nums}}
  .kp-s{{font-family:"Menlo","Courier New",monospace;font-size:10.5px;letter-spacing:.5px;color:{MUTED};margin-top:6px;text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
  .kp-spk{{margin-top:10px}}
  .kp-g{{margin-top:11px}}
  .kp-blue  .kp-l{{color:#2f6fed}}
  .kp-viewc .kp-l{{color:#3b4a6b}}
  .kp-green .kp-l{{color:#1a9e4b}}
  .kp-amber .kp-l{{color:#c98a1a}}
  .bar{{height:26px;background:{FAINT};position:relative}}
  .bar span{{display:block;height:100%}}
  details.more summary{{list-style:none;cursor:pointer;font-family:"Menlo","Courier New",monospace;
    font-size:11px;letter-spacing:1.4px;text-transform:uppercase;color:{RED};
    padding:13px 0;border-top:1px solid {FAINT};text-align:center}}
  details.more summary::-webkit-details-marker{{display:none}}
  details.more summary::after{{content:" \\25BC";font-size:9px}}
  details.more[open] summary{{color:{MUTED}}}
  details.more[open] summary::after{{content:" \\25B2"}}
  .sec-h{{display:flex;justify-content:space-between;align-items:baseline;padding:22px 0 10px}}
  .sec-h b{{font-size:15px;font-weight:800;letter-spacing:1px;text-transform:uppercase}}
  .sec-h span{{font-family:"Menlo","Courier New",monospace;font-size:11px;letter-spacing:1.2px;color:{MUTED};text-transform:uppercase}}
  .rk{{display:grid;grid-template-columns:34px 116px 1fr auto;align-items:center;gap:18px;
    padding:13px 0;border-top:1px solid {FAINT}}}
  .rk:hover .rk-t{{color:{RED}}}
  .rk-i{{font-family:"Menlo","Courier New",monospace;font-size:13px;color:{MUTED}}}
  .rk-th{{display:block;width:116px;height:65px;background:#ddd center/cover;border:1px solid {FAINT}}}
  .rk-t{{font-size:16px;font-weight:500;line-height:1.3;max-width:52ch;
    display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
  .rk-m{{font-family:"Menlo","Courier New",monospace;font-size:12px;text-align:right;letter-spacing:.3px;line-height:1.7}}
  .rk-d{{color:{MUTED};font-size:10.5px}}
  .tbl{{margin-top:2px;overflow-x:auto}}
  .thead,.trow{{display:grid;grid-template-columns:22px 64px minmax(120px,1fr) 96px 78px 58px 48px 46px 42px;align-items:center;gap:10px;min-width:820px}}
  .thead{{font-family:"Menlo","Courier New",monospace;font-size:10px;letter-spacing:1.1px;text-transform:uppercase;color:{MUTED};padding:0 0 9px;border-bottom:2px solid {INK}}}
  .thead .r{{text-align:right}}
  .sortable{{cursor:pointer;user-select:none;white-space:nowrap}}
  .sortable:hover{{color:{INK}}}
  .sortable.act{{color:{RED}}}
  .sortable.act::after{{content:" \\25BE";font-size:8px}}
  .sortable.act.asc::after{{content:" \\25B4"}}
  .trow{{padding:8px 0;border-top:1px solid {FAINT};color:inherit}}
  .trow.hidden{{display:none}}
  .trow:hover .t-name{{color:{RED}}}
  .t-i{{font-family:"Menlo","Courier New",monospace;font-size:12px;color:{MUTED}}}
  .t-th{{display:block;width:64px;height:36px;background:#ddd center/cover;border:1px solid {FAINT}}}
  .tt{{display:flex;flex-direction:column;gap:3px;min-width:0}}
  .t-name{{font-size:14px;font-weight:500;line-height:1.25;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
  .t-pub{{font-family:"Menlo","Courier New",monospace;font-size:10px;letter-spacing:.5px;color:{MUTED};text-transform:uppercase}}
  .t-trend{{opacity:.8}}
  .t-v{{text-align:right;font-size:18px;font-weight:800;letter-spacing:-.5px;font-variant-numeric:tabular-nums;line-height:1}}
  .t-v em{{display:block;font-style:normal;font-family:"Menlo","Courier New",monospace;font-size:8.5px;font-weight:400;letter-spacing:1px;color:{MUTED};text-transform:uppercase;margin-top:2px}}
  .t-d,.t-c,.t-m,.t-s{{text-align:right;font-family:"Menlo","Courier New",monospace;font-size:13px;font-variant-numeric:tabular-nums;color:{MUTED}}}
  .t-s{{color:{BLUE}}}
  .t-up{{color:{RED};font-weight:700}}
  .t-flat{{color:{FAINT}}}
  .t-new{{color:{MUTED};font-size:10px;letter-spacing:1px}}
  .ctools{{display:flex;align-items:center;gap:14px;font-family:"Menlo","Courier New",monospace;
    font-size:11px;letter-spacing:1.2px;color:{MUTED};text-transform:uppercase}}
  #filter{{font-family:"Menlo","Courier New",monospace;font-size:11px;letter-spacing:1px;text-transform:uppercase;
    background:transparent;border:1px solid {FAINT};color:{INK};padding:6px 10px;width:150px;outline:none}}
  #filter:focus{{border-color:{INK}}}
  #baseline{{font-family:"Menlo","Courier New",monospace;font-size:10.5px;letter-spacing:.6px;text-transform:uppercase;
    background:transparent;border:1px solid {FAINT};color:{INK};padding:6px 8px;outline:none;cursor:pointer}}
  #toggle{{cursor:pointer;font-family:"Menlo","Courier New",monospace;font-size:11px;letter-spacing:1.4px;
    text-transform:uppercase;color:{RED};padding:13px 0;border-top:1px solid {FAINT};text-align:center}}
  .pt{{cursor:pointer}}
  #tip{{position:fixed;z-index:99;background:{INK};color:{PAPER};font-family:"Menlo","Courier New",monospace;
    font-size:11px;letter-spacing:.5px;padding:5px 9px;pointer-events:none;opacity:0;transition:opacity .1s;white-space:nowrap;transform:translate(-50%,-140%)}}
  .pipe-wrap{{border-top:3px solid {INK};margin-top:6px}}
  .pipe{{display:flex;align-items:center;gap:6px;padding:16px 0 4px}}
  .pp{{flex:1;text-align:center}}
  .pp-n{{font-size:30px;font-weight:800;letter-spacing:-1px;font-variant-numeric:tabular-nums}}
  .pp.ready .pp-n{{color:{RED}}}
  .pp-l{{font-family:"Menlo","Courier New",monospace;font-size:10px;letter-spacing:1.2px;color:{MUTED};margin-top:3px}}
  .pp.ready .pp-l{{color:{RED}}}
  .pp-x{{font-family:"Menlo","Courier New",monospace;color:{FAINT};font-size:18px}}
  .foot{{font-family:"Menlo","Courier New",monospace;font-size:10px;letter-spacing:1px;color:{MUTED};
    text-transform:uppercase;padding-top:20px}}
  @media (max-width:820px){{.band,.kprow{{grid-template-columns:repeat(2,1fr)}}}}
</style>'''

    body = f'''
  <div class="wrap">
    <div class="mast">
      <div class="brand">Creator&nbsp;<em>HQ</em></div>
      <div class="ed">EDITION {m['wk']:02d} &middot; {m['year']}<br>WEEK OF {m['week_label']}</div>
    </div>
    <div class="rule"></div>
    <div class="subrow">
      <span>{esc(m['name']).upper()} &middot; {fmt_num(m['subs'])} SUBSCRIBERS &middot; {fmt_num(m['total'])} VIDEOS</span>
      <span>COHORT AS OF {m['cohort_asof']} &middot; SUBS LIVE</span>
    </div>
    <div class="band">{checks}</div>
    <div class="kprow">{kpis}</div>
    <div class="sec-h"><b>Tracked Cohort</b>
      <span class="ctools"><input id="filter" placeholder="Filter title" autocomplete="off"><select id="baseline"><option value="last">Growth vs last snapshot</option><option value="begin">Growth since beginning</option></select><span>{m['cohort_size']} videos</span></span></div>
    <div class="tbl">{thead}<div id="rows">{rows_html}</div><div id="toggle"></div></div>
    <div class="pipe-wrap"></div>
    <div class="sec-h"><b>Pipeline</b><span>{m['ptotal']} In Production</span></div>
    <div class="pipe">{pipe}</div>
    <div class="foot">Creator HQ &middot; auto-pulled from YouTube &middot; tap a dot for its date &middot; click a column to sort</div>
  </div>
  <div id="tip"></div>''' + RUNDOWN_JS
    return css, body


# ---- DESIGN B: THE MARQUEE -------------------------------------------------
def design_marquee(m):
    IVORY, INK, TEAL, CORAL, MUTED, LINE = "#efeae0", "#211d16", "#0f6a64", "#e5533a", "rgba(33,29,22,.55)", "rgba(33,29,22,.14)"

    def hero_num(count, goal, label):
        behind = count < goal
        val = f'{count}<i>/{goal}</i>' if goal else f'{count}'
        cls = "hn behind" if behind else "hn"
        return f'<div class="{cls}"><div class="hn-n">{val}</div><div class="hn-l">{label}</div></div>'

    hero = (hero_num(m['created'], m['g_create'], 'CREATED')
            + '<span class="hn-dot"></span>'
            + hero_num(m['released'], m['g_release'], 'RELEASED')
            + '<span class="hn-dot"></span>'
            + hero_num(m['ready'], 0, 'READY'))

    stats = f'''
      <div class="sx"><div class="sx-n">{fmt_num(m['subs'])}</div><div class="sx-l">Subscribers</div><div class="sx-s">{m['milestone']}</div></div>
      <div class="sx"><div class="sx-n">{fmt_num(m['total'])}</div><div class="sx-l">Total Videos</div><div class="sx-s">{m['last30']} in last 30 days</div></div>
      <div class="sx"><div class="sx-n">{fmt_num(m['avg_views'])}</div><div class="sx-l">Avg Views</div><div class="sx-spk">{spark(m['spark'], TEAL)}</div></div>
      <div class="sx"><div class="sx-n">{m['top_val']}</div><div class="sx-l">Top Recent</div><div class="sx-s">{esc(m['top_title'][:30])}</div></div>'''

    strip = ""
    for r in m["rows"]:
        thumb = f'<span class="fs-th" style="background-image:url({r["thumb"]})"><em>{r["dur"]}</em></span>' if r["thumb"] else '<span class="fs-th"></span>'
        strip += f'''
        <a class="fs" href="{esc(r['url'])}" target="_blank" rel="noopener">
          {thumb}
          <span class="fs-t">{esc(r['title'])}</span>
          <span class="fs-m">{fmt_num(r['views'])} views &middot; {r['when']}</span>
        </a>'''

    pipe = ""
    for i, s in enumerate(STAGES):
        cls = "mp ready" if s == "ready" else "mp"
        pipe += f'<div class="{cls}"><div class="mp-n">{m["pc"][s]}</div><div class="mp-l">{STAGE_LABEL[s]}</div></div>'
        if i < len(STAGES) - 1:
            pipe += '<span class="mp-x"></span>'

    css = f'''<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  html,body{{background:{IVORY};color:{INK};
    font-family:"Avenir Next","Avenir",Futura,sans-serif;-webkit-font-smoothing:antialiased}}
  a{{color:inherit;text-decoration:none}}
  .wrap{{max-width:1340px;margin:0 auto;padding:32px 36px 42px}}
  .mast{{display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:20px}}
  .brand{{font-family:Futura,"Avenir Next",sans-serif;font-size:52px;font-weight:600;letter-spacing:1px;line-height:.85;text-transform:uppercase}}
  .brand em{{font-style:normal;color:{TEAL}}}
  .tag{{text-align:right;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:{MUTED};line-height:1.8}}
  .tag b{{color:{INK};font-weight:600}}
  .hero{{background:{TEAL};color:{IVORY};padding:26px 30px;display:flex;align-items:center;gap:26px}}
  .hero-k{{font-family:Futura,sans-serif;font-size:12px;letter-spacing:3px;text-transform:uppercase;writing-mode:vertical-rl;transform:rotate(180deg);opacity:.8}}
  .hn{{flex:1}}
  .hn-n{{font-family:Futura,sans-serif;font-size:58px;font-weight:600;line-height:.9;letter-spacing:-1px}}
  .hn-n i{{font-style:normal;font-size:30px;opacity:.6}}
  .hn.behind .hn-n{{color:{CORAL}}}
  .hn-l{{font-size:12px;letter-spacing:2.5px;text-transform:uppercase;margin-top:8px;opacity:.9}}
  .hn-dot{{width:6px;height:6px;border-radius:50%;background:{IVORY};opacity:.5;flex:none}}
  .stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:0;margin:30px 0 8px}}
  .sx{{padding:0 26px;border-left:1px solid {LINE}}}
  .sx:first-child{{padding-left:0;border-left:none}}
  .sx-n{{font-family:Futura,sans-serif;font-size:46px;font-weight:600;letter-spacing:-1px;line-height:1}}
  .sx-l{{font-size:12px;letter-spacing:2px;text-transform:uppercase;color:{MUTED};margin-top:8px}}
  .sx-s{{font-size:11.5px;letter-spacing:.5px;color:{MUTED};margin-top:6px;text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
  .sx-spk{{margin-top:10px}}
  .divider{{height:2px;background:{INK};margin:26px 0 4px}}
  .sec{{font-family:Futura,sans-serif;font-size:14px;font-weight:600;letter-spacing:2.5px;text-transform:uppercase;margin:22px 0 16px;display:flex;justify-content:space-between}}
  .sec span{{color:{MUTED};font-size:11px;letter-spacing:1.5px}}
  .film{{display:grid;grid-template-columns:repeat(4,1fr);gap:20px}}
  .fs-th{{display:block;position:relative;aspect-ratio:16/9;background:#ccc center/cover;border:1px solid {INK}}}
  .fs-th em{{position:absolute;right:6px;bottom:6px;background:{INK};color:{IVORY};font-style:normal;
    font-size:10.5px;font-weight:600;letter-spacing:.5px;padding:2px 6px}}
  .fs-t{{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;
    font-size:14px;font-weight:600;line-height:1.3;margin-top:11px}}
  .fs:hover .fs-t{{color:{TEAL}}}
  .fs-m{{display:block;font-size:11px;letter-spacing:1px;text-transform:uppercase;color:{MUTED};margin-top:5px}}
  .mpipe{{display:flex;align-items:center;gap:0;border:1px solid {INK};margin-top:4px}}
  .mp{{flex:1;text-align:center;padding:18px 8px}}
  .mp+.mp,.mp-x+.mp{{border-left:1px solid {LINE}}}
  .mp.ready{{background:{TEAL};color:{IVORY}}}
  .mp-n{{font-family:Futura,sans-serif;font-size:30px;font-weight:600;line-height:1}}
  .mp-l{{font-size:11px;letter-spacing:1.5px;text-transform:uppercase;color:{MUTED};margin-top:5px}}
  .mp.ready .mp-l{{color:{IVORY};opacity:.85}}
  .mp-x{{display:none}}
  .foot{{font-size:10.5px;letter-spacing:1.5px;text-transform:uppercase;color:{MUTED};margin-top:22px;text-align:center}}
  @media (max-width:820px){{.stats,.film{{grid-template-columns:repeat(2,1fr)}}}}
</style>'''

    body = f'''
  <div class="wrap">
    <div class="mast">
      <div class="brand">Creator&nbsp;<em>HQ</em></div>
      <div class="tag">{esc(m['name']).upper()}<br><b>{fmt_num(m['subs'])} SUBSCRIBERS</b><br>WK {m['wk']:02d} &middot; {m['week_label']}</div>
    </div>
    <div class="hero">
      <div class="hero-k">This Week</div>
      {hero}
    </div>
    <div class="stats">{stats}</div>
    <div class="divider"></div>
    <div class="sec">Recent Uploads<span>Newest First</span></div>
    <div class="film">{strip}</div>
    <div class="sec">Pipeline<span>{m['ptotal']} In Production</span></div>
    <div class="mpipe">{pipe}</div>
    <div class="foot">Creator HQ &middot; auto-pulled from YouTube &middot; targets {m['g_create']} created / {m['g_release']} released weekly</div>
  </div>'''
    return css, body


def write(name, css, body):
    doc = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
           '<title>Creator HQ</title>' + css + '</head><body>' + body + '</body></html>')
    (BASE / f"preview-{name}.html").write_text(doc)
    (BASE / f"{name}.artifact.html").write_text('<title>Creator HQ</title>' + css + body)
    print(f"Wrote preview-{name}.html + {name}.artifact.html")


def main():
    m = metrics()
    for name, fn in (("rundown", design_rundown), ("marquee", design_marquee)):
        css, body = fn(m)
        write(name, css, body)


if __name__ == "__main__":
    main()
