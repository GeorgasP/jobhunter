"""
SQLite storage layer.

Το schema είναι multi-user από τώρα (user_id παντού) ώστε ο ίδιος κώδικας να
σηκώνει και το SaaS αργότερα, αλλά σε local mode υπάρχει ένας χρήστης (id=1).
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from .config import DB_PATH, ensure_dirs

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT UNIQUE NOT NULL,
    name        TEXT,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    source       TEXT NOT NULL,
    external_id  TEXT NOT NULL,
    company      TEXT NOT NULL,
    title        TEXT NOT NULL,
    location     TEXT,
    description  TEXT,
    url          TEXT NOT NULL,
    apply_email  TEXT,
    salary_min   INTEGER,
    salary_max   INTEGER,
    remote       INTEGER DEFAULT 0,
    posted_at    TEXT,
    raw          TEXT,
    first_seen   TEXT NOT NULL,
    last_seen    TEXT NOT NULL,
    UNIQUE(source, external_id)
);
CREATE INDEX IF NOT EXISTS ix_jobs_company   ON jobs(company);
CREATE INDEX IF NOT EXISTS ix_jobs_posted_at ON jobs(posted_at DESC);

CREATE TABLE IF NOT EXISTS matches (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id     INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    score      INTEGER NOT NULL,
    reasons    TEXT,
    status     TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    UNIQUE(user_id, job_id)
);
CREATE INDEX IF NOT EXISTS ix_matches_user_score ON matches(user_id, score DESC);

CREATE TABLE IF NOT EXISTS cover_letters (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    match_id   INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    language   TEXT NOT NULL,
    content    TEXT NOT NULL,
    model      TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS applications (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id          INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    match_id        INTEGER REFERENCES matches(id) ON DELETE SET NULL,
    cover_letter_id INTEGER REFERENCES cover_letters(id) ON DELETE SET NULL,
    method          TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'prepared',
    pack_dir        TEXT,
    contact_email   TEXT,
    prepared_at     TEXT NOT NULL,
    sent_at         TEXT,
    last_update_at  TEXT,
    notes           TEXT,
    UNIQUE(user_id, job_id)
);
CREATE INDEX IF NOT EXISTS ix_apps_user ON applications(user_id, prepared_at DESC);

CREATE TABLE IF NOT EXISTS events (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    at             TEXT NOT NULL,
    kind           TEXT NOT NULL,
    detail         TEXT
);
CREATE INDEX IF NOT EXISTS ix_events_app ON events(application_id, at);

CREATE TABLE IF NOT EXISTS runs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at   TEXT NOT NULL,
    finished_at  TEXT,
    jobs_seen    INTEGER DEFAULT 0,
    jobs_new     INTEGER DEFAULT 0,
    matches_new  INTEGER DEFAULT 0,
    apps_new     INTEGER DEFAULT 0,
    detail       TEXT
);
"""

# statuses
MATCH_PENDING, MATCH_APPLIED, MATCH_IGNORED, MATCH_SAVED = "pending", "applied", "ignored", "saved"
APP_PREPARED, APP_SENT = "prepared", "sent"
APP_INTERVIEW, APP_REJECTED, APP_OFFER, APP_GHOSTED = "interview", "rejected", "offer", "ghosted"

TERMINAL_STATUSES = {APP_REJECTED, APP_OFFER}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)


def get_or_create_user(conn: sqlite3.Connection, email: str, name: str | None = None) -> int:
    row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute(
        "INSERT INTO users (email, name, created_at) VALUES (?, ?, ?)",
        (email, name, now()),
    )
    return int(cur.lastrowid)


