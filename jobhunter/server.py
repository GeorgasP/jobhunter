"""
Local dashboard — http://127.0.0.1:8765

Σκέτο http.server, κανένα framework. Δένεται ΜΟΝΟ στο 127.0.0.1: τίποτα δεν
εκτίθεται στο δίκτυο. Το UI είναι αγγλικά (worldwide χρήστες)· τα σχόλια
ελληνικά.
"""
from __future__ import annotations

import base64
import html
import json
import mimetypes
import re
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import apply as apply_mod
from . import companies, db, letters, matcher, pipeline, sources
from .config import Settings
from .profile import Preferences, Profile

STATIC_DIR = Path(__file__).resolve().parent / "static"

_state: dict = {"profile": None, "settings": None, "scan": "idle", "flash": ""}
_scan_lock = threading.Lock()

STATUS_LABEL = {
    db.APP_PREPARED: ("Prepared", "prep"),
    db.APP_SENT: ("Sent", "sent"),
    db.APP_INTERVIEW: ("Interview", "int"),
    db.APP_OFFER: ("Offer", "offer"),
    db.APP_REJECTED: ("Rejected", "rej"),
    db.APP_GHOSTED: ("No reply", "ghost"),
}

CSS = """
:root{--bg:#0d1117;--panel:#161b22;--line:#26303d;--fg:#e6edf3;--dim:#8b949e;
      --accent:#2f81f7;--ok:#3fb950;--warn:#d29922;--bad:#f85149;--radius:10px}
@media (prefers-color-scheme:light){:root{--bg:#f6f8fa;--panel:#fff;--line:#d7dee6;
      --fg:#1f2328;--dim:#636c76}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
header{position:sticky;top:0;background:var(--panel);border-bottom:1px solid var(--line);
       padding:14px 22px;display:flex;gap:22px;align-items:center;flex-wrap:wrap;z-index:5}
header h1{font-size:17px;margin:0;letter-spacing:-.2px}
nav{display:flex;gap:18px}
nav a{color:var(--dim);font-weight:500;padding:6px 0}
nav a.on{color:var(--fg);border-bottom:2px solid var(--accent)}
main{max-width:1000px;margin:0 auto;padding:24px 22px 80px}
.stats{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:22px}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
      padding:12px 16px;min-width:110px}
.stat b{display:block;font-size:22px;line-height:1.2}
.stat span{color:var(--dim);font-size:12px;text-transform:uppercase;letter-spacing:.4px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
      padding:16px 18px;margin-bottom:12px;display:flex;gap:16px;align-items:flex-start}
.score{flex:none;width:52px;height:52px;border-radius:50%;display:grid;place-items:center;
       font-weight:700;font-size:16px;border:2px solid var(--line)}
.s-hi{border-color:var(--ok);color:var(--ok)}.s-mid{border-color:var(--warn);color:var(--warn)}
.s-lo{border-color:var(--line);color:var(--dim)}
.card h3{margin:0 0 4px;font-size:15.5px}
.meta{color:var(--dim);font-size:13px;margin-bottom:8px}
.why{font-size:13px;color:var(--dim);background:rgba(127,127,127,.08);
     padding:6px 10px;border-radius:6px;display:inline-block;margin-bottom:10px}
.actions{display:flex;gap:8px;flex-wrap:wrap}
button,.btn{font:inherit;font-size:13px;padding:7px 13px;border-radius:7px;cursor:pointer;
     border:1px solid var(--line);background:transparent;color:var(--fg)}
button:hover,.btn:hover{border-color:var(--accent);text-decoration:none}
button.primary{background:var(--accent);border-color:var(--accent);color:#fff}
button[disabled]{opacity:.45;cursor:default}
form.inline{display:inline}
table{width:100%;border-collapse:collapse;background:var(--panel);
      border:1px solid var(--line);border-radius:var(--radius);overflow:hidden}
th,td{text-align:left;padding:11px 14px;border-bottom:1px solid var(--line);font-size:14px}
th{color:var(--dim);font-size:12px;text-transform:uppercase;letter-spacing:.4px}
tr:last-child td{border-bottom:none}
.pill{font-size:12px;padding:3px 9px;border-radius:20px;border:1px solid var(--line);white-space:nowrap}
.pill.sent{color:var(--accent);border-color:var(--accent)}
.pill.int{color:var(--warn);border-color:var(--warn)}
.pill.offer{color:var(--ok);border-color:var(--ok)}
.pill.rej{color:var(--bad);border-color:var(--bad)}
.flash{background:var(--panel);border:1px solid var(--accent);border-radius:var(--radius);
       padding:12px 16px;margin-bottom:18px;font-size:14px}
pre.letter{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
       padding:16px;white-space:pre-wrap;font:14px/1.6 ui-monospace,Consolas,monospace}
.empty{color:var(--dim);text-align:center;padding:60px 0}
.timeline{list-style:none;padding:0;margin:0}
.timeline li{padding:8px 0;border-bottom:1px solid var(--line);font-size:13.5px}
.timeline span{color:var(--dim);margin-right:10px;font-variant-numeric:tabular-nums}
fieldset{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
         padding:18px;margin:0 0 16px}
legend{padding:0 8px;color:var(--dim);font-size:12px;text-transform:uppercase;letter-spacing:.5px}
label.row{display:block;margin-bottom:14px}
label.row span{display:block;font-size:13px;color:var(--dim);margin-bottom:5px}
input[type=text],input[type=number],select,textarea{width:100%;padding:9px 11px;font:inherit;
       font-size:14px;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:7px}
textarea{min-height:110px;font-family:ui-monospace,Consolas,monospace;font-size:13px}
.checks{display:flex;flex-wrap:wrap;gap:10px 18px}
.checks label{font-size:14px;display:flex;align-items:center;gap:6px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:0 18px}
@media(max-width:640px){.grid2{grid-template-columns:1fr}}
.hint{color:var(--dim);font-size:12.5px;margin:-8px 0 14px}
"""


