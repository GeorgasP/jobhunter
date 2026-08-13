"""
Μετατρέπει τα CV της HTML σε PDF, με headless Chrome.

    python cv/build.py            # όλα τα cv_*.html
    python cv/build.py cv_en      # μόνο ένα

Γιατί Chrome: δίνει σωστό A4, πραγματικό κείμενο (άρα διαβάζεται από τα ATS)
και επιλέξιμα links — χωρίς καμία βιβλιοθήκη.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

CV_DIR = Path(__file__).resolve().parent

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]


def find_chrome() -> str:
    import os

    for path in CHROME_CANDIDATES:
        if Path(path).exists():
            return path
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        candidate = Path(local) / "Google/Chrome/Application/chrome.exe"
        if candidate.exists():
            return str(candidate)
    raise SystemExit("Chrome not found — install Chrome or edit CHROME_CANDIDATES.")


def to_pdf(chrome: str, html: Path) -> Path:
    pdf = html.with_suffix(".pdf")
    # Χωριστό προφίλ: αλλιώς το headless αρνείται αν τρέχει ήδη Chrome.
    with tempfile.TemporaryDirectory() as profile:
        cmd = [
            chrome, "--headless=new", "--disable-gpu", "--no-first-run",
            f"--user-data-dir={profile}",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf}",
            html.resolve().as_uri(),
        ]
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if not pdf.exists():
        raise SystemExit(f"Chrome did not produce {pdf.name}:\n{run.stderr[-800:]}")
    return pdf


def main() -> int:
    chrome = find_chrome()
    wanted = sys.argv[1:]
    files = [CV_DIR / f"{w}.html" if not w.endswith(".html") else CV_DIR / w for w in wanted] \
        or sorted(CV_DIR.glob("cv_*.html"))

    for html in files:
        if not html.exists():
            print(f"  x {html.name} not found")
            continue
        pdf = to_pdf(chrome, html)
        print(f"  + {pdf.name}  ({pdf.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
