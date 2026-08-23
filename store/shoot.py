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
WINDOW_H = H + 90                      # ό,τι κρατάει για τον εαυτό του το Chrome
PORT = 8791
ROOT = pathlib.Path(__file__).resolve().parent.parent
SHOTS = ROOT / "store" / "screenshots"
PAGES = ["1-matches", "2-pipeline", "5-profile", "3-autofill", "4-onboarding"]

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


def main():
    if CHROME is None:
        print("  δεν βρέθηκε το chrome.exe — βάλε τη διαδρομή στο CHROME")
        return 1
    from PIL import Image                      # μόνο για το κόψιμο

    httpd = serve()
    tmp = pathlib.Path(tempfile.mkdtemp())
    SHOTS.mkdir(exist_ok=True)
    made = 0

    try:
        for i, name in enumerate(PAGES, 1):
            raw = tmp / f"{name}.png"
            subprocess.run([
                str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                "--force-device-scale-factor=1", f"--window-size={W},{WINDOW_H}",
                "--virtual-time-budget=6000", f"--screenshot={raw}",
                f"http://127.0.0.1:{PORT}/store/screenshots/{name}.html",
            ], capture_output=True, timeout=120)

            if not raw.exists():
                print(f"  [ ] {i}.png  το Chrome δεν έγραψε τίποτα για «{name}»")
                continue

            out = SHOTS / f"{i}.png"
            Image.open(raw).crop((0, 0, W, H)).save(out)
            size = png_size(out)
            if size != (W, H):
                print(f"  [!] {i}.png  βγήκε {size[0]}×{size[1]}")
                continue
            print(f"  [x] {i}.png  {W}×{H}  ({out.stat().st_size // 1024} KB)  {name}")
            made += 1
    finally:
        httpd.shutdown()

    print(f"\n  {made}/{len(PAGES)} έτοιμα στο store/screenshots/")
    return 0 if made == len(PAGES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
