# 🎯 JobHunter

Finds jobs that match you anywhere in the world, writes the cover letters,
prepares or sends the applications, and keeps the full history. The only thing
left for you is replying to the companies that want to talk.

**You choose everything** — job titles, countries, salary floor, industries,
seniority, language. No market, region or industry is baked in.

**Zero dependencies.** Plain Python 3.11+. No `pip install`, no database
server, no cloud account, no API key required.

---

## Quick start

```bash
python -m jobhunter init          # onboarding wizard
python -m jobhunter run --apply 5 # scan, match, prepare 5 applications
python -m jobhunter serve         # dashboard at http://127.0.0.1:8765
```

On Windows you can just double-click `JobHunter.bat`.

---

## How it works

```
   ┌──────────────┐   26 sources     ┌───────────┐   your filters ┌──────────┐
   │  job boards  │ ───────────────► │  scoring  │ ─────────────► │ matches  │
   │  + ATS APIs  │  ~2,000 postings │   0-100   │                │  ranked  │
   └──────────────┘                  └───────────┘                └────┬─────┘
                                                                        │
   ┌──────────────┐   IMAP           ┌───────────┐   apply pack   ┌────▼─────┐
   │  your inbox  │ ───────────────► │  history  │ ◄───────────── │  apply   │
   │              │  auto status     │ + timeline│  + cover letter│          │
   └──────────────┘                  └───────────┘                └──────────┘
```

1. **Scan** — pulls postings from public APIs: six ATS providers (Greenhouse,
   Lever, Ashby, Workable, SmartRecruiters, Recruitee) for any company you
   target, plus six worldwide job boards (Remotive, Arbeitnow, RemoteOK,
   Jobicy, Himalayas, WorkingNomads).
2. **Match** — every posting is scored 0-100: title (40), location (25),
   industry (10), language (10), freshness (10), salary (5), minus seniority
   penalties. Postings outside the regions you can work in are dropped, and the
   reason is always visible.
3. **Apply** — generates a cover letter (Claude if you add a key, template
   otherwise) and then:
   - **email** — fully automatic. If the posting lists an application address
     and you configured SMTP, it sends the letter with your CV attached.
   - **assisted** — builds a folder with the cover letter, your CV and
     ready-to-paste form answers, then opens the posting. Combined with the
     autofill below, about fifteen seconds per application.
4. **Track** — every application gets a timeline. With IMAP configured, replies
   from companies are read and the status flips to interview / rejected / offer
   on its own.

---

## Form autofill

Public ATS APIs are read-only — Greenhouse and Lever both require an API key
that only the *employer* can issue — so no tool can legitimately POST an
application for you. What works instead is filling the form inside your own
browser, on your own session, and leaving Submit to you.

Open `http://127.0.0.1:8765/connect` and pick one:

**Browser extension** (`jobhunter/extension/`, works everywhere)
1. `chrome://extensions` → enable Developer mode → **Load unpacked**
2. Select the `jobhunter/extension` folder
3. Click the JobHunter icon, paste the pairing key from `/connect`, Save

A “Fill with JobHunter” button then appears on Greenhouse, Lever, Ashby,
Workable, SmartRecruiters, Recruitee, Teamtailor, BambooHR and Workday pages.

**Bookmarklet** (nothing to install) — drag the button from `/connect` to your
bookmarks bar. Greenhouse and Ashby set a `connect-src` policy that blocks page
scripts from reaching your computer, so use the extension for those; Workable,
SmartRecruiters, Lever and most company career pages work fine.

Either way it fills name, email, phone, location, LinkedIn, salary
expectation, notice period and the cover letter, and **attaches your CV as a
real file**. Dropdowns and radio buttons for legal questions (work
authorization, relocation) are deliberately left alone and reported back to
you — a wrong answer there is expensive. Fields you already typed in are never
overwritten, and Submit is never pressed.

The job is matched from the page URL against your prepared applications, so the
flow is: **Apply in the dashboard → the posting opens → hit the autofill**.

Security: the API is bound to `127.0.0.1` and every request needs the pairing
key stored in `data/settings.json`. Without it, other sites you visit cannot
read your data from the local server.

---

## Commands

