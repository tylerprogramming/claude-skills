#!/usr/bin/env python3
"""
model-bench: run the SAME prompt across multiple Claude models and capture
cost + time for each, saving runnable outputs and a side-by-side viewer.

Runs through the Claude Code CLI in headless mode (`claude -p ... --output-format
json`), so it uses your SUBSCRIPTION, not a separate API key. No per-token bill.
The "cost" column is the equivalent API cost, computed from the task tokens
(input + output) Claude Code reports, so models compare apples-to-apples.

Dependency-free (stdlib only).

Usage:
  python3 bench.py "<prompt>"
  python3 bench.py "<prompt>" --models opus-5,fable-5
  python3 bench.py "<prompt>" --models opus-4.8,opus-5,fable-5 --slug heptagon
  python3 bench.py --batch prompts.txt        # prompts separated by a line of ---
"""
import argparse
import datetime
import html as htmllib
import json
import os
import re
import subprocess
import sys
import time

# Friendly name -> full model id.
MODEL_ALIASES = {
    "opus-4.8": "claude-opus-4-8", "opus4.8": "claude-opus-4-8", "opus-4-8": "claude-opus-4-8",
    "opus-5": "claude-opus-5", "opus5": "claude-opus-5", "opus": "claude-opus-5",
    "fable-5": "claude-fable-5", "fable5": "claude-fable-5", "fable": "claude-fable-5",
    "sonnet-5": "claude-sonnet-5", "sonnet5": "claude-sonnet-5", "sonnet": "claude-sonnet-5",
    "sonnet-4.6": "claude-sonnet-4-6",
    "haiku-4.5": "claude-haiku-4-5", "haiku": "claude-haiku-4-5",
}

# Full model id -> (input $/1M, output $/1M). Add a row for any new model.
PRICES = {
    "claude-opus-4-8": (5.0, 25.0),
    "claude-opus-5": (5.0, 25.0),
    "claude-fable-5": (10.0, 50.0),
    "claude-sonnet-5": (3.0, 15.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
}

DEFAULT_MODELS = ["opus-4.8", "opus-5", "fable-5"]

# Tools disabled in headless mode so each run is a single-shot generation.
NO_TOOLS = ["Write", "Edit", "MultiEdit", "NotebookEdit", "Bash", "Read",
            "Glob", "Grep", "WebSearch", "WebFetch", "TodoWrite", "Task"]

# Output kind -> file extension.
EXT = {"html": "html", "svg": "svg", "py": "py", "js": "js", "text": "md"}

COMPARE_CSS = """
body{font-family:-apple-system,system-ui,sans-serif;margin:0;background:#f4f4f5;color:#18181b}
h1{font-size:16px;padding:12px 16px;margin:0;background:#fff;border-bottom:1px solid #e4e4e7}
.row{display:flex;gap:10px;padding:10px;overflow-x:auto}
.col{flex:1;min-width:360px;background:#fff;border:1px solid #e4e4e7;border-radius:8px;overflow:hidden;display:flex;flex-direction:column}
.hd{padding:8px 12px;border-bottom:1px solid #e4e4e7}
.meta{font-size:12px;color:#71717a}
iframe{width:100%;height:640px;border:0}
pre{margin:0;padding:12px;font-size:12px;overflow:auto;max-height:640px;white-space:pre-wrap}
.ans{font-size:15px}
.run{padding:8px 12px;background:#fef9c3;font-size:13px}
.fail{padding:24px;color:#b91c1c;text-align:center}
"""


# --- helpers ---------------------------------------------------------------

def resolve_model(name):
    return MODEL_ALIASES.get(name.strip().lower(), name.strip())


def slugify(text, maxlen=40):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (s[:maxlen] or "prompt").strip("-")


def cost_for(model_id, tin, tout):
    """Equivalent API cost for the task tokens, or None if the model has no price."""
    if model_id not in PRICES:
        return None
    pin, pout = PRICES[model_id]
    return (tin / 1_000_000.0) * pin + (tout / 1_000_000.0) * pout


def fmt_cost(cost):
    return "$%.4f" % cost if cost is not None else "unknown"


def detect_output(text):
    """Classify a model response. Returns (kind, body) with kind in EXT."""
    blocks = re.findall(r"```([\w+-]*)\n(.*?)```", text, re.DOTALL)
    if blocks:
        blocks.sort(key=lambda b: len(b[1]), reverse=True)  # largest code block wins
        lang, body = blocks[0][0].lower(), blocks[0][1].strip()
    else:
        lang, body = "", text.strip()
    low = body.lower()
    if lang in ("html", "xml") or low.startswith("<!doctype") or "<html" in low:
        return "html", body
    if lang == "svg" or low.startswith("<svg") or ("<svg" in low and "</svg>" in low):
        return "svg", body
    if lang in ("python", "py") or "import tkinter" in low or "import pygame" in low:
        return "py", body
    if lang in ("javascript", "js", "jsx", "typescript", "ts"):
        return "js", body
    return "text", (body if blocks else text.strip())


# --- model call ------------------------------------------------------------

def call_model(model_id, prompt, timeout):
    """Call the claude CLI headless. Returns a result dict (see keys below)."""
    cmd = ["claude", "-p", prompt, "--model", model_id,
           "--output-format", "json", "--disallowedTools", *NO_TOOLS]
    start = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"timeout after {timeout}s", "time": time.time() - start}
    except FileNotFoundError:
        return {"ok": False, "error": "claude CLI not found on PATH", "time": time.time() - start}
    elapsed = time.time() - start

    out = proc.stdout.strip()
    if not out:
        return {"ok": False, "error": f"no output (exit {proc.returncode}): {proc.stderr[:200]}", "time": elapsed}
    try:
        data = json.loads(out.splitlines()[-1])
    except (ValueError, IndexError):
        return {"ok": False, "error": f"unparseable output: {out[:200]}", "time": elapsed}
    if data.get("is_error"):
        return {"ok": False, "error": str(data.get("result", ""))[:250], "time": elapsed}

    # Pull the target model's own usage out of modelUsage (ignores Claude Code's
    # internal helper calls and its cached system prompt).
    usage = _model_usage(data, model_id)
    dur = data.get("duration_ms")
    return {
        "ok": True,
        "text": data.get("result", ""),
        "in": usage["in"],
        "out": usage["out"],
        "cc_cost": usage["cc_cost"],
        "session_total_usd": data.get("total_cost_usd"),
        "time": dur / 1000.0 if dur else elapsed,
    }


