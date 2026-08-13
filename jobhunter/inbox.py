"""
Auto-tracking απαντήσεων: διαβάζει το mailbox σου (IMAP, read-only) και
ενημερώνει μόνο του το status των αιτήσεων.

Δεν σβήνει, δεν απαντάει, δεν μαρκάρει τίποτα ως διαβασμένο (BODY.PEEK).
Εσύ απλώς απαντάς στα mail που έχουν σημασία.
"""
from __future__ import annotations

import email
import imaplib
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from email.header import decode_header, make_header
from email.utils import parseaddr

from . import db
from .config import Settings

REJECTION_MARKERS = (
    "unfortunately", "we regret", "not moving forward", "not be moving forward",
    "decided to proceed with other", "will not be progressing", "unsuccessful",
    "not selected", "other candidates", "δεν θα προχωρήσουμε", "δυστυχώς",
    "δεν επιλεγ", "άλλους υποψηφίους",
)
INTERVIEW_MARKERS = (
    "interview", "schedule a call", "book a time", "meet with", "next step",
    "phone screen", "video call", "hiring manager would like",
    "συνέντευξη", "κλείσουμε ραντεβού", "τηλεφωνική επικοινωνία", "επόμενο στάδιο",
)
OFFER_MARKERS = (
    "offer letter", "pleased to offer", "we would like to offer", "job offer",
    "πρόταση εργασίας", "σας προσφέρουμε",
)
ACK_MARKERS = (
    "we have received your application", "thanks for applying", "thank you for applying",
    "application received", "λάβαμε την αίτησή", "ευχαριστούμε για το ενδιαφέρον",
)

_WORD_RE = re.compile(r"[a-z0-9]+")


def classify(subject: str, body: str) -> tuple[str | None, str]:
    """Returns (new_status | None, matched marker)."""
    text = f"{subject}\n{body}".lower()
    for marker in OFFER_MARKERS:
        if marker in text:
            return db.APP_OFFER, marker
    for marker in REJECTION_MARKERS:
        if marker in text:
            return db.APP_REJECTED, marker
    for marker in INTERVIEW_MARKERS:
        if marker in text:
            return db.APP_INTERVIEW, marker
    for marker in ACK_MARKERS:
        if marker in text:
            return None, marker            # απλή επιβεβαίωση λήψης
    return None, ""


def _decode(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def _body_text(msg: email.message.Message, limit: int = 4000) -> str:
    parts = []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition")):
                parts.append(part.get_payload(decode=True) or b"")
    else:
        parts.append(msg.get_payload(decode=True) or b"")
    text = b"\n".join(p for p in parts if p).decode("utf-8", errors="replace")
    return text[:limit]


def _company_tokens(company: str) -> set[str]:
    stop = {"the", "inc", "ltd", "llc", "gmbh", "bv", "sa", "ag", "group", "labs", "technologies"}
    return {w for w in _WORD_RE.findall(company.lower()) if len(w) > 2 and w not in stop}


def _matches_application(from_addr: str, subject: str, body: str, app: sqlite3.Row) -> bool:
    domain = from_addr.split("@")[-1].lower()
    tokens = _company_tokens(app["company"])
    if tokens and any(t in domain for t in tokens):
        return True
    haystack = f"{subject} {body[:1500]}".lower()
    if app["title"] and app["title"].lower() in haystack:
        return True
    return bool(tokens) and all(t in haystack for t in tokens)


def check(conn: sqlite3.Connection, user_id: int, settings: Settings,
          days: int = 30, log=print) -> list[dict]:
    """Σαρώνει το inbox και ενημερώνει statuses. Returns λίστα με ό,τι άλλαξε."""
    if not settings.has_imap:
        raise SystemExit(
            "IMAP is not configured. Set imap_host / imap_user / imap_password in data/settings.json\n"
            "(Gmail: imap.gmail.com + an app password from https://myaccount.google.com/apppasswords)"
        )

    apps = [a for a in db.list_applications(conn, user_id)
            if a["status"] not in db.TERMINAL_STATUSES]
    if not apps:
        log("No active applications to track.")
        return []

    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%d-%b-%Y")
    updates: list[dict] = []

    with imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port) as imap:
        imap.login(settings.imap_user, settings.imap_password)
        imap.select(settings.imap_folder, readonly=True)

        status, data = imap.search(None, "SINCE", since)
        if status != "OK":
            log(f"IMAP search failed: {status}")
            return []

        ids = (data[0] or b"").split()
        log(f"→ Scanning {len(ids)} messages from the last {days} days "
            f"against {len(apps)} active applications...")

        for msg_id in reversed(ids):                      # νεότερα πρώτα
            status, msg_data = imap.fetch(msg_id, "(BODY.PEEK[])")
            if status != "OK" or not msg_data or not isinstance(msg_data[0], tuple):
                continue
            msg = email.message_from_bytes(msg_data[0][1])

            from_addr = parseaddr(_decode(msg.get("From")))[1].lower()
            subject = _decode(msg.get("Subject"))
            body = _body_text(msg)

            for app in apps:
                if app["id"] in {u["application_id"] for u in updates}:
                    continue
                if not _matches_application(from_addr, subject, body, app):
                    continue

                new_status, marker = classify(subject, body)
                db.add_event(conn, app["id"], "email_received",
                             f"from={from_addr} subject={subject[:120]}")
                if new_status and new_status != app["status"]:
                    db.set_application_status(conn, app["id"], new_status,
                                              f"auto-detected from email: \"{marker}\"")
                    updates.append({
                        "application_id": app["id"], "company": app["company"],
                        "title": app["title"], "status": new_status,
                        "from": from_addr, "subject": subject,
                    })
                    icon = {db.APP_OFFER: "🎉", db.APP_INTERVIEW: "📞", db.APP_REJECTED: "✗"}.get(new_status, "•")
                    log(f"  {icon} {app['company']} — {app['title']} → {new_status}")
                break

    return updates
