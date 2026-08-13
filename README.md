# 🎯 JobHunter

Automatic job hunting. Upload your CV once; from then on it searches twice a
day, ranks what actually fits you, writes the cover letter, fills in the
application form and tracks every application.

Two implementations of the same engine:

| | |
|---|---|
| **[`extension/`](extension/README.md)** | **The product.** A Chrome/Edge extension — no server, no account, no Python. Everything runs and stays in your browser. |
| [`jobhunter/`](jobhunter/README.md) | The Python version for power users. Same engine, plus SMTP email applications and IMAP tracking of company replies — things a browser extension cannot do. Zero dependencies, stdlib only. |
| [`store/`](store/LAUNCH.md) | Chrome Web Store packaging: build script, listing copy, privacy policy, screenshots. |
| `app/` | Early FastAPI + Next.js SaaS scaffold. Superseded by the extension; kept for reference. |

---

## Run the extension

```
chrome://extensions  →  Developer mode  →  Load unpacked  →  select extension/
```

Setup opens automatically. Drop in a CV, confirm your job titles, done.

## Run the Python version

```bash
python -m jobhunter init      # onboarding
python -m jobhunter run       # scan + match
python -m jobhunter serve     # dashboard at 127.0.0.1:8765
```

Needs nothing but Python 3.11+.

## Build the store package

```bash
python store/package.py
```

Produces `store/dist/jobhunter-<version>.zip` and checks the manifest against
the most common rejection reasons.

---

## How the matching works

Every posting is scored 0-100 and the reasons are always visible:

| Signal | Points |
|---|---|
| Job title match | 40 |
| Location | 25 |
| Industry | 10 |
| Language requirement | 10 |
| How fresh the posting is | 10 |
| Salary vs your minimum | 5 |

Minus penalties when the seniority is wrong. Postings outside the regions you
can work in are dropped and it says so. Salary is shown in the currency and
period the employer used, and converted only for comparing against your floor.

## Where the jobs come from

Public, documented APIs only.

**Job boards:** Remotive · Arbeitnow · RemoteOK · Jobicy · Himalayas ·
WorkingNomads · The Muse · We Work Remotely · Landing.jobs · Cryptocurrency Jobs

**Company career pages:** any employer on Greenhouse, Lever, Ashby, Workable,
SmartRecruiters, Recruitee, Workday, Teamtailor or Breezy.

No LinkedIn or Indeed automation — their terms forbid it and it gets accounts
banned.

---

## Working on this from another machine

```bash
git clone git@github.com:GeorgasP/jobhunter.git
cd jobhunter
```

That is all — there is nothing to install for the extension, and the Python
side has no dependencies either.

**Your own data never lives in this repository.** `data/`, `output/`, your CV
and your applications are gitignored. When you clone somewhere new, run
`python -m jobhunter init` (or the extension's onboarding) to create a fresh
local profile there.

## Layout

```
extension/
  manifest.json      permissions, content-script targets
  background.js      service worker: scheduled scans, badge, notifications
  lib/               sources · matcher · cv · letters · fx · suggest · store
  app.html/js/css    dashboard: matches, pipeline, settings
  onboarding.html/js first-run setup
  content/           the form filler injected into application pages

jobhunter/           the same engine in Python, plus SMTP and IMAP
store/               packaging and Chrome Web Store paperwork
cv/build.py          renders an HTML CV to a PDF via headless Chrome
```