def _e(text) -> str:
    return html.escape(str(text if text is not None else ""))


def _page(title: str, active: str, body: str) -> bytes:
    flash = _state.get("flash") or ""
    _state["flash"] = ""
    nav = "".join(
        f'<a href="{href}" class="{"on" if key == active else ""}">{label}</a>'
        for key, href, label in (("matches", "/", "Matches"),
                                 ("apps", "/applications", "Applications"),
                                 ("autofill", "/connect", "Autofill"),
                                 ("settings", "/settings", "Settings"))
    )
    scanning = _state["scan"] == "running"
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_e(title)} · JobHunter</title><style>{CSS}</style></head><body>
<header>
  <h1>🎯 JobHunter</h1>
  <nav>{nav}</nav>
  <form method="post" action="/scan" style="margin-left:auto">
    <button class="primary" {"disabled" if scanning else ""}>{"Scanning…" if scanning else "Scan now"}</button>
  </form>
  <form method="post" action="/inbox"><button>Check inbox</button></form>
</header>
<main>{f'<div class="flash">{flash}</div>' if flash else ''}{body}</main>
</body></html>""".encode("utf-8")


def _score_class(score: int) -> str:
    return "s-hi" if score >= 70 else "s-mid" if score >= 50 else "s-lo"


def _uid(conn) -> int:
    profile: Profile = _state["profile"]
    return db.get_or_create_user(conn, profile.email or "local@jobhunter", profile.name)


# ════════════════════════════════════════════════════════════════
# Views
# ════════════════════════════════════════════════════════════════
def view_matches() -> bytes:
    settings: Settings = _state["settings"]
    with db.connect() as conn:
        uid = _uid(conn)
        rows = db.pending_matches(conn, uid, settings.min_score, 60)
        s = db.stats(conn, uid)

    stats_html = "".join(
        f'<div class="stat"><b>{v}</b><span>{k}</span></div>'
        for k, v in (("jobs tracked", s["jobs_tracked"]), ("matches", s["matches_pending"]),
                     ("applications", s["applications_total"]),
                     ("interviews", s["by_status"].get(db.APP_INTERVIEW, 0)))
    )

    if not rows:
        cards = ('<div class="empty">No pending matches.<br>Hit “Scan now”, widen your '
                 'filters in <a href="/settings">Settings</a>, or lower the minimum score.</div>')
    else:
        parts = []
        for r in rows:
            why = matcher.explain(json.loads(r["reasons"] or "{}"))
            parts.append(f"""<div class="card">
  <div class="score {_score_class(r['score'])}">{r['score']}</div>
  <div style="flex:1;min-width:0">
    <h3><a href="{_e(r['url'])}" target="_blank" rel="noopener">{_e(r['title'])}</a></h3>
    <div class="meta">{_e(r['company'])} · {_e(r['location'] or 'n/a')} · {_e(r['source'])}</div>
    <div class="why">{_e(why)}</div>
    <div class="actions">
      <form class="inline" method="post" action="/apply">
        <input type="hidden" name="match_id" value="{r['id']}">
        <input type="hidden" name="method" value="auto">
        <button class="primary">Apply</button>
      </form>
      <form class="inline" method="post" action="/apply">
        <input type="hidden" name="match_id" value="{r['id']}">
        <input type="hidden" name="method" value="manual">
        <button>Log only</button>
      </form>
      <form class="inline" method="post" action="/ignore">
        <input type="hidden" name="match_id" value="{r['id']}">
        <button>Dismiss</button>
      </form>
      <a class="btn" href="{_e(r['url'])}" target="_blank" rel="noopener">Open posting</a>
    </div>
  </div>
