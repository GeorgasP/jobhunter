"""
Job → User matcher. Scores each job per user preferences.

Multi-tenant version of the original _job_hunter.py scoring logic,
generalized for any user's preferences (not just crypto/Greek market).
"""
import re
from app.schemas import UserPreferences


def score_job_for_user(
    job_title: str,
    job_location: str,
    job_description: str,
    prefs: UserPreferences,
) -> tuple[int, dict]:
    """
    Score 0-100 for relevance of job to user. Returns (score, reasons).

    Threshold > 30 to be shown to user.
    < 0 means hard-disqualified.
    """
    text = " ".join([
        (job_title or "").lower(),
        (job_location or "").lower(),
        (job_description or "")[:2000].lower(),
    ])

    score = 0
    reasons = {}

    # ─── DISQUALIFIERS ───
    for kw in prefs.exclude_keywords or []:
        if kw.lower() in text:
            return -100, {"disqualified": f"matched exclude keyword: {kw}"}

    # ─── LOCATION MATCH ───
    location_score = 0
    matched_loc = None
    for loc in prefs.locations or []:
        if loc.lower() == "remote" or "remote" in loc.lower():
            if "remote" in text:
                location_score = max(location_score, 50)
                matched_loc = "Remote"
        elif loc.lower() in (job_location or "").lower():
            location_score = max(location_score, 50)
            matched_loc = loc

    if location_score == 0 and prefs.remote_only and "remote" not in text:
        return -100, {"disqualified": "not remote (remote_only=true)"}

    score += location_score
    if location_score > 0:
        reasons["location_match"] = matched_loc

    # ─── ROLE MATCH ───
    for role in prefs.roles or []:
        if role.lower() in text:
            score += 25
            reasons.setdefault("matched_roles", []).append(role)
            break

    # ─── INDUSTRY HINTS ───
    for industry in prefs.industries or []:
        if industry.lower() in text:
            score += 15
            reasons.setdefault("matched_industries", []).append(industry)
            break

    # ─── EXPERIENCE LEVEL ───
    senior_keywords = ["senior", "lead", "principal", "staff", "director",
                       "head of", "vp ", "chief", "manager"]
    entry_keywords = ["junior", "entry", "associate", "graduate", "trainee",
                      "intern", "specialist"]

    is_senior_listing = any(k in text for k in senior_keywords)
    is_entry_listing = any(k in text for k in entry_keywords)

    if prefs.experience_level == "entry":
        if is_senior_listing:
            score -= 30
            reasons["penalty"] = "senior role mismatch"
        if is_entry_listing:
            score += 15
            reasons["bonus"] = "entry-level match"
    elif prefs.experience_level == "senior":
        if is_entry_listing:
            score -= 20
        if is_senior_listing:
            score += 15

    # ─── LANGUAGE PREFERENCE ───
    lang_keywords = {
        "en": [],  # default
        "el": ["greek", "ελληνικά", "greece"],
        "es": ["spanish", "español", "spain", "madrid", "barcelona"],
        "de": ["german", "deutsch", "germany"],
        "fr": ["french", "français", "france"],
    }
    for lang in prefs.languages or []:
        for kw in lang_keywords.get(lang, []):
            if kw in text:
                score += 20
                reasons.setdefault("language_signal", []).append(lang)
                break

    return max(0, min(100, score)), reasons


def matches_threshold(score: int, threshold: int = 30) -> bool:
    """Returns True if job should be shown to user."""
    return score >= threshold
