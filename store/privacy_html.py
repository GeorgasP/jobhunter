# -*- coding: utf-8 -*-
"""
Φτιάχνει τις δύο HTML πολιτικές από το PRIVACY.md.

Γιατί υπάρχει: η πολιτική ζούσε σε τρία αντίγραφα — PRIVACY.md, PRIVACY.html
και docs/privacy.html — συντηρημένα στο χέρι. Ξέφυγαν. Το κείμενο έλεγε «δύο
προορισμοί» και «δώδεκα πηγές» ενώ η εφαρμογή είχε ήδη τρεις και εικοσιτέσσερις,
και δεν ανέφερε καθόλου το κουμπί στα κοινωνικά δίκτυα. Ένα αρχείο είναι η
αλήθεια· τα άλλα δύο παράγονται.

Τρέξιμο:  python store/privacy_html.py
"""
import html as _html
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "store" / "PRIVACY.md"
OUT = [ROOT / "store" / "PRIVACY.html", ROOT / "docs" / "privacy.html"]

STYLE = """body{max-width:720px;margin:0 auto;padding:48px 22px 90px;
  font:16px/1.7 -apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;color:#1b2029;background:#fff}
h1{font-size:30px;letter-spacing:-.7px;margin:0 0 6px}
h2{font-size:19px;letter-spacing:-.3px;margin:34px 0 10px}
p,li{color:#333b47}ul{padding-left:22px}li{margin:5px 0}
code{background:#f2f4f7;padding:2px 6px;border-radius:5px;font-size:14px}
a{color:#2f6fe0}strong{color:#111}
@media(prefers-color-scheme:dark){body{background:#0f1319;color:#e6ebf2}
  p,li{color:#b7c1cf}h1,h2,strong{color:#f2f5f9}code{background:#1b2029}a{color:#7aa7ff}}"""


def inline(s):
    """Το υποσύνολο της Markdown που χρησιμοποιεί όντως η πολιτική."""
    s = _html.escape(s, quote=False)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def render(md):
    out, para, bullets = [], [], []

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()
        if bullets:
            out.append("<ul>" + "".join(f"<li>{inline(b)}</li>" for b in bullets) + "</ul>")
            bullets.clear()

    for line in md.split("\n"):
        line = line.rstrip()
        if not line.strip():
            flush()
        elif line.startswith("## "):
            flush()
            out.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith("# "):
            flush()
            out.append(f"<h1>{inline(line[2:])}</h1>")
        elif line.startswith("- "):
            if para:
                flush()
            bullets.append(line[2:])
        elif bullets:
            bullets[-1] += " " + line.strip()      # συνέχεια κουκκίδας
        else:
            para.append(line.strip())
    flush()
    return "\n".join(out)


def main():
    md = SRC.read_text(encoding="utf-8")
    title = re.search(r"^# (.+)$", md, re.M).group(1)
    page = (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f"<title>{_html.escape(title)}</title>\n"
        f"<style>\n{STYLE}\n</style></head><body>\n"
        f"{render(md)}\n"
        "</body></html>\n"
    )
    for p in OUT:
        p.write_text(page, encoding="utf-8")
        print(f"  [x] {p.relative_to(ROOT)}  ({len(page) // 1024 + 1} KB)")
    print("\n  Θυμήσου: το docs/ σερβίρεται από GitHub Pages — θέλει push για να ζωντανέψει.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
