# Privacy Policy — Jobora

**Last updated: 21 September 2026**

Jobora is a browser extension that searches public job listings, ranks them
against a profile you define, and fills in application forms for you.

## The short version

There is no Jobora server and no Jobora account. Your CV, your personal
details and your application history are stored by your browser, on your
computer, and are never sent to us. We have no way of reading them.

## What is stored, and where

All of the following is kept in your browser's local extension storage
(`chrome.storage.local`) on your device:

- Your CV file and the text extracted from it
- Your name, email, phone, location, LinkedIn and GitHub links, work
  authorization status and notice period
- Your profile photo, headline and the text you write about yourself. The photo
  is resized and stored on your device; it is never attached to an application
- Your search preferences: job titles, locations, industries, salary floor,
  seniority, filters
- Job postings retrieved from public job boards
- Your applications, cover letters and their status history
- An Anthropic API key, if you choose to add one
- An Adzuna application ID and key, if you choose to add your own

Uninstalling the extension deletes all of it. You can also clear it at any time
from the extension's settings or your browser's site data controls.

## What leaves your device

Jobora makes network requests to three kinds of destination, and to nothing
else.

**1. Public job listing APIs and pages.** To find jobs, the extension requests
publicly available listings from the applicant tracking systems Greenhouse,
Lever, Ashby, Workable, SmartRecruiters, Recruitee, Workday, Teamtailor and
Breezy; from the job boards Remotive, Arbeitnow, RemoteOK, Jobicy, Himalayas,
WorkingNomads, The Muse, We Work Remotely, Cryptocurrency Jobs, Landing.jobs
and DevITjobs; and from the Greek sites psf.org.gr, skywalker.gr and ordino.gr.
These are ordinary read requests for postings that anyone can see without
logging in. **No personal data of yours is included** — not your CV, not your
name, not your preferences. The matching happens on your computer after the
listings arrive.

One exception, and only if you set it up: **Adzuna**. If you enter your own
Adzuna application ID and key in Settings, requests to `api.adzuna.com` carry
those credentials and the country codes you chose to search, because that is
how their API identifies the caller. Your CV, name and contact details are
still not sent. Without a key, no request is made to Adzuna at all.

**2. Currency exchange rates.** Once a day the extension requests published
exchange rates from `open.er-api.com`, so that a minimum salary you set in one
currency can be compared against a job advertised in another. The request has
no parameters and carries no data about you.

**3. Anthropic's API — only if you opt in.** If, and only if, you enter your own
Anthropic API key in Settings, Jobora sends the text of your CV, anything you
wrote about yourself in your profile, and the description of the specific job to
`api.anthropic.com` in order to write a cover letter for that job. This happens
once per application, at your request. Without a key, cover letters are produced
from a local template and nothing is sent. That traffic is governed by
[Anthropic's privacy policy](https://www.anthropic.com/legal/privacy).

Nothing else is transmitted anywhere. There is no analytics, no telemetry, no
error reporting, no advertising and no tracking of any kind.

## The save button on social networks — off unless you turn it on

Some jobs are only ever posted as a post: a group on Facebook, a thread on
Reddit, an update on a page. Jobora can show a "Save to Jobora" button
while you are reading such a post, so you can keep it alongside the listings it
found itself.

This is **switched off by default**. Turning it on asks Chrome for permission to
run on facebook.com, instagram.com, reddit.com, x.com, twitter.com and
threads.net; turning it off withdraws that permission again. Until you turn it
on, the extension has no access to those sites at all.

While it is on, the button reads the text of the post you are looking at only
after **you** press it, and shows you exactly what it will keep, in a form you
can correct first. Nothing is read in the background, nothing is collected while
you browse, and nothing is sent anywhere: what you save is stored on your device
like any other listing.

## Form filling

When you press "Fill with Jobora" on an application page, the extension reads
that page's form — the labels and field names, so it knows which box wants your
phone number and which wants your city — and then writes your details in and
attaches your CV file. Both the reading and the writing happen inside your
browser, at the moment you press the button. The page's contents are not stored
and are not sent anywhere.

The data goes to the employer only when **you** press the employer's own Submit
button. Jobora never submits a form on your behalf. Questions it cannot
answer safely, such as dropdowns about work authorization, are deliberately left
untouched and counted for you.

## Data we sell or share

None. We do not sell your data, transfer it to third parties, or use it for
anything other than the function described above. We do not use it for
advertising, credit assessment or lending.

## Children

Jobora is not directed at children under 13.

## Changes

If this policy changes, the updated version will be published at this address
and the date at the top will change.

## Contact

Questions about this policy: **panosgiorgas10@gmail.com**
