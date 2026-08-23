# -*- coding: utf-8 -*-
"""
Έλεγχος πριν από κάθε υποβολή στο Chrome Web Store.

Πιάνει ό,τι απορρίπτεται αυτόματα (manifest, εικονίδια, όρια χαρακτήρων) και
ό,τι θα έσπαγε μόνο μετά την εγκατάσταση (domain εκτός host_permissions,
κλειδί μετάφρασης που λείπει, στοιχείο DOM που δεν υπάρχει).

    python store/preflight.py

Δεν αντικαθιστά το store/SMOKE_TEST.md: το service worker, τα alarms, οι
ειδοποιήσεις και η συμπλήρωση φορμών θέλουν πραγματικό Chrome.
"""

import json, pathlib, re, sys, zipfile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = pathlib.Path(r"C:\Users\Panos\Desktop\JobHunt")
E = R / "extension"

fails, warns, oks = [], [], []
def ok(m): oks.append(m)
def bad(m): fails.append(m)
def warn(m): warns.append(m)

m = json.loads((E / "manifest.json").read_text(encoding="utf-8"))

# ── Υποχρεωτικά πεδία ────────────────────────────────────────────────
if m.get("manifest_version") == 3: ok("manifest_version 3")
else: bad(f"manifest_version = {m.get('manifest_version')} — το 2 δεν γίνεται πια δεκτό")

name = m.get("name", "")
if not name: bad("λείπει το name")
elif len(name) > 45: bad(f"name {len(name)} χαρακτήρες — όριο 45")
else: ok(f"name «{name}» ({len(name)}/45)")

desc = m.get("description", "")
if not desc: bad("λείπει η description — υποχρεωτική")
elif len(desc) > 132: bad(f"description {len(desc)} χαρακτήρες — όριο 132")
else: ok(f"description ({len(desc)}/132)")

if re.fullmatch(r"\d+(\.\d+){0,3}", str(m.get("version", ""))): ok(f"version {m['version']}")
else: bad(f"version «{m.get('version')}» — μόνο αριθμοί και τελείες")

# ── Εικονίδια ────────────────────────────────────────────────────────
icons = m.get("icons", {})
need = {"16", "48", "128"}
have = set(icons)
if need <= have: ok(f"icons {sorted(have, key=int)}")
else: bad(f"λείπουν εικονίδια: {sorted(need - have)}")
for size, rel in icons.items():
    f = E / rel
    if not f.exists(): bad(f"το εικονίδιο {size} δείχνει σε ανύπαρκτο αρχείο: {rel}")

# ── Δικαιώματα: κάθε ένα θέλει δικαιολόγηση στη φόρμα ───────────────
perms = m.get("permissions", [])
hosts = m.get("host_permissions", [])
ok(f"permissions: {', '.join(perms)}")
ok(f"host_permissions: {len(hosts)} μοτίβα")
if "<all_urls>" in hosts or "*://*/*" in hosts:
    bad("<all_urls> — προκαλεί σχεδόν βέβαιο πρόσθετο έλεγχο· ζήτα μόνο ό,τι χρειάζεσαι")
if "tabs" in perms:
    warn("το «tabs» θεωρείται ευαίσθητο· βεβαιώσου ότι το δικαιολογείς")

# ── Αρχεία που δηλώνονται αλλά λείπουν ──────────────────────────────
refs = []
sw = m.get("background", {}).get("service_worker")
if sw: refs.append(sw)
if m.get("action", {}).get("default_popup"): refs.append(m["action"]["default_popup"])
for cs in m.get("content_scripts", []):
    refs += cs.get("js", []) + cs.get("css", [])
for r in refs:
    if not (E / r).exists(): bad(f"το manifest δηλώνει {r} που δεν υπάρχει")
if refs: ok(f"{len(refs)} δηλωμένα αρχεία υπάρχουν όλα")

# ── Απαγορευμένα σε MV3 ─────────────────────────────────────────────
for f in E.rglob("*.js"):
    src = f.read_text(encoding="utf-8", errors="replace")
    rel = f.relative_to(E)
    if re.search(r'\beval\s*\(', src): bad(f"{rel}: eval() — απαγορεύεται")
    if re.search(r'new\s+Function\s*\(', src): bad(f"{rel}: new Function() — απαγορεύεται")
    if re.search(r'<script[^>]*src=["\']https?://', src):
        bad(f"{rel}: φορτώνει απομακρυσμένο script — απαγορεύεται")

# ── Το ίδιο το zip ──────────────────────────────────────────────────
z = sorted((R / "store/dist").glob("*.zip"))
if not z: bad("δεν υπάρχει zip στο store/dist — τρέξε python store/package.py")
else:
    zf = z[-1]
    size = zf.stat().st_size
    with zipfile.ZipFile(zf) as a:
        names = a.namelist()
        if a.testzip() is not None: bad("το zip είναι κατεστραμμένο")
    if "manifest.json" not in names:
        bad("το manifest.json δεν είναι στη ΡΙΖΑ του zip — η Google θα το απορρίψει")
    else: ok("το manifest.json είναι στη ρίζα του zip")
    if size > 100 * 1024 * 1024: bad(f"zip {size//1048576} MB — όριο 100 MB")
    else: ok(f"zip {size//1024} KB, {len(names)} αρχεία")
    junk = [n for n in names if n.startswith(".") or "__MACOSX" in n or n.endswith(".map")]
    if junk: warn(f"περιττά αρχεία στο zip: {junk[:4]}")

