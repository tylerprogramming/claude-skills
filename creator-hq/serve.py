#!/usr/bin/env python3
"""
Creator HQ - LAN kiosk server.

Serves ~/creator-hq over the local network so an iPad (or any device on your
wifi) can open the dashboard. Root path redirects to dashboard.html. Optionally
rebuilds the dashboard on an interval so a wall display stays fresh.

Usage:
    python3 serve.py [--port 8080] [--rebuild 30]

    --port     port to bind (default 8080)
    --rebuild  minutes between auto-rebuilds (fetch + render). Omit to serve
               only the current build (rebuild manually via the skill).

Then on the iPad, open:   http://<this-machine-ip>:<port>/
"""
import argparse
import http.server
import socket
import socketserver
import subprocess
import sys
import threading
import time
from pathlib import Path

BASE = Path.home() / "creator-hq"
SKILL = Path(__file__).resolve().parent


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(BASE), **kw)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(302)
            self.send_header("Location", "/dashboard.html")
            self.end_headers()
            return
        super().do_GET()

    def end_headers(self):
        # never let the kiosk serve a stale cached copy
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *a):
        pass  # quiet


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def rebuild():
    try:
        subprocess.run([sys.executable, str(SKILL / "fetch_stats.py")], timeout=600)
        subprocess.run([sys.executable, str(SKILL / "dashboard.py")], timeout=120)
        print(f"[{time.strftime('%H:%M:%S')}] rebuilt dashboard", flush=True)
    except Exception as e:
        print(f"[rebuild error] {e}", flush=True)


def rebuild_loop(minutes):
    while True:
        time.sleep(minutes * 60)
        rebuild()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--rebuild", type=int, default=0, help="minutes between rebuilds")
    args = ap.parse_args()

    if not (BASE / "dashboard.html").exists():
        print("No dashboard.html yet - building once...")
        rebuild()

    if args.rebuild > 0:
        threading.Thread(target=rebuild_loop, args=(args.rebuild,), daemon=True).start()
        print(f"Auto-rebuild every {args.rebuild} min")

    ip = lan_ip()
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", args.port), Handler) as httpd:
        print(f"\nCreator HQ is live. On the iPad, open:\n  http://{ip}:{args.port}/\n")
        print("Ctrl-C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