</div>""")
        cards = "".join(parts)

    return _page("Matches", "matches", f'<div class="stats">{stats_html}</div>{cards}')


def view_applications() -> bytes:
    with db.connect() as conn:
        rows = db.list_applications(conn, _uid(conn))

    if not rows:
        return _page("Applications", "apps", '<div class="empty">No applications yet.</div>')

    body = ['<table><tr><th>Date</th><th>Company</th><th>Role</th><th>Method</th>'
            '<th>Status</th><th></th></tr>']
    for r in rows:
        label, cls = STATUS_LABEL.get(r["status"], (r["status"], ""))
        body.append(
            f"<tr><td>{_e(r['prepared_at'][:10])}</td><td>{_e(r['company'])}</td>"
            f"<td><a href=\"/application/{r['id']}\">{_e(r['title'])}</a></td>"
            f"<td>{_e(r['method'])}</td>"
            f'<td><span class="pill {cls}">{_e(label)}</span></td>'
            f'<td><a href="/application/{r["id"]}">details →</a></td></tr>'
        )
    body.append("</table>")
    return _page("Applications", "apps", "".join(body))


def view_application(app_id: int) -> bytes:
    with db.connect() as conn:
        app = db.get_application(conn, app_id)
        if not app:
            return _page("Not found", "apps", '<div class="empty">Not found.</div>')
        events = db.application_events(conn, app_id)
        letter = conn.execute(
            "SELECT * FROM cover_letters WHERE id = ?", (app["cover_letter_id"],)
        ).fetchone() if app["cover_letter_id"] else None

    buttons = "".join(
        f'<form class="inline" method="post" action="/status">'
        f'<input type="hidden" name="app_id" value="{app_id}">'
        f'<input type="hidden" name="status" value="{key}">'
        f'<button {"disabled" if app["status"] == key else ""}>{label}</button></form>'
        for key, (label, _cls) in STATUS_LABEL.items()
    )
    timeline = "".join(
        f'<li><span>{_e(e["at"][:16].replace("T", " "))}</span>{_e(e["kind"])} '
        f'{_e(e["detail"] or "")}</li>' for e in events
    )
    letter_html = (f'<h3>Cover letter <small style="color:var(--dim)">({_e(letter["model"])})</small></h3>'
                   f'<pre class="letter">{_e(letter["content"])}</pre>') if letter else ""
    pack_html = (f'<p>Application folder: <code>{_e(app["pack_dir"])}</code></p>'
                 if app["pack_dir"] else "")

    body = f"""
<p><a href="/applications">← Applications</a></p>
<h2 style="margin:6px 0">{_e(app['title'])}</h2>
<div class="meta">{_e(app['company'])} · {_e(app['location'] or 'n/a')} ·
  <a href="{_e(app['url'])}" target="_blank" rel="noopener">view posting ↗</a></div>