# ── Screenshots ─────────────────────────────────────────────────────
shots = list((R / "store/screenshots").glob("*.png")) + list((R / "store/screenshots").glob("*.jpg"))
if not shots:
    bad("κανένα screenshot — απαιτείται τουλάχιστον 1 στα 1280×800 ή 640×400")
else:
    ok(f"{len(shots)} screenshots βρέθηκαν")

# ── Πολιτική απορρήτου ──────────────────────────────────────────────
if (R / "store/PRIVACY.html").exists(): ok("PRIVACY.html υπάρχει τοπικά")
else: bad("λείπει το PRIVACY.html")
# Δεν αρκεί το τοπικό αρχείο: η Google ζητάει URL που ανοίγει χωρίς login.
# Το ελέγχουμε αντί να το υπενθυμίζουμε κάθε φορά.
PRIVACY_URL = "https://georgasp.github.io/jobhunter/privacy.html"
try:
    import urllib.request
    with urllib.request.urlopen(PRIVACY_URL, timeout=15) as r:
        if r.status == 200: ok(f"η πολιτική είναι δημόσια: {PRIVACY_URL}")
        else: warn(f"η πολιτική απάντησε {r.status} — {PRIVACY_URL}")
except Exception as e:
    warn(f"η πολιτική δεν ανοίγει δημόσια ({type(e).__name__}) — {PRIVACY_URL}")

# ── Locales ─────────────────────────────────────────────────────────
locs = list((E / "locales").glob("*.json"))
ref = None
for f in sorted(locs):
    d = json.loads(f.read_text(encoding="utf-8"))
    if ref is None: ref = set(d)
    elif set(d) != ref: bad(f"{f.name}: διαφορετικά κλειδιά από το en.json")
ok(f"{len(locs)} γλώσσες, {len(ref)} κλειδιά η καθεμία")

print("=" * 60)
for x in oks: print(f"  ok    {x}")
print()
for x in warns: print(f"  ΠΡΟΣΟΧΗ  {x}")
print()
for x in fails: print(f"  ΚΟΒΕΙ    {x}")
print("=" * 60)
print(f"\n  {len(fails)} μπλοκάρουν την υποβολή · {len(warns)} θέλουν προσοχή")


print()


import json, pathlib, re, sys, zipfile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
E = pathlib.Path(r"C:\Users\Panos\Desktop\JobHunt\extension")
R = E.parent

fails, warns = [], []
def bad(m): fails.append(m)
def warn(m): warns.append(m)

html_files = {f.name: f.read_text(encoding="utf-8", errors="replace") for f in E.glob("*.html")}
js_files = {str(f.relative_to(E)): f.read_text(encoding="utf-8", errors="replace")
            for f in list(E.glob("*.js")) + list(E.glob("*/*.js"))}
locales = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in (E / "locales").glob("*.json")}
en = locales["en"]

# ── 1. Κάθε $("#id") στο JS πρέπει να υπάρχει σε κάποιο HTML ─────────
PAGES = {"app.js": "app.html", "onboarding.js": "onboarding.html", "popup.js": "popup.html"}
print("1 · Αναφορές σε στοιχεία που δεν υπάρχουν στο HTML")
found_any = False
for js, page in PAGES.items():
    if js not in js_files: continue
    html = html_files.get(page, "")
    ids_in_html = set(re.findall(r'id="([^"]+)"', html))
    # ids που φτιάχνονται δυναμικά μέσα σε template literals
    dynamic = set(re.findall(r'id="([a-z0-9-]+)\$\{', js_files[js]))
    dynamic |= set(re.findall(r'id="([a-z0-9-]+)"', js_files[js]))
    for m in re.finditer(r'\$\("#([a-zA-Z0-9_-]+)"\)', js_files[js]):
        el = m.group(1)
        if el not in ids_in_html and el not in dynamic:
            line = js_files[js][:m.start()].count("\n") + 1
            bad(f"{js}:{line} → #{el} δεν υπάρχει στο {page}")
            found_any = True
if not found_any: print("   κανένα\n")
else: print()

