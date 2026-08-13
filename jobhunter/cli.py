"""
CLI: python -m jobhunter <command>

Το UI είναι αγγλικά — η εφαρμογή απευθύνεται σε χρήστες παντού. Τα σχόλια
του κώδικα μένουν ελληνικά.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

from . import apply as apply_mod
from . import companies, db, inbox, letters, matcher, pipeline
from .config import PROFILE_PATH, SETTINGS_PATH, Settings, ensure_dirs, load_settings
from .profile import DEFAULT_BOARDS, Profile, build_profile, load_profile

BANNER = "🎯 JobHunter"


def _ctx() -> tuple[Profile, Settings]:
    return load_profile(), load_settings()


def _user_id(conn, profile: Profile) -> int:
    return db.get_or_create_user(conn, profile.email or "local@jobhunter", profile.name)


def _csv(value: str) -> list[str]:
    return [p.strip() for p in value.split(",") if p.strip()]


# ════════════════════════════════════════════════════════════════
# init — onboarding wizard
# ════════════════════════════════════════════════════════════════
def _ask(prompt: str, default: str = "", example: str = "") -> str:
    hint = f" [{default}]" if default else (f"  (e.g. {example})" if example else "")
    try:
        answer = input(f"  {prompt}{hint}: ").strip()
    except EOFError:
        answer = ""
    return answer or default


def _wizard(args) -> Profile:
    print(textwrap.dedent(f"""
        {BANNER} — setup

        Answer a few questions and JobHunter will search worldwide on your behalf.
        Press Enter to accept the default shown in brackets. You can change
        everything later in data/profile.json or from the dashboard.
    """))

    name = args.name or _ask("Your full name")
    email = args.email or _ask("Your email")

    print("\n  What are you looking for?")
    titles = _csv(_ask("Job titles, comma separated", example="Data Analyst, BI Analyst"))
    while not titles:
        titles = _csv(_ask("At least one job title is required", example="Nurse, Care Assistant"))

    print("\n  Where can you work? Use countries, cities or regions.")
    print("  Write 'Remote' for remote roles open to your region, or 'Worldwide'.")
    locations = _csv(_ask("Locations, comma separated", default="Remote",
                          example="Remote, Berlin, Germany, EU"))
    remote_only = _ask("Remote only? (y/N)", default="n").lower().startswith("y")
    strict = _ask("Hide jobs outside those locations? (Y/n)", default="y").lower().startswith("y")
    blocked = _csv(_ask("Regions you can NOT work in (optional)", example="USA, Canada"))

    print("\n  Filters")
    salary_raw = _ask("Minimum yearly salary, numbers only (optional)", example="45000")
    salary_min = int("".join(c for c in salary_raw if c.isdigit()) or 0) or None
    level = _ask("Experience level: entry / mid / senior", default="mid").lower()
    level = level if level in ("entry", "mid", "senior") else "mid"
    exclude = _csv(_ask("Keywords that disqualify a job (optional)", example="unpaid, internship"))

    print(f"\n  Industries — pick any of: {', '.join(companies.ALL_INDUSTRIES)}")
    print("  This decides which company career pages get tracked. Leave empty for a broad mix.")
    industries = _csv(_ask("Industries, comma separated", example="health, education"))

    print("\n  Languages")
    lang = _ask("Language for your cover letters (en, el, es, de, fr, it, pt)", default="en").lower()
    languages = _csv(_ask("Languages you speak, comma separated", default=lang))

    profile = build_profile(
        name=name, email=email, titles=titles, locations=locations or ["Remote"],
        blocked_locations=blocked, industries=industries, salary_min=salary_min,
        experience_level=level, languages=languages, remote_only=remote_only,
        strict_location=strict, exclude_keywords=exclude, default_language=lang,
        boards=list(DEFAULT_BOARDS),
    )

    print("\n  Extras used to pre-fill application forms (optional)")
    profile.phone = _ask("Phone")
    profile.location = _ask("Where you live", example="Lisbon, Portugal")
    profile.linkedin = _ask("LinkedIn URL")
    profile.work_authorization = _ask("Work authorization", example="EU citizen, no sponsorship needed")
    profile.notice_period = _ask("Notice period", default="Immediately available")

    if profile.cv:
        print(f"\n  Found CV files: {', '.join(f'{k}: {v}' for k, v in profile.cv.items())}")
    cv_answer = _ask("Path to your CV (.md/.txt/.pdf), empty to keep the above")
    if cv_answer:
        profile.cv[lang] = cv_answer

    return profile


def cmd_init(args) -> int:
    ensure_dirs()
    db.init_db()

    if PROFILE_PATH.exists() and not args.force:
        print(f"A profile already exists: {PROFILE_PATH}\nUse --force to start over.")
    else:
        profile = _wizard(args) if not args.quiet else build_profile(
            name=args.name, email=args.email, locations=["Remote"], strict_location=False)
        profile.save()
        print(f"\n✓ Profile saved:  {PROFILE_PATH}")
        print(f"  {len(profile.targets)} companies + {len(profile.boards)} job boards tracked")
        missing = companies.uncovered(profile.preferences.industries)
        if missing:
            print(f"  No companies bundled for: {', '.join(missing)} — the job boards cover "
                  f"those, and you can add employers under \"targets\" any time.")

    if not SETTINGS_PATH.exists():
        Settings().save()
        print(f"✓ Settings saved: {SETTINGS_PATH}")

    print(textwrap.dedent(f"""
        Next steps:
          python -m jobhunter run --apply 5     scan, match and prepare 5 applications
          python -m jobhunter serve             dashboard at http://127.0.0.1:8765
          python -m jobhunter doctor            check that every source works

        Optional, in {SETTINGS_PATH.name}:
          anthropic_api_key   AI-written cover letters instead of templates
          smtp_*              send email applications automatically
          imap_*              auto-track replies from companies
    """).strip())
    return 0


# ════════════════════════════════════════════════════════════════
def cmd_run(args) -> int:
    profile, settings = _ctx()
    db.init_db()
    with db.connect() as conn:
        uid = _user_id(conn, profile)
        report = pipeline.run(
            conn, uid, profile, settings,
            apply_limit=args.apply,
            method=args.method,
            open_browser=not args.no_browser,
        )

    print(f"\n{'─' * 60}")
    print(f"New jobs: {report.jobs_new} · New matches: {report.matches_new} · "
          f"Applications: {report.applied_ok}")
    if report.errors:
        print(f"\n⚠ {len(report.errors)} sources failed:")
        for e in report.errors[:8]:
            print(f"   • {e}")
    if not args.apply:
        print("\nSee your matches:  python -m jobhunter matches")
    return 0


def cmd_matches(args) -> int:
    profile, settings = _ctx()
    with db.connect() as conn:
        uid = _user_id(conn, profile)
        rows = db.pending_matches(conn, uid, args.min_score or settings.min_score, args.limit)

    if not rows:
        print("No pending matches. Run:  python -m jobhunter run")
        return 0

    for r in rows:
        reasons = json.loads(r["reasons"] or "{}")
        print(f"\n[{r['id']:>4}] {r['score']:>3}/100  {r['company']} — {r['title']}")
        print(f"       {r['location'] or 'n/a'} · {matcher.explain(reasons)}")
        print(f"       {r['url']}")
    print(f"\n{len(rows)} matches. Apply:  python -m jobhunter apply --top 5")
    return 0


def cmd_rescore(args) -> int:
    profile, settings = _ctx()
    with db.connect() as conn:
        uid = _user_id(conn, profile)
        pipeline.rescore(conn, uid, profile, settings)
    return 0


def cmd_apply(args) -> int:
    profile, settings = _ctx()
    with db.connect() as conn:
        uid = _user_id(conn, profile)

        if args.match_ids:
            rows = []
            for mid in args.match_ids:
                row = conn.execute(
                    """SELECT m.*, j.company, j.title, j.location, j.url, j.description,
                              j.remote, j.apply_email, j.source, j.posted_at
                       FROM matches m JOIN jobs j ON j.id = m.job_id
                       WHERE m.id = ? AND m.user_id = ?""",
                    (mid, uid),
                ).fetchone()
                if row is None:
                    print(f"✗ match {mid} not found")
                else:
                    rows.append(row)
            results = [
                apply_mod.apply_to_match(conn, uid, r, profile, settings,
                                         method=args.method,
                                         open_browser=not args.no_browser)
                for r in rows
            ]
            for row, res in zip(rows, results):
                icon = "✓" if res.get("ok") else "✗"
                extra = res.get("sent_to") or res.get("error") or res.get("pack_dir", "")
                print(f"{icon} {row['company']} — {row['title']}  ({extra})")
        else:
            results = pipeline.auto_apply(conn, uid, profile, settings, args.top,
                                          method=args.method,
                                          open_browser=not args.no_browser)

    ok = sum(1 for r in results if r.get("ok"))
    print(f"\n{ok}/{len(results)} applications prepared. History: python -m jobhunter history")
    return 0


def cmd_history(args) -> int:
    profile, _ = _ctx()
    with db.connect() as conn:
        uid = _user_id(conn, profile)
        rows = db.list_applications(conn, uid, args.status)
        if not rows:
            print("No applications yet.")
            return 0
        icons = {db.APP_PREPARED: "○", db.APP_SENT: "→", db.APP_INTERVIEW: "📞",
                 db.APP_OFFER: "🎉", db.APP_REJECTED: "✗", db.APP_GHOSTED: "…"}
        for r in rows:
            print(f"[{r['id']:>4}] {icons.get(r['status'], '•')} {r['status']:<10} "
                  f"{r['prepared_at'][:10]}  {r['company']} — {r['title']}")
            if args.verbose:
                for e in db.application_events(conn, r["id"]):
                    print(f"         {e['at'][:16]}  {e['kind']}  {e['detail'] or ''}")
    return 0


def cmd_status(args) -> int:
    profile, settings = _ctx()
    with db.connect() as conn:
        uid = _user_id(conn, profile)
        s = db.stats(conn, uid)

    print(f"{BANNER} — {profile.name or profile.email}")
    print(f"  Jobs in database:   {s['jobs_tracked']}")
    print(f"  Pending matches:    {s['matches_pending']}")
    print(f"  Applications:       {s['applications_total']}")
    for status, n in sorted(s["by_status"].items()):
        print(f"     {status:<12} {n}")
    print(f"  Last run:           {s['last_run'] or '—'}")
    print(f"\n  AI cover letters:   {'on' if settings.has_ai else 'off (template mode)'}")
    print(f"  Email applications: {'on' if settings.has_smtp else 'off'}")
    print(f"  Inbox tracking:     {'on' if settings.has_imap else 'off'}")
    return 0


def cmd_mark(args) -> int:
    profile, _ = _ctx()
    valid = {db.APP_PREPARED, db.APP_SENT, db.APP_INTERVIEW, db.APP_REJECTED,
             db.APP_OFFER, db.APP_GHOSTED}
    if args.status not in valid:
        print(f"Unknown status. Options: {', '.join(sorted(valid))}")
        return 1
    with db.connect() as conn:
        _user_id(conn, profile)
        app = db.get_application(conn, args.application_id)
        if not app:
            print(f"Application {args.application_id} not found.")
            return 1
        db.set_application_status(conn, args.application_id, args.status, args.note)
        print(f"✓ {app['company']} — {app['title']} → {args.status}")
    return 0


def cmd_inbox(args) -> int:
    profile, settings = _ctx()
    with db.connect() as conn:
        uid = _user_id(conn, profile)
        updates = inbox.check(conn, uid, settings, days=args.days)
    print(f"\n{len(updates)} applications changed status." if updates else "\nNo changes.")
    return 0


def cmd_letter(args) -> int:
    profile, settings = _ctx()
    with db.connect() as conn:
        uid = _user_id(conn, profile)
        row = conn.execute(
            """SELECT m.id, j.company, j.title, j.location, j.description, j.url
               FROM matches m JOIN jobs j ON j.id = m.job_id
               WHERE m.id = ? AND m.user_id = ?""",
            (args.match_id, uid),
        ).fetchone()
        if not row:
            print(f"Match {args.match_id} not found.")
            return 1
        content, model = letters.generate(dict(row), profile, settings, args.language)
        db.save_cover_letter(conn, uid, args.match_id, args.language or profile.default_language,
                             content, model)
    print(f"─── {row['company']} — {row['title']}  [{model}] ───\n")
    print(content)
    return 0


def cmd_open(args) -> int:
    profile, _ = _ctx()
    with db.connect() as conn:
        _user_id(conn, profile)
        app = db.get_application(conn, args.application_id)
    if not app:
        print(f"Application {args.application_id} not found.")
        return 1
    if not app["pack_dir"]:
        print("This application has no prepared folder.")
        return 1
    path = Path(app["pack_dir"])
    if sys.platform == "win32":
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)
    print(f"✓ {path}")
    return 0


def cmd_companies(args) -> int:
    """Δείχνει τη βιβλιοθήκη εταιρειών ώστε να διαλέξει ο χρήστης."""
    industries = _csv(args.industry) if args.industry else []
    picks = companies.pick(industries, limit=args.limit)
    print(f"Industries available: {', '.join(companies.ALL_INDUSTRIES)}\n")
    for c in picks:
        print(f"  {c['name']:<18} {c['provider']:<16} {c['slug']}")
    print(f"\n{len(picks)} companies. Add them to \"targets\" in {PROFILE_PATH.name}, "
          f"then run:  python -m jobhunter doctor")
    return 0


def cmd_doctor(args) -> int:
    """Ελέγχει ότι κάθε target/board απαντάει ακόμα — τα ATS αλλάζουν συχνά."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from . import sources

    profile, settings = _ctx()
    print(f"{BANNER} doctor\n")
    print(f"  profile:  {PROFILE_PATH}")
    print(f"  CV ({profile.default_language}): {profile.cv_path() or '⚠ not found'}")
    print(f"  AI:       {'on' if settings.has_ai else 'off (template cover letters)'}")
    print(f"  SMTP:     {'on' if settings.has_smtp else 'off (assisted apply only)'}")
    print(f"  IMAP:     {'on' if settings.has_imap else 'off (manual tracking)'}\n")

    broken: list[str] = []

    def check_target(t: dict) -> tuple[str, int, str]:
        fetcher = sources.ATS_PROVIDERS.get(t.get("provider", ""))
        if not fetcher:
            return f"{t.get('name')} ({t.get('provider')})", -1, "unknown provider"
        try:
            return f"{t['name']} ({t['provider']}:{t['slug']})", len(fetcher(t["slug"], t["name"])), ""
        except Exception as e:
            return f"{t['name']} ({t['provider']}:{t['slug']})", -1, f"{type(e).__name__}: {e}"

    def check_board(name: str) -> tuple[str, int, str]:
        fetcher = sources.AGGREGATORS.get(name)
        if not fetcher:
            return name, -1, "unknown board"
        try:
            return name, len(fetcher(profile.board_query)), ""
        except Exception as e:
            return name, -1, f"{type(e).__name__}: {e}"

    with ThreadPoolExecutor(max_workers=10) as pool:
        futs = [pool.submit(check_target, t) for t in profile.targets]
        futs += [pool.submit(check_board, b) for b in profile.boards]
        for fut in as_completed(futs):
            label, count, err = fut.result()
            if count > 0:
                print(f"  ✓ {label:<42} {count:>4} jobs")
            else:
                print(f"  ✗ {label:<42} {err or 'empty board'}")
                broken.append(label)

    if broken:
        print(f"\n⚠ {len(broken)} sources are not responding. Open the company's careers "
              f"page — the application URL tells you the ATS and the slug — then fix the "
              f"entry under \"targets\" in profile.json.")
    else:
        print("\nAll sources responding.")
    return 0


