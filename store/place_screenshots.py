# -*- coding: utf-8 -*-
"""
Παίρνει τις λήψεις από τα Downloads, ελέγχει ότι είναι ακριβώς 1280×800 και
τις βάζει στο store/screenshots ως 1.png … 4.png.

Δεν τις μεγεθύνει: μια μαλακή εικόνα στο listing φαίνεται, και είναι το πρώτο
πράγμα που βλέπει ο κόσμος. Αν το μέγεθος δεν είναι σωστό, το λέει και σου
δείχνει τι να ξανακάνεις.
"""
import pathlib, struct, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

W, H = 1280, 800
ORDER = ["1-matches", "2-pipeline", "3-autofill", "4-onboarding"]
SRC = pathlib.Path.home() / "Downloads"
DST = pathlib.Path(__file__).resolve().parent / "screenshots"

def png_size(p):
    b = p.read_bytes()
    if b[:8] != b"\x89PNG\r\n\x1a\n": return None
    return struct.unpack(">II", b[16:24])

ok = bad = 0
for i, name in enumerate(ORDER, 1):
    hits = sorted(SRC.glob(f"*{name}*.png"), key=lambda f: -f.stat().st_mtime)
    if not hits:
        print(f"  [ ] {i}.png  δεν βρέθηκε λήψη για «{name}»"); bad += 1; continue
    src = hits[0]
    size = png_size(src)
    if size != (W, H):
        print(f"  [!] {i}.png  η λήψη είναι {size[0]}×{size[1]}, χρειάζεται {W}×{H}")
        print(f"        ξανακάνε την με Ctrl+Shift+M και μέγεθος 1280×800, zoom 100%")
        bad += 1; continue
    DST.mkdir(exist_ok=True)
    (DST / f"{i}.png").write_bytes(src.read_bytes())
    print(f"  [x] {i}.png  {W}×{H}  ({src.stat().st_size // 1024} KB)")
    ok += 1

print(f"\n  τοποθετήθηκαν {ok}/4")
if bad:
    print("  Οι λήψεις μένουν στα Downloads — ξαναδοκίμασε και ξανατρέξε το.")
else:
    print("  Ολα ετοιμα. Trekse:  python store/preflight.py")
