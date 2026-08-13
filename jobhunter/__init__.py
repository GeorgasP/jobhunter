"""
JobHunter — automated job discovery, matching, applying & tracking.

Zero third-party dependencies: stdlib only (urllib, sqlite3, smtplib, imaplib,
http.server). Τρέχει με σκέτη Python 3.11+, χωρίς pip install.

  python -m jobhunter init        → φτιάχνει profile + DB
  python -m jobhunter run         → scan + match + prepare applications
  python -m jobhunter serve       → local dashboard στο http://127.0.0.1:8765
  python -m jobhunter inbox       → διαβάζει απαντήσεις εταιρειών από το mail σου
"""

__version__ = "2.0.0"
