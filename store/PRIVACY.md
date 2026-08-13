# Privacy Policy — JobHunter

**Last updated: 11 August 2026**

JobHunter is a browser extension that searches public job listings, ranks them
against a profile you define, and fills in application forms for you.

## The short version

There is no JobHunter server and no JobHunter account. Your CV, your personal
details and your application history are stored by your browser, on your
computer, and are never sent to us. We have no way of reading them.

## What is stored, and where

All of the following is kept in your browser's local extension storage
(`chrome.storage.local`) on your device:

- Your CV file and the text extracted from it
- Your name, email, phone, location, LinkedIn and GitHub links, work
  authorization status and notice period
- Your search preferences: job titles, locations, industries, salary floor,
  seniority, filters
- Job postings retrieved from public job boards
- Your applications, cover letters and their status history
- An Anthropic API key, if you choose to add one

Uninstalling the extension deletes all of it. You can also clear it at any time
from the extension's settings or your browser's site data controls.

## What leaves your device

JobHunter makes network requests to exactly two kinds of destination.

**1. Public job listing APIs.** To find jobs, the extension requests public
listings from: Greenhouse, Lever, Ashby, Workable, SmartRecruiters, Recruitee,
Remotive, Arbeitnow, RemoteOK, Jobicy, Himalayas and WorkingNomads. These are
ordinary read requests for publicly available job postings. **No personal data
of yours is included** — not your CV, not your name, not your preferences. The
matching happens on your computer after the listings arrive.

**2. Anthropic's API — only if you opt in.** If, and only if, you enter your own
Anthropic API key in Settings, JobHunter sends the text of your CV and the
description of the specific job to `api.anthropic.com` in order to write a
cover letter for that job. This happens once per application, at your request.
Without a key, cover letters are produced from a local template and nothing is
sent. That traffic is governed by
[Anthropic's privacy policy](https://www.anthropic.com/legal/privacy).

Nothing else is transmitted anywhere. There is no analytics, no telemetry, no
error reporting, no advertising and no tracking of any kind.

## Form filling

When you press "Fill with JobHunter" on an application page, the extension
writes your details into that page's form fields and attaches your CV file. This
happens entirely inside your browser. The data goes to the employer only when
**you** press the employer's own Submit button. JobHunter never submits a form
on your behalf.

## Data we sell or share

None. We do not sell your data, transfer it to third parties, or use it for
anything other than the function described above. We do not use it for
advertising, credit assessment or lending.

## Children

JobHunter is not directed at children under 13.

## Changes

If this policy changes, the updated version will be published at this address
and the date at the top will change.

## Contact

Questions about this policy: **panosgiorgas10@gmail.com**
