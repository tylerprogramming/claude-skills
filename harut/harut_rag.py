#!/usr/bin/env python3
"""
Harut RAG - Ask questions about Harut Martirosyan's 100k/month business teachings.

Usage:
  python harut_rag.py status                        - Check if index is built
  python harut_rag.py index <transcript_path>       - Build vector index from transcript
  python harut_rag.py query "<your question>"       - Ask a question
"""

import sys
import os
import re
import json
import subprocess
from pathlib import Path

# ── Auto-install dependencies ─────────────────────────────────────────────────

def pip_install(*packages):
    subprocess.run([sys.executable, "-m", "pip", "install", *packages, "-q"], check=True)

try:
    import numpy as np
except ImportError:
    print("Installing numpy...")
    pip_install("numpy")
    import numpy as np

try:
    from openai import OpenAI
except ImportError:
    print("Installing openai...")
    pip_install("openai")
    from openai import OpenAI

# ── Config ────────────────────────────────────────────────────────────────────

SKILL_DIR   = Path.home() / ".claude" / "skills" / "harut"
DB_DIR      = SKILL_DIR / "chroma_db"
COLLECTION  = "harut"
EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL  = "gpt-5-mini"
CHUNK_WORDS = 1000   # target words per chunk
OVERLAP_LINES = 5    # lines of overlap between chunks to avoid hard cuts
TOP_K       = 10     # chunks to retrieve per query

# ── Who is Harut — baked-in context ───────────────────────────────────────────

SYSTEM_PROMPT = """You are an AI business advisor that has deeply studied Harut Martirosyan's complete 21-hour masterclass on growing a business to $100k/month.

ABOUT HARUT MARTIROSYAN:
- Business coach, personal brand strategist, and Skool investor
- Started at age 13 making his first $4 online; by early 20s had made $1M+ online
- Built and exited multiple YouTube channels (including 70K subscriber channel)
- Generated 1B+ organic views across platforms
- Scaled a Skool community to $210K revenue in 90 days with 1.5% churn
- Won Skool Games 2024. Personal investor in Skool (co-owned by Alex Hormozi)
- Now has 100K+ followers and runs the "Achieve Greatness Accelerator" (private coaching)

HARUT'S CORE FRAMEWORK — THE P.R.O.F.I.T. SYSTEM:
The 6 critical constraints stopping people from reaching $100K/month:
1. Not enough hot leads
2. Not enough profit
3. Low conversion/close rate
4. Lost sales and leakages in the funnel
5. No client results, or it entirely relies on your time
6. Low-leverage team and lack of systems

His solution pillars: Skill (base ability) × Leverage (systems + reach) × Reputation (authority + trust)

HARUT'S KEY PRINCIPLES:
- Organic growth over paid ads — content is the client-generation machine
- Personal brand as the foundation — you ARE the business
- Community-driven recurring revenue (Skool is his primary vehicle)
- Case study selling — demonstrate outcomes, not outputs
- Constraint analysis — find the ONE thing actually blocking your growth
- Systems obsession — remove yourself as the bottleneck
- Lifestyle-first design — build the business around your desired life

YOU ARE ADVISING TYLER REED:
Tyler's business context:
- Creates YouTube content about AI tools — primarily Claude Code, automation, AI workflows
- Runs a Skool community for his audience
- Active on: YouTube (long-form + Shorts), LinkedIn, Instagram, TikTok, X/Twitter
- Uses Claude Code skills to automate his entire content workflow
- Weekly output: 2 long-form YT videos, 5 Shorts, LinkedIn posts daily, IG carousels, TikToks
- Goal: reach $100k/month revenue

WHEN ANSWERING:
1. Ground your answer in the actual transcript excerpts provided — quote or paraphrase Harut's words
2. Apply it SPECIFICALLY to Tyler's AI content creator + Skool business
3. Be direct and tactical — tell Tyler exactly what to DO
4. Reference the timestamp when relevant (e.g. "At 3:42:00 Harut explains...")
5. End with 2-3 concrete next actions Tyler can take this week
6. Harut's tone is direct, confident, no fluff — match that energy"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_env():
    env_path = Path.home() / ".claude" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

INDEX_FILE = SKILL_DIR / "harut_index.json"  # stores chunks + embeddings

def get_client():
    load_env()
    return OpenAI()

def save_index(chunks, embeddings):
    """Save chunks and embeddings to disk as JSON."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "chunks": chunks,
        "embeddings": [e.tolist() for e in embeddings],
    }
    INDEX_FILE.write_text(json.dumps(data))
    print(f"Index saved to {INDEX_FILE}")

def load_index():
    """Load index from disk. Returns (chunks, embeddings_array)."""
    if not INDEX_FILE.exists():
        raise FileNotFoundError(f"No index at {INDEX_FILE}")
    data = json.loads(INDEX_FILE.read_text())
    embeddings = np.array(data["embeddings"], dtype=np.float32)
    return data["chunks"], embeddings

def cosine_similarity(query_vec, matrix):
    """Return cosine similarities between query_vec and each row of matrix."""
    q = query_vec / (np.linalg.norm(query_vec) + 1e-10)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10
    normed = matrix / norms
    return normed @ q

