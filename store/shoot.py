# -*- coding: utf-8 -*-
"""
Βγάζει τα screenshots του listing μόνο του, χωρίς χέρια.

Γιατί υπάρχει: οι λήψεις με το χέρι βγήκαν 1310×991 επειδή το παράθυρο του
Chrome δεν είναι ποτέ ακριβώς όσο νομίζεις — υπάρχει η μπάρα διεύθυνσης, το
zoom, η κλίμακα της οθόνης. Η Google θέλει ακριβώς 1280×800 και απορρίπτει
οτιδήποτε άλλο. Εδώ το μέγεθος δεν εξαρτάται από την οθόνη κανενός.

Δύο λεπτομέρειες που κόστισαν:

  • Το headless=new κρατάει ~90 πίξελ του παραθύρου για τον εαυτό του, οπότε
    ζητάμε 890 ύψος και κόβουμε τα πρώτα 800. Αν ζητήσεις 800, το ωφέλιμο
    είναι 710 και η σελίδα βγαίνει κομμένη.

  • Χωρίς virtual-time-budget η λήψη γίνεται πριν τελειώσουν τα animations
    εισόδου, που ξεκινούν από opacity 0 — οι κάρτες βγαίνουν αόρατες και η
    εικόνα δείχνει άδεια εφαρμογή.

Τρέξιμο:  python store/shoot.py
"""
import http.server, functools, pathlib, socketserver, struct, subprocess
import sys, tempfile, threading

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

W, H = 1280, 800
CHROME_INSET = 90                      # ό,τι κρατάει για τον εαυτό του το Chrome
PORT = 8791
ROOT = pathlib.Path(__file__).resolve().parent.parent
SHOTS = ROOT / "store" / "screenshots"
PAGES = ["1-matches", "2-pipeline", "5-profile", "3-autofill", "4-onboarding"]

# Η κάρτα που βλέπει ο κόσμος όταν μοιράζεσαι τον σύνδεσμο. Ζούσε μόνο ως PNG,
# οπότε το νούμερο μέσα της δεν μπορούσε να ενημερωθεί μαζί με τον κώδικα.
OG = ("docs/og.html", ROOT / "docs" / "og.png", 1200, 630)

# Προαιρετικά στο store, αλλά το μικρό είναι ό,τι βλέπει κανείς όταν ξεφυλλίζει
# μια κατηγορία — εκεί κρίνεται αν θα ανοίξει καν τη σελίδα.
PROMO = [
    ("store/promo/small.html", ROOT / "store" / "promo" / "440x280.png", 440, 280),
    ("store/promo/marquee.html", ROOT / "store" / "promo" / "1400x560.png", 1400, 560),
]

CHROME = next((p for p in [
    pathlib.Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    pathlib.Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    pathlib.Path("/usr/bin/google-chrome"),
    pathlib.Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
] if p.exists()), None)


def serve():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(ROOT))
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def png_size(path):
    b = path.read_bytes()
    return struct.unpack(">II", b[16:24]) if b[:8] == b"\x89PNG\r\n\x1a\n" else None


def capture(page, out, w, h, tmp):
    """Μία σελίδα → ένα PNG ακριβώς w×h."""
    from PIL import Image                      # μόνο για το κόψιμο

    raw = tmp / (out.stem + "-raw.png")
    subprocess.run([
        str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--force-device-scale-factor=1", f"--window-size={w},{h + CHROME_INSET}",
        # Ο χρόνος δεν αρκεί από μόνος του: μια λήψη έχασε τρεις από τις πέντε
        # στήλες του πίνακα επειδή περίμεναν ακόμη τη σειρά τους. Αντί να
        # ελπίζουμε ότι πρόλαβαν, ζητάμε να μην ξεκινήσουν καθόλου.
        "--force-prefers-reduced-motion",
        "--virtual-time-budget=6000", f"--screenshot={raw}",
        f"http://127.0.0.1:{PORT}/{page}",
    ], capture_output=True, timeout=120)

    if not raw.exists():
        print(f"  [ ] {out.name}  το Chrome δεν έγραψε τίποτα για «{page}»")
        return 0

    out.parent.mkdir(exist_ok=True)
    Image.open(raw).crop((0, 0, w, h)).save(out)
    size = png_size(out)
    if size != (w, h):
        print(f"  [!] {out.name}  βγήκε {size[0]}×{size[1]}")
        return 0
    print(f"  [x] {out.name}  {w}×{h}  ({out.stat().st_size // 1024} KB)  {page}")
    return 1


def stage_for_upload():
    """
    Μαζεύει σε έναν φάκελο ό,τι σέρνεται στη φόρμα του store.

    Γιατί: οι εικόνες ζουν δίπλα στις HTML πηγές τους, σε τρεις διαφορετικούς
    φακέλους. Τη στιγμή που ανεβάζεις, δεν θέλεις να διαλέγεις ανάμεσα σε
    «1.png» και «1-matches.html» — θέλεις έναν φάκελο όπου κάθε όνομα λέει
    μόνο του πού πάει, και όπου τα screenshots μένουν στη σειρά τους.
    """
    out = ROOT / "store" / "dist" / "upload"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.png"):
        old.unlink()

    staged = []
    for i in range(1, len(PAGES) + 1):
        staged.append((SHOTS / f"{i}.png", out / f"screenshot-{i}.png"))
    staged.append((ROOT / "store" / "promo" / "440x280.png", out / "promo-small-440x280.png"))
    staged.append((ROOT / "store" / "promo" / "1400x560.png", out / "promo-marquee-1400x560.png"))
    staged.append((ROOT / "extension" / "icons" / "128.png", out / "store-icon-128.png"))

    for src, dst in staged:
        if src.exists():
            dst.write_bytes(src.read_bytes())
            print(f"  [x] {dst.name}")
        else:
            print(f"  [ ] λείπει το {src.name}")
    return out


def main():
    if CHROME is None:
        print("  δεν βρέθηκε το chrome.exe — βάλε τη διαδρομή στο CHROME")
        return 1

    httpd = serve()
    tmp = pathlib.Path(tempfile.mkdtemp())
    made = 0

    try:
        print("  Screenshots του listing")
        for i, name in enumerate(PAGES, 1):
            made += capture(f"store/screenshots/{name}.html", SHOTS / f"{i}.png", W, H, tmp)

        print("\n  Κάρτα κοινοποίησης")
        page, out, w, h = OG
        made += capture(page, out, w, h, tmp)

        print("\n  Promo tiles του store")
        for page, out, w, h in PROMO:
            made += capture(page, out, w, h, tmp)
    finally:
        httpd.shutdown()

    total = len(PAGES) + 1 + len(PROMO)
    print(f"\n  {made}/{total} έτοιμα")

    print("\n  Έτοιμα για ανέβασμα")
    folder = stage_for_upload()
    print(f"\n  {folder}")
    return 0 if made == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
