#!/usr/bin/env python3
"""
Shared database schema and helpers for TikTok analytics tracking.

Tables:
  tiktok_videos         - Every video posted (one row per video, immutable metadata)
  tiktok_metrics        - Public metric snapshots (views, likes, comments, shares, saves)
  tiktok_deep_metrics   - Private metrics from TikTok analytics (watch time, retention, traffic sources)
  tiktok_daily_overview - Daily account-level stats (from TikTok's Overview CSV export)
"""

import sqlite3
from pathlib import Path
from datetime import date

DATA_DIR = Path.home() / ".claude" / "skills" / "tiktok-analytics" / "data"
DB_PATH = DATA_DIR / "tiktok.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_all_tables(conn: sqlite3.Connection):
    """Create or migrate all TikTok analytics tables."""

    # --- tiktok_videos: one row per video, immutable metadata ---
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tiktok_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT UNIQUE NOT NULL,
            url TEXT,
            caption TEXT,
            posted_at TEXT,
            duration_seconds REAL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # --- tiktok_metrics: public metric snapshots (from Apify or manual) ---
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tiktok_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL,
            snapshot_date TEXT NOT NULL,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            saves INTEGER DEFAULT 0,
            source TEXT DEFAULT 'manual',
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(video_id, snapshot_date),
            FOREIGN KEY (video_id) REFERENCES tiktok_videos(video_id)
        )
    """)

    # --- tiktok_deep_metrics: private analytics (from screenshots or manual entry) ---
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tiktok_deep_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL,
            snapshot_date TEXT NOT NULL,
            avg_watch_time_seconds REAL,
            full_watch_pct REAL,
            total_play_time TEXT,
            new_followers INTEGER,
            fyp_pct REAL,
            search_pct REAL,
            profile_pct REAL,
            following_pct REAL,
            dm_pct REAL,
            sound_pct REAL,
            other_pct REAL,
            source TEXT DEFAULT 'screenshot',
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(video_id, snapshot_date),
            FOREIGN KEY (video_id) REFERENCES tiktok_videos(video_id)
        )
    """)

    # --- tiktok_daily_overview: account-level daily stats (from CSV export) ---
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tiktok_daily_overview (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            video_views INTEGER DEFAULT 0,
            profile_views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # --- Indexes ---
    conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_video ON tiktok_metrics(video_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_date ON tiktok_metrics(snapshot_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_deep_video ON tiktok_deep_metrics(video_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_overview_date ON tiktok_daily_overview(date)")

    conn.commit()


# --- Video CRUD ---

def upsert_video(conn, video_id, url=None, caption=None, posted_at=None, duration_seconds=None):
    """Insert or update a video's metadata."""
    conn.execute("""
        INSERT INTO tiktok_videos (video_id, url, caption, posted_at, duration_seconds)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(video_id) DO UPDATE SET
            url = COALESCE(excluded.url, url),
            caption = COALESCE(excluded.caption, caption),
            posted_at = COALESCE(excluded.posted_at, posted_at),
            duration_seconds = COALESCE(excluded.duration_seconds, duration_seconds)
    """, (video_id, url, caption, posted_at, duration_seconds))
    conn.commit()


def get_all_videos(conn):
    """Get all tracked videos, newest first."""
    return conn.execute("""
        SELECT v.*,
               m.views, m.likes, m.comments, m.shares, m.saves, m.snapshot_date as last_snapshot
        FROM tiktok_videos v
        LEFT JOIN tiktok_metrics m ON v.video_id = m.video_id
            AND m.snapshot_date = (SELECT MAX(snapshot_date) FROM tiktok_metrics WHERE video_id = v.video_id)
        ORDER BY v.posted_at DESC
    """).fetchall()


def get_video_by_id(conn, video_id):
    """Get a single video by its TikTok video ID."""
    return conn.execute("SELECT * FROM tiktok_videos WHERE video_id = ?", (video_id,)).fetchone()


def search_videos(conn, query):
    """Search videos by caption text."""
    return conn.execute("""
        SELECT * FROM tiktok_videos WHERE caption LIKE ? ORDER BY posted_at DESC
    """, (f"%{query}%",)).fetchall()


# --- Public Metrics ---

def save_metrics(conn, video_id, views, likes, comments, shares, saves=0, source="manual", snapshot_date=None):
    """Save a public metrics snapshot for a video."""
    snap_date = snapshot_date or date.today().isoformat()
    conn.execute("""
        INSERT OR REPLACE INTO tiktok_metrics
            (video_id, snapshot_date, views, likes, comments, shares, saves, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (video_id, snap_date, views, likes, comments, shares, saves, source))
    conn.commit()


def get_metrics_history(conn, video_id):
    """Get all metric snapshots for a video."""
    return conn.execute("""
        SELECT * FROM tiktok_metrics WHERE video_id = ? ORDER BY snapshot_date
    """, (video_id,)).fetchall()


def get_latest_metrics(conn):
    """Get the latest metrics for all videos."""
    return conn.execute("""
        SELECT v.video_id, v.url, v.caption, v.posted_at, v.duration_seconds,
               m.views, m.likes, m.comments, m.shares, m.saves, m.snapshot_date
        FROM tiktok_videos v
        LEFT JOIN tiktok_metrics m ON v.video_id = m.video_id
            AND m.snapshot_date = (SELECT MAX(snapshot_date) FROM tiktok_metrics WHERE video_id = v.video_id)
        ORDER BY m.views DESC
    """).fetchall()


# --- Deep Metrics ---

def save_deep_metrics(conn, video_id, avg_watch_time_seconds=None, full_watch_pct=None,
                      total_play_time=None, new_followers=None, fyp_pct=None,
                      search_pct=None, profile_pct=None, following_pct=None,
                      dm_pct=None, sound_pct=None, other_pct=None,
                      source="screenshot", snapshot_date=None):
    """Save deep analytics metrics (from screenshots or manual entry)."""
    snap_date = snapshot_date or date.today().isoformat()
    conn.execute("""
        INSERT OR REPLACE INTO tiktok_deep_metrics
            (video_id, snapshot_date, avg_watch_time_seconds, full_watch_pct,
             total_play_time, new_followers, fyp_pct, search_pct, profile_pct,
             following_pct, dm_pct, sound_pct, other_pct, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (video_id, snap_date, avg_watch_time_seconds, full_watch_pct,
          total_play_time, new_followers, fyp_pct, search_pct, profile_pct,
          following_pct, dm_pct, sound_pct, other_pct, source))
    conn.commit()


def get_deep_metrics(conn, video_id):
    """Get deep metrics for a video."""
    return conn.execute("""
        SELECT * FROM tiktok_deep_metrics WHERE video_id = ? ORDER BY snapshot_date DESC
    """, (video_id,)).fetchall()


# --- Daily Overview ---

def save_daily_overview(conn, date_str, video_views, profile_views, likes, comments, shares):
    """Save a daily overview row (from CSV export)."""
    conn.execute("""
        INSERT OR REPLACE INTO tiktok_daily_overview
            (date, video_views, profile_views, likes, comments, shares)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (date_str, video_views, profile_views, likes, comments, shares))
    conn.commit()


def get_daily_overview(conn, start_date=None, end_date=None):
    """Get daily overview data, optionally filtered by date range."""
    query = "SELECT * FROM tiktok_daily_overview"
    params = []
    if start_date and end_date:
        query += " WHERE date >= ? AND date <= ?"
        params = [start_date, end_date]
    elif start_date:
        query += " WHERE date >= ?"
        params = [start_date]
    query += " ORDER BY date"
    return conn.execute(query, params).fetchall()


# --- Reporting ---

def get_summary(conn):
    """Get a high-level summary of the tracked data."""
    videos = conn.execute("SELECT COUNT(*) as count FROM tiktok_videos").fetchone()
    metrics = conn.execute("SELECT COUNT(DISTINCT video_id) as count FROM tiktok_metrics").fetchone()
    deep = conn.execute("SELECT COUNT(DISTINCT video_id) as count FROM tiktok_deep_metrics").fetchone()
    overview_days = conn.execute("SELECT COUNT(*) as count FROM tiktok_daily_overview").fetchone()

    latest = conn.execute("""
        SELECT MAX(snapshot_date) as latest FROM tiktok_metrics
    """).fetchone()

    total_views = conn.execute("""
        SELECT SUM(m.views) as total
        FROM tiktok_metrics m
        WHERE m.snapshot_date = (SELECT MAX(snapshot_date) FROM tiktok_metrics WHERE video_id = m.video_id)
    """).fetchone()

    return {
        "total_videos": videos["count"],
        "videos_with_metrics": metrics["count"],
        "videos_with_deep_metrics": deep["count"],
        "overview_days": overview_days["count"],
        "latest_snapshot": latest["latest"] if latest else None,
        "total_views": total_views["total"] or 0,
    }


if __name__ == "__main__":
    conn = get_connection()
    init_all_tables(conn)
    print(f"Database initialized at {DB_PATH}")

    summary = get_summary(conn)
    print(f"Videos tracked: {summary['total_videos']}")
    print(f"With public metrics: {summary['videos_with_metrics']}")
    print(f"With deep metrics: {summary['videos_with_deep_metrics']}")
    print(f"Daily overview days: {summary['overview_days']}")
    print(f"Total views (latest): {summary['total_views']}")

    conn.close()
