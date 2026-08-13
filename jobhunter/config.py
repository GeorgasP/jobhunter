"""
Paths + settings.

Settings resolution order (last wins):
  1. defaults εδώ
  2. data/settings.json
  3. environment variables (JOBHUNTER_* / ANTHROPIC_API_KEY)

Τα secrets μένουν ΤΟΠΙΚΑ στο data/settings.json. Τίποτα δεν φεύγει από το
μηχάνημά σου εκτός από: (a) τα public job-board APIs, (b) το Anthropic API αν
βάλεις key, (c) το δικό σου SMTP/IMAP.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, fields
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
PACKS_DIR = OUTPUT_DIR / "applications"

DB_PATH = DATA_DIR / "jobhunter.db"
PROFILE_PATH = DATA_DIR / "profile.json"
SETTINGS_PATH = DATA_DIR / "settings.json"


@dataclass
class Settings:
    # ── AI (προαιρετικό: χωρίς key πέφτει σε template cover letters) ──
    anthropic_api_key: str = ""
    claude_model: str = "claude-haiku-4-5-20251001"

    # ── Outgoing mail (για email applications + follow-ups) ──
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""          # Gmail → app password, ΟΧΙ το κανονικό
    smtp_from: str = ""

    # ── Incoming mail (για auto-tracking απαντήσεων) ──
    imap_host: str = ""
    imap_port: int = 993
    imap_user: str = ""
    imap_password: str = ""
    imap_folder: str = "INBOX"

    # ── Behaviour ──
    min_score: int = 45              # κάτω από αυτό δεν εμφανίζεται καν
    daily_limit: int = 25            # max νέα applications ανά run
    auto_send_email: bool = False    # True = στέλνει email applications χωρίς ερώτηση
    open_browser: bool = True        # άνοιγμα του apply URL στο assisted apply
    server_port: int = 8765

    # Κλειδί για το autofill API. Χωρίς αυτό, οποιοδήποτε site που επισκέπτεσαι
    # θα μπορούσε να ζητήσει τα στοιχεία σου από τον local server.
    api_token: str = ""

    def save(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(
            json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8"
        )

    @property
    def has_ai(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def has_smtp(self) -> bool:
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)

    @property
    def has_imap(self) -> bool:
        return bool(self.imap_host and self.imap_user and self.imap_password)

    def ensure_token(self) -> str:
        """Σταθερό token — επιβιώνει restart, ώστε bookmarklet/extension να μη ξαναδένονται."""
        if not self.api_token:
            import secrets

            self.api_token = secrets.token_urlsafe(24)
            self.save()
        return self.api_token


_ENV_PREFIX = "JOBHUNTER_"


def load_settings() -> Settings:
    data: dict = {}

    if SETTINGS_PATH.exists():
        try:
            data.update(json.loads(SETTINGS_PATH.read_text(encoding="utf-8")))
        except json.JSONDecodeError as e:
            raise SystemExit(f"Χαλασμένο {SETTINGS_PATH}: {e}")

    # `from __future__ import annotations` κάνει τα f.type strings, οπότε
    # παίρνουμε τους τύπους από τα defaults.
    defaults = Settings()
    known = {f.name: type(getattr(defaults, f.name)) for f in fields(Settings)}

    for name in known:
        env_val = os.environ.get(_ENV_PREFIX + name.upper())
        if env_val is not None:
            data[name] = env_val

    # Το ANTHROPIC_API_KEY είναι η καθιερωμένη μεταβλητή — τη σεβόμαστε.
    if os.environ.get("ANTHROPIC_API_KEY"):
        data.setdefault("anthropic_api_key", os.environ["ANTHROPIC_API_KEY"])

    clean: dict = {}
    for name, value in data.items():
        if name not in known:
            continue
        kind = known[name]
        if kind is bool:
            clean[name] = value if isinstance(value, bool) else str(value).strip().lower() in ("1", "true", "yes", "on")
        elif kind is int:
            clean[name] = int(value)
        else:
            clean[name] = str(value)

    return Settings(**clean)


def ensure_dirs() -> None:
    for d in (DATA_DIR, OUTPUT_DIR, PACKS_DIR):
        d.mkdir(parents=True, exist_ok=True)
