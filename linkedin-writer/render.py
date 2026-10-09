#!/usr/bin/env python3
"""Render LinkedIn creatives from HTML to PNG with headless Chrome.

Exact label text every time, which AI image generators cannot guarantee.

  python3 render.py spec.json outdir/            # THEME=electric by default

Palette comes from ~/social-studio/themes/<id>.json, the SAME source of truth
/instagram-writer uses, so LinkedIn and Instagram stay on one brand. Override
with THEME=midnight, THEME=terminal, etc.

spec.json: {"width":1200,"height":680,"slides":[{"name":"01","html":"...","extra":"..."}]}
`html` is BODY content. `extra` is optional per-slide CSS.
"""
import json, os, subprocess, sys, pathlib

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

def load_theme(name=None):
    name = name or os.environ.get("THEME", "electric")
    fb = {"bgColor": "#F7F8FA", "textColor": "#0A0A0A", "accentColor": "#2454F0"}
    p = pathlib.Path.home() / "social-studio" / "themes" / f"{name}.json"
    try:
        t = json.loads(p.read_text())
        return t if all(k in t for k in fb) else fb
    except Exception:
        return fb

T = load_theme()
# Electric, read from ~/social-studio/themes/electric.json - the same palette
# /instagram-writer renders with. Ground carries a faint dot grid; ONE accent,
# used only to mark the thing that matters. Dark surfaces lift the accent.
GROUND, INK, ACCENT = T["bgColor"], T["textColor"], T["accentColor"]
DOT, MUT, LIFT = "#D7D7E2", "#8A8A99", "#5B82F5"

STYLE = f"""
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--gd:{GROUND};--ink:{INK};--ac:{ACCENT};--mut:{MUT};--lift:{LIFT}}}
body{{background:{GROUND};color:{INK};overflow:hidden;
     font-family:"Helvetica Neue",Arial,sans-serif;display:flex;flex-direction:column;
     background-image:radial-gradient(circle,{DOT} 1.6px,transparent 1.6px);
     background-size:37px 37px}}
.mono{{font-family:"SF Mono",Menlo,monospace}}
.rail{{display:flex;align-items:center;gap:18px;padding:26px 44px 0;
      font-family:"SF Mono",Menlo,monospace;font-size:19px;letter-spacing:4px;color:{MUT}}}
.pill{{border:2px solid var(--ac);border-radius:9px;padding:6px 14px;color:var(--ac);
      letter-spacing:2px;font-weight:700}}
.hr{{height:1px;background:#DFDFE8;margin:16px 44px 0}}
.ttl{{padding:16px 44px 0;font-size:58px;font-weight:800;letter-spacing:-2.4px;text-transform:uppercase}}
.ttl .ac{{color:var(--ac)}}
.grid{{flex:1;display:flex;align-items:stretch;gap:15px;padding:18px 44px 8px}}
.col{{display:flex;flex-direction:column;gap:10px;flex:1;justify-content:space-between}}
.lbl{{font-family:"SF Mono",Menlo,monospace;font-size:14px;color:{MUT};letter-spacing:2.6px}}
.lbl.ac{{color:var(--ac)}}
.bx{{background:#fff;border:1.5px solid #E3E3EC;border-radius:13px;padding:15px 16px;
    box-shadow:0 1px 2px rgba(10,10,30,.04)}}
.bt{{font-size:20px;font-weight:750;line-height:1.15}}
.bs{{font-size:14px;color:{MUT};margin-top:4px;line-height:1.25}}
.ar{{color:var(--ac);font-size:38px;flex-shrink:0;align-self:center}}
.hub{{background:#fff;border:2.5px solid var(--ac);border-radius:15px;padding:22px;
     text-align:center;flex:1;display:flex;flex-direction:column;justify-content:center;
     box-shadow:0 3px 14px rgba(36,84,240,.10)}}
.ht{{font-size:33px;font-weight:800;line-height:1.1;letter-spacing:-1.1px}}
.hs{{font-size:20px;color:var(--ac);font-weight:700;margin-top:6px}}
.chip{{display:inline-block;background:var(--ac);color:#fff;font-family:"SF Mono",Menlo,monospace;
      font-size:19px;font-weight:700;border-radius:7px;padding:7px 15px;margin-top:15px}}
.hn{{font-size:14px;color:{MUT};margin-top:13px}}
.band{{margin:0 44px;background:#fff;border:1.5px solid #E3E3EC;border-radius:12px;
      padding:13px 18px;display:flex;align-items:center;gap:11px}}
.bl{{font-family:"SF Mono",Menlo,monospace;font-size:14px;color:{MUT};letter-spacing:2.6px;margin-right:4px}}
.pl{{background:#EEF1FE;border-radius:20px;padding:7px 16px;font-size:17px;font-weight:650}}
.pl.hi{{background:var(--ac);color:#fff}}
.ftr{{margin-top:auto;padding:18px 44px 26px;display:flex;justify-content:space-between;
     align-items:center;font-family:"SF Mono",Menlo,monospace;font-size:18px;
     letter-spacing:3px;color:{MUT};border-top:1px solid #DFDFE8;margin-left:44px;margin-right:44px;
     padding-left:0;padding-right:0}}
"""


def render_pdf(spec, outpath):
    """Multi-page PDF for a LinkedIn document post. Pages are the same house
    style as slides; each `slides` entry becomes one page."""
    w, h = spec.get("width", 1080), spec.get("height", 1350)
    pages = "".join(
        f'<div class="page" style="width:{w}px;height:{h}px">{s["html"]}</div>'
        for s in spec["slides"])
    extra = "".join(s.get("extra", "") for s in spec["slides"])
    html = (f"<!doctype html><html><head><meta charset='utf-8'><style>"
            f"@page{{size:{w}px {h}px;margin:0}}"
            f"{STYLE}{extra}"
            f".page{{position:relative;display:flex;flex-direction:column;"
            f"break-after:page;page-break-after:always;overflow:hidden}}"
            f".page:last-child{{break-after:auto;page-break-after:auto}}"
            f"body{{display:block;width:auto;height:auto}}"
            f"</style></head><body>{pages}</body></html>")
    tmp = pathlib.Path(outpath).with_suffix(".html")
    tmp.write_text(html)
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                    "--no-pdf-header-footer", f"--print-to-pdf={outpath}",
                    f"file://{tmp}"], capture_output=True)
    print("pdf written", outpath)


def main():
    spec = json.load(open(sys.argv[1]))
    if sys.argv[2].endswith(".pdf"):
        return render_pdf(spec, sys.argv[2])
    out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    w, h = spec.get("width", 1200), spec.get("height", 680)
    tmp = out / "_html"; tmp.mkdir(exist_ok=True)
    for s in spec["slides"]:
        f = tmp / f"{s['name']}.html"
        f.write_text(f"<!doctype html><html><head><meta charset='utf-8'><style>"
                     f"body{{width:{w}px;height:{h}px;position:relative}}{STYLE}{s.get('extra','')}"
                     f"</style></head><body>{s['html']}</body></html>")
        png = out / f"{s['name']}.png"
        subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                        f"--screenshot={png}", f"--window-size={w},{h}", f"file://{f}"],
                       capture_output=True)
        print("rendered", png)

if __name__ == "__main__":
    main()
