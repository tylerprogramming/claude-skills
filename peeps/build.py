#!/usr/bin/env python3
"""Build ~/peeps/index.html from all person JSON files in ~/peeps/data/.

The page is fully self-contained: person data is inlined as a JS array, so it
works offline with no server. Birthdays/ages are computed client-side so the
page stays accurate over time without rebuilding.
"""

import json
import os
import glob

HOME = os.path.expanduser("~")
PEEPS_DIR = os.path.join(HOME, "peeps")
DATA_DIR = os.path.join(PEEPS_DIR, "data")
OUT_FILE = os.path.join(PEEPS_DIR, "index.html")


def load_people():
    people = []
    for path in sorted(glob.glob(os.path.join(DATA_DIR, "*.json"))):
        try:
            with open(path, "r", encoding="utf-8") as f:
                people.append(json.load(f))
        except (json.JSONDecodeError, OSError) as e:
            print(f"  ! skipped {os.path.basename(path)}: {e}")
    return people


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Peeps</title>
<style>
  :root {
    --bg: #f6f7f9; --card: #ffffff; --ink: #1d2129; --muted: #6b7280;
    --line: #e6e8eb; --accent: #4f46e5; --accent-soft: #eef2ff; --chip: #f0f1f3;
    --shadow: 0 1px 3px rgba(0,0,0,.06), 0 8px 24px rgba(0,0,0,.05);
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0f1115; --card: #1a1d24; --ink: #e9ebef; --muted: #9aa3b2;
      --line: #272b34; --accent: #8b87ff; --accent-soft: #20223a; --chip: #232732;
      --shadow: 0 1px 3px rgba(0,0,0,.4), 0 8px 24px rgba(0,0,0,.35);
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--ink);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  .wrap { max-width: 1100px; margin: 0 auto; padding: 32px 20px 80px; }
  header h1 { font-size: 30px; margin: 0 0 4px; letter-spacing: -.02em; }
  header p { color: var(--muted); margin: 0 0 24px; }
  .controls { position: sticky; top: 0; background: var(--bg); padding: 12px 0;
    z-index: 5; margin-bottom: 8px; }
  #search {
    width: 100%; padding: 13px 16px; font-size: 16px; border: 1px solid var(--line);
    border-radius: 12px; background: var(--card); color: var(--ink); outline: none;
  }
  #search:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
  .pills { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
  .pill {
    border: 1px solid var(--line); background: var(--card); color: var(--muted);
    padding: 6px 13px; border-radius: 999px; font-size: 13px; cursor: pointer;
    user-select: none; transition: all .12s;
  }
  .pill.active { background: var(--accent); border-color: var(--accent); color: #fff; }
  .bdays { background: var(--accent-soft); border: 1px solid var(--line);
    border-radius: 14px; padding: 14px 18px; margin: 16px 0 24px; }
  .bdays h2 { font-size: 13px; text-transform: uppercase; letter-spacing: .06em;
    color: var(--muted); margin: 0 0 10px; }
  .bdays ul { list-style: none; margin: 0; padding: 0; display: flex;
    flex-wrap: wrap; gap: 8px 18px; }
  .bdays li { font-size: 14px; }
  .bdays b { color: var(--accent); }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 16px; }
  .card {
    background: var(--card); border: 1px solid var(--line); border-radius: 16px;
    padding: 18px; box-shadow: var(--shadow); cursor: pointer; transition: transform .12s;
  }
  .card:hover { transform: translateY(-2px); }
  .card-top { display: flex; gap: 14px; align-items: center; }
  .avatar { width: 52px; height: 52px; border-radius: 50%; flex: 0 0 auto;
    object-fit: cover; display: flex; align-items: center; justify-content: center;
    font-weight: 600; font-size: 19px; color: #fff; }
  .name { font-weight: 600; font-size: 17px; line-height: 1.2; }
  .nick { color: var(--muted); font-size: 13px; }
  .meta { color: var(--muted); font-size: 13px; margin-top: 3px; }
  .bday-badge { display: inline-block; margin-top: 8px; font-size: 12px;
    background: var(--accent-soft); color: var(--accent); padding: 3px 9px;
    border-radius: 999px; font-weight: 600; }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
  .chip { background: var(--chip); color: var(--muted); font-size: 12px;
    padding: 3px 10px; border-radius: 999px; }
  .detail { display: none; margin-top: 14px; padding-top: 14px;
    border-top: 1px solid var(--line); font-size: 14px; }
  .card.open .detail { display: block; }
  .detail .row { margin: 7px 0; }
  .detail .label { color: var(--muted); font-size: 12px; text-transform: uppercase;
    letter-spacing: .04em; }
  .detail a { color: var(--accent); text-decoration: none; }
  .detail .notes { margin-top: 10px; white-space: pre-wrap; }
  .empty { text-align: center; color: var(--muted); padding: 60px 0; }
  footer { text-align: center; color: var(--muted); font-size: 12px; margin-top: 40px; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Peeps</h1>
    <p id="count"></p>
  </header>
  <div class="controls">
    <input id="search" type="search" placeholder="Search name, location, tags, interests, notes...">
    <div class="pills" id="pills"></div>
  </div>
  <div class="bdays" id="bdays" style="display:none">
    <h2>Upcoming birthdays</h2>
    <ul id="bdayList"></ul>
  </div>
  <div class="grid" id="grid"></div>
  <div class="empty" id="empty" style="display:none">No one matches that search.</div>
  <footer>Generated from ~/peeps/data &middot; edit the JSON and rerun build.py</footer>
</div>
<script>
const PEOPLE = __DATA__;

const COLORS = ["#4f46e5","#0ea5e9","#10b981","#f59e0b","#ef4444","#ec4899","#8b5cf6","#14b8a6"];
function colorFor(s){let h=0;for(let i=0;i<s.length;i++)h=s.charCodeAt(i)+((h<<5)-h);return COLORS[Math.abs(h)%COLORS.length];}
function initials(name){return (name||"?").split(/\\s+/).slice(0,2).map(w=>w[0]||"").join("").toUpperCase();}
function esc(s){return (s==null?"":String(s)).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));}

function bdayInfo(p){
  const b=p.dates&&p.dates.birthday; if(!b) return null;
  const m=b.match(/^(?:(\\d{4})|-)?-?(\\d{2})-(\\d{2})$/)||b.match(/^(\\d{4})-(\\d{2})-(\\d{2})$/);
  if(!m) return null;
  let year,mo,day;
  if(b.startsWith("--")){const mm=b.match(/^--(\\d{2})-(\\d{2})$/);if(!mm)return null;year=null;mo=+mm[1];day=+mm[2];}
  else{const mm=b.match(/^(\\d{4})-(\\d{2})-(\\d{2})$/);if(!mm)return null;year=+mm[1];mo=+mm[2];day=+mm[3];}
  const now=new Date();const today=new Date(now.getFullYear(),now.getMonth(),now.getDate());
  let next=new Date(now.getFullYear(),mo-1,day);
  if(next<today) next=new Date(now.getFullYear()+1,mo-1,day);
  const days=Math.round((next-today)/86400000);
  let age=null; if(year){age=next.getFullYear()-year;}
  const dateStr=new Date(2000,mo-1,day).toLocaleDateString(undefined,{month:"short",day:"numeric"});
  return {days,age,dateStr};
}
function bdayLabel(info){
  if(info.days===0) return "🎂 Today!";
  if(info.days===1) return "🎂 Tomorrow";
  if(info.days<=30) return "🎂 in "+info.days+" days";
  return "🎂 "+info.dateStr;
}

let activeTag=null;
const allTags=[...new Set(PEOPLE.flatMap(p=>p.tags||[]))].sort();

function searchText(p){
  return [p.name,p.nickname,p.location,p.how_we_met,p.notes,
    (p.tags||[]).join(" "),(p.interests||[]).join(" "),
    p.relationships&&p.relationships.partner,
    (p.relationships&&p.relationships.kids||[]).join(" ")
  ].filter(Boolean).join(" ").toLowerCase();
}

function detailHtml(p){
  const r=[];const rel=p.relationships||{};const c=p.contact||{};const d=p.dates||{};
  const line=(label,val)=>val?`<div class="row"><span class="label">${label}</span><br>${val}</div>`:"";
  if(c.phone) r.push(line("Phone",`<a href="tel:${esc(c.phone)}">${esc(c.phone)}</a>`));
  if(c.email) r.push(line("Email",`<a href="mailto:${esc(c.email)}">${esc(c.email)}</a>`));
  if(c.socials){const s=Object.entries(c.socials).filter(([k,v])=>v).map(([k,v])=>`${esc(k)}: ${esc(v)}`).join(" &middot; ");if(s)r.push(line("Social",s));}
  if(d.anniversary) r.push(line("Anniversary",esc(d.anniversary)));
  if(d.met_on) r.push(line("Met on",esc(d.met_on)));
  if(rel.partner) r.push(line("Partner",esc(rel.partner)));
  if(rel.kids&&rel.kids.length) r.push(line("Kids",esc(rel.kids.join(", "))));
  if(rel.family_notes) r.push(line("Family",esc(rel.family_notes)));
  if(p.interests&&p.interests.length) r.push(line("Interests",esc(p.interests.join(", "))));
  if(p.gift_ideas&&p.gift_ideas.length) r.push(line("Gift ideas",esc(p.gift_ideas.join(", "))));
  if(p.notes) r.push(`<div class="notes">${esc(p.notes)}</div>`);
  return r.join("");
}

function render(){
  const q=document.getElementById("search").value.trim().toLowerCase();
  const grid=document.getElementById("grid");grid.innerHTML="";
  let shown=0;
  PEOPLE.forEach(p=>{
    if(activeTag&&!(p.tags||[]).includes(activeTag)) return;
    if(q&&!searchText(p).includes(q)) return;
    shown++;
    const info=bdayInfo(p);
    const card=document.createElement("div");card.className="card";
    const av=p.photo?`<img class="avatar" src="${esc(p.photo)}" alt="">`:
      `<div class="avatar" style="background:${colorFor(p.name||"")}">${esc(initials(p.name))}</div>`;
    card.innerHTML=`
      <div class="card-top">
        ${av}
        <div>
          <div class="name">${esc(p.name)}${p.nickname?` <span class="nick">"${esc(p.nickname)}"</span>`:""}</div>
          ${p.how_we_met?`<div class="meta">${esc(p.how_we_met)}</div>`:""}
          ${p.location?`<div class="meta">📍 ${esc(p.location)}</div>`:""}
        </div>
      </div>
      ${info?`<div class="bday-badge">${bdayLabel(info)}${info.age?` &middot; turning ${info.age}`:""}</div>`:""}
      ${(p.tags||[]).length?`<div class="chips">${p.tags.map(t=>`<span class="chip">${esc(t)}</span>`).join("")}</div>`:""}
      <div class="detail">${detailHtml(p)}</div>`;
    card.addEventListener("click",()=>card.classList.toggle("open"));
    grid.appendChild(card);
  });
  document.getElementById("empty").style.display=shown?"none":"block";
}

function renderBdays(){
  const up=PEOPLE.map(p=>({p,info:bdayInfo(p)})).filter(x=>x.info&&x.info.days<=45)
    .sort((a,b)=>a.info.days-b.info.days);
  const box=document.getElementById("bdays");const list=document.getElementById("bdayList");
  if(!up.length){box.style.display="none";return;}
  box.style.display="block";
  list.innerHTML=up.map(x=>`<li><b>${esc(x.p.name)}</b> — ${bdayLabel(x.info).replace("🎂 ","")}</li>`).join("");
}

function renderPills(){
  const wrap=document.getElementById("pills");
  allTags.forEach(t=>{
    const el=document.createElement("span");el.className="pill";el.textContent=t;
    el.addEventListener("click",()=>{
      activeTag=activeTag===t?null:t;
      [...wrap.children].forEach(c=>c.classList.toggle("active",c.textContent===activeTag));
      render();
    });
    wrap.appendChild(el);
  });
}

document.getElementById("count").textContent=PEOPLE.length+" "+(PEOPLE.length===1?"person":"people");
document.getElementById("search").addEventListener("input",render);
renderPills();renderBdays();render();
</script>
</body>
</html>
"""


def main():
    people = load_people()
    data_json = json.dumps(people, ensure_ascii=False)
    html = HTML_TEMPLATE.replace("__DATA__", data_json)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Built {OUT_FILE} with {len(people)} {'person' if len(people)==1 else 'people'}.")


if __name__ == "__main__":
    main()
