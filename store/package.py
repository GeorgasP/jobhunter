"""
Χτίζει το .zip για το Chrome Web Store και ελέγχει ό,τι απορρίπτεται συχνά.

    python store/package.py
    python store/package.py --bump 1.0.1
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXT = ROOT / "extension"
OUT = ROOT / "store" / "dist"

# Ό,τι δεν πρέπει να μπει ποτέ στο πακέτο.
EXCLUDE_NAMES = {".DS_Store", "Thumbs.db", "README.md"}
EXCLUDE_PATTERNS = ("_preview", "_shim", ".map", ".zip", ".log")


def load_manifest() -> dict:
    return json.loads((EXT / "manifest.json").read_text(encoding="utf-8"))


def check(manifest: dict) -> list[str]:
    """Οι έλεγχοι που αντιστοιχούν στους πιο συχνούς λόγους απόρριψης."""
    problems: list[str] = []

    if manifest.get("manifest_version") != 3:
        problems.append("manifest_version must be 3 — MV2 is no longer accepted")

    name = manifest.get("name", "")
    if not name or len(name) > 75:
        problems.append(f"name must be 1-75 chars (currently {len(name)})")

    desc = manifest.get("description", "")
    if not desc:
        problems.append("description is required")
    elif len(desc) > 132:
        problems.append(f"description must be ≤132 chars (currently {len(desc)})")

    if not re.fullmatch(r"\d+(\.\d+){0,3}", manifest.get("version", "")):
        problems.append("version must be 1-4 dot-separated integers")

    for size in ("16", "32", "48", "128"):
        icon = manifest.get("icons", {}).get(size)
        if not icon:
            problems.append(f"missing {size}px icon in manifest")
        elif not (EXT / icon).exists():
            problems.append(f"icon file not found: {icon}")

    # Κάθε αρχείο που αναφέρεται πρέπει να υπάρχει
    referenced = [
        manifest.get("background", {}).get("service_worker"),
        manifest.get("action", {}).get("default_popup"),
        manifest.get("options_page"),
    ]
    for block in manifest.get("content_scripts", []):
        referenced += block.get("js", []) + block.get("css", [])
    for ref in filter(None, referenced):
        if not (EXT / ref).exists():
            problems.append(f"file referenced in manifest is missing: {ref}")

    if "<all_urls>" in manifest.get("host_permissions", []):
        problems.append("<all_urls> host permission almost always triggers a manual review")

    # Απαγορευμένος remote code
    for js in EXT.rglob("*.js"):
        text = js.read_text(encoding="utf-8", errors="replace")
        rel = js.relative_to(EXT)
        if re.search(r"\bnew\s+Function\s*\(", text) or re.search(r"(?<![\w.])eval\s*\(", text):
            problems.append(f"{rel}: eval/new Function is banned under MV3")
        for m in re.finditer(r"""["'](https?://[^"']+\.js)["']""", text):
            problems.append(f"{rel}: loads remote script {m.group(1)} — not allowed")

    return problems


def build(manifest: dict) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / f"jobhunter-{manifest['version']}.zip"

    files: list[Path] = []
    for path in sorted(EXT.rglob("*")):
        if not path.is_file():
            continue
        if path.name in EXCLUDE_NAMES:
            continue
        if any(p in path.name for p in EXCLUDE_PATTERNS):
            continue
        files.append(path)

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            zf.write(path, path.relative_to(EXT).as_posix())

    return target


def _setup_console() -> None:
    """Windows terminals ξεκινούν σε legacy codepage — τα σύμβολα σκάνε."""
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        except Exception:
            pass
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def main() -> int:
    _setup_console()
    ap = argparse.ArgumentParser()
    ap.add_argument("--bump", metavar="VERSION", help="set a new version before building")
    args = ap.parse_args()

    manifest_path = EXT / "manifest.json"
    manifest = load_manifest()

    if args.bump:
        raw = manifest_path.read_text(encoding="utf-8")
        raw = re.sub(r'("version":\s*")[^"]+(")', rf"\g<1>{args.bump}\g<2>", raw, count=1)
        manifest_path.write_text(raw, encoding="utf-8")
        manifest = load_manifest()
        print(f"version → {manifest['version']}")

    problems = check(manifest)
    for p in problems:
        print(f"  ✗ {p}")
    if problems:
        print(f"\n{len(problems)} problem(s) — fix before uploading.")
        return 1

    target = build(manifest)
    with zipfile.ZipFile(target) as zf:
        count = len(zf.namelist())
        size = target.stat().st_size

    print(f"  ✓ manifest v{manifest['manifest_version']}, version {manifest['version']}")
    print(f"  ✓ description {len(manifest['description'])}/132 chars")
    print(f"  ✓ all icons and referenced files present")
    print(f"  ✓ no remote code")
    print(f"\nPackage: {target.relative_to(ROOT)}  ({count} files, {size/1024:.0f} KB)")
    print("Upload it at https://chrome.google.com/webstore/devconsole")
    return 0


if __name__ == "__main__":
    sys.exit(main())