<div class="actions" style="margin:16px 0">{buttons}</div>
{pack_html}
{letter_html}
<h3>History</h3><ul class="timeline">{timeline}</ul>
"""
    return _page(app["title"], "apps", body)


# ════════════════════════════════════════════════════════════════
# Settings — ο χρήστης ορίζει τα πάντα από εδώ
# ════════════════════════════════════════════════════════════════
def _text_row(label: str, name: str, value, hint: str = "", kind: str = "text") -> str:
    return (f'<label class="row"><span>{_e(label)}</span>'
            f'<input type="{kind}" name="{name}" value="{_e(value)}"></label>'
            + (f'<div class="hint">{_e(hint)}</div>' if hint else ""))


def _check(label: str, name: str, checked: bool) -> str:
    return (f'<label><input type="checkbox" name="{name}" value="1" '
            f'{"checked" if checked else ""}> {_e(label)}</label>')


def view_settings() -> bytes:
    profile: Profile = _state["profile"]
    settings: Settings = _state["settings"]
    p = profile.preferences

    industry_checks = "".join(
        _check(i, f"industry__{i}", i in p.industries) for i in companies.ALL_INDUSTRIES
    )
    board_checks = "".join(
        _check(b, f"board__{b}", b in profile.boards) for b in sorted(sources.AGGREGATORS)
    )
    targets_text = "\n".join(f"{t['provider']}:{t['slug']}:{t['name']}" for t in profile.targets)
    levels = "".join(
        f'<option value="{lv}" {"selected" if p.experience_level == lv else ""}>{lv}</option>'
        for lv in ("entry", "mid", "senior")
    )

    body = f"""
<form method="post" action="/settings">
<fieldset><legend>What you are looking for</legend>
  {_text_row("Job titles", "titles", ", ".join(p.titles),
             "Comma separated. This is the strongest matching signal.")}
  {_text_row("Locations", "locations", ", ".join(p.locations),
             "Countries, cities or regions. Use Remote or Worldwide for remote work.")}
  {_text_row("Regions you cannot work in", "blocked_locations", ", ".join(p.blocked_locations),
             "Optional. Postings limited to these are hidden.")}
  <div class="checks" style="margin-bottom:14px">
    {_check("Remote only", "remote_only", p.remote_only)}
    {_check("Hide jobs outside my locations", "strict_location", p.strict_location)}
  </div>
  <div class="grid2">
    {_text_row("Minimum yearly salary", "salary_min", p.salary_min or "", "", "number")}
    <label class="row"><span>Experience level</span><select name="experience_level">{levels}</select></label>
  </div>
  <div class="grid2">
    {_text_row("Must-have keywords", "must_have", ", ".join(p.must_have))}
    {_text_row("Disqualifying keywords", "exclude_keywords", ", ".join(p.exclude_keywords))}
  </div>
  <div class="grid2">
    {_text_row("Max posting age (days)", "max_age_days", p.max_age_days, "", "number")}
    {_text_row("Minimum score to show", "min_score", settings.min_score, "", "number")}
  </div>
</fieldset>

<fieldset><legend>Industries</legend>
  <div class="checks">{industry_checks}</div>
  <div class="hint" style="margin-top:12px">
    {_check("Rebuild my company list from these industries", "rebuild_targets", False)}
  </div>
</fieldset>

<fieldset><legend>Sources</legend>
  <span style="font-size:13px;color:var(--dim)">Job boards</span>
  <div class="checks" style="margin:8px 0 16px">{board_checks}</div>
  <label class="row"><span>Company career pages — one per line: provider:slug:Name</span>
    <textarea name="targets">{_e(targets_text)}</textarea></label>
  <div class="hint">Providers: {", ".join(sorted(sources.ATS_PROVIDERS))}.
    Open a company's careers page — the application URL reveals the provider and slug.
    Run <code>python -m jobhunter doctor</code> to verify.</div>
</fieldset>