| Command | What it does |
|---|---|
| `init` | onboarding wizard → `data/profile.json` |
| `run [--apply N]` | scan + score, optionally apply to the top N |
| `matches [--limit N]` | pending matches with scores and reasons |
| `apply <match_id...>` / `apply --top N` | apply to specific matches |
| `letter <match_id>` | write a cover letter without applying |
| `history [-v]` | application history (`-v` adds the event timeline) |
| `mark <app_id> <status>` | `sent` / `interview` / `rejected` / `offer` / `ghosted` |
| `inbox [--days N]` | read replies from your mailbox and update statuses |
| `rescore` | re-score stored jobs after changing your profile |
| `companies [--industry X]` | browse the built-in company library |
| `doctor` | check every source and setting |
| `serve [--port N]` | the dashboard |
| `open <app_id>` | open an application's folder |

`--method` accepts `auto` (default), `assisted`, `email`, `manual`.

---

## Configuration

Everything is editable from the dashboard's **Settings** page, or directly in
`data/profile.json`:

```jsonc
{
  "name": "...", "email": "...", "location": "Lisbon, Portugal",
  "work_authorization": "EU citizen", "notice_period": "1 month",
  "cv": { "en": "cv.md" },                    // .md, .txt or .pdf
  "preferences": {
    "titles": ["Data Analyst", "BI Analyst"], // strongest signal
    "must_have": [],                          // must appear in the posting
    "exclude_keywords": ["unpaid"],
    "locations": ["Remote", "Lisbon", "EU"],  // countries, cities, regions
    "blocked_locations": ["USA"],             // where you cannot work
    "strict_location": true,                  // hide anything outside the above
    "remote_only": false,
    "salary_min": 45000,
    "languages": ["en", "pt"],
    "industries": ["tech", "fintech"],
    "experience_level": "mid",                // entry | mid | senior
    "max_age_days": 45
  },
  "targets": [{ "provider": "greenhouse", "slug": "datadog", "name": "Datadog" }],
  "boards": ["remotive", "arbeitnow", "remoteok", "jobicy", "himalayas", "workingnomads"]
}
```

Locations understand shorthands: `EU`, `EMEA`, `APAC`, `LATAM`, `US`, `UK`,
`ANZ`, `UAE`, plus any country or city name. `Worldwide` postings are never
filtered out by geography.

To track a new company, open its careers page — the application URL reveals the
ATS (`boards.greenhouse.io/acme` → provider `greenhouse`, slug `acme`) — add it
under `targets`, then run `doctor`.

### `data/settings.json` — all optional

```jsonc
{
  "anthropic_api_key": "sk-ant-...",   // AI cover letters instead of templates
  "smtp_host": "smtp.gmail.com", "smtp_port": 587,
  "smtp_user": "you@gmail.com", "smtp_password": "<app password>",
  "imap_host": "imap.gmail.com", "imap_user": "you@gmail.com",
  "imap_password": "<app password>",   // auto-tracking of replies
  "min_score": 45, "daily_limit": 25
}
```

Gmail requires an **app password** (https://myaccount.google.com/apppasswords),
not your account password. Secrets stay on your machine; nothing is uploaded.

---

## Running it daily

Windows:

```powershell
schtasks /create /tn "JobHunter" /tr "python -m jobhunter run --apply 5 --no-browser" /sc daily /st 08:00 /f
```

macOS / Linux (`crontab -e`):

```bash
0 8 * * * cd /path/to/JobHunt && python -m jobhunter run --apply 5 --no-browser
0 */4 * * * cd /path/to/JobHunt && python -m jobhunter inbox
```

---

## What it does not do, and why

**No LinkedIn or Indeed account automation.** Driving those accounts violates
their terms of service and gets accounts banned. Everything here uses public,
free, documented endpoints.

**No auto-submitting web forms.** ATS forms have anti-bot protection and
per-role custom questions; automated submission produces either broken
applications or a blocked account. Assisted mode keeps each application at
about a minute without that risk.

**Email applications are fully automatic** — wherever a posting asks for an
application by mail, it goes out on its own with your CV and cover letter.

---

## Layout

```
jobhunter/
  config.py     paths + settings (env → data/settings.json)
  db.py         SQLite: jobs, matches, applications, events, runs
  profile.py    your profile, preferences, CV loading
  companies.py  built-in company library by industry and region
  sources.py    6 ATS providers + 6 worldwide job boards
  matcher.py    0-100 scoring, geography rules
  letters.py    Claude API (plain urllib) + template fallback
  apply.py      apply packs, email delivery, logging
  inbox.py      IMAP → automatic status updates
  pipeline.py   scan → match → apply
  server.py     local dashboard (http.server)
  cli.py        command line

data/           profile.json, settings.json, jobhunter.db   ← local and private
output/applications/NNNN-company-role/   cover_letter.txt, CV, form_answers.md
```
