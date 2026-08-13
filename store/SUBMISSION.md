# Shipping JobHunter to the Chrome Web Store

The package is built and passes the automated checks. What remains needs your
hands — an account, a payment, a hosted URL and four screenshots.

```bash
python store/package.py
```
→ `store/dist/jobhunter-1.0.0.zip` · 21 files · 45 KB

---

## Step 1 — Developer account (5 minutes, $5)

1. Go to https://chrome.google.com/webstore/devconsole
2. Sign in with the Google account that should own the extension. **Pick
   carefully** — moving an extension between accounts later is painful.
3. Pay the one-time $5 registration fee.
4. Fill in the account's publisher name and a contact email. Google emails a
   verification link; the extension cannot go live until you click it.

Only you can do this — it needs your payment method.

---

## Step 2 — Host the privacy policy (10 minutes)

A privacy policy URL is **mandatory** for us, because the extension handles
personal information. It must be publicly reachable without a login.

`store/PRIVACY.md` is written and ready. The cheapest way to host it:

1. Create a public GitHub repo (e.g. `jobhunter`)
2. Push the project, or at minimum `store/PRIVACY.md`
3. Settings → Pages → deploy from `main` → the file is served at
   `https://<you>.github.io/jobhunter/store/PRIVACY.html`

A public Gist also works. Whatever URL you end up with goes in the Privacy tab
of the listing.

---

## Step 3 — Screenshots (15 minutes)

At least one is required; five are allowed. Four are prepared, sized exactly
1280×800, in `store/screenshots/`:

| File | Shows |
|---|---|
| `1-matches.html` | The ranked matches with score rings and the reasons |
| `2-pipeline.html` | The application pipeline board |
| `3-autofill.html` | A real application form, filled, CV attached |
| `4-onboarding.html` | CV upload with details read out of it |

To capture each one at exact pixel size:

1. Open the file in Chrome
2. `F12` → toggle device toolbar (`Ctrl+Shift+M`) → set **1280 × 800**
3. `Ctrl+Shift+P` → type *screenshot* → **Capture screenshot**

That saves a PNG at exactly the right size, no cropping needed.

Order them 1 → 4 in the listing; the first is the one people actually look at.

---

## Step 4 — Create the listing (20 minutes)

In the Developer Dashboard: **Add new item** → upload
`store/dist/jobhunter-1.0.0.zip`.

Then work through the tabs, pasting from `LISTING.md`:

- **Store listing** — name, short description, detailed description, category
  (Productivity), language, screenshots, store icon
- **Privacy practices** — single purpose statement, a justification for every
  permission, the data-usage disclosures, the three certification checkboxes,
  and your privacy policy URL
- **Distribution** — Public, all regions, free

Every field you need is written out in `LISTING.md`. Do not skip the permission
justifications: a missing or lazy justification is the single most common cause
of rejection.

---

## Step 5 — Submit and wait

Review typically takes a few days. Extensions that read page content — ours
does, on job application forms — sometimes get a manual review that runs one to
three weeks. You will get an email either way.

If it is rejected, the email names the policy. Fix, bump the version, rebuild:

```bash
python store/package.py --bump 1.0.1
```

---

## Things worth knowing before you press submit

**The name.** "JobHunter" is generic and there are products using similar names.
Google will not check trademarks for you, but a rights holder can file a
complaint later and get the listing pulled. Search the Web Store and the EUIPO
register for the name before you commit to it. If you want to be safe, a
distinctive name costs you nothing now and a lot later.

**First-run permissions.** On install Chrome will show the user a permission
prompt listing every host. Ours reads: "Read and change your data on 13 sites".
That is honest and narrow — no `<all_urls>` — but expect some users to hesitate.
The listing description addresses this directly.

**Reviewers test the extension.** Yours works immediately on install: the
onboarding opens, a CV can be dropped in, and a real search runs. Nothing is
gated behind an account or a key. That is a meaningful advantage during review.

**Updates.** Each update goes through review again. Batch changes rather than
shipping daily.

**What is not in this package.** The Python version in `jobhunter/` — SMTP email
applications and IMAP reply tracking — stays out. A browser extension cannot do
either, and shipping unused code invites questions.
