"""
Application engine — τι σημαίνει «κάνει apply για εσένα» στην πράξη.

Τρεις μέθοδοι, με φθίνουσα αυτοματοποίηση και αύξουσα ασφάλεια:

  email     → ΠΛΗΡΩΣ αυτόματο. Όταν η αγγελία δίνει email υποψηφιοτήτων,
              στέλνεται mail με cover letter + CV συνημμένο από το δικό σου
              SMTP. Καταγράφεται ως sent.
  assisted  → Ετοιμάζεται πλήρες "apply pack" (cover letter, CV, απαντήσεις στις
              συνηθισμένες ερωτήσεις της φόρμας) και ανοίγει το apply URL. Εσύ
              πατάς μόνο copy/paste + submit.
  manual    → Απλή καταγραφή στο ιστορικό, χωρίς να ετοιμαστεί τίποτα.

Γιατί όχι αυτόματο submit σε web φόρμες: Greenhouse/Lever/Workable κ.λπ.
απαιτούν authenticated session ή έχουν anti-bot· η αυτόματη υποβολή παραβιάζει
τους όρους τους και ρισκάρει μπλόκο του λογαριασμού σου. Το assisted κρατάει
τον χρόνο ανά αίτηση στα ~60 δευτερόλεπτα χωρίς αυτό το ρίσκο.
"""
from __future__ import annotations

import mimetypes
import re
import shutil
import smtplib
import sqlite3
import webbrowser
from email.message import EmailMessage
from pathlib import Path

from . import db, letters
from .config import PACKS_DIR, Settings
from .profile import Profile

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]*[\w]")
_SLUG_RE = re.compile(r"[^a-z0-9]+")

# Emails που εμφανίζονται σε αγγελίες αλλά δεν δέχονται υποψηφιότητες.
_EMAIL_BLOCKLIST = ("noreply", "no-reply", "donotreply", "privacy", "gdpr",
                    "dpo@", "legal@", "press@", "abuse@", "security@")

# Το κείμενο ΓΥΡΩ από το email είναι το πραγματικό σήμα, όχι το local part.
# Οι μισές αγγελίες γράφουν "για accommodation λόγω αναπηρίας στείλτε στο
# careers@..." — αίτηση εκεί είναι spam σε λάθος inbox.
_NEGATIVE_CONTEXT = (
    "accommodation", "accomodation", "disabilit", "accessib", "assistance due to",
    "equal opportunity", "eeo", "affirmative action", "protected veteran",
    "discriminat", "privacy policy", "personal data", "gdpr", "unsubscribe",
    "report a concern", "whistlebl", "harassment", "fraud", "scam",
    "adaptación", "behinderung", "handicap", "αναπηρ", "προσωπικά δεδομένα",
)

# Ρητή πρόθεση «στείλε την αίτησή σου εδώ» — πολύγλωσσο, το app είναι worldwide.
_APPLY_INTENT = (
    "how to apply", "to apply", "apply by email", "apply via email", "send your cv",
    "send your resume", "send us your cv", "send us your resume", "submit your resume",
    "submit your cv", "send your application", "applications to", "email your cv",
    "email your resume", "email us your", "forward your cv", "share your cv",
    "resume to", "cv to", "interested candidates",
    "envía tu cv", "enviar cv", "postúlate", "envie seu currículo", "candidature",
    "envoyez votre cv", "bewerbung", "bewerbungen an", "lebenslauf",
    "invia il tuo cv", "στείλτε το βιογραφικό", "αποστολή βιογραφικού",
)


def _slug(text: str, limit: int = 40) -> str:
    return _SLUG_RE.sub("-", text.lower()).strip("-")[:limit] or "job"


def find_application_email(job: dict) -> str | None:
    """
    Διεύθυνση υποψηφιοτήτων μέσα στην αγγελία — μόνο όταν το κείμενο γύρω της
    ζητάει ρητά αποστολή αίτησης. Σε αμφιβολία επιστρέφει None και η αίτηση
    πάει assisted: καλύτερα μια χειροκίνητη υποβολή παρά mail σε λάθος inbox.
    """
    if job.get("apply_email"):
        return job["apply_email"].strip().rstrip(".,;:")

    text = job.get("description") or ""
    lowered = text.lower()

    for match in EMAIL_RE.finditer(text):
        addr = match.group(0).rstrip(".,;:)>]}'\"")
        if any(bad in addr.lower() for bad in _EMAIL_BLOCKLIST):
            continue
        window = lowered[max(0, match.start() - 280): match.end() + 140]
        if any(neg in window for neg in _NEGATIVE_CONTEXT):
            continue
        if any(pos in window for pos in _APPLY_INTENT):
            return addr
    return None


# ════════════════════════════════════════════════════════════════
# Apply pack
# ════════════════════════════════════════════════════════════════
QUESTION_ANSWERS = """# Ready-to-paste answers for the application form

Full name:            {name}
Email:                {email}
Phone:                {phone}
Location:             {location}
LinkedIn:             {linkedin}
GitHub:               {github}
Work authorization:   {work_auth}
Notice period:        {notice}
Salary expectation:   {salary}
How did you hear:     Company careers page
Willing to relocate:  {relocate}
"""