# ════════════════════════════════════════════════════════════════
# Jobs
# ════════════════════════════════════════════════════════════════
def upsert_job(conn: sqlite3.Connection, job: dict[str, Any]) -> tuple[int, bool]:
    """Insert ή refresh ένα job. Returns (job_id, is_new)."""
    ts = now()
    existing = conn.execute(
        "SELECT id FROM jobs WHERE source = ? AND external_id = ?",
        (job["source"], job["external_id"]),
    ).fetchone()

    if existing:
        conn.execute(
            """UPDATE jobs SET company=?, title=?, location=?, description=?, url=?,
                   apply_email=?, salary_min=?, salary_max=?, remote=?, posted_at=?,
                   raw=?, last_seen=?
               WHERE id=?""",
            (job["company"], job["title"], job.get("location"), job.get("description"),
             job["url"], job.get("apply_email"), job.get("salary_min"), job.get("salary_max"),
             int(bool(job.get("remote"))), job.get("posted_at"),
             json.dumps(job.get("raw") or {}, ensure_ascii=False), ts, existing["id"]),
        )
        return existing["id"], False

    cur = conn.execute(
        """INSERT INTO jobs (source, external_id, company, title, location, description, url,
               apply_email, salary_min, salary_max, remote, posted_at, raw, first_seen, last_seen)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (job["source"], job["external_id"], job["company"], job["title"], job.get("location"),
         job.get("description"), job["url"], job.get("apply_email"), job.get("salary_min"),
         job.get("salary_max"), int(bool(job.get("remote"))), job.get("posted_at"),
         json.dumps(job.get("raw") or {}, ensure_ascii=False), ts, ts),
    )
    return int(cur.lastrowid), True


# ════════════════════════════════════════════════════════════════
# Matches
# ════════════════════════════════════════════════════════════════
def upsert_match(conn: sqlite3.Connection, user_id: int, job_id: int,
                 score: int, reasons: dict) -> tuple[int, bool]:
    """Δεν πειράζει ποτέ status που έχει ήδη αλλάξει ο χρήστης."""
    existing = conn.execute(
        "SELECT id, status FROM matches WHERE user_id = ? AND job_id = ?", (user_id, job_id)
    ).fetchone()

    if existing:
        if existing["status"] == MATCH_PENDING:
            conn.execute(
                "UPDATE matches SET score = ?, reasons = ? WHERE id = ?",
                (score, json.dumps(reasons, ensure_ascii=False), existing["id"]),
            )
        return existing["id"], False

    cur = conn.execute(
        "INSERT INTO matches (user_id, job_id, score, reasons, status, created_at) VALUES (?,?,?,?,?,?)",
        (user_id, job_id, score, json.dumps(reasons, ensure_ascii=False), MATCH_PENDING, now()),
    )
    return int(cur.lastrowid), True


def pending_matches(conn: sqlite3.Connection, user_id: int, min_score: int, limit: int) -> list[sqlite3.Row]:
    return conn.execute(
        """SELECT m.*, j.company, j.title, j.location, j.url, j.description, j.remote,
                  j.apply_email, j.source, j.posted_at
           FROM matches m JOIN jobs j ON j.id = m.job_id
           WHERE m.user_id = ? AND m.status = ? AND m.score >= ?
           ORDER BY m.score DESC, j.posted_at DESC
           LIMIT ?""",
        (user_id, MATCH_PENDING, min_score, limit),
    ).fetchall()


def set_match_status(conn: sqlite3.Connection, match_id: int, status: str) -> None:
    conn.execute("UPDATE matches SET status = ? WHERE id = ?", (status, match_id))


def drop_pending_match(conn: sqlite3.Connection, user_id: int, job_id: int) -> bool:
    """Σβήνει match που δεν περνάει πια το κατώφλι (π.χ. άλλαξες preferences).
    Ό,τι έχεις ήδη αγγίξει (applied/saved/ignored) μένει ανέπαφο."""
    cur = conn.execute(
        "DELETE FROM matches WHERE user_id = ? AND job_id = ? AND status = ?",
        (user_id, job_id, MATCH_PENDING),
    )
    return cur.rowcount > 0


def all_jobs(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM jobs").fetchall()


# ════════════════════════════════════════════════════════════════
# Applications + history
# ════════════════════════════════════════════════════════════════
def create_application(conn: sqlite3.Connection, user_id: int, job_id: int, match_id: int | None,
                       method: str, status: str, pack_dir: str | None = None,
                       cover_letter_id: int | None = None, contact_email: str | None = None,
                       notes: str | None = None) -> int | None:
    """Returns application id, ή None αν έχει ήδη γίνει apply σε αυτό το job."""
    ts = now()
    try:
        cur = conn.execute(
            """INSERT INTO applications
                 (user_id, job_id, match_id, cover_letter_id, method, status, pack_dir,
                  contact_email, prepared_at, sent_at, last_update_at, notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (user_id, job_id, match_id, cover_letter_id, method, status, pack_dir,
             contact_email, ts, ts if status == APP_SENT else None, ts, notes),
        )
    except sqlite3.IntegrityError:
        return None

    app_id = int(cur.lastrowid)
    add_event(conn, app_id, "created", f"method={method} status={status}")
    if match_id:
        set_match_status(conn, match_id, MATCH_APPLIED)
    return app_id


def add_event(conn: sqlite3.Connection, application_id: int, kind: str, detail: str | None = None) -> None:
    conn.execute(
        "INSERT INTO events (application_id, at, kind, detail) VALUES (?,?,?,?)",
        (application_id, now(), kind, detail),
    )


def set_application_status(conn: sqlite3.Connection, app_id: int, status: str,
                           detail: str | None = None) -> None:
    ts = now()
    if status == APP_SENT:
        conn.execute(
            "UPDATE applications SET status=?, sent_at=COALESCE(sent_at, ?), last_update_at=? WHERE id=?",
            (status, ts, ts, app_id),
        )
    else:
        conn.execute(
            "UPDATE applications SET status=?, last_update_at=? WHERE id=?", (status, ts, app_id)
        )
    add_event(conn, app_id, f"status:{status}", detail)


def list_applications(conn: sqlite3.Connection, user_id: int, status: str | None = None) -> list[sqlite3.Row]:
    sql = """SELECT a.*, j.company, j.title, j.location, j.url, j.source
             FROM applications a JOIN jobs j ON j.id = a.job_id
             WHERE a.user_id = ?"""
    params: list[Any] = [user_id]
    if status:
        sql += " AND a.status = ?"
        params.append(status)
    sql += " ORDER BY a.prepared_at DESC"
    return conn.execute(sql, params).fetchall()


def get_application(conn: sqlite3.Connection, app_id: int) -> sqlite3.Row | None:
    return conn.execute(
        """SELECT a.*, j.company, j.title, j.location, j.url, j.source, j.description
           FROM applications a JOIN jobs j ON j.id = a.job_id WHERE a.id = ?""",
        (app_id,),
    ).fetchone()


def application_events(conn: sqlite3.Connection, app_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM events WHERE application_id = ? ORDER BY at", (app_id,)
    ).fetchall()


def save_cover_letter(conn: sqlite3.Connection, user_id: int, match_id: int,
                      language: str, content: str, model: str | None) -> int:
    cur = conn.execute(
        "INSERT INTO cover_letters (user_id, match_id, language, content, model, created_at) VALUES (?,?,?,?,?,?)",
        (user_id, match_id, language, content, model, now()),
    )
    return int(cur.lastrowid)


# ════════════════════════════════════════════════════════════════
# Stats
# ════════════════════════════════════════════════════════════════
def stats(conn: sqlite3.Connection, user_id: int) -> dict[str, Any]:
    def scalar(sql: str, params: tuple = ()) -> int:
        return int(conn.execute(sql, params).fetchone()[0])

    by_status = {
        r["status"]: r["n"]
        for r in conn.execute(
            "SELECT status, COUNT(*) n FROM applications WHERE user_id = ? GROUP BY status",
            (user_id,),
        )
    }
    return {
        "jobs_tracked": scalar("SELECT COUNT(*) FROM jobs"),
        "matches_pending": scalar(
            "SELECT COUNT(*) FROM matches WHERE user_id = ? AND status = 'pending'", (user_id,)
        ),
        "applications_total": scalar("SELECT COUNT(*) FROM applications WHERE user_id = ?", (user_id,)),
        "by_status": by_status,
        "last_run": (conn.execute("SELECT finished_at FROM runs ORDER BY id DESC LIMIT 1").fetchone() or [None])[0],
    }
