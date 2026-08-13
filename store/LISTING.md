# Chrome Web Store listing — copy/paste sheet

Everything below is ready to paste into the Developer Dashboard forms.

---

## Store listing tab

**Name** (max 75)
```
JobHunter — automatic job search
```

**Short description** (max 132 — this one is 118)
```
Finds jobs that match you every day and fills in the application forms for you. Your CV never leaves your browser.
```

**Category:** Productivity
**Language:** English

**Detailed description**
```
Job hunting is 90% repetitive admin. JobHunter does that part.

Upload your CV once. From then on JobHunter searches twice a day, ranks what
actually fits you, writes the cover letter, and fills in the application form —
including attaching your CV as a real file. You review and press Submit.

── HOW IT WORKS ──────────────────────────────────────────

1. Upload your CV. JobHunter reads it and fills in your name, email, phone and
   LinkedIn automatically, then suggests job titles based on your experience.

2. Say what you want. Job titles, countries or "Remote", salary floor,
   industries, seniority. Every filter is yours to set.

3. It searches on its own. Twice a day in the background, across public job
   boards and thousands of company career pages. You get a notification and a
   badge count when new roles match.

4. Apply in about fifteen seconds. Press Apply, the posting opens, press "Fill
   with JobHunter", check the form, submit.

5. Track everything. A pipeline board from Prepared to Sent, Interview and
   Offer. Drag cards between stages.

── WHY THE MATCHES ARE ACTUALLY GOOD ─────────────────────

Every job gets a 0-100 score, and JobHunter always tells you why: job title
(40 points), location (25), industry (10), language (10), how fresh the posting
is (10), salary (5), minus penalties when the seniority is wrong.

Crucially, it understands geography. A "Remote" job that is really "US only" is
dropped if you cannot work in the US — and it says so, instead of wasting your
time. Regional shorthands like EU, EMEA, APAC, LATAM, UK and ANZ are understood.

── WHERE THE JOBS COME FROM ──────────────────────────────

Public, documented APIs only: Remotive, Arbeitnow, RemoteOK, Jobicy, Himalayas
and WorkingNomads, plus any employer using Greenhouse, Lever, Ashby, Workable,
SmartRecruiters or Recruitee. Pick your industries and a matching set of company
career pages is tracked for you.

JobHunter does not automate LinkedIn or Indeed accounts. Their terms forbid it
and it gets people's accounts banned.

── YOUR DATA STAYS YOURS ─────────────────────────────────

There is no JobHunter server and no account. Your CV, your details and your
application history live in your browser's local storage and are never sent to
us — we have no way of reading them. No analytics, no telemetry, no tracking.

Optionally, you can add your own Anthropic API key so Claude writes each cover
letter from your CV and the job description. Without a key, a solid template is
used and nothing is transmitted.

── WHAT IT WILL NOT DO ───────────────────────────────────

It never presses Submit. Dropdown questions about work authorization or
relocation are deliberately left untouched and flagged for you — a wrong answer
to a legal question costs more than the three seconds it takes you to pick.
Fields you already filled in are never overwritten.
```

---

## Privacy practices tab

**Single purpose description**
```
JobHunter has one purpose: to help a person find job openings that match their
profile and complete the application forms for those openings. Every feature —
searching public job boards, scoring listings, writing a cover letter, filling
the application form, and tracking the resulting applications — serves that one
purpose.
```

**Permission justifications**

| Permission | Justification to paste |
|---|---|
| `storage` | Stores the user's profile, CV, search preferences, retrieved job listings and application history locally on their device. The extension has no server, so this is the only place the data exists. |
| `unlimitedStorage` | The cached job listings and the user's CV file routinely exceed the 5 MB default quota. Nothing is uploaded anywhere; it is all local. |
| `alarms` | Runs the twice-daily background job search so the user does not have to open the extension to get new results. |
| `notifications` | Tells the user when a background search has found new job openings that match their profile. |
| `activeTab` | When the user clicks "Fill the current page" in the extension popup, the form filler is injected into the tab the user is actively looking at, at that moment, on their explicit click. |
| `scripting` | Injects the form-filling script into an application page in response to that same explicit user click, for career sites not covered by the declared content scripts. |
| Host permissions for job boards | Read-only requests for publicly available job listings from Greenhouse, Lever, Ashby, Workable, SmartRecruiters, Recruitee, Remotive, Arbeitnow, RemoteOK, Jobicy, Himalayas and WorkingNomads. No user data is sent in these requests. |
| Host permission `open.er-api.com` | Fetches published currency exchange rates once per day so a minimum-salary filter set in one currency can be compared against jobs advertised in another. No user data is sent; the request has no parameters. |
| Host permission `api.anthropic.com` | Optional feature. Only if the user enters their own Anthropic API key, the extension sends the user's CV text and the job description to Anthropic to generate a cover letter for that specific job. Disabled and unused by default. |
| Content scripts on ATS domains | Displays the "Fill with JobHunter" button on job application forms hosted by Greenhouse, Lever, Ashby, Workable, SmartRecruiters, Recruitee, Teamtailor, BambooHR, Workday, Personio, Jobvite and iCIMS, so the user can fill the form in one click. |

**Remote code:** No. All JavaScript is contained in the package. Nothing is
evaluated from a remote source.

**Data usage disclosures** — tick these:

| Category | Collected? | Note |
|---|---|---|
| Personally identifiable information | **Yes** | Name, email, phone, CV. Stored locally. Transmitted only to `api.anthropic.com`, and only if the user supplies their own API key for the optional cover-letter feature. |
| Location | **Yes** | The city/country the user types in as their own location. Stored locally, used for matching. |
| Web history | No | |
| User activity | No | |
| Website content | No | |
| Health, financial, authentication info, personal communications | No | |

Certify all three:
- ☑ I do not sell or transfer user data to third parties, outside of the approved use cases
- ☑ I do not use or transfer user data for purposes that are unrelated to my item's single purpose
- ☑ I do not use or transfer user data to determine creditworthiness or for lending purposes

**Privacy policy URL:** the public URL where you host `PRIVACY.md`
(GitHub Pages, a Gist, or any static host — it must be reachable without login).

---

## Assets

| Asset | Size | Status |
|---|---|---|
| Store icon | 128×128 | ✅ `extension/icons/128.png` |
| Screenshots | 1280×800 | ⏳ capture from `store/screenshots/*.html` (see SUBMISSION.md) |
| Small promo tile | 440×280 | Optional |
| Marquee promo tile | 1400×560 | Optional |