def _model_usage(data, model_id):
    for key, val in (data.get("modelUsage") or {}).items():
        if val.get("canonicalModel") == model_id or key == model_id or key.startswith(model_id):
            return {"in": val.get("inputTokens", 0), "out": val.get("outputTokens", 0),
                    "cc_cost": val.get("costUSD")}
    u = data.get("usage", {})  # fallback
    return {"in": u.get("input_tokens", 0), "out": u.get("output_tokens", 0), "cc_cost": None}


# --- run + reporting -------------------------------------------------------

def run_one(prompt, models, outdir, timeout, do_open):
    os.makedirs(outdir, exist_ok=True)
    _write(os.path.join(outdir, "prompt.txt"), prompt + "\n")

    results = []
    for name in models:
        model_id = resolve_model(name)
        r = dict(name=name, model_id=model_id, label=slugify(name, 20))
        print(f"  -> {name} ({model_id}) ...", flush=True)
        r.update(call_model(model_id, prompt, timeout))
        if r["ok"]:
            kind, body = detect_output(r["text"])
            r["kind"] = kind
            r["file"] = f"{r['label']}.{EXT[kind]}"
            r["cost"] = cost_for(model_id, r["in"], r["out"])
            _write(os.path.join(outdir, r["file"]), body)
            print(f"     {r['in']} in / {r['out']} out  |  {fmt_cost(r['cost'])}  |  {r['time']:.1f}s  |  {kind}")
        else:
            print(f"     FAILED: {r['error']}")
        results.append(r)

    write_results_md(prompt, results, outdir)
    write_results_json(prompt, results, outdir)
    build_compare_html(prompt, results, outdir)

    compare = os.path.join(outdir, "compare.html")
    if do_open and sys.platform == "darwin" and os.path.exists(compare):
        subprocess.run(["open", compare], check=False)
    return results