<fieldset><legend>You</legend>
  <div class="grid2">
    {_text_row("Full name", "name", profile.name)}
    {_text_row("Email", "email", profile.email)}
    {_text_row("Phone", "phone", profile.phone)}
    {_text_row("Where you live", "location", profile.location)}
    {_text_row("LinkedIn", "linkedin", profile.linkedin)}
    {_text_row("GitHub", "github", profile.github)}
    {_text_row("Work authorization", "work_authorization", profile.work_authorization)}
    {_text_row("Notice period", "notice_period", profile.notice_period)}
  </div>
  <div class="grid2">
    {_text_row("Cover letter language", "default_language", profile.default_language, "en, el, es, de, fr, it, pt")}
    {_text_row("Languages you speak", "languages", ", ".join(p.languages))}
  </div>
  {_text_row("CV file for that language", "cv_path", profile.cv.get(profile.default_language, ""),
             ".md, .txt or .pdf — path relative to the project folder")}
</fieldset>

<button class="primary" style="font-size:15px;padding:10px 22px">Save settings</button>
<span style="color:var(--dim);font-size:13px;margin-left:12px">
  Saved matches are re-scored immediately with the new filters.</span>
</form>
"""
    return _page("Settings", "settings", body)


def action_settings(form: dict) -> str:
    profile: Profile = _state["profile"]
    settings: Settings = _state["settings"]

    def one(key: str, default: str = "") -> str:
        return (form.get(key, [default])[0] or "").strip()

    def csv(key: str) -> list[str]:
        return [x.strip() for x in one(key).split(",") if x.strip()]

    def num(key: str) -> int | None:
        digits = "".join(c for c in one(key) if c.isdigit())
        return int(digits) if digits else None

    p = Preferences(
        titles=csv("titles"),
        must_have=csv("must_have"),
        exclude_keywords=csv("exclude_keywords"),
        locations=csv("locations") or ["Remote"],
        blocked_locations=csv("blocked_locations"),
        strict_location="strict_location" in form,
        remote_only="remote_only" in form,
        salary_min=num("salary_min"),
        languages=csv("languages") or [one("default_language", "en")],
        industries=[i for i in companies.ALL_INDUSTRIES if f"industry__{i}" in form],
        experience_level=one("experience_level", "mid"),
        max_age_days=num("max_age_days") or 45,
    )

    profile.preferences = p
    profile.name = one("name")
    profile.email = one("email")
    profile.phone = one("phone")
    profile.location = one("location")
    profile.linkedin = one("linkedin")
    profile.github = one("github")
    profile.work_authorization = one("work_authorization")
    profile.notice_period = one("notice_period")
    profile.default_language = one("default_language", "en") or "en"
    if one("cv_path"):
        profile.cv[profile.default_language] = one("cv_path")

    profile.boards = [b for b in sources.AGGREGATORS if f"board__{b}" in form]

    if "rebuild_targets" in form:
        profile.targets = companies.pick(p.industries)
    else:
        targets = []
        for line in one("targets").splitlines():
            parts = [x.strip() for x in line.split(":")]
            if len(parts) >= 2 and parts[0] and parts[1]:
                targets.append({"provider": parts[0], "slug": parts[1],
                                "name": parts[2] if len(parts) > 2 and parts[2] else parts[1]})
        profile.targets = targets

    profile.save()

    new_min = num("min_score")
    if new_min is not None and new_min != settings.min_score:
        settings.min_score = new_min
        settings.save()

    with db.connect() as conn:
        kept, dropped = pipeline.rescore(conn, _uid(conn), profile, settings, log=lambda *_: None)

    _state["flash"] = (f"Settings saved. {kept} matches now pass your filters"
                       f"{f', {dropped} dropped' if dropped else ''}.")
    return "/settings"


# ════════════════════════════════════════════════════════════════
# Autofill API — τροφοδοτεί το bookmarklet και το extension
# ════════════════════════════════════════════════════════════════
_ID_RE = re.compile(r"\d{5,}")


def _url_keys(url: str) -> set[str]:
    """Ταυτότητες μέσα σε ένα URL αγγελίας (job id, slug) για αντιστοίχιση."""
    if not url:
        return set()
    parsed = urllib.parse.urlparse(url)
    keys = set(_ID_RE.findall(url))
    tail = [p for p in parsed.path.split("/") if p]
    if tail:
        keys.add(tail[-1].lower())
    return keys


def find_application_for_url(conn, user_id: int, page_url: str):
    """Ποια αίτηση αφορά η σελίδα που βλέπει ο χρήστης."""
    rows = db.list_applications(conn, user_id)
    if not rows:
        return None

    page_keys = _url_keys(page_url)
    if page_keys:
        for r in rows:
            if r["url"] == page_url:
                return r
        for r in rows:
            if page_keys & _url_keys(r["url"]):
                return r

    # Fallback: η τελευταία που ετοιμάστηκε — συνήθως αυτή που μόλις άνοιξες.
    return rows[0]


def prefill_payload(page_url: str) -> dict:
    profile: Profile = _state["profile"]
    settings: Settings = _state["settings"]

    with db.connect() as conn:
        uid = _uid(conn)
        app = find_application_for_url(conn, uid, page_url)
        if not app:
            return {"ok": False, "error": "No application prepared yet. Hit Apply in the dashboard first."}

        letter = None
        if app["cover_letter_id"]:
            row = conn.execute("SELECT content FROM cover_letters WHERE id = ?",
                               (app["cover_letter_id"],)).fetchone()
            letter = row["content"] if row else None
        if not letter:
            letter, _model = letters.generate(dict(app), profile, settings)

    parts = (profile.name or "").split()
    salary = f"{profile.preferences.salary_min:,}" if profile.preferences.salary_min else ""

    payload = {
        "ok": True,
        "application_id": app["id"],
        "job": {"company": app["company"], "title": app["title"], "url": app["url"]},
        "answers": {
            "full_name": profile.name,
            "first_name": parts[0] if parts else "",
            "last_name": " ".join(parts[1:]) if len(parts) > 1 else "",
            "email": profile.email,
            "phone": profile.phone,
            "location": profile.location,
            "linkedin": profile.linkedin,
            "github": profile.github,
            "website": profile.linkedin or profile.github,
            "work_authorization": profile.work_authorization,
            "notice_period": profile.notice_period or "Immediately available",
            "salary_expectation": salary,
            "how_did_you_hear": "Company careers page",
        },
        "cover_letter": letter or "",
    }

    cv_path = profile.cv_path()
    if cv_path and cv_path.exists() and cv_path.stat().st_size < 8_000_000:
        payload["cv"] = {
            "filename": f"CV_{(profile.name or 'candidate').replace(' ', '_')}{cv_path.suffix}",
            "mime": mimetypes.guess_type(cv_path.name)[0] or "application/octet-stream",
            "base64": base64.b64encode(cv_path.read_bytes()).decode("ascii"),
        }
    return payload


def _bookmarklet(token: str, port: int) -> str:
    """Ένα bookmarklet που κατεβάζει τα δεδομένα και τρέχει τον filler inline."""
    filler = (STATIC_DIR / "prefill.js").read_text(encoding="utf-8")
    code = (
        "(function(){"
        f"var B='http://127.0.0.1:{port}';var T='{token}';"
        + filler +
        "fetch(B+'/api/prefill?token='+T+'&url='+encodeURIComponent(location.href))"
        ".then(function(r){return r.json()})"
        ".then(function(d){if(!d.ok){alert('JobHunter: '+d.error);return}window.__jobhunterFill(d)})"
        ".catch(function(e){alert('JobHunter could not reach the dashboard at '+B+"
        "'\\n\\nEither it is not running, or this site blocks localhost requests (Greenhouse, "
        "Ashby). Use the browser extension there.\\n\\n'+e)});"
        "})()"
    )
    return "javascript:" + urllib.parse.quote(code, safe="")


def view_connect() -> bytes:
    settings: Settings = _state["settings"]
    token = settings.ensure_token()
    port = _state.get("port", settings.server_port)
    mark = _bookmarklet(token, port)
    ext_dir = Path(__file__).resolve().parent.parent / "extension"

    body = f"""