def build_pack(app_id: int, job: dict, profile: Profile, cover_letter: str,
               language: str) -> Path:
    """Γράφει τον φάκελο με ό,τι χρειάζεται η αίτηση. Returns pack dir."""
    pack = PACKS_DIR / f"{app_id:04d}-{_slug(job.get('company', ''))}-{_slug(job.get('title', ''))}"
    pack.mkdir(parents=True, exist_ok=True)

    (pack / "cover_letter.txt").write_text(cover_letter, encoding="utf-8")

    prefs = profile.preferences
    salary = f"{prefs.salary_min:,}+ per year" if prefs.salary_min else "Open to discussion"
    (pack / "form_answers.md").write_text(
        QUESTION_ANSWERS.format(
            name=profile.name or "—", email=profile.email or "—", phone=profile.phone or "—",
            location=profile.location or "—", linkedin=profile.linkedin or "—",
            github=profile.github or "—", salary=salary,
            work_auth=profile.work_authorization or "—",
            notice=profile.notice_period or "Immediately available",
            relocate="Yes" if not prefs.remote_only else "Prefer remote",
        ),
        encoding="utf-8",
    )

    (pack / "job.md").write_text(
        f"# {job.get('title')} — {job.get('company')}\n\n"
        f"- Location: {job.get('location') or 'n/a'}\n"
        f"- Source: {job.get('source')}\n"
        f"- URL: {job.get('url')}\n"
        f"- Salary: {job.get('salary_min') or '?'}–{job.get('salary_max') or '?'}\n\n"
        f"---\n\n{job.get('description') or ''}\n",
        encoding="utf-8",
    )

    cv_path = profile.cv_path(language)
    if cv_path and cv_path.exists():
        shutil.copy2(cv_path, pack / f"CV{cv_path.suffix}")

    return pack


# ════════════════════════════════════════════════════════════════
# Email submission
# ════════════════════════════════════════════════════════════════
def send_email_application(to_addr: str, job: dict, profile: Profile,
                           cover_letter: str, settings: Settings,
                           cv_path: Path | None) -> None:
    """Στέλνει την αίτηση από το δικό σου mailbox. Σηκώνει exception αν αποτύχει."""
    if not settings.has_smtp:
        raise RuntimeError("SMTP is not configured (data/settings.json)")

    msg = EmailMessage()
    msg["Subject"] = f"Application: {job.get('title')} — {profile.name or profile.email}"
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = to_addr
    if profile.email:
        msg["Reply-To"] = profile.email
    msg.set_content(cover_letter)

    if cv_path and cv_path.exists():
        ctype, _ = mimetypes.guess_type(cv_path.name)
        maintype, _, subtype = (ctype or "application/octet-stream").partition("/")
        msg.add_attachment(cv_path.read_bytes(), maintype=maintype, subtype=subtype,
                           filename=f"CV_{_slug(profile.name or 'candidate')}{cv_path.suffix}")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)


# ════════════════════════════════════════════════════════════════
# Top-level: apply σε ένα match
# ════════════════════════════════════════════════════════════════
def apply_to_match(conn: sqlite3.Connection, user_id: int, match: sqlite3.Row,
                   profile: Profile, settings: Settings, *,
                   method: str = "auto", open_browser: bool | None = None,
                   language: str | None = None) -> dict:
    """
    method:
      "auto"     → email αν γίνεται, αλλιώς assisted
      "assisted" → πάντα pack + browser
      "email"    → μόνο email (σφάλμα αν δεν υπάρχει διεύθυνση)
      "manual"   → μόνο καταγραφή

    Returns dict με ό,τι έγινε. Ποτέ δεν πετάει exception για ένα job — τα
    προβλήματα γυρνάνε σαν {"ok": False, "error": ...}.
    """
    job = dict(match)
    job["description"] = match["description"]
    lang = language or profile.default_language

    contact = find_application_email(job)
    if method == "auto":
        method = "email" if (contact and settings.has_smtp) else "assisted"
    if method == "email" and not contact:
        return {"ok": False, "error": "no application email found in the posting"}

    # 1. Cover letter
    if method == "manual":
        content, model, letter_id = "", None, None
    else:
        content, model = letters.generate(job, profile, settings, lang)
        letter_id = db.save_cover_letter(conn, user_id, match["id"], lang, content, model)

    # 2. Application record (UNIQUE user+job → δεν κάνουμε ποτέ διπλό apply)
    app_id = db.create_application(
        conn, user_id, match["job_id"], match["id"], method=method,
        status=db.APP_PREPARED, cover_letter_id=letter_id,
        contact_email=contact if method == "email" else None,
    )
    if app_id is None:
        return {"ok": False, "error": "already applied to this job"}

    result = {"ok": True, "application_id": app_id, "method": method,
              "letter_model": model, "company": job.get("company"), "title": job.get("title")}

    # 3. Pack
    pack_dir = None
    if method != "manual":
        pack_dir = build_pack(app_id, job, profile, content, lang)
        conn.execute("UPDATE applications SET pack_dir = ? WHERE id = ?", (str(pack_dir), app_id))
        result["pack_dir"] = str(pack_dir)

    # 4. Παράδοση
    if method == "email":
        try:
            send_email_application(contact, job, profile, content, settings,
                                   profile.cv_path(lang))
        except Exception as e:
            db.add_event(conn, app_id, "email_failed", str(e))
            result.update(ok=False, error=f"email delivery failed: {e}")
            return result
        db.set_application_status(conn, app_id, db.APP_SENT, f"email → {contact}")
        result["sent_to"] = contact

    elif method == "assisted":
        should_open = settings.open_browser if open_browser is None else open_browser
        if should_open and job.get("url"):
            try:
                webbrowser.open(job["url"])
                result["opened"] = job["url"]
            except Exception as e:                       # headless/WSL κ.λπ.
                db.add_event(conn, app_id, "browser_failed", str(e))

    return result