# ── 2. Κάθε κλειδί μετάφρασης που ζητά ο κώδικας πρέπει να υπάρχει ──
print("2 · Κλειδιά μετάφρασης που ζητούνται αλλά λείπουν")
used = set()
for src in list(js_files.values()):
    # Τα σχόλια περιέχουν παραδείγματα κλήσεων — δεν είναι πραγματική χρήση.
    clean = re.sub(r"/\*[\s\S]*?\*/|//[^\n]*", "", src)
    used |= set(re.findall(r'\bt\(\s*"([a-zA-Z0-9._]+)"', clean))
    # t(συνθήκη ? "a" : "b") — μετράνε και τα δύο σκέλη, αλλά μόνο μέσα σε t()
    for a, b in re.findall(
            r'\bt\(\s*[^(),]*?\?\s*"([a-zA-Z0-9._]+)"\s*:\s*"([a-zA-Z0-9._]+)"', clean):
        used |= {a, b}
for html in html_files.values():
    for attr in ("data-i18n", "data-i18n-ph", "data-i18n-title", "data-i18n-html", "data-i18n-doc"):
        used |= set(re.findall(attr + r'="([^"]+)"', html))
used = {u for u in used if not u.startswith("`")}
missing = sorted(u for u in used if u not in en)
if missing:
    for u in missing: bad(f"το κλειδί «{u}» δεν υπάρχει στο en.json")
else:
    print(f"   κανένα — {len(used)} κλειδιά σε χρήση, όλα υπάρχουν\n")

# δυναμικά stage.*
stages = ["prepared", "sent", "interview", "offer", "rejected"]
for s in stages:
    if f"stage.{s}" not in en: bad(f"λείπει το κλειδί stage.{s}")

# ── 3. Κλειδιά που υπάρχουν αλλά δεν χρησιμοποιούνται πουθενά ────────
print("3 · Κλειδιά που δεν χρησιμοποιούνται")
dyn_prefixes = ("stage.", "settings.experience.", "time.", "popup.", "notify.", "error.", "fill.")
unused = [k for k in en if k not in used and not k.startswith(dyn_prefixes)]
if unused: warn(f"{len(unused)} αχρησιμοποίητα: {', '.join(unused[:6])}{'…' if len(unused) > 6 else ''}")
print(f"   {len(unused)}\n")

# ── 4. Κάθε αρχείο που φορτώνει το HTML πρέπει να υπάρχει ────────────
print("4 · Αρχεία που φορτώνουν οι σελίδες")
n = 0
for page, html in html_files.items():
    for ref in re.findall(r'(?:src|href)="(?!https?:|#|data:)([^"]+)"', html):
        n += 1
        if not (E / ref).exists(): bad(f"{page} φορτώνει το {ref} που δεν υπάρχει")
print(f"   {n} αναφορές ελέγχθηκαν\n")

# ── 5. Κάθε import μεταξύ modules ────────────────────────────────────
print("5 · Imports μεταξύ αρχείων")
n = 0
for rel, src in js_files.items():
    base = (E / rel).parent
    for imp in re.findall(r'from\s+"(\./[^"]+)"', src):
        n += 1
        if not (base / imp).resolve().exists():
            bad(f"{rel}: import «{imp}» δεν βρέθηκε")
print(f"   {n} imports ελέγχθηκαν\n")

# ── 6. Το zip περιέχει ό,τι χρειάζεται ───────────────────────────────
print("6 · Πληρότητα του zip")
zips = sorted((R / "store/dist").glob("*.zip"))
if zips:
    with zipfile.ZipFile(zips[-1]) as a: names = set(a.namelist())
    # Το package.py εξαιρεί σκόπιμα κάποια αρχεία· διαβάζουμε τη λίστα του.
    pkg = (R / "store/package.py").read_text(encoding="utf-8")
    skip = set(re.findall(r'"([^"]+)"', re.search(r"EXCLUDE_NAMES\s*=\s*\{([^}]*)\}", pkg).group(1)))
    pats = re.findall(r'"([^"]+)"', re.search(r"EXCLUDE_PATTERNS\s*=\s*\(([^)]*)\)", pkg).group(1))
    need = {str(f.relative_to(E)).replace("\\", "/")
            for f in E.rglob("*")
            if f.is_file() and f.name not in skip and not any(p in f.name for p in pats)}
    absent = sorted(need - names)
    if absent: bad(f"λείπουν από το zip: {absent[:6]}")
    else: print(f"   και τα {len(need)} αρχεία του extension είναι μέσα\n")
else: bad("δεν υπάρχει zip")

# ── 7. Content scripts: έγκυρα match patterns ────────────────────────
print("7 · Content scripts")
m = json.loads((E / "manifest.json").read_text(encoding="utf-8"))
for cs in m.get("content_scripts", []):
    for pat in cs.get("matches", []):
        if not re.match(r'^(\*|https?|file|ftp)://', pat):
            bad(f"άκυρο match pattern: {pat}")
    print(f"   {len(cs.get('matches', []))} μοτίβα, {len(cs.get('js', []))} scripts")
print()

print("=" * 62)
for w in warns: print(f"  ΠΡΟΣΟΧΗ  {w}")
for f in fails: print(f"  ΣΦΑΛΜΑ   {f}")
print("=" * 62)
print(f"\n  {len(fails)} σφάλματα · {len(warns)} προειδοποιήσεις")
