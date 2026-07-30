# model-bench

Run the SAME prompt across multiple Claude models and capture **cost + time** for each. Saves each model's output to a runnable file, builds a side-by-side `compare.html` viewer, and writes a `results.md` scoring table. Built for head-to-head model comparisons (e.g. Opus 4.8 vs Opus 5 vs Fable 5).

## How it runs (important)

It drives the **Claude Code CLI in headless mode** (`claude -p ... --output-format json`), so every call runs on the user's **subscription** - no API key, no per-token bill. The **Cost** column is the *equivalent* API cost, computed from the task tokens Claude Code reports (input + output), so models compare apples-to-apples. Requires the `claude` CLI on PATH and an active login (already true if Claude Code works).

## Instructions

1. Parse the user's request for:
   - **the prompt** (the benchmark task to run)
   - **the models** they want (default: `opus-4.8,opus-5,fable-5`). Friendly names: `opus-4.8`, `opus-5`, `fable-5`, `sonnet-5`, `haiku-4.5`, or any full model id.

2. Run the script:
   ```
   python3 ~/.claude/skills/model-bench/bench.py "<prompt>" --models <m1,m2,m3>
   ```
   Options: `--slug <name>` to name the folder, `--batch <file>` to run many prompts (separated by a line of `---`), `--timeout <sec>` per model, `--no-open` to skip auto-opening the viewer.

3. The script, per model:
   - Calls `claude` headless with tools disabled (single-shot generation), capturing the output, **task tokens**, **cost** (tokens x that model's price), and **wall-clock time**.
   - Auto-detects the output type and saves it: HTML / SVG / three.js -> `.html`/`.svg` (opened in a browser); Python (e.g. tkinter) -> `.py` (prints the run command, does NOT auto-run); text/reasoning -> shown inline.
   - Writes to `~/content/research/benchmarks/<date>-<slug>/`: `prompt.txt`, one file per model, `results.md`, `results.json`, and `compare.html` (auto-opened on macOS).

4. After it runs, present the `results.md` table and point to `compare.html`. Remind the user the **Runs?** and **Score** columns are filled in by opening/running each output (cost and time are already captured).

## Adding a model

Prices live in the `PRICES` dict in `bench.py` (input $/1M, output $/1M). Any model not in the table still runs; its cost shows as `unknown` until a price row is added. Friendly-name aliases live in `MODEL_ALIASES`.

## Notes

- Dependency-free (stdlib only); runs on any Python 3.9+.
- **Single-shot generation** (Claude Code headless with tools disabled), not a full agentic session. Intentional for a fair, controlled benchmark - say so on camera.
- Reported cost excludes Claude Code's shared system-prompt overhead, so it reflects the task generation itself.
- Generated Python is never executed automatically. Opening HTML runs its JS in the browser sandbox (fine); running a `.py` executes code locally, so that stays the user's manual step.
