"""
Scoring: πόσο ταιριάζει ένα job στο profile σου (0-100).

Ο τίτλος μετράει πολύ περισσότερο από το description — εκεί κρύβονται τα
false positives ("κάπου στη σελίδα γράφει customer success" ≠ CS ρόλος).
Ό,τι κόβεται, κόβεται με λόγο που φαίνεται στο dashboard.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from .profile import Preferences

# βάρη ανά κατηγορία — άθροισμα 100
W_TITLE, W_LOCATION, W_INDUSTRY, W_LANGUAGE, W_FRESHNESS, W_SALARY = 40, 25, 10, 10, 10, 5

SENIOR_MARKERS = ("senior", "sr.", "lead", "principal", "staff", "head of",
                  "director", "vp ", "vice president", "chief", "manager iii")
ENTRY_MARKERS = ("junior", "jr.", "entry", "graduate", "trainee", "intern",
                 "apprentice", "associate")

LANGUAGE_SIGNALS = {
    "el": ("greek", "ελλην", "greece", "athens", "hellenic"),
    "es": ("spanish", "español", "espanol", "spain", "madrid", "barcelona"),
    "de": ("german", "deutsch", "germany", "berlin", "munich"),
    "fr": ("french", "français", "francais", "france", "paris"),
    "it": ("italian", "italiano", "italy", "milan", "rome"),
    "pt": ("portuguese", "português", "portugal", "lisbon"),
}


# Αγγελίες ανοιχτές σε όλο τον κόσμο — δεν κόβονται ποτέ γεωγραφικά.
GLOBAL_MARKERS = ("worldwide", "anywhere", "global", "fully remote", "remote - global")

REMOTE_WORDS = ("remote", "anywhere", "worldwide", "work from home", "distributed")

# Συντομογραφίες περιοχών → πώς γράφονται στις αγγελίες.
REGION_ALIASES = {
    "eu": ("eu", "europe", "european", "emea"),
    "europe": ("europe", "european", "eu", "emea"),
    "emea": ("emea", "europe", "middle east", "africa"),
    "us": ("us", "usa", "u.s.", "united states", "america"),
    "usa": ("usa", "us", "u.s.", "united states"),
    "uk": ("uk", "united kingdom", "england", "britain", "london"),
    "uae": ("uae", "united arab emirates", "dubai", "abu dhabi"),
    "apac": ("apac", "asia", "asia-pacific", "asia pacific"),
    "latam": ("latam", "latin america", "south america"),
    "anz": ("anz", "australia", "new zealand"),
}


def _norm(s: str | None) -> str:
    return (s or "").lower()


def _location_hits(location: str, wanted: list[str]) -> list[str]:
    """Ποιες από τις περιοχές σου καλύπτει η αγγελία. Δουλεύει για κάθε χώρα."""
    hits = []
    for loc in wanted:
        low = loc.strip().lower()
        if not low:
            continue
        if low in REMOTE_WORDS:
            if any(w in location for w in REMOTE_WORDS):
                hits.append("Remote")
            continue
        variants = REGION_ALIASES.get(low, (low,))
        if any(v in location for v in variants):
            hits.append(loc)
    return hits


def _age_days(posted_at: str | None) -> float | None:
    if not posted_at:
        return None
    try:
        dt = datetime.fromisoformat(posted_at)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - dt).total_seconds() / 86400


def _phrase_in(phrase: str, text: str) -> bool:
    """Word-boundary match ώστε το 'BD' να μην πιάνει το 'BDD'."""
    return re.search(r"(?<!\w)" + re.escape(phrase.lower()) + r"(?!\w)", text) is not None


def score_job(job: dict, prefs: Preferences) -> tuple[int, dict]:
    """Returns (score 0-100, reasons). score == 0 σημαίνει «μη το δείξεις»."""
    title = _norm(job.get("title"))
    location = _norm(job.get("location"))
    description = _norm(job.get("description"))[:6000]
    haystack = f"{title} {location} {description}"

    reasons: dict[str, object] = {}

    # ─── Hard filters ───────────────────────────────────────────
    for kw in prefs.exclude_keywords:
        if _phrase_in(kw, title) or _phrase_in(kw, description[:1500]):
            return 0, {"rejected": f"excluded keyword: {kw}"}

    for kw in prefs.must_have:
        if not _phrase_in(kw, haystack):
            return 0, {"rejected": f"missing must-have: {kw}"}

    if prefs.remote_only and not (job.get("remote") or "remote" in haystack):
        return 0, {"rejected": "not remote"}

    # ─── Γεωγραφία ──────────────────────────────────────────────
    # Ίδια λογική για κάθε χώρα του κόσμου: "Remote — US only" δεν σε αφορά αν
    # είσαι στη Βραζιλία, όπως "Remote — LATAM" δεν αφορά κάποιον στην Ιαπωνία.
    geo_hits = _location_hits(location, prefs.locations)
    globally_open = any(w in location for w in GLOBAL_MARKERS) or not location

    blocked_hit = next((b for b in prefs.blocked_locations if b.lower() in location), None)
    if blocked_hit and not geo_hits:
        return 0, {"rejected": f"blocked location: {blocked_hit}"}

    if prefs.strict_location and prefs.locations and not geo_hits and not globally_open:
        return 0, {"rejected": f"location outside your list: {job.get('location')}"}

    age = _age_days(job.get("posted_at"))
    if age is not None and prefs.max_age_days and age > prefs.max_age_days:
        return 0, {"rejected": f"stale posting ({int(age)} days old)"}

    score = 0.0

    # ─── Title (το βαρύτερο σήμα) ───────────────────────────────
    title_hits = [t for t in prefs.titles if _phrase_in(t, title)]
    desc_hits = [t for t in prefs.titles if t not in title_hits and _phrase_in(t, description)]
    if title_hits:
        score += W_TITLE
        reasons["title_match"] = title_hits
    elif desc_hits:
        score += W_TITLE * 0.35
        reasons["title_match_in_description"] = desc_hits
    elif prefs.titles:
        reasons["title_match"] = None      # χωρίς title hit ξεκινάς πολύ πίσω

    # ─── Location ───────────────────────────────────────────────
    if geo_hits:
        score += W_LOCATION
        reasons["location_match"] = sorted(set(geo_hits))
    elif globally_open or not prefs.locations:
        score += W_LOCATION * 0.7
        reasons["location_match"] = ["Worldwide"]

    # ─── Industry ───────────────────────────────────────────────
    industry_hits = [i for i in prefs.industries if _phrase_in(i, haystack)]
    if industry_hits:
        score += W_INDUSTRY
        reasons["industry_match"] = industry_hits

    # ─── Γλώσσα ως πλεονέκτημα (π.χ. "Greek speaker required") ──
    lang_hits = []
    for lang in prefs.languages:
        for marker in LANGUAGE_SIGNALS.get(lang, ()):
            if marker in haystack:
                lang_hits.append(lang)
                break
    if lang_hits:
        score += W_LANGUAGE
        reasons["language_signal"] = lang_hits

    # ─── Φρεσκάδα ───────────────────────────────────────────────
    if age is None:
        score += W_FRESHNESS * 0.5
    else:
        window = max(prefs.max_age_days or 45, 1)
        score += W_FRESHNESS * max(0.0, 1 - age / window)
        reasons["posted_days_ago"] = int(age)

    # ─── Μισθός ─────────────────────────────────────────────────
    smax, smin = job.get("salary_max"), job.get("salary_min")
    if prefs.salary_min and (smin or smax):
        best = smax or smin
        if best >= prefs.salary_min:
            score += W_SALARY
            reasons["salary_ok"] = f"{smin or '?'}–{smax or '?'}"
        else:
            score -= W_SALARY * 2
            reasons["salary_low"] = f"{smin or '?'}–{smax or '?'}"

    # ─── Seniority fit ──────────────────────────────────────────
    is_senior = any(m in title for m in SENIOR_MARKERS)
    is_entry = any(m in title for m in ENTRY_MARKERS)
    if prefs.experience_level == "entry" and is_senior:
        score -= 25
        reasons["seniority_penalty"] = "senior role"
    elif prefs.experience_level == "senior" and is_entry:
        score -= 20
        reasons["seniority_penalty"] = "entry-level role"
    elif prefs.experience_level == "mid" and is_senior and any(
        m in title for m in ("director", "vp ", "chief", "head of")
    ):
        score -= 15
        reasons["seniority_penalty"] = "leadership role"

    final = int(max(0, min(100, round(score))))
    return final, reasons


def explain(reasons: dict) -> str:
    """One-line summary for CLI/dashboard."""
    if "rejected" in reasons:
        return f"✗ {reasons['rejected']}"
    bits = []
    if reasons.get("title_match"):
        bits.append("title: " + ", ".join(reasons["title_match"]))
    elif reasons.get("title_match_in_description"):
        bits.append("title (in text): " + ", ".join(reasons["title_match_in_description"]))
    if reasons.get("location_match"):
        bits.append("location: " + ", ".join(reasons["location_match"]))
    if reasons.get("industry_match"):
        bits.append("industry: " + ", ".join(reasons["industry_match"]))
    if reasons.get("language_signal"):
        bits.append("language: " + ", ".join(reasons["language_signal"]))
    if reasons.get("salary_ok"):
        bits.append(f"salary: {reasons['salary_ok']}")
    if reasons.get("seniority_penalty"):
        bits.append(f"⚠ {reasons['seniority_penalty']}")
    if reasons.get("posted_days_ago") is not None:
        bits.append(f"{reasons['posted_days_ago']}d ago")
    return " · ".join(bits) or "general match"