def parse_transcript(text):
    """
    Parse timestamped transcript into a list of (timestamp_str, seconds, text) tuples.
    Handles both [MM:SS] and [HH:MM:SS] formats.
    """
    lines = []
    pattern = re.compile(r"^\[(\d{1,2}:\d{2}(?::\d{2})?)\]\s*(.+)$")
    for line in text.splitlines():
        m = pattern.match(line.strip())
        if m:
            ts_str, content = m.group(1), m.group(2).strip()
            parts = ts_str.split(":")
            if len(parts) == 2:
                seconds = int(parts[0]) * 60 + int(parts[1])
            else:
                seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            lines.append((ts_str, seconds, content))
    return lines

def chunk_by_words(lines, chunk_words=CHUNK_WORDS, overlap_lines=OVERLAP_LINES):
    """
    Group timestamped lines into chunks of ~chunk_words words.
    Each chunk includes start/end timestamps and the combined text.
    Uses line-level overlap so chunks don't hard-cut mid-thought.
    """
    chunks = []
    i = 0
    while i < len(lines):
        chunk_lines = []
        word_count = 0
        j = i
        while j < len(lines) and word_count < chunk_words:
            chunk_lines.append(lines[j])
            word_count += len(lines[j][2].split())
            j += 1

        if not chunk_lines:
            break

        start_ts  = chunk_lines[0][0]
        start_sec = chunk_lines[0][1]
        end_ts    = chunk_lines[-1][0]
        end_sec   = chunk_lines[-1][1]

        # Combine into readable text (keep timestamps inline for context)
        text = " ".join(line[2] for line in chunk_lines)

        chunks.append({
            "text":      text,
            "start_ts":  start_ts,
            "end_ts":    end_ts,
            "start_sec": start_sec,
            "end_sec":   end_sec,
        })

        # Advance, stepping back by overlap_lines for continuity
        i = max(i + 1, j - overlap_lines)

    return chunks

# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_status():
    if INDEX_FILE.exists():
        data = json.loads(INDEX_FILE.read_text())
        count = len(data["chunks"])
        size_mb = INDEX_FILE.stat().st_size / (1024 * 1024)
        print(f"Harut index: {count} chunks ({size_mb:.1f}MB) at {INDEX_FILE}")
        print("Ready. Run: python harut_rag.py query \"<your question>\"")
    else:
        print("No index found.")
        print("Run: python harut_rag.py index ~/scripts/transcript_u2hmXbhTTLE.txt")


def cmd_index(transcript_path):
    path = Path(transcript_path).expanduser()
    if not path.exists():
        print(f"Transcript not found: {path}")
        sys.exit(1)

    print(f"Parsing transcript: {path}")
    text  = path.read_text(encoding="utf-8")
    lines = parse_transcript(text)
    print(f"Parsed {len(lines):,} timestamped lines")

    chunks = chunk_by_words(lines)
    print(f"Created {len(chunks)} chunks (~{CHUNK_WORDS} words each, {OVERLAP_LINES}-line overlap)")
    print(f"Coverage: {chunks[0]['start_ts']} → {chunks[-1]['end_ts']}")

    client     = get_client()
    embeddings = []
    batch_size = 100

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        end   = min(i + batch_size, len(chunks))
        print(f"  Embedding {i+1}-{end}/{len(chunks)}...")
        texts = [c["text"] for c in batch]
        resp  = client.embeddings.create(model=EMBED_MODEL, input=texts)
        for item in resp.data:
            embeddings.append(np.array(item.embedding, dtype=np.float32))

    save_index(chunks, embeddings)
    print(f"\nDone! {len(chunks)} chunks indexed and saved.")
    print("Ask questions: python harut_rag.py query \"How should I price my Skool?\"")


def cmd_query(question):
    client = get_client()

    try:
        chunks, emb_matrix = load_index()
    except FileNotFoundError:
        print("Index not found. Run: python harut_rag.py index <transcript_path>")
        sys.exit(1)

    # Embed question and find top-K chunks by cosine similarity
    q_resp = client.embeddings.create(model=EMBED_MODEL, input=[question])
    q_vec  = np.array(q_resp.data[0].embedding, dtype=np.float32)
    sims   = cosine_similarity(q_vec, emb_matrix)
    top_k  = int(min(TOP_K, len(chunks)))
    top_idx = np.argsort(sims)[::-1][:top_k]

    # Build context with timestamps
    context_parts = []
    for idx in top_idx:
        c = chunks[idx]
        context_parts.append(f"[{c['start_ts']} — {c['end_ts']}]\n{c['text']}")
    context = "\n\n---\n\n".join(context_parts)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"QUESTION: {question}\n\n"
                f"RELEVANT EXCERPTS FROM HARUT'S TEACHINGS (with video timestamps):\n\n"
                f"{context}\n\n"
                f"Answer the question using these excerpts. Apply it directly to Tyler's AI "
                f"content creator + Skool business. Reference timestamps when useful so Tyler "
                f"can jump to that part of the video."
            ),
        },
    ]

    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
    )

    print(resp.choices[0].message.content)

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "status":
        cmd_status()
    elif mode == "index":
        if len(sys.argv) < 3:
            print("Usage: python harut_rag.py index <transcript_path>")
            sys.exit(1)
        cmd_index(sys.argv[2])
    elif mode == "query":
        if len(sys.argv) < 3:
            print("Usage: python harut_rag.py query \"<your question>\"")
            sys.exit(1)
        cmd_query(" ".join(sys.argv[2:]))
    else:
        print(f"Unknown command: {mode}")
        sys.exit(1)

if __name__ == "__main__":
    main()
