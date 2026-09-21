# -*- coding: utf-8 -*-
"""
Συγκρίνει ό,τι υπόσχεται το LISTING.md με ό,τι κάνει όντως το extension.

Γιατί υπάρχει: η πολιτική απορρήτου, η περιγραφή του store και η κάρτα
κοινοποίησης βρέθηκαν και οι τρεις ξεπερασμένες — όχι από αμέλεια, αλλά επειδή
κανείς δεν τις ξαναδιαβάζει όταν προστίθεται μια πηγή. Το preflight ελέγχει ότι
ο κώδικας τρέχει· αυτό ελέγχει ότι λέμε την αλήθεια γι' αυτόν.

Τρέξιμο:  python store/audit_listing.py
"""
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parent.parent
E = ROOT / "extension"
DOCS = {name: (ROOT / "store" / name).read_text(encoding="utf-8")
        for name in ("LISTING.md", "PRIVACY.md", "SUBMISSION.md")}
MANIFEST = json.loads((E / "manifest.json").read_text(encoding="utf-8"))
SOURCES = (E / "lib" / "sources.js").read_text(encoding="utf-8")

fails, warns = [], []


def check(ok, label, detail=""):
    print(f"  {'ok  ' if ok else 'ΛΑΘΟΣ'}  {label}" + (f"   {detail}" if detail else ""))
    if not ok:
        fails.append(label)


def boards():
    part = SOURCES[SOURCES.index("export const BOARDS"):]
    return set(re.findall(r"^  async (\w+)\(", part, re.M))


def ats():
    part = SOURCES[SOURCES.index("const ATS ="):SOURCES.index("export const BOARDS")]
    return set(re.findall(r"^  async (\w+)\(", part, re.M))


# ── 1. Τίτλος και σύνοψη: το store τα παίρνει από το manifest ────────
print("1 · Τίτλος και σύνοψη — πρέπει να ταιριάζουν με το manifest")
name = re.search(r"\*\*Name\*\* \(max 75\)\n```\n(.+?)\n```", DOCS["LISTING.md"], re.S)
short = re.search(r"\*\*Short description\*\*[^\n]*\n```\n(.+?)\n```", DOCS["LISTING.md"], re.S)
check(name and name.group(1).strip() == MANIFEST["name"], "Name == manifest.name",
      f"«{MANIFEST['name']}»")
check(short and short.group(1).strip() == MANIFEST["description"],
      "Short description == manifest.description", f"{len(MANIFEST['description'])}/132")

# ── 2. Άδειες: καμία αδικαιολόγητη, καμία φανταστική ────────────────
print("\n2 · Άδειες — κάθε μία δηλωμένη πρέπει να δικαιολογείται")
listing = DOCS["LISTING.md"]
for perm in MANIFEST["permissions"]:
    check(f"`{perm}`" in listing, f"δικαιολογείται το «{perm}»")
check("optional host permissions" in listing.lower(),
      "αναφέρονται οι προαιρετικές άδειες (κοινωνικά δίκτυα)")

# ── 3. Πηγές: ό,τι χτυπάει ο κώδικας πρέπει να το λένε τα κείμενα ───
print("\n3 · Πηγές — ό,τι κατεβάζουμε πρέπει να δηλώνεται")
NAMES = {
    "remotive": "Remotive", "arbeitnow": "Arbeitnow", "remoteok": "RemoteOK",
    "jobicy": "Jobicy", "himalayas": "Himalayas", "workingnomads": "WorkingNomads",
    "themuse": "The Muse", "weworkremotely": "We Work Remotely",
    "cryptojobs": "Cryptocurrency Jobs", "landingjobs": "Landing.jobs",
    "devitjobs": "DevITjobs", "adzuna": "Adzuna", "psf": "psf.org.gr",
    "skywalker": "skywalker.gr", "ordino": "ordino.gr",
    "greenhouse": "Greenhouse", "lever": "Lever", "ashby": "Ashby",
    "workable": "Workable", "smartrecruiters": "SmartRecruiters",
    "recruitee": "Recruitee", "workday": "Workday", "teamtailor": "Teamtailor",
    "breezy": "Breezy",
}
for doc in ("LISTING.md", "PRIVACY.md"):
    missing = sorted(NAMES[k] for k in (boards() | ats())
                     if k in NAMES and NAMES[k].lower() not in DOCS[doc].lower())
    check(not missing, f"{doc} αναφέρει όλες τις πηγές",
          "λείπουν: " + ", ".join(missing) if missing else f"{len(boards() | ats())} πηγές")

unknown = sorted((boards() | ats()) - set(NAMES))
if unknown:
    warns.append(f"νέες πηγές που δεν ξέρει ο έλεγχος: {', '.join(unknown)}")

# ── 4. Hosts: κάθε host_permission να έχει λόγο ύπαρξης ─────────────
print("\n4 · Host permissions — κάθε τομέας να εξηγείται κάπου")
SPECIAL = {"open.er-api.com": "exchange rate", "api.anthropic.com": "anthropic"}
for host, word in SPECIAL.items():
    check(word.lower() in listing.lower() and word.lower() in DOCS["PRIVACY.md"].lower(),
          f"εξηγείται το «{host}»")

# ── 5. Δείκτες που γερνάνε σιωπηλά ──────────────────────────────────
print("\n5 · Αριθμοί μέσα στα κείμενα")
W = re.search(r"const W = \{([^}]+)\}", (E / "lib" / "matcher.js").read_text(encoding="utf-8"))
weights = dict(re.findall(r"(\w+): (\d+)", W.group(1)))
claimed = re.search(r"\((\d+) points\), location \((\d+)\), industry \((\d+)\), language \((\d+)\)",
                    listing)
check(claimed and [claimed.group(i) for i in (1, 2, 3, 4)]
      == [weights["title"], weights["location"], weights["industry"], weights["language"]],
      "οι βαθμοί της περιγραφής == matcher.js",
      f"title {weights['title']} · location {weights['location']}")

langs = sorted(p.stem for p in (E / "locales").glob("*.json"))
check(str(len(langs)) in listing or "English, Greek, German" in listing,
      f"οι {len(langs)} γλώσσες αναφέρονται")

print("\n" + "=" * 62)
for w in warns:
    print(f"  ΠΡΟΣΟΧΗ  {w}")
print(f"  {len(fails)} ασυμφωνίες · {len(warns)} προειδοποιήσεις")
raise SystemExit(1 if fails else 0)