def write_results_md(prompt, results, outdir):
    table = ["| Model | In | Out | Cost | Time | Type | Output | Runs? | Score |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        if r["ok"]:
            table.append(f"| {r['name']} | {r['in']} | {r['out']} | {fmt_cost(r['cost'])} | "
                         f"{r['time']:.1f}s | {r['kind']} | `{r['file']}` |  |  |")
        else:
            table.append(f"| {r['name']} | - | - | - | {r['time']:.1f}s | FAILED | {r['error'][:60]} |  |  |")

    header = ["# model-bench results\n", f"**Prompt:** {prompt}\n",
              "_Cost = equivalent API cost from task tokens (subscription run, no real charge)._\n"]
    footer = "\n_Fill in Runs? and Score by opening/running each output._\n"
    _write(os.path.join(outdir, "results.md"), "\n".join(header + table) + footer)
    print("\n" + "\n".join(table))


def write_results_json(prompt, results, outdir):
    payload = {"prompt": prompt,
               "results": [{k: v for k, v in r.items() if k != "text"} for r in results]}
    _write(os.path.join(outdir, "results.json"), json.dumps(payload, indent=2))


def build_compare_html(prompt, results, outdir):
    cols = [_compare_col(r, outdir) for r in results]
    page = (f"<!doctype html><html><head><meta charset=utf-8><title>model-bench</title>"
            f"<style>{COMPARE_CSS}</style></head><body>"
            f"<h1>Prompt: {htmllib.escape(prompt)}</h1>"
            f"<div class='row'>{''.join(cols)}</div></body></html>")
    _write(os.path.join(outdir, "compare.html"), page)


def _compare_col(r, outdir):
    if not r["ok"]:
        meta = "failed"
        inner = f"<div class='fail'>FAILED<br><small>{htmllib.escape(r['error'][:200])}</small></div>"
    else:
        meta = f"{fmt_cost(r['cost'])} &middot; {r['time']:.1f}s &middot; {r['in']}/{r['out']} tok"
        inner = _compare_body(r, outdir)
    return (f"<div class='col'><div class='hd'><b>{htmllib.escape(r['name'])}</b>"
            f"<div class='meta'>{meta}</div></div>{inner}</div>")


def _compare_body(r, outdir):
    if r["kind"] in ("html", "svg"):
        return f"<iframe src='{r['file']}'></iframe>"
    body = _read(os.path.join(outdir, r["file"]))
    if r["kind"] in ("py", "js"):
        runcmd = f"python3 {r['file']}" if r["kind"] == "py" else f"node {r['file']}"
        head = "\n".join(body.splitlines()[:60])
        return f"<div class='run'>Run: <code>{htmllib.escape(runcmd)}</code></div><pre>{htmllib.escape(head)}</pre>"
    return f"<pre class='ans'>{htmllib.escape(body)}</pre>"


def _write(path, text):
    with open(path, "w") as f:
        f.write(text)


def _read(path):
    with open(path) as f:
        return f.read()


# --- cli -------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Benchmark one prompt across Claude models (cost + time).")
    ap.add_argument("prompt", nargs="?", help="The prompt to send to every model")
    ap.add_argument("--models", default=",".join(DEFAULT_MODELS),
                    help="Comma-separated model names (default: opus-4.8,opus-5,fable-5)")
    ap.add_argument("--slug", help="Folder name slug")
    ap.add_argument("--outdir", help="Explicit output dir")
    ap.add_argument("--timeout", type=int, default=900, help="Per-model timeout in seconds")
    ap.add_argument("--batch", help="File of prompts separated by a line of ---")
    ap.add_argument("--no-open", action="store_true", help="Do not auto-open compare.html")
    args = ap.parse_args()

    models = [m for m in args.models.split(",") if m.strip()]
    base = os.path.expanduser("~/content/research/benchmarks")
    date = datetime.date.today().isoformat()

    if args.batch:
        prompts = [p.strip() for p in _read(args.batch).split("\n---\n") if p.strip()]
        print(f"Batch: {len(prompts)} prompts x {len(models)} models\n")
        for i, prompt in enumerate(prompts, 1):
            outdir = os.path.join(base, f"{date}-batch-{i:02d}-{slugify(prompt, 24)}")
            print(f"[{i}/{len(prompts)}] {prompt[:60]}")
            run_one(prompt, models, outdir, args.timeout, not args.no_open)
        return

    if not args.prompt:
        sys.exit("ERROR: provide a prompt (or use --batch <file>)")
    outdir = args.outdir or os.path.join(base, args.slug or f"{date}-{slugify(args.prompt)}")
    print(f"Prompt: {args.prompt}\nModels: {', '.join(models)}\nOut: {outdir}\n")
    run_one(args.prompt, models, outdir, args.timeout, not args.no_open)


if __name__ == "__main__":
    main()