def cmd_serve(args) -> int:
    from .server import serve
    profile, settings = _ctx()
    serve(profile, settings, port=args.port or settings.server_port, open_browser=not args.no_browser)
    return 0


# ════════════════════════════════════════════════════════════════
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="jobhunter",
                                description="Find jobs worldwide, apply, and track every application")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("init", help="set up your profile (interactive)")
    s.add_argument("--email", default="")
    s.add_argument("--name", default="")
    s.add_argument("--quiet", action="store_true", help="skip the wizard, use neutral defaults")
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("run", help="scan sources + score matches (+ apply)")
    s.add_argument("--apply", type=int, default=0, metavar="N", help="apply to the top N matches")
    s.add_argument("--method", default="auto", choices=["auto", "assisted", "email", "manual"])
    s.add_argument("--no-browser", action="store_true")
    s.set_defaults(func=cmd_run)

    s = sub.add_parser("matches", help="pending matches")
    s.add_argument("--limit", type=int, default=20)
    s.add_argument("--min-score", type=int, default=0)
    s.set_defaults(func=cmd_matches)

    s = sub.add_parser("rescore", help="re-score stored jobs after changing your profile")
    s.set_defaults(func=cmd_rescore)

    s = sub.add_parser("apply", help="apply to matches")
    s.add_argument("match_ids", nargs="*", type=int)
    s.add_argument("--top", type=int, default=5)
    s.add_argument("--method", default="auto", choices=["auto", "assisted", "email", "manual"])
    s.add_argument("--no-browser", action="store_true")
    s.set_defaults(func=cmd_apply)

    s = sub.add_parser("history", help="application history")
    s.add_argument("--status", default=None)
    s.add_argument("-v", "--verbose", action="store_true", help="include the event timeline")
    s.set_defaults(func=cmd_history)

    s = sub.add_parser("status", help="summary")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("mark", help="change an application's status")
    s.add_argument("application_id", type=int)
    s.add_argument("status")
    s.add_argument("--note", default=None)
    s.set_defaults(func=cmd_mark)

    s = sub.add_parser("inbox", help="read company replies from your mailbox")
    s.add_argument("--days", type=int, default=30)
    s.set_defaults(func=cmd_inbox)

    s = sub.add_parser("letter", help="write a cover letter for one match")
    s.add_argument("match_id", type=int)
    s.add_argument("--language", default=None)
    s.set_defaults(func=cmd_letter)

    s = sub.add_parser("open", help="open an application's folder")
    s.add_argument("application_id", type=int)
    s.set_defaults(func=cmd_open)

    s = sub.add_parser("companies", help="browse the built-in company library")
    s.add_argument("--industry", default="", help="comma separated")
    s.add_argument("--limit", type=int, default=40)
    s.set_defaults(func=cmd_companies)

    s = sub.add_parser("doctor", help="check that every source and setting works")
    s.set_defaults(func=cmd_doctor)

    s = sub.add_parser("serve", help="local web dashboard")
    s.add_argument("--port", type=int, default=0)
    s.add_argument("--no-browser", action="store_true")
    s.set_defaults(func=cmd_serve)

    return p


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


def main(argv: list[str] | None = None) -> int:
    _setup_console()
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
