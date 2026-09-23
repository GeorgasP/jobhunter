"""
Το ημερήσιο run: scan → match → (προαιρετικά) apply.

Ένα run είναι idempotent: ξανατρέχοντας δεν δημιουργεί διπλά jobs, matches ή
applications — το UNIQUE constraint στη βάση το εγγυάται.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Callable

from . import apply as apply_mod
from . import db, matcher, sources
from .config import Settings
from .profile import Profile


@dataclass
class RunReport:
    jobs_seen: int = 0
    jobs_new: int = 0
    matches_new: int = 0
    matches_scored: int = 0
    applications: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    source_stats: list[tuple[str, int, str]] = field(default_factory=list)

    @property
    def applied_ok(self) -> int:
        return sum(1 for a in self.applications if a.get("ok"))


def scan(conn: sqlite3.Connection, user_id: int, profile: Profile, settings: Settings,
         log: Callable[[str], None] = print) -> RunReport:
    """Τραβάει από όλες τις πηγές, αποθηκεύει jobs, υπολογίζει matches."""
    report = RunReport()

    def progress(label: str, count: int, status: str) -> None:
        report.source_stats.append((label, count, status))
        icon = "✓" if status == "ok" else "✗"
        log(f"  {icon} {label:<34} {count:>4} jobs" + ("" if status == "ok" else f"  [{status[:60]}]"))

    log(f"→ Scanning {len(profile.targets)} companies + {len(profile.boards)} job boards...")
    jobs, errors = sources.fetch_all(profile.targets, profile.boards, profile.board_query,
                                     on_progress=progress)
    report.errors.extend(errors)
    report.jobs_seen = len(jobs)

    for job in jobs:
        if not job.get("url") or not job.get("title"):
            continue
        job_id, is_new = db.upsert_job(conn, job)
        report.jobs_new += int(is_new)

        score, reasons = matcher.score_job(job, profile.preferences)
        if score < settings.min_score:
            db.drop_pending_match(conn, user_id, job_id)   # άλλαξαν preferences
            continue
        report.matches_scored += 1
        _, match_is_new = db.upsert_match(conn, user_id, job_id, score, reasons)
        report.matches_new += int(match_is_new)

    return report


def rescore(conn: sqlite3.Connection, user_id: int, profile: Profile, settings: Settings,
            log: Callable[[str], None] = print) -> tuple[int, int]:
    """Ξαναπερνάει ΟΛΑ τα αποθηκευμένα jobs με τα τρέχοντα preferences.
    Τρέξ' το όποτε αλλάζεις το profile — χωρίς νέο network scan."""
    kept = dropped = 0
    for row in db.all_jobs(conn):
        job = dict(row)
        score, reasons = matcher.score_job(job, profile.preferences)
        if score < settings.min_score:
            dropped += int(db.drop_pending_match(conn, user_id, row["id"]))
            continue
        db.upsert_match(conn, user_id, row["id"], score, reasons)
        kept += 1
    log(f"→ {kept} matches ≥{settings.min_score}, {dropped} dropped")
    return kept, dropped


def auto_apply(conn: sqlite3.Connection, user_id: int, profile: Profile, settings: Settings,
               limit: int, method: str = "auto", open_browser: bool | None = None,
               log: Callable[[str], None] = print) -> list[dict]:
    """Κάνει apply στα top-scoring pending matches."""
    matches = db.pending_matches(conn, user_id, settings.min_score, limit)
    results = []
    for m in matches:
        res = apply_mod.apply_to_match(conn, user_id, m, profile, settings,
                                       method=method, open_browser=open_browser)
        results.append(res)
        if res.get("ok"):
            where = res.get("sent_to") or "pack ready"
            log(f"  ✓ [{m['score']:>3}] {m['company']} — {m['title']}  ({res['method']}: {where})")
        else:
            log(f"  ✗ [{m['score']:>3}] {m['company']} — {m['title']}  ({res.get('error')})")
    return results


def run(conn: sqlite3.Connection, user_id: int, profile: Profile, settings: Settings, *,
        apply_limit: int = 0, method: str = "auto", open_browser: bool | None = None,
        log: Callable[[str], None] = print) -> RunReport:
    cur = conn.execute("INSERT INTO runs (started_at) VALUES (?)", (db.now(),))
    run_id = int(cur.lastrowid)

    report = scan(conn, user_id, profile, settings, log=log)
    log(f"\n→ {report.jobs_seen} postings ({report.jobs_new} new) · "
        f"{report.matches_new} new matches ≥{settings.min_score}")

    if apply_limit > 0:
        log(f"\n→ Preparing applications (max {apply_limit})...")
        report.applications = auto_apply(conn, user_id, profile, settings, apply_limit,
                                         method=method, open_browser=open_browser, log=log)

    conn.execute(
        """UPDATE runs SET finished_at=?, jobs_seen=?, jobs_new=?, matches_new=?, apps_new=?, detail=?
           WHERE id=?""",
        (db.now(), report.jobs_seen, report.jobs_new, report.matches_new,
         report.applied_ok, "; ".join(report.errors[:20]) or None, run_id),
    )
    return report