<h2 style="margin:0 0 6px">One-click form autofill</h2>
<p style="color:var(--dim);margin-top:0">Open a job application form, trigger JobHunter, and every
text field plus your CV is filled in. It never presses Submit — that stays your call.</p>

<fieldset><legend>Option 1 — The browser extension (recommended)</legend>
  <p style="margin-top:0">A standalone version of JobHunter that needs neither Python nor this
  dashboard: it searches, scores, tracks and autofills entirely inside your browser. It also works
  on Greenhouse and Ashby, which block page scripts from reaching your computer.</p>
  <ol style="line-height:1.9;padding-left:20px">
    <li>Open <code>chrome://extensions</code> (or <code>edge://extensions</code>)</li>
    <li>Turn on <b>Developer mode</b>, click <b>Load unpacked</b></li>
    <li>Select this folder:<br><code>{_e(ext_dir)}</code></li>
  </ol>
  <div class="hint">No pairing key needed — it keeps its own profile, jobs and applications.</div>
</fieldset>

<fieldset><legend>Option 2 — Bookmarklet for this dashboard</legend>
  <p style="margin-top:0">Fills forms from the applications prepared <em>here</em>. Drag the button
  to your bookmarks bar, then click it while you are on an application form.</p>
  <p><a class="btn" style="font-size:15px;padding:10px 18px" href="{_e(mark)}">🎯 Fill with JobHunter</a></p>
  <div class="hint">Works on Workable, SmartRecruiters, Lever and most company career pages.
  On Greenhouse and Ashby it will tell you to use the extension instead.
  It matches the page URL against your prepared applications, so the flow is:
  <b>Apply here → the posting opens → click the bookmarklet</b>.</div>
