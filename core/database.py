"""
database.py  (extended for exam proctoring)
Keeps original study session tables and adds exam-specific tables.
"""
import sqlite3
import json
import os
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'study.db')


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            subject TEXT DEFAULT 'General',
            duration_mins INTEGER DEFAULT 0,
            focus_pct INTEGER DEFAULT 0,
            distractions INTEGER DEFAULT 0,
            history TEXT DEFAULT '[]',
            stats TEXT DEFAULT '{}',
            ai_report TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            target_mins INTEGER DEFAULT 120,
            completed_mins INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS streaks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_study_date TEXT,
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS exam_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            exam_id TEXT NOT NULL,
            started_at TEXT,
            ended_at TEXT,
            duration_secs INTEGER DEFAULT 0,
            risk_score INTEGER DEFAULT 0,
            risk_level TEXT DEFAULT 'Low',
            violations TEXT DEFAULT '{}',
            answers TEXT DEFAULT '{}',
            ai_summary TEXT DEFAULT '',
            evidence_files TEXT DEFAULT '[]',
            created_at TEXT DEFAULT (datetime('now'))
        );
        """)
        conn.execute(
            "INSERT OR IGNORE INTO streaks (id, last_study_date, current_streak, longest_streak)"
            " VALUES (1, '', 0, 0)"
        )
        defaults = {
            'theme': 'dark',
            'camera_enabled': 'true',
            'gemini_api_key': '',
            'daily_goal_mins': '120',
        }
        for k, v in defaults.items():
            conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))


def save_exam_session(student_id, exam_id, started_at, ended_at,
                      duration_secs, risk_score, risk_level,
                      violations, answers, ai_summary, evidence_files):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO exam_sessions
                (student_id, exam_id, started_at, ended_at, duration_secs,
                 risk_score, risk_level, violations, answers, ai_summary, evidence_files)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (student_id, exam_id, started_at, ended_at, duration_secs,
              risk_score, risk_level,
              json.dumps(violations), json.dumps(answers),
              ai_summary, json.dumps(evidence_files)))


def get_exam_sessions(limit=50):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM exam_sessions ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


# ── Original helpers (unchanged) ──────────────────────────────────

def save_session(subject, duration_mins, focus_pct, distractions, history, stats, ai_report=""):
    today = date.today().isoformat()
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO sessions (date, subject, duration_mins, focus_pct, distractions, history, stats, ai_report)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (today, subject, duration_mins, focus_pct, distractions,
              json.dumps(history), json.dumps(stats), ai_report))
        row = conn.execute("SELECT * FROM goals WHERE date=?", (today,)).fetchone()
        if row:
            conn.execute("UPDATE goals SET completed_mins=completed_mins+? WHERE date=?",
                         (duration_mins, today))
        else:
            target = int(get_setting('daily_goal_mins') or 120)
            conn.execute("INSERT INTO goals (date, target_mins, completed_mins) VALUES (?,?,?)",
                         (today, target, duration_mins))
        update_streak(conn, today)


def update_streak(conn, today):
    from datetime import timedelta
    row = conn.execute("SELECT * FROM streaks WHERE id=1").fetchone()
    if not row:
        return
    last = row['last_study_date']
    streak = row['current_streak']
    longest = row['longest_streak']
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    if last == today:
        return
    elif last == yesterday:
        streak += 1
    else:
        streak = 1
    longest = max(longest, streak)
    conn.execute(
        "UPDATE streaks SET last_study_date=?, current_streak=?, longest_streak=? WHERE id=1",
        (today, streak, longest))


def get_sessions(limit=30):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_today_goal():
    today = date.today().isoformat()
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM goals WHERE date=?", (today,)).fetchone()
        if row:
            return dict(row)
        target = int(get_setting('daily_goal_mins') or 120)
        return {'date': today, 'target_mins': target, 'completed_mins': 0}


def get_streak():
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM streaks WHERE id=1").fetchone()
        return dict(row) if row else {'current_streak': 0, 'longest_streak': 0}


def get_setting(key):
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row['value'] if row else None


def set_setting(key, value):
    with get_conn() as conn:
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, str(value)))


def get_weekly_stats():
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT date, SUM(duration_mins) as total_mins, AVG(focus_pct) as avg_focus
            FROM sessions WHERE date >= date('now', '-7 days')
            GROUP BY date ORDER BY date ASC
        """).fetchall()
        return [dict(r) for r in rows]


def get_subject_stats():
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT subject, COUNT(*) as sessions, SUM(duration_mins) as total_mins,
                   AVG(focus_pct) as avg_focus
            FROM sessions GROUP BY subject ORDER BY total_mins DESC
        """).fetchall()
        return [dict(r) for r in rows]
