# Chrome Web Store listing — copy/paste sheet

Everything below is ready to paste into the Developer Dashboard forms.

---

## Store listing tab

**Name** (max 75)
```
Jobora — automatic job search
```

**Short description** (max 132 — this one is 118)
```
Finds jobs that match you every day and fills in the application forms for you. Your CV never leaves your browser.
```

**Category:** Productivity
**Language:** English

**Detailed description**
```
Job hunting is mostly admin. Jobora does that part.

Upload your CV once. After that it searches twice a day, ranks what actually
fits, drafts the cover letter, and fills in the application form with your CV
attached as a real file. You check it and press Submit.


HOW IT WORKS

1. Upload your CV. Jobora reads your name, email, phone and LinkedIn out of it,
   then suggests job titles based on what you have done.

2. Say what you want: job titles, countries or "Remote", a salary floor,
   industries, seniority. Every change saves itself as you type.

3. It searches on its own, twice a day, in the background. When something new
   matches, you get a notification and a number on the toolbar icon.

4. Applying takes about fifteen seconds. Press Apply, the posting opens, press
   "Fill with Jobora", check the form, submit it yourself.

5. Track it. A board from Prepared to Sent, Interview and Offer. Drag the cards.


NOT ONLY DESK JOBS

Most job tools are built for software engineers. This one knows 31 industries
and over 400 professions: care work, construction, kitchens, classrooms, stages.
It also reads job titles in your own language, so an advert that never uses an
English word still reaches you.


WHY THE MATCHES ARE GOOD

Every posting gets a score out of 100, and Jobora shows its working: job title
is worth 40 points, location 25, industry 10, the language you speak 10, how
recent the posting is 10, salary 5. Wrong seniority loses points.

It understands geography, which matters more than it sounds. A "Remote" job that
turns out to mean "US only" gets dropped if you cannot work in the US, and
Jobora says that is why. It also reads the regional shorthand employers use
instead of naming countries.

When nothing matches, it names the filter that emptied the list. No more staring
at a zero and wondering whether the thing is broken.


WHERE THE JOBS COME FROM

Public listings, from two kinds of place: open job boards, and the career pages
companies publish through the usual applicant tracking systems. Choose your
industries and a matching set of employers gets watched for you. A few national
job sites are in there too, for the work that never reaches an international
board. Clinics. Theatres. Workshops. Hotels.

Connect your own free key from a job-market data provider and the search widens
from the employers it knows to a country's whole market.


YOUR DATA STAYS YOURS

No account. No server. No analytics. Your CV, your details and your application
history live in your browser's storage, on your machine, and we have no way of
reading them.

If you add your own Anthropic API key, each cover letter is written from your CV
and the job description. Without a key it uses a template and nothing is sent
anywhere at all.


WHAT IT WILL NOT DO

It never presses Submit. Dropdown questions about work authorisation or
relocation are left alone on purpose and flagged for you, because a wrong answer
to a legal question costs more than the three seconds it takes to answer it
yourself. Anything you have already typed is never overwritten. If required
questions are still empty, it tells you how many, so you do not send half an
application.

Interface in eight languages. Free, open source, no upsell.
```

---

## Privacy practices tab

**Single purpose description**
```
Jobora has one purpose: to help a person find job openings that match their
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
| Host permissions for job boards | Read-only requests for publicly available job listings. Applicant tracking systems: Greenhouse, Lever, Ashby, Workable, SmartRecruiters, Recruitee, Workday, Teamtailor, Breezy. Job boards: Remotive, Arbeitnow, RemoteOK, Jobicy, Himalayas, WorkingNomads, The Muse, We Work Remotely, Cryptocurrency Jobs, Landing.jobs, DevITjobs. National sources: psf.org.gr, skywalker.gr, ordino.gr. No user data is sent in these requests. |
| Host permission `api.adzuna.com` | Optional feature. Only if the user enters their own Adzuna application ID and key, the extension queries Adzuna for listings in the countries the user selected. The request carries the user's own credentials and those country codes, which is how the Adzuna API identifies a caller. No CV, name or contact details are sent. Without a key no request is made. |
| Host permission `open.er-api.com` | Fetches published currency exchange rates once per day so a minimum-salary filter set in one currency can be compared against jobs advertised in another. No user data is sent; the request has no parameters. |
| Host permission `api.anthropic.com` | Optional feature. Only if the user enters their own Anthropic API key, the extension sends the user's CV text and the job description to Anthropic to generate a cover letter for that specific job. Disabled and unused by default. |
| Optional host permissions for social networks | Not requested at install and off by default. Some jobs are only posted as a post in a group or thread. If the user switches on "Save button on social posts" in Settings, Chrome asks them to grant access to facebook.com, instagram.com, reddit.com, x.com, twitter.com and threads.net, and switching it off withdraws the permission. While on, a button appears over a post that reads like a job ad; the post's text is read only when the user presses that button, is shown to them for correction, and is stored locally. Nothing is read in the background and nothing is transmitted. |
| Content scripts on ATS domains | Displays the "Fill with Jobora" button on job application forms hosted by Greenhouse, Lever, Ashby, Workable, SmartRecruiters, Recruitee, Teamtailor, BambooHR, Workday, Personio, Jobvite and iCIMS, so the user can fill the form in one click. |

**Remote code:** No. All JavaScript is contained in the package. Nothing is
evaluated from a remote source.

**Data usage disclosures** — tick these:

| Category | Collected? | Note |
|---|---|---|
| Personally identifiable information | **Yes** | Name, email, phone, CV, profile photo and the text the user writes about themselves. Stored locally. Transmitted only to `api.anthropic.com`, and only if the user supplies their own API key for the optional cover-letter feature. The photo is never transmitted or attached to an application. |
| Location | **Yes** | The city/country the user types in as their own location. Stored locally, used for matching. |
| Web history | No | |
| User activity | No | |
| Website content | No | |
| Health, financial, authentication info, personal communications | No | |

Certify all three:
- ☑ I do not sell or transfer user data to third parties, outside of the approved use cases
- ☑ I do not use or transfer user data for purposes that are unrelated to my item's single purpose
- ☑ I do not use or transfer user data to determine creditworthiness or for lending purposes

**Privacy policy URL:**
```
https://georgasp.github.io/jobora/privacy.html
```
Served from `docs/` by GitHub Pages. `store/privacy_html.py` regenerates it from
`store/PRIVACY.md`; it only goes live once the commit is pushed.

---

## Assets

| Asset | Size | Status |
|---|---|---|
| Store icon | 128×128 | ✅ `extension/icons/128.png` |
| Screenshots | 1280×800 | ✅ `store/screenshots/1.png` … `5.png` — rebuild with `python store/shoot.py` |
| Small promo tile | 440×280 | Optional |
| Marquee promo tile | 1400×560 | Optional |
