"""
Το profile σου: ποιος είσαι, τι ψάχνεις, πού ψάχνει ο hunter.

Ένα αρχείο JSON (data/profile.json) — το επεξεργάζεσαι με το χέρι ή από το
dashboard. Δεν χρειάζεται DB migration για να αλλάξεις preferences.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .config import PROFILE_PATH, ROOT, ensure_dirs


@dataclass
class Preferences:
    titles: list[str] = field(default_factory=list)          # ρόλοι που θες
    must_have: list[str] = field(default_factory=list)       # λέξεις που ΠΡΕΠΕΙ να υπάρχουν
    exclude_keywords: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=lambda: ["Remote"])
    # Περιοχές όπου ΔΕΝ μπορείς να δουλέψεις (work authorization / timezone).
    # Κόβονται μόνο αν η αγγελία δεν αναφέρει και κάποια από τις locations σου.
    blocked_locations: list[str] = field(default_factory=list)
    # True = κράτα μόνο αγγελίες που καλύπτουν κάποια από τις locations σου
    # (ή είναι worldwide). False = δείξε τα πάντα και κρίνε μόνος σου.
    strict_location: bool = True
    remote_only: bool = False
    salary_min: int | None = None
    languages: list[str] = field(default_factory=lambda: ["en"])
    industries: list[str] = field(default_factory=list)
    experience_level: str = "mid"                            # entry | mid | senior
    max_age_days: int = 45


@dataclass
class Profile:
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    # Απαντήσεις που ζητούν σχεδόν όλες οι φόρμες — μπαίνουν στο apply pack.
    work_authorization: str = ""      # π.χ. "EU citizen", "US work permit", "needs sponsorship"
    notice_period: str = ""           # π.χ. "Immediately available", "1 month"
    default_language: str = "en"
    cv: dict[str, str] = field(default_factory=dict)         # lang -> path
    preferences: Preferences = field(default_factory=Preferences)
    targets: list[dict[str, str]] = field(default_factory=list)
    boards: list[str] = field(default_factory=lambda: ["remotive", "arbeitnow", "remoteok", "jobicy"])
    board_query: str = ""

    # ── CV helpers ──────────────────────────────────────────────
    def cv_path(self, language: str | None = None) -> Path | None:
        lang = language or self.default_language
        raw = self.cv.get(lang) or self.cv.get(self.default_language) or next(iter(self.cv.values()), None)
        if not raw:
            return None
        p = Path(raw)
        if not p.is_absolute():
            p = ROOT / p
        return p if p.exists() else None

    def cv_text(self, language: str | None = None, limit: int = 12000) -> str:
        path = self.cv_path(language)
        if not path:
            return ""
        if path.suffix.lower() == ".pdf":
            return _pdf_text(path)[:limit]
        return path.read_text(encoding="utf-8", errors="replace")[:limit]

    def save(self) -> None:
        ensure_dirs()
        PROFILE_PATH.write_text(
            json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8"
        )


def _pdf_text(path: Path) -> str:
    """Minimal PDF text extraction (χωρίς dependencies). Καλύτερα δώσε .md/.txt."""
    try:
        import zlib

        raw = path.read_bytes()
        chunks: list[str] = []
        for match in re.finditer(rb"stream\r?\n(.*?)endstream", raw, re.S):
            try:
                data = zlib.decompress(match.group(1))
            except zlib.error:
                continue
            for t in re.findall(rb"\((.*?)\)\s*Tj", data, re.S):
                chunks.append(t.decode("latin-1", errors="replace"))
        return " ".join(chunks)
    except Exception:
        return ""


def load_profile() -> Profile:
    if not PROFILE_PATH.exists():
        raise SystemExit(
            f"No profile found at {PROFILE_PATH}.\nRun this first:  python -m jobhunter init"
        )
    data: dict[str, Any] = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    prefs = Preferences(**{k: v for k, v in (data.pop("preferences", {}) or {}).items()
                           if k in Preferences.__dataclass_fields__})
    known = {k: v for k, v in data.items() if k in Profile.__dataclass_fields__}
    return Profile(preferences=prefs, **known)


# ════════════════════════════════════════════════════════════════
# Starter profile
# ════════════════════════════════════════════════════════════════
DEFAULT_BOARDS = ["remotive", "arbeitnow", "remoteok", "jobicy", "himalayas", "workingnomads"]


def build_profile(*, name: str = "", email: str = "", titles: list[str] | None = None,
                  locations: list[str] | None = None, blocked_locations: list[str] | None = None,
                  industries: list[str] | None = None, salary_min: int | None = None,
                  experience_level: str = "mid", languages: list[str] | None = None,
                  remote_only: bool = False, strict_location: bool = True,
                  exclude_keywords: list[str] | None = None,
                  cv: dict[str, str] | None = None, default_language: str = "en",
                  boards: list[str] | None = None, targets: list[dict] | None = None,
                  board_query: str = "") -> Profile:
    """Φτιάχνει profile από τις επιλογές του χρήστη. Καμία υπόθεση για χώρα ή κλάδο."""
    from . import companies

    industries = industries or []
    return Profile(
        name=name,
        email=email,
        default_language=default_language,
        cv=cv or _discover_cv_files(),
        preferences=Preferences(
            titles=titles or [],
            exclude_keywords=exclude_keywords or [],
            locations=locations or ["Remote"],
            blocked_locations=blocked_locations or [],
            strict_location=strict_location,
            remote_only=remote_only,
            salary_min=salary_min,
            languages=languages or [default_language],
            industries=industries,
            experience_level=experience_level,
        ),
        targets=targets if targets is not None else companies.pick(industries),
        boards=boards or list(DEFAULT_BOARDS),
        board_query=board_query,
    )


def _discover_cv_files() -> dict[str, str]:
    """Βρίσκει CV αρχεία στον φάκελο του project (cv.md, resume.pdf, CV_*.md...)."""
    found: dict[str, str] = {}
    patterns = [("en", ("cv*.md", "cv*.txt", "cv*.pdf", "resume*.md", "resume*.pdf")),
                ("el", ("*_gr.md", "*_el.md", "*_gr.pdf"))]
    for lang, globs in patterns:
        for pattern in globs:
            matches = sorted(ROOT.glob(pattern)) + sorted(ROOT.glob(pattern.upper()))
            for m in matches:
                name = m.name.lower()
                is_greek = "_gr" in name or "_el" in name
                key = "el" if is_greek else "en"
                found.setdefault(key, m.name)
    return found


def starter_profile(email: str = "", name: str = "") -> Profile:
    """Ουδέτερο profile: worldwide remote, χωρίς υπόθεση κλάδου ή χώρας."""
    return build_profile(name=name, email=email, locations=["Remote"], strict_location=False)