</fieldset>
"""
    return _page("Autofill", "autofill", body)


# ════════════════════════════════════════════════════════════════
# Actions
# ════════════════════════════════════════════════════════════════
def _run_scan_background() -> None:
    def worker() -> None:
        profile, settings = _state["profile"], _state["settings"]
        try:
            with db.connect() as conn:
                uid = db.get_or_create_user(conn, profile.email or "local@jobhunter", profile.name)
                report = pipeline.run(conn, uid, profile, settings, log=lambda *_: None)
            _state["flash"] = (f"Scan finished: {report.jobs_seen} postings, "
                               f"{report.jobs_new} new, {report.matches_new} new matches.")
        except Exception as e:
            _state["flash"] = f"Scan failed: {html.escape(str(e))}"
        finally:
            _state["scan"] = "idle"

    with _scan_lock:
        if _state["scan"] == "running":
            return
        _state["scan"] = "running"
    threading.Thread(target=worker, daemon=True).start()


def action_apply(form: dict) -> str:
    match_id = int(form.get("match_id", [0])[0])
    method = form.get("method", ["auto"])[0]
    profile, settings = _state["profile"], _state["settings"]

    with db.connect() as conn:
        uid = _uid(conn)
        row = conn.execute(
            """SELECT m.*, j.company, j.title, j.location, j.url, j.description,
                      j.remote, j.apply_email, j.source, j.posted_at
               FROM matches m JOIN jobs j ON j.id = m.job_id
               WHERE m.id = ? AND m.user_id = ?""",
            (match_id, uid),
        ).fetchone()
        if not row:
            _state["flash"] = "Match not found."
            return "/"
        res = apply_mod.apply_to_match(conn, uid, row, profile, settings, method=method)

    if res.get("ok"):
        detail = (f"emailed to {res['sent_to']}" if res.get("sent_to")
                  else f"pack ready at {res.get('pack_dir', '—')}")
        _state["flash"] = f"✓ {_e(row['company'])} — {_e(row['title'])}: {_e(detail)}"
    else:
        _state["flash"] = f"✗ {_e(res.get('error'))}"
    return "/"


def action_ignore(form: dict) -> str:
    with db.connect() as conn:
        db.set_match_status(conn, int(form.get("match_id", [0])[0]), db.MATCH_IGNORED)
    return "/"


def action_status(form: dict) -> str:
    app_id = int(form.get("app_id", [0])[0])
    status = form.get("status", [db.APP_SENT])[0]
    with db.connect() as conn:
        db.set_application_status(conn, app_id, status, "set manually from dashboard")
    return f"/application/{app_id}"


def action_inbox(form: dict) -> str:
    from . import inbox
    profile, settings = _state["profile"], _state["settings"]
    if not settings.has_imap:
        _state["flash"] = ("Inbox tracking needs imap_host / imap_user / imap_password "
                           "in data/settings.json.")
        return "/applications"
    try:
        with db.connect() as conn:
            updates = inbox.check(conn, _uid(conn), settings, log=lambda *_: None)
        _state["flash"] = (f"{len(updates)} applications updated from your inbox."
                           if updates else "No new replies.")
    except Exception as e:
        _state["flash"] = f"Inbox check failed: {_e(e)}"
    return "/applications"


# ════════════════════════════════════════════════════════════════
class Handler(BaseHTTPRequestHandler):
    server_version = "JobHunter"

    def log_message(self, fmt, *args):        # ησυχία στο terminal
        pass

    def _send(self, payload: bytes, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _redirect(self, location: str) -> None:
        self.send_response(303)
        self.send_header("Location", location)
        self.end_headers()

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        # Η φόρμα ζει σε άλλο origin (greenhouse.io κ.λπ.), οπότε CORS ανοιχτό —
        # η προστασία είναι το token, όχι το origin.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self, query: dict) -> bool:
        settings: Settings = _state["settings"]
        given = (query.get("token") or [""])[0]
        return bool(given) and given == settings.ensure_token()

    def do_OPTIONS(self) -> None:                      # CORS preflight
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/api/prefill":
            if not self._authorized(query):
                self._send_json({"ok": False, "error": "invalid or missing token"}, 403)
                return
            try:
                self._send_json(prefill_payload((query.get("url") or [""])[0]))
            except Exception as e:
                self._send_json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)
            return

        if path == "/static/prefill.js":
            body = (STATIC_DIR / "prefill.js").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/":
            self._send(view_matches())
        elif path == "/applications":
            self._send(view_applications())
        elif path == "/connect":
            self._send(view_connect())
        elif path == "/settings":
            self._send(view_settings())
        elif path.startswith("/application/"):
            try:
                app_id = int(path.rsplit("/", 1)[1])
            except ValueError:
                self._send(_page("Not found", "apps", '<div class="empty">404</div>'), 404)
                return
            self._send(view_application(app_id))
        else:
            self._send(_page("Not found", "matches", '<div class="empty">404</div>'), 404)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        form = urllib.parse.parse_qs(self.rfile.read(length).decode("utf-8")) if length else {}
        path = urllib.parse.urlparse(self.path).path

        if path == "/scan":
            _run_scan_background()
            _state["flash"] = "Scan started — refresh in a moment."
            self._redirect("/")
        elif path == "/apply":
            self._redirect(action_apply(form))
        elif path == "/ignore":
            self._redirect(action_ignore(form))
        elif path == "/status":
            self._redirect(action_status(form))
        elif path == "/inbox":
            self._redirect(action_inbox(form))
        elif path == "/settings":
            self._redirect(action_settings(form))
        else:
            self._send(_page("Not found", "matches", '<div class="empty">404</div>'), 404)


def _sync_extension_filler() -> None:
    """Το extension δεν διαβάζει αρχεία εκτός του φακέλου του — κρατάμε αντίγραφο
    του filler συγχρονισμένο ώστε να μη ξεχαστεί ποτέ ενημέρωση."""
    source = STATIC_DIR / "prefill.js"
    target = Path(__file__).resolve().parent.parent / "extension" / "content" / "prefill.js"
    try:
        if not target.exists() or target.read_bytes() != source.read_bytes():
            target.write_bytes(source.read_bytes())
    except OSError:
        pass


def serve(profile: Profile, settings: Settings, port: int = 8765,
          open_browser: bool = True) -> None:
    _state["profile"] = profile
    _state["settings"] = settings
    _state["port"] = port
    db.init_db()
    settings.ensure_token()
    _sync_extension_filler()

    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}"
    print(f"🎯 JobHunter dashboard → {url}   (Ctrl+C to stop)")
    print(f"   Form autofill setup  → {url}/connect")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        httpd.server_close()
