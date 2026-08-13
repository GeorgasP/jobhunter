# 🎯 JobHunter — browser extension

Job hunting that runs by itself. Upload your CV once; from then on it searches
twice a day, ranks what fits you, and fills in the application forms.

**Nothing to install beyond the extension.** No Python, no account, no server.
Your CV, your profile and every application stay in your browser.

---

## Install (2 minutes)

1. Open `chrome://extensions` — or `edge://extensions`, or `brave://extensions`
2. Turn on **Developer mode** (top right)
3. Click **Load unpacked** and select this `extension` folder
4. Setup opens automatically: drop in your CV, confirm your job titles, done

The first search starts immediately and takes about half a minute.

---

## What happens next

```
   ┌────────────┐   twice a day    ┌──────────┐   your filters  ┌──────────┐
   │ job boards │ ───────────────► │  scoring │ ──────────────► │  matches │
   │  + career  │  ~2,000 postings │  0-100   │                 │  ranked  │
   │   pages    │                  └──────────┘                 └────┬─────┘
   └────────────┘                                                     │
                       ┌──────────┐   you press submit   ┌───────────▼──────┐
                       │ pipeline │ ◄─────────────────── │  form filled in  │
                       │ tracking │                      │  + CV attached   │
                       └──────────┘                      └──────────────────┘
```

- **Searches on its own.** Twice a day in the background, with a notification
  when new roles match. The toolbar icon shows how many are waiting.
- **Explains every score.** 0-100 from job title (40), location (25), industry
  (10), language (10), freshness (10) and salary (5). Roles outside the regions
  you can work in are dropped, and it says so.
- **Writes the cover letter.** From a template, or from Claude if you add your
  own Anthropic API key in Settings.
- **Fills the form.** Open a posting and press *Fill with JobHunter*: name,
  email, phone, location, LinkedIn, salary, notice period, the cover letter —
  and your CV attached as a real file.
- **Tracks everything.** A pipeline board from Prepared through Sent, Interview
  and Offer. Drag cards between stages.

It never presses Submit. Dropdowns about work authorization or relocation are
left untouched and flagged — a wrong answer there costs more than the three
seconds it takes you to pick.

---

## Where the jobs come from

Public, documented, free APIs only:

**Job boards** — Remotive, Arbeitnow, RemoteOK, Jobicy, Himalayas, WorkingNomads.

**Company career pages** — any employer on Greenhouse, Lever, Ashby, Workable,
SmartRecruiters or Recruitee. Pick industries in Settings and a matching set is
tracked for you.

No LinkedIn or Indeed automation: their terms forbid it and it gets accounts
banned.

---

## Settings worth knowing

| Setting | What it does |
|---|---|
| **Job titles** | The strongest signal — 40 of the 100 points |
| **Where you can work** | Countries, cities, or `Remote` / `Worldwide`. Understands `EU`, `EMEA`, `APAC`, `LATAM`, `US`, `UK`, `ANZ`, `UAE` |
| **Hide jobs outside my locations** | Drops “Remote — US only” style postings |
| **Regions you cannot work in** | Explicit blocklist for work-authorization reasons |
| **Industries** | Chooses which company career pages get watched |
| **Anthropic API key** | Optional. Claude writes each letter from your CV and the job description |
| **Minimum score** | How picky the matches list is. Default 55 |

---

## Privacy

Everything lives in `chrome.storage.local` on this machine. The extension talks
to exactly two kinds of host: the public job APIs listed above, and
`api.anthropic.com` — only if you supply your own key. There is no JobHunter
server and no account.

---

## Layout

```
manifest.json        permissions and content-script targets
background.js        the engine: scheduled scans, badge, notifications, messages
lib/sources.js       6 ATS providers + 6 job boards
lib/matcher.js       0-100 scoring and the geography rules
lib/cv.js            PDF / DOCX / TXT parsing, pulls your details out of the CV
lib/letters.js       cover letters — template or Claude
lib/companies.js     company library by industry
lib/store.js         storage layer
app.html/js/css      dashboard: matches, pipeline, settings
onboarding.html/js   first-run setup
popup.html/js        toolbar popup
content/prefill.js   the form filler
content/button.js    the “Fill with JobHunter” button on application pages
```

There is also a Python version in `../jobhunter/` for power users: same engine,
plus SMTP email applications and IMAP tracking of company replies — things a
browser extension cannot do.
